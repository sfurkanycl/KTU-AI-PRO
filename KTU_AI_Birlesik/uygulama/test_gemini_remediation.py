import unittest
from unittest.mock import patch
from role_quiz import AccountSession, semantic_key
from curriculum_practice import PracticeWorker

class RemediationTests(unittest.TestCase):
 def seed(self,text='7 + 5 kaçtır?'):
  return dict(id=1,skill='m3_toplama',text=text,choices=['12','11','10','13'],answer=0,concept='addition')
 def test_generated_variants_do_not_replace_visible_question_or_duplicate(self):
  seed=self.seed();s=AccountSession(None,[seed,self.seed('8 + 4 kaçtır?')])
  s.next_question()
  new=self.seed('9 + 3 kaçtır?')
  self.assertEqual(s.add_generated_review(seed,[seed,new,new]),1)
  self.assertEqual(s.questions[0]['text'],seed['text'])
  self.assertEqual(s.questions[1]['text'],new['text'])
  self.assertTrue(s.questions[1]['_support_question'])
  self.assertEqual(s.questions[1]['source'],'ai-remediation')
 def test_arrival_after_answer_is_next_question(self):
  seed=self.seed();s=AccountSession(None,[seed,self.seed('8 + 4 kaçtır?')])
  s.next_question();s.attempts=1;s._recorded=True
  s.add_generated_review(seed,[self.seed('9 + 3 kaçtır?')])
  self.assertEqual(s.next_question()['text'],'9 + 3 kaçtır?')
 def test_worker_calls_generator_and_reports_failure_without_fake_ai_fallback(self):
  worker=PracticeWorker('auto-similar',self.seed(),3,3)
  errors=[];results=[];worker.failed.connect(errors.append);worker.ready.connect(results.append)
  with patch('curriculum_practice.generate_similar',side_effect=ValueError('kota')),patch('curriculum_practice.offline_similar') as fallback:
   worker.run()
  self.assertEqual(errors,['kota']);self.assertEqual(results,[]);fallback.assert_not_called()
  from curriculum_practice import _WORKERS
  _WORKERS.discard(worker)

if __name__=='__main__':unittest.main()
