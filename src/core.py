"""
DAIA Core Module - Unified Entry Point

Clean architecture entry point for call analysis.
Exposes business logic without infrastructure dependencies.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any

# Ensure engine package is importable
ROOT_DIR = Path(__file__).resolve().parent
ENGINE_SRC = ROOT_DIR / "engine"
if str(ENGINE_SRC) not in sys.path:
    sys.path.insert(0, str(ENGINE_SRC))

# Import core engine components
from daia.infrastructure.pipeline import PipelineOrchestrator

logger = logging.getLogger(__name__)


def analyze_call(file_path: str, level: str = "STANDARD") -> Dict[str, Any]:
    """
    Analyze a single call audio file.

    This is the main entry point for call analysis business logic.
    Uses the DAIA engine without breaking existing functionality.

    Args:
        file_path: Path to the audio file to analyze
        level: Analysis level - "BASIC", "STANDARD", or "ADVANCED"

    Returns:
        Dict containing the complete analysis result with:
        - status: "success" or "error"
        - data: Analysis results (transcription, sentiment, QA, KPIs, etc.)
        - metadata: Processing information

    Raises:
        FileNotFoundError: If audio file doesn't exist
        ValueError: If level is invalid
    """
    # Validate inputs
    audio_path = Path(file_path)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    if level not in ["BASIC", "STANDARD", "ADVANCED"]:
        raise ValueError(f"Invalid level '{level}'. Must be BASIC, STANDARD, or ADVANCED")

    # Map level to service_level (lowercase for engine compatibility)
    service_level_map = {
        "BASIC": "basic",
        "STANDARD": "standard",
        "ADVANCED": "advanced"
    }
    service_level = service_level_map[level]

    try:
        logger.info(f"Starting analysis of {file_path} at level {level}")

        # Initialize pipeline orchestrator
        # Uses default config.yaml and local SQLite database
        db_path = "data/daia_audit.db"
        orchestrator = PipelineOrchestrator(db_path=db_path)

        # Process the audio file
        result = orchestrator.process_audio_file(
            audio_path=str(audio_path),
            service_level=service_level
        )

        logger.info(f"Analysis completed for {file_path}")
        return result

    except Exception as e:
        logger.error(f"Analysis failed for {file_path}: {e}")
        return {
            "status": "error",
            "error": str(e),
            "data": {},
            "metadata": {
                "file_path": str(file_path),
                "level": level
            }
        }


# Convenience functions for different analysis levels
def analyze_call_basic(file_path: str) -> Dict[str, Any]:
    """Analyze call with basic level (transcription + risk detection)."""
    return analyze_call(file_path, "BASIC")


def analyze_call_standard(file_path: str) -> Dict[str, Any]:
    """Analyze call with standard level (basic + sentiment + QA + KPIs)."""
    return analyze_call(file_path, "STANDARD")


def analyze_call_advanced(file_path: str) -> Dict[str, Any]:
    """Analyze call with advanced level (standard + patterns + anomalies)."""
    return analyze_call(file_path, "ADVANCED")