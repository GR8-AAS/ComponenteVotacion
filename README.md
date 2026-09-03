# Componente de Estrategia de Votación (Consenso y Detección de Fallas)

Este componente implementa el patrón arquitectónico de **Votación / Redundancia N-Modular (N-Version Programming / Active Redundancy)** con una API REST en **Flask** y autenticación **JWT**.

Su objetivo es enviar peticiones en paralelo (`asyncio.gather` con `httpx.AsyncClient`) a múltiples réplicas de un servicio, evaluar el consenso mediante mayoría estricta y detectar fallos aislando réplicas caídas o disidentes.

---

## 🏗️ Arquitectura y Funcionamiento

```
                 +-----------------------------------------------+
                 |             Cliente / Gateway                 |
                 |      (Header: Authorization Bearer <token>)   |
                 +-----------------------------------------------+
                                         |
                                         v  POST /api/v1/execute
                 +-----------------------------------------------+
                 |             API Flask (api_votacion)          |
                 |                                               |
                 |   +---------------------------------------+   |
                 |   |           EvaluadorVotacion           |   |
                 |   |    (asyncio.gather + httpx.AsyncClient)   |   |
                 |   +---------------------------------------+   |
                 +-----------------------------------------------+
                       /                 |                 \
                      /                  |                  \
                     v                   v                   v
              +-------------+     +-------------+     +-------------+
              | Instancia 1 |     | Instancia 2 |     | Instancia 3 |
              +-------------+     +-------------+     +-------------+
                     \                   |                   /
                      \                  |                  /
                       v                 v                 v
                 +-----------------------------------------------+
                 |           VotadorMayoria (Consenso)           |
                 | - Quórum automático: (N // 2) + 1             |
                 | - Determina la respuesta consensuada          |
                 | - Detecta réplicas disidentes o con fallos    |
                 +-----------------------------------------------+
                                         |
                                         v
                 +-----------------------------------------------+
                 |       Respuesta Consensuada + Diagnóstico     |
                 +-----------------------------------------------+
```

---

## ⚙️ Configuración (`.env`)

```env
FLASK_APP=run.py
FLASK_ENV=development
PORT=5000
DEBUG=True

# URLs de las instancias réplicas separadas por coma
SERVICE_INSTANCES=http://localhost:8001,http://localhost:8002,http://localhost:8003

# Timeout en segundos por réplica
VOTING_TIMEOUT_SECONDS=3.0

# Llave secreta para validación de tokens JWT
JWT_SECRET_KEY=llave-secreta-jwt-componente-votacion-2026-super-segura-y-robusta
```

---

## 📡 Endpoint de la API

### Ejecución de Votación Distribuida
- **Endpoint**: `POST /api/v1/execute`
- **Seguridad**: Requiere `Authorization: Bearer <token_jwt>`.
- **Descripción**: Envía la solicitud en paralelo a todas las réplicas configuradas, realiza la votación y devuelve el consenso con el informe de fallas y disidencias.

**Ejemplo de Petición (JSON)**:
```json
{
  "metodo": "POST",
  "ruta": "/api/procesar",
  "carga_util": {
    "transaccion_id": "TX-12345",
    "monto": 100.50
  },
  "encabezados": {
    "Content-Type": "application/json"
  },
  "instancias": [
    "http://localhost:8001",
    "http://localhost:8002",
    "http://localhost:8003"
  ]
}
```

**Ejemplo de Respuesta (200 OK)**:
```json
{
  "veredicto": "CONSENSO_ALCANZADO",
  "datos_consenso": {
    "status": "APROBADO",
    "codigo": 200
  },
  "codigo_estado_consenso": 200,
  "total_instancias": 3,
  "votos_consenso": 2,
  "quorum_requerido": 2,
  "instancias_exitosas": [
    "http://localhost:8001",
    "http://localhost:8002"
  ],
  "instancias_fallidas": [],
  "instancias_disidentes": [
    "http://localhost:8003"
  ],
  "distribucion_votos": {
    "{\"codigo\": 200, \"status\": \"APROBADO\"}": 2,
    "{\"codigo\": 500, \"status\": \"RECHAZADO\"}": 1
  },
  "detalles": [
    {
      "id_instancia": "http://localhost:8001",
      "codigo_estado": 200,
      "datos": {"codigo": 200, "status": "APROBADO"},
      "latencia_ms": 12.35,
      "es_exitosa": true,
      "error": null
    },
    {
      "id_instancia": "http://localhost:8002",
      "codigo_estado": 200,
      "datos": {"codigo": 200, "status": "APROBADO"},
      "latencia_ms": 15.10,
      "es_exitosa": true,
      "error": null
    },
    {
      "id_instancia": "http://localhost:8003",
      "codigo_estado": 500,
      "datos": {"codigo": 500, "status": "RECHAZADO"},
      "latencia_ms": 18.22,
      "es_exitosa": true,
      "error": null
    }
  ]
}
```

---

## 🧪 Pruebas Automatizadas

Ejecutar la suite de pruebas completa:

```powershell
pytest -v
```
