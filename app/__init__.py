import os

from dotenv import load_dotenv
from flask import Flask, jsonify
from werkzeug.exceptions import RequestEntityTooLarge

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_FILE_SIZE", "10485760"))

    @app.errorhandler(RequestEntityTooLarge)
    def handle_file_too_large(error):
        return jsonify({"message": "File is too large"}), 413

    from app.database.mongo import init_indexes
    init_indexes()

    from app.routes.auth_routes import auth_bp
    from app.routes.file_routes import file_bp
    from app.routes.profile_routes import profile_bp
    from app.routes.task_routes import task_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(file_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(task_bp)

    from app.swagger import setup_swagger
    setup_swagger(app)

    return app
