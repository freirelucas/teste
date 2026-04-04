// ===== DICTIONARY =====
let dictFilters={belt:'all',action:'all'};

function initDict(){
const fs=document.getElementById('dict-filters');
fs.innerHTML='';
['all','branca','laranja','azul','amarela','verde','marrom','kata'].forEach(b=>{
  const btn=document.createElement('button');
  btn.className='f-btn'+(dictFilters.belt===b?' on':'');
  btn.textContent=b==='all'?'Todas as faixas':b;
  btn.onclick=()=>{dictFilters.belt=b;initDict()};
  fs.appendChild(btn);
});
['','tsuki','uchi','geri','uke','barai','keage'].forEach(a=>{
  const btn=document.createElement('button');
  btn.className='f-btn'+(dictFilters.action===(a||'all')?' on':'');
  btn.textContent=a||'Todas as ações';
  btn.onclick=()=>{dictFilters.action=a||'all';initDict()};
  fs.appendChild(btn);
});
renderDict();
document.getElementById('dict-search').oninput=renderDict;
}

function renderDict(){
const q=(document.getElementById('dict-search').value||'').toLowerCase();
const grid=document.getElementById('dict-grid');grid.innerHTML='';
TECHS.filter(t=>{
  if(dictFilters.belt!=='all'&&t.belt!==dictFilters.belt)return false;
  if(dictFilters.action!=='all'&&t.action!==dictFilters.action)return false;
  if(q&&!t.name.toLowerCase().includes(q)&&!t.pt.toLowerCase().includes(q)
    &&!(t.desc||'').toLowerCase().includes(q)
    &&!t.nodes.some(nid=>NMAP[nid]&&(NMAP[nid].label.toLowerCase().includes(q)||NMAP[nid].pt.toLowerCase().includes(q))))return false;
  return true;
}).forEach(t=>{
  const div=document.createElement('div');
  div.className='dc';
  div.style.borderLeftColor=BS[t.belt];
  div.innerHTML='<div class="dc-name">'+t.name+'</div>'+
    '<div class="dc-pt">'+t.pt+'</div>'+
    '<div class="dc-tags">'+
      '<span class="dc-tag">'+t.action+'</span>'+
      t.nodes.slice(0,3).map(nid=>{const n=NMAP[nid];return n?'<span class="dc-tag" style="color:'+NT[n.type]+'">'+n.label+'</span>':''}).join('')+
      (t.kataOnly?'<span class="dc-tag" style="color:var(--kata)">kata only</span>':'')+
    '</div>'+
    '<div class="dc-hint">▸ detalhes</div>'+
    '<div class="dc-exp">'+
      '<div class="dc-desc">'+(t.desc||'')+'</div>'+
      (t.exec?'<div class="dc-exec">'+t.exec+'</div>':'')+
    '</div>';
  div.onclick=()=>div.classList.toggle('exp');
  const btn=document.createElement('button');
  btn.className='dc-const-btn';btn.textContent='✦ Ver na Constelação';
  btn.onclick=(e)=>{e.stopPropagation();switchTab('constelacao');requestAnimationFrame(()=>showTechDetail(t));};
  div.querySelector('.dc-exp').appendChild(btn);
  grid.appendChild(div);
});
const countEl=document.getElementById('dict-count');
if(grid.children.length===0){
  grid.innerHTML='<div style="color:var(--text2);font-size:13px">Nenhuma técnica encontrada.</div>';
  if(countEl)countEl.textContent='';
} else {
  if(countEl)countEl.textContent='Exibindo '+grid.children.length+' de '+TECHS.length+' técnicas';
}
}

function findAndShowTech(name){
const t=TECHS.find(x=>x.name===name)||TECHS.find(x=>x.name.startsWith(name.split(' ')[0]));
if(t){switchTab('constelacao');requestAnimationFrame(()=>showTechDetail(t));}
}

