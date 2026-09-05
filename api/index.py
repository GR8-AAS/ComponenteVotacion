import sys
import os
import urllib.parse

DIRECTORIO_RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if DIRECTORIO_RAIZ not in sys.path:
    sys.path.insert(0, DIRECTORIO_RAIZ)

from src.app import app


class MiddlewareRutasVercel:
    """Restaura el PATH_INFO original capturado por la regla de rewrite de Vercel."""

    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        query_string = environ.get("QUERY_STRING", "")
        if "__vercel_path" in query_string:
            parametros = urllib.parse.parse_qs(query_string, keep_blank_values=True)
            if "__vercel_path" in parametros:
                ruta = parametros.pop("__vercel_path")[0] or "/"
                if not ruta.startswith("/"):
                    ruta = "/" + ruta
                environ["PATH_INFO"] = ruta
                environ["QUERY_STRING"] = urllib.parse.urlencode(parametros, doseq=True)

        return self.wsgi_app(environ, start_response)


app.wsgi_app = MiddlewareRutasVercel(app.wsgi_app)
