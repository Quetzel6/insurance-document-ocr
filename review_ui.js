'use strict';
const consistencyNotice=document.createElement('p');
consistencyNotice.className='notice';
consistencyNotice.textContent='v0.7: Approval requires matching Document ID, Date and Amount lines in corrected text and the three fields. DocumentID is also accepted. Example: Amount: 123.45. No digits are guessed. Matching values can still be wrong; verify the image. Older approvals were not checked retroactively.';
document.querySelector('main').prepend(consistencyNotice);
const $=id=>document.getElementById(id);
let cases=[],token='',runId='',current=null,dirty=false;
let suggestion=null,suggestionRevision=0;
let wordSuggestion=null,formatSuggestion=null;
const fields=['document_id','date','amount'];
const status=c=>c.decision?c.decision.status:'pending';
function renderQueue(){
 const filter=$('filter').value;
 $('counts').textContent=`${cases.filter(c=>status(c)==='pending').length} pending · ${cases.filter(c=>status(c)==='approved').length} approved · ${cases.filter(c=>status(c)==='rejected').length} rejected`;
 $('queue').replaceChildren();
 const visible=cases.filter(c=>filter==='all'||(filter==='invalid'?c.reasons.length>0:status(c)===filter));
 visible.sort((a,b)=>b.reasons.length-a.reasons.length);
 for(const c of visible){const b=document.createElement('button');b.textContent=`${c.id} · ${status(c)}${c.reasons.length?' ⚑':''}`;b.className=current&&c.id===current.id?'active':'';b.onclick=()=>{if(!dirty||confirm('Discard unsaved changes?'))select(c)};$('queue').append(b)}
 if(!visible.length)$('queue').textContent='No cases in this filter.';
}
function select(c){$('image').hidden=false;current=c;clearSuggestions();
 const textOnly=c.review_mode==='text';
 $('structured_fields').hidden=textOnly;$('suggestion_tools').hidden=textOnly;
 for(const k of fields){$(k).disabled=textOnly;$(k).required=!textOnly}
 $('approve').textContent=textOnly?'Approve text':'Approve values';
 $('confirmation_help').textContent=textOnly?'ตรวจข้อความทั้งหมดกับภาพและติ๊กยืนยันทุกครั้งก่อน Approve text หากอ่านไม่ได้ให้ Reject พร้อมเหตุผล':'Required to approve changed text. If unreadable, reject with a reason.';
 consistencyNotice.textContent=textOnly?'ตรวจเฉพาะข้อความ: ไม่ใช้ ID / Date / Amount ผล OCR อาจผิดได้ โปรดตรวจภาพก่อนอนุมัติ ไม่รองรับการแปลงตารางเป็นเซลล์':'Approval requires matching ID, Date and Amount in text and fields. DocumentID is accepted. Verify all values against the image.';dirty=false;$('title').textContent=c.id;$('image').src='/image/'+encodeURIComponent(c.id);$('ocr').textContent=c.text;
 const d=c.decision;for(const k of fields)$(k).value=textOnly?'':(d?d.values:c.original)[k];
 $('corrected_text').value=d&&typeof d.corrected_text==='string'?d.corrected_text:c.text; $('text_confirmed').checked=!!(d&&d.text_confirmed); renderDiff();
 $('note').value=d?d.note:'';if(d)$('reviewer').value=d.reviewer;
 $('reasons').textContent=textOnly?'โหมดตรวจข้อความทั่วไป — แก้ข้อความจากภาพ ไม่ต้องกรอก ID / Date / Amount':c.reasons.length?'Original prediction flags: '+c.reasons.join(' '):'Original prediction passes format checks. Inspect every field against the image.';
 $('original').textContent='Original prediction: '+fields.map(k=>`${k}: ${c.original[k]||'(missing)'}`).join(' · ');
 $('history').textContent=d?`${d.status} · version ${d.version}\n${d.reviewer} · ${d.saved_at}\n${d.note}`:'None';$('message').textContent='';renderQueue();
}
async function save(decision){if(!current)return;if(!$('reviewer').value.trim()){ $('message').textContent='Enter reviewer name.';return;}
 const body={run_id:runId,id:current.id,version:current.decision?current.decision.version:0,status:decision,reviewer:$('reviewer').value,note:$('note').value,corrected_text:$('corrected_text').value,text_confirmed:$('text_confirmed').checked,values:Object.fromEntries(fields.map(k=>[k,$(k).value]))};
 try{const r=await fetch('/api/decision',{method:'POST',headers:{'Content-Type':'application/json','X-Review-Token':token},body:JSON.stringify(body)});const d=await r.json();if(!r.ok)throw Error(d.error);current.decision=d;select(current);$('message').style.color='#176759';$('message').textContent='Decision saved. Select another case to continue.'}catch(e){$('message').style.color='#8c2d2d';$('message').textContent=e.message}
}
$('form').onsubmit=e=>{e.preventDefault();save('approved')};$('reject').onclick=()=>save('rejected');$('form').oninput=()=>{dirty=true;clearSuggestions()}; $('corrected_text').oninput=()=>{dirty=true;$('text_confirmed').checked=false;renderDiff()};$('filter').onchange=renderQueue;
window.addEventListener('beforeunload',e=>{if(dirty){e.preventDefault();e.returnValue=''}});
(async()=>{try{const r=await fetch('/api/cases');if(!r.ok)throw Error('Could not load queue');const d=await r.json();cases=d.cases;token=d.token;runId=d.run_id;$('import_label').hidden=d.queue_kind!=='uploads';$('import_help').hidden=d.queue_kind!=='uploads';renderQueue();if(!cases.length)$('title').textContent='นำเข้าชุดส่งตรวจจาก Image Reader เพื่อเริ่มต้น';if(cases.length)select([...cases].sort((a,b)=>b.reasons.length-a.reasons.length)[0]);}catch(e){$('title').textContent=e.message}})();

function renderDiff(){
 const a=current.text,b=$('corrected_text').value,out=$('text_diff');out.replaceChildren();
 if(a===b){out.textContent='No text changes.';return}
 // Keep complete before/after blocks: multi-line edits must not splice unrelated lines.
 out.append(document.createTextNode('ก่อนแก้ / Original OCR\n'));
 const removed=document.createElement('del');removed.textContent=a;out.append(removed);
 out.append(document.createTextNode('\n\nหลังแก้ / Corrected OCR\n'));
 const added=document.createElement('ins');added.textContent=b;out.append(added);
}

$('reset_round').onclick=async()=>{
 if(!confirm('เริ่มรอบตรวจใหม่? ระบบจะเก็บผลและประวัติรอบเดิมไว้ แล้วให้ทุกรายการในคิวนี้กลับเป็น Pending ส่วนที่ยังไม่บันทึกจะถูกทิ้ง'))return;
 $('reset_round').disabled=true;
 try{const r=await fetch('/api/reset',{method:'POST',headers:{'Content-Type':'application/json','X-Review-Token':token},body:JSON.stringify({run_id:runId})});const d=await r.json();if(!r.ok)throw Error(d.error);dirty=false;location.reload()}catch(e){$('message').textContent=e.message;$('reset_round').disabled=false}
};


$('import_file').onchange=async()=>{
 const file=$('import_file').files[0];if(!file)return;
 if(dirty&&!confirm('Discard unsaved changes?')){$('import_file').value='';return}
 $('import_file').disabled=true;$('import_status').style.color='#173953';$('import_status').textContent='กำลังตรวจและนำเข้าชุดส่งตรวจ…';
 try{
  if(file.size>15*1024*1024)throw Error('ชุดส่งตรวจต้องไม่เกิน 15 MiB');
  if(!file.name.toLowerCase().endsWith('.json'))throw Error('ช่องนี้รับชุดส่งตรวจ .json เท่านั้น กรุณาอ่านภาพที่พอร์ต 8766 แล้วกดดาวน์โหลดชุดส่งตรวจ');
  let packageData;try{packageData=JSON.parse(await file.text())}catch{throw Error('อ่าน JSON ไม่ได้ กรุณาดาวน์โหลดชุดส่งตรวจใหม่จากพอร์ต 8766')}
  if(!packageData||packageData.format!=='ocr-review-package-v1'||!packageData.image_base64||!packageData.result)throw Error('ไฟล์นี้ไม่ใช่ชุดส่งตรวจ กรุณาไปพอร์ต 8766 แล้วกด “ดาวน์โหลดชุดส่งตรวจ” ใช้ไฟล์ ocr-review-package.json ไม่ใช่ผล JSON หรือประวัติ decisions');
  if(!['document','general','sparse'].includes(packageData.result.layout))throw Error('รูปแบบภาพไม่รองรับ กรุณาสร้างชุดส่งตรวจใหม่ที่พอร์ต 8766');
  const r=await fetch('/api/import',{method:'POST',headers:{'Content-Type':'application/json','X-Review-Token':token},body:JSON.stringify({run_id:runId,package:packageData})});
  const d=await r.json();if(!r.ok)throw Error(d.error);
  const response=await fetch('/api/cases');if(!response.ok)throw Error('Cannot refresh queue');
  const queue=await response.json();cases=queue.cases;token=queue.token;runId=queue.run_id;
  $('filter').value='all';select(cases.find(c=>c.id===d.id));
  $('import_status').textContent=d.created?'นำเข้าแล้ว — ตรวจภาพก่อนอนุมัติ':'มีชุดนี้แล้ว — เปิดรายการเดิม';
 }catch(e){$('import_status').style.color='#8c2d2d';$('import_status').textContent=e.message}
 finally{$('import_file').disabled=false;$('import_file').value=''}
};


function clearSuggestions(){
 clearFormatSuggestions();
 clearWordSuggestions();
 suggestion=null;suggestionRevision++;
 $('apply_fields').disabled=true;$('preview_fields').disabled=!current||current.review_mode==='text';
 $('suggest_preview').hidden=true;$('suggest_preview').textContent='';$('suggest_status').textContent='';
}
$('preview_fields').onclick=async()=>{
 if(!current||current.review_mode==='text')return;
 clearSuggestions();
 const revision=suggestionRevision,caseId=current.id,text=$('corrected_text').value;
 const before=Object.fromEntries(fields.map(k=>[k,$(k).value]));
 $('preview_fields').disabled=true;$('suggest_status').textContent='กำลังตรวจข้อความเพื่อเสนอค่า…';
 try{
  const response=await fetch('/api/suggestions',{method:'POST',headers:{'Content-Type':'application/json','X-Review-Token':token},body:JSON.stringify({run_id:runId,id:caseId,corrected_text:text})});
  const data=await response.json();
  if(revision!==suggestionRevision||!current||current.id!==caseId||$('corrected_text').value!==text)return;
  if(!response.ok)throw Error(data.error);
  suggestion={caseId,text,before,values:data.values,revision};
  const names={document_id:'Document ID',date:'Date',amount:'Amount'};
  $('suggest_preview').textContent=fields.map(k=>`${names[k]}: ${before[k]||'(ว่าง)'} → ${data.values[k]===null?'ไม่พบ/กำกวม — คงค่าเดิม':data.values[k]}`).join('\n');
  $('suggest_preview').hidden=false;
  const found=fields.filter(k=>data.values[k]!==null);
  $('apply_fields').disabled=found.length===0;
  $('suggest_status').textContent=found.length?'ตรวจค่าที่เสนอกับภาพ แล้วกดใช้ค่า ช่องที่ไม่พบจะไม่ถูกล้าง':'ไม่พบค่าที่ชัดเจน กรุณาแก้ข้อความจากภาพ หรือ Reject หากอ่านไม่ได้';
 }catch(error){if(revision===suggestionRevision)$('suggest_status').textContent=error.message}
 finally{if(revision===suggestionRevision)$('preview_fields').disabled=!current||current.review_mode==='text'}
};
$('apply_fields').onclick=()=>{
 if(!suggestion||!current)return;
 const proposal=suggestion;
 if(proposal.revision!==suggestionRevision||proposal.caseId!==current.id||proposal.text!==$('corrected_text').value||fields.some(k=>proposal.before[k]!==$(k).value)){
  clearSuggestions();$('suggest_status').textContent='ข้อมูลเปลี่ยนแล้ว กรุณากดเสนอค่าใหม่';return;
 }
 for(const k of fields)if(proposal.values[k]!==null)$(k).value=proposal.values[k];
 dirty=true;$('text_confirmed').checked=false;clearSuggestions();
 $('suggest_status').textContent='เติมค่าที่พบแล้ว ยังไม่ได้บันทึก — ตรวจภาพและยืนยันข้อความก่อน Approve';
};


// Small, explicit vocabulary only. Numeric values and punctuation stay untouched.
function proposeWords(text){
 const changes=[];
 const replace=(pattern,replacement)=>{text=text.replace(pattern,(whole,prefix,word)=>{
  changes.push(`${word} → ${replacement}`);return prefix+replacement;
 })};
 replace(/^([ \t]*)(amourt|arnrourt)(?=[ \t:])/gim,'Amount');
 replace(/^([ \t]*)(serwce)(?=[ \t:])/gim,'Service');
 text=text.replace(/^([ \t]*Service[^\r\n]*)$/gim,line=>{
  return line.replace(/\b(Synthetx)\b/gi,word=>{
   changes.push(`${word} → Synthetic`);return 'Synthetic';
  }).replace(/\b(reper|repew)\b(?=[ \t]+(?:estimate|estirnate|estirnte)\b)/gi,word=>{
   changes.push(`${word} → repair`);return 'repair';
  }).replace(/\b(estirnate|estirnte)\b/gi,word=>{
   changes.push(`${word} → estimate`);return 'estimate';
  });
 });
 return {text,changes};
}
function clearWordSuggestions(){
 wordSuggestion=null;$('apply_words').disabled=true;
 $('word_preview').hidden=true;$('word_preview').textContent='';$('word_status').textContent='';
}
$('preview_words').onclick=()=>{
 clearWordSuggestions();if(!current)return;
 const before=$('corrected_text').value,proposal=proposeWords(before);
 if(!proposal.changes.length){$('word_status').textContent='ไม่พบคำในรายการที่เสนอแก้ได้ ตัวเลขและคำอื่นต้องตรวจจากภาพ';return}
 wordSuggestion={caseId:current.id,before,after:proposal.text};
 $('word_preview').textContent=proposal.changes.join('\n')+'\n\n'+proposal.text;
 $('word_preview').hidden=false;$('apply_words').disabled=false;
 $('word_status').textContent='ตรวจคำที่เสนอกับภาพก่อนใช้ ยังไม่แก้ข้อความหรือบันทึก';
};
$('apply_words').onclick=()=>{
 if(!wordSuggestion||!current)return;
 const proposal=wordSuggestion;
 if(proposal.caseId!==current.id||proposal.before!==$('corrected_text').value){clearWordSuggestions();return}
 $('corrected_text').value=proposal.after;dirty=true;$('text_confirmed').checked=false;
 clearSuggestions();renderDiff();
 $('word_status').textContent='ใช้ข้อความที่เสนอแล้ว — ตัวเลขคงเดิม ตรวจภาพและยืนยันก่อนอนุมัติ ยังไม่ได้บันทึก';
};


// Review assistance only: format existing digits using explicitly supplied field values.
function proposeFormats(text,values){
 const changes=[],skipped=[];
 const lines=text.split('\n');
 const specs=[
  {key:'document_id',label:/^\s*Document[ \t]*(?:ID|I0|IO|1D)\b/i,
   whole:/^(\s*Document[ \t]*(?:ID|I0|IO|1D))\s*:?\s*(SYN(?:[ \t]*[-.][ \t]*|[ \t]+)[0-9](?:[0-9 ]*[0-9])?)\s*$/i,
   canonical:/^SYN-[0-9]{6}$/},
  {key:'date',label:/^\s*Date\b/i,whole:/^(\s*Date)\s*:?\s*([0-9]{4}-?[0-9]{2}-?[0-9]{2})\s*$/i,
   canonical:/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/},
  {key:'amount',label:/^\s*(?:Amount|Amourt|Arnrourt|Ammourt)\b/i,
   whole:/^(\s*(?:Amount|Amourt|Arnrourt|Ammourt))\s*:?\s*([0-9]{1,12}(?:\.[0-9]{2}|[ \t]+[0-9]{2}))\s*$/i,
   canonical:/^[0-9]{1,12}\.[0-9]{2}$/}
 ];
 for(const spec of specs){
  const indexes=lines.map((line,i)=>spec.label.test(line)?i:-1).filter(i=>i>=0);
  if(!indexes.length)continue;
  const value=values[spec.key];
  if(indexes.length!==1||!spec.canonical.test(value)){skipped.push(spec.key);continue}
  if(spec.key==='date'){
   const parsed=new Date(value+'T00:00:00Z');
   if(value.startsWith('0000')||!Number.isFinite(parsed.getTime())||parsed.toISOString().slice(0,10)!==value){skipped.push(spec.key);continue}
  }
  const i=indexes[0],match=lines[i].match(spec.whole);
  if(!match||match[2].replace(/[^0-9]/g,'')!==value.replace(/[^0-9]/g,'')){
   skipped.push(spec.key);continue;
  }
  const after=({document_id:'Document ID: ',date:'Date: ',amount:'Amount: '})[spec.key]+value;
  if(lines[i]!==after){changes.push(lines[i]+' → '+after);lines[i]=after}
 }
 return {text:lines.join('\n'),changes,skipped};
}
function clearFormatSuggestions(){
 formatSuggestion=null;$('apply_format').disabled=true;
 $('format_preview').hidden=true;$('format_preview').textContent='';$('format_status').textContent='';
}
$('preview_format').onclick=()=>{
 clearFormatSuggestions();if(!current||current.review_mode==='text')return;
 const before=$('corrected_text').value,values=Object.fromEntries(fields.map(k=>[k,$(k).value.trim()]));
 const proposal=proposeFormats(before,values);
 $('format_status').textContent=proposal.skipped.length?'ข้ามช่องที่ว่าง กำกวม รูปแบบไม่รองรับ หรือลำดับตัวเลขไม่ตรง: '+proposal.skipped.join(', '):'ตรวจค่ากับภาพก่อนใช้ ไม่มีการอ่านภาพซ้ำหรือยืนยันว่าตัวเลขถูก';
 if(!proposal.changes.length){$('format_status').textContent+=' — ไม่มีรูปแบบที่เสนอแก้ได้';return}
 formatSuggestion={caseId:current.id,before,values,after:proposal.text};
 $('format_preview').textContent=proposal.changes.join('\n');$('format_preview').hidden=false;$('apply_format').disabled=false;
};
$('apply_format').onclick=()=>{
 if(!formatSuggestion||!current||current.review_mode==='text')return;
 const p=formatSuggestion;
 if(p.caseId!==current.id||p.before!==$('corrected_text').value||fields.some(k=>p.values[k]!==$(k).value.trim())){clearFormatSuggestions();return}
 $('corrected_text').value=p.after;dirty=true;$('text_confirmed').checked=false;
 clearSuggestions();renderDiff();$('format_status').textContent='จัดรูปแบบแล้ว ยังไม่ได้บันทึก ตรวจข้อความและตัวเลขกับภาพก่อนยืนยันและ Approve';
};

