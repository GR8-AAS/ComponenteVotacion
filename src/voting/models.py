from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class VeredictoVotacion(str, Enum):
    CONSENSO_ALCANZADO = "CONSENSO_ALCANZADO"
    SIN_CONSENSO = "SIN_CONSENSO"
    EMPATE = "EMPATE"
    TODAS_FALLIDAS = "TODAS_FALLIDAS"


class RespuestaInstancia(BaseModel):
    id_instancia: str
    codigo_estado: Optional[int] = None
    datos: Optional[Any] = None
    latencia_ms: float = 0.0
    es_exitosa: bool = False
    error: Optional[str] = None


class ResultadoVotacion(BaseModel):
    veredicto: VeredictoVotacion
    datos_consenso: Optional[Any] = None
    codigo_estado_consenso: Optional[int] = None
    total_instancias: int = 0
    votos_consenso: int = 0
    quorum_requerido: int = 0
    instancias_exitosas: List[str] = Field(default_factory=list)
    instancias_fallidas: List[str] = Field(default_factory=list)
    instancias_disidentes: List[str] = Field(default_factory=list)
    distribucion_votos: Dict[str, int] = Field(default_factory=dict)
    detalles: List[RespuestaInstancia] = Field(default_factory=list)
