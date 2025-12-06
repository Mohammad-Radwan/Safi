from flask import Flask
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager

from app.logging_config import configure_logging
from config import DevelopmentConfig

from .routes.auth import auth_bp
from .routes.groups import groups_bp
from .routes.users import users_bp

bcrypt = Bcrypt()
jwt = JWTManager()


def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # register blueprints
    app.register_blueprint(users_bp)
    app.register_blueprint(groups_bp)
    app.register_blueprint(auth_bp)

    configure_logging(app)
    app.logger.info("Starting up the application...")

    return app
