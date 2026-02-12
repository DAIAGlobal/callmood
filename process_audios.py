#!/usr/bin/env python
"""
DAIA 2.0 - Procesar Audios Reales
Ejemplo de cómo procesar archivos de audio y generar reportes
"""

import sys
import os
import sqlite3
from pathlib import Path
import io
import json
from datetime import datetime

# Fix PyTorch DLL loading on Windows Python 3.13
if sys.platform == "win32":
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
    os.environ['TORCH_ALLOW_TF32_CUBLAS_OVERRIDE'] = '1'

# Fix Windows encoding
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except Exception as e:
        print(f"Warning: No se pudo establecer UTF-8: {e}", file=sys.stderr)

sys.path.insert(0, str(Path(__file__).parent / "scripts"))

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

from lib_resources import ConfigManager
from pipeline import PipelineOrchestrator
from lib_database import DAIADatabase

def ensure_directories():
    """Crear directorios necesarios"""
    dirs = [
        'audio_in',
        'reports',
        'analysis',
        'data'
    ]
    for d in dirs:
        Path(d).mkdir(exist_ok=True)
    logger.info(f"✓ Directorios verificados: {', '.join(dirs)}")

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def process_single_audio(orchestrator, audio_path, service_level='standard'):
    """Procesar un archivo de audio individual"""
    
    # Validar entrada
    if not audio_path or not isinstance(audio_path, str):
        logger.error(f"❌ Ruta inválida: {audio_path}")
        return None
    
    audio_path_obj = Path(audio_path)
    
    # Validar existencia
    if not audio_path_obj.exists():
        logger.error(f"❌ Archivo no encontrado: {audio_path}")
        return None
    
    # Validar tamaño
    file_size = audio_path_obj.stat().st_size
    if file_size == 0:
        logger.error(f"❌ Archivo vacío: {audio_path}")
        return None
    
    # Validar formato
    valid_extensions = ['.wav', '.mp3', '.m4a', '.ogg', '.flac']
    if audio_path_obj.suffix.lower() not in valid_extensions:
        logger.error(f"❌ Formato no soportado: {audio_path_obj.suffix}")
        return None
    
    # Validar nivel de servicio
    valid_levels = ['basic', 'standard', 'advanced']
    if service_level not in valid_levels:
        logger.warning(f"⚠️ Nivel '{service_level}' inválido, usando 'standard'")
        service_level = 'standard'
    
    logger.info(f"🔄 Procesando: {audio_path} (Nivel: {service_level})")
    
    try:
        result = orchestrator.process_audio_file(
            audio_path,
            service_level=service_level
        )
        
        if not result:
            logger.error(f"❌ Resultado nulo para: {audio_path}")
            return None
        
        if result.get('status') == 'completed':
            logger.info(f"✅ Completado: {audio_path}")
            
            # Guardar reportes automáticamente
            logger.info("💾 Guardando reportes...")
            json_path = save_json_report(result)
            txt_path = save_text_report(result)
            db_id = save_to_database(orchestrator, result)
            
            if json_path:
                logger.info(f"✓ Reporte JSON: {json_path}")
            if txt_path:
                logger.info(f"✓ Reporte TXT: {txt_path}")
            if db_id:
                logger.info(f"✓ BD: Llamada #{db_id}")
            
            return result
        else:
            error_msg = result.get('error', 'Unknown error')
            logger.error(f"❌ Error: {error_msg}")
            return None
            
    except ValueError as e:
        logger.error(f"❌ Valor inválido: {e}")
        return None
    except RuntimeError as e:
        logger.error(f"❌ Error de runtime: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Excepción inesperada: {type(e).__name__}: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return None

def process_directory(orchestrator, audio_dir='audio_in', service_level='standard'):
    """Procesar todos los audios en un directorio"""
    
    audio_path = Path(audio_dir)
    
    # Buscar archivos de audio
    audio_files = list(audio_path.glob('*.wav'))
    audio_files += list(audio_path.glob('*.mp3'))
    audio_files += list(audio_path.glob('*.m4a'))
    audio_files += list(audio_path.glob('*.ogg'))
    audio_files += list(audio_path.glob('*.flac'))
    
    if not audio_files:
        logger.warning(f"⚠️  No se encontraron archivos de audio en {audio_dir}")
        return []
    
    logger.info(f"📊 Encontrados {len(audio_files)} archivo(s) de audio")
    
    results = []
    for i, audio_file in enumerate(audio_files, 1):
        logger.info(f"\n[{i}/{len(audio_files)}] Procesando: {audio_file.name}")
        
        result = orchestrator.process_audio_file(
            str(audio_file),
            service_level=service_level
        )
        
        if result and result['status'] == 'completed':
            results.append(result)
            qa_data = result.get('qa', {})
            qa_pct = qa_data.get('compliance_percentage', result.get('qa_percentage', result.get('qa_score', 0)*100))
            sentiment = result.get('data', {}).get('sentiment', result.get('sentiment', {}))
            sentiment_label = sentiment.get('label', sentiment.get('overall', 'N/A'))
            logger.info(f"✅ OK - QA: {qa_pct:.1f}% | Sent: {sentiment_label}")
            
            # Guardar reportes automáticamente
            logger.info("💾 Guardando reportes...")
            json_path = save_json_report(result)
            txt_path = save_text_report(result)
            db_id = save_to_database(orchestrator, result)
            
            if json_path:
                logger.info(f"✓ Reporte JSON: {json_path}")
            if txt_path:
                logger.info(f"✓ Reporte TXT: {txt_path}")
            if db_id:
                logger.info(f"✓ BD: Llamada #{db_id}")
        else:
            logger.error(f"❌ FALLIDO")
    
    return results

def save_json_report(result, output_dir='reports'):
    """Guardar resultado como JSON"""
    try:
        # Validar resultado
        if not result or not isinstance(result, dict):
            logger.error(f"❌ Resultado inválido para JSON")
            return None
        
        # Crear directorio
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Crear nombre de archivo basado en timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename_base = Path(result.get('audio_file', 'unknown')).stem
        if not filename_base or filename_base == 'unknown':
            filename_base = 'report'
        
        filename = f"{timestamp}_{filename_base}.json"
        filepath = output_path / filename
        
        # Preparar datos serializables
        data = result.get('data', {})
        transcript_text = data.get('transcription', {}).get('text', '')
        
        report_data = {
            'timestamp': timestamp,
            'filename': result.get('audio_file', 'unknown'),
            'duration': result.get('duration', 0),
            'service_level': result.get('service_level', 'standard'),
            'status': result.get('status', 'unknown'),
            'transcript': transcript_text[:500] + '...' if len(transcript_text) > 500 else transcript_text,
            'qa': data.get('qa', {}),
            'sentiment': data.get('sentiment', {}),
            'risk': data.get('risk', {}),
            'kpis': data.get('kpis', {}),
            'patterns': data.get('patterns', []),
            'anomalies': data.get('anomalies', [])
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"✓ JSON guardado: {filepath}")
        return str(filepath)
        
    except IOError as e:
        logger.error(f"❌ Error de I/O al guardar JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Error guardando JSON: {e}")
        return None

def save_text_report(result, output_dir='reports'):
    """Guardar resultado como texto formateado profesional"""
    try:
        # Validar resultado
        if not result or not isinstance(result, dict):
            logger.error(f"❌ Resultado inválido para texto")
            return None
        
        # Crear directorio
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename_base = Path(result.get('audio_file', 'unknown')).stem
        if not filename_base or filename_base == 'unknown':
            filename_base = 'report'
        
        filename = f"{timestamp}_{filename_base}.txt"
        filepath = output_path / filename
        
        data = result.get('data', {})
        transcript_data = data.get('transcription', {})
        qa_data = data.get('qa', {})
        sentiment_data = data.get('sentiment', {})
        risk_data = data.get('risk', {})
        kpis_data = data.get('kpis', {})
        patterns_data = data.get('patterns', [])
        anomalies_data = data.get('anomalies', [])
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("DAIA 2.0 - REPORTE DE ANÁLISIS DE LLAMADA\n")
            f.write("=" * 80 + "\n\n")
            
            # INFORMACIÓN GENERAL
            f.write("-" * 80 + "\n")
            f.write("📋 INFORMACIÓN GENERAL\n")
            f.write("-" * 80 + "\n")
            f.write(f"Archivo: {result.get('audio_file', 'N/A')}\n")
            duration = result.get('duration', 0)
            f.write(f"Duración: {duration} segundos ({int(duration)//60}min {int(duration)%60}s)\n")
            f.write(f"Nivel de análisis: {result.get('service_level', 'N/A').upper()}\n")
            f.write(f"Procesado: {timestamp}\n")
            f.write(f"Estado: {result.get('status', 'N/A').upper()}\n\n")
            
            # RESUMEN EJECUTIVO
            f.write("-" * 80 + "\n")
            f.write("🎯 RESUMEN EJECUTIVO\n")
            f.write("-" * 80 + "\n")
            
            qa_score = qa_data.get('compliance_percentage', 0)
            qa_class = qa_data.get('classification', 'N/A')
            risk_level = risk_data.get('level', 'N/A')
            
            overall_sent = sentiment_data.get('overall', {})
            if isinstance(overall_sent, dict):
                sentiment_label = overall_sent.get('label', 'N/A')
                sentiment_conf = overall_sent.get('confidence', 0)
            else:
                sentiment_label = str(overall_sent)
                sentiment_conf = sentiment_data.get('confidence', 0)
            
            f.write(f"\n📊 Calidad General: {qa_class}\n")
            f.write(f"   • Cumplimiento QA: {qa_score:.1f}%\n")
            eval_status = '✅ APROBADO' if qa_score >= 70 else '❌ NO CUMPLE' if qa_score < 50 else '⚠️ MEJORABLE'
            f.write(f"   • Evaluación: {eval_status}\n\n")
            
            f.write(f"😊 Análisis Emocional: {str(sentiment_label).upper().replace('_', ' ')}\n")
            f.write(f"   • Confianza: {sentiment_conf:.1%}\n")
            sent_status = '✅ Positivo' if 'positive' in str(sentiment_label).lower() else '❌ Negativo' if 'negative' in str(sentiment_label).lower() else '⚪ Neutral'
            f.write(f"   • Valoración: {sent_status}\n\n")
            
            f.write(f"⚠️ Nivel de Riesgo: {risk_level}\n")
            critical_keywords = risk_data.get('critical_found', [])
            if critical_keywords:
                f.write(f"   • Palabras críticas: {', '.join(critical_keywords)}\n")
            risk_status = '🔴 CRÍTICO - Requiere atención' if risk_level == 'CRITICAL' else '🟡 MEDIO - Supervisar' if risk_level == 'MEDIUM' else '🟢 BAJO - Normal'
            f.write(f"   • Estado: {risk_status}\n\n")
            
            # ANÁLISIS EMOCIONAL DETALLADO
            if sentiment_data.get('segments'):
                f.write("-" * 80 + "\n")
                f.write("💭 ANÁLISIS EMOCIONAL POR SEGMENTO\n")
                f.write("-" * 80 + "\n\n")
                
                segments = sentiment_data.get('segments', [])
                for i, seg in enumerate(segments[:5], 1):
                    seg_label = seg.get('label', 'unknown')
                    seg_conf = seg.get('confidence', 0)
                    seg_text = seg.get('text', '')[:100]
                    
                    emoji = "😊" if 'positive' in str(seg_label).lower() else "😞" if 'negative' in str(seg_label).lower() else "😐"
                    f.write(f"{emoji} Segmento {i}: {str(seg_label).upper().replace('_', ' ')} ({seg_conf:.1%})\n")
                    f.write(f'   "{seg_text}..."\n\n')
            
            # TRANSCRIPCIÓN
            f.write("-" * 80 + "\n")
            f.write("📝 TRANSCRIPCIÓN\n")
            f.write("-" * 80 + "\n")
            transcript_text = transcript_data.get('text', 'No disponible')
            f.write(transcript_text[:1000] + ("..." if len(transcript_text) > 1000 else "") + "\n\n")
            
            # MÉTRICAS DE CALIDAD (QA)
            f.write("-" * 80 + "\n")
            f.write("✅ EVALUACIÓN DE CALIDAD (QA)\n")
            f.write("-" * 80 + "\n")
            f.write(f"Puntuación: {qa_score:.1f}%\n")
            f.write(f"Clasificación: {qa_class}\n")
            f.write(f"Nivel evaluado: {qa_data.get('level', 'N/A')}\n\n")
            
            if qa_data.get('details'):
                f.write("Detalles por categoría:\n")
                for detail in qa_data.get('details', []):
                    check_type = detail.get('check_type', 'N/A')
                    passed = detail.get('passed', False)
                    status_icon = "✅" if passed else "❌"
                    f.write(f"  {status_icon} {check_type}\n")
            f.write("\n")
            
            # KPIs OPERACIONALES
            if kpis_data:
                f.write("-" * 80 + "\n")
                f.write("📊 MÉTRICAS OPERACIONALES (KPIs)\n")
                f.write("-" * 80 + "\n\n")
                
                metrics = kpis_data.get('metrics', {})
                for metric_name, metric_info in metrics.items():
                    value = metric_info.get('value', 'N/A')
                    classification = metric_info.get('classification', '')
                    unit = metric_info.get('unit', '')
                    
                    f.write(f"• {metric_name.replace('_', ' ').title()}: {value}{unit}")
                    if classification:
                        f.write(f" ({classification})")
                    f.write("\n")
                f.write("\n")
            
            # PATRONES DETECTADOS
            if patterns_data:
                f.write("-" * 80 + "\n")
                f.write("🔍 PATRONES DE CONVERSACIÓN DETECTADOS\n")
                f.write("-" * 80 + "\n")
                for pattern in patterns_data:
                    f.write(f"  • {pattern.get('type', 'N/A')}: {pattern.get('description', 'N/A')}\n")
                f.write("\n")
            
            # ANOMALÍAS
            if anomalies_data:
                f.write("-" * 80 + "\n")
                f.write("⚠️ ANOMALÍAS DETECTADAS\n")
                f.write("-" * 80 + "\n")
                for anomaly in anomalies_data:
                    f.write(f"  ⚠️ {anomaly.get('type', 'N/A')}: {anomaly.get('description', 'N/A')}\n")
                f.write("\n")
            
            # RECOMENDACIONES
            f.write("-" * 80 + "\n")
            f.write("💡 RECOMENDACIONES\n")
            f.write("-" * 80 + "\n")
            
            if qa_score < 50:
                f.write("  🔴 CRÍTICO: Llamada no cumple estándares mínimos de calidad\n")
                f.write("     - Revisar protocolo de atención\n")
                f.write("     - Capacitación urgente requerida\n")
            elif qa_score < 70:
                f.write("  🟡 ATENCIÓN: Llamada requiere mejoras\n")
                f.write("     - Reforzar cumplimiento de procedimientos\n")
                f.write("     - Supervisión cercana recomendada\n")
            else:
                f.write("  🟢 SATISFACTORIO: Llamada cumple estándares\n")
                f.write("     - Mantener nivel de servicio\n")
            
            if 'negative' in str(sentiment_label).lower():
                f.write("  😞 Sentimiento negativo detectado\n")
                f.write("     - Evaluar satisfacción del cliente\n")
                f.write("     - Considerar follow-up\n")
            
            if risk_level in ['CRITICAL', 'HIGH']:
                f.write(f"  ⚠️ Riesgo {risk_level} identificado\n")
                f.write("     - Revisión inmediata requerida\n")
                f.write("     - Escalación a supervisor\n")
            
            f.write("\n")
            f.write("=" * 80 + "\n")
            f.write("Fin del Reporte\n")
            f.write("=" * 80 + "\n")
        
        logger.info(f"✓ Reporte TXT guardado: {filepath}")
        return str(filepath)
        
    except IOError as e:
        logger.error(f"❌ Error de I/O guardando reporte: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Error guardando reporte: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return None

def save_to_database(orchestrator, result):
    """Guardar resultado en base de datos con manejo transaccional"""
    
    # Validar resultado
    if not result or not isinstance(result, dict):
        logger.error(f"❌ Resultado inválido para BD")
        return None
    
    # Verificar que tenga los campos necesarios (pero permitir duration=0)
    if not result.get('audio_file'):
        logger.error(f"❌ Datos requeridos faltantes en resultado: audio_file")
        return None
    
    if 'duration' not in result:
        logger.warning(f"⚠️ Duración no encontrada en resultado, usando 0")
        result['duration'] = 0
    
    db = None
    try:
        db = DAIADatabase('data/daia_audit.db')
        
        # Si ya existe call_id en result (pipeline ya lo insertó), usarlo
        # De lo contrario, insertar nuevo registro
        if result.get('call_id'):
            call_id = result['call_id']
            logger.debug(f"✓ Usando call_id existente: {call_id}")
        else:
            # Insert call
            call_id = db.insert_call(
                filename=result.get('audio_file', 'unknown'),
                duration=result.get('duration', 0),
                service_level=result.get('service_level', 'standard'),
                audio_path=result.get('audio_file', 'unknown')
            )
            
            if not call_id:
                logger.error(f"❌ No se pudo crear registro de llamada")
                return None
            
            logger.debug(f"✓ Llamada registrada con ID: {call_id}")
        
        # Insert transcript (si está disponible)
        data = result.get('data', {})
        transcript_data = data.get('transcription', {})
        if transcript_data.get('text'):
            try:
                db.insert_transcript(
                    call_id=call_id,
                    text_raw=transcript_data.get('text', ''),
                    text_clean=transcript_data.get('text', ''),
                    language=orchestrator.config.get('general.language', 'es'),
                    model_used=transcript_data.get('model_used', 'whisper')
                )
                logger.debug(f"✓ Transcripción guardada")
            except Exception as e:
                logger.warning(f"⚠️ Error guardando transcripción: {e}")
        
        # Insert QA
        qa_data = data.get('qa', {})
        if qa_data:
            try:
                db.insert_qa_score(call_id=call_id, qa_result=qa_data)
                logger.debug("✓ QA score guardado")
            except Exception as e:
                logger.warning(f"⚠️ Error guardando QA: {e}")
        
        # Insert risk
        risk_data = data.get('risk', {})
        if risk_data:
            try:
                db.insert_risk_assessment(call_id=call_id, risk_result=risk_data)
                logger.debug("✓ Análisis de riesgo guardado")
            except Exception as e:
                logger.warning(f"⚠️ Error guardando riesgo: {e}")
        
        # Insert sentiment
        sentiment_data = data.get('sentiment', {})
        if sentiment_data:
            try:
                db.insert_sentiment_analysis(call_id=call_id, sentiment_result=sentiment_data)
                logger.debug("✓ Análisis de sentimiento guardado")
            except Exception as e:
                logger.warning(f"⚠️ Error guardando sentimiento: {e}")
        
        logger.info(f"✓ Registro completo guardado en BD (ID: {call_id})")
        return call_id
        
    except sqlite3.IntegrityError as e:
        logger.error(f"❌ Error de integridad BD: {e}")
        return None
    except sqlite3.DatabaseError as e:
        logger.error(f"❌ Error de BD: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Error inesperado al guardar en BD: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return None
    finally:
        if db:
            try:
                db.close()
            except Exception as e:
                logger.warning(f"⚠️ Error cerrando BD: {e}")

def main():
    """Menú interactivo principal"""
    
    print_header("DAIA 2.0 - Audit & Compliance System")
    print("Inicializando...")
    
    # Ensure directories exist
    ensure_directories()
    
    # Initialize orchestrator
    try:
        config_path = 'config.yaml'
        orchestrator = PipelineOrchestrator(config_path)
        logger.info("✓ Pipeline inicializado")
    except Exception as e:
        logger.error(f"❌ Error inicializando pipeline: {e}")
        return
    
    while True:
        print("\n" + "=" * 70)
        print("  MENÚ PRINCIPAL")
        print("=" * 70)
        print("1. Procesar un archivo de audio")
        print("2. Procesar carpeta completa (audio_in/)")
        print("3. Ver últimos reportes")
        print("4. Salir")
        print("=" * 70)
        
        choice = input("\nSelecciona una opción (1-4): ").strip()
        
        if choice == '1':
            # Process single file
            audio_file = input("Ruta del archivo de audio: ").strip()
            if audio_file:
                level = input("Nivel de análisis (basic/standard/advanced) [standard]: ").strip()
                level = level if level in ['basic', 'standard', 'advanced'] else 'standard'
                
                result = process_single_audio(orchestrator, audio_file, service_level=level)
                
                if result:
                    print_header("Resultado del Procesamiento")
                    qa_pct = result.get('qa_percentage', result.get('qa', {}).get('compliance_percentage', 0))
                    sentiment = result.get('data', {}).get('sentiment', result.get('sentiment', {}))
                    sentiment_label = sentiment.get('label', sentiment.get('overall', 'N/A'))
                    print(f"Estado: {result.get('status')}")
                    print(f"Duración: {result.get('duration')} segundos")
                    print(f"QA Score: {qa_pct:.1f}%")
                    print(f"Sentimiento: {sentiment_label}")
                    print("✓ Reportes guardados automáticamente")
        
        elif choice == '2':
            # Process directory
            results = process_directory(orchestrator)
            
            if results:
                print_header(f"Resumen: {len(results)} archivo(s) procesados")
                
                qa_pcts = [r.get('qa_percentage', r.get('qa', {}).get('compliance_percentage', r.get('qa_score', 0)*100)) for r in results]
                total_qa = sum(qa_pcts) / len(qa_pcts)
                print(f"QA Promedio: {total_qa:.1f}%")
                print("✓ Reportes guardados automáticamente para todos los archivos")
        
        elif choice == '3':
            # List recent reports
            reports_dir = Path('reports')
            if reports_dir.exists():
                files = sorted(reports_dir.glob('*.txt'), reverse=True)[:5]
                if files:
                    print_header("Últimos Reportes")
                    for f in files:
                        print(f"• {f.name}")
                else:
                    print("No hay reportes disponibles")
            else:
                print("Carpeta de reportes no existe")
        
        elif choice == '4':
            print("\n👋 ¡Hasta luego!")
            break
        
        else:
            print("❌ Opción inválida")

if __name__ == "__main__":
    main()
