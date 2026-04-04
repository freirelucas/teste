
function findAndShowTech(name){
const t=TECHS.find(x=>x.name===name)||TECHS.find(x=>x.name.startsWith(name.split(' ')[0]));
if(t){switchTab('constelacao');requestAnimationFrame(()=>showTechDetail(t));}
}

// ===== KATA =====
let kataFilter='all';
function initKata(){
const fs=document.getElementById('kata-filters');if(!fs)return;
fs.innerHTML='';
['all','branca','laranja','azul','amarela','verde','marrom','shodan'].forEach(b=>{
  const btn=document.createElement('button');
  btn.className='f-btn'+(kataFilter===b?' on':'');
  btn.textContent=b==='all'?'Todas':b;
  btn.onclick=()=>{kataFilter=b;renderKata();initKata();};
  fs.appendChild(btn);
});
const sep=document.createElement('span');
sep.style.cssText='color:var(--border);padding:0 6px;font-size:14px;align-self:center;opacity:.5';
sep.textContent='|';fs.appendChild(sep);
[{key:'taikyoku',lbl:'Taikyoku'},{key:'sokugi',lbl:'Sokugi'},
 {key:'pinan',lbl:'Pinan'},{key:'avancado',lbl:'Avançado'}].forEach(s=>{
  const btn=document.createElement('button');
  btn.className='f-btn'+(kataFilter===s.key?' on':'');
  btn.textContent=s.lbl;
  btn.onclick=()=>{kataFilter=s.key;renderKata();initKata();};
  fs.appendChild(btn);
});
}
function renderKata(){
const SERIES={
  taikyoku:k=>k.id.startsWith('k_tai'),
  sokugi:  k=>k.id.startsWith('k_stai'),
  pinan:   k=>k.id.startsWith('k_pi')||k.id==='k_sanchin'||k.id==='k_tsuki',
  avancado:k=>!['k_tai1','k_tai2','k_tai3','k_stai1','k_stai2','k_stai3',
                'k_pi1','k_pi2','k_pi3','k_pi4','k_pi5','k_sanchin','k_tsuki'].includes(k.id),
};
const grid=document.getElementById('kata-grid');grid.innerHTML='';
KATA.filter(k=>{
  if(kataFilter==='all')return true;
  if(SERIES[kataFilter])return SERIES[kataFilter](k);
  return k.belt===kataFilter;
}).forEach(k=>{
  const belt=k.belt;
  const div=document.createElement('div');div.className='kc';
  div.innerHTML=
    '<div class="kc-belt" style="background:'+BS[belt]+'22;color:'+BS[belt]+'">'+belt+'</div>'+
    '<div class="kc-name">'+k.name+'</div>'+
    '<div class="kc-origin">'+k.origin+'</div>'+
    '<div class="kc-emb"><svg viewBox="0 0 60 90" width="60" height="90" style="display:block">'+
    '<rect width="60" height="90" fill="#111118" rx="4"/>'+
    '<path d="'+k.embusen+'" fill="none" stroke="'+BS[belt]+'" stroke-width="2" stroke-linecap="round"/>'+
    '<circle cx="30" cy="80" r="3" fill="'+BS[belt]+'" opacity=".7"/>'+
    '</svg></div>'+
    '<div class="kc-note">'+k.note+'</div>'+
    (k.silences?'<div class="kc-detail"><div style="font-size:10px;color:var(--text2);margin-bottom:4px;letter-spacing:.06em">SILÊNCIOS CANÔNICOS</div><div style="font-size:11px;color:var(--text2)">'+k.silences+'</div></div>':'')+
    (k.techs&&k.techs.length?'<div class="kc-detail"><div style="font-size:10px;color:var(--text2);margin-bottom:4px">TÉCNICAS INTRODUZIDAS</div>'+k.techs.map(tc=>'<div class="kc-tl" data-tc="'+tc+'">'+tc+' <span style="opacity:.4;font-size:9px">→ constelação</span></div>').join('')+'</div>':'')+
    (k.steps&&k.steps.length?'<div class="kc-detail kc-steps-wrap"><div class="kc-steps-hdr">ROTEIRO DE PRÁTICA <span style="opacity:.5;font-weight:400">('+k.steps.filter(s=>!s.startsWith('  ▶')).length+' seq.)</span></div>'+k.steps.map(s=>{
      if(s.startsWith('  ▶'))return'<div class="kc-step-item sub">'+s.slice(3)+'</div>';
      const m=s.match(/^(\d+)\.\s+(.*)/);
      if(m){const kiai=m[2].includes('KIAI');return'<div class="kc-step-item"><span class="step-n">'+m[1]+'.</span> <span class="step-cmd">'+m[2].replace(/\s*·?\s*KIAI/g,'')+'</span>'+(kiai?'<span class="kiai">KIAI</span>':'')+'</div>';}
      return'<div class="kc-step-item" style="color:var(--gold);font-size:10px;letter-spacing:.05em">'+s+'</div>';
    }).join('')+'</div>':'');
  div.querySelectorAll('.kc-tl').forEach(el=>el.addEventListener('click',e=>{
    e.stopPropagation();findAndShowTech(el.dataset.tc);
  }));
  // Speak kata name on header click
  const nameEl=div.querySelector('.kc-name');
  if(nameEl)nameEl.addEventListener('click',e=>{e.stopPropagation();speak(k.name);});
  div.onclick=()=>div.classList.toggle('open');
  grid.appendChild(div);
});
if(!grid.children.length)grid.innerHTML='<div style="color:var(--text2);font-size:13px;padding:12px 0">Nenhum kata nesta seleção.</div>';
}

