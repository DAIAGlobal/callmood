#!/usr/bin/env python
"""
DAIA 2.0 - Complete System Test & Demo
Valida que todos los módulos funcionen correctamente.
"""

import sys
import os
from pathlib import Path
import io

# Fix for Windows console encoding sin cerrar stdout/stderr (evita conflicto con pytest)
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Agregar scripts al path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def cleanup_test_db():
    """Elimina la base de datos de prueba para dejar el entorno limpio."""
    test_db = Path("data/test_daia.db")
    try:
        if test_db.exists():
            test_db.unlink()
            logger.info("✓ Database de prueba eliminada (cleanup)")
    except Exception as e:
        logger.warning(f"⚠️ No se pudo limpiar DB de prueba: {e}")


def test_all_modules():
    """Prueba todos los módulos del sistema"""
    
    print("\n" + "="*70)
    print("DAIA 2.0 - SYSTEM VALIDATION TEST")
    print("="*70 + "\n")
    
    tests_passed = 0
    tests_failed = 0
    
    # 1. Test lib_resources
    try:
        logger.info("Testing lib_resources...")
        from lib_resources import ResourceManager, ConfigManager
        
        rm = ResourceManager()
        logger.info(f"  ✓ GPU: {rm.has_gpu}")
        logger.info(f"  ✓ CPU Cores: {rm.cpu_cores}")
        logger.info(f"  ✓ RAM: {rm.ram_available:.1f}GB")
        logger.info(f"  ✓ Whisper Model: {rm.get_whisper_model()}")
        
        config = ConfigManager("config.yaml")
        logger.info(f"  ✓ Config loaded: {config.get('general.version')}")
        
        tests_passed += 1
    except Exception as e:
        logger.error(f"  ✗ Error: {e}")
        tests_failed += 1
    
    # 2. Test lib_transcription
    try:
        logger.info("\nTesting lib_transcription...")
        from lib_transcription import create_transcriber
        
        transcriber = create_transcriber("config.yaml")
        logger.info(f"  ✓ Transcriber created")
        logger.info(f"  ✓ Model: {transcriber.model_name}")
        logger.info(f"  ✓ Device: {transcriber.device}")
        
        tests_passed += 1
    except Exception as e:
        logger.error(f"  ✗ Error: {e}")
        tests_failed += 1
    
    # 3. Test lib_sentiment
    try:
        logger.info("\nTesting lib_sentiment...")
        from lib_sentiment import create_sentiment_analyzer
        
        analyzer = create_sentiment_analyzer()
        test_text = "This is a great product! I love it."
        result = analyzer.analyze_text(test_text)
        logger.info(f"  ✓ Sentiment analyzer created")
        logger.info(f"  ✓ Test sentiment: {result['overall']} ({result['score']:.2f})")
        
        tests_passed += 1
    except Exception as e:
        logger.error(f"  ✗ Error: {e}")
        tests_failed += 1
    
    # 4. Test lib_qa
    try:
        logger.info("\nTesting lib_qa...")
        from lib_qa import QARuleEngine
        
        config = ConfigManager("config.yaml")
        rules = config.get("qa.rules")
        qa_engine = QARuleEngine(rules)
        
        test_transcript = "Buenos días, ¿cómo puedo ayudarle?"
        result = qa_engine.evaluate_call(test_transcript, level="basic")
        logger.info(f"  ✓ QA engine created")
        logger.info(f"  ✓ Test QA Score: {result['score']:.2f}")
        logger.info(f"  ✓ Classification: {result.get('classification')}")
        
        tests_passed += 1
    except Exception as e:
        logger.error(f"  ✗ Error: {e}")
        tests_failed += 1
    
    # 5. Test lib_kpis
    try:
        logger.info("\nTesting lib_kpis...")
        from lib_kpis import KPICalculator
        
        config = ConfigManager("config.yaml")
        kpi_calc = KPICalculator(config.get("kpis"))
        
        test_text = "Buenos días. ¿Cómo puedo ayudarle? " * 20
        kpis = kpi_calc.calculate_all_kpis(test_text, audio_duration=60)
        logger.info(f"  ✓ KPI calculator created")
        logger.info(f"  ✓ Metrics calculated: {len(kpis['metrics'])}")
        
        tests_passed += 1
    except Exception as e:
        logger.error(f"  ✗ Error: {e}")
        tests_failed += 1
    
    # 6. Test lib_database
    try:
        logger.info("\nTesting lib_database...")
        from lib_database import DAIADatabase
        
        db = DAIADatabase("data/test_daia.db")
        call_id = db.insert_call("test_call.wav", duration=60, service_level="standard")
        logger.info(f"  ✓ Database created")
        logger.info(f"  ✓ Test call inserted: ID {call_id}")
        
        db.insert_transcript(
            call_id,
            raw_text="Test transcript",
            cleaned_text="Test transcript"
        )
        logger.info(f"  ✓ Test transcript inserted")
        
        analysis = db.get_call_analysis(call_id)
        logger.info(f"  ✓ Call analysis retrieved")
        
        db.close()
        tests_passed += 1
    except Exception as e:
        logger.error(f"  ✗ Error: {e}")
        tests_failed += 1
    
    # 7. Test pipeline
    try:
        logger.info("\nTesting pipeline...")
        from pipeline import PipelineOrchestrator
        
        logger.info(f"  ✓ Pipeline module imported")
        logger.info(f"  ✓ PipelineOrchestrator class available")
        
        tests_passed += 1
    except Exception as e:
        logger.error(f"  ✗ Error: {e}")
        tests_failed += 1
    
    # Resumen
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"\n✓ Passed: {tests_passed}/7")
    print(f"✗ Failed: {tests_failed}/7")
    
    if tests_failed == 0:
        print("\n✅ ALL TESTS PASSED - DAIA 2.0 IS READY!")
        cleanup_test_db()
        return 0
    else:
        print("\n❌ SOME TESTS FAILED - CHECK ERRORS ABOVE")
        cleanup_test_db()
        return 1


if __name__ == "__main__":
    exit_code = test_all_modules()
    sys.exit(exit_code)
