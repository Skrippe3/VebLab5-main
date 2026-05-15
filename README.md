# Лабораторная работа №6  
## MongoDB + Flask REST API

## Описание проекта

Проект представляет собой REST API на Flask с JWT авторизацией, OAuth Yandex, Swagger документацией, Redis и MongoDB.

В рамках лабораторной работы выполнена миграция слоя хранения данных с PostgreSQL на MongoDB.

Реализовано:

- JWT authentication
- Refresh tokens
- HttpOnly cookies
- OAuth Yandex
- CRUD задач
- Soft Delete
- Пагинация
- Swagger документация
- Docker Compose инфраструктура
- MongoDB
- Redis

---

# Используемые технологии

- Python 3.12
- Flask
- MongoDB 6
- PyMongo
- Redis 7
- Docker
- Docker Compose
- JWT
- Swagger / Flasgger

---

# Структура проекта

```text
app/
├── database/
│   └── mongo.py
├── middleware/
│   └── auth_middleware.py
├── models/
│   ├── auth_token.py
│   ├── task.py
│   └── user.py
├── routes/
│   ├── auth_routes.py
│   └── task_routes.py
├── services/
│   ├── auth_service.py
│   └── task_service.py
├── utils/
│   ├── cookie_utils.py
│   ├── hash_utils.py
│   └── jwt_utils.py
├── swagger.py
└── __init__.py
