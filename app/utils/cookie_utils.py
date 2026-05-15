def set_auth_cookies(response, access_token, refresh_token):
    response.set_cookie(
        "access_token",
        access_token,
        httponly=True,
        samesite="Lax",
        max_age=15 * 60
    )

    response.set_cookie(
        "refresh_token",
        refresh_token,
        httponly=True,
        samesite="Lax",
        max_age=7 * 24 * 60 * 60
    )


def clear_auth_cookies(response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
