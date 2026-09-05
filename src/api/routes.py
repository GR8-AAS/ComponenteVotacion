import logging
from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required

from ..voting.models import VeredictoVotacion
from ..voting.voter import VotadorMayoria
from ..voting.evaluator import EvaluadorVotacion

registrador = logging.getLogger(__name__)

api_bp = Blueprint("api_votacion", __name__)


@api_bp.route("/", methods=["GET"])
def inicio():
    """Ruta raíz para verificar que el servicio está activo desde el navegador."""
    return jsonify({
        "servicio": "Componente de Estrategia de Votación",
        "estado": "activo",
        "version": "1.0.0",
        "endpoint_principal": "POST /api/v1/execute (requiere Authorization: Bearer <token>)",
    }), 200


@api_bp.route("/api/v1/execute", methods=["POST"])
@jwt_required()
async def ejecutar_votacion():
    cuerpo = request.get_json(silent=True) or {}

    metodo = cuerpo.get("metodo") or cuerpo.get("method", "POST")
    ruta = cuerpo.get("ruta") or cuerpo.get("path", "")
    carga_util = cuerpo.get("carga_util") if "carga_util" in cuerpo else cuerpo.get("payload")
    encabezados = cuerpo.get("encabezados") or cuerpo.get("headers")
    parametros = cuerpo.get("parametros") or cuerpo.get("params")
    instancias_personalizadas = cuerpo.get("instancias") or cuerpo.get("instances")

    configuracion = current_app.config
    instancias = instancias_personalizadas or configuracion.get("SERVICE_INSTANCES", [])
    segundos_timeout = configuracion.get("VOTING_TIMEOUT_SECONDS", 3.0)

    votador = VotadorMayoria()
    evaluador = EvaluadorVotacion(
        urls_instancias=instancias,
        segundos_timeout=segundos_timeout,
        votador=votador,
    )

    resultado = await evaluador.evaluar(
        metodo=metodo,
        ruta=ruta,
        carga_util=carga_util,
        encabezados=encabezados,
        parametros=parametros,
    )

    # Determinar código HTTP de respuesta según el veredicto
    codigo_estado_http = 200
    if resultado.veredicto == VeredictoVotacion.TODAS_FALLIDAS:
        codigo_estado_http = 502  # Bad Gateway (todas las réplicas fallaron)
    elif resultado.veredicto in (VeredictoVotacion.SIN_CONSENSO, VeredictoVotacion.EMPATE):
        codigo_estado_http = 409  # Conflict (no hay acuerdo o empate)

    return jsonify(resultado.model_dump()), codigo_estado_http
