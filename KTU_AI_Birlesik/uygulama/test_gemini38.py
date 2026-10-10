import json,os,unittest
from types import SimpleNamespace
from unittest.mock import Mock,patch
import teaching_materials as materials
class Gemini38Tests(unittest.TestCase):
 def setUp(self):
  self.env=patch.dict(os.environ,{'GEMINI_GENERATOR_KEY':'test-only','GEMINI_GENERATOR_MODEL':'gemini-3.8-flash','QUESTION_PROVIDER':'gemini'});self.env.start();self.addCleanup(self.env.stop)
 def client(self,side_effect=None):
  qs=[dict(text=f'What is 2 + {i}?',choices=[str(i+2),'10','11','12'],answer=0,hint='Add.',explanation='Add two to the other value.',example='2 + 2 = 4',concept='addition') for i in (3,4)]
  return SimpleNamespace(interactions=SimpleNamespace(create=Mock(return_value=SimpleNamespace(output_text=json.dumps({'questions':qs})),side_effect=side_effect)),close=Mock())
 def generate(self):return materials.generate_questions('A worksheet about adding small whole numbers. '*5,2,'Matematik','Toplama',2)
 def test_new_request_and_local_validation(self):
  c=self.client()
  with patch('google.genai.Client',return_value=c):qs=self.generate()
  args=c.interactions.create.call_args.kwargs
  self.assertEqual(args['model'],'gemini-3.8-flash');self.assertFalse(args['store']);self.assertEqual(args['timeout'],60)
  self.assertEqual(args['response_format']['mime_type'],'application/json');self.assertIn('questions',args['input'])
  self.assertEqual(len(qs),2);self.assertTrue(all(not q['verified'] for q in qs));c.close.assert_called_once()
 def check_error(self,code,word):
  error=Exception('provider error');error.status_code=code;c=self.client(error)
  with patch('google.genai.Client',return_value=c),self.assertRaisesRegex(ValueError,word):self.generate()
  c.close.assert_called_once()
 def test_missing_model_message(self):self.check_error(404,'modeli')
 def test_quota_message(self):self.check_error(429,'kotası')
if __name__=='__main__':unittest.main()
