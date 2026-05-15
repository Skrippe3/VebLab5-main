import os
import secrets
from urllib.parse import urlencode

from flask import Blueprint, g, jsonify, make_response, redirect, request

from app.middleware.auth_middleware import auth_required
from app.services.auth_service import AuthService
from app.utils.cookie_utils import clear_auth_cookies, set_auth_cookies

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/auth/register", methods=["POST"])
def register():
    """
    Регистрация нового пользователя.
    ---
    tags:
      - Auth
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/RegisterRequest'
    responses:
      201:
        description: Пользователь успешно зарегистрирован
        schema:
          $ref: '#/definitions/UserResponse'
      400:
        description: Ошибка валидации или пользователь уже существует
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"message": "JSON body is required"}), 400

    if not data.get("email") or not data.get("password"):
        return jsonify({"message": "Email and password are required"}), 400

    try:
        user = AuthService.register(data)
    except ValueError as error:
        return jsonify({"message": str(error)}), 400

    return jsonify(
        {
            "id": str(user["_id"]),
            "email": user["email"],
        }
    ), 201


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    """
    Вход пользователя и установка HttpOnly cookies.
    ---
    tags:
      - Auth
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/LoginRequest'
    responses:
      200:
        description: Успешный вход. Access и Refresh токены установлены в HttpOnly cookies.
        examples:
          application/json:
            message: "Logged in"
      400:
        description: Не передан JSON или обязательные поля
        schema:
          $ref: '#/definitions/ErrorResponse'
      401:
        description: Неверный email или пароль
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"message": "JSON body is required"}), 400

    if not data.get("email") or not data.get("password"):
        return jsonify({"message": "Email and password are required"}), 400

    result = AuthService.login(data)

    if not result:
        return jsonify({"message": "Invalid credentials"}), 401

    user, access_token, refresh_token = result

    response = make_response(jsonify({"message": "Logged in"}))
    set_auth_cookies(response, access_token, refresh_token)

    return response, 200


@auth_bp.route("/auth/refresh", methods=["POST"])
def refresh():
    """
    Обновление пары Access/Refresh токенов.
    ---
    tags:
      - Auth
    security:
      - refreshCookieAuth: []
    responses:
      200:
        description: Токены успешно обновлены
        examples:
          application/json:
            message: "Tokens refreshed"
      401:
        description: Refresh token отсутствует или недействителен
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        return jsonify({"message": "Refresh token is missing"}), 401

    result = AuthService.refresh(refresh_token)

    if not result:
        return jsonify({"message": "Invalid refresh token"}), 401

    user, access_token, new_refresh_token = result

    response = make_response(
        jsonify(
            {
                "message": "Tokens refreshed",
                "user": {
                    "id": str(user["_id"]),
                    "email": user["email"],
                },
            }
        )
    )
    set_auth_cookies(response, access_token, new_refresh_token)

    return response, 200


@auth_bp.route("/auth/whoami", methods=["GET"])
@auth_required
def whoami():
    """
    Проверка текущего авторизованного пользователя.
    ---
    tags:
      - Auth
    security:
      - cookieAuth: []
    responses:
      200:
        description: Данные текущего пользователя без чувствительных полей
        schema:
          $ref: '#/definitions/UserResponse'
      401:
        description: Пользователь не авторизован
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    user = g.current_user

    return jsonify(
        {
            "id": str(user["_id"]),
            "email": user["email"],
            "yandex_id": user.get("yandex_id"),
        }
    ), 200


@auth_bp.route("/auth/logout", methods=["POST"])
@auth_required
def logout():
    """
    Выход из текущей сессии.
    ---
    tags:
      - Auth
    security:
      - cookieAuth: []
    responses:
      200:
        description: Текущая сессия завершена, cookies очищены
        examples:
          application/json:
            message: "Logged out"
      401:
        description: Пользователь не авторизован
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")

    AuthService.logout(access_token, refresh_token)

    response = make_response(jsonify({"message": "Logged out"}))
    clear_auth_cookies(response)

    return response, 200


@auth_bp.route("/auth/logout-all", methods=["POST"])
@auth_required
def logout_all():
    """
    Выход из всех сессий пользователя.
    ---
    tags:
      - Auth
    security:
      - cookieAuth: []
    responses:
      200:
        description: Все сессии пользователя завершены, cookies очищены
        examples:
          application/json:
            message: "Logged out from all sessions"
      401:
        description: Пользователь не авторизован
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    user = g.current_user

    AuthService.logout_all(str(user["_id"]))

    response = make_response(jsonify({"message": "Logged out from all sessions"}))
    clear_auth_cookies(response)

    return response, 200


@auth_bp.route("/auth/oauth/yandex", methods=["GET"])
def yandex_oauth_start():
    """
    Начало OAuth авторизации через Yandex ID.
    ---
    tags:
      - Auth
    responses:
      302:
        description: Редирект пользователя на страницу авторизации Yandex OAuth
      500:
        description: OAuth Yandex не настроен
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    client_id = os.getenv("YANDEX_CLIENT_ID")
    redirect_uri = os.getenv("YANDEX_CALLBACK_URL")

    if not client_id or not redirect_uri:
        return jsonify({"message": "Yandex OAuth is not configured"}), 500

    state = secrets.token_urlsafe(32)

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
    }

    yandex_url = "https://oauth.yandex.ru/authorize?" + urlencode(params)

    response = redirect(yandex_url)
    response.set_cookie(
        "oauth_state",
        state,
        httponly=True,
        samesite="Lax",
        max_age=300,
    )

    return response


@auth_bp.route("/auth/oauth/yandex/callback", methods=["GET"])
def yandex_oauth_callback():
    """
    Callback OAuth Yandex после авторизации пользователя.
    ---
    tags:
      - Auth
    parameters:
      - in: query
        name: code
        required: true
        type: string
        description: Authorization code от Yandex OAuth
      - in: query
        name: state
        required: true
        type: string
        description: CSRF state, который должен совпасть с cookie oauth_state
    responses:
      302:
        description: Успешная авторизация, установка cookies и редирект на /auth/whoami
      400:
        description: Отсутствует code или неверный state
        schema:
          $ref: '#/definitions/ErrorResponse'
      401:
        description: Ошибка авторизации через Yandex
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    code = request.args.get("code")
    state = request.args.get("state")
    saved_state = request.cookies.get("oauth_state")

    if not code:
        return jsonify({"message": "Authorization code is missing"}), 400

    if not state or not saved_state or state != saved_state:
        return jsonify({"message": "Invalid OAuth state"}), 400

    result = AuthService.login_with_yandex(code)

    if not result:
        return jsonify({"message": "Yandex OAuth failed"}), 401

    user, access_token, refresh_token = result

    response = redirect("/auth/whoami")
    set_auth_cookies(response, access_token, refresh_token)
    response.delete_cookie("oauth_state")

    return response