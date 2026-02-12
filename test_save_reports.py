#!/usr/bin/env python
"""
Script de prueba para verificar que los reportes se guarden correctamente
"""

import sys
import os
from pathlib import Path
from shutil import copyfile

# Fix PyTorch DLL loading on Windows Python 3.13
if sys.platform == "win32":
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
    os.environ['TORCH_ALLOW_TF32_CUBLAS_OVERRIDE'] = '1'

sys.path.insert(0, str(Path(__file__).parent / "scripts"))

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

from lib_resources import ConfigManager
from pipeline import PipelineOrchestrator
from process_audios import process_single_audio, ensure_directories


def ensure_test_audio():
    """Garantiza que el audio de prueba exista antes de procesar."""
    target = Path("audio_in/Grabación de llamada 1929_251211_145452.m4a")
    if target.exists():
        return target

    candidates = [
        Path("audio_in/Grabación de llamada 097748960_260115_102922.m4a"),
        Path("audio_in/llamada1.m4a"),
        Path("audio_in/llamada2.m4a"),
    ]
    source = next((c for c in candidates if c.exists()), None)
    if source:
        target.parent.mkdir(parents=True, exist_ok=True)
        copyfile(source, target)
        return target
    raise FileNotFoundError("No se encontró audio de prueba en audio_in/")

def main():
    """Función principal de prueba"""
    
    print("=" * 70)
    print("  PRUEBA DE GUARDADO DE REPORTES")
    print("=" * 70)
    
    # Asegurar directorios
    ensure_directories()
    audio_file = str(ensure_test_audio())
    
    # Inicializar sistema
    orchestrator = PipelineOrchestrator()
    
    logger.info(f"🔄 Procesando archivo de prueba: {audio_file}")
    logger.info("🔄 Nivel: standard")
    
    # Procesar
    result = process_single_audio(orchestrator, audio_file, service_level='standard')
    
    if result:
        print("\n" + "=" * 70)
        print("  ✅ PRUEBA EXITOSA")
        print("=" * 70)
        print(f"Estado: {result.get('status')}")
        print(f"QA Score: {result.get('qa_score', 0):.2%}")
        print("\nVerifica la carpeta 'reports/' para ver los archivos generados")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("  ❌ PRUEBA FALLIDA")
        print("=" * 70)

if __name__ == "__main__":
    main()
