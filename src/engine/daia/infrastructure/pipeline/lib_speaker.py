"""
Speaker identification and role assignment utilities for DAIA.

Features:
- Detect mono/stereo layout and basic audio metadata.
- Stereo path: split channels and treat left=operator, right=client.
- Mono path: lightweight diarization and role inference with cue phrases.
- Build transcript_by_speaker, role mapping, speaking balance and sentiment per role.

Designed to stay offline and keep backward compatibility with existing pipeline output.
"""

from __future__ import annotations

import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import librosa
import numpy as np
from pydub import AudioSegment

logger = logging.getLogger(__name__)


@dataclass
class AudioProfile:
    """Simple audio metadata used for routing the pipeline."""

    channels: int
    sample_rate: int
    duration_seconds: float
    sample_width: int
    frame_rate: int
    format: str

    @property
    def is_stereo(self) -> bool:
        return self.channels == 2


@dataclass
class SpeakerSegment:
    """Minimal representation of a diarized segment."""

    speaker: str
    start: float
    end: float
    confidence: float = 0.5


def detect_audio_profile(audio_path: str) -> AudioProfile:
    """Return audio metadata used to decide mono/stereo path."""

    audio = AudioSegment.from_file(audio_path)
    duration_seconds = len(audio) / 1000.0
    return AudioProfile(
        channels=audio.channels,
        sample_rate=audio.frame_rate,
        duration_seconds=duration_seconds,
        sample_width=audio.sample_width,
        frame_rate=audio.frame_rate,
        format=Path(audio_path).suffix.lower(),
    )


def split_stereo_channels(audio_path: str) -> Tuple[str, str]:
    """Split a stereo file into two temporary mono wav files.

    Returns:
        tuple(left_path, right_path)
    """

    audio = AudioSegment.from_file(audio_path)
    if audio.channels != 2:
        raise ValueError("Audio is not stereo; cannot split channels")

    left, right = audio.split_to_mono()

    left_tmp = tempfile.NamedTemporaryFile(suffix="_left.wav", delete=False)
    right_tmp = tempfile.NamedTemporaryFile(suffix="_right.wav", delete=False)

    left.export(left_tmp.name, format="wav")
    right.export(right_tmp.name, format="wav")

    logger.debug("Stereo channels exported to temporary wav files")
    return left_tmp.name, right_tmp.name


class LightweightDiarizer:
    """Lightweight diarization fallback (no external heavy models).

    Approach: energy-based VAD + alternating speaker assignment. Not as
    accurate as pyannote but keeps the system fully offline and dependency-free.
    """

    def __init__(self, frame_ms: int = 32, hop_ms: int = 16, energy_threshold: float = 0.5):
        self.frame_ms = frame_ms
        self.hop_ms = hop_ms
        self.energy_threshold = energy_threshold

    def diarize(self, audio_path: str) -> List[SpeakerSegment]:
        y, sr = librosa.load(audio_path, sr=16000, mono=True)
        frame_length = int(sr * self.frame_ms / 1000)
        hop_length = int(sr * self.hop_ms / 1000)

        rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
        rms_norm = rms / (np.max(rms) + 1e-9)
        threshold = max(self.energy_threshold * np.mean(rms_norm), 0.05)

        segments: List[SpeakerSegment] = []
        active = False
        start_frame = 0
        last_active_frame = 0

        for idx, energy in enumerate(rms_norm):
            if energy >= threshold and not active:
                active = True
                start_frame = idx
            if energy >= threshold:
                last_active_frame = idx
            if energy < threshold and active:
                segments.append(self._build_segment(start_frame, last_active_frame, hop_length, sr, len(segments)))
                active = False

        if active:
            segments.append(self._build_segment(start_frame, last_active_frame, hop_length, sr, len(segments)))

        if not segments:
            # Fallback: single speaker segment covering the entire audio
            duration = len(y) / sr
            segments = [SpeakerSegment(speaker="speaker_1", start=0.0, end=duration, confidence=0.2)]

        return segments

    def _build_segment(self, start_frame: int, end_frame: int, hop_length: int, sr: int, idx: int) -> SpeakerSegment:
        start = (start_frame * hop_length) / sr
        end = ((end_frame + 1) * hop_length) / sr
        speaker_label = "speaker_1" if idx % 2 == 0 else "speaker_2"
        return SpeakerSegment(speaker=speaker_label, start=start, end=end, confidence=0.5)


class SpeakerRoleAnalyzer:
    """End-to-end speaker detection and role mapping for DAIA."""

    OPERATOR_CUES = [
        "lo llamo de",
        "buenos dias",
        "buenos días",
        "mi nombre es",
        "habla con",
        "en que puedo ayudar",
        "soy del",
    ]
    CLIENT_CUES = [
        "no puedo pagar",
        "estoy sin trabajo",
        "necesito ayuda",
        "no me cobraron bien",
        "no tengo dinero",
        "no estoy de acuerdo",
    ]

    def __init__(self, transcriber, sentiment_analyzer=None):
        self.transcriber = transcriber
        self.sentiment_analyzer = sentiment_analyzer
        self.diarizer = LightweightDiarizer()

    def process_audio(self, audio_path: str) -> Dict[str, Any]:
        audio_profile = detect_audio_profile(audio_path)
        logger.info(
            "Perfil de audio: channels=%s, sr=%s, duration=%.2fs",
            audio_profile.channels,
            audio_profile.sample_rate,
            audio_profile.duration_seconds,
        )

        if audio_profile.is_stereo:
            return self._process_stereo(audio_path, audio_profile)
        return self._process_mono(audio_path, audio_profile)

    def _process_stereo(self, audio_path: str, profile: AudioProfile) -> Dict[str, Any]:
        logger.info("Detectado audio estéreo → canal izquierdo=operador, derecho=cliente")
        left_path, right_path = split_stereo_channels(audio_path)

        operator_tx = self.transcriber.transcribe_file(left_path, with_segments=False)
        client_tx = self.transcriber.transcribe_file(right_path, with_segments=False)

        transcript_by_speaker = [
            {
                "speaker": "channel_left",
                "role": "operator",
                "text": operator_tx.get("text", ""),
                "duration": operator_tx.get("duration", profile.duration_seconds / 2),
                "word_count": len(operator_tx.get("text", "").split()),
            },
            {
                "speaker": "channel_right",
                "role": "client",
                "text": client_tx.get("text", ""),
                "duration": client_tx.get("duration", profile.duration_seconds / 2),
                "word_count": len(client_tx.get("text", "").split()),
            },
        ]

        combined_text = self._build_labeled_transcript(transcript_by_speaker)
        role_mapping = {
            "operator": "channel_left",
            "client": "channel_right",
            "confidence": 0.95,
            "strategy": "stereo_channel_mapping",
            "notes": "Canal izquierdo forzado a operador por policy",
        }

        sentiment = self._sentiment_for_roles(transcript_by_speaker, combined_text)
        speaking_balance = self._compute_speaking_balance(transcript_by_speaker)

        transcript_result = {
            "filename": Path(audio_path).name,
            "text": combined_text,
            "language": operator_tx.get("language", "es") or client_tx.get("language", "es"),
            "duration": profile.duration_seconds,
            "model_used": self.transcriber.model_name,
            "device_used": self.transcriber.device,
            "char_count": len(combined_text),
            "segments": [],
            "transcript_by_speaker": transcript_by_speaker,
            "role_mapping": role_mapping,
            "speaking_balance": speaking_balance,
            "sentiment_by_role": sentiment,
        }

        return {
            "transcript": transcript_result,
            "audio_profile": profile.__dict__,
            "speaker_summary": self._build_speaker_summary(transcript_by_speaker, role_mapping, sentiment, profile),
        }

    def _process_mono(self, audio_path: str, profile: AudioProfile) -> Dict[str, Any]:
        logger.info("Audio mono → iniciando diarización y asignación de roles")

        diar_segments = self.diarizer.diarize(audio_path)
        whisper_result = self.transcriber.transcribe_file(audio_path, with_segments=True)

        whisper_segments = whisper_result.get("segments", [])
        aligned_segments = self._align_segments(whisper_segments, diar_segments)
        transcript_by_speaker = self._aggregate_by_speaker(aligned_segments)

        role_mapping = self._infer_roles(transcript_by_speaker)
        combined_text = self._build_labeled_transcript(transcript_by_speaker)
        sentiment = self._sentiment_for_roles(transcript_by_speaker, combined_text)
        speaking_balance = self._compute_speaking_balance(transcript_by_speaker)

        transcript_result = {
            "filename": Path(audio_path).name,
            "text": combined_text,
            "language": whisper_result.get("language", "es"),
            "duration": whisper_result.get("duration", profile.duration_seconds),
            "model_used": self.transcriber.model_name,
            "device_used": self.transcriber.device,
            "char_count": len(combined_text),
            "segments": aligned_segments,
            "transcript_by_speaker": transcript_by_speaker,
            "role_mapping": role_mapping,
            "speaking_balance": speaking_balance,
            "sentiment_by_role": sentiment,
        }

        return {
            "transcript": transcript_result,
            "audio_profile": profile.__dict__,
            "speaker_summary": self._build_speaker_summary(transcript_by_speaker, role_mapping, sentiment, profile),
        }

    def _align_segments(self, whisper_segments: List[Dict[str, Any]], diar_segments: List[SpeakerSegment]) -> List[Dict[str, Any]]:
        """Assign whisper segments to diarized speaker ids by midpoint overlap."""

        aligned = []
        for ws in whisper_segments:
            midpoint = (ws.get("start", 0) + ws.get("end", 0)) / 2
            matched = next((ds for ds in diar_segments if ds.start <= midpoint <= ds.end), None)
            speaker = matched.speaker if matched else "speaker_1"
            confidence = matched.confidence if matched else 0.3
            aligned.append(
                {
                    "speaker": speaker,
                    "start": ws.get("start", 0.0),
                    "end": ws.get("end", 0.0),
                    "text": ws.get("text", ""),
                    "confidence": confidence,
                }
            )
        return aligned

    def _aggregate_by_speaker(self, aligned_segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        bucket: Dict[str, Dict[str, Any]] = {}
        for seg in aligned_segments:
            speaker = seg["speaker"]
            entry = bucket.setdefault(
                speaker,
                {"speaker": speaker, "text": "", "duration": 0.0, "segments": [], "word_count": 0},
            )
            entry["text"] += seg.get("text", "").strip() + " "
            entry["duration"] += max(seg.get("end", 0) - seg.get("start", 0), 0)
            entry["segments"].append(seg)

        # Normalize and compute word counts
        for entry in bucket.values():
            entry["text"] = entry["text"].strip()
            entry["word_count"] = len(entry["text"].split())

        return list(bucket.values())

    def _infer_roles(self, transcript_by_speaker: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not transcript_by_speaker:
            return {"operator": None, "client": None, "confidence": 0.0, "strategy": "no_data"}

        scores = {}
        for idx, speaker_entry in enumerate(transcript_by_speaker):
            text_lower = speaker_entry.get("text", "").lower()
            score = 0.0
            # Initial speaker bias → likely operator
            if idx == 0:
                score += 0.3
            score += sum(1 for cue in self.OPERATOR_CUES if cue in text_lower) * 0.2
            score -= sum(1 for cue in self.CLIENT_CUES if cue in text_lower) * 0.2
            scores[speaker_entry["speaker"]] = score

        if len(scores) == 1:
            speaker_id = next(iter(scores))
            return {
                "operator": speaker_id,
                "client": None,
                "confidence": 0.4,
                "strategy": "single_speaker",
                "notes": "Solo se detectó un hablante",
            }

        # Choose operator as highest score, client as the other
        sorted_speakers = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        operator_id, operator_score = sorted_speakers[0]
        client_id, client_score = sorted_speakers[1]

        confidence = min(max(operator_score - client_score, 0.2), 0.95)
        uncertain = confidence < 0.5

        return {
            "operator": operator_id,
            "client": client_id,
            "confidence": confidence,
            "strategy": "cue_and_order",
            "uncertain": uncertain,
        }

    def _build_labeled_transcript(self, transcript_by_speaker: List[Dict[str, Any]]) -> str:
        lines = []
        for speaker_entry in transcript_by_speaker:
            role = speaker_entry.get("role") or speaker_entry.get("speaker")
            text = speaker_entry.get("text", "").strip()
            if not text:
                continue
            label = role.upper()
            lines.append(f"[{label}] {text}")
        return "\n".join(lines).strip()

    def _compute_speaking_balance(self, transcript_by_speaker: List[Dict[str, Any]]) -> Dict[str, Any]:
        operator_words = 0
        client_words = 0
        for entry in transcript_by_speaker:
            role = entry.get("role") or entry.get("speaker")
            words = entry.get("word_count", 0)
            if role == "operator":
                operator_words += words
            elif role == "client":
                client_words += words

        total = operator_words + client_words
        if total == 0:
            return {
                "operator_percentage": 0.0,
                "client_percentage": 0.0,
                "balance_quality": "SIN_DATOS",
                "note": "sin palabras",
            }

        operator_pct = (operator_words / total) * 100
        client_pct = (client_words / total) * 100
        balance_quality = "BUENO" if 35 <= operator_pct <= 55 else "DESBALANCEADO"

        return {
            "operator_percentage": (operator_words / total) * 100,
            "client_percentage": client_pct,
            "operator_words": operator_words,
            "client_words": client_words,
            "unit": "porcentaje",
            "balance_quality": balance_quality,
        }

    def _sentiment_for_roles(self, transcript_by_speaker: List[Dict[str, Any]], combined_text: str) -> Dict[str, Any]:
        if not self.sentiment_analyzer:
            return {}

        operator_text = " ".join(entry.get("text", "") for entry in transcript_by_speaker if entry.get("role") == "operator")
        client_text = " ".join(entry.get("text", "") for entry in transcript_by_speaker if entry.get("role") == "client")

        return {
            "operator": self.sentiment_analyzer.analyze_text(operator_text) if operator_text else None,
            "client": self.sentiment_analyzer.analyze_text(client_text) if client_text else None,
            "overall": self.sentiment_analyzer.analyze_text(combined_text),
        }

    def _build_speaker_summary(
        self,
        transcript_by_speaker: List[Dict[str, Any]],
        role_mapping: Dict[str, Any],
        sentiment: Dict[str, Any],
        profile: AudioProfile,
    ) -> Dict[str, Any]:
        return {
            "speakers": transcript_by_speaker,
            "role_mapping": role_mapping,
            "sentiment_by_role": sentiment,
            "speaking_balance": self._compute_speaking_balance(transcript_by_speaker),
            "audio_profile": profile.__dict__,
        }
