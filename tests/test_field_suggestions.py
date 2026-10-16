import json,tempfile,threading,unittest,urllib.request,urllib.error
from pathlib import Path
from http.server import HTTPServer
from review_suggestions import suggest_fields
from review_consistency import check_consistency
from review_app import Store,make_handler
TEXT='DocumentID: SYN-123456\nDate: 2026-10-16\nAmount: 10425.45'
VALUES=dict(document_id='SYN-123456',date='2026-10-16',amount='10425.45')
class SuggestionTests(unittest.TestCase):
 def test_joined_label_and_consistency_agree(self):
  self.assertEqual(suggest_fields(TEXT)['values'],VALUES)
  self.assertTrue(check_consistency(TEXT,VALUES)['passed'])
 def test_invalid_dates_and_missing_decimals_are_not_guessed(self):
  values=suggest_fields('DocumentID: SYN-12345O\nDate: 2026-02-30\nAmount: 10425 45')['values']
  self.assertTrue(all(v is None for v in values.values()))
 def test_duplicates_even_invalid_are_not_suggested(self):
  for extra in ['\nDocument ID: SYN-654321','\nDocumentID: unreadable']:
   self.assertIsNone(suggest_fields(TEXT+extra)['values']['document_id'])
  self.assertIsNone(suggest_fields(TEXT+'\nAmount: unreadable')['values']['amount'])
 def test_no_digit_substitutions_or_partial_matches(self):
  for value in ['12.456','12.45 USD','1,234.56','-12.45','12.OO']:
   self.assertIsNone(suggest_fields('Amount: '+value)['values']['amount'])
 def test_non_label_text_does_not_match(self):
  self.assertIsNone(suggest_fields('Account DocumentID: SYN-123456')['values']['document_id'])
 def test_partial_suggestion_preserves_missing_as_none(self):
  r=suggest_fields('Amount: 0.00')
  self.assertEqual(r['values'],dict(document_id=None,date=None,amount='0.00'))
  self.assertEqual(set(r['missing_or_ambiguous']),{'document_id','date'})
 def test_type_and_length_limits(self):
  for text in [None,[],1,'x'*10001]:
   with self.assertRaises(ValueError):suggest_fields(text)
 def test_legacy_spaced_label_remains_accepted(self):
  self.assertTrue(check_consistency(TEXT.replace('DocumentID','Document ID'),VALUES)['passed'])
 def test_apply_requires_explicit_save_and_preserves_original(self):
  with tempfile.TemporaryDirectory() as tmp:
   store=Store(Path(tmp)/'state.db','test')
   try:
    original=dict(document_id='',date='',amount='');raw='OCR unreadable'
    proposed=suggest_fields(TEXT)['values'];self.assertIsNone(store.get('case'))
    data=dict(version=0,status='approved',values=proposed,reviewer='Test',note='',corrected_text=TEXT,text_confirmed=False)
    with self.assertRaises(ValueError):store.save('case',data,original,raw)
    saved=store.save('case',data|{'text_confirmed':True},original,raw)
    self.assertEqual(saved['original'],original);self.assertEqual(saved['original_text'],raw)
    self.assertEqual(saved['corrected_text'],TEXT);self.assertTrue(saved['consistency']['passed'])
    self.assertEqual(len(store.export()['audit']),1)
   finally:store.db.close()
 def test_http_read_only_and_authorization(self):
  with tempfile.TemporaryDirectory() as tmp:
   ready=threading.Event();state={}
   def serve():
    store=Store(Path(tmp)/'state.db','test')
    cases={'case':dict(id='case',original=VALUES,text=TEXT,reasons=[])}
    server=HTTPServer(('127.0.0.1',0),make_handler(cases,store,'secret',0))
    server.RequestHandlerClass=make_handler(cases,store,'secret',server.server_port)
    state['server']=server;ready.set()
    try:server.serve_forever()
    finally:server.server_close();store.db.close()
   thread=threading.Thread(target=serve);thread.start();self.assertTrue(ready.wait(3))
   base=f"http://127.0.0.1:{state['server'].server_port}"
   def get(path):
    with urllib.request.urlopen(base+path,timeout=3) as response:return json.load(response)
   def post(payload,token='secret'):
    req=urllib.request.Request(base+'/api/suggestions',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','X-Review-Token':token})
    with urllib.request.urlopen(req,timeout=3) as response:return json.load(response)
   try:
    before=get('/api/export');run_id=before['run_id'];payload=dict(run_id=run_id,id='case',corrected_text=TEXT)
    self.assertEqual(post(payload)['values'],VALUES);self.assertEqual(before,get('/api/export'))
    for body,token,status in [(payload,'wrong',403),(payload|{'run_id':'old'},'secret',409),(payload|{'id':'missing'},'secret',400),(payload|{'corrected_text':None},'secret',400)]:
     with self.assertRaises(urllib.error.HTTPError) as error:post(body,token)
     self.assertEqual(error.exception.code,status)
   finally:state['server'].shutdown();thread.join(3)
