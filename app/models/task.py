from datetime import datetime


def task_to_dict(task):
    return {
        "id": str(task["_id"]),
        "title": task.get("title"),
        "description": task.get("description"),
        "status": task.get("status"),
        "createdAt": task.get("created_at").isoformat(),
        "updatedAt": task.get("updated_at").isoformat(),
    }


def create_task_document(user_id, title, description, status="new"):
    now = datetime.utcnow()

    return {
        "user_id": user_id,
        "title": title,
        "description": description,
        "status": status,
        "created_at": now,
        "updated_at": now,
        "deleted_at": None,
    }