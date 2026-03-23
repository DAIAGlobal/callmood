# CallMood (Call Audit AI)

Plataforma local para auditar llamadas de voz con transcripción, QA por reglas, análisis de riesgo y reportes ejecutivos. Código organizado con Domain-Driven Design para evolucionar a SaaS en 12–18 meses.

Nota: la marca de producto es CallMood, pero el paquete Python sigue siendo `daia` para mantener compatibilidad de imports y scripts existentes.

## Qué hace
- Transcribe audio con Whisper y separa roles (operador/cliente).
- Evalúa cumplimiento (QA), riesgos y KPIs operativos.
- Genera hallazgos de negocio y métricas accionables (QA score, duración, silencio, interrupciones, sentimiento).
- Persiste en SQLite y exporta reportes JSON/TXT; PDF/DOCX opcional.
- Funciona 100% offline; sin dependencias de cloud.

## Arquitectura (DDD)
- **daia/domain**: Entidades inmutables (`AuditedCall`, `AuditResult`, `Finding`, `Metric`).
- **daia/application**: Casos de uso (`BatchAuditService`) que orquestan el pipeline y devuelven agregados de dominio.
- **daia/infrastructure**:
  - `pipeline/`: Orchestrator + módulos de transcripción, QA, KPIs, sentimiento, reglas dinámicas, base de datos.
  - `reporting/`: Generación de PDF/DOCX y helpers para JSON/TXT.
  - `drive/`: Adaptadores Google Drive (sin acoplar al dominio).
- **gui/**: Interfaz PySide6 desacoplada; invoca el entrypoint CLI.
- **run_daia.py**: Único entrypoint soportado (CLI).  
Separación garantizada: dominio no depende de infraestructura; aplicación solo consume puertos de infraestructura.

### Estructura principal
```
daia_call_audit/
├── run_daia.py                   # Entry point CLI unificado
├── daia/
│   ├── domain/
│   ├── application/services/
│   └── infrastructure/
│       ├── pipeline/             # Whisper, QA, KPIs, DB, reglas
│       ├── reporting/            # ReportGenerator + report_saver
│       └── drive/                # Adaptadores Google Drive
├── gui/                          # UI opcional, aislada
├── config.yaml                   # Configuración operativa
├── data/rulesets.json            # Reglas dinámicas (versionables)
└── reports/                      # Salida (git-ignored)
```

## Instalación
Requisitos: Python 3.10+, ffmpeg en PATH, ~5GB libres.  
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

## Uso (CLI único)
Procesar un archivo:
```bash
python run_daia.py audio_in/muestra.wav --service-level standard
```

Procesar carpeta completa y generar PDF consolidado:
```bash
python run_daia.py audio_in/ --service-level standard --batch-pdf
```

Opciones clave:
- `--config`: ruta a `config.yaml` (default).
- `--db-path`: ruta SQLite (default `data/daia_audit.db`).
- `--reports-dir`: carpeta de salida (`reports/`).
- `--no-json` / `--no-txt`: desactivar formatos.

## Salidas garantizadas
- **JSON**: resumen con QA, riesgo, sentimiento, KPIs (en `reports/`).
- **TXT**: reporte ejecutivo listo para QA humano.
- **Métricas**: `qa_score`, duración, silencio, interrupciones, tono emocional.
- **Base de datos**: inserciones automáticas en `data/daia_audit.db`.
- **Batch PDF** (opcional): `--batch-pdf` usa `ReportGenerator`.

## Configuración y reglas
- `config.yaml`: niveles de servicio, rutas de audio, modelos y umbrales.
- `data/rulesets.json`: reglas dinámicas de riesgo/compliance.  
  Se versiona en git; el engine crea preset por defecto si falta.
- Env vars soportadas: `DAIA_RULES_USER` para seleccionar ruleset por usuario.

## Validación rápida
```bash
pytest test_domain_models.py test_save_reports.py
```
- `test_domain_models`: valida entidades de dominio (sin dependencias externas).
- `test_save_reports`: smoke test de generación JSON/TXT con datos de prueba.

## GUI (opcional)
```bash
python launch_gui.py
```
La GUI usa el mismo CLI (`run_daia.py`) bajo el capó; no afecta la capa de dominio.

## Roadmap hacia SaaS / API
1. Exponer casos de uso vía API (FastAPI) en `daia/interfaces/api/` (placeholder creado).
2. Añadir autenticación y multi-tenant en capa de aplicación.
3. Persistencia pluggable (SQLite → Postgres) detrás de puerto de repositorio.
4. Jobs async y colas para lotes grandes.
5. Observabilidad: métricas Prometheus y trazas estructuradas.

## Notas de operación
- Directorios runtime (`audio_in/`, `reports/`, `analysis/`, `transcripts/`, bases SQLite) están ignorados en git.
- `rulesets.json` se mantiene versionado para reproducibilidad.
- Para GPU en Windows: `KMP_DUPLICATE_LIB_OK=TRUE` y `TORCH_ALLOW_TF32_CUBLAS_OVERRIDE=1` ya aplican en el entrypoint.
