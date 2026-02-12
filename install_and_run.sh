#!/bin/bash
# DAIA 2.0 - Instalador Rápido para Linux/Mac
# Este script instala todas las dependencias necesarias

echo "======================================================================"
echo "  DAIA 2.0 - Instalador Rápido"
echo "======================================================================"
echo

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 no está instalado"
    echo "Por favor instala Python 3.8+ desde: https://www.python.org"
    exit 1
fi

echo "[INFO] Python detectado"
python3 --version
echo

# Verificar pip
if ! command -v pip3 &> /dev/null; then
    echo "[ERROR] pip3 no está disponible"
    exit 1
fi

echo "[INFO] Instalando dependencias..."
echo

# Instalar requirements
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo
    echo "[ERROR] Error durante la instalación"
    exit 1
fi

echo
echo "======================================================================"
echo "  Instalación Completa!"
echo "======================================================================"
echo
echo "Comandos disponibles:"
echo "  - python3 launch_gui.py       : Iniciar interfaz gráfica"
echo "  - python3 process_audios.py   : Procesar audios por terminal"
echo "  - python3 test_system.py      : Validar sistema"
echo
echo "Presiona Enter para iniciar la GUI..."
read

# Iniciar GUI
python3 launch_gui.py
