from functools import wraps
from datetime import datetime

from bson import ObjectId
from flask import request, jsonify, g

from app.database.mongo import users_collection, auth_tokens_collection
from app.utils.hash_utils import hash_token
from app.utils.jwt_utils import decode_access_token


def auth_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.cookies.get("access_token")

        if not token:
            return jsonify({"message": "Unauthorized"}), 401

        try:
            payload = decode_access_token(token)

            if payload.get("type") != "access":
                return jsonify({"message": "Unauthorized"}), 401

            user_id = payload.get("sub")

            try:
                user_object_id = ObjectId(user_id)
            except Exception:
                return jsonify({"message": "Unauthorized"}), 401

            user = users_collection.find_one({
                "_id": user_object_id,
                "deleted_at": None
            })

            if not user:
                return jsonify({"message": "Unauthorized"}), 401

            token_record = auth_tokens_collection.find_one({
                "user_id": user_id,
                "token_hash": hash_token(token),
                "token_type": "access",
                "revoked": False
            })

            if not token_record:
                return jsonify({"message": "Unauthorized"}), 401

            if token_record["expires_at"] < datetime.utcnow():
                auth_tokens_collection.update_one(
                    {"_id": token_record["_id"]},
                    {"$set": {"revoked": True}}
                )
                return jsonify({"message": "Unauthorized"}), 401

            g.current_user = user

        except Exception:
            return jsonify({"message": "Unauthorized"}), 401

        return f(*args, **kwargs)

    return wrapper