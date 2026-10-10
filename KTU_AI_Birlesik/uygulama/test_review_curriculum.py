"""Voluntary exit, wrong-answer isolation, and applied primary curricula."""
import json,os,unittest
from unittest.mock import patch
import test_roles as fixtures
from role_quiz import StudentQuiz,AccountSession,practice_questions
from curriculum_practice import topics,offline_bank,generate_similar
from curriculum import catalogue
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QPushButton,QInputDialog
from PyQt6.QtCore import QEvent
store=fixtures.store

class ReviewTests(unittest.TestCase):
    setUpClass=classmethod(fixtures.RoleTests.setUpClass.__func__)
    setUp=fixtures.RoleTests.setUp
    close_windows=fixtures.RoleTests.close_windows

    def test_free_exit_needs_no_parent_and_starts_no_guard(self):
        from keyboard_guard import guard
        with patch.object(guard,'start') as start,patch.object(QInputDialog,'getText') as password:
            quiz=StudentQuiz(self.student,practice_questions(self.student,2,['homework_turkce']))
            self.windows.append(quiz)
            start.assert_not_called()
            self.assertIn('Çalışmadan çık',[b.text() for b in quiz.findChildren(QPushButton)])
            quiz.keyPressEvent(QKeyEvent(QEvent.Type.KeyPress,Qt.Key.Key_Escape,Qt.KeyboardModifier.NoModifier))
            self.assertTrue(quiz._allow_close);password.assert_not_called()

    def test_parent_assignment_keeps_exit_guard(self):
        aid=store.create_task(self.parent,'Görev','traffic',2,student_id=self.child)
        from keyboard_guard import guard
        with patch.object(guard,'start') as start:
            quiz=StudentQuiz(self.student,store.task_questions(self.student,aid),aid);self.windows.append(quiz)
            start.assert_called_once()
            quiz.keyPressEvent(QKeyEvent(QEvent.Type.KeyPress,Qt.Key.Key_Escape,Qt.KeyboardModifier.NoModifier))
            self.assertFalse(quiz._allow_close)

    def test_wrong_practice_is_private_and_correct_retry_removes_it(self):
        q=practice_questions(self.student,1,['homework_turkce'])[0]
        store.save_answer(self.student,q,(q['answer']+1)%4,False)
        wrong=store.wrong_questions(self.student)
        self.assertEqual(len(wrong),1);self.assertEqual(wrong[0]['choices'],q['choices'])
        self.assertEqual(store.wrong_questions(self.student2),[])
        store.save_answer(self.student,wrong[0],wrong[0]['answer'],False)
        self.assertEqual(store.wrong_questions(self.student),[])

    def test_wrong_task_can_be_retried_without_overwriting_task_result(self):
        aid=store.create_task(self.parent,'Görev','traffic',2,student_id=self.child)
        q=store.task_questions(self.student,aid)[0]
        store.save_answer(self.student,q,(q['answer']+1)%len(q['choices']),False,aid)
        wrong=store.wrong_questions(self.student)
        self.assertEqual(len(wrong),1)
        store.save_answer(self.student,wrong[0],wrong[0]['answer'],False)
        self.assertEqual(store.wrong_questions(self.student),[])
        with fixtures.school.get_connection() as c:
            self.assertEqual(c.execute('SELECT is_correct FROM student_results WHERE question_id=?',(q['id'],)).fetchone()[0],0)

    def test_english_only_in_grades_two_to_four_and_uses_applied_fourth_grade_plan(self):
        self.assertFalse(any(t['subject']=='İngilizce' for t in topics(1)))
        for grade in (2,3,4):
            english=[t for t in topics(grade) if t['subject']=='İngilizce']
            self.assertTrue(english)
            for t in english:
                bank=offline_bank(t['skill']);self.assertEqual(len(bank),8)
                self.assertTrue(all(q['choices'][q['answer']] in q['explanation'] for q in bank))
        fourth=[t['title'] for t in topics(4) if t['subject']=='İngilizce']
        self.assertEqual(len(fourth),10);self.assertIn('Classroom Rules',fourth[0])
        self.assertTrue(any('Yer Kabuğu' in t['title'] for t in topics(4) if t['subject']=='Fen Bilimleri'))
        self.assertTrue(any('Görsel Sanatlar'==c['subject'] for c in catalogue(1)))

    def test_similar_generation_sends_question_not_student_identity(self):
        q=practice_questions(self.student,1,['homework_turkce'])[0]
        draft=dict(text='Yeni örnek soru?',choices=['A','B','C','D'],answer=0,hint='Düşün',explanation='A doğrudur.')
        with patch('teaching_materials.generate_questions',return_value=[draft]) as generate:
            result=generate_similar(q,3,6)
        self.assertNotIn(self.student.name,generate.call_args.args[0])
        self.assertEqual(result[0]['source'],'ai-remediation')
        self.assertFalse(result[0]['verified']);self.assertEqual(result[0]['skill'],q['skill'])

    def test_missing_ai_key_has_clear_error(self):
        from curriculum_practice import generate_topic
        t=next(t for t in topics(3) if t['subject']=='Türkçe')
        with patch.dict(os.environ,{'GEMINI_GENERATOR_KEY':''}):
            with self.assertRaisesRegex(ValueError,'Gemini anahtarı'):generate_topic(t['skill'])

    def test_similar_without_key_uses_distinct_same_unit_questions(self):
        from curriculum_practice import offline_similar,PracticeWorker
        for grade in range(1,5):
            for topic in topics(grade):
                original=offline_bank(topic['skill'])[0]
                qs=offline_similar(original,grade,6)
                self.assertTrue(qs)
                self.assertEqual(len({q['text'] for q in qs}),len(qs))
                self.assertNotIn(original['text'],[q['text'] for q in qs])
                self.assertTrue(all(q['curriculum']['title']==original['curriculum']['title'] for q in qs))
        worker=PracticeWorker('similar',original,4,6);received=[];failed=[]
        worker.ready.connect(received.append);worker.failed.connect(failed.append)
        with patch.dict(os.environ,{'GEMINI_GENERATOR_KEY':''}),patch('curriculum_practice.generate_similar') as ai:worker.run()
        ai.assert_not_called();self.assertTrue(received);self.assertEqual(failed,[])
    def test_similar_ai_failure_falls_back_without_popup(self):
        from curriculum_practice import PracticeWorker
        original=offline_bank(topics(3)[0]['skill'])[0]
        worker=PracticeWorker('similar',original,3,6);received=[]
        worker.ready.connect(received.append)
        with patch.dict(os.environ,{'GEMINI_GENERATOR_KEY':'test'}),patch('curriculum_practice.generate_similar',side_effect=RuntimeError('Service unavailable')):worker.run()
        self.assertTrue(received);self.assertTrue(all(q['source']=='offline-remediation' for q in received[0]))
    def test_similar_button_without_key_opens_practice(self):
        from role_ui import RoleWindow
        from PyQt6.QtTest import QTest
        original=offline_bank(topics(3)[0]['skill'])[0]
        window=RoleWindow();self.windows.append(window);window.enter(self.student)
        with patch.dict(os.environ,{'GEMINI_GENERATOR_KEY':''}),patch.object(window,'open_questions') as opened,patch('role_ui.QMessageBox.information') as popup:
            window.generate_practice('similar',original,6)
            for _ in range(100):
                QTest.qWait(20)
                if opened.called:break
            window.practice_worker.wait(1000)
            self.assertTrue(opened.called);popup.assert_not_called()
            qs=opened.call_args.args[0]
            self.assertEqual(len(qs),len({q['text'] for q in qs}))
        window.schedule_timer.stop()

if __name__=='__main__':unittest.main()
