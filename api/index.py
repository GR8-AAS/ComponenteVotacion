import sys
import os

DIRECTORIO_RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if DIRECTORIO_RAIZ not in sys.path:
    sys.path.insert(0, DIRECTORIO_RAIZ)

from src.app import app
