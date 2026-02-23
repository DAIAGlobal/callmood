# 🎯 CallMood - Sistema de Auditoría de Llamadas

**Versión:** 2.0.0 Final | **Estado:** ✅ Producción 

Sistema empresarial de auditoría de llamadas 100% local, sin APIs externas, zero-cost.

---

## ✨ Características

- 🎙️ Transcripción local (Whisper)
- 😊 Análisis de sentimiento (BERT)
- ✅ Evaluación QA (reglas YAML)
- 📊 8+ métricas operacionales
- 🔍 Detección de patrones
- ⚠️ Análisis de riesgos
- 💾 Base de datos SQLite
- 📈 Reportes profesionales

---

## 🚀 Inicio Rápido

### Opción 1: Interfaz Gráfica (Recomendado) 🆕

```powershell
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Iniciar GUI
python launch_gui.py
```

### Opción 2: Línea de Comandos

```powershell
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Validar sistema
python test_system.py

# 3. Procesar audios
python process_audios.py
```

📖 **Ver [GUI_MANUAL.md](GUI_MANUAL.md) para guía completa de la interfaz gráfica**

---

## 📁 Estructura

```
daia_call_audit/
├── scripts/          # 7 módulos core
├── gui/              # 🆕 Interfaz gráfica (PySide6)
├── audio_in/         # Audios para procesar
├── reports/          # Reportes generados
├── data/             # Base de datos SQLite
├── config.yaml       # Configuración
├── launch_gui.py     # 🆕 Launcher GUI
├── test_system.py    # Validación
└── process_audios.py # Procesador principal
```

---

## 💻 Uso Programático

```python
from pipeline import PipelineOrchestrator

orchestrator = PipelineOrchestrator('config.yaml')
result = orchestrator.process_audio_file(
    'audio_in/llamada.wav',
    service_level='standard'
)
```

---

## 🎯 Niveles de Servicio

- **BASIC**: Transcripción + Riesgos (2-5min GPU | 10-30min CPU)
- **STANDARD** ⭐: BASIC + Sentiment + QA + KPIs (recomendado)
- **ADVANCED**: STANDARD + Patrones + Anomalías

---

## 📊 Métricas de Calidad

- ✅ EXCELENTE: ≥85%
- ✅ BUENO: 70-84%
- ⚠️ ACEPTABLE: 50-69%
- ❌ DEFICIENTE: <30%

---

## 💾 Base de Datos

SQLite en `data/daia_audit.db` con 7 tablas:
- calls, transcripts, qa_scores, risk_assessments
- kpi_results, sentiment_analysis, audit_logs

---

## 🔒 Seguridad

- ✅ 100% local (sin cloud)
- ✅ Sin APIs externas
- ✅ Datos privados
- ✅ GDPR compliant

---

## 💰 Costos

**$0 USD** operacional (vs $1,500-$3,000/año en cloud)

---

## 🛠️ Requisitos

- Python 3.8+
- 4GB RAM mínimo
- 5GB espacio disco

---

## 📖 Comandos

```powershell
python launch_gui.py       # 🆕 Iniciar GUI
python test_system.py      # Validar
python demo.py             # Demo
python process_audios.py   # Procesar
```

**🎨 Interfaz Gráfica:**
- Procesamiento visual con logs en tiempo real
- Selector de archivos/carpetas
- Acceso rápido a reportes
- Ver [GUI_MANUAL.md](GUI_MANUAL.md)

---

## ✅ Estado

**Tests:** 7/7 ✓ | **Líneas:** 2,600+ | **Módulos:** 7

Ver **QUICK_START.md** para guía detallada.
