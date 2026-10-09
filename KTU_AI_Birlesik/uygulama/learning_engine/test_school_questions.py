import json
import unittest
from concurrent.futures import Future
from unittest.mock import patch

from learning_engine.learning_core import LearningEngine, LocalQuestionProvider
from learning_engine.gemini_questions import CachedGeminiProvider, SceneQuestion, build_question
from learning_engine.school_content import SCENES, TOPICS, draw_scene


class SchoolQuestionsTest(unittest.TestCase):
    def test_all_topics_all_primary_grades(self):
        for grade in range(1, 5):
            for skill, (subject, _) in TOPICS.items():
                engine = LearningEngine(":memory:", LocalQuestionProvider())
                try:
                    student = engine.create_student("Test", grade)
                    session = engine.start_session(student, subject, skill, target=6, max_attempts=18)
                    signatures = set()
                    for attempt in range(18):
                        question = engine.next_question(session)
                        self.assertNotIn("correct_index", question)
                        self.assertEqual(question, engine.next_question(session))
                        row = engine.db.execute("SELECT payload FROM learning_questions WHERE id=?", (question["id"],)).fetchone()
                        payload = json.loads(row["payload"])
                        self.assertNotIn(payload["signature"], signatures)
                        signatures.add(payload["signature"])
                        if subject != "matematik":
                            self.assertIn(question["visual"]["scene_id"], SCENES)
                        if attempt:
                            self.assertTrue(question["practice"])
                            if subject != "matematik":
                                remaining = any(
                                    s["skill"] == skill and s["concept"] == previous["concept"]
                                    and any(f"scene:{key}:{v}" not in (signatures - {payload["signature"]}) for v in range(8))
                                    for key, s in SCENES.items())
                                if remaining:
                                    self.assertEqual(payload["concept"], previous["concept"])
                        previous = payload
                        wrong = (payload["correct_index"] + 1) % len(payload["options"])
                        result = engine.submit_answer(session, question["id"], wrong)
                        self.assertFalse(result["correct"])
                    self.assertEqual(result["status"], "needs_parent")
                finally:
                    engine.close()

    def test_cached_similar_prefers_reviewed_concept(self):
        provider = CachedGeminiProvider()
        payload = provider.local.generate(4, "fen", "matter_states", set())
        provider.packs = {"4:fen:matter_states": [payload]}
        chosen = provider.generate_similar(4, "fen", "matter_states", set(), payload)
        self.assertEqual(chosen["signature"], payload["signature"])

    def test_generated_scene_validation(self):
        item = SceneQuestion(scene_id="water", prompt="Bardaktaki su hangi haldedir?",
                             options=["Kati", "Sivi", "Gaz"], correct_index=1,
                             hint="Akip akmadigini dusun.", explanation="Su sividir ve kabinin seklini alir.",
                             example="Sut de sivi bir maddedir.")
        payload = build_question(item, 3, "matter_states")
        self.assertEqual(payload["concept"], "sivi")
        self.assertEqual(payload["options"][payload["correct_index"]], "Sıvı")
        with self.assertRaises(ValueError):
            build_question(item, 3, "traffic")

    def test_every_scene_draws_and_fits_canvas(self):
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        try:
            canvas = tk.Canvas(root, width=740, height=170)
            for key in SCENES:
                canvas.delete("all")
                draw_scene(canvas, {"scene_id": key})
                self.assertGreaterEqual(len(canvas.find_all()), 3, key)
                x1, y1, x2, y2 = canvas.bbox("all")
                self.assertLessEqual(x2, 742, key)
                self.assertLessEqual(y2, 177, key)
        finally:
            root.destroy()

    def test_correct_and_assisted_progress(self):
        engine = LearningEngine(":memory:")
        try:
            student = engine.create_student("Test", 4)
            session = engine.start_session(student, "fen", "matter_states", target=1)
            question = engine.next_question(session)
            engine.request_hint(session, question["id"])
            def correct(q):
                return json.loads(engine.db.execute("SELECT payload FROM learning_questions WHERE id=?", (q["id"],)).fetchone()["payload"])["correct_index"]
            result = engine.submit_answer(session, question["id"], correct(question))
            self.assertTrue(result["correct"])
            self.assertEqual(result["streak"], 0)
            question = engine.next_question(session)
            self.assertTrue(question["practice"])
            result = engine.submit_answer(session, question["id"], correct(question))
            self.assertEqual(result["status"], "completed")
        finally:
            engine.close()

    def test_ui_topics_and_help_window(self):
        import tkinter as tk
        from learning_engine import demo_ui
        from learning_engine import visual_help
        root = tk.Tk()
        root.withdraw()
        real_engine = LearningEngine
        try:
            with patch.object(demo_ui, "synthesize"), patch.object(demo_ui, "warmup_audio"), patch.object(demo_ui, "LearningEngine", side_effect=lambda *args, **kwargs: real_engine(":memory:", provider=kwargs.get("provider"))), patch.object(demo_ui.messagebox, "showerror", side_effect=AssertionError):
                app = demo_ui.LearningDemo(root)
                for skill in TOPICS:
                    app.start(skill)
                    root.update_idletasks()
                    self.assertTrue(app.question["visual"])
                    self.assertGreaterEqual(len(app.option_buttons), 3)
                    app.answer(0)
                pending = Future()
                with patch.object(visual_help.AUDIO_POOL, "submit", return_value=pending):
                    window = visual_help.VisualHelp(app.root, {"_lesson": {"kind": "general", "steps": [("Resmi incele", "Bu bir deneme anlatimidir.")]}})
                    window.close()
                app.engine.close()
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
