# CallMood SaaS

Plataforma SaaS para auditoría de llamadas. El motor analítico DAIA se mantiene intacto en `src/engine/daia`; se expone vía API FastAPI y worker asíncrono con Redis/RQ.

## Arquitectura (carpetas clave)
- `src/engine/daia`: motor de análisis (pipeline, modelos y reporting).
- `src/backend/app`: API FastAPI (autenticación, gestión de llamadas, métricas).
- `workers/worker.py`: worker RQ que ejecuta el pipeline y persiste resultados.
- `storage/`: subidas de audio.
- `artifacts/`: artefactos secundarios (reports, transcripts, analysis).
- `docs/`: documentación previa del proyecto.
- `tests/`: pruebas portadas al nuevo layout.

## Endpoints mínimos
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/users/me`
- `POST /api/v1/calls/upload`
- `GET /api/v1/calls`
- `GET /api/v1/calls/{id}`
- `GET /api/v1/calls/{id}/analysis`
- `GET /api/v1/metrics/overview`
- `GET /api/v1/metrics/operators`

## Ejecutar con Docker
1) Copiar `.env.example` a `.env` y ajustar secretos si es necesario.
2) `docker compose up --build`
3) API disponible en http://localhost:8000 (docs en `/docs`).

## Flujo de procesamiento
1. `POST /calls/upload` sube audio → se almacena en `storage/uploads/<company_id>/`.
2. Se encola tarea RQ `process_call`.
3. Worker ejecuta `PipelineOrchestrator` y guarda resultados en PostgreSQL.
4. Artefactos opcionales JSON/TXT se escriben en `artifacts/reports/`.

## Variables de entorno relevantes
Ver `.env.example` (DATABASE_URL, REDIS_URL, STORAGE_DIR, ARTIFACTS_DIR, CONFIG_PATH, SECRET_KEY).
