from datetime import datetime

from bson import ObjectId

from app.database.mongo import tasks_collection
from app.models.task import create_task_document, task_to_dict


class TaskService:

    @staticmethod
    def create(user_id, data):
        task_doc = create_task_document(
            user_id=str(user_id),
            title=data["title"],
            description=data["description"],
            status=data.get("status", "new")
        )

        result = tasks_collection.insert_one(task_doc)
        task_doc["_id"] = result.inserted_id

        return task_doc

    @staticmethod
    def get_all(user_id, page=1, limit=10):
        query = {
            "user_id": str(user_id),
            "deleted_at": None
        }

        total = tasks_collection.count_documents(query)

        tasks = list(
            tasks_collection
            .find(query)
            .sort("created_at", -1)
            .skip((page - 1) * limit)
            .limit(limit)
        )

        return {
            "data": [task_to_dict(task) for task in tasks],
            "meta": {
                "total": total,
                "page": page,
                "limit": limit
            }
        }

    @staticmethod
    def get_one(user_id, task_id):
        try:
            object_id = ObjectId(task_id)
        except Exception:
            return None

        return tasks_collection.find_one({
            "_id": object_id,
            "user_id": str(user_id),
            "deleted_at": None
        })

    @staticmethod
    def soft_delete(user_id, task_id):
        try:
            object_id = ObjectId(task_id)
        except Exception:
            return None

        task = tasks_collection.find_one({
            "_id": object_id,
            "user_id": str(user_id),
            "deleted_at": None
        })

        if not task:
            return None

        tasks_collection.update_one(
            {"_id": object_id},
            {
                "$set": {
                    "deleted_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )

        return task