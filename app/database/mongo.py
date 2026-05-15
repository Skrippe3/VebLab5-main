import os
from pymongo import MongoClient

client = MongoClient(os.getenv("MONGO_URI"))
db = client.get_default_database()

users_collection = db["users"]
tasks_collection = db["tasks"]
auth_tokens_collection = db["auth_tokens"]


def init_indexes():
    users_collection.create_index("email", unique=True)
    users_collection.create_index("yandex_id")
    tasks_collection.create_index("user_id")
    auth_tokens_collection.create_index("user_id")
    auth_tokens_collection.create_index("token_hash")