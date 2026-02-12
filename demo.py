#!/usr/bin/env python
"""
DAIA 2.0 - Quick Start Interactive Demo
Demostración interactiva del sistema completo
"""

import sys
import os
from pathlib import Path
import io

# Fix Windows encoding
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except:
        pass

sys.path.insert(0, str(Path(__file__).parent / "scripts"))

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

from lib_resources import ResourceManager, ConfigManager
from lib_transcription import create_transcriber
from lib_sentiment import create_sentiment_analyzer
from lib_qa import QARuleEngine
from lib_kpis import KPICalculator
from lib_database import DAIADatabase

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def demo_resources():
    """Demo 1: Resource Detection"""
    print_header("DEMO 1: DETECCIÓN DE RECURSOS")
    rm = ResourceManager()
    print(f"\n  GPU disponible: {rm.has_gpu}")
    print(f"  CPU cores: {rm.cpu_cores}")
    print(f"  RAM disponible: {rm.available_ram:.1f}GB / {rm.total_ram:.1f}GB")
    print(f"  Modelo Whisper seleccionado: {rm.get_whisper_model()}")
    print(f"  Configuración: FP16={rm.use_fp16} | Device={rm.device}")

def demo_config():
    """Demo 2: Configuration Loading"""
    print_header("DEMO 2: CARGA DE CONFIGURACIÓN")
    config = ConfigManager('config.yaml')
    print(f"\n  Versión DAIA: {config.get('version')}")
    print(f"  Idioma: {config.get('general.language')}")
    print(f"  Log level: {config.get('general.log_level')}")
    print(f"  Modelo sentimiento: {config.get('sentiment.model')}")
    
    # Show available levels
    levels = ['basic', 'standard', 'advanced']
    print(f"\n  Niveles de servicio disponibles:")
    for level in levels:
        rules = config.get(f'qa.rules.{level}')
        if rules:
            print(f"    - {level.upper()}: {len(rules)} reglas de QA")

def demo_sentiment():
    """Demo 3: Sentiment Analysis"""
    print_header("DEMO 3: ANÁLISIS DE SENTIMIENTO")
    config = ConfigManager('config.yaml')
    
    try:
        analyzer = create_sentiment_analyzer(config)
        
        test_texts = [
            "Este producto es excelente, muy recomendado",
            "El servicio fue deficiente y frustrante",
            "Es un producto normal, nada especial",
        ]
        
        for text in test_texts:
            result = analyzer.analyze_text(text)
            print(f"\n  Texto: \"{text}\"")
            print(f"  Sentimiento: {result['label'].upper()} (score: {result['score']:.3f})")
    except Exception as e:
        logger.error(f"Error en sentiment: {e}")

def demo_qa():
    """Demo 4: QA Engine"""
    print_header("DEMO 4: MOTOR DE QA (Calidad)")
    config = ConfigManager('config.yaml')
    
    # Create QA engine
    qa_engine = QARuleEngine(config.get('qa.rules'))
    
    # Sample transcripts
    test_transcripts = [
        {
            "level": "basic",
            "text": """Hola, buenos días. ¿Cómo puedo ayudarle?
            Cliente: Hola, tengo un problema con mi cuenta.
            Operador: Entiendo, déjeme revisar.
            [pausa]
            Operador: Ya está resuelto. ¿Hay algo más?"""
        },
        {
            "level": "standard", 
            "text": """Hola, buenos días. Bienvenido a nuestro servicio.
            Cliente: Necesito hablar sobre mi facturación.
            Operador: Claro, le ayudaremos con gusto.
            Cliente: La factura tiene error.
            Operador: Revisemos los detalles juntos."""
        }
    ]
    
    for test in test_transcripts:
        score = qa_engine.evaluate_call(test['text'], level=test['level'])
        print(f"\n  Nivel: {test['level'].upper()}")
        print(f"  Puntuación QA: {score['score']:.2f}/1.00")
        print(f"  Clasificación: {score['classification']}")

def demo_database():
    """Demo 5: Database Operations"""
    print_header("DEMO 5: OPERACIONES DE BASE DE DATOS")
    
    # Create demo database
    db = DAIADatabase('data/demo_daia.db')
    
    # Insert sample call
    db.insert_call(
        filename='demo_call.wav',
        duration=300,
        service_level='standard',
        audio_path='demo_call.wav'
    )
    
    # Query calls
    calls = db.select_calls_by_service_level('standard')
    print(f"\n  Llamadas guardadas en BD: {len(calls)}")
    
    for call in calls[:3]:  # Show first 3
        print(f"    - ID {call['id']}: {call['filename']} ({call['duration']}s)")
    
    db.close()
    print(f"  BD guardada en: data/demo_daia.db")

def demo_pipeline():
    """Demo 6: Pipeline Info"""
    print_header("DEMO 6: INFORMACIÓN DEL PIPELINE")
    
    print("""
  NIVELES DE SERVICIO:
  
  ⭐ BASIC (Rápido)
     • Transcripción + Risk Analysis
     • Tiempo: 2-5 min (GPU) | 10-30 min (CPU)
     • Mejor para: Análisis rápido
  
  ⭐⭐ STANDARD (Recomendado)
     • BASIC + Sentiment + QA + KPIs
     • Tiempo: 3-10 min (GPU) | 15-45 min (CPU)
     • Mejor para: Uso operacional normal
  
  ⭐⭐⭐ ADVANCED (Completo)
     • STANDARD + Pattern Detection + Anomalies
     • Tiempo: 5-15 min (GPU) | 20-60 min (CPU)
     • Mejor para: Análisis profundo
  
  MÉTODOS DISPONIBLES:
  
  1. Process single file:
     orchestrator.process_audio_file('audio.wav', 'standard')
  
  2. Process directory:
     orchestrator.process_audio_directory('audio_in/', 'standard')
  
  3. Custom analysis:
     Importa módulos individuales y combínalos
  """)

def main():
    """Run interactive demo"""
    print_header("DAIA 2.0 - SISTEMA DE AUDITORÍA DE LLAMADAS")
    print("\n  Bienvenido a DAIA 2.0 - Sistema 100% Local")
    print("  Versión: 2.0.0 | Status: ✅ PRODUCCIÓN LISTA")
    
    demos = [
        ("Detección de Recursos", demo_resources),
        ("Cargar Configuración", demo_config),
        ("Análisis de Sentimiento", demo_sentiment),
        ("Motor de QA", demo_qa),
        ("Base de Datos", demo_database),
        ("Pipeline & Niveles", demo_pipeline),
    ]
    
    print("\nDEMOSTRACIONES DISPONIBLES:")
    for i, (name, _) in enumerate(demos, 1):
        print(f"  {i}. {name}")
    print(f"  0. Ejecutar todas")
    print(f"  q. Salir")
    
    while True:
        try:
            choice = input("\n➡️  Selecciona opción (0-6, q): ").strip().lower()
            
            if choice == 'q':
                print("\n👋 ¡Hasta luego!")
                break
            elif choice == '0':
                for name, demo_func in demos:
                    try:
                        demo_func()
                    except Exception as e:
                        logger.error(f"Error en {name}: {e}")
                print_header("DEMOSTRACIÓN COMPLETADA")
                break
            elif choice.isdigit() and 0 < int(choice) <= len(demos):
                idx = int(choice) - 1
                name, demo_func = demos[idx]
                try:
                    demo_func()
                except Exception as e:
                    logger.error(f"Error: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("❌ Opción inválida")
        except KeyboardInterrupt:
            print("\n\n👋 Interrupción del usuario")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
