import io
import os
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

from learning_engine import audio_service
from learning_engine import lesson_service
class LocalAudioTest(unittest.TestCase):
    def test_local_speech_never_calls_gemini_and_caches(self):
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(22050)
            wav.writeframes(b"\0\0" * 100)
        audio = buffer.getvalue()
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {"AUDIO_PROVIDER": "piper"}), patch.object(audio_service, "CACHE_DIR", Path(folder)), patch("learning_engine.local_audio.local_audio", return_value=audio) as local, patch.object(audio_service, "gemini_audio", side_effect=AssertionError("Cloud request")), patch.object(audio_service.time, "sleep", side_effect=AssertionError("Quota delay")):
            self.assertEqual(audio_service.synthesize("Merhaba"), audio)
            self.assertEqual(audio_service.synthesize("Merhaba"), audio)
            self.assertEqual(local.call_count, 1)

    def test_local_lesson_uses_stored_explanation_without_api(self):
        question = dict(prompt="Bitki neye ihtiyac duyar?", hint="Topragi dusun.",
                        explanation="Bitkiler suya ihtiyaç duyar.", example="Saksıyı sulamak.")
        with patch.dict(os.environ, {"LESSON_PROVIDER": "local"}), patch.object(lesson_service.genai, "Client", side_effect=AssertionError("Cloud request")):
            result = lesson_service.prepare_question(question)
        self.assertEqual(result["_lesson"]["steps"][2][1], question["explanation"])

    def test_gemini_is_still_available_by_explicit_setting(self):
        with patch.dict(os.environ, {"AUDIO_PROVIDER": "gemini"}), patch.object(audio_service, "synthesize_gemini", return_value=b"gemini") as cloud:
            self.assertEqual(audio_service.synthesize("Merhaba"), b"gemini")
            cloud.assert_called_once()


if __name__ == "__main__":
    unittest.main()
