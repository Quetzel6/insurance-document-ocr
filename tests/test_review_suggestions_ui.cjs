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

 // Regression: adding B near the top must never display it next to Amount.
 el('corrected_text').value='Currency THB\nService Synthetic repair estimate\nAmount: 86622.45';
 el('corrected_text').oninput();
 const diff=el('text_diff').children;
 assert.equal(diff.length,4);
 assert.equal(diff[1].textContent,cases[1].text,'Original block must remain intact');
 assert.equal(diff[3].textContent,el('corrected_text').value,'Corrected block must exactly match textarea');
 assert.ok(diff[3].textContent.startsWith('Currency THB\n'));
 const raw='Serwce Synthetx reper estirnate\nAmourt 55082 45\nDocument I0 SYN-117642\nDate 20260911\nน้ำหนัก 412 กรัม';
 el('corrected_text').value=raw;el('corrected_text').oninput();el('form').oninput();
 const saveCount=requests.filter(url=>url==='/api/decision').length;
 el('preview_words').onclick();
 assert.equal(el('corrected_text').value,raw,'Word preview must not edit text');
 assert.equal(el('apply_words').disabled,false);
 el('text_confirmed').checked=true;el('apply_words').onclick();
 assert.equal(el('corrected_text').value,'Service Synthetic repair estimate\nAmount 55082 45\nDocument I0 SYN-117642\nDate 20260911\nน้ำหนัก 412 กรัม');
 assert.equal(el('text_confirmed').checked,false);
 assert.equal(el('amount').value,'0.00','Word suggestions must not change fields');
 assert.equal(requests.filter(url=>url==='/api/decision').length,saveCount,'No automatic save');
 el('corrected_text').value='Arnrourt 0.00\nService repew estirnte';el('preview_words').onclick();
 el('corrected_text').value='Human edit';el('apply_words').onclick();
 assert.equal(el('corrected_text').value,'Human edit','Stale text proposal must be discarded');
 el('corrected_text').value='Amourt 123.45';el('preview_words').onclick();
 el('queue').children[0].onclick();el('apply_words').onclick();
 assert.equal(el('corrected_text').value,text('1.00'),'Switching case must invalidate proposal');
 el('corrected_text').value='XSerwce Amourt\nOther Synthetx reper estirnate\nAmount 123.45';el('preview_words').onclick();
 assert.equal(el('apply_words').disabled,true,'Unknown or embedded words must stay unchanged');
 el('corrected_text').value='Arnrourt 0.00\nService repew estirnte';el('preview_words').onclick();el('apply_words').onclick();
 assert.equal(el('corrected_text').value,'Amount 0.00\nService repair estimate');
 console.log('Word suggestions passed: explicit vocabulary, preview/apply, no digit/punctuation repair, stale text/case protection, no save.');

 el('date').value='2026-10-16';el('amount').value='86622.45';
 const unformatted='Currency THB\nDate 20261016\nAmount 86622 45';
 el('corrected_text').value=unformatted;el('corrected_text').oninput();el('form').oninput();
 el('preview_format').onclick();assert.equal(el('corrected_text').value,unformatted);
 assert.equal(el('apply_format').disabled,false);el('text_confirmed').checked=true;el('apply_format').onclick();
 assert.equal(el('corrected_text').value,'Currency THB\nDate: 2026-10-16\nAmount: 86622.45');
 assert.equal(el('amount').value,'86622.45');assert.equal(el('text_confirmed').checked,false);
 assert.equal(requests.filter(url=>url==='/api/decision').length,saveCount);
 for(const raw of ['Amount 86682 45','Amount 86622 45\nAmount unreadable','Amount -86622 45','Amount 8662245','Amount 86,622 45','Amount 86622 45 USD']){
  el('corrected_text').value=raw;el('preview_format').onclick();assert.equal(el('apply_format').disabled,true,raw);
 }
 el('corrected_text').value='Date 20260230';el('date').value='2026-02-30';el('preview_format').onclick();
 assert.equal(el('apply_format').disabled,true,'Invalid calendar date');
 el('date').value='2026-10-16';el('corrected_text').value=unformatted;el('preview_format').onclick();
 el('amount').value='1.00';el('apply_format').onclick();assert.equal(el('corrected_text').value,unformatted,'Stale field');
 el('amount').value='86622.45';el('preview_format').onclick();el('corrected_text').value='Human change';el('apply_format').onclick();
 assert.equal(el('corrected_text').value,'Human change','Stale text');
 el('corrected_text').value=unformatted;el('preview_format').onclick();el('queue').children[1].onclick();el('apply_format').onclick();
 assert.equal(el('corrected_text').value,text('2.00'),'Stale case');
 console.log('Formatting suggestions passed: matching digits only, calendar validation, ambiguity/sign/grouping rejection, preview/apply and stale guards.');
 el('queue').children[2].onclick();
 assert.equal(el('structured_fields').hidden,true);assert.equal(el('suggestion_tools').hidden,true);
 for(const key of ['document_id','date','amount']){assert.equal(el(key).disabled,true);assert.equal(el(key).required,false);assert.equal(el(key).value,'')}
 el('preview_format').onclick();assert.equal(el('apply_format').disabled,true);
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


