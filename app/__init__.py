from dotenv import load_dotenv
from flask import Flask

load_dotenv()


def create_app():
    app = Flask(__name__)

    from app.database.mongo import init_indexes
    init_indexes()

    from app.routes.auth_routes import auth_bp
    from app.routes.task_routes import task_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(task_bp)

    from app.swagger import setup_swagger
    setup_swagger(app)

    return app