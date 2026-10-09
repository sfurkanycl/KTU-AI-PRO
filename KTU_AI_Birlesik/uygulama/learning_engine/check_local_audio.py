"""Exercise the real local HTTP API, WAV output, cache and pygame playback."""
import io
import json
import os
import tempfile
import time
import wave
from pathlib import Path
from unittest.mock import patch

import httpx
import pygame

from learning_engine import audio_service
from learning_engine import local_audio
from learning_engine.voice_config import voice_name

BASE_DIR = Path(__file__).resolve().parent


def main():
    text = "Merhaba! Şimdi birlikte öğrenelim. Görseli incele ve doğru seçeneği bul. Seçimini değiştirmek istersen tekrar düşün."
    report = {"engine": "drifting-tts" if voice_name() == "female" else "piper", "voice": voice_name(), "cloud_calls": 0}
    start = time.perf_counter()
    local_audio.start()
    report["warmup_seconds"] = round(time.perf_counter() - start, 3)
    try:
        with httpx.Client(trust_env=False, timeout=5) as client:
            denied = client.post(local_audio._endpoint + "/synthesize", json={"text": text})
            assert denied.status_code == 403
            headers = {"X-Local-TTS-Token": local_audio._token}
            health = client.get(local_audio._endpoint + "/health", headers=headers)
            assert health.json()["ready"]
            report["provider"] = health.json().get("provider")
            invalid = client.post(local_audio._endpoint + "/synthesize", json={"text": ""}, headers=headers)
            assert invalid.status_code == 400
        results = []
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {"AUDIO_PROVIDER": "piper"}), patch.object(audio_service, "CACHE_DIR", Path(folder)), patch.object(audio_service, "gemini_audio", side_effect=AssertionError("Cloud request")):
            for run in range(2):
                start = time.perf_counter()
                audio = audio_service.synthesize(text)
                elapsed = time.perf_counter() - start
                with wave.open(io.BytesIO(audio), "rb") as wav:
                    duration = wav.getnframes() / wav.getframerate()
                    assert duration > 1 and wav.getnchannels() == 1
                results.append(dict(run=run+1, cached=bool(run), elapsed_seconds=round(elapsed, 3), audio_seconds=round(duration, 2)))
            (BASE_DIR / "local_voice_sample.wav").write_bytes(audio)
        pygame.mixer.init(frequency=22050, size=-16, channels=1)
        sound = pygame.mixer.Sound(file=io.BytesIO(audio))
        channel = sound.play()
        assert channel is not None and channel.get_busy()
        channel.stop()
        report.update(runs=results, pygame_playback="started_and_stopped", api_checks="passed")
        (BASE_DIR / "local_audio_benchmark.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
    finally:
        pygame.mixer.quit()
        local_audio.shutdown()


if __name__ == "__main__":
    main()
