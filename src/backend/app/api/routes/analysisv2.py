"""
Clean Analysis API Endpoint (Step 2)

Uses core.py directly for unified call analysis.
Supports all service levels: BASIC, STANDARD, ADVANCED.
"""

import sys
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, status, BackgroundTasks, UploadFile, File

from ...schemas.analysis import (
    AnalysisRequest,
    AnalysisResult,
    AnalysisUploadRequest,
)

# Ensure core module is importable
ROOT_DIR = Path(__file__).resolve().parents[3]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from core import analyze_call
except ImportError:
    # Fallback for different import paths
    from src.core import analyze_call

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analyze", tags=["analysis"])


@router.post("", response_model=AnalysisResult, status_code=status.HTTP_200_OK)
def analyze_audio(request: AnalysisRequest):
    """
    Analyze a call audio file using unified core engine.

    **Levels:**
    - BASIC: Transcription + Risk Detection
    - STANDARD: BASIC + Sentiment + QA + KPIs
    - ADVANCED: STANDARD + Pattern Detection + Anomalies

    **Example:**
    ```json
    {
        "file_path": "audio_in/llamada1.m4a",
        "level": "STANDARD"
    }
    ```
    """
    try:
        # Validate level
        if request.level not in ["BASIC", "STANDARD", "ADVANCED"]:
            raise ValueError(
                f"Invalid level '{request.level}'. Must be BASIC, STANDARD, or ADVANCED"
            )

        # Validate file exists
        audio_path = Path(request.file_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {request.file_path}")

        logger.info(f"Analyzing {request.file_path} at level {request.level}")

        # Call core engine
        result = analyze_call(request.file_path, request.level)

        # Map result to response schema
        return AnalysisResult(
            status=result.get("status", "error"),
            filename=result.get("filename", audio_path.name),
            service_level=request.level,
            duration=result.get("duration"),
            qa_score=result.get("qa_score"),
            qa_percentage=result.get("qa_percentage"),
            sentiment=result.get("sentiment"),
            transcription=result.get("transcription"),
            kpis=result.get("kpis"),
            findings=result.get("findings"),
            errors=result.get("errors"),
            processing_time_seconds=result.get("processing_time_seconds", 0),
            data=result.get("data", {}),
        )

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}",
        )


@router.post("/upload", response_model=AnalysisResult, status_code=status.HTTP_200_OK)
def analyze_uploaded_file(
    file: UploadFile = File(...),
    level: str = "STANDARD",
):
    """
    Upload and analyze an audio file in one request.

    **Levels:** BASIC, STANDARD, ADVANCED

    **Returns:** Full analysis result
    """
    try:
        # Validate level
        if level not in ["BASIC", "STANDARD", "ADVANCED"]:
            raise ValueError(
                f"Invalid level '{level}'. Must be BASIC, STANDARD, or ADVANCED"
            )

        # Create temporary file
        from tempfile import NamedTemporaryFile

        with NamedTemporaryFile(suffix=Path(file.filename).suffix, delete=False) as tmp:
            tmp.write(file.file.read())
            tmp_path = tmp.name

        try:
            logger.info(f"Analyzing uploaded file {file.filename} at level {level}")

            # Analyze using core
            result = analyze_call(tmp_path, level)

            return AnalysisResult(
                status=result.get("status", "error"),
                filename=file.filename,
                service_level=level,
                duration=result.get("duration"),
                qa_score=result.get("qa_score"),
                qa_percentage=result.get("qa_percentage"),
                sentiment=result.get("sentiment"),
                transcription=result.get("transcription"),
                kpis=result.get("kpis"),
                findings=result.get("findings"),
                errors=result.get("errors"),
                processing_time_seconds=result.get("processing_time_seconds", 0),
                data=result.get("data", {}),
            )
        finally:
            # Clean up temp file
            Path(tmp_path).unlink(missing_ok=True)

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Upload/Analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}",
        )


@router.get("/levels")
def get_analysis_levels():
    """
    Get available analysis levels.

    Returns information about what each level includes.
    """
    return {
        "levels": {
            "BASIC": {
                "description": "Transcription + Risk Detection",
                "includes": [
                    "transcription",
                    "risk_assessment",
                ],
            },
            "STANDARD": {
                "description": "BASIC + Sentiment + QA + KPIs",
                "includes": [
                    "transcription",
                    "risk_assessment",
                    "sentiment_analysis",
                    "qa_score",
                    "kpis",
                    "quality_findings",
                ],
            },
            "ADVANCED": {
                "description": "STANDARD + Pattern Detection",
                "includes": [
                    "transcription",
                    "risk_assessment",
                    "sentiment_analysis",
                    "qa_score",
                    "kpis",
                    "quality_findings",
                    "pattern_detection",
                    "anomaly_detection",
                ],
            },
        }
    }


@router.get("/health")
def health_check():
    """Health check for analysis service"""
    return {
        "status": "healthy",
        "service": "analysis",
        "version": "2.0.0",
    }
