from urllib.parse import quote

from flask import Blueprint, Response, g, jsonify, request, stream_with_context
from werkzeug.exceptions import RequestEntityTooLarge

from app.middleware.auth_middleware import auth_required
from app.models.file import file_to_response
from app.services.storage_service import SizeLimitExceeded, StorageService

file_bp = Blueprint("files", __name__)


@file_bp.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(error):
    return jsonify({"message": "File is too large"}), 413


@file_bp.route("/files", methods=["POST"])
@auth_required
def upload_file():
    """
    Upload a file to MinIO using multipart/form-data.
    ---
    tags:
      - Files
    security:
      - cookieAuth: []
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: file
        type: file
        required: true
        description: File binary stream
    responses:
      201:
        description: File uploaded
        schema:
          $ref: '#/definitions/FileResponse'
      400:
        description: Invalid upload request
        schema:
          $ref: '#/definitions/ErrorResponse'
      401:
        description: Unauthorized
        schema:
          $ref: '#/definitions/ErrorResponse'
      413:
        description: File is too large
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    uploaded_file = request.files.get("file")

    if not uploaded_file:
        return jsonify({"message": "File is required"}), 400

    try:
        file_doc = StorageService.upload_file(
            stream=uploaded_file.stream,
            filename=uploaded_file.filename,
            mimetype=uploaded_file.mimetype,
            user_id=str(g.current_user["_id"]),
        )
    except SizeLimitExceeded:
        return jsonify({"message": "File is too large"}), 413
    except ValueError as error:
        return jsonify({"message": str(error)}), 400

    return jsonify(file_to_response(file_doc)), 201


@file_bp.route("/files/<file_id>", methods=["GET"])
@auth_required
def download_file(file_id):
    """
    Download an owned file by UUID.
    ---
    tags:
      - Files
    security:
      - cookieAuth: []
    parameters:
      - in: path
        name: file_id
        required: true
        type: string
        format: uuid
    responses:
      200:
        description: File stream
      401:
        description: Unauthorized
        schema:
          $ref: '#/definitions/ErrorResponse'
      404:
        description: File not found
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    file_meta = StorageService.get_owned_file_meta(str(g.current_user["_id"]), file_id)

    if not file_meta:
        return jsonify({"message": "Not found"}), 404

    storage_stream = StorageService.get_file_stream(file_meta["object_key"])

    def generate():
        try:
            for chunk in storage_stream.stream(32 * 1024):
                yield chunk
        finally:
            storage_stream.close()
            storage_stream.release_conn()

    response = Response(
        stream_with_context(generate()),
        mimetype=file_meta["mimetype"],
        direct_passthrough=True,
    )
    response.headers["Content-Type"] = file_meta["mimetype"]
    response.headers["Content-Length"] = str(file_meta["size"])
    response.headers["Content-Disposition"] = (
        "attachment; filename*=UTF-8''"
        + quote(file_meta["original_name"])
    )

    return response


@file_bp.route("/files/<file_id>", methods=["DELETE"])
@auth_required
def delete_file(file_id):
    """
    Soft delete an owned file and remove the MinIO object.
    ---
    tags:
      - Files
    security:
      - cookieAuth: []
    parameters:
      - in: path
        name: file_id
        required: true
        type: string
        format: uuid
    responses:
      204:
        description: File deleted
      401:
        description: Unauthorized
        schema:
          $ref: '#/definitions/ErrorResponse'
      404:
        description: File not found
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    file_doc = StorageService.soft_delete_owned_file(str(g.current_user["_id"]), file_id)

    if not file_doc:
        return jsonify({"message": "Not found"}), 404

    return "", 204
