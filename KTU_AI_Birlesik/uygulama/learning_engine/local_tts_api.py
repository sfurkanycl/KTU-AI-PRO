"""Local-only Piper API. Run with .venv-tts/Scripts/python.exe.

The application launches it on a free loopback port and stops it on exit.
"""
import argparse
import io
import json
import os
import secrets
import wave
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from learning_engine.voice_config import model_filename, voice_name, LENGTH_SCALE, NOISE_SCALE, NOISE_W_SCALE

BASE_DIR = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--model", default=str(BASE_DIR / "local_models" / model_filename()))
    args = parser.parse_args()
    if voice_name() == "female":
        from learning_engine.female_voice import FemaleVoice
        voice = FemaleVoice(args.model)
        synthesize = voice.synthesize_wav
        engine = "drifting-tts"
        provider = voice.provider
    else:
        from piper import PiperVoice, SynthesisConfig
        from piper.phonemize_espeak import ESPEAK_DATA_DIR
        espeak_dir = ESPEAK_DATA_DIR
        if os.name == "nt" and not str(espeak_dir).isascii():
            import ctypes
            buffer = ctypes.create_unicode_buffer(32768)
            length = ctypes.windll.kernel32.GetShortPathNameW(str(espeak_dir.parent), buffer, len(buffer))
            if not length:
                raise RuntimeError("Windows kısa veri yolu alınamadı.")
            espeak_dir = Path(buffer.value) / espeak_dir.name
        voice = PiperVoice.load(args.model, espeak_data_dir=espeak_dir)
        config = SynthesisConfig(length_scale=LENGTH_SCALE, noise_scale=NOISE_SCALE, noise_w_scale=NOISE_W_SCALE)

        def synthesize(text):
            buffer = io.BytesIO()
            with wave.open(buffer, "wb") as wav:
                voice.synthesize_wav(text, wav, syn_config=config)
            return buffer.getvalue()

        engine = "piper"
        provider = "CPUExecutionProvider"
    token = os.environ.get("LOCAL_TTS_TOKEN") or secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, status, body, mime="application/json"):
            self.send_response(status)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def authorized(self):
            return secrets.compare_digest(self.headers.get("X-Local-TTS-Token", ""), token)

        def do_GET(self):
            if not self.authorized():
                self.reply(403, b'{"error":"forbidden"}')
            elif self.path == "/health":
                self.reply(200, json.dumps(dict(engine=engine, language="tr_TR", ready=True,
                                               voice=voice_name(), provider=provider)).encode())
            else:
                self.reply(404, b'{}')

        def do_POST(self):
            if not self.authorized():
                self.reply(403, b'{"error":"forbidden"}')
                return
            if self.path != "/synthesize":
                self.reply(404, b'{}')
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 16000:
                    raise ValueError("Invalid body size")
                data = json.loads(self.rfile.read(length))
                text = data.get("text") if isinstance(data, dict) else None
                if not isinstance(text, str) or not text.strip() or len(text) > 2000:
                    raise ValueError("Invalid text")
            except (ValueError, UnicodeError):
                self.reply(400, b'{"error":"invalid text"}')
                return
            try:
                self.reply(200, synthesize(text), "audio/wav")
            except Exception:
                self.reply(500, b'{"error":"local synthesis failed"}')

    server = HTTPServer(("127.0.0.1", args.port), Handler)
    print(json.dumps({"port": server.server_port, "token": token}), flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
