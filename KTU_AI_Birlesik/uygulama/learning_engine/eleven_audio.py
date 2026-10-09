"""ElevenLabs Turkish speech, cached as pygame-compatible PCM WAV."""
import hashlib
import io
import json
import os
import re
import threading
import time
import wave

import httpx
from learning_engine.turkish_text import restore_text

LOCK = threading.Lock()
BLOCKED_UNTIL = 0.0


def synthesize_elevenlabs(text, cache_dir):
    from learning_engine.audio_service import AudioUnavailable
    global BLOCKED_UNTIL
    text = restore_text(text).strip()
    if not text:
        raise ValueError("Seslendirilecek metin boş.")
    selected = os.getenv("ELEVENLABS_VOICE", "jessica").strip().lower()
    if selected not in ("jessica", "cicek", "ryan"):
        raise AudioUnavailable("ELEVENLABS_VOICE için jessica, cicek veya ryan seç.")
    default_voice = "cgSgspJ2msm6clMCkdW9" if selected == "jessica" else ""
    voice = os.getenv(f"ELEVENLABS_{selected.upper()}_VOICE_ID", default_voice).strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", voice):
        raise AudioUnavailable(f"{selected} sesinin ElevenLabs Voice ID bilgisi .env dosyasında eksik veya geçersiz.")
    model = os.getenv("ELEVENLABS_MODEL", "eleven_multilingual_v2").strip()
    payload = {"text": text, "model_id": model,
               "voice_settings": {"stability": 0.5, "similarity_boost": 0.75,
                                  "style": 0.0, "use_speaker_boost": True}}
    identity = json.dumps([voice, payload, "pcm_24000"], ensure_ascii=False, sort_keys=True)
    path = cache_dir / ("eleven-" + hashlib.sha256(identity.encode()).hexdigest() + ".wav")
    with LOCK:
        if path.exists():
            return path.read_bytes()
        key = os.getenv("ELEVENLABS_API_KEY", "").strip()
        if not key:
            raise AudioUnavailable("ElevenLabs API anahtarını yerel .env dosyasına ekle.")
        if time.monotonic() < BLOCKED_UNTIL:
            raise AudioUnavailable(f"ElevenLabs kullanım sınırı beklemede. {int(BLOCKED_UNTIL - time.monotonic()) + 1} saniye sonra tekrar dene.")
        try:
            with httpx.Client(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
                response = client.post(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{voice}",
                    params={"output_format": "pcm_24000"},
                    headers={"xi-api-key": key}, json=payload)
        except httpx.TransportError:
            raise AudioUnavailable("ElevenLabs bağlantısı kurulamadı. İnternet bağlantını kontrol edip tekrar dinle.") from None
        if response.status_code == 429:
            try:
                delay = max(15.0, min(3600.0, float(response.headers.get("retry-after", "30"))))
            except ValueError:
                delay = 30.0
            BLOCKED_UNTIL = time.monotonic() + delay
            raise AudioUnavailable("ElevenLabs kota veya eşzamanlı istek sınırına ulaşıldı. Hesabın kullanımını kontrol et.")
        if response.status_code in (401, 403):
            raise AudioUnavailable("ElevenLabs anahtarı veya ses erişim izni geçersiz. Hesap ayarlarını kontrol et.")
        if response.status_code != 200:
            raise AudioUnavailable(f"ElevenLabs sesi hazırlanamadı (HTTP {response.status_code}). Voice ID ve model ayarlarını kontrol et.")
        pcm = response.content
        if not pcm or len(pcm) % 2 or "json" in response.headers.get("content-type", "").lower():
            raise AudioUnavailable("ElevenLabs geçerli PCM ses verisi döndürmedi.")
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(24000)
            wav.writeframes(pcm)
        audio = buffer.getvalue()
        temporary = path.with_suffix(".tmp")
        temporary.write_bytes(audio)
        temporary.replace(path)
        return audio
