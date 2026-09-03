import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


class Config:

    FLASK_ENV: str = os.getenv("FLASK_ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
    PORT: int = int(os.getenv("PORT", "5000"))

    _instances_raw: str = os.getenv(
        "SERVICE_INSTANCES",
        "http://localhost:8001,http://localhost:8002,http://localhost:8003"
    )
    SERVICE_INSTANCES: List[str] = [
        inst.strip() for inst in _instances_raw.split(",") if inst.strip()
    ]

    VOTING_TIMEOUT_SECONDS: float = float(os.getenv("VOTING_TIMEOUT_SECONDS", "3.0"))

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "llave-secreta-jwt-componente-votacion-2026-super-segura-y-robusta")


