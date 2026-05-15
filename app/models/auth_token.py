from datetime import datetime


def create_auth_token_document(user_id, token_hash, token_type, expires_at, revoked=False):
    return {
        "user_id": user_id,
        "token_hash": token_hash,
        "token_type": token_type,
        "expires_at": expires_at,
        "revoked": revoked,
        "created_at": datetime.utcnow(),
    }