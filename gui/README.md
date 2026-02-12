# DAIA 2.0 - GUI Module

## 📋 Descripción

Módulo de interfaz gráfica (GUI) para el sistema DAIA 2.0 de auditoría de llamadas.

## ✨ Características

- **Interfaz moderna** con PySide6 (Qt)
- **Procesamiento en tiempo real** con logs visibles
- **Dos modos de operación:**
  - Procesar archivo individual
  - Procesar carpeta completa (batch)
- **Selector de nivel de análisis** (Básico/Estándar/Avanzado)
- **Visualización de reportes** generados
- **Acceso rápido** a carpeta de reportes
- **No modifica scripts existentes** - ejecuta como subprocesos

## 🚀 Uso

### Iniciar GUI

```bash
python launch_gui.py
```

### Desde Python

```python
from gui.main_window import main
main()
```

## 🎯 Funcionalidades

### Panel de Control

1. **Selector de Archivo**: Elegir un archivo de audio específico
2. **Selector de Carpeta**: Elegir carpeta con múltiples audios (por defecto: `audio_in/`)
3. **Nivel de Análisis**: Básico, Estándar o Avanzado
4. **Botones de Acción**:
   - 🎙️ Procesar Archivo Individual
   - 📊 Procesar Carpeta Completa
   - ⛔ Detener proceso actual

### Panel de Logs

- Visualización en tiempo real del procesamiento
- Logs con formato de consola
- Botón para limpiar logs

### Panel de Reportes

- Lista de últimos 20 reportes generados
- Botón para actualizar lista
- Abrir reporte seleccionado
- Abrir carpeta de reportes

## 🔧 Arquitectura

```
gui/
├── __init__.py           # Módulo GUI
└── main_window.py        # Ventana principal

launch_gui.py             # Launcher principal
```

### Componentes

- **DAIAMainWindow**: Ventana principal de la aplicación
- **ProcessThread**: Thread para procesar archivo individual
- **BatchProcessThread**: Thread para procesamiento en lote

### Integración

La GUI ejecuta los scripts existentes como subprocesos usando `subprocess.Popen`:

```python
subprocess.Popen(
    [python_exe, "process_audios.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    ...
)
```

## 📦 Dependencias

- PySide6 (Qt for Python)
- Todas las dependencias existentes del proyecto

Instalar con:

```bash
pip install -r requirements.txt
```

## ✅ Compatibilidad

- ✓ Windows (probado)
- ✓ Linux (compatible)
- ✓ macOS (compatible)
- ✓ Python 3.8+
- ✓ Compatible con ejecución por terminal

## 🔐 Seguridad

- Todo ejecuta localmente
- Sin APIs externas
- Sin costos adicionales
- Los scripts originales no se modifican

## 📝 Notas

- La GUI no modifica ningún script existente
- Los procesos se ejecutan en threads separados para no bloquear la interfaz
- Los logs se muestran en tiempo real
- Compatible con el sistema de ejecución por terminal existente
