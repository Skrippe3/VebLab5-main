from flask import Blueprint, g, jsonify, request

from app.middleware.auth_middleware import auth_required
from app.models.task import task_to_dict
from app.services.task_service import TaskService

task_bp = Blueprint("tasks", __name__)


@task_bp.route("/tasks", methods=["GET"])
@auth_required
def get_tasks():
    """
    Получение списка задач текущего пользователя.
    ---
    tags:
      - Tasks
    security:
      - cookieAuth: []
    parameters:
      - in: query
        name: page
        required: false
        type: integer
        default: 1
        description: Номер страницы
      - in: query
        name: limit
        required: false
        type: integer
        default: 10
        description: Количество задач на странице
    responses:
      200:
        description: Список задач пользователя с пагинацией
        schema:
          $ref: '#/definitions/TasksListResponse'
      400:
        description: Некорректные параметры пагинации
        schema:
          $ref: '#/definitions/ErrorResponse'
      401:
        description: Пользователь не авторизован
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 10))
    except ValueError:
        return jsonify({"message": "Invalid pagination params"}), 400

    if page < 1 or limit < 1:
        return jsonify({"message": "Invalid pagination params"}), 400

    result = TaskService.get_all(str(g.current_user["_id"]), page, limit)

    return jsonify(result), 200


@task_bp.route("/tasks", methods=["POST"])
@auth_required
def create_task():
    """
    Создание задачи текущего пользователя.
    ---
    tags:
      - Tasks
    security:
      - cookieAuth: []
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/TaskRequest'
    responses:
      201:
        description: Задача успешно создана
        schema:
          $ref: '#/definitions/TaskResponse'
      400:
        description: Ошибка валидации тела запроса
        schema:
          $ref: '#/definitions/ErrorResponse'
      401:
        description: Пользователь не авторизован
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"message": "JSON body is required"}), 400

    if not data.get("title") or not data.get("description"):
        return jsonify({"message": "Title and description are required"}), 400

    task = TaskService.create(str(g.current_user["_id"]), data)

    return jsonify(task_to_dict(task)), 201


@task_bp.route("/tasks/<task_id>", methods=["DELETE"])
@auth_required
def delete_task(task_id):
    """
    Soft delete задачи текущего пользователя.
    ---
    tags:
      - Tasks
    security:
      - cookieAuth: []
    parameters:
      - in: path
        name: task_id
        required: true
        type: string
        description: ID задачи MongoDB ObjectId
    responses:
      204:
        description: Задача успешно удалена через soft delete
      401:
        description: Пользователь не авторизован
        schema:
          $ref: '#/definitions/ErrorResponse'
      404:
        description: Задача не найдена или принадлежит другому пользователю
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    task = TaskService.soft_delete(str(g.current_user["_id"]), task_id)

    if not task:
        return jsonify({"message": "Not found"}), 404

    return "", 204