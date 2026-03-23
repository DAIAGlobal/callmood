#!/usr/bin/env python
"""
DAIA 2.0 - GUI Launcher
Inicia la interfaz gráfica de usuario
"""

import sys
from pathlib import Path

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).parent))

# Fix PyTorch DLL loading on Windows Python 3.13
import os
if sys.platform == "win32":
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
    os.environ['TORCH_ALLOW_TF32_CUBLAS_OVERRIDE'] = '1'

try:
    from gui.main_window import main
    
    if __name__ == "__main__":
        print("🚀 Iniciando DAIA 2.0 GUI...")
        main()
        
except ImportError as e:
    print("❌ Error al importar módulos necesarios")
    print(f"   Detalle: {e}")
    print("\n💡 Solución:")
    print("   Instala las dependencias con:")
    print("   pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error inesperado: {e}")
    sys.exit(1)
