"""
DAIA - Transcription Module (Whisper Local)
Transcripción offline con auto-fallback según recursos.
100% Local, 0 USD, Control Total.
"""

import os
import logging
import torch
import whisper
from pathlib import Path
from typing import Dict, Any, Optional
from lib_resources import ResourceManager, ConfigManager

logger = logging.getLogger(__name__)


class WhisperTranscriber:
    """Transcriptor Whisper optimizado con auto-fallback"""
    
    def __init__(self, config: ConfigManager, rm: ResourceManager):
        self.config = config
        self.rm = rm
        self.device = rm.get_device()
        self.model = None
        self.model_name = None
        
        # Auto-seleccionar modelo
        self.model_name = rm.get_whisper_model()
        self._load_model()
    
    def _load_model(self):
        """Carga el modelo Whisper con manejo de errores"""
        try:
            logger.info(f"Cargando modelo Whisper '{self.model_name}'...")
            
            whisper_config = self.rm.get_whisper_config()
            
            # Cargar modelo
            self.model = whisper.load_model(
                self.model_name,
                device=self.device
            )
            
            logger.info(f"✓ Modelo '{self.model_name}' cargado en {self.device.upper()}")
            
        except Exception as e:
            logger.error(f"Error cargando modelo '{self.model_name}': {e}")
            self._fallback_model()
    
    def _fallback_model(self):
        """Fallback a modelo más pequeño si hay error"""
        if self.model_name != "small":
            logger.warning(f"⚠ Fallback desde '{self.model_name}' a 'small'")
            self.model_name = "small"
            self.model = whisper.load_model(self.model_name, device=self.device)
            logger.info(f"✓ Modelo 'small' cargado (fallback)")
        else:
            logger.error("❌ No se pudo cargar ningún modelo Whisper")
            raise RuntimeError("Fallo crítico en carga de modelos")
    
    def transcribe_file(self, audio_path: str, with_segments: bool = False) -> Dict[str, Any]:
        """
        Transcribe un archivo de audio con validaciones.
        
        Args:
            audio_path: Ruta del archivo de audio
            with_segments: Cuando es True devuelve segmentos con timestamps para
                alineación/diarización.
            
        Returns:
            dict: {'text': transcripción, 'language': idioma, 'duration': duración, 'segments': []}
                  None si hay error
        """
        # Validar entrada
        if not audio_path or not isinstance(audio_path, str):
            logger.error(f"❌ audio_path inválido: {audio_path}")
            return None
        
        audio_path = Path(audio_path)
        
        # Validar existencia
        if not audio_path.exists():
            logger.error(f"❌ Archivo no encontrado: {audio_path}")
            return None
        
        # Validar tamaño
        try:
            file_size = audio_path.stat().st_size
            if file_size == 0:
                logger.error(f"❌ Archivo vacío: {audio_path}")
                return None
        except Exception as e:
            logger.error(f"❌ Error verificando archivo: {e}")
            return None
        
        # Validar modelo
        if not self.model:
            logger.error(f"❌ Modelo Whisper no está cargado")
            return None
        
        try:
            logger.info(f"🎙️ Transcribiendo: {audio_path.name} ({file_size / 1024:.1f}KB)")
            
            # Transcribir
            result = self.model.transcribe(
                str(audio_path),
                language=self.config.get("general.language", "es"),
                verbose=False,
                word_timestamps=with_segments,
            )
            
            if not result or not result.get('text'):
                logger.error(f"❌ Transcripción vacía: {audio_path.name}")
                return None
            
            duration = self._estimate_duration(audio_path)
            
            logger.info(f"✅ Transcripción completada: {len(result['text'])} caracteres")
            
            segments = []
            if with_segments and result.get('segments'):
                for seg in result['segments']:
                    segments.append({
                        'start': seg.get('start'),
                        'end': seg.get('end'),
                        'text': seg.get('text', '').strip(),
                    })

            return {
                'filename': audio_path.name,
                'text': result['text'],
                'language': result.get('language', 'es'),
                'duration': duration,
                'model_used': self.model_name,
                'device_used': self.device,
                'char_count': len(result['text']),
                'duration_seconds': duration,
                'segments': segments,
            }
            
        except RuntimeError as e:
            logger.error(f"❌ Error de GPU/CUDA: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error transcribiendo: {type(e).__name__}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None
    
    def _estimate_duration(self, audio_path: Path) -> float:
        """Estima la duración del audio en segundos"""
        try:
            import librosa
            y, sr = librosa.load(str(audio_path), sr=None)
            return len(y) / sr
        except:
            return 0.0
    
    def transcribe_batch(self, audio_dir: str, output_dir: str = None) -> list:
        """
        Transcribe múltiples archivos.
        
        Args:
            audio_dir: Directorio con archivos de audio
            output_dir: Directorio para guardar transcripciones (opcional)
            
        Returns:
            list: Lista de resultados
        """
        audio_dir = Path(audio_dir)
        results = []
        
        audio_extensions = self.config.get(
            "transcription.audio_extensions",
            ['.wav', '.mp3', '.m4a', '.ogg', '.flac']
        )
        
        audio_files = [
            f for f in audio_dir.iterdir()
            if f.suffix.lower() in audio_extensions
        ]
        
        logger.info(f"Encontrados {len(audio_files)} archivos de audio")
        
        for i, audio_file in enumerate(audio_files, 1):
            logger.info(f"[{i}/{len(audio_files)}] Procesando {audio_file.name}")
            
            result = self.transcribe_file(str(audio_file))
            if result:
                results.append(result)
                
                # Guardar si se especifica output_dir
                if output_dir:
                    self._save_transcript(result, output_dir)
        
        logger.info(f"✓ Procesamiento completado: {len(results)}/{len(audio_files)}")
        return results
    
    def _save_transcript(self, result: Dict, output_dir: str):
        """Guarda transcripción en archivo"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Usar nombre del archivo original
        output_file = output_dir / f"{Path(result['filename']).stem}.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result['text'])
        
        logger.debug(f"Guardado: {output_file}")


def create_transcriber(config_path: str = "config.yaml") -> WhisperTranscriber:
    """Factory para crear transcriptor con configuración automática"""
    
    config = ConfigManager(config_path)
    config.validate()
    
    rm = ResourceManager()
    rm.log_summary()
    
    return WhisperTranscriber(config, rm)


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Crear transcriptor
    transcriber = create_transcriber("../config.yaml")
    
    # Ejemplo: transcribir archivo específico
    # result = transcriber.transcribe_file("../audio_in/example.wav")
    # print(result)
