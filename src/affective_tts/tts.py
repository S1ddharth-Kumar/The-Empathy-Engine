from __future__ import annotations

from io import BytesIO

from gtts import gTTS
from pydub import AudioSegment

from src.affective_tts.config import (
    FFMPEG_BINARY,
    FFPROBE_BINARY,
    GTTS_FEMALE_TLD,
    GTTS_MALE_TLD,
)


class AffectiveTTSEngine:
    def __init__(self) -> None:
        if FFMPEG_BINARY:
            AudioSegment.converter = FFMPEG_BINARY
        if FFPROBE_BINARY:
            AudioSegment.ffprobe = FFPROBE_BINARY

    def synthesize(self, text: str, emotion: str, voice: str) -> tuple[bytes, str, str]:
        tld = GTTS_MALE_TLD if voice == "Male" else GTTS_FEMALE_TLD
        mp3_buffer = BytesIO()
        gTTS(text=text, lang="en", tld=tld, slow=False).write_to_fp(mp3_buffer)
        mp3_bytes = mp3_buffer.getvalue()

        try:
            mp3_buffer.seek(0)
            audio = AudioSegment.from_file(mp3_buffer, format="mp3")
            audio = self.apply_emotion(audio, emotion)

            wav_buffer = BytesIO()
            audio.export(wav_buffer, format="wav")
            return wav_buffer.getvalue(), "audio/wav", "wav"
        except FileNotFoundError:
            # ffmpeg/ffprobe is unavailable, so return the base gTTS MP3 instead of crashing
            return mp3_bytes, "audio/mp3", "mp3"

    def apply_emotion(self, audio: AudioSegment, emotion: str) -> AudioSegment:
        settings = {
            "Joy": {"speed": 1.1, "semitones": 2.0, "gain": 1.5},
            "Surprise": {"speed": 1.1, "semitones": 2.0, "gain": 1.5},
            "Sadness": {"speed": 0.8, "semitones": -2.0, "gain": -1.5},
            "Fear": {"speed": 0.8, "semitones": -2.0, "gain": -1.0},
            "Anger": {"speed": 1.2, "semitones": 1.0, "gain": 4.0},
            "Disgust": {"speed": 1.2, "semitones": 1.0, "gain": 3.0},
            "Confusion": {"speed": 0.9, "semitones": 0.5, "gain": 0.0},
        }.get(emotion, {"speed": 1.0, "semitones": 0.0, "gain": 0.0})

        if settings["semitones"]:
            audio = self._change_pitch(audio, settings["semitones"])
        if settings["speed"] != 1.0:
            audio = self._change_speed(audio, settings["speed"])
        if settings["gain"]:
            audio = audio.apply_gain(settings["gain"])
        return audio

    @staticmethod
    def _change_pitch(audio: AudioSegment, semitones: float) -> AudioSegment:
        new_frame_rate = int(audio.frame_rate * (2.0 ** (semitones / 12.0)))
        return audio._spawn(
            audio.raw_data,
            overrides={"frame_rate": new_frame_rate},
        ).set_frame_rate(audio.frame_rate)

    @staticmethod
    def _change_speed(audio: AudioSegment, speed: float) -> AudioSegment:
        new_frame_rate = int(audio.frame_rate * speed)
        return audio._spawn(
            audio.raw_data,
            overrides={"frame_rate": new_frame_rate},
        ).set_frame_rate(audio.frame_rate)
