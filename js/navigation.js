// ===== NAVIGATION STATE =====
let navHistory=[]; // [{type:'node',id:nid}|{type:'tech',id:techIdx}]
let navContext=[];  // tech list for ←/→ arrow navigation
let navContextIdx=-1;

function _updateNavUI(){
  const back=document.getElementById('det-back');
  const counter=document.getElementById('det-counter');
  if(back) back.style.display=navHistory.length>1?'':'none';
  if(counter){
    const show=navContext.length>0&&navContextIdx>=0;
    counter.style.display=show?'':'none';
    if(show) counter.textContent=(navContextIdx+1)+' / '+navContext.length;
  }
}

function showNodeDetail(nid,_hist){
if(!_hist) navHistory.push({type:'node',id:nid});
if(navHistory.length>20) navHistory.shift();
const node=NMAP[nid];if(!node)return;
const det=document.getElementById('detail');
det.classList.remove('bodymap');
const kw=document.getElementById('karateka-wrap');if(kw)kw.remove();
document.getElementById('det-name').textContent=node.label;
const _deg=NODE_DEGREE[nid]||0;
document.getElementById('det-type').textContent=node.pt+' · '+node.type.replace('_',' ')+(_deg?' · '+_deg+' técnicas':'');
document.getElementById('det-tags').innerHTML='<span class="tag" style="color:'+NT[node.type]+';border-color:'+NT[node.type]+'">'+node.type+'</span>';
const roleDesc={
  acao:'Verbo — ação que inicia a técnica · Tetraedro / Fogo',
  buki_mao:'Instrumento de mão — a arma utilizada · Hexagrama / Fogo+Terra',
  buki_pe:'Instrumento de pé — a arma utilizada · Losango / Terra',
  direcao:'Advérbio — modifica trajetória e direção · Octaedro / Ar',
  alvo:'Objeto — alvo anatômico da técnica · Dodecaedro / Éter',
  dachi:'Fundação — postura e base · Cubo / Terra',
  ido:'Movimento — deslocamento e footwork · Icosaedro / Água',
};
document.getElementById('det-desc').innerHTML=(roleDesc[node.type]||'')+(node.note?'<div style="margin-top:8px;padding-top:8px;border-top:1px solid var(--border);font-size:11px;line-height:1.7;color:var(--text2)">'+node.note+'</div>':'');
const ul=document.getElementById('det-techs');
const techsForNode=TECHS.filter(t=>t.nodes.includes(nid)||t.dachi===nid||getIdo(t.id)===nid);
ul.innerHTML='<div style="font-size:10px;color:var(--text2);margin-bottom:6px">TÉCNICAS ('+techsForNode.length+')</div>';
techsForNode.forEach(t=>{
  const li=document.createElement('li');
  li.style.borderLeftColor=BS[t.belt];
  li.innerHTML='<span style="font-weight:600;font-size:12px">'+t.name+'</span>'
    +'<span style="font-size:10px;color:var(--text2);display:block">'+t.pt+'</span>'
    +(t.desc?'<span style="font-size:10px;color:var(--text2);line-height:1.4;display:block;margin-top:2px">'+t.desc.slice(0,80)+'…</span>':'');
  li.onclick=()=>showTechDetail(t);
  ul.appendChild(li);
});
navContext=techsForNode;
navContextIdx=-1;
_updateNavUI();
det.classList.add('open');
// highlight connected edges
highlightNode(nid);
if(document.getElementById('p-constelacao').classList.contains('active'))panToNode(nid);
}

function showTechDetail(tech,_hist){
if(!_hist){navHistory.push({type:'tech',id:TECHS.indexOf(tech)});if(navHistory.length>20)navHistory.shift();}
const ctxIdx=navContext.indexOf(tech);if(ctxIdx>=0)navContextIdx=ctxIdx;
_updateNavUI();
const det=document.getElementById('detail');
det.classList.remove('bodymap');
const kw=document.getElementById('karateka-wrap');if(kw)kw.remove();
document.getElementById('det-name').textContent=tech.name;
document.getElementById('det-type').innerHTML=tech.pt+
  ('speechSynthesis'in window?` <button class="speak-btn" title="Pronunciar em japonês" onclick="speak('${tech.name.replace(/'/g,'\\\'')}')" style="margin-left:8px">🔊 ouvir</button>`:'');
document.getElementById('det-tags').innerHTML=
  '<span class="tag" style="color:'+BS[tech.belt]+';border-color:'+BS[tech.belt]+'">'+tech.belt+'</span>'+
  '<span class="tag" style="color:var(--text2);border-color:var(--border)">'+tech.action+'</span>'+
  (tech.kataOnly?'<span class="tag" style="color:var(--kata);border-color:var(--kata)">kata only</span>':'');
document.getElementById('det-desc').innerHTML=
  (tech.desc?'<p style="font-size:12px;color:var(--text2);line-height:1.6;margin-bottom:8px">'+tech.desc+'</p>':'')
  +(tech.exec?'<div class="dc-exec" style="font-size:12px;padding:8px 12px;background:var(--bg2);border-radius:6px;border-left:3px solid var(--gold);line-height:1.5">'+tech.exec+'</div>':'');
// Visual grammar formula
const ul=document.getElementById('det-techs');
const AXIS_ORDER=['buki_mao','buki_pe','acao','direcao','alvo','ido'];
const AXIS_LBL={buki_mao:'Buki·Mão',buki_pe:'Buki·Pé',acao:'Ação',direcao:'Direção',alvo:'Alvo',ido:'Ido'};
const orderedNodes=[...tech.nodes].sort((a,b)=>AXIS_ORDER.indexOf(NMAP[a]?.type)-AXIS_ORDER.indexOf(NMAP[b]?.type));
let fHtml='<div class="gram-formula">';
let axHtml='<div class="gram-axis-row">';
orderedNodes.forEach((nid,i)=>{
  const node=NMAP[nid];if(!node)return;
  const c=NT[node.type];
  if(i>0){fHtml+='<span class="gram-op">·</span>';}
  fHtml+=`<div class="gram-slot nav" onclick="showNodeDetail('${nid}')" title="${node.pt}" style="color:${c};border-color:${c}40;background:${c}0f"><div class="gram-slot-lbl" style="color:${c}">${AXIS_LBL[node.type]||node.type}</div><div class="gram-slot-val">${node.label}</div></div>`;
  axHtml+=`<div class="gram-axis-lbl" style="color:${c}88">${node.pt}</div>`;
});
if(tech.dachi){
  const d=NMAP[tech.dachi];
  if(d){
    const c=NT.dachi;
    fHtml+=`<span class="gram-sep">|</span><div class="gram-slot nav" onclick="showNodeDetail('${tech.dachi}')" title="${d.pt}" style="color:${c};border-color:${c}40;background:${c}0f"><div class="gram-slot-lbl" style="color:${c}">Dachi</div><div class="gram-slot-val">${d.label}</div></div>`;
    axHtml+=`<div class="gram-axis-lbl" style="color:${c}88">${d.pt}</div>`;
  }
}
const idoId=getIdo(tech.id);
const idoNode=NMAP[idoId];
if(idoNode){
  const c=NT.ido;
  fHtml+=`<span class="gram-op">·</span><div class="gram-slot nav" onclick="showNodeDetail('${idoId}')" title="${idoNode.pt}" style="color:${c};border-color:${c}40;background:${c}0f;min-width:44px"><div class="gram-slot-lbl" style="color:${c}">Ido</div><div class="gram-slot-val">${idoNode.label}</div></div>`;
  axHtml+=`<div class="gram-axis-lbl" style="color:${c}88">${idoNode.pt}</div>`;
}
fHtml+='</div>';axHtml+='</div>';
ul.innerHTML='<div style="font-size:10px;color:var(--text2);margin-bottom:4px;letter-spacing:.06em">FÓRMULA</div>'+fHtml+axHtml;
det.classList.add('open');
if(document.getElementById('p-constelacao').classList.contains('active')&&tech.nodes.length>0)
  panToNode(tech.nodes[0]);
}

function highlightNode(nid){
const svg=document.getElementById('cv');
// Reset prior pulse
svg.querySelectorAll('[data-ti]').forEach(el=>{
  el.style.strokeDasharray='';el.style.strokeDashoffset='';el.style.transition='';
});
svg.querySelectorAll('[data-ti]').forEach(el=>{
  const ti=el.dataset.ti;if(ti===undefined)return;
  const tech=TECHS[+ti];
  const connected=tech&&(tech.nodes.includes(nid)||tech.dachi===nid||getIdo(tech.id)===nid);
  el.setAttribute('opacity',connected?'.85':'.12');
  // Pulse animation on connected visible line edges
  if(connected&&el.tagName==='line'&&el.getAttribute('stroke')!=='transparent'){
    const dx=parseFloat(el.getAttribute('x2'))-parseFloat(el.getAttribute('x1'));
    const dy=parseFloat(el.getAttribute('y2'))-parseFloat(el.getAttribute('y1'));
    const len=Math.hypot(dx,dy);
    el.style.strokeDasharray=`${len} ${len}`;
    el.style.strokeDashoffset=`${len}`;
    el.style.transition=`stroke-dashoffset ${(0.4+Math.random()*.3).toFixed(2)}s ease-out`;
    requestAnimationFrame(()=>{el.style.strokeDashoffset='0';});
    setTimeout(()=>{el.style.strokeDasharray='';el.style.strokeDashoffset='';el.style.transition='';},900);
  }
});
svg.querySelectorAll('[data-nid]').forEach(el=>{
  el.setAttribute('opacity',el.dataset.nid===nid?'1':'.22');
});
// Draw technique polygons: each connected technique forms a closed polygon
// across its component nodes — a gramática linguística gera geometria
svg.querySelectorAll('.tech-poly').forEach(e=>e.remove());
const cvg=document.getElementById('cv-g');
const eg=document.getElementById('cv-edges');
const ni={};SIM_NODES.forEach(n=>ni[n.id]=n);
TECHS.filter(t=>t.nodes.includes(nid)||t.dachi===nid||getIdo(t.id)===nid).forEach(t=>{
  const allIds=[...t.nodes];
  if(t.dachi&&ni[t.dachi])allIds.push(t.dachi);
  const idoId=getIdo(t.id);if(ni[idoId])allIds.push(idoId);
  const pts=allIds.filter(id=>ni[id]).map(id=>ni[id].x.toFixed(1)+','+ni[id].y.toFixed(1)).join(' ');
  if(!pts||allIds.filter(id=>ni[id]).length<3)return;
  const poly=document.createElementNS('http://www.w3.org/2000/svg','polygon');
  poly.setAttribute('points',pts);
  poly.setAttribute('fill',BS[t.belt]||'#888');
  poly.setAttribute('fill-opacity','.09');
  poly.setAttribute('stroke',BS[t.belt]||'#888');
  poly.setAttribute('stroke-width','1');
  poly.setAttribute('stroke-opacity','.4');
  poly.setAttribute('class','tech-poly');
  poly.setAttribute('pointer-events','none');
  cvg.insertBefore(poly,eg);
});
}

function highlightType(type){
const svg=document.getElementById('cv');
svg.querySelectorAll('[data-ti]').forEach(el=>{
  const ti=el.dataset.ti;if(ti===undefined)return;
  const tech=TECHS[+ti];if(!tech)return;
  const connected=tech.nodes.some(nid=>{const node=NMAP[nid];return node&&node.type===type;})
    ||(type==='dachi'&&tech.dachi&&NMAP[tech.dachi]?.type==='dachi')
    ||(type==='ido'&&NMAP[getIdo(tech.id)]?.type==='ido');
  el.setAttribute('opacity',connected?'.72':'.04');
});
svg.querySelectorAll('[data-nid]').forEach(el=>{
  const node=NMAP[el.dataset.nid];
  el.setAttribute('opacity',(node&&node.type===type)?'1':'.18');
});
svg.querySelectorAll('.tech-poly').forEach(e=>e.remove());
}

let _panAnimId=null;
function panToNode(nid){
if(!SIM_NODES)return;
const node=SIM_NODES.find(n=>n.id===nid);if(!node)return;
const g=document.getElementById('cv-g');if(!g)return;
if(_panAnimId)cancelAnimationFrame(_panAnimId);
const tx=SIM_W/2-node.x*cvScale, ty=SIM_H/2-node.y*cvScale;
const sx=cvPan.x, sy=cvPan.y;
const DUR=22;let f=0;
function step(){
  f++;const e=1-(1-f/DUR)*(1-f/DUR);
  cvPan.x=sx+(tx-sx)*e;cvPan.y=sy+(ty-sy)*e;
  g.setAttribute('transform','translate('+cvPan.x.toFixed(1)+','+cvPan.y.toFixed(1)+') scale('+cvScale+')');
  if(f<DUR)_panAnimId=requestAnimationFrame(step);
}
_panAnimId=requestAnimationFrame(step);
}

function renderKaratekaPanel(){
const det=document.getElementById('detail');
det.classList.add('open','bodymap');
const old=document.getElementById('karateka-wrap');if(old)old.remove();
const wrap=document.createElement('div');
wrap.id='karateka-wrap';
const title=document.createElement('h4');
title.textContent='Mapa Corporal · Toque uma zona';
wrap.appendChild(title);
const NS='http://www.w3.org/2000/svg';
const ZONES=[
  {id:'jodan',   nid:'jodan',        color:NT.alvo,    label:'JODAN',
   polys:['96,18 124,18 128,30 122,42 98,42 92,30'],   lx:110,ly:32},
  {id:'gammen',  nid:'gammen',       color:NT.alvo,    label:'GAMMEN',
   polys:['100,42 120,42 122,54 118,62 102,62 98,54'],  lx:110,ly:53},
  {id:'chudan',  nid:'chudan',       color:NT.alvo,    label:'CHUDAN',
   polys:['90,70 130,70 134,110 128,120 92,120 86,110'],lx:110,ly:95},
  {id:'hizo',    nid:'hizo',         color:NT.alvo,    label:'HIZO',
   polys:['86,110 134,110 138,138 130,148 90,148 82,138'],lx:110,ly:130},
  {id:'gedan',   nid:'gedan',        color:NT.alvo,    label:'GEDAN',
   polys:['90,148 130,148 128,172 120,180 100,180 92,172'],lx:110,ly:164},
  {id:'kansetsu',nid:'kansetsu',     color:NT.alvo,    label:'KANSETSU',
   polys:['138,118 152,112 156,128 142,134','122,218 136,212 140,226 126,232'],lx:148,ly:122},
  {id:'buki_mao',typeFilt:'buki_mao',color:NT.buki_mao,label:'BUKI·MAO',
   polys:['58,100 72,94 78,108 64,114','142,144 156,138 160,152 146,158'],lx:68,ly:104},
  {id:'buki_pe', typeFilt:'buki_pe', color:NT.buki_pe, label:'BUKI·PE',
   polys:['118,308 140,304 144,320 122,322','80,310 102,306 104,320 82,322'],lx:112,ly:314},
  {id:'dachi',   typeFilt:'dachi',   color:NT.dachi,   label:'DACHI',
   polys:['72,280 148,280 152,296 68,296'],lx:110,ly:289},
  {id:'direcao', typeFilt:'direcao', color:NT.direcao, label:'DIRECAO',
   polys:['164,90 176,84 186,96 176,108 164,102 168,96'],lx:175,ly:97},
  {id:'ido',     typeFilt:'ido',     color:NT.ido,     label:'IDO',
   polys:['60,260 76,254 80,268 64,274'],lx:70,ly:264},
  {id:'acao',    typeFilt:'acao',    color:NT.acao,    label:'ACAO',
   polys:['84,64 98,58 104,72 102,80 88,78 82,70'],lx:93,ly:71},
];
const svg=document.createElementNS(NS,'svg');
svg.setAttribute('viewBox','0 0 220 340');
svg.setAttribute('width','220');
svg.setAttribute('height','340');
svg.style.cssText='display:block;margin:0 auto';
// Body silhouette parts — angular/geometric, non-interactive
[
  ['92,18 128,18 132,44 118,64 102,64 88,44'],       // head
  ['104,64 116,64 118,72 102,72'],                    // neck
  ['82,72 138,72 142,180 78,180'],                    // torso
  ['82,78 94,78 88,118 76,118'],                      // left upper arm
  ['76,118 88,118 74,148 62,148'],                    // left forearm
  ['138,78 150,78 156,116 144,116'],                  // right upper arm
  ['144,116 156,116 160,154 148,154'],                // right forearm
  ['78,178 142,178 148,200 72,200'],                  // hips
  ['110,200 140,200 136,242 106,242'],                // right thigh
  ['106,242 136,242 140,286 110,286'],                // right shin
  ['110,286 142,286 148,306 114,308'],                // right foot
  ['80,200 110,200 106,242 76,242'],                  // left thigh
  ['76,242 106,242 100,286 70,286'],                  // left shin
  ['70,286 100,286 102,306 68,308'],                  // left foot
].forEach(([pts])=>{
  const p=document.createElementNS(NS,'polygon');
  p.setAttribute('points',pts);
  p.setAttribute('fill','#1a1a2e');
  p.setAttribute('stroke','#3a4466');
  p.setAttribute('stroke-width','1.2');
  p.setAttribute('pointer-events','none');
  svg.appendChild(p);
});
// Ground line
const gnd=document.createElementNS(NS,'line');
['x1','40','y1','322','x2','180','y2','322'].reduce((e,[k,v])=>{e.setAttribute(k,v);return e;},gnd);
gnd.setAttribute('stroke','#3a4466');gnd.setAttribute('stroke-width','1');
gnd.setAttribute('opacity','.5');gnd.setAttribute('pointer-events','none');
svg.appendChild(gnd);
// Interactive zones
ZONES.forEach(z=>{
  const zg=document.createElementNS(NS,'g');
  zg.setAttribute('class','kzone');
  zg.setAttribute('data-zone',z.id);
  zg.style.opacity='1';
  z.polys.forEach(pts=>{
    const poly=document.createElementNS(NS,'polygon');
    poly.setAttribute('points',pts);
    poly.setAttribute('fill',z.color);
    poly.setAttribute('fill-opacity','.22');
    poly.setAttribute('stroke',z.color);
    poly.setAttribute('stroke-width','1');
    poly.setAttribute('stroke-opacity','.6');
    zg.appendChild(poly);
  });
  const txt=document.createElementNS(NS,'text');
  txt.setAttribute('x',z.lx);txt.setAttribute('y',z.ly);
  txt.setAttribute('class','kzone-label');
  txt.setAttribute('fill',z.color);
  txt.setAttribute('font-size','7');
  txt.textContent=z.label;
  zg.appendChild(txt);
  zg.addEventListener('click',ev=>{
    ev.stopPropagation();
    if(z.nid) highlightNode(z.nid);
    else if(z.typeFilt) highlightType(z.typeFilt);
    svg.querySelectorAll('.kzone').forEach(el=>el.style.opacity=el===zg?'1':'.3');
  });
  svg.appendChild(zg);
});
wrap.appendChild(svg);
const hint=document.createElement('div');
hint.style.cssText='font-size:10px;color:var(--text2);text-align:center;margin-top:6px;line-height:1.5';
hint.textContent='Toque uma zona para filtrar a constelação';
wrap.appendChild(hint);
document.getElementById('det-techs').parentNode.insertBefore(wrap,document.getElementById('det-techs'));
renderPlatonicLegend();
}

function _closeDetail(){
const det=document.getElementById('detail');
det.classList.remove('open','bodymap');
const kw=document.getElementById('karateka-wrap');if(kw)kw.remove();
const svg=document.getElementById('cv');
svg.querySelectorAll('[data-ti]').forEach(el=>{
  el.style.strokeDasharray='';el.style.strokeDashoffset='';el.style.transition='';
  el.setAttribute('opacity',
    (el.tagName==='line'||el.tagName==='path')&&el.getAttribute('stroke')!=='transparent'?'.05':'1');
});
svg.querySelectorAll('[data-nid]').forEach(el=>el.setAttribute('opacity','1'));
svg.querySelectorAll('.tech-poly').forEach(e=>e.remove());
navHistory.length=0;navContext=[];navContextIdx=-1;
document.getElementById('det-back').style.display='none';
document.getElementById('det-counter').style.display='none';
}
document.getElementById('det-close').onclick=_closeDetail;
document.getElementById('det-back').onclick=()=>{
navHistory.pop(); // remove current
const prev=navHistory.pop(); // remove prev (will be re-pushed)
if(!prev)return;
if(prev.type==='node') showNodeDetail(prev.id);
else showTechDetail(TECHS[prev.id]);
};
document.addEventListener('keydown',e=>{
const drop=document.getElementById('search-drop');
// Search dropdown keyboard navigation
if(drop&&drop.style.display!=='none'){
  const items=[...drop.querySelectorAll('.sdrop-item')];
  const active=drop.querySelector('.sdrop-item.hi');
  let idx=active?items.indexOf(active):-1;
  if(e.key==='ArrowDown'){e.preventDefault();idx=Math.min(idx+1,items.length-1);items.forEach((it,i)=>it.classList.toggle('hi',i===idx));}
  else if(e.key==='ArrowUp'){e.preventDefault();idx=Math.max(idx-1,0);items.forEach((it,i)=>it.classList.toggle('hi',i===idx));}
  else if(e.key==='Enter'&&active){active.click();return;}
  else if(e.key==='Escape'){document.getElementById('nav-search').value='';drop.style.display='none';return;}
  return;
}
if(e.key==='?'&&e.target.tagName!=='INPUT'){
  const ov=document.getElementById('help-overlay');
  ov.classList.toggle('open');return;
}
const det=document.getElementById('detail');
if(e.key==='Escape'){
  const ov=document.getElementById('help-overlay');
  if(ov.classList.contains('open')){ov.classList.remove('open');return;}
}
if(!det.classList.contains('open'))return;
if(e.key==='Escape'){_closeDetail();return;}
if(e.key==='ArrowRight'&&navContext.length>0){
  e.preventDefault();
  navContextIdx=Math.min(navContextIdx+1,navContext.length-1);
  if(navContextIdx<0)navContextIdx=0;
  showTechDetail(navContext[navContextIdx],true);
} else if(e.key==='ArrowLeft'&&navContext.length>0&&navContextIdx>0){
  e.preventDefault();
  navContextIdx--;
  showTechDetail(navContext[navContextIdx],true);
}
});

