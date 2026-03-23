#!/usr/bin/env python
"""
Smoke test for JSON/TXT report generation utilities.
"""

import json
from pathlib import Path
from datetime import datetime
import wave
import sys
import os

ROOT_DIR = Path(__file__).resolve().parents[1]
ENGINE_SRC = ROOT_DIR / "src" / "engine"
if str(ENGINE_SRC) not in sys.path:
    sys.path.insert(0, str(ENGINE_SRC))

from daia.infrastructure.reporting.report_saver import save_json_report, save_text_report


def _ensure_sample_audio() -> Path:
    path = Path("audio_in/test_silence.wav")
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"\x00\x00" * 16000)
    return path


def _build_fake_result(audio_path: Path) -> dict:
    return {
        "audio_file": str(audio_path),
        "duration": 60,
        "service_level": "standard",
        "status": "completed",
        "data": {
            "transcription": {"text": "Hola, gracias por llamar. ¿Cómo puedo ayudarte?", "duration": 60},
            "qa": {"compliance_percentage": 82.5, "classification": "GOOD", "details": []},
            "sentiment": {"overall": {"label": "positive", "confidence": 0.91}},
            "risk": {"level": "BAJO", "critical_found": []},
            "kpis": {"metrics": {"duration": {"value": 60, "unit": "s", "classification": "ok"}}},
            "patterns": [],
            "anomalies": [],
        },
        "processing_time_seconds": 1.2,
        "generated_at": datetime.now().isoformat(),
    }


def test_report_files_are_created(tmp_path: Path):
    audio_path = _ensure_sample_audio()
    raw_result = _build_fake_result(audio_path)
    reports_dir = tmp_path / "reports"

    json_path = save_json_report(raw_result, output_dir=reports_dir)
    txt_path = save_text_report(raw_result, output_dir=reports_dir)

    assert json_path is not None
    assert txt_path is not None

    json_file = Path(json_path)
    assert json_file.exists()
    with json_file.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    assert payload["qa"]["compliance_percentage"] == raw_result["data"]["qa"]["compliance_percentage"]
    assert "transcript" in payload

    txt_file = Path(txt_path)
    assert txt_file.exists()
    content = txt_file.read_text(encoding="utf-8")
    assert "CallMood" in content
    assert "QA" in content
    assert "RECOMENDACIONES" in content
