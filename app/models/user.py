from datetime import datetime


def user_to_response(user):
    return {
        "id": str(user["_id"]),
        "email": user.get("email"),
        "yandex_id": user.get("yandex_id"),
    }


def create_user_document(email, password_hash, password_salt, yandex_id=None, vk_id=None):
    now = datetime.utcnow()

    return {
        "email": email,
        "password_hash": password_hash,
        "password_salt": password_salt,
        "yandex_id": yandex_id,
        "vk_id": vk_id,
        "created_at": now,
        "updated_at": now,
        "deleted_at": None,
    }