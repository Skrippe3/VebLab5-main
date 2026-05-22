import os
from datetime import datetime
from pathlib import PurePosixPath
from uuid import uuid4

from minio import Minio
from minio.error import S3Error
from werkzeug.utils import secure_filename

from app.database.mongo import files_collection
from app.models.file import create_file_document, file_to_cache
from app.services.cache_service import CacheService


class SizeLimitExceeded(ValueError):
    pass


class SizeLimitStream:
    def __init__(self, stream, max_size):
        self.stream = stream
        self.max_size = max_size
        self.bytes_read = 0

    def read(self, size=-1):
        chunk = self.stream.read(size)
        self.bytes_read += len(chunk)

        if self.bytes_read > self.max_size:
            raise SizeLimitExceeded("File is too large")

        return chunk


class StorageService:
    MINIO_PART_SIZE = 10 * 1024 * 1024

    @staticmethod
    def max_file_size():
        return int(os.getenv("MAX_FILE_SIZE", "10485760"))

    @staticmethod
    def allowed_mimetypes():
        raw_value = os.getenv(
            "ALLOWED_FILE_MIMETYPES",
            "image/png,image/jpeg,image/jpg,application/pdf,text/plain",
        )
        return {item.strip() for item in raw_value.split(",") if item.strip()}

    @staticmethod
    def avatar_mimetypes():
        return {"image/png", "image/jpeg", "image/jpg"}

    @staticmethod
    def bucket():
        return os.getenv("MINIO_BUCKET", "wp-labs-files")

    @staticmethod
    def client():
        return Minio(
            os.getenv("MINIO_ENDPOINT", "minio:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY"),
            secret_key=os.getenv("MINIO_SECRET_KEY"),
            secure=os.getenv("MINIO_USE_SSL", "false").lower() == "true",
        )

    @classmethod
    def ensure_bucket(cls):
        client = cls.client()
        bucket = cls.bucket()

        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)

        return bucket

    @classmethod
    def upload_file(cls, stream, filename, mimetype, user_id):
        if mimetype not in cls.allowed_mimetypes():
            raise ValueError("Unsupported file type")

        original_name = filename or "file"
        safe_name = secure_filename(original_name) or "file"
        object_key = str(PurePosixPath(str(user_id), str(uuid4()), safe_name))
        bucket = cls.ensure_bucket()
        limited_stream = SizeLimitStream(stream, cls.max_file_size())

        try:
            cls.client().put_object(
                bucket,
                object_key,
                limited_stream,
                length=-1,
                part_size=cls.MINIO_PART_SIZE,
                content_type=mimetype,
            )
        except SizeLimitExceeded:
            try:
                cls.client().remove_object(bucket, object_key)
            except Exception:
                pass
            raise

        file_doc = create_file_document(
            user_id=user_id,
            original_name=original_name,
            object_key=object_key,
            size=limited_stream.bytes_read,
            mimetype=mimetype,
            bucket=bucket,
        )

        files_collection.insert_one(file_doc)
        CacheService.delete(CacheService.file_meta_key(file_doc["_id"]))

        return file_doc

    @classmethod
    def get_file_stream(cls, object_key):
        return cls.client().get_object(cls.bucket(), object_key)

    @classmethod
    def delete_file(cls, object_key):
        cls.client().remove_object(cls.bucket(), object_key)

    @classmethod
    def file_exists(cls, object_key):
        try:
            cls.client().stat_object(cls.bucket(), object_key)
            return True
        except S3Error as error:
            if error.code == "NoSuchKey":
                return False
            raise

    @staticmethod
    def get_owned_file_meta(user_id, file_id):
        cache_key = CacheService.file_meta_key(file_id)
        cached = CacheService.get_json(cache_key)

        if cached and cached.get("user_id") == str(user_id) and not cached.get("deleted_at"):
            return cached

        file_doc = files_collection.find_one(
            {
                "_id": file_id,
                "user_id": str(user_id),
                "deleted_at": None,
            }
        )

        if not file_doc:
            return None

        meta = file_to_cache(file_doc)
        CacheService.set_json(cache_key, meta, CacheService.FILE_META_TTL_SECONDS)

        return meta

    @staticmethod
    def soft_delete_owned_file(user_id, file_id):
        file_doc = files_collection.find_one(
            {
                "_id": file_id,
                "user_id": str(user_id),
                "deleted_at": None,
            }
        )

        if not file_doc:
            return None

        now = datetime.utcnow()
        files_collection.update_one(
            {"_id": file_id},
            {"$set": {"deleted_at": now, "updated_at": now}},
        )
        CacheService.delete(CacheService.file_meta_key(file_id))

        try:
            StorageService.delete_file(file_doc["object_key"])
        except S3Error:
            pass

        return file_doc
