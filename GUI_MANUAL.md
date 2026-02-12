# DAIA 2.0 - Guía de Uso de la GUI

## 🎯 Inicio Rápido

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 2. Iniciar la GUI

```bash
python launch_gui.py
```

## 📖 Manual de Usuario

### Panel de Control

#### Procesar Archivo Individual

1. Haz clic en **"📁 Explorar"** junto a "Archivo de audio"
2. Selecciona el archivo de audio (.wav, .mp3, .m4a, .ogg, .flac)
3. Elige el nivel de análisis en el menú desplegable:
   - **basic**: Análisis rápido (solo transcripción)
   - **standard**: Análisis completo (recomendado)
   - **advanced**: Análisis detallado (más lento)
4. Haz clic en **"🎙️ Procesar Archivo Individual"**
5. Observa el progreso en el panel de Logs

#### Procesar Carpeta Completa

1. La carpeta por defecto es `audio_in/`
2. Si deseas cambiarla, haz clic en **"📁 Explorar"** junto a "Carpeta de audios"
3. Selecciona la carpeta con tus archivos de audio
4. Haz clic en **"📊 Procesar Carpeta Completa"**
5. Todos los archivos de audio en la carpeta se procesarán secuencialmente

#### Detener Proceso

- Durante el procesamiento, el botón **"⛔ Detener"** se activa
- Haz clic para interrumpir el proceso actual

### Panel de Logs

- Muestra información en tiempo real sobre el procesamiento
- Los logs incluyen:
  - Inicio de procesamiento
  - Progreso de transcripción
  - Análisis de riesgos
  - Análisis de sentimiento
  - Evaluación de calidad (QA)
  - Resultados finales
- Usa **"🗑️ Limpiar Logs"** para limpiar la consola

### Panel de Reportes

- Lista los últimos 20 reportes generados
- Reportes ordenados por fecha (más reciente primero)
- Acciones disponibles:
  - **🔄 Actualizar Lista**: Recargar lista de reportes
  - **📄 Abrir Reporte**: Abrir reporte seleccionado en la lista
  - **📁 Abrir Carpeta Reports**: Abrir carpeta con todos los reportes

## 📊 Tipos de Reportes Generados

Cada procesamiento genera dos archivos:

1. **Archivo JSON** (`YYYYMMDD_HHMMSS_nombrearchivo.json`)
   - Contiene todos los datos estructurados
   - Incluye transcripción, riesgos, sentimiento, QA, KPIs

2. **Archivo TXT** (`YYYYMMDD_HHMMSS_nombrearchivo.txt`)
   - Reporte legible para humanos
   - Resume los hallazgos principales

## 💡 Consejos

### Optimización de Rendimiento

- **CPU vs GPU**: La aplicación detecta automáticamente si hay GPU disponible
- **Nivel de Análisis**:
  - Usa **basic** para pruebas rápidas
  - Usa **standard** para análisis completo (recomendado)
  - Usa **advanced** solo cuando necesites análisis detallado

### Formatos de Audio Soportados

- ✅ WAV (sin comprimir)
- ✅ MP3 (comprimido)
- ✅ M4A (AAC)
- ✅ OGG (Vorbis)
- ✅ FLAC (lossless)

### Estructura de Carpetas

```
daia_call_audit/
├── audio_in/          # Coloca aquí tus audios
├── reports/           # Reportes generados
├── transcripts/       # Transcripciones intermedias
├── analysis/          # Análisis detallados
└── data/             # Base de datos SQLite
```

## 🔧 Solución de Problemas

### La GUI no inicia

```bash
# Verificar instalación de PySide6
pip list | grep PySide6

# Reinstalar si es necesario
pip install --upgrade PySide6
```

### Procesamiento lento

- **Normal en CPU**: El procesamiento puede tomar 1-2 minutos por minuto de audio
- **Con GPU**: Hasta 10x más rápido
- **Solución**: Considera usar nivel **basic** para pruebas

### Error al abrir reporte

- Verifica que tengas una aplicación asociada para archivos .json o .txt
- En Windows: Los archivos se abren con la aplicación predeterminada

### Logs no se actualizan

- Los logs se actualizan en tiempo real
- Si no ves actualizaciones, el proceso podría estar colgado
- Usa el botón **"⛔ Detener"** y reinicia

## 🆚 GUI vs Terminal

### Ventajas de la GUI

- ✅ Interfaz visual intuitiva
- ✅ No necesitas recordar comandos
- ✅ Logs en tiempo real en ventana dedicada
- ✅ Acceso rápido a reportes
- ✅ Selector visual de archivos y carpetas

### Ventajas del Terminal

- ✅ Automatización con scripts
- ✅ Integración con CI/CD
- ✅ Menor uso de memoria
- ✅ Ejecución remota (SSH)

### ¡Ambos funcionan perfectamente!

La GUI y el terminal son 100% compatibles:
- Puedes usar la GUI para desarrollo/pruebas
- Puedes usar terminal para producción/automatización
- Los reportes son los mismos en ambos casos

## 📞 Soporte

Para más información sobre el sistema DAIA:
- Ver: `README.md` principal
- Ver: `QUICK_START.md`
- Ver: `gui/README.md` (documentación técnica)

## 🎓 Ejemplo de Flujo de Trabajo

1. **Preparación**
   ```bash
   # Copiar audios a la carpeta
   cp mis_audios/*.m4a audio_in/
   ```

2. **Procesamiento**
   - Iniciar GUI: `python launch_gui.py`
   - Hacer clic en "📊 Procesar Carpeta Completa"
   - Esperar a que finalice

3. **Revisión de Resultados**
   - Ver logs en panel de Logs
   - Hacer clic en "🔄 Actualizar Lista"
   - Seleccionar reporte y hacer clic en "📄 Abrir Reporte"

4. **Análisis**
   - Revisar transcripciones en carpeta `transcripts/`
   - Revisar análisis detallados en carpeta `analysis/`
   - Revisar reportes en carpeta `reports/`

¡Listo! 🎉
