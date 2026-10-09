"""Single source of truth for the local voice and its cache identity."""
import os


def voice_name():
    name = os.getenv("LOCAL_TTS_VOICE", "female").strip().lower()
    if name not in ("female", "eren", "dfki"):
        raise ValueError("LOCAL_TTS_VOICE için female, eren veya dfki seç.")
    return name


def model_filename():
    return {"female": "drifting-female", "eren": "tr_TR-eren.onnx", "dfki": "tr_TR-dfki-medium.onnx"}[voice_name()]


LENGTH_SCALE = 1.12
NOISE_SCALE = 0.4
NOISE_W_SCALE = 0.3


def cache_identity():
    if voice_name() == "female":
        return "drifting-v3.1-female-323-v1-length1.04-temp0.3-cfg2"
    return f"piper-{voice_name()}-v2-{LENGTH_SCALE}-{NOISE_SCALE}-{NOISE_W_SCALE}"
