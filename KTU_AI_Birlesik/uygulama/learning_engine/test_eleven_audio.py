import io
import os
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

import httpx
from learning_engine import audio_service
from learning_engine import eleven_audio
class ElevenAudioTest(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {
            "AUDIO_PROVIDER": "elevenlabs", "ELEVENLABS_API_KEY": "test-key",
            "ELEVENLABS_VOICE": "cicek", "ELEVENLABS_CICEK_VOICE_ID": "testCicek",
            "ELEVENLABS_RYAN_VOICE_ID": "testRyan"})
        self.env.start()
        self.addCleanup(self.env.stop)
        eleven_audio.BLOCKED_UNTIL = 0.0
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.cache = patch.object(audio_service, "CACHE_DIR", Path(self.folder.name))
        self.cache.start()
        self.addCleanup(self.cache.stop)

    def test_wav_cache_unicode_and_separate_voices(self):
        response = httpx.Response(200, content=b"\0\0" * 200,
                                  headers={"content-type": "audio/pcm"})
        with patch("learning_engine.eleven_audio.httpx.Client") as client:
            post = client.return_value.__enter__.return_value.post
            post.return_value = response
            audio = audio_service.synthesize("Çiçek, birlikte öğrenelim.")
            with wave.open(io.BytesIO(audio)) as wav:
                self.assertEqual(wav.getframerate(), 24000)
                self.assertEqual(wav.getnframes(), 200)
            self.assertIn("Çiçek", post.call_args.kwargs["json"]["text"])
            self.assertEqual(audio_service.synthesize("Çiçek, birlikte öğrenelim."), audio)
            self.assertEqual(post.call_count, 1)
            os.environ["ELEVENLABS_VOICE"] = "ryan"
            audio_service.synthesize("Çiçek, birlikte öğrenelim.")
            self.assertEqual(post.call_count, 2)
            self.assertTrue(post.call_args.args[0].endswith("testRyan"))

    def test_429_does_not_retry_or_switch_voice(self):
        with patch("learning_engine.eleven_audio.httpx.Client") as client:
            post = client.return_value.__enter__.return_value.post
            post.return_value = httpx.Response(429)
            for _ in range(2):
                with self.assertRaises(audio_service.AudioUnavailable):
                    audio_service.synthesize("Merhaba")
            self.assertEqual(post.call_count, 1)

    def test_missing_configuration_never_calls_network(self):
        os.environ["ELEVENLABS_CICEK_VOICE_ID"] = ""
        with patch("learning_engine.eleven_audio.httpx.Client", side_effect=AssertionError("Network")):
            with self.assertRaises(audio_service.AudioUnavailable):
                audio_service.synthesize("Merhaba")

    def test_connection_failure_is_readable(self):
        with patch("learning_engine.eleven_audio.httpx.Client") as client:
            client.return_value.__enter__.return_value.post.side_effect = httpx.ConnectError("offline")
            with self.assertRaisesRegex(audio_service.AudioUnavailable, "bağlantısı"):
                audio_service.synthesize("Merhaba")

    def test_jessica_uses_selected_voice(self):
        os.environ["ELEVENLABS_VOICE"] = "jessica"
        os.environ["ELEVENLABS_JESSICA_VOICE_ID"] = "cgSgspJ2msm6clMCkdW9"
        with patch("learning_engine.eleven_audio.httpx.Client") as client:
            post = client.return_value.__enter__.return_value.post
            post.return_value = httpx.Response(200, content=b"\0\0" * 100)
            audio_service.synthesize("Merhaba")
            self.assertTrue(post.call_args.args[0].endswith("cgSgspJ2msm6clMCkdW9"))
