import logging
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_restful import Api

from .config import Config
from .api.routes import api_bp


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    
    CORS(app)
    JWTManager(app)
    Api(app)

    
    app.register_blueprint(api_bp)

    return app


app = create_app(Config)
