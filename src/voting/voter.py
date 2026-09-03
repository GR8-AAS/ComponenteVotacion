import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from .models import RespuestaInstancia, VeredictoVotacion, ResultadoVotacion

registrador = logging.getLogger(__name__)


class VotadorMayoria:

    @staticmethod
    def serializar_carga_util(datos: Any) -> str:
        try:
            return json.dumps(datos, sort_keys=True, ensure_ascii=False)
        except (TypeError, ValueError):
            return str(datos)

    def votar(self, respuestas: List[RespuestaInstancia]) -> ResultadoVotacion:
        """
        Ejecuta la votación sobre una lista de respuestas de instancias.
        El quórum se calcula estrictamente a partir del total de réplicas: (total // 2) + 1.

        :param respuestas: Lista de RespuestaInstancia recolectadas.
        :return: ResultadoVotacion con el consenso, veredicto e identificación de instancias disidentes o con fallos.
        """
        total = len(respuestas)
        if total == 0:
            return ResultadoVotacion(
                veredicto=VeredictoVotacion.TODAS_FALLIDAS,
                total_instancias=0,
                quorum_requerido=0,
            )

        quorum = total // 2 + 1

        instancias_exitosas: List[str] = []
        instancias_fallidas: List[str] = []
        # Agrupación: clave_serializada -> (conteo, datos_originales, codigo_estado, lista_id_instancias)
        grupos: Dict[str, Tuple[int, Any, Optional[int], List[str]]] = {}

        for respuesta in respuestas:
            if not respuesta.es_exitosa or respuesta.error or (respuesta.codigo_estado and respuesta.codigo_estado >= 400):
                instancias_fallidas.append(respuesta.id_instancia)
                continue

            instancias_exitosas.append(respuesta.id_instancia)
            clave = self.serializar_carga_util(respuesta.datos)

            if clave not in grupos:
                grupos[clave] = (1, respuesta.datos, respuesta.codigo_estado, [respuesta.id_instancia])
            else:
                conteo, datos, codigo_estado, lista_instancias = grupos[clave]
                lista_instancias.append(respuesta.id_instancia)
                grupos[clave] = (conteo + 1, datos, codigo_estado, lista_instancias)

        # Si ninguna instancia respondió con éxito
        if not instancias_exitosas:
            registrador.warning("Todas las instancias fallaron o respondieron con error.")
            return ResultadoVotacion(
                veredicto=VeredictoVotacion.TODAS_FALLIDAS,
                total_instancias=total,
                quorum_requerido=quorum,
                instancias_fallidas=instancias_fallidas,
                detalles=respuestas,
            )

        # Distribución de votos para el resumen
        distribucion_votos = {clave: valor[0] for clave, valor in grupos.items()}

        # Ordenar grupos por número de votos de manera descendente
        grupos_ordenados = sorted(grupos.values(), key=lambda g: g[0], reverse=True)
        votos_lider, datos_lider, codigo_lider, instancias_lider = grupos_ordenados[0]

        # Verificar si hay empate en el primer lugar
        if len(grupos_ordenados) > 1 and grupos_ordenados[1][0] == votos_lider:
            registrador.info("Empate detectado entre respuestas de instancias.")
            return ResultadoVotacion(
                veredicto=VeredictoVotacion.EMPATE,
                total_instancias=total,
                votos_consenso=votos_lider,
                quorum_requerido=quorum,
                instancias_exitosas=instancias_exitosas,
                instancias_fallidas=instancias_fallidas,
                distribucion_votos=distribucion_votos,
                detalles=respuestas,
            )

        # Verificar si alcanza el quórum
        if votos_lider < quorum:
            registrador.info("No se alcanzó el quórum requerido (%d/%d votos).", votos_lider, quorum)
            return ResultadoVotacion(
                veredicto=VeredictoVotacion.SIN_CONSENSO,
                total_instancias=total,
                votos_consenso=votos_lider,
                quorum_requerido=quorum,
                instancias_exitosas=instancias_exitosas,
                instancias_fallidas=instancias_fallidas,
                distribucion_votos=distribucion_votos,
                detalles=respuestas,
            )

        # Se alcanzó el consenso: identificar instancias disidentes
        instancias_disidentes = [
            id_inst for id_inst in instancias_exitosas if id_inst not in instancias_lider
        ]

        registrador.info(
            "Consenso alcanzado con %d votos. Disidentes: %s, Fallidas: %s",
            votos_lider,
            instancias_disidentes,
            instancias_fallidas,
        )

        return ResultadoVotacion(
            veredicto=VeredictoVotacion.CONSENSO_ALCANZADO,
            datos_consenso=datos_lider,
            codigo_estado_consenso=codigo_lider,
            total_instancias=total,
            votos_consenso=votos_lider,
            quorum_requerido=quorum,
            instancias_exitosas=instancias_exitosas,
            instancias_fallidas=instancias_fallidas,
            instancias_disidentes=instancias_disidentes,
            distribucion_votos=distribucion_votos,
            detalles=respuestas,
        )
