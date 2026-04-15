# Affective TTS Streamlit App

This project is a hardware-lite Streamlit app for emotion-aware text to speech on free-tier hosting. It uses a distilled emotion classifier locally, a tiny profanity screen for safety, and `gTTS` plus `pydub` for low-cost voice generation and emotion shaping.

## Features

- Lightweight safety gate using `alt-profanity-check` plus regex backstops for sexual or self-harm phrases.
- Distilled transformer emotion analysis with `bhadresh-savani/distilbert-base-uncased-emotion`.
- Base speech generation with `gTTS`.
- Emotion-aware pitch, speed, and gain shaping with `pydub`.
- Streamlit UI with a 150-character limit, default male voice, always-on safety filter, audio player, and WAV download.
- `packages.txt` support for `ffmpeg` so Streamlit Cloud can process audio.

## Project Layout

```text
text-speech/
├── app.py
├── .env.example
├── packages.txt
├── README.md
├── requirements.txt
└── src/
    └── affective_tts/
        ├── __init__.py
        ├── config.py
        ├── emotion.py
        ├── safety.py
        └── tts.py
```

## Walkthrough

### 1. Safety screening

The app first checks the input with `alt-profanity-check`, which is much lighter than moderation transformers and works well on CPU. It also runs small regex backstops for:

- sexual content
- self-harm or violent threats

If the text is flagged, audio generation stops immediately.

### 2. Emotion detection

Emotion tagging uses:

- `bhadresh-savani/distilbert-base-uncased-emotion`

This is much smaller than the earlier RoBERTa-based setup and is a better fit for free-tier memory limits. The model is also dynamically quantized to reduce the size of linear layers on CPU.

### 3. Emotion mapping

The raw model labels are folded into the app’s UI emotions:

- `joy`, `love` -> `Joy`
- `sadness` -> `Sadness`
- `anger` -> `Anger`
- `fear` -> `Fear`
- `surprise` -> `Surprise`
- low-confidence predictions -> `Confusion`

The model does not directly emit `Disgust`, so the app only infers it in low-confidence anger-heavy cases.

### 4. TTS generation

The app generates a base MP3 with `gTTS`, then loads it into `pydub` and reshapes the audio:

- `Joy` or `Surprise`: faster and brighter
- `Sadness` or `Fear`: slower and lower
- `Anger` or `Disgust`: faster, sharper, and louder
- `Confusion`: slightly slower with a mild pitch lift

The app uses the default male-style `gTTS` voice configuration so the flow stays simple and free-tier friendly.

If `ffmpeg` or `ffprobe` is unavailable, the app now falls back to the raw `gTTS` MP3 instead of crashing. In that case, emotion-based pitch and speed shaping is skipped.

### 5. Streamlit Cloud deployment

For Streamlit Cloud or other free-tier hosts:

- keep prompts short
- install Python packages from `requirements.txt`
- install `ffmpeg` through `packages.txt`
- avoid local TTS models entirely

## Setup

### 1. Create and activate a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Create a local `.env` file

Copy `.env.example` to `.env` and adjust values if you want:

```dotenv
EMOTION_MODEL_NAME=bhadresh-savani/distilbert-base-uncased-emotion
GTTS_MALE_TLD=co.uk
GTTS_FEMALE_TLD=com.au
PROFANITY_THRESHOLD=0.65
FFMPEG_BINARY=
FFPROBE_BINARY=
```

### 4. Run the app

```powershell
streamlit run app.py
```

## Configuration

The app loads `.env` automatically via `python-dotenv`.

Available settings:

- `EMOTION_MODEL_NAME`: defaults to `bhadresh-savani/distilbert-base-uncased-emotion`
- `GTTS_MALE_TLD`: defaults to `co.uk`
- `GTTS_FEMALE_TLD`: defaults to `com.au`
- `PROFANITY_THRESHOLD`: defaults to `0.65`
- `FFMPEG_BINARY`: optional absolute path to `ffmpeg.exe`
- `FFPROBE_BINARY`: optional absolute path to `ffprobe.exe`

## Why This Fits Free-Tier Hardware

- No local TTS model is loaded into RAM.
- `gTTS` handles speech generation remotely.
- The local model is a distilled emotion classifier instead of a large RoBERTa encoder.
- Safety uses a small profanity model and regex checks instead of a heavy moderation model.
- `ffmpeg` is the only extra system dependency.
- On Windows, if `ffmpeg` is not on `PATH`, set `FFMPEG_BINARY` and `FFPROBE_BINARY` in `.env`.

## Suggested Next Improvements

- Add caching for generated WAV files so repeat prompts return instantly.
- Add a visible warning that the Male/Female toggle changes accent style, not a true speaker identity model.
- Add a fallback regex-only safety mode in case the profanity package fails to load.
