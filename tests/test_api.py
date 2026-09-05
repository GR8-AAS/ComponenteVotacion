import pytest
from unittest.mock import patch, MagicMock
from flask_jwt_extended import create_access_token
from src.app import create_app
from src.config import Config


class ConfiguracionPruebas(Config):
    TESTING = True
    SERVICE_INSTANCES = [
        "http://replica1:8000",
        "http://replica2:8000",
        "http://replica3:8000",
    ]
    VOTING_TIMEOUT_SECONDS = 1.0
    JWT_SECRET_KEY = "clave-de-prueba-jwt-super-segura-de-mas-de-32-bytes"



@pytest.fixture
def aplicacion():
    app = create_app(ConfiguracionPruebas)
    return app


@pytest.fixture
def cliente(aplicacion):
    with aplicacion.test_client() as cliente_prueba:
        yield cliente_prueba


@pytest.fixture
def token_autorizacion(aplicacion):
    with aplicacion.app_context():
        token = create_access_token(identity="usuario_prueba")
        return {"Authorization": f"Bearer {token}"}


def test_inicio_ruta_raiz(cliente):
    respuesta = cliente.get("/")
    assert respuesta.status_code == 200
    datos = respuesta.get_json()
    assert datos["estado"] == "activo"
    assert datos["servicio"] == "Componente de Estrategia de Votación"


def test_ejecutar_sin_token_retorna_401(cliente):
    respuesta = cliente.post(
        "/api/v1/execute",
        json={"metodo": "POST", "ruta": "/computar", "carga_util": {"entrada": 5}},
    )
    assert respuesta.status_code == 401


def test_ejecutar_con_token_llave_invalida_es_rechazado(cliente):
    import jwt
    # Token generado con una clave distinta a JWT_SECRET_KEY
    token_falso = jwt.encode({"sub": "atacante"}, "otra-llave-completamente-distinta-123456", algorithm="HS256")
    respuesta = cliente.post(
        "/api/v1/execute",
        headers={"Authorization": f"Bearer {token_falso}"},
        json={"metodo": "POST", "ruta": "/computar", "carga_util": {"entrada": 5}},
    )
    assert respuesta.status_code == 422
    assert "Signature verification failed" in respuesta.get_json()["msg"]




@patch("httpx.AsyncClient.request")
def test_flujo_ejecutar_consenso(mock_peticion, cliente, token_autorizacion):
    async def efecto_secundario(method, url, **kwargs):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        if "replica3" in url:
            mock_resp.json.return_value = {"total": 50}
        else:
            mock_resp.json.return_value = {"total": 100}
        return mock_resp

    mock_peticion.side_effect = efecto_secundario

    respuesta = cliente.post(
        "/api/v1/execute",
        headers=token_autorizacion,
        json={"metodo": "POST", "ruta": "/computar", "carga_util": {"entrada": 5}},
    )

    assert respuesta.status_code == 200
    datos_json = respuesta.get_json()
    assert datos_json["veredicto"] == "CONSENSO_ALCANZADO"
    assert datos_json["datos_consenso"] == {"total": 100}
    assert "http://replica3:8000" in datos_json["instancias_disidentes"]
    assert datos_json["votos_consenso"] == 2
    assert datos_json["quorum_requerido"] == 2


@patch("httpx.AsyncClient.request")
def test_flujo_ejecutar_todas_fallidas(mock_peticion, cliente, token_autorizacion):
    async def efecto_secundario(method, url, **kwargs):
        raise Exception("Error de red simulado")

    mock_peticion.side_effect = efecto_secundario

    respuesta = cliente.post(
        "/api/v1/execute",
        headers=token_autorizacion,
        json={"metodo": "GET", "ruta": "/estado"},
    )

    assert respuesta.status_code == 502
    datos_json = respuesta.get_json()
    assert datos_json["veredicto"] == "TODAS_FALLIDAS"
    assert len(datos_json["instancias_fallidas"]) == 3


@patch("httpx.AsyncClient.request")
def test_flujo_ejecutar_con_instancias_personalizadas(mock_peticion, cliente, token_autorizacion):
    async def efecto_secundario(method, url, **kwargs):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"estado": "OK"}
        return mock_resp

    mock_peticion.side_effect = efecto_secundario

    instancias_personalizadas = ["http://custom1:9000", "http://custom2:9000"]
    respuesta = cliente.post(
        "/api/v1/execute",
        headers=token_autorizacion,
        json={
            "metodo": "POST",
            "ruta": "/trabajar",
            "carga_util": {"dato": 123},
            "instancias": instancias_personalizadas,
        },
    )

    assert respuesta.status_code == 200
    datos_json = respuesta.get_json()
    assert datos_json["veredicto"] == "CONSENSO_ALCANZADO"
    assert datos_json["total_instancias"] == 2
    assert datos_json["quorum_requerido"] == 2
