from flask import Blueprint, g, jsonify, request

from app.middleware.auth_middleware import auth_required
from app.services.profile_service import ProfileService

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/profile", methods=["GET"])
@auth_required
def get_profile():
    """
    Get current user profile.
    ---
    tags:
      - Profile
    security:
      - cookieAuth: []
    responses:
      200:
        description: Current user profile
        schema:
          $ref: '#/definitions/ProfileResponse'
      401:
        description: Unauthorized
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    return jsonify(ProfileService.get_profile(g.current_user)), 200


@profile_bp.route("/profile", methods=["POST"])
@auth_required
def update_profile():
    """
    Update current user profile and optional avatar file UUID.
    ---
    tags:
      - Profile
    security:
      - cookieAuth: []
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/ProfileUpdateRequest'
    responses:
      200:
        description: Updated profile
        schema:
          $ref: '#/definitions/ProfileResponse'
      400:
        description: Invalid request
        schema:
          $ref: '#/definitions/ErrorResponse'
      401:
        description: Unauthorized
        schema:
          $ref: '#/definitions/ErrorResponse'
      403:
        description: Avatar file belongs to another user or does not exist
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    data = request.get_json(silent=True)

    if data is None:
        return jsonify({"message": "JSON body is required"}), 400

    try:
        profile = ProfileService.update_profile(g.current_user, data)
    except PermissionError as error:
        return jsonify({"message": str(error)}), 403
    except ValueError as error:
        return jsonify({"message": str(error)}), 400

    return jsonify(profile), 200
