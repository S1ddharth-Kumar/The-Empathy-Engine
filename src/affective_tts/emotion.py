from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

import streamlit as st
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

from src.affective_tts.config import (
    CANONICAL_EMOTIONS,
    DEFAULT_EMOTION_MODEL,
    DISTIL_EMOTION_MAP,
)

try:
    from torch.ao.quantization import quantize_dynamic
except ImportError:  # pragma: no cover
    from torch.quantization import quantize_dynamic  # type: ignore


torch.set_num_threads(1)


@dataclass
class EmotionResult:
    primary_emotion: str
    scores: dict[str, float]


@st.cache_resource(show_spinner=False)
def _load_emotion_classifier():
    tokenizer = AutoTokenizer.from_pretrained(DEFAULT_EMOTION_MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(
        DEFAULT_EMOTION_MODEL,
        low_cpu_mem_usage=True,
    )
    model.eval()
    model = quantize_dynamic(model, {torch.nn.Linear}, dtype=torch.qint8)
    return pipeline(
        "text-classification",
        model=model,
        tokenizer=tokenizer,
        top_k=None,
        device=-1,
    )


class EmotionAnalyzer:
    def __init__(self) -> None:
        self.classifier = _load_emotion_classifier()

    def predict(self, text: str) -> EmotionResult:
        raw_scores = self.classifier(
            text,
            truncation=True,
            max_length=256,
        )
        scores = self._normalize_scores(raw_scores[0])
        return EmotionResult(primary_emotion=max(scores, key=scores.get), scores=scores)

    def _normalize_scores(self, raw_scores: list[dict[str, float]]) -> dict[str, float]:
        aggregated = defaultdict(float)

        for entry in raw_scores:
            canonical = DISTIL_EMOTION_MAP.get(entry["label"].lower())
            if canonical:
                aggregated[canonical] += float(entry["score"])

        if not aggregated:
            aggregated["Confusion"] = 1.0

        best_score = max(aggregated.values())
        if best_score < 0.6:
            aggregated["Confusion"] = max(aggregated["Confusion"], 1.0 - best_score)
            if aggregated.get("Anger", 0.0) >= 0.45:
                aggregated["Disgust"] = aggregated["Anger"] * 0.75

        ordered_scores = {}
        for emotion in CANONICAL_EMOTIONS:
            ordered_scores[emotion] = round(float(aggregated.get(emotion, 0.0)), 4)
        return ordered_scores
