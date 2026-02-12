"""
DAIA - KPI Calculation Module (Local)
Cálculo de métricas operativas sin servicios externos.
100% Local, 0 USD, Control Total.
"""

import logging
import re
from typing import Dict, List, Any
from collections import Counter
import statistics

logger = logging.getLogger(__name__)


class KPICalculator:
    """Calculador de KPIs operativos basado en transcripciones"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Inicializa el calculador de KPIs.
        
        Args:
            config: Configuración de KPIs desde config.yaml
        """
        self.config = config or {}
        self.metrics = {}
    
    def calculate_all_kpis(self, transcript: str, audio_duration: float = None, speaker_summary: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Calcula todos los KPIs disponibles.
        
        Args:
            transcript: Transcripción del audio
            audio_duration: Duración del audio en segundos (si se conoce)
            
        Returns:
            dict: Diccionario con todos los KPIs calculados
        """
        kpis = {
            'timestamp': None,
            'transcript_metadata': self._get_transcript_metadata(transcript),
            'metrics': {}
        }
        
        # Calcular cada métrica
        kpis['metrics']['duration'] = self._calculate_duration(transcript, audio_duration)
        kpis['metrics']['word_count'] = self._calculate_word_count(transcript)
        kpis['metrics']['silence_ratio'] = self._calculate_silence_ratio(transcript)
        kpis['metrics']['speech_rate'] = self._calculate_speech_rate(transcript)
        kpis['metrics']['vocabulary_richness'] = self._calculate_vocabulary_richness(transcript)
        kpis['metrics']['response_time'] = self._calculate_response_time(transcript)
        kpis['metrics']['speaking_balance'] = self._calculate_speaking_balance(
            transcript,
            speaker_summary=speaker_summary,
        )
        kpis['metrics']['interruptions'] = self._calculate_interruptions(transcript)
        
        return kpis
    
    def _get_transcript_metadata(self, transcript: str) -> Dict:
        """Obtiene metadatos básicos del transcript"""
        lines = [l for l in transcript.split('\n') if l.strip()]
        
        return {
            'lines': len(lines),
            'characters': len(transcript),
            'paragraphs': len([p for p in transcript.split('\n\n') if p.strip()])
        }
    
    def _calculate_duration(self, transcript: str, audio_duration: float = None) -> Dict:
        """
        Calcula duración estimada.
        
        Si se proporciona audio_duration, la usa.
        Si no, estima basándose en conteo de palabras.
        """
        word_count = len(transcript.split())
        
        if audio_duration:
            # Usar duración real del audio
            return {
                'type': 'duration',
                'value': audio_duration,
                'unit': 'seconds',
                'estimated': False,
                'formatted': self._format_duration(audio_duration)
            }
        else:
            # Estimar: ~150 palabras/minuto = 2.5 palabras/segundo
            estimated_seconds = word_count / 2.5
            return {
                'type': 'duration',
                'value': estimated_seconds,
                'unit': 'seconds',
                'estimated': True,
                'formatted': self._format_duration(estimated_seconds)
            }
    
    def _calculate_word_count(self, transcript: str) -> Dict:
        """Calcula cantidad de palabras"""
        words = transcript.split()
        return {
            'type': 'word_count',
            'value': len(words),
            'unit': 'palabras',
            'average_word_length': statistics.mean(len(w) for w in words) if words else 0
        }
    
    def _calculate_silence_ratio(self, transcript: str) -> Dict:
        """
        Calcula ratio de silencios.
        Simplificación: líneas en blanco vs líneas con contenido.
        """
        lines = transcript.split('\n')
        empty_lines = len([l for l in lines if not l.strip()])
        content_lines = len([l for l in lines if l.strip()])
        total_lines = len(lines)
        
        ratio = empty_lines / total_lines if total_lines > 0 else 0
        
        return {
            'type': 'silence_ratio',
            'value': ratio,
            'unit': 'ratio (0-1)',
            'percentage': ratio * 100,
            'status': 'NORMAL' if ratio < 0.3 else 'ALTO' if ratio < 0.5 else 'CRÍTICO',
            'metadata': {
                'empty_lines': empty_lines,
                'content_lines': content_lines,
                'total_lines': total_lines
            }
        }
    
    def _calculate_speech_rate(self, transcript: str) -> Dict:
        """
        Calcula velocidad de habla.
        Aproximación: palabras por minuto.
        """
        words = transcript.split()
        word_count = len(words)
        
        # Estimar duración en minutos (2.5 palabras/segundo)
        estimated_minutes = word_count / (2.5 * 60)
        
        if estimated_minutes > 0:
            words_per_minute = word_count / estimated_minutes
        else:
            words_per_minute = 0
        
        # Clasificación: rango normal es 120-150 wpm
        if words_per_minute < 100:
            classification = "LENTO"
        elif words_per_minute > 180:
            classification = "RÁPIDO"
        else:
            classification = "NORMAL"
        
        return {
            'type': 'speech_rate',
            'value': words_per_minute,
            'unit': 'palabras/minuto',
            'classification': classification,
            'estimated_duration_minutes': estimated_minutes
        }
    
    def _calculate_vocabulary_richness(self, transcript: str) -> Dict:
        """
        Calcula riqueza léxica (Type-Token Ratio).
        Palabras únicas / Total de palabras.
        """
        words = transcript.lower().split()
        unique_words = len(set(words))
        total_words = len(words)
        
        # TTR: 0-1, donde 1 es vocabulario perfecto
        ttr = unique_words / total_words if total_words > 0 else 0
        
        # Clasificación según TTR
        if ttr > 0.5:
            richness = "ALTO"
        elif ttr > 0.35:
            richness = "MEDIO"
        else:
            richness = "BAJO"
        
        return {
            'type': 'vocabulary_richness',
            'value': ttr,
            'unit': 'Type-Token Ratio (0-1)',
            'richness_level': richness,
            'unique_words': unique_words,
            'total_words': total_words
        }
    
    def _calculate_response_time(self, transcript: str) -> Dict:
        """
        Calcula tiempo promedio de respuesta del operador.
        Simplificación: tiempo entre intervenciones.
        """
        # Asumir que hay intercambios entre líneas
        lines = [l for l in transcript.split('\n') if l.strip()]
        
        if len(lines) < 2:
            return {
                'type': 'response_time',
                'value': 0,
                'unit': 'seconds',
                'note': 'Insuficientes intercambios para calcular'
            }
        
        # Estimar tiempo de respuesta basado en duración total / número de intercambios
        total_duration = len(transcript.split()) / 2.5  # segundos
        exchanges = max(1, len(lines) // 2)
        avg_response_time = total_duration / exchanges if exchanges > 0 else 0
        
        return {
            'type': 'response_time',
            'value': avg_response_time,
            'unit': 'seconds',
            'estimated': True,
            'exchanges': exchanges,
            'classification': 'NORMAL' if avg_response_time < 10 else 'LENTO'
        }
    
    def _calculate_speaking_balance(self, transcript: str, speaker_summary: Dict[str, Any] = None) -> Dict:
        """
        Calcula balance de habla entre participantes.
        
        Si llega un speaker_summary con conteo de palabras por rol, lo usa para
        evitar heurísticas débiles. Si no, mantiene el cálculo previo.
        """
        if speaker_summary and speaker_summary.get('speaking_balance'):
            balance = speaker_summary['speaking_balance']
            return {
                'type': 'speaking_balance',
                'operator_percentage': balance.get('operator_percentage', 0),
                'client_percentage': balance.get('client_percentage', 0),
                'operator_words': balance.get('operator_words', 0),
                'client_words': balance.get('client_words', 0),
                'balance_quality': balance.get('balance_quality', 'DESCONOCIDO'),
                'unit': balance.get('unit', 'porcentaje'),
                'note': 'calculado_con_diarizacion',
            }

        lines = [l for l in transcript.split('\n') if l.strip()]
        
        if not lines:
            return {
                'type': 'speaking_balance',
                'value': 0.5,
                'unit': 'ratio',
                'note': 'Sin datos para calcular'
            }
        
        # Dividir: asumir participante 1 vs participante 2
        mid = len(lines) // 2
        
        speaker1_words = len(' '.join(lines[:mid]).split())
        speaker2_words = len(' '.join(lines[mid:]).split())
        total_words = speaker1_words + speaker2_words
        
        ratio = speaker1_words / total_words if total_words > 0 else 0
        
        # Ratio ideal: 40-50 % para operador
        operator_percentage = ratio * 100
        client_percentage = (1 - ratio) * 100
        
        balance_quality = "BUENO" if 35 < operator_percentage < 55 else "DESBALANCEADO"
        
        return {
            'type': 'speaking_balance',
            'operator_percentage': operator_percentage,
            'client_percentage': client_percentage,
            'operator_words': speaker1_words,
            'client_words': speaker2_words,
            'balance_quality': balance_quality,
            'unit': 'porcentaje'
        }
    
    def _calculate_interruptions(self, transcript: str) -> Dict:
        """
        Calcula número estimado de interrupciones.
        Simplificación: cambios rápidos de hablante.
        """
        lines = [l for l in transcript.split('\n') if l.strip()]
        
        # Interrupciones: cuando hay cambios de línea con poco contenido
        short_lines = [l for l in lines if len(l.split()) < 3]
        
        # Cambios consecutivos rápidos = posible interrupción
        interruptions = len(short_lines)
        
        return {
            'type': 'interruptions',
            'count': interruptions,
            'percentage': (interruptions / len(lines) * 100) if lines else 0,
            'classification': 'NORMAL' if interruptions < 5 else 'FRECUENTES',
            'unit': 'número'
        }
    
    def _format_duration(self, seconds: float) -> str:
        """Formatea duración en HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def get_summary(self, kpis: Dict) -> str:
        """Genera resumen textual de KPIs"""
        summary = "\nRESUMEN DE KPIs\n" + "="*50 + "\n"
        
        for metric_name, metric_data in kpis['metrics'].items():
            summary += f"\n• {metric_data.get('type', metric_name).upper()}\n"
            summary += f"  Valor: {metric_data.get('value', 'N/A')}"
            
            if 'unit' in metric_data:
                summary += f" {metric_data['unit']}"
            
            if 'classification' in metric_data:
                summary += f" ({metric_data['classification']})"
            
            summary += "\n"
        
        return summary


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Cargar configuración
    from lib_resources import ConfigManager
    config = ConfigManager("../config.yaml")
    kpi_config = config.get("kpis")
    
    # Crear calculador
    kpi_calc = KPICalculator(kpi_config)
    
    # Ejemplo de transcripción
    test_transcript = """
    Buenos días, ¿cómo puedo ayudarle?
    Hola, tengo un problema con mi factura.
    Entiendo. Voy a revisar su cuenta ahora.
    Ok, espero.
    Encontré el error. Lo voy a corregir inmediatamente.
    Perfecto, gracias.
    Listo, está resuelto. ¿Hay algo más?
    No, nada más. Gracias de verdad.
    A usted. Que tenga un excelente día.
    """
    
    # Calcular KPIs
    kpis = kpi_calc.calculate_all_kpis(test_transcript, audio_duration=180)
    print(kpi_calc.get_summary(kpis))
    
    # Mostrar detalles
    import json
    print("\nDETALLE COMPLETO (JSON):")
    print(json.dumps(kpis, indent=2, default=str))
