"""Every active curriculum unit must work offline in practice and assignments."""
import os,re,unittest
from unittest.mock import patch
import test_roles as f
from curriculum_practice import topics,offline_bank
from curriculum import ready_skills
from role_quiz import practice_questions,StudentQuiz
from PyQt6.QtTest import QTest
class AllTopicTests(unittest.TestCase):
 setUpClass=classmethod(f.RoleTests.setUpClass.__func__)
 setUp=f.RoleTests.setUp
 close_windows=f.RoleTests.close_windows
 def test_every_topic_has_valid_explained_offline_questions(self):
  total=0
  for grade in range(1,5):
   for t in topics(grade):
    with self.subTest(grade=grade,subject=t['subject'],unit=t['title']):
     qs=offline_bank(t['skill']);self.assertGreaterEqual(len(qs),8)
     self.assertIn(t['skill'],ready_skills(t['subject'],t['title'],grade))
     for q in qs:
      self.assertEqual(q['skill'],t['skill']);self.assertEqual(q['curriculum']['grade'],grade)
      self.assertEqual(len(q['choices']),4);self.assertEqual(len(set(q['choices'])),4)
      self.assertIn(q['answer'],range(4));self.assertTrue(q['explanation'])
      self.assertTrue(q.get('verified'));self.assertFalse(q['source'].startswith('ai-'))
     total+=1
  self.assertEqual(total,182)
 def test_all_topics_start_practice_without_ai(self):
  with patch.dict(os.environ,{'GEMINI_GENERATOR_KEY':''}),patch('curriculum_practice.generate_topic',side_effect=AssertionError('Network generation must not run')):
   for grade in range(1,5):
    sid=f.store.add_child(self.parent,'Deneme '+str(grade),grade)
    identity=f.store.student_identity(sid)
    for t in topics(grade):
     with self.subTest(grade=grade,unit=t['title']):
      qs=practice_questions(identity,12,[t['skill']]);self.assertEqual(len(qs),12)
      self.assertTrue(all(q['skill']==t['skill'] for q in qs))
 def test_every_unit_supports_thirty_question_parent_assignment(self):
  for grade in range(1,5):
   sid=f.store.add_child(self.parent,'Görev '+str(grade),grade);identity=f.store.student_identity(sid)
   for t in topics(grade):
    with self.subTest(grade=grade,unit=t['title']):
     curriculum=dict(grade=grade,subject=t['subject'],title=t['title'],source=t['url'])
     aid=f.store.create_task(self.parent,'Konu denemesi',t['skill'],30,student_id=sid,curriculum=curriculum)
     qs=f.store.task_questions(identity,aid);self.assertEqual(len(qs),30)
     self.assertTrue(all(q['skill']==t['skill'] for q in qs))
 def test_math_answers_against_worded_operations(self):
  checked=0
  for grade in range(1,5):
   for t in topics(grade):
    if t['subject']!='Matematik':continue
    for q in offline_bank(t['skill']):
     text=q['text'];actual=q['choices'][q['answer']]
     m=re.search(r'^(\d+) \+ (\d+) işleminin',text)
     if m:self.assertEqual(int(actual),sum(map(int,m.groups())));checked+=1
     m=re.search(r'^(\d+) sayısından (sonra|önce)',text)
     if m:self.assertEqual(int(actual),int(m[1])+(1 if m[2]=='sonra' else -1));checked+=1
     m=re.search(r'Bir kenarı (\d+) cm olan karenin çevresi',text)
     if m:self.assertEqual(int(actual),int(m[1])*4);checked+=1
  self.assertGreater(checked,100)
 def test_reading_answers_are_in_original_passages(self):
  for grade in range(1,5):
   for t in topics(grade):
    if t['subject']!='Türkçe':continue
    for q in offline_bank(t['skill']):
     if q.get('concept','').startswith('reading_'):
      if 'kişi kimdir?' in q['text']:
       self.assertEqual(q['choices'][q['answer']],q['text'].split(',')[0])
 def test_student_all_subjects_have_enabled_start_and_long_answers_render(self):
  window=f.RoleWindow();self.windows.append(window);window.enter(self.student)
  with patch.dict(os.environ,{'GEMINI_GENERATOR_KEY':''}):
   for i in range(window.practice_subject.count()):
    window.practice_subject.setCurrentIndex(i)
    for j in range(1,window.practice_topic.count()):
     window.practice_topic.setCurrentIndex(j)
     self.assertTrue(window.explore_button.isEnabled(),window.practice_topic.currentText())
     self.assertEqual(window.practice_notice.text(),'')
  topic=next(t for t in topics(3) if t['subject']=='Görsel Sanatlar')
  qs=practice_questions(self.student,3,[topic['skill']])
  quiz=StudentQuiz(self.student,qs);self.windows.append(quiz);quiz.resize(1200,850);quiz.show();QTest.qWait(450)
  self.assertEqual(quiz.choice_btns[0].text(),quiz.learning.current['choices'][0])
  quiz.grab().save('test_artifacts/offline_art_quiz.png')
if __name__=='__main__':unittest.main()
