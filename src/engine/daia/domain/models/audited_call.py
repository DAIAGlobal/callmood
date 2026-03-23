"""
Domain Model: AuditedCall

Representa una llamada telefónica que ha sido auditada.
Entity (tiene identidad única - call_id).
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from enum import Enum


class CallStatus(Enum):
    """Estados posibles de una llamada"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ServiceLevel(Enum):
    """Niveles de servicio de auditoría"""
    BASIC = "basic"          # Transcripción + Riesgos
    STANDARD = "standard"    # + Sentimiento + QA + KPIs
    ADVANCED = "advanced"    # + Patrones + Anomalías


@dataclass(frozen=True)
class AuditedCall:
    """
    Entity: Llamada telefónica auditada
    
    Aggregate Root del dominio de auditoría.
    Inmutable para garantizar consistencia.
    
    Attributes:
        call_id: Identificador único de la llamada (None si aún no persistida)
        filename: Nombre del archivo de audio
        audio_path: Ruta completa al archivo de audio
        duration_seconds: Duración de la llamada en segundos
        processing_date: Fecha y hora de procesamiento
        status: Estado actual de la llamada
        service_level: Nivel de auditoría aplicado
        error_message: Mensaje de error si status=FAILED
        
    Business Rules:
        - La duración debe ser > 0 si está completada
        - El archivo debe existir si status != FAILED
        - service_level determina qué análisis se ejecutan
    """
    
    # Identity
    call_id: Optional[int]
    
    # Core attributes
    filename: str
    audio_path: str
    duration_seconds: float
    
    # Metadata
    processing_date: datetime
    status: CallStatus
    service_level: ServiceLevel
    
    # Optional
    error_message: Optional[str] = None
    original_filename: Optional[str] = None
    
    def __post_init__(self):
        """Validaciones de negocio"""
        # Validar duración
        if self.status == CallStatus.COMPLETED and self.duration_seconds <= 0:
            raise ValueError(
                f"Completed call must have duration > 0, got {self.duration_seconds}"
            )
        
        # Validar que el archivo existe (si no es un error)
        if self.status != CallStatus.FAILED:
            audio_file = Path(self.audio_path)
            if not audio_file.exists():
                raise ValueError(
                    f"Audio file does not exist: {self.audio_path}"
                )
    
    @property
    def is_completed(self) -> bool:
        """Verifica si la llamada fue procesada exitosamente"""
        return self.status == CallStatus.COMPLETED
    
    @property
    def has_error(self) -> bool:
        """Verifica si hubo error en el procesamiento"""
        return self.status == CallStatus.FAILED
    
    @property
    def duration_minutes(self) -> float:
        """Retorna duración en minutos"""
        return self.duration_seconds / 60.0
    
    @property
    def file_size_mb(self) -> float:
        """Retorna tamaño del archivo en MB"""
        try:
            return Path(self.audio_path).stat().st_size / (1024 * 1024)
        except FileNotFoundError:
            return 0.0
    
    def requires_basic_analysis(self) -> bool:
        """Verifica si requiere análisis básico"""
        return self.service_level in [
            ServiceLevel.BASIC,
            ServiceLevel.STANDARD,
            ServiceLevel.ADVANCED
        ]
    
    def requires_standard_analysis(self) -> bool:
        """Verifica si requiere análisis estándar"""
        return self.service_level in [
            ServiceLevel.STANDARD,
            ServiceLevel.ADVANCED
        ]
    
    def requires_advanced_analysis(self) -> bool:
        """Verifica si requiere análisis avanzado"""
        return self.service_level == ServiceLevel.ADVANCED
    
    def __str__(self) -> str:
        return f"AuditedCall(id={self.call_id}, file={self.filename}, status={self.status.value})"
    
    def __repr__(self) -> str:
        return (
            f"AuditedCall("
            f"call_id={self.call_id}, "
            f"filename='{self.filename}', "
            f"duration={self.duration_seconds:.1f}s, "
            f"status={self.status.value}, "
            f"level={self.service_level.value})"
        )


# Factory methods para crear instancias comunes
def create_new_call(
    filename: str,
    audio_path: str,
    service_level: ServiceLevel = ServiceLevel.STANDARD
) -> AuditedCall:
    """
    Factory: Crea una nueva llamada para procesar
    
    Args:
        filename: Nombre del archivo
        audio_path: Ruta completa al archivo
        service_level: Nivel de auditoría a aplicar
        
    Returns:
        AuditedCall en estado PENDING
    """
    return AuditedCall(
        call_id=None,
        filename=filename,
        audio_path=audio_path,
        duration_seconds=0.0,  # Se actualiza tras transcripción
        processing_date=datetime.now(),
        status=CallStatus.PENDING,
        service_level=service_level,
        original_filename=filename
    )


def create_completed_call(
    call_id: Optional[int],
    filename: str,
    audio_path: str,
    duration_seconds: float,
    service_level: ServiceLevel
) -> AuditedCall:
    """
    Factory: Crea una llamada completada
    
    Args:
        call_id: ID de la llamada (puede ser None)
        filename: Nombre del archivo
        audio_path: Ruta completa
        duration_seconds: Duración procesada
        service_level: Nivel aplicado
        
    Returns:
        AuditedCall en estado COMPLETED
    """
    return AuditedCall(
        call_id=call_id,
        filename=filename,
        audio_path=audio_path,
        duration_seconds=duration_seconds,
        processing_date=datetime.now(),
        status=CallStatus.COMPLETED,
        service_level=service_level
    )


def create_failed_call(
    filename: str,
    audio_path: str,
    error_message: str,
    service_level: ServiceLevel = ServiceLevel.STANDARD
) -> AuditedCall:
    """
    Factory: Crea una llamada fallida
    
    Args:
        filename: Nombre del archivo
        audio_path: Ruta completa
        error_message: Descripción del error
        service_level: Nivel que se intentó aplicar
        
    Returns:
        AuditedCall en estado FAILED
    """
    return AuditedCall(
        call_id=None,
        filename=filename,
        audio_path=audio_path,
        duration_seconds=0.0,
        processing_date=datetime.now(),
        status=CallStatus.FAILED,
        service_level=service_level,
        error_message=error_message
    )
