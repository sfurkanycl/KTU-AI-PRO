"""Account isolation, task lifecycle, analytics and role UI regression tests."""
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['LESSON_PROVIDER'] = 'local'
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

with patch('ctypes.CDLL', side_effect=OSError('Native hooks disabled during tests')):
    from data import education_database as school
    from data import database as legacy
    import role_store as store
    from role_ui import RoleWindow
    from role_quiz import StudentQuiz, AccountSession, practice_questions
    from PyQt6.QtWidgets import QApplication


class RoleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        from ui_fonts import configure_fonts
        configure_fonts(cls.app)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        for module,name in [(school,'school.db'),(legacy,'legacy.db')]:
            p = patch.object(module,'DB_PATH',Path(self.temp.name)/name)
            p.start()
            self.addCleanup(p.stop)
        store.init()
        legacy.init_db()
        self.parent = store.register('veli1','secure123','Ayşe Yılmaz','parent')
        self.other = store.register('veli2','secure456','Diğer Veli','parent')
        self.teacher = store.register('ogretmen1','secure123','Deniz Öğretmen','teacher')
        self.other_teacher = store.register('ogretmen2','secure123','Diğer Öğretmen','teacher')
        self.child = store.add_child(self.parent,'Furkan',3,'furkan','student123')
        self.second_child = store.add_child(self.parent,'Elif',3,'elif','student123')
        self.foreign_child = store.add_child(self.other,'Başka Çocuk',3,'otherchild','student123')
        self.student = store.authenticate('furkan','student123')
        self.student2 = store.authenticate('elif','student123')
        self.class_id = store.add_class(self.teacher,'3-A',3)
        self.foreign_class = store.add_class(self.other_teacher,'3-B',3)
        code = store.classes(self.teacher)[0]['code']
        store.join_class(self.parent,self.child,code)
        store.join_class(self.parent,self.second_child,code)
        self.windows = []
        self.addCleanup(self.close_windows)

    def close_windows(self):
        for window in self.windows:
            if isinstance(window,StudentQuiz):
                window._finish('test')
            else:
                window.close()
        self.app.processEvents()

    def test_authentication_hashes_and_lockout(self):
        with school.get_connection() as c:
            password_hash = c.execute('SELECT password_hash FROM login_accounts WHERE username=?',('veli1',)).fetchone()[0]
        self.assertNotEqual(password_hash,'secure123')
        for _ in range(5):
            with self.assertRaises(ValueError):
                store.authenticate('veli1','wrong')
        with self.assertRaisesRegex(ValueError,'Beş dakika'):
            store.authenticate('veli1','secure123')

    def test_parent_teacher_student_access_is_scoped(self):
        self.assertEqual({s['id'] for s in store.students(self.parent)}, {self.child,self.second_child})
        self.assertEqual({s['id'] for s in store.students(self.teacher)}, {self.child,self.second_child})
        self.assertEqual({s['id'] for s in store.students(self.student)}, {self.child})
        for identity in (self.parent,self.teacher,self.student):
            with self.assertRaises(ValueError):
                store.analytics(identity,self.foreign_child)
        with self.assertRaises(ValueError):
            store.create_task(self.teacher,'Yabancı sınıf','traffic',2,class_id=self.foreign_class)
        with self.assertRaises(ValueError):
            store.reset_child_password(self.other,self.child,'newpass123')

    def test_parent_assignment_resume_and_real_analytics(self):
        aid = store.create_task(self.parent,'Fen keşfi','matter_states',3,student_id=self.child)
        questions = store.task_questions(self.student,aid)
        session = AccountSession(self.student,questions,aid)
        q = session.next_question()
        session.answer(q['answer'],5)
        with self.assertRaises(ValueError):
            session.answer(q['answer'],5)
        self.assertEqual(len(store.task_questions(self.student,aid)),2)
        resumed = AccountSession(self.student,store.task_questions(self.student,aid),aid)
        q = resumed.next_question()
        resumed.answer((q['answer']+1)%len(q['choices']),8,True)
        report = store.analytics(self.parent,self.child)
        self.assertEqual((report['total'],report['correct'],report['wrong']),(2,1,1))
        self.assertEqual(report['rate'],50)
        self.assertEqual(store.tasks(self.student)[0]['completed'],2)
        self.assertEqual(store.tasks(self.student2),[])
        with self.assertRaises(ValueError):
            store.task_questions(self.student2,aid)

    def test_teacher_whole_class_and_individual_tasks(self):
        all_id = store.create_task(self.teacher,'Sınıf çalışması','traffic',2,class_id=self.class_id)
        individual = store.create_task(self.teacher,'Bireysel destek','living_needs',2,class_id=self.class_id,student_id=self.child)
        self.assertEqual({t['id'] for t in store.tasks(self.student)}, {all_id,individual})
        self.assertEqual({t['id'] for t in store.tasks(self.student2)}, {all_id})
        self.assertEqual(store.tasks(self.other_teacher),[])
        with self.assertRaises(ValueError):
            store.task_questions(self.student2,individual)

    def test_practice_records_belong_to_the_logged_in_child(self):
        questions = practice_questions(self.student,12)
        self.assertGreaterEqual(len({q['skill'] for q in questions}),4)
        session = AccountSession(self.student,questions)
        q = session.next_question()
        session.answer(q['answer'],4)
        self.assertEqual(store.analytics(self.parent,self.child)['total'],1)
        self.assertEqual(store.analytics(self.other)['total'],0)
        self.assertEqual(store.analytics(self.teacher,class_id=self.class_id)['total'],1)

    def test_parent_password_reset(self):
        store.reset_child_password(self.parent,self.child,'newpassword')
        self.assertEqual(store.authenticate('furkan','newpassword').student_id,self.child)
        with self.assertRaises(ValueError):
            store.authenticate('furkan','student123')

    def test_parent_practice_preferences_only_produce_selected_subjects(self):
        store.set_practice_skills(self.parent,self.child,['traffic','homework_turkce'])
        qs = practice_questions(self.student,12)
        self.assertEqual([q['skill'] for q in qs],['traffic','homework_turkce']*6)
        with self.assertRaises(ValueError):
            store.set_practice_skills(self.other,self.child,['traffic'])
        aid = store.create_task(self.parent,'Çarpma görevi','m3_carpma',4,student_id=self.child)
        self.assertEqual(len(store.task_questions(self.student,aid)),4)

    def test_previous_history_import_is_verified_and_idempotent(self):
        from learning import LearningSession
        legacy.save_student('Furkan',3,'erkek')
        legacy.set_pin('7351')
        session = LearningSession(legacy.start_session(),['matter_states'],1,18)
        q = session.next_question()
        session.answer(q['answer'],5)
        with self.assertRaises(ValueError):
            store.import_legacy_history(self.other,self.child,'7351')
        self.assertEqual(store.import_legacy_history(self.parent,self.child,'7351'),1)
        self.assertEqual(store.import_legacy_history(self.parent,self.child,'7351'),0)
        self.assertEqual(store.analytics(self.parent,self.child)['total'],1)
        with self.assertRaises(ValueError):
            store.import_legacy_history(self.parent,self.second_child,'7351')

    def test_completed_assignment_disappears_from_remaining_questions(self):
        aid = store.create_task(self.teacher,'Tamamlanacak görev','traffic',2,class_id=self.class_id)
        session = AccountSession(self.student,store.task_questions(self.student,aid),aid)
        for correct in (True,False):
            q = session.next_question()
            session.answer(q['answer'] if correct else (q['answer']+1)%len(q['choices']),5)
        self.assertTrue(session.goal_reached())
        self.assertEqual(store.task_questions(self.student,aid),[])
        self.assertEqual(store.tasks(self.teacher)[0]['completed_students'],1)
        self.assertEqual(store.tasks(self.teacher)[0]['recipient_count'],2)

    def test_passwordless_child_and_chosen_topic(self):
        sid=store.add_child(self.parent,'Yeni Çocuk',2)
        identity=store.student_identity(sid)
        self.assertEqual(identity.role,'student')
        self.assertEqual(store.students(identity)[0]['id'],sid)
        self.assertIn(sid,{r['id'] for r in store.child_profiles()})
        self.assertEqual({q['skill'] for q in practice_questions(identity,4,skills=['traffic'])},{'traffic'})

    def test_class_notifications_are_owned_and_resharable(self):
        self.assertEqual(store.share_class(self.teacher,self.class_id),2)
        self.assertEqual(len(store.notifications(self.parent)),1)
        self.assertIn(store.classes(self.teacher)[0]['code'],store.notifications(self.parent)[0]['message'])
        store.notifications(self.parent,acknowledge=True)
        self.assertEqual(store.notifications(self.parent),[])
        self.assertEqual(len(store.notifications(self.other)),1)
        with self.assertRaises(ValueError): store.share_class(self.other_teacher,self.class_id)
        store.share_class(self.teacher,self.class_id)
        self.assertEqual(len(store.notifications(self.parent)),1)

    def test_scheduled_task_opens_without_student_button(self):
        from datetime import datetime, timedelta
        import role_schedule as scheduler
        from PyQt6.QtWidgets import QPushButton
        aid = store.create_task(self.parent, 'Otomatik görev', 'traffic', 2, student_id=self.child)
        with patch.object(scheduler, 'register_windows'):
            scheduler.schedule(self.parent, aid, self.child, (datetime.now()+timedelta(days=1)).isoformat(timespec='seconds'))
        window = RoleWindow()
        self.windows.append(window)
        window.identity = self.student
        window.student_home()
        self.assertFalse(any(b.text() == 'Göreve başla' for b in window.findChildren(QPushButton)))
        with school.get_connection() as c:
            c.execute("UPDATE task_schedules SET starts_at='2000-01-01T12:00:00'")
        window.identity = None
        with patch.object(window, 'start_quiz') as launch:
            window.check_schedules()
            launch.assert_called_once_with(aid)
            self.assertEqual(window.identity.student_id, self.child)
            window.check_schedules()
            launch.assert_called_once()
        window.schedule_timer.stop()

    def test_student_practice_filters_count_and_no_task_start(self):
        from PyQt6.QtWidgets import QPushButton
        from curriculum import subject_for_skill
        store.create_task(self.parent, 'Saati bekleniyor', 'traffic', 2, student_id=self.child)
        window=RoleWindow();self.windows.append(window);window.identity=self.student;window.student_home()
        texts=[b.text() for b in window.findChildren(QPushButton)]
        self.assertNotIn('Göreve başla',texts);self.assertNotIn('Göreve devam et',texts)
        window.practice_subject.setCurrentText('Türkçe')
        skills=[window.practice_topic.itemData(i) for i in range(1,window.practice_topic.count())]
        self.assertTrue(skills)
        self.assertTrue(all(subject_for_skill(k,3)=='Türkçe' for k in skills))
        window.practice_subject.setCurrentText('İngilizce')
        skills=[window.practice_topic.itemData(i) for i in range(1,window.practice_topic.count())]
        window.practice_topic.setCurrentIndex(1)
        window.practice_count.setValue(37)
        with patch.object(window,'start_quiz') as launch:
            next(b for b in window.findChildren(QPushButton) if b.text()=='Alıştırmaya başla').click()
            self.assertEqual(launch.call_args.kwargs['count'],37)
            self.assertEqual(launch.call_args.kwargs['skills'],[skills[0]])
        window.practice_continuous.setChecked(True)
        self.assertFalse(window.practice_count.isEnabled())
        Path('test_artifacts').mkdir(exist_ok=True)
        window.resize(1240,850);window.show();self.app.processEvents()
        window.grab().save('test_artifacts/student_pastel.png')
        window.schedule_timer.stop()

    def test_continuous_practice_extends_selected_subject(self):
        session=AccountSession(self.student,practice_questions(self.student,1,['homework_turkce']),continuous=True,practice_skills=['homework_turkce'])
        first=session.next_question();session.answer(first['answer'],10)
        self.assertFalse(session.goal_reached())
        next_question=session.next_question()
        self.assertEqual(next_question['skill'],'homework_turkce')
        self.assertGreater(len(session.questions),1)
        with self.assertRaises(ValueError):practice_questions(self.student,0)

    def test_schedule_interrupts_free_practice(self):
        from datetime import datetime,timedelta
        import role_schedule as scheduler
        from unittest.mock import Mock
        aid=store.create_task(self.parent,'Saat geldi','traffic',2,student_id=self.child)
        with patch.object(scheduler,'register_windows'):
            scheduler.schedule(self.parent,aid,self.child,(datetime.now()+timedelta(days=1)).isoformat(timespec='seconds'))
        with school.get_connection() as c:c.execute("UPDATE task_schedules SET starts_at='2000-01-01T12:00:00'")
        window=RoleWindow();self.windows.append(window)
        quiz=Mock();quiz._allow_close=False;quiz.learning.assignment_id=None;window.quiz=quiz
        with patch.object(window,'start_quiz') as launch:
            window.check_schedules();launch.assert_called_once_with(aid)
            quiz._finish.assert_called_once_with('saatli_gorev')
        window.quiz=None;window.schedule_timer.stop()

    def test_schedule_is_per_child_and_replaces_old_time(self):
        from datetime import datetime,timedelta
        import role_schedule as scheduler
        aid=store.create_task(self.teacher,'Sınıf görevi','traffic',2,class_id=self.class_id)
        first=(datetime.now()+timedelta(days=1)).isoformat(timespec='seconds')
        second=(datetime.now()+timedelta(days=2)).isoformat(timespec='seconds')
        with patch.object(scheduler,'register_windows'):
            scheduler.schedule(self.parent,aid,self.child,first)
            self.assertIn('scheduled_at',store.tasks(self.student)[0])
            self.assertNotIn('scheduled_at',store.tasks(self.student2)[0])
            scheduler.schedule(self.parent,aid,self.child,second)
        with school.get_connection() as c:
            rows=c.execute('SELECT status FROM task_schedules WHERE assignment_id=? ORDER BY id',(aid,)).fetchall()
        self.assertEqual([r[0] for r in rows],['cancelled','pending'])
        self.assertEqual(store.tasks(self.student)[0]['scheduled_at'],second)

    def test_schedule_persistence_and_single_claim(self):
        from datetime import datetime,timedelta
        import role_schedule as scheduler
        aid=store.create_task(self.parent,'Saatli görev','traffic',2,student_id=self.child)
        when=(datetime.now()+timedelta(days=1)).isoformat(timespec='seconds')
        with patch.object(scheduler,'register_windows') as register:
            scheduler.schedule(self.parent,aid,self.child,when)
            register.assert_called_once()
        self.assertIsNone(scheduler.due_schedule())
        with school.get_connection() as c:
            c.execute("UPDATE task_schedules SET starts_at='2000-01-01T12:00:00'")
        item=scheduler.due_schedule()
        self.assertEqual(item['student_id'],self.child)
        self.assertTrue(scheduler.claim_schedule(item['id']))
        self.assertFalse(scheduler.claim_schedule(item['id']))
        with self.assertRaises(ValueError): scheduler.schedule(self.other,aid,self.child,when)

    def test_curriculum_assignment_records_source(self):
        from curriculum import catalogue
        course=next(r for r in catalogue(3) if r['subject']=='Matematik')
        unit=next(u for u in course['units'] if 'İşlemlerden' in u['title'])
        metadata=dict(grade=3,subject='Matematik',title=unit['title'],source=unit['url'])
        aid=store.create_task(self.parent,'MEB işlemler alıştırması','m3_toplama',3,student_id=self.child,curriculum=metadata)
        self.assertEqual(store.task_questions(self.student,aid)[0]['curriculum'],metadata)
        with self.assertRaises(ValueError):
            store.create_task(self.parent,'Yanlış eşleşme','traffic',2,student_id=self.child,curriculum=metadata)

    def test_task_dialog_curriculum_and_clock(self):
        from PyQt6.QtCore import QTimer
        from PyQt6.QtWidgets import QDialog,QComboBox,QTimeEdit,QCheckBox
        window=RoleWindow();self.windows.append(window)
        window.enter(self.parent)
        observed=[]
        def inspect():
            d=next(w for w in self.app.topLevelWidgets() if isinstance(w,QDialog) and w.isVisible())
            combos=d.findChildren(QComboBox)
            subject=next(w for w in combos if w.itemText(0)=='Hazır alıştırmalar')
            subject.setCurrentIndex(subject.findText('Matematik'))
            unit=next(w for w in combos if w.count() and 'Tema:' in w.itemText(0))
            unit.setCurrentIndex(next(i for i in range(unit.count()) if 'İşlemlerden' in unit.itemText(i)))
            custom=next(w for w in d.findChildren(QCheckBox) if 'kendi sorumu' in w.text())
            observed.append(not custom.isChecked() and bool(d.findChildren(QTimeEdit)))
            Path('test_artifacts').mkdir(exist_ok=True)
            d.grab().save('test_artifacts/role_task_curriculum.png')
            d.reject()
        QTimer.singleShot(100,inspect)
        window.task_dialog()
        self.assertEqual(observed,[True])

    def test_demo_seed_is_idempotent(self):
        import seed_demo
        seed_demo.seed()
        with school.get_connection() as c:
            count=c.execute('SELECT COUNT(*) FROM students').fetchone()[0]
            attempts=c.execute("SELECT COUNT(*) FROM practice_attempts WHERE question_text LIKE '[Örnek veri]%'").fetchone()[0]
        seed_demo.seed()
        with school.get_connection() as c:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM students').fetchone()[0],count)
            self.assertEqual(c.execute("SELECT COUNT(*) FROM practice_attempts WHERE question_text LIKE '[Örnek veri]%'").fetchone()[0],attempts)
        self.assertGreater(attempts,300)

    def test_role_screens_and_quiz_render_real_records(self):
        aid = store.create_task(self.parent,'Maddenin hâlleri','matter_states',4,student_id=self.child)
        session = AccountSession(self.student,store.task_questions(self.student,aid),aid)
        for correct in (True,False):
            q = session.next_question()
            session.answer(q['answer'] if correct else (q['answer']+1)%len(q['choices']),5)
        window = RoleWindow()
        self.windows.append(window)
        window.show()
        Path('test_artifacts').mkdir(exist_ok=True)
        self.app.processEvents()
        window.grab().save('test_artifacts/role_login.png')
        for identity,name in [(self.parent,'parent'),(self.teacher,'teacher')]:
            window.enter(identity)
            window.student_picker.setCurrentIndex(window.student_picker.findData(self.child))
            self.app.processEvents()
            self.assertEqual(window.identity.role,identity.role)
            window.grab().save(f'test_artifacts/role_{name}.png')
            for section in ('tasks','people','manage'):
                window.show_section(section)
                self.app.processEvents()
        window.enter(self.student)
        self.app.processEvents()
        window.grab().save('test_artifacts/role_student_tasks.png')
        quiz = StudentQuiz(self.student,store.task_questions(self.student,aid),aid)
        self.windows.append(quiz)
        quiz.resize(1200,900)
        quiz.show()
        from PyQt6.QtTest import QTest
        QTest.qWait(450)
        quiz._on_hint()
        QTest.qWait(150)
        self.assertTrue(quiz._hint_used)
        quiz.grab().save('test_artifacts/role_student_quiz.png')
        self.assertEqual(quiz.identity.student_id,self.child)


if __name__ == '__main__':
    unittest.main()
