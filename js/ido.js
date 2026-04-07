// ===== IDO-GEIKO =====
let currentIdoBelt='branca';

function initIdo(){
const tabs=document.getElementById('ido-belts');tabs.innerHTML='';
Object.keys(BELT_REQ).forEach(b=>{
  const btn=document.createElement('button');
  btn.className='ib-tab'+(b===currentIdoBelt?' on':'');
  btn.textContent=b;
  btn.onclick=()=>{currentIdoBelt=b;initIdo()};
  tabs.appendChild(btn);
});
const req=BELT_REQ[currentIdoBelt];
document.getElementById('ido-req').innerHTML=
  '<div class="req-box"><strong>Requisitos — Faixa '+currentIdoBelt.toUpperCase()+'</strong>'+
  '<div>'+req.exam+'</div>'+
  '<div style="margin-top:6px;font-size:11px">Ido-Geiko: '+req.ido+(req.min?'&nbsp;&nbsp;<span style=\"color:var(--gold)\">min. '+req.min+' golpes</span>':'')+'</div>'+
  '</div>';
document.getElementById('ido-out').innerHTML='';
const _sl=document.getElementById('ido-nblocks');
const _sv=document.getElementById('ido-nblocks-val');
if(_sl){
  const defs={branca:3,laranja:3,azul:4,amarela:4,verde:5,marrom:6,shodan:8};
  _sl.value=defs[currentIdoBelt]||4;
  _sv.textContent=_sl.value;
  const beltIdxEst=Object.keys(BELT_REQ).indexOf(currentIdoBelt);
  const poolEst=RENRAKU.filter(r=>Object.keys(BELT_REQ).indexOf(r.belt)<=beltIdxEst);
  const avgSteps=poolEst.length?poolEst.reduce((s,r)=>s+r.steps.length,0)/poolEst.length:4;
  const _se=document.getElementById('ido-est');
  function _updateEst(){if(_se)_se.textContent='~'+Math.round(parseInt(_sl.value)*avgSteps)+' golpes';}
  _sl.oninput=()=>{_sv.textContent=_sl.value;_updateEst();};
  _updateEst();
}
}

// Classify a renraku block: 'geri' if foot-dominant, 'te' if hand-dominant, 'misto' otherwise
function _renrakuCat(r){
  const g=(r.name.match(/\b(Geri|Keage)\b/gi)||[]).length;
  const t=(r.name.match(/\b(Tsuki|Uchi|Uke|Barai|Empi|Uraken|Tettsui|Shuto|Shotei|Nukite|Hiza)\b/gi)||[]).length;
  return g>t?'geri':t>g?'te':'misto';
}

function generateIdo(){
const beltIdx=Object.keys(BELT_REQ).indexOf(currentIdoBelt);
const pool=RENRAKU.filter(r=>Object.keys(BELT_REQ).indexOf(r.belt)<=beltIdx);
if(!pool.length){document.getElementById('ido-out').innerHTML='<div style="color:var(--text2);font-size:13px">Sem renraku disponíveis.</div>';return;}
const _sl=document.getElementById('ido-nblocks');
let nBlocks=_sl?Math.max(3,Math.min(12,parseInt(_sl.value,10)||4)):4;
const req=BELT_REQ[currentIdoBelt];
const minGoals=req.min||0;

// Smart selection: shuffle, avoid consecutive same id, ensure ≥1 geri + ≥1 te if pool allows
const shuffled=[...pool].sort(()=>Math.random()-.5);
let blocks=[];
for(let i=0;i<shuffled.length&&blocks.length<nBlocks;i++){
  const r=shuffled[i];
  // avoid back-to-back duplicate
  if(blocks.length>0&&blocks[blocks.length-1].id===r.id)continue;
  blocks.push(r);
}
// If we couldn't fill nBlocks (tiny pool), fall back
if(blocks.length<nBlocks){
  const extra=shuffled.filter(r=>!blocks.includes(r));
  blocks=[...blocks,...extra].slice(0,nBlocks);
}
// Ensure balance: if no geri block and pool has geri, swap one in
const hasGeri=blocks.some(r=>_renrakuCat(r)==='geri');
const hasTe=blocks.some(r=>_renrakuCat(r)==='te');
if(!hasGeri){
  const g=shuffled.find(r=>_renrakuCat(r)==='geri'&&!blocks.includes(r));
  if(g&&blocks.length>1)blocks[Math.floor(blocks.length/2)]=g;
}
if(!hasTe){
  const t=shuffled.find(r=>_renrakuCat(r)==='te'&&!blocks.includes(r));
  if(t&&blocks.length>1)blocks[0]=t;
}

let total=blocks.reduce((s,r)=>s+r.steps.length,0);
if(minGoals>0&&total<minGoals){
  const extra=[...pool].sort(()=>Math.random()-.5);
  let i=0;
  while(total<minGoals&&blocks.length<15&&i<extra.length){
    const r=extra[i++];
    if(blocks[blocks.length-1]?.id!==r.id){blocks.push(r);total=blocks.reduce((s,r)=>s+r.steps.length,0);}
  }
}
const LBLS=['【Aquecimento】','【Desenvolvimento】','【Ritmo】','【Pico】','【Fechamento】',
  '【Variação】','【Aceleração】','【Potência】','【Técnica】','【Explosão】',
  '【Transição】','【Consolidação】','【Finalização】','【Kime】','【Zanshin】'];
const out=document.getElementById('ido-out');
out.innerHTML='<div class="s-block" style="text-align:center;letter-spacing:.15em;font-size:15px;font-weight:700;color:var(--gold)">YOI!</div>';
let rendered=0;
let cntTe=0,cntGeri=0,cntMisto=0;
blocks.forEach((r,i)=>{
  rendered+=r.steps.length;
  const cat=_renrakuCat(r);
  if(cat==='geri')cntGeri++;else if(cat==='te')cntTe++;else cntMisto++;
  const div=document.createElement('div');div.className='s-block';
  const catPill=cat==='geri'
    ?'<span style="font-size:9px;padding:1px 5px;border-radius:3px;background:rgba(68,136,221,.15);color:#4488dd;margin-left:6px">pé</span>'
    :cat==='te'
    ?'<span style="font-size:9px;padding:1px 5px;border-radius:3px;background:rgba(224,96,96,.15);color:#e06060;margin-left:6px">mão</span>'
    :'<span style="font-size:9px;padding:1px 5px;border-radius:3px;background:rgba(136,102,238,.15);color:#8866ee;margin-left:6px">misto</span>';
  div.innerHTML='<div class="sb-label">'+(LBLS[i]||`【Bloco ${i+1}】`)+'</div>'+
    '<div class="sb-name" style="color:'+(BS[r.belt]||'#888')+'">'+r.name+catPill+'</div>'+
    r.steps.map(s=>'<div style="font-size:12px;color:var(--text2);margin:2px 0;line-height:1.5">'+s+'</div>').join('')+
    '<div class="sb-note" style="margin-top:8px;padding-top:8px;border-top:1px solid var(--border)">'+r.note+'</div>';
  out.appendChild(div);
});
const kiai=document.createElement('div');kiai.className='s-kiai';kiai.textContent='KIAI! — YAME! NAORE! — OSU!';out.appendChild(kiai);
const pass=minGoals===0||rendered>=minGoals;
const badge=minGoals>0?'&nbsp;<span style="display:inline-block;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700;background:'+(pass?'#33aa6620':'#cc444420')+';color:'+(pass?'#33aa66':'#cc4444')+';border:1px solid '+(pass?'#33aa6660':'#cc444460')+'">'+(pass?'✓ APROVADO':'✗ INCOMPLETO')+'</span>':'';
const tot=document.createElement('div');tot.className='s-total';
const distParts=[];
if(cntGeri)distParts.push('<span style="color:#4488dd">pé×'+cntGeri+'</span>');
if(cntTe)distParts.push('<span style="color:#e06060">mão×'+cntTe+'</span>');
if(cntMisto)distParts.push('<span style="color:#8866ee">misto×'+cntMisto+'</span>');
tot.innerHTML='Total: <strong>'+rendered+'</strong> golpes'+(minGoals>0?' de mín. <strong>'+minGoals+'</strong>':'')+badge
  +(distParts.length?'&nbsp;&nbsp;<span style="opacity:.6;font-size:10px">'+distParts.join(' · ')+'</span>':'');
out.appendChild(tot);
const copyBtn=document.createElement('button');
copyBtn.style.cssText='margin-top:10px;background:var(--bg3);border:1px solid var(--border);color:var(--text2);cursor:pointer;border-radius:6px;padding:5px 14px;font-size:11px;letter-spacing:.04em;transition:all .2s';
copyBtn.textContent='⎘ Copiar sequência';
copyBtn.onclick=()=>{
  const txt=[...out.querySelectorAll('.s-block,.s-kiai')].map(el=>el.innerText).join('\n\n');
  navigator.clipboard.writeText(txt).then(()=>{
    copyBtn.textContent='✓ Copiado!';copyBtn.style.color='#33aa66';
    setTimeout(()=>{copyBtn.textContent='⎘ Copiar sequência';copyBtn.style.color='';},2000);
  });
};
out.appendChild(copyBtn);
}

