# CallMood - Inicio Rápido

## 1) Instalar
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```
Requisitos: Python 3.10+, ffmpeg en PATH, ~5GB libres.

## 2) Ejecutar (CLI unificado)
Procesar un archivo:
```bash
python run_daia.py audio_in/muestra.wav --service-level standard
```
Procesar carpeta y generar PDF consolidado:
```bash
python run_daia.py audio_in/ --service-level standard --batch-pdf
```

## 3) Estructura mínima que debes conocer
- `run_daia.py`: entrypoint único.
- `daia/domain`: entidades (`AuditedCall`, `AuditResult`, `Finding`, `Metric`).
- `daia/application/services/batch_audit_service.py`: orquesta el pipeline y retorna agregados de dominio.
- `daia/infrastructure/pipeline/`: Whisper, QA, KPIs, riesgo, reglas dinámicas, SQLite.
- `daia/infrastructure/reporting/`: PDF/DOCX + helpers JSON/TXT.
- `data/rulesets.json`: reglas dinámicas versionadas.

## 4) Salidas
- `reports/*.json`: resumen con QA, riesgo, sentimiento, KPIs.
- `reports/*.txt`: reporte ejecutivo QA-ready.
- `data/daia_audit.db`: persistencia local (7 tablas).

## 5) Tests ligeros
```bash
pytest test_domain_models.py test_save_reports.py
```

## 6) GUI opcional
```bash
python launch_gui.py
```
La GUI llama al mismo entrypoint (`run_daia.py`); no afecta al dominio.
