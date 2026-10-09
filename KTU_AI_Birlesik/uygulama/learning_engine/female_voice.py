"""Local Turkish female speaker using Vyvo/Drifting TTS ONNX models.

Inference follows kadirnar/drifting-tts/web/tts.js (MIT).
Weights: Vyvo/drifting-tts-tr, CC-BY-4.0; named female speaker 323.
"""
import io
import json
import wave
from pathlib import Path

import numpy as np
import onnxruntime as ort

from learning_engine.vendor.drifting_text import normalize, split_sentences, text_to_ids


class FemaleVoice:
    def __init__(self, folder):
        folder = Path(folder)
        self.config = json.loads((folder / "config.json").read_text(encoding="utf-8"))
        self.speaker = self.config["voices"]["female"]
        options = ort.SessionOptions()
        options.intra_op_num_threads = 4
        options.enable_mem_pattern = False
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        available = ort.get_available_providers()
        self.provider = "DmlExecutionProvider" if "DmlExecutionProvider" in available else "CPUExecutionProvider"
        self.encoder = ort.InferenceSession(str(folder / "text_encoder.onnx"), sess_options=options,
                                           providers=["CPUExecutionProvider"])
        self.generator = ort.InferenceSession(str(folder / "generator.onnx"), sess_options=options,
                                             providers=[self.provider, "CPUExecutionProvider"])
        self.vocoder = ort.InferenceSession(str(folder / "vocoder.onnx"), sess_options=options,
                                           providers=[self.provider, "CPUExecutionProvider"])

    def sentence(self, text, rng):
        cfg = self.config
        speaker = np.array([self.speaker], dtype=np.int64)
        ids = np.array([text_to_ids(text, normalized=True)], dtype=np.int64)
        encoded = dict(zip([o.name for o in self.encoder.get_outputs()],
                           self.encoder.run(None, {"text": ids, "speaker": speaker})))
        scale = np.float32(cfg["duration_scales"][str(self.speaker)] * 1.04)
        durations = np.maximum(0, np.ceil(np.exp(encoded["logw"].reshape(-1)).astype(np.float32) * scale)).astype(np.int64)
        cond = np.repeat(encoded["cond"], durations, axis=2)
        frames = cond.shape[2]
        if not 0 < frames <= 2400:
            raise ValueError("Kadın ses modelinde geçersiz süre.")
        noise = (rng.standard_normal((1, cfg["n_mels"], frames)) * 0.3).astype(np.float32)
        labels = rng.integers(0, cfg["noise_classes"], (1, cfg["noise_coords"]), dtype=np.int64)
        mel = self.generator.run(None, {"z": noise, "cond": cond, "speaker": speaker,
                                       "cfg_scale": np.array([2.0], dtype=np.float32),
                                       "noise_labels": labels})[0]
        # Bound vocoder windows so a long sentence does not exhaust 4 GB VRAM.
        parts = []
        hop = cfg["hop_length"]
        for start in range(0, frames, 160):
            left, right = max(0, start-32), min(frames, start+160+32)
            audio = self.vocoder.run(None, {"mel": np.ascontiguousarray(mel[:, :, left:right])})[0].reshape(-1)
            offset = (start-left)*hop
            parts.append(audio[offset:offset+min(160, frames-start)*hop])
        return np.concatenate(parts)

    def synthesize_wav(self, text):
        parts = []
        rng = np.random.default_rng(0)
        for sentence in split_sentences(normalize(text), max_chars=140):
            if parts:
                parts.append(np.zeros(3600, dtype=np.float32))
            parts.append(self.sentence(sentence, rng))
        if not parts:
            raise ValueError("Seslendirilecek metin bulunamadı.")
        audio = np.concatenate(parts)
        if not np.isfinite(audio).all():
            raise ValueError("Kadın ses modelinden geçersiz örnekler alındı.")
        pcm = (np.clip(audio, -1, 1) * 30000).astype("<i2").tobytes()
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(self.config["sample_rate"])
            wav.writeframes(pcm)
        return buffer.getvalue()
