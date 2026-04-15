from __future__ import annotations

import re
from dataclasses import dataclass

from profanity_check import predict, predict_prob

from src.affective_tts.config import PROFANITY_THRESHOLD


LEETSPEAK_TABLE = str.maketrans(
    {
        "@": "a",
        "$": "s",
        "0": "o",
        "1": "i",
        "3": "e",
        "4": "a",
        "5": "s",
        "7": "t",
    }
)

PATTERN_GROUPS = {
    "sexual_content": (
        r"\bnsfw\b",
        r"\bxxx\b",
        r"\bporn(?:o|ography)?\b",
        r"\bsex(?:ual)?\b",
        r"\bnude\b",
        r"\bnaked\b",
        r"\bbreasts?\b",
        r"\bpenis\b",
        r"\bvagina\b",
    ),
    "self_harm_or_threats": (
        r"\bkill\b",
        r"\bmurder\b",
        r"\bstab\b",
        r"\bshoot\b",
        r"\bhang\s+yourself\b",
        r"\bgo\s+die\b",
        r"\bsuicide\b",
    ),
}

COMPILED_PATTERNS = {
    category: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    for category, patterns in PATTERN_GROUPS.items()
}


@dataclass
class SafetyResult:
    blocked: bool
    flagged_scores: dict[str, object]


class SafetyGuard:
    def evaluate(self, text: str) -> SafetyResult:
        normalized = self._normalize_text(text)
        matches: dict[str, list[str]] = {}
        profanity_probability = float(predict_prob([normalized])[0])
        profanity_hit = bool(predict([normalized])[0]) or profanity_probability >= PROFANITY_THRESHOLD

        for category, patterns in COMPILED_PATTERNS.items():
            hits: list[str] = []
            for pattern in patterns:
                for matched in pattern.findall(normalized):
                    if matched not in hits:
                        hits.append(matched)
            if hits:
                matches[category] = hits

        blocked = profanity_hit or bool(matches)
        return SafetyResult(
            blocked=blocked,
            flagged_scores={
                "blocked": blocked,
                "profanity_probability": round(profanity_probability, 4),
                "profanity_hit": profanity_hit,
                "matched_categories": list(matches.keys()),
                "matched_terms": matches,
            },
        )

    @staticmethod
    def _normalize_text(text: str) -> str:
        cleaned = text.lower().translate(LEETSPEAK_TABLE)
        cleaned = re.sub(r"[_\-]+", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned
