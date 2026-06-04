from datetime import datetime

from app.database.mongo import users_collection
from app.services.cache_service import CacheService
from app.services.storage_service import StorageService


class ProfileService:
    @staticmethod
    def profile_to_response(user):
        user_id = str(user["_id"])

        return {
            "id": user_id,
            "email": user.get("email"),
            "displayName": user.get("display_name"),
            "bio": user.get("bio"),
            "avatarFileId": user.get("avatar_file_id"),
            "avatarUrl": f"/files/{user.get('avatar_file_id')}" if user.get("avatar_file_id") else None,
        }

    @classmethod
    def get_profile(cls, user):
        return cls.profile_to_response(user)

    @classmethod
    def update_profile(cls, user, data):
        user_id = str(user["_id"])
        update_data = {"updated_at": datetime.utcnow()}

        if "displayName" in data:
            update_data["display_name"] = data.get("displayName")

        if "bio" in data:
            update_data["bio"] = data.get("bio")

        if "avatarFileId" in data:
            avatar_file_id = data.get("avatarFileId")

            if avatar_file_id is not None:
                file_meta = StorageService.get_owned_file_meta(user_id, avatar_file_id)

                if not file_meta:
                    raise PermissionError("Avatar file not found")

                if file_meta.get("mimetype") not in StorageService.avatar_mimetypes():
                    raise ValueError("Avatar must be PNG or JPEG")

            update_data["avatar_file_id"] = avatar_file_id

        users_collection.update_one({"_id": user["_id"]}, {"$set": update_data})
        CacheService.delete(CacheService.profile_key(user_id))

        updated_user = users_collection.find_one({"_id": user["_id"]})
        return cls.profile_to_response(updated_user)
