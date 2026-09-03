import asyncio
import logging
import time
from typing import Any, Dict, List, Optional
import httpx

from .models import RespuestaInstancia, ResultadoVotacion
from .voter import VotadorMayoria

registrador = logging.getLogger(__name__)


class EvaluadorVotacion:

    def __init__(
        self,
        urls_instancias: List[str],
        segundos_timeout: float = 3.0,
        votador: Optional[VotadorMayoria] = None,
    ):
        self.urls_instancias = urls_instancias
        self.segundos_timeout = segundos_timeout
        self.votador = votador or VotadorMayoria()

    async def _llamar_instancia(
        self,
        cliente: httpx.AsyncClient,
        url: str,
        metodo: str = "POST",
        ruta: str = "",
        carga_util: Optional[Any] = None,
        encabezados: Optional[Dict[str, str]] = None,
        parametros: Optional[Dict[str, Any]] = None,
    ) -> RespuestaInstancia:
        url_destino = f"{url.rstrip('/')}/{ruta.lstrip('/')}" if ruta else url
        tiempo_inicio = time.perf_counter()

        try:
            respuesta = await cliente.request(
                method=metodo.upper(),
                url=url_destino,
                json=carga_util,
                params=parametros,
                headers=encabezados,
            )
            ms_transcurridos = (time.perf_counter() - tiempo_inicio) * 1000

            try:
                datos = respuesta.json()
            except Exception:
                datos = respuesta.text

            es_exitosa = 200 <= respuesta.status_code < 300

            return RespuestaInstancia(
                id_instancia=url,
                codigo_estado=respuesta.status_code,
                datos=datos,
                latencia_ms=round(ms_transcurridos, 2),
                es_exitosa=es_exitosa,
                error=None if es_exitosa else f"HTTP {respuesta.status_code}: {respuesta.text[:100]}",
            )

        except httpx.TimeoutException:
            ms_transcurridos = (time.perf_counter() - tiempo_inicio) * 1000
            registrador.warning("Timeout al contactar instancia: %s", url)
            return RespuestaInstancia(
                id_instancia=url,
                latencia_ms=round(ms_transcurridos, 2),
                es_exitosa=False,
                error="Timeout al conectar con la instancia",
            )

        except httpx.RequestError as error_peticion:
            ms_transcurridos = (time.perf_counter() - tiempo_inicio) * 1000
            registrador.warning("Error al contactar instancia %s: %s", url, str(error_peticion))
            return RespuestaInstancia(
                id_instancia=url,
                latencia_ms=round(ms_transcurridos, 2),
                es_exitosa=False,
                error=f"Error de conexión: {str(error_peticion)}",
            )

        except Exception as error_inesperado:
            ms_transcurridos = (time.perf_counter() - tiempo_inicio) * 1000
            registrador.error("Error inesperado al contactar réplica %s: %s", url, str(error_inesperado))
            return RespuestaInstancia(
                id_instancia=url,
                latencia_ms=round(ms_transcurridos, 2),
                es_exitosa=False,
                error=f"Error inesperado: {str(error_inesperado)}",
            )

    async def evaluar(
        self,
        metodo: str = "POST",
        ruta: str = "",
        carga_util: Optional[Any] = None,
        encabezados: Optional[Dict[str, str]] = None,
        parametros: Optional[Dict[str, Any]] = None,
        instancias_personalizadas: Optional[List[str]] = None,
    ) -> ResultadoVotacion:
        instancias_objetivo = instancias_personalizadas or self.urls_instancias

        if not instancias_objetivo:
            registrador.error("No hay instancias configuradas para evaluar la votación.")
            return self.votador.votar([])

        async with httpx.AsyncClient(timeout=self.segundos_timeout) as cliente:
            tareas = [
                self._llamar_instancia(
                    cliente=cliente,
                    url=url,
                    metodo=metodo,
                    ruta=ruta,
                    carga_util=carga_util,
                    encabezados=encabezados,
                    parametros=parametros,
                )
                for url in instancias_objetivo
            ]

            resultados = await asyncio.gather(*tareas, return_exceptions=True)

        respuestas: List[RespuestaInstancia] = []
        for indice, resultado in enumerate(resultados):
            if isinstance(resultado, Exception):
                url = instancias_objetivo[indice]
                registrador.error("Excepción en tarea asíncrona para %s: %s", url, str(resultado))
                respuestas.append(
                    RespuestaInstancia(
                        id_instancia=url,
                        es_exitosa=False,
                        error=f"Error en tarea asíncrona: {str(resultado)}",
                    )
                )
            else:
                respuestas.append(resultado)

        return self.votador.votar(respuestas)
