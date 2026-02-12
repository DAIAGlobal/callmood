@echo off
:: DAIA 2.0 - Instalador Rápido para Windows
:: Este script instala todas las dependencias necesarias

echo ======================================================================
echo   DAIA 2.0 - Instalador Rapido
echo ======================================================================
echo.

:: Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no esta instalado
    echo Por favor instala Python 3.8+ desde: https://www.python.org
    pause
    exit /b 1
)

echo [INFO] Python detectado
python --version
echo.

:: Verificar pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip no esta disponible
    pause
    exit /b 1
)

echo [INFO] Instalando dependencias...
echo.

:: Instalar requirements
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [ERROR] Error durante la instalacion
    pause
    exit /b 1
)

echo.
echo ======================================================================
echo   Instalacion Completa!
echo ======================================================================
echo.
echo Comandos disponibles:
echo   - python launch_gui.py       : Iniciar interfaz grafica
echo   - python process_audios.py   : Procesar audios por terminal
echo   - python test_system.py      : Validar sistema
echo.
echo Presiona cualquier tecla para iniciar la GUI...
pause >nul

:: Iniciar GUI
python launch_gui.py
