"""Punto de entrada WSGI para servidores web y Vercel."""
from src.app import app

if __name__ == "__main__":
    from src.config import Config
    app.run(
        host="0.0.0.0",
        port=Config.PORT,
        debug=Config.DEBUG,
    )
