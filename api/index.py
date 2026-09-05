import sys
import os

# Asegurar que el directorio raíz del proyecto esté en el sys.path para Vercel
DIRECTORIO_RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if DIRECTORIO_RAIZ not in sys.path:
    sys.path.insert(0, DIRECTORIO_RAIZ)

from src.app import create_app
from src.config import Config

app = create_app(Config)
