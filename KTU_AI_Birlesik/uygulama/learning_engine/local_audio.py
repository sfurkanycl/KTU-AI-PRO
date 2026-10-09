"""Start one isolated local speech process and reuse its loaded model."""
import atexit
import json
import os
import queue
import subprocess
import threading
from pathlib import Path

import httpx
from learning_engine.voice_config import model_filename, voice_name

BASE_DIR = Path(__file__).resolve().parent
PROCESS_LOCK = threading.Lock()
_process = None
_endpoint = None
_token = None


def shutdown():
    global _process, _endpoint, _token
    if _process is not None and _process.poll() is None:
        _process.terminate()
        try:
            _process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            _process.kill()
            _process.wait(timeout=3)
    if _process is not None and _process.stdout:
        _process.stdout.close()
    _process = _endpoint = _token = None


def start():
    global _process, _endpoint, _token
    with PROCESS_LOCK:
        if _process is not None and _process.poll() is None and _endpoint:
            return
        shutdown()
        environment = ".venv-female" if voice_name() == "female" else ".venv-tts"
        python = BASE_DIR / environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        model = BASE_DIR / "local_models" / model_filename()
        setup = BASE_DIR / 'setup_local_audio.ps1'
        if not python.exists():
            raise RuntimeError(f'Yerel sesin Python ortamı eksik: {environment}. Kurulum: powershell -ExecutionPolicy Bypass -File "{setup}"')
        if not model.exists():
            raise RuntimeError(f'Yerel ses modeli eksik: {model.name}. Kurulum: powershell -ExecutionPolicy Bypass -File "{setup}"')
        with (BASE_DIR / "local_tts.log").open("a", encoding="utf-8") as log:
            _process = subprocess.Popen(
                [str(python), "-u", "-m", "learning_engine.local_tts_api", "--model", str(model)],
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=log,
                text=True, encoding="utf-8", cwd=str(BASE_DIR.parent),
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
        ready = queue.Queue()
        process = _process

        def read_ready():
            try:
                for line in process.stdout:
                    data = json.loads(line)
                    if "port" in data and "token" in data:
                        ready.put(data)
                        return
            except (ValueError, OSError):
                pass
            ready.put(None)

        threading.Thread(target=read_ready, daemon=True).start()
        try:
            data = ready.get(timeout=60)
            if data is None:
                raise RuntimeError("Yerel ses motoru açılamadı. local_tts.log dosyasını kontrol et.")
            _endpoint = f"http://127.0.0.1:{int(data['port'])}"
            _token = data["token"]
        except Exception:
            shutdown()
            raise


def local_audio(text):
    start()
    try:
        with httpx.Client(trust_env=False, timeout=30) as client:
            response = client.post(_endpoint + "/synthesize", json={"text": text},
                                   headers={"X-Local-TTS-Token": _token})
            response.raise_for_status()
            audio = response.content
    except httpx.HTTPError as error:
        raise RuntimeError("Yerel ses motoru yanıt veremedi. Tekrar dinle ile yeniden dene.") from error
    if audio[:4] != b"RIFF" or audio[8:12] != b"WAVE":
        raise RuntimeError("Yerel ses motoru geçersiz WAV döndürdü.")
    return audio


atexit.register(shutdown)
