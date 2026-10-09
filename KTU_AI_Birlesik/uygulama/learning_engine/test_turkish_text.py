import unittest

from learning_engine.learning_core import normalize_payload, LearningEngine
from learning_engine.turkish_text import restore_text
from learning_engine.school_content import SCENES
from learning_engine.voice_config import cache_identity
from unittest.mock import patch


class TurkishTextTest(unittest.TestCase):
    def test_screenshot_spelling(self):
        self.assertEqual(restore_text("Balonun icindeki hava"), "Balonun içindeki hava")
        self.assertEqual(restore_text("Balonun siskin durmasini saglayan hava"),
                         "Balonun şişkin durmasını sağlayan hava")
        self.assertEqual(restore_text("Ipucu goster"), "İpucu göster")
        self.assertEqual(restore_text("degistir"), "değiştir")

    def test_unicode_preserved_and_codes_unchanged(self):
        payload = {"signature": "scene:water:0", "concept": "sivi",
                   "prompt": "İçindeki sıvıyı düşün. Şimdi doğru seçeneği bul.",
                   "options": ["Kati", "Sivi", "Gaz"], "correct_index": 1}
        result = normalize_payload(payload)
        self.assertEqual(result["prompt"], payload["prompt"])
        self.assertEqual(result["signature"], payload["signature"])
        self.assertEqual(result["concept"], "sivi")
        self.assertEqual(result["options"][result["correct_index"]], "Sıvı")

    def test_old_pending_question_is_corrected_without_changing_answer(self):
        question = LearningEngine._public_question("test", dict(prompt="Balonun icindeki hava hangi haldedir?",
                                                                options=["Sivi", "Kati", "Gaz"]))
        self.assertIn("içindeki", question["prompt"])
        self.assertEqual(question["options"], ["Sıvı", "Katı", "Gaz"])
        self.assertEqual(SCENES["air"]["label"], "Balonun içindeki hava")

    def test_voice_change_does_not_reuse_old_audio(self):
        with patch.dict("os.environ", {"LOCAL_TTS_VOICE": "eren"}):
            new = cache_identity()
        with patch.dict("os.environ", {"LOCAL_TTS_VOICE": "dfki"}):
            old = cache_identity()
        self.assertNotEqual(new, old)


if __name__ == "__main__":
    unittest.main()
