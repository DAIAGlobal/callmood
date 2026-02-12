# DAIA 2.0 - Procesamiento Batch: Guía Rápida

## 🚀 Inicio Rápido (5 minutos)

### 1. Instalar dependencias
```bash
pip install python-docx reportlab
```

### 2. Colocar audios
```bash
# Copiar archivos .wav, .mp3, .m4a, etc. a:
audio_in/
```

### 3. Ejecutar batch
```bash
python process_batch.py audio_in/
```

### 4. Ver resultados
```bash
# Reportes generados en:
reports/
├── batch_audit_report_TIMESTAMP.pdf   # Consolidado
├── batch_audit_report_TIMESTAMP.docx  # Consolidado editable
├── audit_1_TIMESTAMP.pdf              # Individual llamada 1
├── audit_1_TIMESTAMP.docx             # Individual llamada 1
└── ...
```

---

## 📊 Opciones Disponibles

### Formato de Reportes
```bash
# Solo PDF (más rápido)
python process_batch.py audio_in/ --format pdf

# Solo DOCX (editable)
python process_batch.py audio_in/ --format docx

# Ambos formatos (default)
python process_batch.py audio_in/ --format both
```

### Nivel de Auditoría
```bash
# Básico (rápido)
python process_batch.py audio_in/ --service-level basic

# Estándar (default)
python process_batch.py audio_in/ --service-level standard

# Avanzado (completo)
python process_batch.py audio_in/ --service-level advanced
```

### Directorio de Salida
```bash
# Personalizar carpeta de reportes
python process_batch.py audio_in/ --output-dir reportes_enero
```

### Solo Consolidado
```bash
# No generar reportes individuales (solo batch)
python process_batch.py audio_in/ --no-individual
```

---

## 📋 Ejemplo Completo

```bash
# Auditoría avanzada de febrero, solo PDF consolidado
python process_batch.py C:/audios/febrero/ \
    --service-level advanced \
    --format pdf \
    --no-individual \
    --output-dir reportes/feb_2026
```

**Salida**:
```
======================================================================
DAIA 2.0 - PROCESADOR BATCH DE AUDITORÍAS
======================================================================
📁 Carpeta: C:/audios/febrero/
🎯 Nivel: advanced
📄 Formato: pdf
💾 Output: reportes/feb_2026
======================================================================

🚀 FASE 1: Procesando audios...
📊 Procesando 25 archivos en batch...
[1/25] Procesando: llamada_001.m4a
  ✅ QA: 85.0% | Findings: 2 | Status: good
[2/25] Procesando: llamada_002.m4a
  ⚠️ QA: 62.0% | Findings: 5 | Status: acceptable
...

✅ Batch completado: 25 audios procesados
   Aprobados: 20 | Rechazados: 5
   QA Promedio: 78.5%
   Findings críticos: 3

📝 FASE 2: Generando reporte consolidado...
✓ PDF generado: batch_audit_report_20260102_203800.pdf

======================================================================
✅ PROCESO COMPLETADO
======================================================================
✓ 25 audios procesados
✓ 20 aprobados (80.0%)
✓ QA Score promedio: 78.5%
⚠️  3 hallazgos críticos detectados

📂 Reportes guardados en: C:\audios\reportes\feb_2026
======================================================================
```

---

## 🐍 Uso Programático

### Desde Python
```python
from daia import process_audio_folder, generate_batch_reports

# 1. Procesar carpeta
batch_result = process_audio_folder("audio_in/", "standard")

# 2. Analizar resultados
print(f"Total: {batch_result.total_calls}")
print(f"Aprobados: {batch_result.passed_calls}")
print(f"QA Promedio: {batch_result.avg_qa_score:.1f}%")
print(f"Tasa de aprobación: {batch_result.approval_rate:.1f}%")

# 3. Llamadas que requieren atención
for result in batch_result.requires_attention:
    print(f"⚠️ {result.audited_call.filename}: {result.qa_score:.1f}%")

# 4. Generar reportes
reports = generate_batch_reports(batch_result, format="pdf")
print(f"Reporte generado: {reports['pdf']}")
```

### Acceder a Detalles
```python
# Iterar por cada auditoría
for audit in batch_result.results:
    call = audit.audited_call
    print(f"\nLlamada: {call.filename}")
    print(f"  Duración: {call.duration_minutes:.1f} min")
    print(f"  QA Score: {audit.qa_score:.1f}%")
    print(f"  Status: {audit.overall_status}")
    
    # Findings críticos
    if audit.critical_findings:
        print(f"  Findings críticos: {len(audit.critical_findings)}")
        for finding in audit.critical_findings:
            print(f"    - {finding.title}")
    
    # Métricas
    for metric in audit.metrics:
        print(f"  {metric.name}: {metric.formatted_value} [{metric.status.value}]")
```

---

## 📁 Estructura de Reportes

### Reporte Consolidado (batch_audit_report_*.pdf/docx)
```
1. RESUMEN EJECUTIVO
   - Total de llamadas
   - Llamadas aprobadas/rechazadas
   - Tasa de aprobación
   - QA Score promedio
   - Hallazgos críticos
   - Tiempo de procesamiento

2. HALLAZGOS CRÍTICOS
   - Top 10 llamadas con problemas
   - Detalle de findings por severidad

3. MÉTRICAS CLAVE
   - Distribución de status
   - KPIs del batch

4. RECOMENDACIONES
   - Acciones sugeridas basadas en resultados
   - Priorización

5. CONCLUSIÓN OPERATIVA
   - Evaluación general
   - Siguiente paso recomendado
```

### Reporte Individual (audit_*_*.pdf/docx)
```
- Información de la llamada
- QA Score y status
- Lista de findings con severidad
- Tabla de métricas
- Recomendaciones específicas
```

---

## 🎯 Métricas Incluidas

| Métrica | Descripción | Umbral |
|---------|-------------|--------|
| **QA Score** | Cumplimiento del protocolo | Min: 70% |
| **Duración** | Tiempo de llamada | 30s - 600s |
| **Silencio** | % de silencios incómodos | Max: 30% |
| **Interrupciones** | Cantidad de interrupciones | Max: 5 |
| **Tono Emocional** | Sentimiento general | Positive/Neutral |

---

## ⚡ Tips de Rendimiento

### Optimizar Velocidad
```bash
# Procesar solo audios nuevos (no duplicar)
# DAIA detecta automáticamente audios ya procesados en BD

# Usar nivel básico para auditorías rápidas
python process_batch.py audio_in/ --service-level basic

# No generar reportes individuales si no son necesarios
python process_batch.py audio_in/ --no-individual
```

### Grandes Volúmenes
```bash
# Para carpetas con 100+ audios:
# 1. Dividir en subcarpetas por fecha/periodo
# 2. Procesar cada subcarpeta por separado
# 3. Consolidar resultados manualmente

# Ejemplo:
python process_batch.py audio_in/enero/ --output-dir reports/enero
python process_batch.py audio_in/febrero/ --output-dir reports/febrero
```

---

## ❓ Solución de Problemas

### "No se encontraron archivos de audio"
```bash
# Verificar extensiones soportadas:
ls audio_in/*.{wav,mp3,m4a,ogg,flac}

# Copiar archivos a audio_in/
cp /ruta/audios/*.m4a audio_in/
```

### "reportlab no disponible"
```bash
pip install reportlab
```

### "python-docx no disponible"
```bash
pip install python-docx
```

### "Error procesando archivo"
```bash
# El batch continúa con el siguiente archivo
# Revisar log para detalles del error específico
python process_batch.py audio_in/ --verbose
```

---

## 📞 Ayuda

```bash
# Ver todas las opciones
python process_batch.py --help
```

---

## 🎉 ¡Listo!

Tu sistema está configurado para procesar batches de audios y generar reportes profesionales.

**Siguiente paso**: Coloca audios en `audio_in/` y ejecuta:
```bash
python process_batch.py audio_in/
```

Los reportes aparecerán en `reports/` en formato PDF y DOCX.

---

*DAIA 2.0 - Call Audit System*  
*Documentación de Fase 2 - Procesamiento Batch*
