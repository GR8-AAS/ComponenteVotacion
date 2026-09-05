import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from .config import Config
from .api.routes import api_bp


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    logging.basicConfig(
        level=logging.DEBUG if app.config.get("DEBUG") else logging.INFO,
        format="[%(asctime)s] [%(levelname)s] in %(module)s: %(message)s",
    )

    CORS(app)
    JWTManager(app)

    app.register_blueprint(api_bp)

    @app.errorhandler(404)
    def manejar_404(e):
        environ_safe = {
            k: str(v)
            for k, v in request.environ.items()
            if not k.startswith("wsgi.") and k not in ("JWT_SECRET_KEY",)
        }
        return jsonify({
            "error": "Ruta no encontrada",
            "request_path": request.path,
            "environ": environ_safe,
        }), 404

    return app


app = create_app(Config)
