"""No real network, native hooks, user database, or modal prompts in these tests."""
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['LESSON_PROVIDER'] = 'local'
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Import-time native loading is blocked before the preserved guard is imported.
with patch('ctypes.CDLL', side_effect=OSError('Disabled during tests')):
    from data import database as db
    from data import education_database as school
    import questions
    from learning import LearningSession
    from student_panel import BreakWindow
    from unified_parent import UnifiedParent
    from PyQt6.QtWidgets import QApplication
    from pin_security import PinAttemptLimiter


class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        from ui_fonts import configure_fonts
        configure_fonts(cls.app)

    def setUp(self):
        Path('test_artifacts').mkdir(exist_ok=True)
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        for module, name in ((db, 'session.db'), (school, 'school.db')):
            p = patch.object(module, 'DB_PATH', Path(self.folder.name) / name)
            p.start()
            self.addCleanup(p.stop)
            module.init_db()
        db.save_student('Deneme', 4, 'kiz')
        db.set_skills(['matter_states'])
        self.windows = []
        self.addCleanup(self.close_windows)

    def close_windows(self):
        for w in self.windows:
            if hasattr(w, '_allow_close'):
                w._allow_close = True
                w._timer.stop()
            w.close()
            w.deleteLater()
        self.app.processEvents()
        from PyQt6.QtCore import QCoreApplication,QEvent
        QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)

    @classmethod
    def tearDownClass(cls):
        from integrated_ui import shutdown_voice_requests
        from audio_narrator import shutdown_narration
        shutdown_voice_requests()
        shutdown_narration()
        cls.app.processEvents()

    def test_all_primary_grades_have_science_and_social(self):
        for grade in range(1, 5):
            self.assertTrue({'matter_states', 'living_needs', 'traffic', 'directions'} <= dict(questions.skills_for_grade(grade)).keys())

    def test_reviewed_questions_preserve_answer(self):
        bank = questions.reviewed_bank('matter_states', 4)
        self.assertGreater(len(bank), 0)
        for q in bank:
            self.assertTrue(0 <= q['answer'] < len(q['choices']))
            self.assertTrue(q['verified'])

    def test_all_homework_questions_preserved_with_ambiguous_item_flagged(self):
        import json
        original = json.loads(Path('sorular.json').read_text(encoding='utf-8'))
        combined = [q for skill in questions.HOMEWORK_SKILLS for q in questions.homework_bank(skill)]
        self.assertEqual(len(combined), len(original))
        self.assertEqual({q['text'] for q in combined}, {q['soru'] for q in original})
        self.assertEqual(sum(not q['verified'] for q in combined), 1)

    def test_all_skills_support_repeated_wrong_and_hint_answers(self):
        for skill in questions.SKILLS:
            sid = db.start_session()
            session = LearningSession(sid, [skill], 1, 18)
            for _ in range(3):
                q = session.next_question()
                result = session.answer((q['answer']+1) % len(q['choices']), 5, False)
                self.assertFalse(result['correct'])
            q = session.next_question()
            result = session.answer(q['answer'], 5, True)
            self.assertTrue(result['correct'])
            db.finish_session(sid, 'test', 0)

    def test_wrong_answer_same_concept_and_report(self):
        sid = db.start_session()
        session = LearningSession(sid, ['matter_states'], 1, 18)
        q = session.next_question()
        expected = questions.concept_of(q)
        session.answer((q['answer']+1) % len(q['choices']), 5, False)
        next_q = session.next_question()
        self.assertEqual(questions.concept_of(next_q), expected)
        db.finish_session(sid, 'parent_exit', 0)
        self.assertTrue(db.report_rows(sid))

    def test_pin_limiter_uses_hashed_database_pin(self):
        db.set_pin('7351')
        clock = [0]
        limiter = PinAttemptLimiter(max_attempts=2, lock_seconds=30, clock=lambda: clock[0])
        self.assertFalse(limiter.verify('1234')[0])
        self.assertFalse(limiter.verify('0000')[0])
        self.assertFalse(limiter.verify('7351')[0])
        clock[0] = 31
        self.assertTrue(limiter.verify('7351')[0])

    def test_school_database_complete_assignment_flow(self):
        parent = school.create_user('veli', 'Veli', 'parent')
        teacher = school.create_user('ogretmen', 'Öğretmen', 'teacher')
        child = school.add_student('Çocuk', 4, parent)
        classroom = school.create_class('4A', 4, teacher)
        school.enroll_student(classroom, child)
        topic = school.add_topic('Canlılar', 'Fen', 4, teacher, class_id=classroom)
        assignment = school.create_assignment('Canlılar ödevi', topic, teacher, class_id=classroom)
        q = school.add_question(assignment, 'Bitkiye ne gerekir?', 'Su', '["Su", "Oyuncak"]', 'Bitkilerin suya ihtiyacı vardır.')
        school.record_result(child, assignment, q, 'Su', True)
        self.assertEqual(school.get_student_report(child)[0]['correct_count'], 1)
        self.assertNotEqual(db.DB_PATH, school.DB_PATH)

    def test_unified_window_and_assets(self):
        window = UnifiedParent()
        self.windows.append(window)
        window.show()
        self.app.processEvents()
        labels = [window.tabs.tabText(i) for i in range(window.tabs.count())]
        self.assertIn('Sınıflar ve Ödevler', labels)
        self.assertIn('Renkli Giriş', labels)
        import integrated_ui
        for name in ('kızögrenci.png', 'erkekögrenci.png', 'veli.png', 'ogretmen.png'):
            self.assertTrue(Path(integrated_ui._asset_path(name)).exists())
        Path('test_artifacts').mkdir(exist_ok=True)
        self.assertTrue(window.grab().save('test_artifacts/parent.png'))

    def test_animated_quiz_logs_real_answer_and_explanation(self):
        sid = db.start_session()
        session = LearningSession(sid, ['matter_states'], 1, 18)
        window = BreakWindow(session, 60)
        self.windows.append(window)
        window.resize(1100, 850)
        window.show()
        from PyQt6.QtTest import QTest
        QTest.qWait(500)
        self.assertEqual(window.question.text(), session.current['text'])
        with patch('integrated_ui.start_narration'):
            window._explain()
        self.assertTrue(window._hint_used)
        window._explanation_dialog.close()
        window._on_choice(session.current['answer'])
        self.assertEqual(session.attempts, 1)
        self.assertTrue(db.report_rows(sid))
        self.assertTrue(window.grab().save('test_artifacts/quiz.png'))

    def test_writing_and_all_math_illustrations(self):
        from learning_engine.visual_help import make_lesson
        from quiz_tools import LessonScene
        sid = db.start_session()
        session = LearningSession(sid, ['matter_states'], 1, 18)
        window = BreakWindow(session, 60)
        self.windows.append(window)
        window.resize(1200, 900)
        window.show()
        window._open_writing()
        window.notes.setPlainText('İşlemimi buraya yazıyorum.')
        self.assertIn('İşlemimi', window.notes.toPlainText())
        self.assertGreaterEqual(window.pad.minimumHeight(), 180)
        for prompt in ('27 + 15 işleminin sonucu kaçtır?', '1/3 ile 1/5 karşılaştır.'):
            session.current = dict(text=prompt, choices=['1', '2', '3', '4'],
                                   answer=0, hint='Birlikte düşün.', explanation='Adımları izle.')
            with patch('integrated_ui.start_narration') as speak:
                window._explain()
                self.assertTrue(speak.called)
                self.app.processEvents()
                scene = window._explanation_dialog.findChild(LessonScene)
                self.assertGreater(len(scene.scene().items()), 0)
                lesson = make_lesson(dict(prompt=prompt))
                for step in range(len(lesson['steps'])):
                    scene.show_step(lesson, step)
                    self.assertGreater(len(scene.scene().items()), 0)
                window._explanation_dialog.grab().save('test_artifacts/lesson.png')
                window._explanation_dialog.close()
        window._load_question()
        self.assertEqual(window.notes.toPlainText(), '')
        from PyQt6.QtTest import QTest
        QTest.qWait(650)
        window.grab().save('test_artifacts/quiz_readable.png')
        window._writing_dialog.grab().save('test_artifacts/writing.png')

    def test_ink_eight_becomes_typeset_number(self):
        import math
        from PyQt6.QtCore import QPointF
        from quiz_tools import InkRecognition, WritingPad
        stroke = [QPointF(150 + 45 * math.sin(t), 140 + 80 * math.sin(t) * math.cos(t))
                  for t in (i * 2 * math.pi / 160 for i in range(161))]
        worker = InkRecognition([stroke])
        values, errors = [], []
        worker.recognized.connect(values.append)
        worker.failed.connect(errors.append)
        worker.run()
        self.assertEqual(errors, [])
        self.assertEqual(values, ['8'])
        pad = WritingPad()
        pad.strokes = [stroke]
        pad.commit_text(values[0])
        pad.resize(600, 260)
        pad.grab().save('test_artifacts/typeset_eight.png')
        pad.undo()
        self.assertEqual(pad.typeset_text, '')
        self.assertEqual(pad.strokes, [stroke])

    def test_selected_subjects_rotate_and_unsaved_selection_is_used(self):
        skills = ['m3_toplama', 'matter_states', 'traffic', 'homework_turkce']
        session = LearningSession(db.start_session(), skills, 4, 18)
        received = []
        for _ in range(8):
            q = session.next_question()
            received.append(q['skill'])
            session.answer((q['answer'] + 1) % len(q['choices']), 8)
        self.assertEqual(received, skills * 2)
        window = UnifiedParent()
        self.windows.append(window)
        from parent_panel import ParentPanel
        with patch.object(window, '_checked_skills', return_value=skills), \
             patch.object(ParentPanel, '_start_session') as start:
            window._start_session()
            start.assert_called_once()
        self.assertEqual(set(db.get_skills()), set(skills))

    def test_automatic_ink_preserves_previous_numbers(self):
        import math
        from PyQt6.QtCore import QPointF
        from PyQt6.QtTest import QTest
        from PyQt6.QtWidgets import QInputDialog
        session = LearningSession(db.start_session(), ['matter_states'], 1, 18)
        window = BreakWindow(session, 60)
        self.windows.append(window)
        window._open_writing()
        with patch.object(QInputDialog, 'getText', side_effect=AssertionError('Automatic ink must not prompt')):
            for offset in (0, 220):
                stroke = [QPointF(70 + offset + 35 * math.sin(t), 100 + 65 * math.sin(t) * math.cos(t))
                          for t in (i * 2 * math.pi / 160 for i in range(161))]
                expected_count = len(window.pad.committed) + 1
                window.pad.strokes = [stroke]
                window.pad.strokes_changed.emit()
                for _ in range(60):
                    QTest.qWait(100)
                    if len(window.pad.committed) == expected_count:
                        break
                self.assertEqual(len(window.pad.committed), expected_count)
        self.assertEqual(window.pad.typeset_text, '8 8')
        self.assertEqual(window.pad.strokes, [])
        window.pad.grab().save('test_artifacts/continuous_writing.png')
        window.pad.undo()
        self.assertEqual(len(window.pad.committed), 1)
        self.assertTrue(window.pad.strokes)

    def test_correct_answer_advances_and_wrong_answer_waits(self):
        from PyQt6.QtTest import QTest
        session = LearningSession(db.start_session(), ['matter_states', 'traffic'], 2, 18)
        window = BreakWindow(session, 60)
        self.windows.append(window)
        window.show()
        first = session.current['qkey']
        window._on_choice(session.current['answer'])
        self.assertTrue(window._advance_timer.isActive())
        QTest.qWait(1400)
        self.assertNotEqual(session.current['qkey'], first)
        self.assertFalse(window._answered)
        current = session.current['qkey']
        window._on_choice((session.current['answer']+1) % len(session.current['choices']))
        self.assertFalse(window._advance_timer.isActive())
        QTest.qWait(1400)
        self.assertEqual(session.current['qkey'], current)

    def test_all_school_visuals_are_rendered(self):
        from quiz_tools import LessonScene
        from learning_engine.school_content import SCENES
        view = LessonScene()
        for key in SCENES:
            view.show_visual({'scene_id': key})
            self.assertGreater(len(view.scene().items()), 2, key)
        view.show_visual({})
        self.assertEqual(len(view.scene().items()), 0)


if __name__ == '__main__':
    unittest.main()
