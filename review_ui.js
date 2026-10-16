'use strict';
const consistencyNotice=document.createElement('p');
consistencyNotice.className='notice';
consistencyNotice.textContent='v0.7: Approval requires matching Document ID, Date and Amount lines in corrected text and the three fields. Example: Amount: 123.45. No digits are guessed. Matching values can still be wrong; verify the image. Older approvals were not checked retroactively.';
document.querySelector('main').prepend(consistencyNotice);
const $=id=>document.getElementById(id);
let cases=[],token='',runId='',current=null,dirty=false;
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
function select(c){$('image').hidden=false;current=c;dirty=false;$('title').textContent=c.id;$('image').src='/image/'+encodeURIComponent(c.id);$('ocr').textContent=c.text;
 const d=c.decision;for(const k of fields)$(k).value=(d?d.values:c.original)[k];
 $('corrected_text').value=d&&typeof d.corrected_text==='string'?d.corrected_text:c.text; $('text_confirmed').checked=!!(d&&d.text_confirmed); renderDiff();
 $('note').value=d?d.note:'';if(d)$('reviewer').value=d.reviewer;
 $('reasons').textContent=c.reasons.length?'Original prediction flags: '+c.reasons.join(' '):'Original prediction passes format checks. Inspect every field against the image.';
 $('original').textContent='Original prediction: '+fields.map(k=>`${k}: ${c.original[k]||'(missing)'}`).join(' · ');
 $('history').textContent=d?`${d.status} · version ${d.version}\n${d.reviewer} · ${d.saved_at}\n${d.note}`:'None';$('message').textContent='';renderQueue();
}
async function save(decision){if(!current)return;if(!$('reviewer').value.trim()){ $('message').textContent='Enter reviewer name.';return;}
 const body={run_id:runId,id:current.id,version:current.decision?current.decision.version:0,status:decision,reviewer:$('reviewer').value,note:$('note').value,corrected_text:$('corrected_text').value,text_confirmed:$('text_confirmed').checked,values:Object.fromEntries(fields.map(k=>[k,$(k).value]))};
 try{const r=await fetch('/api/decision',{method:'POST',headers:{'Content-Type':'application/json','X-Review-Token':token},body:JSON.stringify(body)});const d=await r.json();if(!r.ok)throw Error(d.error);current.decision=d;select(current);$('message').style.color='#176759';$('message').textContent='Decision saved. Select another case to continue.'}catch(e){$('message').style.color='#8c2d2d';$('message').textContent=e.message}
}
$('form').onsubmit=e=>{e.preventDefault();save('approved')};$('reject').onclick=()=>save('rejected');$('form').oninput=()=>dirty=true; $('corrected_text').oninput=()=>{dirty=true;$('text_confirmed').checked=false;renderDiff()};$('filter').onchange=renderQueue;
window.addEventListener('beforeunload',e=>{if(dirty){e.preventDefault();e.returnValue=''}});
(async()=>{try{const r=await fetch('/api/cases');if(!r.ok)throw Error('Could not load queue');const d=await r.json();cases=d.cases;token=d.token;runId=d.run_id;$('import_label').hidden=d.queue_kind!=='uploads';$('import_help').hidden=d.queue_kind!=='uploads';renderQueue();if(!cases.length)$('title').textContent='นำเข้าชุดส่งตรวจจาก Image Reader เพื่อเริ่มต้น';if(cases.length)select([...cases].sort((a,b)=>b.reasons.length-a.reasons.length)[0]);}catch(e){$('title').textContent=e.message}})();

function renderDiff(){
 const a=current.text,b=$('corrected_text').value,out=$('text_diff');out.replaceChildren();
 if(a===b){out.textContent='No text changes.';return}
 let start=0,endA=a.length,endB=b.length;
 while(start<endA&&start<endB&&a[start]===b[start])start++;
 while(endA>start&&endB>start&&a[endA-1]===b[endB-1]){endA--;endB--}
 out.append(document.createTextNode(a.slice(0,start)));
 const removed=document.createElement('del');removed.textContent=a.slice(start,endA);out.append(removed);
 const added=document.createElement('ins');added.textContent=b.slice(start,endB);out.append(added);
 out.append(document.createTextNode(a.slice(endA)));
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
  if(packageData.result.layout!=='document')throw Error('คิวนี้รองรับโหมดเอกสาร ID / Date / Amount กรุณาเลือกโหมดนี้และอ่าน OCR ใหม่ที่พอร์ต 8766');
  const r=await fetch('/api/import',{method:'POST',headers:{'Content-Type':'application/json','X-Review-Token':token},body:JSON.stringify({run_id:runId,package:packageData})});
  const d=await r.json();if(!r.ok)throw Error(d.error);
  const response=await fetch('/api/cases');if(!response.ok)throw Error('Cannot refresh queue');
  const queue=await response.json();cases=queue.cases;token=queue.token;runId=queue.run_id;
  $('filter').value='all';select(cases.find(c=>c.id===d.id));
  $('import_status').textContent=d.created?'นำเข้าแล้ว — ตรวจภาพก่อนอนุมัติ':'มีชุดนี้แล้ว — เปิดรายการเดิม';
 }catch(e){$('import_status').style.color='#8c2d2d';$('import_status').textContent=e.message}
 finally{$('import_file').disabled=false;$('import_file').value=''}
};
