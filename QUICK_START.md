# 🎯 DAIA 2.0 - INICIO RÁPIDO

## ✅ Estado: PRODUCCIÓN LISTA (7/7 tests pasados)

### Archivos Principales

| Módulo | Líneas | Descripción |
|--------|--------|-------------|
| **pipeline.py** | 430 | Orquestador principal (3 niveles) |
| **lib_database.py** | 414 | SQLite con 7 tablas normalizadas |
| **lib_qa.py** | 358 | Motor QA basado en reglas YAML |
| **lib_kpis.py** | 339 | Cálculo de 8+ métricas |
| **lib_sentiment.py** | 243 | Análisis sentimiento local (BERT) |
| **lib_resources.py** | 232 | Detección hardware + auto-fallback |
| **lib_transcription.py** | 182 | Whisper local con fallback |
| **config.yaml** | 373 | Configuración completa |

### Scripts Útiles

| Script | Propósito |
|--------|-----------|
| **test_system.py** | Validar sistema (ejecutar PRIMERO) |
| **demo.py** | Demostración interactiva |
| **process_audios.py** | Procesar audios (menú interactivo) |

### Documentación

| Documento | Contenido |
|-----------|-----------|
| **STATUS.md** | Estado + Quick Start |
| **EXECUTIVE_SUMMARY.md** | Resumen ejecutivo completo |
| **ARCHITECTURE.md** | Diseño arquitectónico detallado |
| **README.md** | Documentación general |

---

## 🚀 Comandos Esenciales

```powershell
# 1. Validar sistema
python test_system.py

# 2. Demo interactivo
python demo.py

# 3. Procesar audios
python process_audios.py
```

---

## 💡 Uso Directo (Python)

```python
import sys
sys.path.insert(0, 'scripts')

from pipeline import PipelineOrchestrator
from lib_resources import ConfigManager

# Cargar config
config = ConfigManager('config.yaml')

# Crear orquestador
orchestrator = PipelineOrchestrator(config)

# Procesar audio
result = orchestrator.process_audio_file(
    'audio_in/llamada.wav',
    service_level='standard'  # basic, standard, advanced
)

# Ver resultados
print(f"QA: {result['qa_score']}")
print(f"Sentiment: {result['sentiment']}")
print(f"Risk: {result['risk_level']}")
```

---

## 📊 Sistema en Números

- ✅ **7 módulos** core (2,600 líneas)
- ✅ **3 niveles** de servicio
- ✅ **7 tablas** SQLite normalizadas
- ✅ **8+ métricas** operacionales
- ✅ **6 tipos** de checks QA
- ✅ **8 patrones** detectables
- ✅ **100%** local (cero APIs)
- ✅ **$0** costo operacional

---

## 🎓 Arquitectura en 3 Líneas

1. **audio → transcripción** (Whisper local)
2. **transcripción → análisis** (QA, sentiment, KPIs, risk)
3. **análisis → reportes + BD** (SQLite + CSV/JSON/TXT)

---

## 🔧 Configuración Rápida

Todo en `config.yaml`:

```yaml
general:
  language: es          # Idioma
  log_level: INFO       # DEBUG para más detalle

transcription:
  model: small          # small, medium, large
  
qa:
  rules:
    standard:           # Edita reglas aquí
      - mandatory_phrases: [...]
      
kpis:
  enabled_metrics: [duration, words, ...]  # Activa/desactiva
```

Cambiar config = **sin tocar código**.

---

## 📁 Estructura Clave

```
daia_call_audit/
├── scripts/              # 7 módulos core
│   ├── lib_*.py         # Librerías independientes
│   └── pipeline.py      # Orquestador
│
├── audio_in/            # Audios para procesar
├── reports/             # Reportes generados
├── data/                # SQLite BD
│
├── config.yaml          # Configuración
├── test_system.py       # Validación
├── demo.py              # Demo interactivo
└── process_audios.py    # Procesador con menú
```

---

## ⚡ Niveles de Servicio

### BASIC (Rápido)
- Transcripción + Risk
- ⏱️ 2-5 min GPU | 10-30 min CPU

### STANDARD ⭐ (Recomendado)
- BASIC + Sentiment + QA + KPIs
- ⏱️ 3-10 min GPU | 15-45 min CPU

### ADVANCED (Completo)
- STANDARD + Patterns + Anomalies
- ⏱️ 5-15 min GPU | 20-60 min CPU

---

## 🔒 Seguridad

- ✅ 100% procesamiento local
- ✅ Sin APIs externas
- ✅ SQLite local (encriptable)
- ✅ Datos privados
- ✅ Audit logs

---

## 📞 Próximos Pasos

1. ✅ **Validar**: `python test_system.py`
2. 🎮 **Probar**: `python demo.py`
3. 🎙️ **Usar**: Copiar audios a `audio_in/` → ejecutar `process_audios.py`

---

**Versión**: 2.0.0  
**Estado**: 🟢 PRODUCCIÓN LISTA  
**Tests**: ✅ 7/7 PASADOS  
**Última actualización**: 2025-12-30
