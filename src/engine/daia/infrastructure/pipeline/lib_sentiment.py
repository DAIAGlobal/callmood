"""
DAIA - Sentiment Analysis Module (Local HuggingFace)
Análisis de sentimiento offline con modelos locales.
100% Local, 0 USD, Control Total.
"""

import logging
from typing import Dict, List, Tuple, Any
from pathlib import Path
from transformers import pipeline
import torch

logger = logging.getLogger(__name__)


class LocalSentimentAnalyzer:
    """Analizador de sentimiento basado en transformers locales"""
    
    def __init__(self, model_name: str = None, language: str = "es"):
        """
        Inicializa el analizador de sentimiento.
        
        Args:
            model_name: Nombre del modelo HuggingFace (default: multilingual)
            language: Idioma (para seleccionar modelo apropiado)
        """
        self.language = language
        self.model_name = model_name or "nlptown/bert-base-multilingual-uncased-sentiment"
        self.device = 0 if torch.cuda.is_available() else -1
        self.threshold = 0.7
        
        self._load_pipeline()
    
    def _load_pipeline(self):
        """Carga el pipeline de transformers"""
        try:
            logger.info(f"Cargando modelo de sentimiento: {self.model_name}")
            
            self.classifier = pipeline(
                "sentiment-analysis",
                model=self.model_name,
                device=self.device,
                truncation=True,
                max_length=512
            )
            
            device_name = "GPU" if self.device == 0 else "CPU"
            logger.info(f"✓ Modelo cargado en {device_name}")
            
        except Exception as e:
            logger.error(f"Error cargando modelo: {e}")
            raise
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analiza el sentimiento de un texto completo con validaciones.
        
        Args:
            text: Texto a analizar (no vacío)
            
        Returns:
            dict: {
                'overall': sentimiento general,
                'score': puntuación (0-1),
                'confidence': confianza,
                'segments': lista de análisis por segmento
            }
        """
        # Validar entrada
        if not text or not isinstance(text, str):
            logger.warning(f"❌ Texto inválido para análisis de sentimiento")
            return {
                'overall': 'unknown',
                'score': 0.0,
                'confidence': 0.0,
                'segments': []
            }
        
        text = text.strip()
        if len(text) == 0:
            logger.warning(f"❌ Texto vacío para análisis de sentimiento")
            return {
                'overall': 'neutral',
                'score': 0.5,
                'confidence': 0.0,
                'segments': []
            }
        
        # Validar modelo
        if not self.classifier:
            logger.error(f"❌ Modelo de sentimiento no está cargado")
            return {
                'overall': 'unknown',
                'score': 0.0,
                'confidence': 0.0,
                'segments': []
            }
        
        try:
            logger.debug(f"Analizando sentimiento: {len(text)} caracteres")
            
            # Análisis de texto completo (limitar a 512 tokens)
            result = self.classifier(text[:512])[0]
            
            # Validar resultado
            if not result or 'label' not in result or 'score' not in result:
                logger.error(f"❌ Resultado inválido de clasificador")
                return {
                    'overall': 'unknown',
                    'score': 0.0,
                    'confidence': 0.0,
                    'segments': []
                }
            
            # Mapear etiquetas
            label = self._normalize_label(result['label'])
            score = self._normalize_score(result['label'], result['score'])
            confidence = min(float(result['score']), 1.0)
            
            # Análisis por segmentos (si el texto es largo)
            segments = self._analyze_segments(text) if len(text) > 512 else []
            
            logger.debug(f"✓ Sentimiento analizado: {label} ({confidence:.2%})")
            
            return {
                'overall': label,
                'score': score,
                'confidence': confidence,
                'segments': segments,
                'raw_label': result['label']
            }
            
        except RuntimeError as e:
            logger.error(f"❌ Error de GPU/CUDA en sentimiento: {e}")
            return {
                'overall': 'unknown',
                'score': 0.0,
                'confidence': 0.0,
                'segments': []
            }
        except Exception as e:
            logger.error(f"❌ Error inesperado en análisis de sentimiento: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return {
                'overall': 'unknown',
                'score': 0.5,
                'confidence': 0.0,
                'segments': []
            }
    
    def _normalize_label(self, label: str) -> str:
        """Normaliza etiquetas del modelo a formato estándar"""
        label_lower = label.lower()
        
        if '5' in label_lower or 'very_positive' in label_lower:
            return 'very_positive'
        elif '4' in label_lower or 'positive' in label_lower:
            return 'positive'
        elif '3' in label_lower or 'neutral' in label_lower:
            return 'neutral'
        elif '2' in label_lower or 'negative' in label_lower:
            return 'negative'
        elif '1' in label_lower or 'very_negative' in label_lower:
            return 'very_negative'
        
        return 'neutral'
    
    def _normalize_score(self, label: str, confidence: float) -> float:
        """Convierte etiqueta y confianza a puntuación numérica (0-1)"""
        label = self._normalize_label(label)
        
        score_map = {
            'very_positive': 1.0,
            'positive': 0.75,
            'neutral': 0.5,
            'negative': 0.25,
            'very_negative': 0.0
        }
        
        base_score = score_map.get(label, 0.5)
        
        # Ajustar por confianza
        return base_score * confidence
    
    def _analyze_segments(self, text: str, segment_size: int = 512) -> List[Dict]:
        """Analiza sentimiento por segmentos del texto"""
        segments = []
        
        # Dividir en oraciones/párrafos
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        current_segment = ""
        for sentence in sentences:
            if len(current_segment) + len(sentence) < segment_size:
                current_segment += sentence + ". "
            else:
                if current_segment:
                    result = self.classifier(current_segment[:512])[0]
                    segments.append({
                        'text': current_segment.strip(),
                        'label': self._normalize_label(result['label']),
                        'confidence': result['score']
                    })
                current_segment = sentence + ". "
        
        # Último segmento
        if current_segment:
            result = self.classifier(current_segment[:512])[0]
            segments.append({
                'text': current_segment.strip(),
                'label': self._normalize_label(result['label']),
                'confidence': result['score']
            })
        
        return segments
    
    def analyze_conversation(self, transcript: str, speaker_markers: dict = None) -> Dict:
        """
        Analiza sentimiento de una conversación (operador vs cliente).
        
        Args:
            transcript: Transcripción completa
            speaker_markers: Dict con marcadores de hablantes {'operator': 'OPE', 'client': 'CLI'}
            
        Returns:
            dict: Análisis por hablante
        """
        operator_text = ""
        client_text = ""
        
        if speaker_markers:
            operator_marker = speaker_markers.get('operator', 'OPE')
            client_marker = speaker_markers.get('client', 'CLI')
            
            lines = transcript.split('\n')
            for line in lines:
                if operator_marker in line:
                    operator_text += line + " "
                elif client_marker in line:
                    client_text += line + " "
        else:
            # Asumir 50-50 si no hay marcadores
            lines = transcript.split('\n')
            mid = len(lines) // 2
            operator_text = ' '.join(lines[:mid])
            client_text = ' '.join(lines[mid:])
        
        return {
            'operator_sentiment': self.analyze_text(operator_text),
            'client_sentiment': self.analyze_text(client_text),
            'overall': self.analyze_text(transcript)
        }
    
    def get_sentiment_score(self, text: str) -> float:
        """
        Retorna puntuación de sentimiento simple (0-1).
        
        Args:
            text: Texto a analizar
            
        Returns:
            float: Puntuación (0=muy negativo, 1=muy positivo)
        """
        result = self.analyze_text(text)
        return result['score']


def create_sentiment_analyzer(model: str = None, language: str = "es") -> LocalSentimentAnalyzer:
    """Factory para crear analizador de sentimiento"""
    return LocalSentimentAnalyzer(model, language)


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Crear analizador
    analyzer = create_sentiment_analyzer()
    
    # Ejemplo de análisis
    test_text = """
    Hola, buenos días. ¿Cómo puedo ayudarle hoy?
    Tengo un problema grave con mi cuenta, llevo tres días esperando.
    Lo lamento mucho. Voy a resolver esto inmediatamente.
    Gracias por su paciencia. Espero no tener más problemas.
    """
    
    result = analyzer.analyze_text(test_text)
    print(f"\nAnálisis de sentimiento:")
    print(f"  Sentimiento general: {result['overall']}")
    print(f"  Puntuación: {result['score']:.2f}")
    print(f"  Confianza: {result['confidence']:.2f}")
    print(f"  Segmentos: {len(result['segments'])}")
