"""Módulo de lógica y modelos de votación."""
from .models import RespuestaInstancia, ResultadoVotacion, VeredictoVotacion
from .voter import VotadorMayoria
from .evaluator import EvaluadorVotacion

__all__ = [
    "RespuestaInstancia",
    "ResultadoVotacion",
    "VeredictoVotacion",
    "VotadorMayoria",
    "EvaluadorVotacion",
]
