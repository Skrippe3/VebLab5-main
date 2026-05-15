import os
from datetime import datetime, timedelta

import jwt


def create_access_token(user_id):
    payload = {
        "sub": user_id,
        "type": "access",
        "exp": datetime.utcnow() + timedelta(minutes=15)
    }

    return jwt.encode(
        payload,
        os.getenv("JWT_ACCESS_SECRET"),
        algorithm="HS256"
    )


def create_refresh_token(user_id):
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": datetime.utcnow() + timedelta(days=7)
    }

    return jwt.encode(
        payload,
        os.getenv("JWT_REFRESH_SECRET"),
        algorithm="HS256"
    )


def decode_access_token(token):
    return jwt.decode(
        token,
        os.getenv("JWT_ACCESS_SECRET"),
        algorithms=["HS256"]
    )


def decode_refresh_token(token):
    return jwt.decode(
        token,
        os.getenv("JWT_REFRESH_SECRET"),
        algorithms=["HS256"]
    )
