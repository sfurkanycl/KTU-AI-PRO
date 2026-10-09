import hashlib
import io
import os
import random
import re
import threading
import time
import wave
from pathlib import Path
from learning_engine.turkish_text import restore_text
from learning_engine.voice_config import cache_identity

from dotenv import load_dotenv
from google import genai
from google.genai import types
import httpx


BASE_DIR = Path(__file__).resolve().parent
CACHE_DIR = Path(os.environ['OM_LOCAL_DATA_DIR'])/'audio_cache' if os.environ.get('OM_LOCAL_DATA_DIR') else BASE_DIR / "audio_cache"
CACHE_DIR.mkdir(parents=True,exist_ok=True)

load_dotenv(BASE_DIR / ".env")

LOCK = threading.Lock()
GEMINI_BLOCKED_UNTIL = 0.0
NEXT_GEMINI_REQUEST = 0.0

STYLE = (
    "Speak in fluent, natural Turkish. Sound like a warm, "
    "patient primary-school teacher. Use clear pronunciation "
    "and a comfortable pace. Do not sound robotic or sing-song."
)


def gemini_audio(text):
    key = os.getenv("GEMINI_GENERATOR_KEY", "").strip()

    if not key:
        raise ValueError("API anahtarı bulunamadı.")

    client = genai.Client(
        api_key=key,
        http_options=types.HttpOptions(timeout=60000),
    )

    try:
        response = client.models.generate_content(
            model=os.getenv(
                "GEMINI_TTS_MODEL",
                "gemini-3.8-flash-tts",
            ),
            contents=[{
                "role": "user",
                "parts": [{
                    "text": text,
                    "speech_metadata": {"style": STYLE},
                }],
            }],
            config={
                "response_modalities": ["AUDIO"],
                "speech_config": {
                    "voice_config": {
                        "voice": os.getenv(
                            "GEMINI_TTS_VOICE", "Kore"
                        )
                    }
                },
            },
        )
    finally:
        client.close()

    for candidate in response.candidates or []:
        if not candidate.content:
            continue

        for part in candidate.content.parts or []:
            if part.inline_data and part.inline_data.data:
                audio = part.inline_data.data

                if (
                    audio[:4] == b"RIFF"
                    and audio[8:12] == b"WAVE"
                ):
                    return audio

                mime = part.inline_data.mime_type or ""
                if mime.lower().startswith(("audio/l16", "audio/pcm")):
                    rate = re.search(r"rate=(\d+)", mime)
                    if len(audio) % 2:
                        raise ValueError("Eksik PCM ses verisi.")
                    buffer = io.BytesIO()
                    with wave.open(buffer, "wb") as wav:
                        wav.setnchannels(1)
                        wav.setsampwidth(2)
                        wav.setframerate(int(rate.group(1)) if rate else 24000)
                        wav.writeframes(audio)
                    return buffer.getvalue()

    raise ValueError("Geçerli WAV sesi alınamadı.")


class AudioUnavailable(RuntimeError):
    """A recoverable Gemini error suitable for display in the UI."""


def error_code(error):
    try:
        return int(getattr(error, "code", None) or
                   getattr(getattr(error, "response", None), "status_code", 0))
    except (TypeError, ValueError):
        return 0


def retry_delay(error):
    response = getattr(error, "response", None)
    headers = getattr(response, "headers", {}) or {}
    try:
        delay = float(headers.get("retry-after", 0))
    except (TypeError, ValueError):
        delay = 0
    match = re.search(r'(?:retryDelay[\"\s:]+|retry in\s+)([\d.]+)s',
                      str(error), re.IGNORECASE)
    if match:
        delay = max(delay, float(match.group(1)))
    return max(15.0, delay)


def warmup_audio():
    if os.getenv("AUDIO_PROVIDER", "piper").lower() == "piper":
        from learning_engine.local_audio import start
        start()


def synthesize(text):
    """Use local speech by default; Gemini is an explicit opt-in."""
    provider = os.getenv("AUDIO_PROVIDER", "piper").strip().lower()
    if provider == "gemini":
        return synthesize_gemini(text)
    if provider == "elevenlabs":
        from learning_engine.eleven_audio import synthesize_elevenlabs
        return synthesize_elevenlabs(text, CACHE_DIR)
    if provider != "piper":
        raise AudioUnavailable("Geçersiz AUDIO_PROVIDER. piper, gemini veya elevenlabs seç.")
    text = restore_text(text).strip()
    if not text:
        raise ValueError("Seslendirilecek metin boş.")
    digest = hashlib.sha256((cache_identity() + "|" + text).encode("utf-8")).hexdigest()
    path = CACHE_DIR / f"local-{digest}.wav"
    with LOCK:
        if path.exists():
            return path.read_bytes()
        from learning_engine.local_audio import local_audio
        try:
            audio = local_audio(text)
        except Exception as error:
            raise AudioUnavailable(str(error)) from error
        temporary = path.with_suffix(".tmp")
        temporary.write_bytes(audio)
        temporary.replace(path)
        return audio


def synthesize_gemini(text):
    global GEMINI_BLOCKED_UNTIL
    global NEXT_GEMINI_REQUEST

    text = text.strip()
    if not text:
        raise ValueError("Seslendirilecek metin boş.")

    voice = os.getenv("GEMINI_TTS_VOICE", "Kore")
    model = os.getenv(
        "GEMINI_TTS_MODEL",
        "gemini-3.8-flash-tts",
    )

    identity = "|".join([model, voice, STYLE, text])
    digest = hashlib.sha256(
        identity.encode("utf-8")
    ).hexdigest()

    primary_path = CACHE_DIR / f"{digest}.wav"

    # Only reuse natural Gemini speech.
    if primary_path.exists():
        return primary_path.read_bytes()

    with LOCK:
        # Another request may have generated it while waiting.
        if primary_path.exists():
            return primary_path.read_bytes()

        now = time.monotonic()

        if now < GEMINI_BLOCKED_UNTIL:
            raise AudioUnavailable(
                f"Gemini ses kotası beklemede. "
                f"{int(GEMINI_BLOCKED_UNTIL - now) + 1} saniye sonra tekrar dinle."
            )

        remaining = NEXT_GEMINI_REQUEST - now

        if remaining > 0:
            time.sleep(remaining)

        NEXT_GEMINI_REQUEST = time.monotonic() + 15.0

        try:
            for attempt in range(3):
                try:
                    audio = gemini_audio(text)
                    break
                except Exception as error:
                    code = error_code(error)
                    transient = code in (429, 500, 502, 503, 504) or isinstance(
                        error, (httpx.TransportError, ConnectionError, TimeoutError)
                    )
                    if not transient:
                        raise
                    delay = retry_delay(error) if code == 429 else 2 ** (attempt + 1)
                    if code == 429:
                        GEMINI_BLOCKED_UNTIL = time.monotonic() + delay
                    if attempt == 2 or delay > 60:
                        raise AudioUnavailable(
                            f"Gemini ses {'kotası dolu' if code == 429 else 'bağlantısı kesildi'}. "
                            f"{int(delay) + 1} saniye sonra tekrar dinle."
                        ) from error
                    time.sleep(delay + random.uniform(0, 1))
                    NEXT_GEMINI_REQUEST = time.monotonic() + 15.0

            temporary = primary_path.with_suffix(".tmp")
            temporary.write_bytes(audio)
            temporary.replace(primary_path)

            print("[SES] Akıcı Gemini sesi")
            return audio

        except Exception as error:
            code = error_code(error)

            print(
                f"[SES] Gemini sesi hazırlanamadı ({code}). "
                "Yedek sese geçilmiyor."
            )
            raise
