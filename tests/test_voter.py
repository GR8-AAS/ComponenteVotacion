import pytest
from src.voting.models import RespuestaInstancia, VeredictoVotacion
from src.voting.voter import VotadorMayoria


def test_consenso_unanime():
    votador = VotadorMayoria()
    respuestas = [
        RespuestaInstancia(id_instancia="inst-1", codigo_estado=200, datos={"val": 10}, es_exitosa=True),
        RespuestaInstancia(id_instancia="inst-2", codigo_estado=200, datos={"val": 10}, es_exitosa=True),
        RespuestaInstancia(id_instancia="inst-3", codigo_estado=200, datos={"val": 10}, es_exitosa=True),
    ]

    resultado = votador.votar(respuestas)

    assert resultado.veredicto == VeredictoVotacion.CONSENSO_ALCANZADO
    assert resultado.datos_consenso == {"val": 10}
    assert resultado.votos_consenso == 3
    assert len(resultado.instancias_disidentes) == 0
    assert len(resultado.instancias_fallidas) == 0
    assert len(resultado.instancias_exitosas) == 3


def test_mayoria_con_instancia_disidente():
    votador = VotadorMayoria()
    respuestas = [
        RespuestaInstancia(id_instancia="inst-1", codigo_estado=200, datos={"estado": "OK", "codigo": 1}, es_exitosa=True),
        RespuestaInstancia(id_instancia="inst-2", codigo_estado=200, datos={"estado": "OK", "codigo": 1}, es_exitosa=True),
        RespuestaInstancia(id_instancia="inst-3", codigo_estado=200, datos={"estado": "ERROR", "codigo": 99}, es_exitosa=True),
    ]

    resultado = votador.votar(respuestas)

    assert resultado.veredicto == VeredictoVotacion.CONSENSO_ALCANZADO
    assert resultado.datos_consenso == {"estado": "OK", "codigo": 1}
    assert resultado.votos_consenso == 2
    assert resultado.instancias_disidentes == ["inst-3"]
    assert len(resultado.instancias_fallidas) == 0


def test_mayoria_con_instancia_fallida():
    votador = VotadorMayoria()
    respuestas = [
        RespuestaInstancia(id_instancia="inst-1", codigo_estado=200, datos={"estado": "OK"}, es_exitosa=True),
        RespuestaInstancia(id_instancia="inst-2", codigo_estado=200, datos={"estado": "OK"}, es_exitosa=True),
        RespuestaInstancia(id_instancia="inst-3", codigo_estado=500, es_exitosa=False, error="Internal Server Error"),
    ]

    resultado = votador.votar(respuestas)

    assert resultado.veredicto == VeredictoVotacion.CONSENSO_ALCANZADO
    assert resultado.datos_consenso == {"estado": "OK"}
    assert resultado.votos_consenso == 2
    assert resultado.instancias_fallidas == ["inst-3"]
    assert len(resultado.instancias_disidentes) == 0


def test_veredicto_empate():
    votador = VotadorMayoria()
    respuestas = [
        RespuestaInstancia(id_instancia="inst-1", codigo_estado=200, datos={"opcion": "A"}, es_exitosa=True),
        RespuestaInstancia(id_instancia="inst-2", codigo_estado=200, datos={"opcion": "A"}, es_exitosa=True),
        RespuestaInstancia(id_instancia="inst-3", codigo_estado=200, datos={"opcion": "B"}, es_exitosa=True),
        RespuestaInstancia(id_instancia="inst-4", codigo_estado=200, datos={"opcion": "B"}, es_exitosa=True),
    ]

    resultado = votador.votar(respuestas)

    assert resultado.veredicto == VeredictoVotacion.EMPATE
    assert resultado.datos_consenso is None


def test_sin_consenso_con_votos_dispersos():
    votador = VotadorMayoria()
    respuestas = [
        RespuestaInstancia(id_instancia="inst-1", codigo_estado=200, datos={"ans": 1}, es_exitosa=True),
        RespuestaInstancia(id_instancia="inst-2", codigo_estado=200, datos={"ans": 1}, es_exitosa=True),
        RespuestaInstancia(id_instancia="inst-3", codigo_estado=200, datos={"ans": 2}, es_exitosa=True),
        RespuestaInstancia(id_instancia="inst-4", codigo_estado=200, datos={"ans": 3}, es_exitosa=True),
        RespuestaInstancia(id_instancia="inst-5", codigo_estado=200, datos={"ans": 4}, es_exitosa=True),
    ]

    resultado = votador.votar(respuestas)

    assert resultado.veredicto == VeredictoVotacion.SIN_CONSENSO
    assert resultado.votos_consenso == 2
    assert resultado.quorum_requerido == 3


def test_todas_fallidas():
    votador = VotadorMayoria()
    respuestas = [
        RespuestaInstancia(id_instancia="inst-1", codigo_estado=503, es_exitosa=False, error="Service Unavailable"),
        RespuestaInstancia(id_instancia="inst-2", codigo_estado=500, es_exitosa=False, error="Crash"),
        RespuestaInstancia(id_instancia="inst-3", es_exitosa=False, error="Timeout"),
    ]

    resultado = votador.votar(respuestas)

    assert resultado.veredicto == VeredictoVotacion.TODAS_FALLIDAS
    assert len(resultado.instancias_fallidas) == 3
    assert resultado.datos_consenso is None


def test_quorum_dinamico_cinco_replicas():
    votador = VotadorMayoria()
    respuestas = [
        RespuestaInstancia(id_instancia="inst-1", codigo_estado=200, datos={"ok": True}, es_exitosa=True),
        RespuestaInstancia(id_instancia="inst-2", codigo_estado=200, datos={"ok": True}, es_exitosa=True),
        RespuestaInstancia(id_instancia="inst-3", codigo_estado=200, datos={"ok": True}, es_exitosa=True),
        RespuestaInstancia(id_instancia="inst-4", codigo_estado=200, datos={"ok": False}, es_exitosa=True),
        RespuestaInstancia(id_instancia="inst-5", codigo_estado=200, datos={"ok": False}, es_exitosa=True),
    ]

    resultado = votador.votar(respuestas)
    assert resultado.veredicto == VeredictoVotacion.CONSENSO_ALCANZADO
    assert resultado.quorum_requerido == 3
    assert resultado.votos_consenso == 3
    assert resultado.datos_consenso == {"ok": True}
    assert resultado.instancias_disidentes == ["inst-4", "inst-5"]
