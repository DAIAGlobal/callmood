"""
RuleSet Engine

Carga, versiona y aplica reglas dinámicas de riesgo/compliance sin tocar código.
- Storage: JSON en data/rulesets.json (se crea un preset por defecto si no existe).
- Funciones: detectar keywords, validar frases obligatorias y medir similitud con un speech base.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


DEFAULT_RULESET = {
    "id": "default",
    "name": "Base compliance",
    "keywords": ["reclamo", "devolucion", "cancelacion"],
    "required_phrases": ["gracias por llamar", "puedo ayudarte"],
    "template_text": (
        "Gracias por llamar. Mi nombre es ____. Estoy para ayudarte. "
        "¿Podrías confirmar tu número de cliente?"
    ),
    "thresholds": {
        "keyword_weight": 2,
        "missing_required_weight": 3,
        "similarity_weight": 5,
        "critical": 10,
        "high": 7,
        "medium": 4,
    },
    "created_by": "system",
    "user_id": "default",
    "created_at": datetime.utcnow().isoformat(),
    "version": 1,
    "active": True,
}


@dataclass
class RuleSet:
    id: str
    name: str
    keywords: List[str]
    required_phrases: List[str]
    template_text: str
    thresholds: Dict[str, float]
    created_by: str = "user"
    user_id: str = "default"
    created_at: str = datetime.utcnow().isoformat()
    version: int = 1
    active: bool = True

    @staticmethod
    def from_dict(data: Dict) -> "RuleSet":
        return RuleSet(
            id=data.get("id") or data.get("name", "ruleset"),
            name=data.get("name", "Unnamed"),
            keywords=data.get("keywords", []),
            required_phrases=data.get("required_phrases", []),
            template_text=data.get("template_text", ""),
            thresholds=data.get("thresholds", {}),
            created_by=data.get("created_by", "user"),
            user_id=data.get("user_id", data.get("created_by", "default")),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            version=int(data.get("version", 1)),
            active=bool(data.get("active", False)),
        )

    def to_dict(self) -> Dict:
        return asdict(self)


class RuleSetRepository:
    def __init__(self, storage_path: Path | str = Path("data/rulesets.json")):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            self._bootstrap_default()

    def _bootstrap_default(self) -> None:
        self.save_all([RuleSet.from_dict(DEFAULT_RULESET)])

    def load_all(self) -> List[RuleSet]:
        try:
            with self.storage_path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            return [RuleSet.from_dict(item) for item in data]
        except FileNotFoundError:
            self._bootstrap_default()
            return [RuleSet.from_dict(DEFAULT_RULESET)]
        except Exception:
            # Archivo corrupto: recrear con default para no romper el pipeline
            self._bootstrap_default()
            return [RuleSet.from_dict(DEFAULT_RULESET)]

    def save_all(self, rulesets: List[RuleSet]) -> None:
        serializable = [rs.to_dict() for rs in rulesets]
        with self.storage_path.open("w", encoding="utf-8") as fh:
            json.dump(serializable, fh, ensure_ascii=False, indent=2)

    def get_active_ruleset(self, user_id: Optional[str] = None) -> Optional[RuleSet]:
        rulesets = self.load_all()
        if user_id:
            for rs in rulesets:
                if rs.active and rs.user_id == user_id:
                    return rs
        for rs in rulesets:
            if rs.active:
                return rs
        return None

    def activate(self, ruleset_id: str) -> Optional[RuleSet]:
        rulesets = self.load_all()
        found = None
        target_user = None
        for rs in rulesets:
            if rs.id == ruleset_id:
                found = rs
                target_user = rs.user_id
                break

        if not found:
            return None

        for rs in rulesets:
            if rs.user_id == target_user:
                rs.active = rs.id == ruleset_id

        self.save_all(rulesets)
        return found

    def upsert(self, ruleset: RuleSet) -> RuleSet:
        rulesets = self.load_all()
        updated = False
        for idx, rs in enumerate(rulesets):
            if rs.id == ruleset.id:
                # Mantener historial incrementando versión
                ruleset.version = rs.version + 1
                rulesets[idx] = ruleset
                updated = True
                break
        if not updated:
            rulesets.append(ruleset)
        self.save_all(rulesets)
        return ruleset


class RuleEngine:
    def __init__(self, repo: RuleSetRepository):
        self.repo = repo

    @staticmethod
    def _normalize(text: str) -> str:
        lowered = text.lower()
        return re.sub(r"[^a-z0-9áéíóúüñ\s]", " ", lowered)

    def detect_keywords(self, transcript: str, keywords: List[str]) -> List[str]:
        text = self._normalize(transcript)
        hits = []
        for kw in keywords:
            norm_kw = kw.lower().strip()
            if not norm_kw:
                continue
            if norm_kw in text:
                hits.append(kw)
        return hits

    def check_required_phrases(self, transcript: str, phrases: List[str]) -> List[str]:
        text = self._normalize(transcript)
        missing = []
        for phrase in phrases:
            norm_phrase = phrase.lower().strip()
            if norm_phrase and norm_phrase not in text:
                missing.append(phrase)
        return missing

    def similarity_to_template(self, transcript: str, template_text: str) -> float:
        text_tokens = set(self._normalize(transcript).split())
        template_tokens = set(self._normalize(template_text).split())
        if not text_tokens or not template_tokens:
            return 0.0
        intersection = len(text_tokens & template_tokens)
        union = len(text_tokens | template_tokens)
        return round(intersection / union, 3)

    def analyze(self, transcript: str, ruleset: Optional[RuleSet] = None, user_id: Optional[str] = None) -> Dict:
        active_ruleset = ruleset or self.repo.get_active_ruleset(user_id=user_id)
        if not active_ruleset:
            return {
                "enabled": False,
                "message": "No active ruleset",
            }

        keywords_hit = self.detect_keywords(transcript, active_ruleset.keywords)
        missing_required = self.check_required_phrases(transcript, active_ruleset.required_phrases)
        similarity = self.similarity_to_template(transcript, active_ruleset.template_text)

        thresholds = active_ruleset.thresholds or {}
        score = (
            len(keywords_hit) * thresholds.get("keyword_weight", 1)
            + len(missing_required) * thresholds.get("missing_required_weight", 2)
            + similarity * thresholds.get("similarity_weight", 5)
        )

        level = "BAJO"
        critical_th = thresholds.get("critical", 12)
        high_th = thresholds.get("high", 8)
        medium_th = thresholds.get("medium", 4)
        if score >= critical_th:
            level = "CRÍTICO"
        elif score >= high_th:
            level = "ALTO"
        elif score >= medium_th:
            level = "MEDIO"

        return {
            "enabled": True,
            "ruleset_id": active_ruleset.id,
            "ruleset_name": active_ruleset.name,
            "version": active_ruleset.version,
            "score": round(score, 2),
            "level": level,
            "keywords_hit": keywords_hit,
            "missing_required": missing_required,
            "similarity": similarity,
            "created_by": active_ruleset.created_by,
            "created_at": active_ruleset.created_at,
        }

    def save_ruleset(self, data: Dict) -> RuleSet:
        ruleset = RuleSet.from_dict(data)
        return self.repo.upsert(ruleset)
