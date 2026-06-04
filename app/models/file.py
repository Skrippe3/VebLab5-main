from datetime import datetime
from uuid import uuid4


def create_file_document(user_id, original_name, object_key, size, mimetype, bucket):
    now = datetime.utcnow()

    return {
        "_id": str(uuid4()),
        "user_id": str(user_id),
        "original_name": original_name,
        "object_key": object_key,
        "size": int(size),
        "mimetype": mimetype,
        "bucket": bucket,
        "created_at": now,
        "updated_at": now,
        "deleted_at": None,
    }


def file_to_response(file_doc):
    return {
        "id": file_doc["_id"],
        "originalName": file_doc.get("original_name"),
        "size": file_doc.get("size"),
        "mimetype": file_doc.get("mimetype"),
        "createdAt": file_doc.get("created_at").isoformat(),
        "updatedAt": file_doc.get("updated_at").isoformat(),
        "url": f"/files/{file_doc['_id']}",
    }


def file_to_cache(file_doc):
    return {
        "id": file_doc["_id"],
        "user_id": file_doc.get("user_id"),
        "original_name": file_doc.get("original_name"),
        "object_key": file_doc.get("object_key"),
        "size": file_doc.get("size"),
        "mimetype": file_doc.get("mimetype"),
        "bucket": file_doc.get("bucket"),
        "created_at": file_doc.get("created_at").isoformat(),
        "updated_at": file_doc.get("updated_at").isoformat(),
        "deleted_at": file_doc.get("deleted_at").isoformat() if file_doc.get("deleted_at") else None,
    }
