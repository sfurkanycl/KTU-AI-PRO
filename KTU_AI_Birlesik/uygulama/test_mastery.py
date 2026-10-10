"""Mastery completion, remediation persistence and illustrated animation regression."""
import unittest,json
from unittest.mock import patch
import test_materials as fixtures
import role_store as store
from mastery_session import MasterySession
from data import education_database as school
from role_quiz import StudentQuiz
from animated_story import StoryScene

class MasteryTests(unittest.TestCase):
 setUp=fixtures.MaterialTests.setUp
 close_windows=fixtures.MaterialTests.close_windows
 metadata=fixtures.MaterialTests.metadata
 @classmethod
 def setUpClass(cls):fixtures.MaterialTests.setUpClass.__func__(cls)
 def task(self,count=12):
  bank=[dict(text=f'Ada {n} arkadaşına yardım etti. Bu davranış nedir?',choices=['Yardımlaşma','Kavga','İsraf','Kabalık'],answer=0,hint='Paylaşmayı düşün.',explanation='Arkadaşına destek olmak yardımlaşmadır.',concept='yardimlasma') for n in range(count)]
  aid=store.create_task(self.parent,'Yardımlaşma','m3_toplama',count,student_id=self.child,curriculum=self.metadata(),custom_questions=bank)
  return aid,MasterySession(self.student,store.task_questions(self.student,aid),aid)
 def respond(self,s,correct=True,hint=False):
  q=s.next_question();self.assertIsNotNone(q);return s.answer(q['answer'] if correct else (q['answer']+1)%4,3,hint)
 def test_five_clean_answers_allow_early_exit_and_preserve_true_count(self):
  aid,s=self.task()
  for _ in range(5):self.respond(s)
  self.assertTrue(s.goal_reached());self.assertEqual(s.base_answered,5)
  task=store.tasks(self.student)[0]
  self.assertTrue(task['mastered']);self.assertEqual(task['completed'],5)
  self.assertEqual(task['completed_students'],1);self.assertEqual(store.task_questions(self.student,aid),[])
 def test_wrong_answers_extend_and_recent_evidence_can_recover(self):
  aid,s=self.task(5)
  for _ in range(18):self.respond(s,False)
  self.assertFalse(s.goal_reached());self.assertGreater(s.max_attempts,5)
  for _ in range(4):self.respond(s,True)
  self.assertTrue(s.goal_reached());self.assertEqual(s.mastery_percent(),80)
  self.assertGreater(s.support_attempts,0)
 def test_curriculum_variants_keep_pack_skill_and_do_not_repeat(self):
  aid,s=self.task(1)
  seed=dict(s.pool[0])
  variants=[dict(seed,skill='cur_3_other_storage',text=f'Yeni olay {n}: arkadaşına destek olmak hangi davranıştır?') for n in range(20)]
  seen=[]
  with patch('curriculum_practice.offline_similar',return_value=variants):
   for _ in range(18):
    q=s.next_question();seen.append(q['text'])
    self.assertEqual(s.key(q),s.key(seed))
    s.answer((q['answer']+1)%4,5)
  self.assertEqual(len(seen),len(set(seen)))
 def test_resume_remembers_previously_shown_variants(self):
  aid,s=self.task(1)
  seed=dict(s.pool[0])
  variants=[dict(seed,text=f'Farklı yardımlaşma olayı {n}?') for n in range(12)]
  with patch('curriculum_practice.offline_similar',return_value=variants):
   self.respond(s,False);previous=s.next_question();s.answer((previous['answer']+1)%4,5)
   resumed=MasterySession(self.student,store.task_questions(self.student,aid),aid)
   resumed._add_review(resumed.key(seed))
   self.assertNotEqual(resumed.next_question()['text'],previous['text'])

 def test_hinted_answers_do_not_unlock(self):
  _,s=self.task(5)
  for _ in range(8):self.respond(s,True,True)
  self.assertFalse(s.goal_reached());self.assertEqual(s.mastery_percent(),0)
 def test_resume_keeps_evidence_after_all_original_questions_answered(self):
  aid,s=self.task(5)
  for _ in range(5):self.respond(s,False)
  self.assertFalse(store.tasks(self.student)[0]['mastered'])
  qs=store.task_questions(self.student,aid);self.assertTrue(qs)
  resumed=MasterySession(self.student,qs,aid)
  self.assertEqual(resumed.evidence_count,5)
  for _ in range(4):self.respond(resumed)
  self.assertTrue(resumed.goal_reached())
 def test_one_weak_type_cannot_be_hidden_by_other_correct_answers(self):
  aid,s=self.task(10)
  s.requirements={'known':5,'weak':5};s.evidence={'known':[1]*5,'weak':[0]*5};s.evidence_count=100
  self.assertFalse(s.goal_reached());self.assertEqual(s.mastery_percent(),50)
 def test_session_has_no_countdown(self):
  aid,_=self.task()
  with patch('keyboard_guard.guard.start'):
   quiz=StudentQuiz(self.student,store.task_questions(self.student,aid),aid);self.windows.append(quiz)
  value=quiz.remaining
  quiz._on_tick();self.assertEqual(quiz.remaining,value);self.assertIn('%80',quiz.timer_lbl.text())
 def test_story_has_real_motion_and_full_question(self):
  q=dict(text='Ada, sınıfta arkadaşına bir kalem verdi. Bu davranışın adı nedir?',choices=['Yardımlaşma','Kavga','İsraf','Kabalık'],answer=0,hint='Arkadaşına nasıl destek oldu?',explanation='Kalemini paylaşarak arkadaşına yardım etti.')
  widget=StoryScene(q);widget.resize(900,480);widget.set_step(1);widget.show();self.app.processEvents()
  first=widget.grab().toImage();widget.frame=40;widget.update();self.app.processEvents();second=widget.grab().toImage()
  self.assertNotEqual(first,second);self.assertTrue(widget.helping)
  widget.grab().save('test_artifacts/animated_help_story.png');widget.hide();self.assertFalse(widget.timer.isActive());widget.close()
 def test_mastery_exit_button_closes_without_parent_password(self):
  aid,_=self.task()
  with patch('keyboard_guard.guard.start'):
   quiz=StudentQuiz(self.student,store.task_questions(self.student,aid),aid);self.windows.append(quiz)
  for _ in range(5):self.respond(quiz.learning)
  quiz._load_question()
  self.assertEqual(quiz.next_btn.text(),'Uygulamadan çık')
  with patch.object(self.app,'quit') as quit_app,patch('role_quiz.QInputDialog.getText') as password:
   quiz.next_btn.click()
  quit_app.assert_called_once();password.assert_not_called();self.assertTrue(quiz._allow_close)

 def test_document_ai_analyzes_types_and_returns_reviewable_variants(self):
  import os
  from types import SimpleNamespace
  from unittest.mock import MagicMock
  import teaching_materials as materials
  client=MagicMock()
  questions=[dict(text=f'Ada {n} kişiye kalem verdi. Davranışın adı nedir?',choices=['Yardımlaşma','Kavga','İsraf','Kabalık'],answer=0,hint='Paylaşmayı düşün.',explanation='Arkadaşına yardım ediyor.',concept='yardimlasma') for n in range(2)]
  client.interactions.create.return_value=SimpleNamespace(output_text=json.dumps(dict(questions=questions)))
  with patch.dict(os.environ,{'GEMINI_GENERATOR_KEY':'test'}),patch('google.genai.Client',return_value=client):
   result=materials.generate_questions('Ada arkadaşına kalem verir. Bu davranış yardımlaşmadır. '*4,2,'Hayat Bilgisi','Değerlerimiz',2)
  prompt=client.interactions.create.call_args.kwargs['input']
  self.assertIn('soru türlerini',prompt);self.assertIn('aynen kopyalama',prompt)
  self.assertTrue(all(q['source']=='document-ai-draft' and not q['verified'] for q in result));client.close.assert_called_once()

if __name__=='__main__':unittest.main()
