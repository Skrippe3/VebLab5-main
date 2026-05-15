# Лабораторная работа №4

## Тема

Автоматизированное документирование REST API с использованием OpenAPI / Swagger.

## Описание проекта

Проект является продолжением лабораторной работы №3.

В приложении реализованы:

- REST API на Flask;
- PostgreSQL;
- Docker / Docker Compose;
- регистрация и вход пользователей;
- JWT access / refresh tokens;
- хранение токенов в HttpOnly cookies;
- refresh токены;
- logout и logout-all;
- OAuth авторизация через Yandex ID;
- защищенный CRUD задач;
- soft delete задач;
- автоматическая Swagger/OpenAPI документация.

В лабораторной работе №4 добавлена автоматическая документация API через Swagger UI.

Документация доступна только в режиме разработки.

## Стек

- Python 3.12
- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- PostgreSQL 16
- PyJWT
- Requests
- Flasgger
- Docker
- Docker Compose

## Переменные окружения

Пример `.env.example`:

```env
FLASK_APP=run.py
FLASK_ENV=development
APP_ENV=development
SWAGGER_ENABLED=true

DB_HOST=postgres
DB_PORT=5432
DB_NAME=wp_labs
DB_USER=student
DB_PASSWORD=your_password

PORT=4200

JWT_ACCESS_SECRET=change_me_access_secret
JWT_REFRESH_SECRET=change_me_refresh_secret
JWT_ACCESS_EXPIRATION=15m
JWT_REFRESH_EXPIRATION=7d

YANDEX_CLIENT_ID=your_yandex_client_id
YANDEX_CLIENT_SECRET=your_yandex_client_secret
YANDEX_CALLBACK_URL=http://localhost:4200/auth/oauth/yandex/callback