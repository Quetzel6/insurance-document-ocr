import base64,hashlib,io,json,tempfile,threading,unittest,urllib.request,urllib.error
from pathlib import Path
from http.server import HTTPServer
from PIL import Image
from review_app import Store,validate_package,make_handler
FIELDS=('document_id','date','amount')
EMPTY=dict.fromkeys(FIELDS,'')
class GeneralReviewTests(unittest.TestCase):
 def package(self,layout='general',text='น้ำหนักสุทธิ 412 กรัม'):
  out=io.BytesIO();Image.new('RGB',(40,30),'white').save(out,format='PNG');raw=out.getvalue()
  return dict(format='ocr-review-package-v1',image_base64=base64.b64encode(raw).decode(),result=dict(source_sha256=hashlib.sha256(raw).hexdigest(),language='tha+eng',layout=layout,field_extraction_enabled=layout=='document',text=text,fields=dict.fromkeys(FIELDS,None)))
 def data(self,**changes):
  return dict(version=0,status='approved',values=EMPTY.copy(),reviewer='ผู้ตรวจ',note='',corrected_text='น้ำหนักสุทธิ 412 กรัม',text_confirmed=True)|changes
 def test_general_and_sparse_import_without_fields(self):
  for layout in ['general','sparse']:
   case,image=validate_package(self.package(layout));self.assertEqual(case['review_mode'],'text');self.assertEqual(case['layout'],layout)
   self.assertEqual(case['original'],EMPTY);self.assertEqual(case['reasons'],[]);self.assertTrue(image.startswith(b'\x89PNG'))
 def test_modes_have_separate_identity(self):
  a,_=validate_package(self.package('general'));b,_=validate_package(self.package('sparse'));c,_=validate_package(self.package('document'))
  self.assertEqual(len({a['id'],b['id'],c['id']}),3)
 def test_structured_identity_preserved(self):
  p=self.package('document');case,_=validate_package(p)
  identity=json.dumps([p['result']['source_sha256'],'tha+eng',p['result']['text'],EMPTY],sort_keys=True,ensure_ascii=False)
  self.assertEqual(case['id'],'upload-'+hashlib.sha256(identity.encode()).hexdigest());self.assertEqual(case['review_mode'],'structured')
 def test_mismatched_flags_and_smuggled_fields_rejected(self):
  p=self.package();p['result']['field_extraction_enabled']=True
  with self.assertRaises(ValueError):validate_package(p)
  p=self.package();p['result']['fields']['amount']='12.45'
  with self.assertRaises(ValueError):validate_package(p)
 def test_text_confirmation_and_nonempty_text_required(self):
  with tempfile.TemporaryDirectory() as tmp:
   store=Store(Path(tmp)/'state.db','uploads-v1')
   try:
    for data in [self.data(text_confirmed=False),self.data(corrected_text=' \n ')]:
     with self.assertRaises(ValueError):store.save('x',data,EMPTY,'น้ำหนักสุทธิ 412 กรัม',review_mode='text')
    saved=store.save('x',self.data(),EMPTY,'น้ำหนักสุทธิ 412 กรัม',review_mode='text')
    self.assertEqual(saved['review_mode'],'text');self.assertIsNone(saved['consistency']['passed']);self.assertFalse(saved['consistency']['applicable'])
   finally:store.db.close()
 def test_blank_reject_requires_reason_but_not_confirmation(self):
  with tempfile.TemporaryDirectory() as tmp:
   store=Store(Path(tmp)/'state.db','uploads-v1')
   try:
    data=self.data(status='rejected',corrected_text='',text_confirmed=False)
    with self.assertRaises(ValueError):store.save('x',data,EMPTY,'',review_mode='text')
    result=store.save('x',data|{'note':'ภาพเล็ก อ่านไม่ชัด ขอภาพใหม่'},EMPTY,'',review_mode='text');self.assertEqual(result['status'],'rejected')
   finally:store.db.close()
 def test_structured_cannot_bypass_checks_and_text_cannot_store_values(self):
  with tempfile.TemporaryDirectory() as tmp:
   store=Store(Path(tmp)/'state.db','uploads-v1')
   try:
    with self.assertRaises(ValueError):store.save('x',self.data(),EMPTY,'',review_mode='structured')
    with self.assertRaises(ValueError):store.save('x',self.data(values=EMPTY|{'amount':'12.45'}),EMPTY,'',review_mode='text')
   finally:store.db.close()
 def test_persistence_audit_reset_and_legacy_mode(self):
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'state.db';store=Store(path,'uploads-v1');case_id,created=store.import_package(self.package())
   self.assertTrue(created);self.assertFalse(store.import_package(self.package())[1]);case=store.uploaded_cases()[case_id]
   store.save(case_id,self.data(corrected_text='น้ำหนักสุทธิ 412 กรัม (ตรวจแล้ว)'),case['original'],case['text'],review_mode=case['review_mode'])
   exported=store.export();self.assertEqual(exported['documents'][0]['review_mode'],'text');self.assertEqual(exported['audit'][0]['review_mode'],'text')
   store.db.close();store=Store(path,'uploads-v1');self.assertEqual(store.get(case_id)['corrected_text'],'น้ำหนักสุทธิ 412 กรัม (ตรวจแล้ว)')
   with self.assertRaises(RuntimeError):store.save(case_id,self.data(),EMPTY,case['text'],review_mode='text')
   store.reset(store.run_id());self.assertIsNone(store.get(case_id));self.assertEqual(store.archives()[0]['export'],exported)
   self.assertEqual(store.uploaded_cases()[case_id]['review_mode'],'text')
   old_id,_=store.import_package(self.package('document'));old=store.uploaded_cases()[old_id];old.pop('review_mode');old.pop('image_bytes')
   with store.db:store.db.execute('UPDATE uploaded_documents SET payload=? WHERE id=?',(json.dumps(old),old_id))
   self.assertEqual(store.uploaded_cases()[old_id]['review_mode'],'structured');store.db.close()
 def test_http_mode_is_selected_by_stored_case(self):
  with tempfile.TemporaryDirectory() as tmp:
   ready=threading.Event();state={}
   def serve():
    store=Store(Path(tmp)/'state.db','uploads-v1');server=HTTPServer(('127.0.0.1',0),make_handler({},store,'secret',0,True))
    server.RequestHandlerClass=make_handler({},store,'secret',server.server_port,True);state['server']=server;ready.set()
    try:server.serve_forever()
    finally:server.server_close();store.db.close()
   thread=threading.Thread(target=serve);thread.start();self.assertTrue(ready.wait(3));base=f"http://127.0.0.1:{state['server'].server_port}"
   def get(path):
    with urllib.request.urlopen(base+path,timeout=3) as r:return json.load(r)
   def post(path,payload):
    request=urllib.request.Request(base+path,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','X-Review-Token':'secret'})
    with urllib.request.urlopen(request,timeout=3) as r:return json.load(r)
   try:
    run_id=get('/api/cases')['run_id'];general=post('/api/import',dict(run_id=run_id,package=self.package()))['id']
    doc=post('/api/import',dict(run_id=run_id,package=self.package('document')))['id']
    rows=get('/api/cases')['cases'];self.assertEqual(next(r for r in rows if r['id']==general)['review_mode'],'text')
    saved=post('/api/decision',self.data()|dict(run_id=run_id,id=general,review_mode='structured'));self.assertEqual(saved['review_mode'],'text')
    for path,data in [('/api/decision',self.data()|dict(run_id=run_id,id=doc,review_mode='text')),('/api/suggestions',dict(run_id=run_id,id=general,corrected_text='Amount: 12.45'))]:
     with self.assertRaises(urllib.error.HTTPError) as error:post(path,data)
     self.assertEqual(error.exception.code,400)
    exported=get('/api/export');self.assertEqual(exported['audit'][0]['review_mode'],'text')
   finally:state['server'].shutdown();thread.join(3)
