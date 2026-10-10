import unittest,os
from unittest.mock import patch
import test_roles as f
from curriculum_practice import topics
from role_quiz import practice_questions
from teaching_materials import save_pack
class StudentEntryTests(unittest.TestCase):
 setUpClass=classmethod(f.RoleTests.setUpClass.__func__)
 setUp=f.RoleTests.setUp
 close_windows=f.RoleTests.close_windows
 def test_first_entry_reuses_class_student_and_tracks_number(self):
  code=f.store.classes(self.teacher)[0]['code']
  identity=f.store.enter_student_by_number('Furkan','42',code)
  self.assertEqual(identity.student_id,self.child)
  self.assertEqual(f.store.school_number(self.child),'42')
  self.assertEqual(f.store.enter_student_by_number('Furkan','42').student_id,self.child)
  with self.assertRaises(ValueError):f.store.enter_student_by_number('Other','42',code)
 def test_new_student_belongs_only_to_invited_teacher(self):
  code=f.store.classes(self.teacher)[0]['code']
  identity=f.store.enter_student_by_number('Yeni Çocuk','78',code)
  self.assertIn(identity.student_id,[r['id'] for r in f.store.students(self.teacher,self.class_id)])
  self.assertNotIn(identity.student_id,[r['id'] for r in f.store.students(self.other_teacher)])
  self.assertEqual(f.store.require_student(identity,identity.student_id)['grade'],3)
  with self.assertRaises(ValueError):f.store.enter_student_by_number('Yeni','x',code)
  with self.assertRaises(ValueError):f.store.enter_student_by_number('Yeni','79','INVALID')
 def test_offline_approved_topic_works_without_key_and_is_scoped(self):
  topic=next(t for t in topics(3) if t['subject']=='Türkçe')
  q=dict(text='Hangisi bir sözcüktür?',choices=['kalem','...','?','!'],answer=0,hint='Anlamlı olanı seç.',explanation='Kalem anlamlı bir sözcüktür.')
  save_pack(self.teacher,'Türkçe deneme',3,topic['subject'],topic['title'],topic['url'],'',[q,dict(q,text='Hangi seçenek bir sözcüktür?')])
  bank=f.store.student_topic_bank(self.student,topic['skill'])
  self.assertTrue(bank)
  with patch.dict(os.environ,{'GEMINI_GENERATOR_KEY':''}):
   self.assertEqual(len(practice_questions(self.student,3,[topic['skill']])),3)
  foreign=f.store.student_topic_bank(f.store.student_identity(self.foreign_child),topic['skill'])
  self.assertFalse(any(q.get('source')=='adult-approved' for q in foreign))
 def test_student_login_fields_and_unavailable_topic(self):
  window=f.RoleWindow();self.windows.append(window)
  self.assertIsNotNone(window.student_number)
  window.enter(self.student)
  window.practice_subject.setCurrentText('Türkçe');window.practice_topic.setCurrentIndex(1)
  self.assertTrue(window.explore_button.isEnabled())
  self.assertNotIn('GEMINI',window.practice_notice.text())
  window.practice_subject.setCurrentText('İngilizce');window.practice_topic.setCurrentIndex(1)
  self.assertTrue(window.explore_button.isEnabled())
if __name__=='__main__':unittest.main()
