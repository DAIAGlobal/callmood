"""
DAIA - Pipeline Orchestrator (Modular & Hierarchical)
Orquestación de análisis según nivel de servicio.
100% Local, 0 USD, Control Total.

NIVELES:
  basic    → Transcripción + Riesgo
  standard → + Sentimiento + QA + KPIs
  advanced → + Patrones + Anomalías
"""

import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import json

from lib_resources import ResourceManager, ConfigManager
from lib_transcription import WhisperTranscriber
from lib_speaker import SpeakerRoleAnalyzer
from lib_sentiment import LocalSentimentAnalyzer
from lib_qa import QARuleEngine
from lib_kpis import KPICalculator
from lib_database import DAIADatabase
from rules_engine import RuleSetRepository, RuleEngine

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Orquestador principal del pipeline modular"""
    
    def __init__(self, config_path: str = "config.yaml", db_path: str = "data/daia_audit.db"):
        """
        Inicializa el orquestador del pipeline con validaciones.
        
        Args:
            config_path: Ruta del archivo de configuración
            db_path: Ruta de la base de datos SQLite
        """
        try:
            # Configuración
            logger.info("Cargando configuración...")
            self.config = ConfigManager(config_path)
            self.config.validate()
            logger.info("✓ Configuración validada")
            
        except Exception as e:
            logger.error(f"❌ Error en configuración: {e}")
            raise
        
        try:
            # Recursos
            logger.info("Inicializando recursos...")
            self.rm = ResourceManager()
            self.rm.log_summary()
            logger.info("✓ Recursos disponibles")
            
        except Exception as e:
            logger.error(f"❌ Error en recursos: {e}")
            raise
        
        try:
            # Módulos
            logger.info("Cargando módulos...")
            self.transcriber = WhisperTranscriber(self.config, self.rm)
            logger.debug("✓ Transcriber cargado")
            
            self.sentiment_analyzer = LocalSentimentAnalyzer()
            logger.debug("✓ Sentiment analyzer cargado")

            self.speaker_analyzer = SpeakerRoleAnalyzer(
                self.transcriber,
                self.sentiment_analyzer
            )
            
            qa_rules = self.config.get("qa.rules")
            if not qa_rules:
                logger.error("❌ Reglas QA no encontradas en config")
                raise ValueError("QA rules not configured")
            
            self.qa_engine = QARuleEngine(qa_rules)
            logger.debug("✓ QA engine cargado")
            
            kpis_config = self.config.get("kpis")
            if not kpis_config:
                logger.error("❌ KPIs no configurados")
                raise ValueError("KPIs not configured")
            
            self.kpi_calculator = KPICalculator(kpis_config)
            logger.debug("✓ KPI calculator cargado")
            self.rules_repo = RuleSetRepository()
            self.rules_engine = RuleEngine(self.rules_repo)
            logger.debug("✓ Rules engine cargado")
            
        except Exception as e:
            logger.error(f"❌ Error cargando módulos: {e}")
            raise
        
        try:
            # Database
            logger.info("Inicializando base de datos...")
            self.db = DAIADatabase(db_path)
            logger.info("✓ Base de datos iniciada")
            
        except Exception as e:
            logger.error(f"❌ Error en BD: {e}")
            raise
        
        logger.info("✓ Pipeline Orchestrator inicializado correctamente")
    
    def process_audio_directory(self, audio_dir: str, service_level: str = "standard",
                               parallel: bool = True) -> List[Dict]:
        """
        Procesa directorio completo de audios.
        
        Args:
            audio_dir: Directorio con archivos de audio
            service_level: 'basic', 'standard' o 'advanced'
            parallel: Procesar en paralelo
            
        Returns:
            list: Resultados de procesamiento
        """
        audio_dir = Path(audio_dir)
        
        if not audio_dir.exists():
            logger.error(f"Directorio no encontrado: {audio_dir}")
            return []
        
        # Encontrar archivos de audio
        audio_extensions = self.config.get(
            "transcription.audio_extensions",
            ['.wav', '.mp3', '.m4a', '.ogg', '.flac']
        )
        
        audio_files = [
            f for f in audio_dir.iterdir()
            if f.suffix.lower() in audio_extensions
        ]
        
        logger.info(f"Encontrados {len(audio_files)} archivos de audio")
        logger.info(f"Nivel de servicio: {service_level.upper()}")
        
        results = []
        
        if parallel and len(audio_files) > 1:
            # Procesamiento paralelo
            max_workers = self.rm.get_worker_threads()
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(self.process_audio_file, str(f), service_level)
                    for f in audio_files
                ]
                
                for i, future in enumerate(futures, 1):
                    try:
                        result = future.result(timeout=self.config.get(
                            "pipeline.execution.timeout_per_file", 3600
                        ))
                        results.append(result)
                        logger.info(f"[{i}/{len(audio_files)}] ✓ Completado: {result.get('filename')}")
                    except Exception as e:
                        logger.error(f"[{i}/{len(audio_files)}] ✗ Error procesando: {e}")
        else:
            # Procesamiento secuencial
            for i, audio_file in enumerate(audio_files, 1):
                try:
                    result = self.process_audio_file(str(audio_file), service_level)
                    results.append(result)
                    logger.info(f"[{i}/{len(audio_files)}] ✓ Completado: {result.get('filename')}")
                except Exception as e:
                    logger.error(f"[{i}/{len(audio_files)}] ✗ Error procesando: {e}")
        
        logger.info(f"\n✓ Pipeline completado: {len(results)}/{len(audio_files)} exitosos\n")
        return results
    
    def process_audio_file(self, audio_path: str, service_level: str = "standard") -> Dict:
        """
        Procesa un archivo de audio individual con manejo robusto de errores.
        
        Args:
            audio_path: Ruta del archivo de audio
            service_level: 'basic', 'standard' o 'advanced'
            
        Returns:
            dict: Resultado completo del análisis
        """
        # Validar entrada
        if not audio_path or not isinstance(audio_path, str):
            logger.error(f"❌ Ruta inválida: {audio_path}")
            return {
                'status': 'error',
                'error': 'Invalid audio path',
                'data': {}
            }
        
        audio_path = Path(audio_path)
        start_time = time.time()
        
        # Validar que el archivo existe
        if not audio_path.exists():
            logger.error(f"❌ Archivo no encontrado: {audio_path}")
            return {
                'filename': str(audio_path),
                'status': 'error',
                'error': f'File not found: {audio_path}',
                'data': {}
            }
        
        logger.info(f"\n{'='*70}")
        logger.info(f"PROCESANDO: {audio_path.name}")
        logger.info(f"{'='*70}")
        
        # Verificar nivel válido
        valid_levels = ["basic", "standard", "advanced"]
        if service_level not in valid_levels:
            logger.warning(f"⚠️ Nivel '{service_level}' inválido, usando 'standard'")
            service_level = "standard"
        
        result = {
            'filename': audio_path.name,
            'audio_file': str(audio_path),
            'service_level': service_level,
            'status': 'processing',
            'steps_completed': [],
            'errors': [],
            'data': {}
        }
        
        call_id = None
        
        try:
            # Insertar en BD
            call_id = self.db.insert_call(
                str(audio_path),
                service_level=service_level
            )
            
            if not call_id:
                raise Exception("No se pudo crear registro de llamada en BD")
            
            result['call_id'] = call_id
            logger.debug(f"✓ Llamada registrada con ID: {call_id}")
            
            # PASO 1: TRANSCRIPCIÓN + HABLANTES (todos los niveles)
            logger.info("→ Transcribiendo audio y detectando hablantes...")
            speaker_data = self.speaker_analyzer.process_audio(str(audio_path))
            transcript_result = speaker_data.get('transcript')
            speaker_summary = speaker_data.get('speaker_summary', {})
            
            if not transcript_result or not transcript_result.get('text'):
                raise Exception("Fallo en transcripción: resultado vacío")
            
            # Guardar en BD
            try:
                self.db.insert_transcript(
                    call_id,
                    text_raw=transcript_result['text'],
                    text_clean=transcript_result['text'],
                    language=transcript_result.get('language', 'es'),
                    model_used=transcript_result.get('model_used', 'whisper'),
                    device_used=transcript_result.get('device_used', 'cpu')
                )
            except Exception as e:
                logger.warning(f"⚠️ Error guardando transcripción en BD: {e}")
            
            result['data']['transcription'] = transcript_result
            result['data']['speaker'] = speaker_summary
            result['duration'] = transcript_result.get('duration', 0)
            result['steps_completed'].append('transcription')
            logger.info(f"✓ Transcripción + hablantes completada ({len(transcript_result['text'])} caracteres)")
            
            # PASO 2: ANÁLISIS DE RIESGO (todos los niveles)
            try:
                logger.info("→ Analizando riesgos...")
                risk_result = self._analyze_risk(transcript_result['text'])
                
                try:
                    self.db.insert_risk_assessment(call_id, risk_result)
                except Exception as e:
                    logger.warning(f"⚠️ Error guardando riesgo en BD: {e}")
                
                result['data']['risk'] = risk_result
                result['steps_completed'].append('risk_analysis')
                logger.info(f"✓ Riesgo: {risk_result['level']}")
            except Exception as e:
                logger.error(f"❌ Error en análisis de riesgo: {e}")
                result['errors'].append(f"Risk analysis failed: {e}")
                result['data']['risk'] = {'level': 'UNKNOWN', 'score': 0}
            
            # PASO 3: ANÁLISIS DE SENTIMIENTO (standard+)
            if service_level in ["standard", "advanced"]:
                try:
                    logger.info("→ Analizando sentimiento...")
                    sentiment_result = (
                        transcript_result.get('sentiment_by_role')
                        or self.sentiment_analyzer.analyze_conversation(
                            transcript_result['text'],
                            speaker_markers={'operator': 'OPERATOR', 'client': 'CLIENT'}
                        )
                    )
                    
                    try:
                        self.db.insert_sentiment_analysis(call_id, sentiment_result)
                    except Exception as e:
                        logger.warning(f"⚠️ Error guardando sentimiento en BD: {e}")
                    
                    result['data']['sentiment'] = sentiment_result
                    result['steps_completed'].append('sentiment_analysis')
                    logger.info(f"✓ Sentimiento: {sentiment_result['overall']}")
                except Exception as e:
                    logger.error(f"❌ Error en análisis de sentimiento: {e}")
                    result['errors'].append(f"Sentiment analysis failed: {e}")
                    result['data']['sentiment'] = {'overall': 'unknown', 'score': 0}
            
            # PASO 4: QA (standard+)
            if service_level in ["standard", "advanced"]:
                try:
                    logger.info("→ Evaluando calidad (QA)...")
                    qa_result = self.qa_engine.evaluate_call(
                        transcript_result['text'],
                        level=service_level
                    )
                    
                    try:
                        self.db.insert_qa_score(call_id, qa_result)
                    except Exception as e:
                        logger.warning(f"⚠️ Error guardando QA en BD: {e}")
                    
                    result['data']['qa'] = qa_result
                    # Exponer métricas resumidas al toplevel para UI/CLI
                    result['qa_score'] = qa_result.get('compliance_percentage', 0) / 100.0
                    result['qa_percentage'] = qa_result.get('compliance_percentage', 0)
                    result['steps_completed'].append('qa_evaluation')
                    logger.info(f"✓ Cumplimiento QA: {qa_result.get('compliance_percentage', 0):.1f}%")
                except Exception as e:
                    logger.error(f"❌ Error en QA: {e}")
                    result['errors'].append(f"QA evaluation failed: {e}")
                    result['data']['qa'] = {'compliance_percentage': 0, 'classification': 'ERROR'}
            
            # PASO 5: KPIs (standard+)
            if service_level in ["standard", "advanced"]:
                try:
                    logger.info("→ Calculando KPIs...")
                    kpi_result = self.kpi_calculator.calculate_all_kpis(
                        transcript_result['text'],
                        audio_duration=transcript_result.get('duration'),
                        speaker_summary=speaker_summary
                    )
                    
                    try:
                        self.db.insert_kpi_metrics(call_id, kpi_result)
                    except Exception as e:
                        logger.warning(f"⚠️ Error guardando KPIs en BD: {e}")
                    
                    result['data']['kpis'] = kpi_result
                    result['steps_completed'].append('kpi_calculation')
                    logger.info("✓ KPIs calculados")
                except Exception as e:
                    logger.error(f"❌ Error calculando KPIs: {e}")
                    result['errors'].append(f"KPI calculation failed: {e}")
                    result['data']['kpis'] = {'metrics': {}}
            
            # PASO 6: PATRONES (advanced)
            if service_level == "advanced":
                try:
                    logger.info("→ Detectando patrones...")
                    patterns = self._detect_patterns(transcript_result['text'])
                    result['data']['patterns'] = patterns
                    result['steps_completed'].append('pattern_detection')
                    logger.info(f"✓ {len(patterns)} patrones detectados")
                except Exception as e:
                    logger.error(f"❌ Error detectando patrones: {e}")
                    result['errors'].append(f"Pattern detection failed: {e}")
                    result['data']['patterns'] = []
            
            # PASO 7: ANOMALÍAS (advanced)
            if service_level == "advanced":
                try:
                    logger.info("→ Detectando anomalías...")
                    anomalies = self._detect_anomalies(result['data'])
                    result['data']['anomalies'] = anomalies
                    result['steps_completed'].append('anomaly_detection')
                    logger.info(f"✓ {len(anomalies)} anomalías detectadas")
                except Exception as e:
                    logger.error(f"❌ Error detectando anomalías: {e}")
                    result['errors'].append(f"Anomaly detection failed: {e}")
                    result['data']['anomalies'] = []
            
            # Marcar como completado
            result['status'] = 'completed'
            try:
                self.db.update_call_status(call_id, 'completed')
            except Exception as e:
                logger.warning(f"⚠️ Error marcando como completado: {e}")
            
            # Tiempo total
            elapsed = time.time() - start_time
            result['processing_time_seconds'] = elapsed
            
            logger.info(f"\n✓ PROCESAMIENTO EXITOSO en {elapsed:.1f}s")
            logger.info(f"{'='*70}\n")
            
            return result
            
        except Exception as e:
            logger.error(f"✗ Error procesando {audio_path.name}: {e}")
            result['status'] = 'error'
            result['errors'].append(str(e))
            
            if 'call_id' in result:
                self.db.update_call_status(result['call_id'], 'error', str(e))
            
            return result
    
    def _analyze_risk(self, transcript: str) -> Dict:
        """Análisis de riesgo"""
        text_lower = transcript.lower()
        risk_config = self.config.get("risk_analysis")
        
        critical_found = []
        warnings_found = []
        score = 0
        
        # Buscar palabras críticas
        critical_keywords = risk_config['keywords']['critical'].get('list', [])
        for keyword in critical_keywords:
            if keyword in text_lower:
                critical_found.append(keyword)
                score += risk_config['keywords']['critical'].get('weight', 3)
        
        # Buscar palabras de advertencia
        warning_keywords = risk_config['keywords']['warning'].get('list', [])
        for keyword in warning_keywords:
            if keyword in text_lower:
                warnings_found.append(keyword)
                score += risk_config['keywords']['warning'].get('weight', 1)
        
        # Clasificar riesgo
        thresholds = risk_config['thresholds']
        if score >= thresholds['critical']:
            level = 'CRÍTICO'
        elif score >= thresholds['high']:
            level = 'ALTO'
        elif score >= thresholds['medium']:
            level = 'MEDIO'
        else:
            level = 'BAJO'

        # Reglas dinámicas (chat de reglas)
        rules_engine_result = {}
        try:
            user_id = os.environ.get("DAIA_RULES_USER")
            rules_engine_result = self.rules_engine.analyze(transcript, user_id=user_id)
            if rules_engine_result.get("enabled"):
                level = self._pick_highest_level(level, rules_engine_result.get("level", level))
                score += rules_engine_result.get("score", 0)
        except Exception as exc:
            logger.warning("⚠️ Reglas dinámicas deshabilitadas: %s", exc)
            rules_engine_result = {"enabled": False, "error": str(exc)}
        
        return {
            'level': level,
            'score': score,
            'critical_found': critical_found,
            'warnings_found': warnings_found,
            'rules_engine': rules_engine_result,
        }

    @staticmethod
    def _pick_highest_level(base_level: str, new_level: str) -> str:
        """Devuelve la severidad más alta entre dos niveles."""
        order = {
            'BAJO': 0,
            'MEDIO': 1,
            'ALTO': 2,
            'CRÍTICO': 3,
        }
        if order.get(new_level, 0) > order.get(base_level, 0):
            return new_level
        return base_level
    
    def _detect_patterns(self, transcript: str) -> List[Dict]:
        """Detección de patrones (simplificada)"""
        patterns = []
        text_lower = transcript.lower()
        
        # Patrón: escalación
        escalation_keywords = ['escalación', 'supervisor', 'gerente', 'jefe']
        if any(kw in text_lower for kw in escalation_keywords):
            patterns.append({
                'name': 'Escalación Detectada',
                'severity': 'high',
                'keywords': [kw for kw in escalation_keywords if kw in text_lower]
            })
        
        # Patrón: cancelación
        if 'cancelación' in text_lower or 'cancelar' in text_lower:
            patterns.append({
                'name': 'Intención de Cancelación',
                'severity': 'critical'
            })
        
        # Patrón: repetición
        words = text_lower.split()
        word_counts = {}
        for word in words:
            if len(word) > 5:  # Solo palabras largas
                word_counts[word] = word_counts.get(word, 0) + 1
        
        repeated = {w: c for w, c in word_counts.items() if c >= 5}
        if repeated:
            patterns.append({
                'name': 'Palabras Repetidas',
                'severity': 'medium',
                'details': repeated
            })
        
        return patterns
    
    def _detect_anomalies(self, data: Dict) -> List[Dict]:
        """Detección de anomalías"""
        anomalies = []
        
        # Anomalía: QA muy bajo
        if 'qa' in data and data['qa'].get('compliance_percentage', 100) < 50:
            anomalies.append({
                'type': 'low_qa_score',
                'value': data['qa']['compliance_percentage'],
                'threshold': 50
            })
        
        # Anomalía: Riesgo crítico + Sentimiento negativo
        if 'risk' in data and data['risk'].get('level') == 'CRÍTICO':
            if 'sentiment' in data and data['sentiment']['overall'] in ['negative', 'very_negative']:
                anomalies.append({
                    'type': 'critical_risk_negative_sentiment',
                    'severity': 'critical'
                })
        
        # Anomalía: Llamada muy corta
        if 'kpis' in data:
            duration = data['kpis']['metrics'].get('duration', {}).get('value', 0)
            if duration < 30:  # Menos de 30 segundos
                anomalies.append({
                    'type': 'very_short_call',
                    'duration_seconds': duration
                })
        
        return anomalies
    
    def generate_summary_report(self, results: List[Dict]) -> Dict:
        """Genera reporte resumen de procesamiento"""
        if not results:
            return {}
        
        total = len(results)
        completed = len([r for r in results if r['status'] == 'completed'])
        errors = total - completed
        
        avg_processing_time = sum(r.get('processing_time_seconds', 0) for r in results) / total
        
        risk_distribution = {}
        for r in results:
            if 'risk' in r.get('data', {}):
                level = r['data']['risk'].get('level', 'DESCONOCIDO')
                risk_distribution[level] = risk_distribution.get(level, 0) + 1
        
        return {
            'total_processed': total,
            'successful': completed,
            'errors': errors,
            'success_rate': completed / total * 100,
            'avg_processing_time_seconds': avg_processing_time,
            'risk_distribution': risk_distribution,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def close(self):
        """Cierra recursos"""
        self.db.close()
        logger.info("✓ Pipeline Orchestrator cerrado")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - [%(levelname)s] %(message)s'
    )
    
    # Usar con context manager
    with PipelineOrchestrator(config_path="../config.yaml") as pipeline:
        # Procesar directorio
        results = pipeline.process_audio_directory(
            audio_dir="../audio_in",
            service_level="standard",
            parallel=True
        )
        
        # Generar reporte
        summary = pipeline.generate_summary_report(results)
        print("\nRESUMEN DE PROCESAMIENTO:")
        print(json.dumps(summary, indent=2))
