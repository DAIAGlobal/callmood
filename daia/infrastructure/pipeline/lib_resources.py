"""
DAIA - Resource Management & Auto-Fallback System
Detecta recursos disponibles y configura automáticamente los modelos.
100% Local, 0 USD, Control Total.
"""

import torch
import psutil
import logging
from typing import Tuple, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class ResourceManager:
    """Gestor de recursos y auto-fallback inteligente"""
    
    def __init__(self):
        self.has_gpu = torch.cuda.is_available()
        self.gpu_name = torch.cuda.get_device_name(0) if self.has_gpu else None
        self.gpu_vram = self._get_gpu_memory()
        self.cpu_cores = psutil.cpu_count(logical=False)
        self.cpu_freq = psutil.cpu_freq().max if psutil.cpu_freq() else 0
        self.ram_total = psutil.virtual_memory().total / (1024**3)  # GB
        self.ram_available = psutil.virtual_memory().available / (1024**3)  # GB
        
        logger.info(f"GPU disponible: {self.has_gpu}")
        if self.has_gpu:
            logger.info(f"GPU: {self.gpu_name} ({self.gpu_vram:.1f}GB)")
        logger.info(f"CPU: {self.cpu_cores} cores @ {self.cpu_freq:.0f}MHz")
        logger.info(f"RAM: {self.ram_available:.1f}GB / {self.ram_total:.1f}GB")
    
    def _get_gpu_memory(self) -> float:
        """Obtiene VRAM disponible en GB"""
        if not self.has_gpu:
            return 0.0
        return torch.cuda.get_device_properties(0).total_memory / (1024**3)
    
    def get_whisper_model(self) -> str:
        """
        Selecciona automáticamente el mejor modelo Whisper.
        
        Returns:
            str: 'large', 'medium', 'small'
        """
        # GPU: Seleccionar por VRAM disponible
        if self.has_gpu:
            if self.gpu_vram >= 10:
                logger.info("✓ GPU con 10GB+: usando modelo 'large'")
                return "large"
            elif self.gpu_vram >= 5:
                logger.info("✓ GPU con 5GB+: usando modelo 'medium'")
                return "medium"
            else:
                logger.info("✓ GPU con <5GB: usando modelo 'small'")
                return "small"
        
        # CPU: Usar pequeño por rendimiento
        logger.warning("⚠ Sin GPU detectada: fallback a modelo 'small' (CPU mode)")
        logger.info("  Nota: El procesamiento será más lento en CPU")
        logger.info("  Configuración CPU FP32 para compatibilidad")
        return "small"
    
    def get_whisper_config(self) -> Dict[str, Any]:
        """
        Obtiene configuración optimizada para Whisper.
        
        Returns:
            dict: Configuración Whisper optimizada
        """
        base_config = {
            "verbose": False,
            "task": "transcribe",
            "best_of": 1,
            "beam_size": 5,
            "patience": 1.0,
        }
        
        # Optimización según disponibilidad de GPU
        if self.has_gpu:
            base_config["fp16"] = True  # FP16 en GPU acelera
            logger.info("✓ FP16 habilitado para GPU")
        else:
            base_config["fp16"] = False  # FP32 en CPU (más compatible)
            logger.info("✓ FP32 habilitado para CPU (máxima compatibilidad)")
        
        return base_config
    
    def get_device(self) -> str:
        """
        Retorna el device optimizado para PyTorch.
        
        Returns:
            str: 'cuda' o 'cpu'
        """
        device = "cuda" if self.has_gpu else "cpu"
        logger.info(f"Device seleccionado: {device.upper()}")
        return device
    
    def get_batch_size(self) -> int:
        """
        Calcula batch size óptimo basado en memoria disponible.
        
        Returns:
            int: Batch size recomendado
        """
        if self.has_gpu:
            # GPU: batch size basado en VRAM
            if self.gpu_vram >= 10:
                return 16
            elif self.gpu_vram >= 5:
                return 8
            else:
                return 4
        else:
            # CPU: conservative
            return 1
    
    def get_worker_threads(self, max_workers: int = 4) -> int:
        """
        Calcula número óptimo de workers para procesamiento paralelo.
        
        Args:
            max_workers: Máximo de workers configurado
            
        Returns:
            int: Número recomendado de workers
        """
        # No usar más workers que cores disponibles
        available = min(self.cpu_cores, max_workers)
        logger.info(f"Workers paralelos: {available} (de {self.cpu_cores} cores)")
        return available
    
    def log_summary(self):
        """Imprime resumen de recursos disponibles"""
        print("\n" + "="*70)
        print("DAIA - RESUMEN DE RECURSOS DISPONIBLES")
        print("="*70)
        
        print(f"\n🖥️  GPU")
        if self.has_gpu:
            print(f"   ✓ Disponible: {self.gpu_name}")
            print(f"   ✓ VRAM: {self.gpu_vram:.1f}GB")
        else:
            print(f"   ✗ No detectada (procesamiento en CPU)")
        
        print(f"\n⚙️  CPU")
        print(f"   ✓ Cores: {self.cpu_cores}")
        print(f"   ✓ Frecuencia: {self.cpu_freq:.0f}MHz")
        
        print(f"\n💾 RAM")
        print(f"   ✓ Total: {self.ram_total:.1f}GB")
        print(f"   ✓ Disponible: {self.ram_available:.1f}GB")
        
        print(f"\n📊 CONFIGURACIÓN RECOMENDADA")
        model = self.get_whisper_model()
        print(f"   ✓ Modelo Whisper: {model}")
        print(f"   ✓ Device: {self.get_device().upper()}")
        print(f"   ✓ FP16: {'Sí' if self.get_whisper_config().get('fp16') else 'No'}")
        print(f"   ✓ Batch Size: {self.get_batch_size()}")
        print(f"   ✓ Workers: {self.get_worker_threads()}")
        print("\n" + "="*70 + "\n")


class ConfigManager:
    """Gestor de configuración YAML con validación"""
    
    def __init__(self, config_path: str = "config.yaml"):
        import yaml
        
        self.config_path = Path(config_path)
        
        if not self.config_path.exists():
            raise FileNotFoundError(f"config.yaml no encontrado en {config_path}")
        
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        
        logger.info(f"✓ Configuración cargada desde {config_path}")
    
    def get(self, key: str, default=None):
        """Obtiene valor de configuración por clave (ej: 'general.language')"""
        keys = key.split(".")
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        
        return value if value is not None else default
    
    def get_pipeline_level(self, level: str = "standard") -> Dict[str, Any]:
        """Obtiene configuración del nivel de pipeline"""
        valid_levels = ["basic", "standard", "advanced"]
        if level not in valid_levels:
            logger.warning(f"Nivel '{level}' inválido, usando 'standard'")
            level = "standard"
        
        return self.config["pipeline"]["levels"][level]
    
    def get_qa_rules(self, level: str = "standard") -> Dict[str, Any]:
        """Obtiene reglas QA para un nivel específico"""
        return self.config["qa"]["rules"][level]
    
    def validate(self) -> bool:
        """Valida la integridad de la configuración"""
        required_sections = [
            "general", "transcription", "qa", "risk_analysis",
            "kpis", "database", "pipeline", "paths"
        ]
        
        for section in required_sections:
            if section not in self.config:
                logger.error(f"❌ Falta sección requerida: {section}")
                return False
        
        logger.info("✓ Configuración validada correctamente")
        return True


if __name__ == "__main__":
    # Logging setup
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test resource manager
    rm = ResourceManager()
    rm.log_summary()
    
    # Test config manager
    try:
        cm = ConfigManager("config.yaml")
        cm.validate()
    except FileNotFoundError as e:
        logger.error(f"Error: {e}")
