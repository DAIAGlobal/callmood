# 🔧 DAIA 2.0 GUI - Troubleshooting

## 🚨 Problemas Comunes y Soluciones

### 1. La GUI no inicia

#### Error: "No module named 'PySide6'"

**Causa**: PySide6 no está instalado

**Solución**:
```bash
pip install PySide6
# o
pip install -r requirements.txt
```

#### Error: "qt.qpa.plugin: Could not load the Qt platform plugin"

**Causa**: Problemas con plugins de Qt

**Solución Windows**:
```bash
set QT_QPA_PLATFORM_PLUGIN_PATH=%VIRTUAL_ENV%\Lib\site-packages\PySide6\plugins\platforms
python launch_gui.py
```

**Solución Linux**:
```bash
export QT_QPA_PLATFORM=xcb
python3 launch_gui.py
```

#### La ventana se abre pero está en blanco

**Causa**: Problemas de renderizado

**Solución**:
```bash
# Probar con software rendering
set QT_QPA_PLATFORM=windows:sw
python launch_gui.py
```

---

### 2. Problemas al Procesar Archivos

#### Error: "Por favor selecciona un archivo de audio válido"

**Causa**: No se seleccionó archivo o la ruta es incorrecta

**Solución**:
1. Haz clic en "📁 Explorar" junto a "Archivo de audio"
2. Navega hasta el archivo
3. Selecciona el archivo y haz clic en "Abrir"
4. Verifica que la ruta aparezca en el campo de texto

#### El procesamiento no inicia

**Causa**: Validación fallida o archivo no soportado

**Solución**:
1. Verifica que el archivo sea de audio (.wav, .mp3, .m4a, .ogg, .flac)
2. Verifica que el archivo no esté vacío
3. Verifica que tengas permisos de lectura
4. Intenta copiar el archivo a la carpeta `audio_in/`

#### Los logs no se actualizan

**Causa**: Problema con la comunicación del subproceso

**Solución**:
1. Haz clic en "⛔ Detener"
2. Cierra y vuelve a abrir la GUI
3. Intenta nuevamente
4. Si persiste, usa la versión terminal: `python process_audios.py`

---

### 3. Problemas con PyTorch

#### Error: "DLL load failed while importing torch"

**Causa**: PyTorch tiene problemas de carga en Windows

**Solución**: Ya está implementada en el código, pero si persiste:
```bash
# En PowerShell antes de ejecutar
$env:KMP_DUPLICATE_LIB_OK='TRUE'
python launch_gui.py
```

#### Procesamiento muy lento

**Causa**: Ejecutando en CPU sin GPU

**Información**:
- En CPU es normal: 1-2 minutos por minuto de audio
- Con GPU: 10x más rápido
- Usa nivel "basic" para pruebas rápidas

**Solución para acelerar**:
1. Cambiar nivel a "basic" en vez de "standard"
2. Considerar instalar GPU drivers si tienes GPU NVIDIA
3. Procesar archivos en lote por la noche

---

### 4. Problemas con Reportes

#### No aparecen reportes en la lista

**Causa**: Carpeta `reports/` vacía o no existe

**Solución**:
1. Verifica que la carpeta `reports/` exista
2. Procesa al menos un archivo
3. Haz clic en "🔄 Actualizar Lista"

#### No se puede abrir un reporte

**Causa**: No hay aplicación asociada para archivos .json

**Solución Windows**:
```bash
# Abrir con Notepad
notepad reports\archivo.json

# Abrir con VS Code (si está instalado)
code reports\archivo.json
```

**Solución Linux/Mac**:
```bash
# Abrir con editor de texto
gedit reports/archivo.json

# O con VS Code
code reports/archivo.json
```

#### Error al abrir carpeta de reportes

**Causa**: Carpeta no existe o no tienes permisos

**Solución**:
```bash
# Crear carpeta manualmente
mkdir reports

# Verificar permisos
ls -la reports/  # Linux/Mac
dir reports\     # Windows
```

---

### 5. Problemas de Encoding/UTF-8

#### Caracteres raros en los logs (�, ?, etc.)

**Causa**: Problemas de codificación UTF-8

**Solución**:
Ya está implementada en el código, pero si persiste:

**Windows PowerShell**:
```powershell
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
python launch_gui.py
```

**Windows CMD**:
```cmd
chcp 65001
python launch_gui.py
```

---

### 6. Problemas de Rendimiento

#### La GUI se congela durante procesamiento

**Causa**: Este comportamiento es esperado durante procesamiento intensivo

**Explicación**:
- El procesamiento es CPU-intensivo
- Los threads deberían mantener la GUI responsive
- Si se congela completamente, puede ser un problema de threading

**Solución**:
1. Espera a que termine el proceso
2. Si está congelada más de 5 minutos, usa Ctrl+C o cierra la ventana
3. Usa la versión terminal si persiste: `python process_audios.py`

#### Alto uso de RAM

**Causa**: Whisper y BERT son modelos grandes

**Normal**:
- Sin GPU: 2-4 GB RAM
- Con GPU: 1-2 GB RAM + VRAM

**Solución si falta RAM**:
1. Cerrar otros programas
2. Usar nivel "basic" (menos modelos en memoria)
3. Procesar archivos de uno en uno
4. Reiniciar la GUI entre procesamiento de lotes

---

### 7. Problemas Específicos de Plataforma

#### Windows: "Python no se reconoce como comando"

**Causa**: Python no está en el PATH

**Solución**:
```cmd
# Usar python con ruta completa
C:\Python311\python.exe launch_gui.py

# O agregar Python al PATH
setx PATH "%PATH%;C:\Python311"
```

#### Linux: "Permission denied"

**Causa**: Archivo sin permisos de ejecución

**Solución**:
```bash
chmod +x launch_gui.py
chmod +x install_and_run.sh
./launch_gui.py
```

#### macOS: "Application can't be opened"

**Causa**: Restricciones de seguridad de macOS

**Solución**:
```bash
# Dar permisos
chmod +x launch_gui.py

# Ejecutar con python3
python3 launch_gui.py
```

---

### 8. Problemas con Virtual Environment

#### Error: "Module not found" pero lo instalaste

**Causa**: Instalaste en el entorno equivocado

**Solución**:
```bash
# Activar virtual environment
# Windows
.venv\Scripts\Activate.ps1

# Linux/Mac
source .venv/bin/activate

# Verificar que estés en el venv correcto
which python   # Linux/Mac
where python   # Windows

# Instalar dependencias
pip install -r requirements.txt
```

---

### 9. Debugging Avanzado

#### Ejecutar en modo verbose

**Modificar launch_gui.py temporalmente**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Verificar salida de subprocesos

**Revisar la consola donde ejecutaste la GUI**:
- Los errores del subproceso aparecen ahí
- Busca líneas con "ERROR" o "Traceback"

#### Ejecutar proceso_audios.py directamente

**Para aislar el problema**:
```bash
python process_audios.py
# Sigue el menú interactivo
# Si funciona aquí, el problema es en la GUI
# Si falla aquí, el problema es en el pipeline
```

---

### 10. Soluciones de Emergencia

#### Nada funciona - Reinstalación completa

```bash
# 1. Eliminar virtual environment
rm -rf .venv  # Linux/Mac
rmdir /s .venv  # Windows

# 2. Crear nuevo virtual environment
python -m venv .venv

# 3. Activar
.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate    # Linux/Mac

# 4. Actualizar pip
python -m pip install --upgrade pip

# 5. Instalar dependencias
pip install -r requirements.txt

# 6. Ejecutar
python launch_gui.py
```

#### Usar versión terminal como fallback

```bash
# La versión terminal siempre debería funcionar
python process_audios.py

# Sigue el menú:
# 1 - Procesar archivo individual
# 2 - Procesar carpeta completa
# 3 - Ver reportes
# 4 - Salir
```

---

## 📊 Diagnóstico Rápido

### Checklist de Verificación

```bash
# 1. Python instalado
python --version
# Debe mostrar: Python 3.8 o superior

# 2. Pip funcional
pip --version
# Debe mostrar versión de pip

# 3. Dependencias instaladas
pip list | grep PySide6
pip list | grep torch
# Deben aparecer en la lista

# 4. Estructura de carpetas
ls -la  # Linux/Mac
dir     # Windows
# Deben existir: audio_in/, reports/, data/, gui/

# 5. Archivos necesarios
ls gui/main_window.py launch_gui.py process_audios.py
# Todos deben existir

# 6. Permisos de escritura
touch test.txt && rm test.txt  # Linux/Mac
echo test > test.txt && del test.txt  # Windows
# No debe dar error
```

---

## 🆘 Obtener Ayuda

### Información útil para reportar problemas

Cuando reportes un problema, incluye:

1. **Sistema operativo**: Windows 10/11, Ubuntu 22.04, macOS 13, etc.
2. **Versión de Python**: `python --version`
3. **Versión de PySide6**: `pip show PySide6`
4. **Mensaje de error completo**: Copia todo el traceback
5. **Pasos para reproducir**: Qué hiciste antes del error
6. **Logs**: Contenido del panel de logs si es relevante

### Logs de Debugging

```bash
# Ejecutar con salida completa
python launch_gui.py 2>&1 | tee gui_log.txt

# El archivo gui_log.txt contendrá toda la salida
```

---

## ✅ Si Todo Falla

**Usa la versión terminal**:
```bash
python process_audios.py
```

La versión terminal y la GUI son funcionalmente equivalentes. La GUI es solo una interfaz visual sobre los mismos scripts.

**Reporta el problema**:
- Incluye información de diagnóstico
- Describe el problema detalladamente
- Adjunta logs si es posible

---

## 🎓 Notas Importantes

1. **La GUI ejecuta los mismos scripts** que la versión terminal
2. **Si la terminal funciona**, el problema está en la GUI específicamente
3. **Si la terminal falla también**, el problema está en el pipeline/dependencias
4. **Los reportes son idénticos** entre GUI y terminal
5. **Puedes alternar** entre GUI y terminal sin problemas

---

## 📞 Recursos Adicionales

- **Manual de Usuario**: `GUI_MANUAL.md`
- **Documentación Técnica**: `gui/README.md`
- **Inicio Rápido**: `QUICK_START.md`
- **README Principal**: `README.md`

---

## 💡 Consejo Final

**La mejor forma de resolver problemas es:**
1. Leer el mensaje de error completo
2. Buscar el error específico en este documento
3. Seguir la solución paso a paso
4. Si no funciona, usar la versión terminal como alternativa
5. Reportar el problema con toda la información necesaria

¡La mayoría de problemas tienen solución rápida! 🚀
