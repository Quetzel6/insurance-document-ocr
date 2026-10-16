'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
class Element{
 constructor(){this.value='';this.disabled=false;this.hidden=false;this.textContent='';this.files=[];this.style={}}
 querySelector(){return new Element()}
 removeAttribute(name){delete this[name]}
 click(){}
}
(async()=>{
 const elements=new Map();const el=id=>{if(!elements.has(id))elements.set(id,new Element());return elements.get(id)};
 const blobs=[];const URL={createObjectURL(blob){blobs.push(blob);return 'blob:'+blobs.length},revokeObjectURL(){}};
 const document={getElementById:el,createElement:()=>new Element()};
 const fetch=async(url,options)=>{
  if(url==='/api/session')return {ok:true,json:async()=>({token:'token',languages:['eng','tha']})};
  assert.equal(url,'/api/read');const layout=options.headers['X-OCR-Layout'];
  return {ok:true,json:async()=>({layout,language:'tha+eng',field_extraction_enabled:layout==='document',fields:layout==='document'?{document_id:'SYN-123456',date:'2026-10-16',amount:'12.45'}:{document_id:null,date:null,amount:null},text:'น้ำหนักสุทธิ 412 กรัม',source_sha256:'test-hash',timing_seconds:{total:0.1}})};
 };
 vm.runInNewContext(fs.readFileSync(path.resolve(__dirname,'../image_reader.js'),'utf8'),{
  document,fetch,URL,Blob,btoa:value=>Buffer.from(value,'binary').toString('base64'),performance:{now:()=>0},setInterval:()=>1,clearInterval(){},setTimeout(){},console
 });
 await new Promise(setImmediate);
 el('language').value='tha+eng';el('file').files=[{name:'label.png',size:3,arrayBuffer:async()=>new Uint8Array([1,2,3]).buffer}];
 el('file').onchange();
 for(const layout of ['general','sparse','document']){
  el('layout').value=layout;el('layout').onchange();assert.equal(el('review_package').disabled,true);
  await el('read').onclick();assert.equal(el('review_package').disabled,false,`${layout} must allow review package download`);
  await el('review_package').onclick();
  const payload=JSON.parse(await blobs.at(-1).text());assert.equal(payload.format,'ocr-review-package-v1');assert.equal(payload.result.layout,layout);
  assert.equal(payload.image_base64,'AQID');assert.equal(payload.result.field_extraction_enabled,layout==='document');
 }
 el('reset').onclick();assert.equal(el('review_package').disabled,true);
 console.log('Reader package interactions passed: general/sparse/document downloads and reset.');
})().catch(error=>{console.error(error);process.exitCode=1});
