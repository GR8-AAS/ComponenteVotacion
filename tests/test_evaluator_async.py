import pytest
from unittest.mock import MagicMock, patch
from src.voting.evaluator import EvaluadorVotacion
from src.voting.models import VeredictoVotacion


@pytest.mark.asyncio
async def test_evaluador_evaluar_asincrono():
    evaluador = EvaluadorVotacion(
        urls_instancias=["http://inst1:8000", "http://inst2:8000", "http://inst3:8000"],
        segundos_timeout=1.0,
    )

    with patch("httpx.AsyncClient.request") as mock_request:
        async def mock_respuesta(method, url, **kwargs):
            respuesta = MagicMock()
            respuesta.status_code = 200
            if "inst3" in url:
                respuesta.json.return_value = {"respuesta": "NO"}
            else:
                respuesta.json.return_value = {"respuesta": "SI"}
            return respuesta

        mock_request.side_effect = mock_respuesta

        resultado = await evaluador.evaluar(
            metodo="POST",
            ruta="/procesar",
            carga_util={"id": 1},
        )

        assert resultado.veredicto == VeredictoVotacion.CONSENSO_ALCANZADO
        assert resultado.datos_consenso == {"respuesta": "SI"}
        assert resultado.votos_consenso == 2
        assert resultado.instancias_disidentes == ["http://inst3:8000"]
