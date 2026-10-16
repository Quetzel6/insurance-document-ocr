'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
class Element{
 constructor(){this.value='';this.checked=false;this.disabled=false;this.hidden=false;this.textContent='';this.style={};this.children=[];this.files=[]}
 append(...children){this.children.push(...children)}
 prepend(...children){this.children.unshift(...children)}
 replaceChildren(...children){this.children=children}
}
(async()=>{
 const elements=new Map();const el=id=>{if(!elements.has(id))elements.set(id,new Element());return elements.get(id)};
 el('filter').value='all';
 const values=amount=>({document_id:'SYN-123456',date:'2026-10-16',amount});
 const text=amount=>`Document ID: SYN-123456\nDate: 2026-10-16\nAmount: ${amount}`;
 const cases=['1.00','2.00'].map((amount,i)=>({id:`case-${i}`,original:values(amount),text:text(amount),reasons:[],decision:null}));
 cases.push({id:'text-case',review_mode:'text',original:{document_id:'',date:'',amount:''},text:'น้ำหนักสุทธิ 412 กรัม',reasons:[],decision:null});
 let savedBody=null;
 let answer=async()=>({values:{document_id:null,date:null,amount:'9.00'}});const requests=[];
 const fetch=async(url,options)=>{
  requests.push(url);
  if(url==='/api/cases')return {ok:true,json:async()=>({cases,token:'token',run_id:'round',queue_kind:'uploads'})};
  if(url==='/api/suggestions'){const data=await answer();return {ok:true,json:async()=>data}}
  if(url==='/api/decision'){savedBody=JSON.parse(options.body);return {ok:true,json:async()=>({...savedBody,review_mode:'text',version:1,saved_at:'now'})}}
  throw Error(`Unexpected write: ${url}`);
 };
 const document={getElementById:el,querySelector:()=>el('main'),createElement:()=>new Element(),createTextNode:text=>({textContent:text})};
 const file=path.resolve(__dirname,'../review_ui.js');
 vm.runInNewContext(fs.readFileSync(file,'utf8'),{document,fetch,window:{addEventListener(){}},confirm:()=>true,console});
 await new Promise(setImmediate);
 assert.equal(el('amount').value,'1.00');
 await el('preview_fields').onclick();
 assert.equal(el('amount').value,'1.00','Preview must not change form values');
 assert.equal(el('apply_fields').disabled,false);
 el('text_confirmed').checked=true;el('apply_fields').onclick();
 assert.equal(el('amount').value,'9.00');assert.equal(el('document_id').value,'SYN-123456','Missing suggestion must preserve existing value');
 assert.equal(el('text_confirmed').checked,false,'Applying must require renewed human check');
 assert.equal(requests.filter(url=>url==='/api/decision').length,0,'Suggestions must never save a decision');
 let resolve;
 answer=()=>new Promise(done=>{resolve=done});
 const pending=el('preview_fields').onclick();
 el('corrected_text').value=text('7.00');el('corrected_text').oninput();el('form').oninput();
 resolve({values:{document_id:null,date:null,amount:'99.00'}});await pending;
 assert.equal(el('amount').value,'9.00');assert.equal(el('apply_fields').disabled,true,'Stale text response must be discarded');
 answer=async()=>({values:{document_id:null,date:null,amount:'7.00'}});
 await el('preview_fields').onclick();el('amount').value='8.00';el('form').oninput();el('apply_fields').onclick();
 assert.equal(el('amount').value,'8.00','Editing a field must invalidate preview');
 answer=()=>new Promise(done=>{resolve=done});
 const oldCaseRequest=el('preview_fields').onclick();
 el('queue').children[1].onclick();
 resolve({values:{document_id:null,date:null,amount:'99.00'}});await oldCaseRequest;
 assert.equal(el('amount').value,'2.00','Old case response must not affect newly selected case');
 assert.equal(el('apply_fields').disabled,true);
 answer=async()=>({values:{document_id:null,date:null,amount:'0.00'}});
 await el('preview_fields').onclick();el('apply_fields').onclick();assert.equal(el('amount').value,'0.00');
 answer=async()=>({values:{document_id:null,date:null,amount:null}});
 await el('preview_fields').onclick();assert.equal(el('apply_fields').disabled,true);
 assert.equal(el('amount').value,'0.00');
 el('queue').children[2].onclick();
 assert.equal(el('structured_fields').hidden,true);assert.equal(el('suggestion_tools').hidden,true);
 for(const key of ['document_id','date','amount']){assert.equal(el(key).disabled,true);assert.equal(el(key).required,false);assert.equal(el(key).value,'')}
 assert.equal(el('approve').textContent,'Approve text');assert.equal(el('preview_fields').disabled,true);
 el('reviewer').value='Tester';el('text_confirmed').checked=true;
 el('form').onsubmit({preventDefault(){}});await new Promise(setImmediate);
 assert.deepEqual(savedBody.values,{document_id:'',date:'',amount:''});assert.equal(savedBody.corrected_text,'น้ำหนักสุทธิ 412 กรัม');
 el('queue').children[0].onclick();
 assert.equal(el('structured_fields').hidden,false);assert.equal(el('suggestion_tools').hidden,false);
 assert.equal(el('document_id').required,true);assert.equal(el('document_id').disabled,false);assert.equal(el('approve').textContent,'Approve values');
 console.log('Mixed text/structured mode transitions passed.');
 console.log('Field suggestion UI interactions passed: preview/apply, partial/zero values, no autosave, stale text/fields/case rejection.');
})().catch(error=>{console.error(error);process.exitCode=1});

