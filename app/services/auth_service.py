import os
import secrets
from datetime import datetime, timedelta

import requests
from bson import ObjectId

from app.database.mongo import users_collection, auth_tokens_collection
from app.models.user import create_user_document
from app.models.auth_token import create_auth_token_document
from app.utils.hash_utils import generate_salt, hash_password, verify_password, hash_token
from app.utils.jwt_utils import create_access_token, create_refresh_token, decode_refresh_token


class AuthService:

    @staticmethod
    def register(data):
        email = data["email"].strip().lower()
        password = data["password"]

        existing_user = users_collection.find_one({
            "email": email,
            "deleted_at": None
        })

        if existing_user:
            raise ValueError("User already exists")

        salt = generate_salt()
        password_hash = hash_password(password, salt)

        user_doc = create_user_document(
            email=email,
            password_hash=password_hash,
            password_salt=salt
        )

        result = users_collection.insert_one(user_doc)
        user_doc["_id"] = result.inserted_id

        return user_doc

    @staticmethod
    def create_session(user):
        user_id = str(user["_id"])

        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)

        access_token_record = create_auth_token_document(
            user_id=user_id,
            token_hash=hash_token(access_token),
            token_type="access",
            expires_at=datetime.utcnow() + timedelta(minutes=15),
            revoked=False
        )

        refresh_token_record = create_auth_token_document(
            user_id=user_id,
            token_hash=hash_token(refresh_token),
            token_type="refresh",
            expires_at=datetime.utcnow() + timedelta(days=7),
            revoked=False
        )

        auth_tokens_collection.insert_many([
            access_token_record,
            refresh_token_record
        ])

        return access_token, refresh_token

    @staticmethod
    def login(data):
        email = data["email"].strip().lower()
        password = data["password"]

        user = users_collection.find_one({
            "email": email,
            "deleted_at": None
        })

        if not user:
            return None

        if not verify_password(password, user["password_salt"], user["password_hash"]):
            return None

        access_token, refresh_token = AuthService.create_session(user)

        return user, access_token, refresh_token

    @staticmethod
    def refresh(refresh_token):
        try:
            payload = decode_refresh_token(refresh_token)
        except Exception:
            return None

        if payload.get("type") != "refresh":
            return None

        user_id = payload.get("sub")

        try:
            user_object_id = ObjectId(user_id)
        except Exception:
            return None

        user = users_collection.find_one({
            "_id": user_object_id,
            "deleted_at": None
        })

        if not user:
            return None

        token_record = auth_tokens_collection.find_one({
            "user_id": user_id,
            "token_hash": hash_token(refresh_token),
            "token_type": "refresh",
            "revoked": False
        })

        if not token_record:
            return None

        if token_record["expires_at"] < datetime.utcnow():
            auth_tokens_collection.update_one(
                {"_id": token_record["_id"]},
                {"$set": {"revoked": True}}
            )
            return None

        auth_tokens_collection.update_one(
            {"_id": token_record["_id"]},
            {"$set": {"revoked": True}}
        )

        access_token, new_refresh_token = AuthService.create_session(user)

        return user, access_token, new_refresh_token

    @staticmethod
    def logout(access_token=None, refresh_token=None):
        hashes = []

        if access_token:
            hashes.append(hash_token(access_token))

        if refresh_token:
            hashes.append(hash_token(refresh_token))

        if not hashes:
            return

        auth_tokens_collection.update_many(
            {"token_hash": {"$in": hashes}},
            {"$set": {"revoked": True}}
        )

    @staticmethod
    def logout_all(user_id):
        auth_tokens_collection.update_many(
            {
                "user_id": str(user_id),
                "revoked": False
            },
            {
                "$set": {"revoked": True}
            }
        )

    @staticmethod
    def login_with_yandex(code):
        client_id = os.getenv("YANDEX_CLIENT_ID")
        client_secret = os.getenv("YANDEX_CLIENT_SECRET")
        redirect_uri = os.getenv("YANDEX_CALLBACK_URL")

        if not client_id or not client_secret or not redirect_uri:
            return None

        token_response = requests.post(
            "https://oauth.yandex.ru/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri
            },
            timeout=10
        )

        if token_response.status_code != 200:
            print("Yandex token error:", token_response.text)
            return None

        token_data = token_response.json()
        yandex_access_token = token_data.get("access_token")

        if not yandex_access_token:
            return None

        profile_response = requests.get(
            "https://login.yandex.ru/info",
            headers={
                "Authorization": f"OAuth {yandex_access_token}"
            },
            params={
                "format": "json"
            },
            timeout=10
        )

        if profile_response.status_code != 200:
            print("Yandex profile error:", profile_response.text)
            return None

        profile = profile_response.json()

        yandex_id = str(profile.get("id"))
        email = profile.get("default_email")

        if not yandex_id:
            return None

        if not email:
            email = f"yandex_{yandex_id}@local.test"

        email = email.strip().lower()

        user = users_collection.find_one({
            "yandex_id": yandex_id,
            "deleted_at": None
        })

        if not user:
            user = users_collection.find_one({
                "email": email,
                "deleted_at": None
            })

            if user:
                users_collection.update_one(
                    {"_id": user["_id"]},
                    {
                        "$set": {
                            "yandex_id": yandex_id,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                user = users_collection.find_one({"_id": user["_id"]})
            else:
                random_password = secrets.token_urlsafe(32)
                salt = generate_salt()
                password_hash = hash_password(random_password, salt)

                user_doc = create_user_document(
                    email=email,
                    password_hash=password_hash,
                    password_salt=salt,
                    yandex_id=yandex_id
                )

                result = users_collection.insert_one(user_doc)
                user_doc["_id"] = result.inserted_id
                user = user_doc

        access_token, refresh_token = AuthService.create_session(user)

        return user, access_token, refresh_token