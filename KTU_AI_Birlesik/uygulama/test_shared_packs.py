"""Teacher-pack sharing, parent preview and scheduled activation regressions."""
import unittest
from unittest.mock import patch
from datetime import datetime,timedelta
from pathlib import Path
import test_materials as fixtures
import role_store as store
import teaching_materials as materials
from role_ui import RoleWindow
from data import education_database as school
from PyQt6.QtWidgets import QDialog,QPushButton,QListWidget,QLabel
from PyQt6.QtCore import Qt,QTimer

class SharedPackTests(unittest.TestCase):
    setUp=fixtures.MaterialTests.setUp
    close_windows=fixtures.MaterialTests.close_windows
    bank=fixtures.MaterialTests.bank
    metadata=fixtures.MaterialTests.metadata
    @classmethod
    def setUpClass(cls):fixtures.MaterialTests.setUpClass.__func__(cls)
    def save_pack(self,owner):
        m=self.metadata()
        return materials.save_pack(owner,'Öğretmenin okuma soruları',3,'Türkçe',m['title'],m['source'],'',self.bank())
    def test_teacher_packs_scoped_to_selected_child(self):
        own=self.save_pack(self.teacher);self.save_pack(self.other_teacher)
        self.assertEqual([p['id'] for p in materials.available_packs(self.parent,3,self.child)],[own])
        self.assertTrue(materials.available_packs(self.parent,3,self.child)[0]['from_teacher'])
        self.assertEqual(materials.available_packs(self.other,3,self.foreign_child),[])
        with self.assertRaises(ValueError):materials.available_packs(self.other,3,self.child)
        with self.assertRaises(ValueError):materials.available_packs(self.student,3,self.child)
    def test_child_and_class_edits_preserve_membership(self):
        store.update_child(self.parent,self.child,'Furkan Yücel',3)
        store.update_class(self.teacher,self.class_id,'3-A Keşif',3)
        self.assertEqual(store.require_student(self.parent,self.child)['alias'],'Furkan Yücel')
        self.assertEqual(store.classes(self.teacher)[0]['name'],'3-A Keşif')
        with self.assertRaises(ValueError):store.update_child(self.parent,self.child,'Furkan',4)
        with self.assertRaises(ValueError):store.update_class(self.teacher,self.class_id,'4-A',4)
        with self.assertRaises(ValueError):store.update_class(self.other_teacher,self.class_id,'Başka',3)
        with self.assertRaises(ValueError):store.update_child(self.other,self.child,'Başka',3)
    def test_parent_preview_selected_teacher_questions_schedule(self):
        pid=self.save_pack(self.teacher)
        window=RoleWindow();self.windows.append(window);window.enter(self.parent)
        window.student_picker.setCurrentIndex(window.student_picker.findData(self.child))
        errors=[]
        def select():
            d=next(w for w in self.app.topLevelWidgets() if isinstance(w,QDialog) and w.isVisible())
            try:
                preview=d.findChild(QListWidget,'TaskQuestionPreview')
                self.assertEqual(preview.count(),3)
                preview.item(1).setCheckState(Qt.CheckState.Unchecked)
                Path('test_artifacts').mkdir(exist_ok=True)
                d.grab().save('test_artifacts/teacher_pack_parent_preview.png')
                next(b for b in d.findChildren(QPushButton) if b.text()=='Görevi oluştur').click()
                if d.isVisible():raise AssertionError([x.text() for x in d.findChildren(QLabel)])
            except Exception as e:errors.append(e);d.reject()
        import role_schedule
        with patch.object(role_schedule,'register_windows'),patch('role_ui.QMessageBox.information'):
            QTimer.singleShot(100,select);window.task_dialog(pid)
        if errors:raise errors[0]
        task=store.tasks(self.student)[0]
        questions=store.task_questions(self.student,task['id'])
        self.assertEqual([q['text'] for q in questions],[self.bank()[i]['text'] for i in (0,2)])
        self.assertTrue(task['scheduled_at'])
        window.schedule_timer.stop()
    def test_teacher_pack_activates_at_parent_time(self):
        import role_schedule as scheduler
        m=self.metadata();pid=self.save_pack(self.teacher)
        pack=materials.available_packs(self.parent,3,self.child)[0]
        aid=store.create_task(self.parent,'Hocanın soruları','m3_toplama',3,student_id=self.child,curriculum=m,custom_questions=pack['questions'])
        with patch.object(scheduler,'register_windows'):
            scheduler.schedule(self.parent,aid,self.child,(datetime.now()+timedelta(days=1)).isoformat(timespec='seconds'))
        with school.get_connection() as c:c.execute("UPDATE task_schedules SET starts_at='2000-01-01T12:00:00'")
        window=RoleWindow();self.windows.append(window)
        with patch.object(window,'start_quiz') as launch:
            window.check_schedules();window.check_schedules()
            launch.assert_called_once_with(aid)
        self.assertEqual(window.identity.student_id,self.child)
        window.schedule_timer.stop()

    def test_period_filter_keeps_old_results_in_full_report(self):
        from role_quiz import AccountSession,practice_questions
        session=AccountSession(self.student,practice_questions(self.student,2))
        q=session.next_question();session.answer(q['answer'],1)
        with school.get_connection() as c:c.execute("UPDATE practice_attempts SET answered_at='2000-01-01 12:00:00'")
        self.assertEqual(store.analytics(self.parent,self.child)['total'],1)
        self.assertEqual(store.analytics(self.parent,self.child,period_days=7)['total'],0)
    def test_subject_animations_render_and_follow_lesson_step(self):
        from animated_lessons import AnimatedLessonScene
        from learning_engine.lesson_service import local_lesson
        from curriculum import catalogue
        for course in catalogue(3):
            q=dict(self.bank()[0],skill='m3_toplama',curriculum=dict(subject=course['subject']))
            widget=AnimatedLessonScene(q);widget.resize(860,300)
            lesson=local_lesson(dict(prompt=q['text'],options=q['choices'],correct_index=0,hint=q['hint'],explanation=q['explanation']))
            widget.show();widget.show_step(lesson,len(lesson['steps'])-1)
            widget.motion._advance();self.assertEqual(widget.motion.phase,2)
            self.assertFalse(widget.grab().isNull())
            widget.hide();self.assertFalse(widget.motion.timer.isActive());widget.close()
    def test_narration_completion_is_after_playback(self):
        import audio_narrator as audio
        from types import SimpleNamespace
        events=[]
        channel=SimpleNamespace(get_busy=lambda:False,stop=lambda:None)
        mixer=SimpleNamespace(get_init=lambda:True,Sound=lambda **kw:SimpleNamespace(play=lambda:channel))
        worker=audio.NarrationWorker('Deneme')
        worker.succeeded.connect(lambda:events.append('started'))
        worker.playback_finished.connect(lambda:events.append('finished'))
        with patch.object(audio,'synthesize',return_value=b'wav'),patch.dict('sys.modules',{'pygame':SimpleNamespace(mixer=mixer)}):worker.run()
        self.assertEqual(events,['started','finished'])
        worker.requestInterruption();events.clear()
        with patch.object(audio,'synthesize',return_value=b'wav'):worker.run()
        self.assertEqual(events,[])
        audio._CHANNEL=None

if __name__=='__main__':unittest.main()
