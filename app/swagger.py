import os

from flasgger import Swagger


def setup_swagger(app):
    app_env = os.getenv("APP_ENV", "development").lower()
    swagger_enabled = os.getenv("SWAGGER_ENABLED", "true").lower()

    if app_env == "production" or swagger_enabled == "false":
        return

    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "VebLab4 REST API",
            "description": (
                "Автоматизированная OpenAPI/Swagger документация для лабораторной работы №4. "
                "Проект основан на лабораторной работе №3: JWT, HttpOnly cookies, OAuth Yandex "
                "и защищенный CRUD задач."
            ),
            "version": "1.0.0",
        },
        "host": "127.0.0.1:4200",
        "basePath": "/",
        "schemes": ["http"],
        "tags": [
            {
                "name": "Auth",
                "description": "Регистрация, вход, refresh, logout, whoami и OAuth Yandex",
            },
            {
                "name": "Tasks",
                "description": "Защищенный CRUD задач пользователя",
            },
        ],
        "securityDefinitions": {
            "cookieAuth": {
                "type": "apiKey",
                "in": "cookie",
                "name": "access_token",
                "description": (
                    "JWT access token хранится в HttpOnly cookie. "
                    "После вызова /auth/login браузер автоматически отправляет cookie "
                    "в защищенные эндпоинты."
                ),
            },
            "refreshCookieAuth": {
                "type": "apiKey",
                "in": "cookie",
                "name": "refresh_token",
                "description": (
                    "JWT refresh token хранится в HttpOnly cookie и используется "
                    "для обновления access/refresh пары через /auth/refresh."
                ),
            },
        },
        "definitions": {
            "ErrorResponse": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "example": "Invalid credentials",
                    }
                },
            },
            "RegisterRequest": {
                "type": "object",
                "required": ["email", "password"],
                "properties": {
                    "email": {
                        "type": "string",
                        "format": "email",
                        "description": "Email пользователя",
                        "example": "test@mail.com",
                    },
                    "password": {
                        "type": "string",
                        "format": "password",
                        "description": "Пароль пользователя. В ответах не возвращается.",
                        "example": "12345678",
                    },
                },
            },
            "LoginRequest": {
                "type": "object",
                "required": ["email", "password"],
                "properties": {
                    "email": {
                        "type": "string",
                        "format": "email",
                        "example": "test@mail.com",
                    },
                    "password": {
                        "type": "string",
                        "format": "password",
                        "example": "12345678",
                    },
                },
            },
            "UserResponse": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "format": "uuid",
                        "example": "3c7a2a41-7d7b-4fd5-8a7d-f3e03a9d98a1",
                    },
                    "email": {
                        "type": "string",
                        "format": "email",
                        "example": "test@mail.com",
                    },
                    "yandex_id": {
                        "type": "string",
                        "nullable": True,
                        "example": "123456789",
                    },
                },
            },
            "TaskRequest": {
                "type": "object",
                "required": ["title", "description"],
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Название задачи",
                        "example": "Task 1",
                    },
                    "description": {
                        "type": "string",
                        "description": "Описание задачи",
                        "example": "Demo task description",
                    },
                    "status": {
                        "type": "string",
                        "description": "Статус задачи",
                        "example": "new",
                    },
                },
            },
            "TaskResponse": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "format": "uuid",
                        "example": "45e89f53-4e9e-4b51-bd89-3db8c6f013f1",
                    },
                    "title": {
                        "type": "string",
                        "example": "Task 1",
                    },
                    "description": {
                        "type": "string",
                        "example": "Demo task description",
                    },
                    "status": {
                        "type": "string",
                        "example": "new",
                    },
                    "createdAt": {
                        "type": "string",
                        "format": "date-time",
                        "example": "2026-04-24T18:30:00",
                    },
                    "updatedAt": {
                        "type": "string",
                        "format": "date-time",
                        "example": "2026-04-24T18:30:00",
                    },
                },
            },
            "TasksListResponse": {
                "type": "object",
                "properties": {
                    "data": {
                        "type": "array",
                        "items": {
                            "$ref": "#/definitions/TaskResponse",
                        },
                    },
                    "meta": {
                        "type": "object",
                        "properties": {
                            "total": {
                                "type": "integer",
                                "example": 1,
                            },
                            "page": {
                                "type": "integer",
                                "example": 1,
                            },
                            "limit": {
                                "type": "integer",
                                "example": 10,
                            },
                        },
                    },
                },
            },
        },
    }

    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec_1",
                "route": "/apispec_1.json",
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/api/docs/",
    }

    Swagger(app, template=swagger_template, config=swagger_config)