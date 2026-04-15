from __future__ import annotations

from io import BytesIO

import streamlit as st

from src.affective_tts.config import EMOJI_MAP, MAX_INPUT_CHARS
from src.affective_tts.emotion import EmotionAnalyzer
from src.affective_tts.safety import SafetyGuard
from src.affective_tts.tts import AffectiveTTSEngine


st.set_page_config(
    page_title="The Empathy Engine",
    page_icon="",
    layout="centered",
)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(255, 214, 153, 0.22), transparent 30%),
                linear-gradient(180deg, #a14ab0 0%, #f3eee6 100%);
        }
        .hero-card {
            padding: 1.25rem 1.1rem;
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.78);
            border: 1px solid rgba(125, 95, 45, 0.14);
            box-shadow: 0 16px 40px rgba(88, 67, 31, 0.08);
            margin-bottom: 1rem;
        }
        .meta-row {
            display: flex;
            gap: 0.6rem;
            flex-wrap: wrap;
            margin-top: 0.7rem;
        }
        .meta-pill {
            padding: 0.35rem 0.7rem;
            border-radius: 999px;
            background: #a14ab0;
            color: #5a4625;
            font-size: 0.88rem;
            border: 1px solid rgba(125, 95, 45, 0.12);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    st.markdown(
        """
        <div class="hero-card">
            <h1 style="margin:0; color:#2f2417;">The Empathy Engine: Giving AI a Human Voice</h1>
            <p style="margin:0.5rem 0 0; color:#5f4d33;">
                Emotion-aware speech synthesis
            </p>
            <div class="meta-row">
                <!-- <span class="meta-pill">Male voice default</span> -->
                <span class="meta-pill">Safety filter on</span>
                <span class="meta-pill">150-char input</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.expander("What this app does", expanded=False):
        st.markdown(
            """
            - Screens input with a tiny profanity model plus regex backstops.
            - Uses a distilled emotion classifier to stay within tight RAM budgets.
            - Generates a base voice with `gTTS` and reshapes tone with `pydub`.
            - Targets free-tier Streamlit hardware by keeping the heavy work lightweight.
            """
        )


def render_controls() -> str:
    st.markdown("### Enter Text")
    text = st.text_area(
        "Input text",
        max_chars=MAX_INPUT_CHARS,
        height=180,
        placeholder="Type up to 150 characters...",
        label_visibility="collapsed",
        help="Keep text short so the emotion detector and TTS stay responsive on low-memory hosts.",
    )
    cols = st.columns([1, 1, 1])
    cols[0].caption(f"{len(text)}/{MAX_INPUT_CHARS} characters")
    #cols[1].caption("Voice: Male")
    cols[2].caption("Safety: On")
    st.caption(
        "Short expressive lines work best here. The app uses the default male-style voice and always runs the safety filter."
    )
    return text.strip()


def render_audio(
    audio_bytes: bytes,
    emotion: str,
    engine_name: str,
    mime_type: str,
    file_extension: str,
) -> None:
    emoji = EMOJI_MAP.get(emotion, "🎧")
    st.success(f"Detected emotion: {emotion} {emoji}")
    st.caption(f"TTS engine: {engine_name}")
    st.audio(audio_bytes, format=mime_type)
    st.download_button(
        f"Download {file_extension.upper()}",
        data=BytesIO(audio_bytes).getvalue(),
        file_name=f"Text-To-Speech{emotion.lower()}.{file_extension}",
        mime=mime_type,
        use_container_width=True,
    )


def main() -> None:
    inject_styles()
    render_header()
    text = render_controls()
    voice_label = "Male"

    if st.button("Generate", type="primary", use_container_width=True):
        if not text:
            st.warning("Enter a short sentence before generating audio.")
            st.stop()

        try:
            with st.spinner("Running safety checks..."):
                safety_guard = SafetyGuard()
                safety_result = safety_guard.evaluate(text)

            if safety_result.blocked:
                st.warning(
                    "The input matched the lightweight safety filter, so audio generation was skipped."
                )
                st.json(safety_result.flagged_scores)
                st.stop()

            with st.spinner("Detecting emotion..."):
                analyzer = EmotionAnalyzer()
                emotion_result = analyzer.predict(text)

            with st.spinner("Generating speech..."):
                tts_engine = AffectiveTTSEngine()
                audio_bytes, mime_type, file_extension = tts_engine.synthesize(
                    text=text,
                    emotion=emotion_result.primary_emotion,
                    voice=voice_label,
                )
                if file_extension == "wav":
                    engine_name = f"gTTS + pydub ({voice_label})"
                else:
                    engine_name = f"gTTS fallback ({voice_label}, ffmpeg missing)"
                    st.info(
                        "ffmpeg was not found, so emotion-based audio shaping was skipped and the base MP3 was returned."
                    )

            render_audio(
                audio_bytes=audio_bytes,
                emotion=emotion_result.primary_emotion,
                engine_name=engine_name,
                mime_type=mime_type,
                file_extension=file_extension,
            )

            with st.expander("Inference details", expanded=False):
                st.json(
                    {
                        "voice_preference": voice_label,
                        "emotion_scores": emotion_result.scores,
                        "safety_scores": safety_result.flagged_scores,
                    }
                )
        except Exception as exc:
            st.error(
                "Generation failed. Check the README for ffmpeg, gTTS, and free-tier deployment notes."
            )
            st.exception(exc)


if __name__ == "__main__":
    main()
