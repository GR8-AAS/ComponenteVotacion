import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuración global de la aplicación y del componente de votación."""

    FLASK_ENV: str = os.getenv("FLASK_ENV") or "development"
    DEBUG: bool = (os.getenv("DEBUG") or "True").lower() in ("true", "1", "yes")
    PORT: int = int(os.getenv("PORT") or "5000")

    _instances_raw: str = os.getenv("SERVICE_INSTANCES") or "http://localhost:8001,http://localhost:8002,http://localhost:8003"
    SERVICE_INSTANCES: List[str] = [
        inst.strip() for inst in _instances_raw.split(",") if inst.strip()
    ]

    VOTING_TIMEOUT_SECONDS: float = float(os.getenv("VOTING_TIMEOUT_SECONDS") or "3.0")

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY") or "llave-secreta-jwt-componente-votacion-2026-super-segura-y-robusta"
