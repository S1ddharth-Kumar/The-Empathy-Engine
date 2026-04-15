from __future__ import annotations

import os

from dotenv import load_dotenv


load_dotenv()


MAX_INPUT_CHARS = 150

DEFAULT_EMOTION_MODEL = os.getenv(
    "EMOTION_MODEL_NAME",
    "bhadresh-savani/distilbert-base-uncased-emotion",
)

EMOJI_MAP = {
    "Joy": "😊",
    "Sadness": "😢",
    "Anger": "😠",
    "Fear": "😨",
    "Surprise": "😲",
    "Disgust": "🤢",
    "Confusion": "😕",
}

CANONICAL_EMOTIONS = (
    "Joy",
    "Sadness",
    "Anger",
    "Fear",
    "Surprise",
    "Disgust",
    "Confusion",
)

DISTIL_EMOTION_MAP = {
    "joy": "Joy",
    "love": "Joy",
    "sadness": "Sadness",
    "anger": "Anger",
    "fear": "Fear",
    "surprise": "Surprise",
}

GTTS_MALE_TLD = os.getenv("GTTS_MALE_TLD", "co.uk").strip()
GTTS_FEMALE_TLD = os.getenv("GTTS_FEMALE_TLD", "com.au").strip()
PROFANITY_THRESHOLD = float(os.getenv("PROFANITY_THRESHOLD", "0.65"))
FFMPEG_BINARY = os.getenv("FFMPEG_BINARY", "").strip()
FFPROBE_BINARY = os.getenv("FFPROBE_BINARY", "").strip()
