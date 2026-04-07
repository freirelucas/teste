// ===== FONTES =====
function renderFontes(){
const fontes=[
{name:'CBKKO — Confederação Brasileira de Karate Kyokushin Oyama',url:'cbkko.com.br',
desc:'Filiada ao IKO1 (linhagem direta Mas Oyama). Única federação brasileira com autorização direta da linhagem do fundador. Presente em AM, BA, CE, MG, PR, RJ, RS e SP. Referência primária para requisitos de exame neste atlas.'},
{name:'IKO Honbu — International Karate Organization Kyokushinkaikan',url:'kyokushinboxing.wordpress.com/kyokushin-grading-3',
desc:'Documento oficial do IKO Honbu com syllabus técnico de graduação branca→shodan. Base para o inventário canônico de 42 técnicas de kihon e requisitos por faixa.'},
{name:'Jaap Kooman — Kata Documentation v7.1 (KWF/IKO1)',url:'jaapkooman.nl',
desc:'Documentação passo a passo de todos os kata com autoridade KWF/IKO1. Fonte para embusen, técnicas por kata, linhagem histórica e notas pedagógicas. Documento público com nome de autor.'},
{name:'IKO Nederland',url:'ikonederland.nl/technique',
desc:'Syllabus técnico IKO oficial por kyu com vídeos de referência. Usado para confirmar técnicas por faixa e variações de direção dentro de cada família.'},
{name:'Kyokushin Sabakido',url:'kyokushin-sabakido.com/kihon',
desc:'Lista completa do kihon geiko em sequência de treino. Fonte para ordenação e progressão das técnicas.'},
{name:'Kyokushinkaikan Brasil / WKK',url:'kyokushinkaikan.com.br',
desc:'Filiada IKO-Matsushima/WKK. Requisito documentado: para faixa preta, escrever o Kihon Geiko em ordem, identificar desenhos das Armas do Karate, Pontos Vitais, mínimo 30 golpes de Idogeiko. Prova teórica eliminatória com nota mínima 7.'},
];
const div=document.getElementById('fontes-content');div.innerHTML='';
fontes.forEach(f=>{
  const el=document.createElement('div');el.className='fonte';
  el.innerHTML='<h4>'+f.name+'</h4><a class="url" href="https://'+f.url+'" target="_blank" rel="noopener">↗ '+f.url+'</a><p>'+f.desc+'</p>';
  div.appendChild(el);
});
}

// ===== BELT FILTER =====
function filterBelt(belt){
const svg=document.getElementById('cv');
svg.querySelectorAll('[data-ti]').forEach(el=>{
  const ti=el.dataset.ti;if(ti===undefined)return;
  const tech=TECHS[+ti];if(!tech)return;
  if(belt==='all'){el.setAttribute('opacity',
    (el.tagName==='line'||el.tagName==='path')&&el.getAttribute('stroke')!=='transparent'?'.05':'1');return;}
  const bi=BELT_ORDER.indexOf(tech.belt);
  const sel=BELT_ORDER.indexOf(belt);
  const op=bi===sel?'.85':bi<sel?'.18':'.02';
  el.setAttribute('opacity',op);
});
svg.querySelectorAll('[data-nid]').forEach(el=>{
  if(belt==='all'){el.setAttribute('opacity','1');return;}
  const nid=el.dataset.nid;
  const sel=BELT_ORDER.indexOf(belt);
  const hasAny=TECHS.some(t=>t.nodes.includes(nid)&&BELT_ORDER.indexOf(t.belt)<=sel);
  el.setAttribute('opacity',hasAny?'1':'.15');
});
svg.querySelectorAll('.tech-poly').forEach(e=>e.remove());
}

function initBeltBar(){
const bar=document.getElementById('belt-bar');
if(!bar)return;
bar.innerHTML='';
['all',...BELT_ORDER].forEach(b=>{
  const btn=document.createElement('button');
  btn.className='bb-btn'+(b===activeBelt?' on':'');
  btn.textContent=b==='all'?'OSU':b;
  if(b!=='all'){
    btn.style.color=BS[b];
    const n=TECHS.filter(t=>t.belt===b).length;
    btn.title=n+' técnica'+(n!==1?'s':'');
  }
  if(b===activeBelt&&b!=='all')btn.style.background=BS[b]+'33';
  btn.onclick=()=>{activeBelt=b;initBeltBar();filterBelt(b);};
  bar.appendChild(btn);
});
}

// ===== CHORD DIAGRAM =====
function chordLayout(nodes,W,H){
const cx=W/2,cy=H/2,R=Math.min(W,H)*0.40;
const ORDER=['alvo','acao','direcao','ido','buki_mao','buki_pe','dachi'];
const GAP=0.12;
const byType={};nodes.forEach(n=>{if(!byType[n.type])byType[n.type]=[];byType[n.type].push(n);});
const totalArc=Math.PI*2-ORDER.length*GAP;
let a=-Math.PI/2;
ORDER.forEach(type=>{
  const g=byType[type]||[];
  if(!g.length)return;
  const arc=(g.length/nodes.length)*totalArc;
  const step=arc/g.length;
  g.forEach((n,i)=>{const ang=a+step*(i+.5);n.x=cx+R*Math.cos(ang);n.y=cy+R*Math.sin(ang);n.vx=0;n.vy=0;});
  a+=arc+GAP;
});
}

function setMode(mode){
cvMode=mode;
document.getElementById('mode-mandala').classList.toggle('on',mode==='mandala');
document.getElementById('mode-chord').classList.toggle('on',mode==='chord');
initConstellation();
initBeltBar();
renderKaratekaPanel();
}

function resetView(){
cvPan={x:0,y:0};cvScale=1;
const g=document.getElementById('cv-g');
if(g)g.setAttribute('transform','translate(0,0) scale(1)');
}

// ===== PLATONIC LEGEND =====
function renderPlatonicLegend(){
const old=document.getElementById('platonic-legend');if(old)old.remove();
const leg=document.createElement('div');
leg.id='platonic-legend';
leg.style.cssText='margin-top:14px;padding-top:12px;border-top:1px solid var(--border)';
const h=document.createElement('h4');
h.style.cssText='font-size:10px;letter-spacing:.08em;color:var(--text2);text-transform:uppercase;margin-bottom:10px;text-align:center';
h.textContent='Sólidos Platônicos';
leg.appendChild(h);
const NS='http://www.w3.org/2000/svg';
const grid=document.createElement('div');
grid.style.cssText='display:grid;grid-template-columns:repeat(4,1fr);gap:6px;padding:0 4px';
Object.entries(SHAPE_CFG).forEach(([type,cfg])=>{
  const col=NT[type];
  const cell=document.createElement('div');
  cell.style.cssText='display:flex;flex-direction:column;align-items:center;cursor:pointer;opacity:.85;transition:opacity .18s';
  cell.className='pcell';
  cell.onclick=()=>{
    highlightType(type);
    document.querySelectorAll('#platonic-legend .pcell').forEach(c=>c.style.background='none');
    cell.style.background=col+'22';
  };
  const svgEl=document.createElementNS(NS,'svg');
  svgEl.setAttribute('viewBox','0 0 44 44');svgEl.setAttribute('width','40');svgEl.setAttribute('height','40');
  const grp=document.createElementNS(NS,'g');
  grp.style.cssText=`animation:breathe ${type==='acao'?2.6:type==='dachi'?6:4}s ease-in-out infinite;transform-box:fill-box;transform-origin:center`;
  renderNodeWireframe(grp,22,22,13,type,col);
  svgEl.appendChild(grp);
  const lbl=document.createElement('div');
  const NAMES={acao:'Fogo',buki_mao:'Fogo·Terra',buki_pe:'Terra',direcao:'Ar',alvo:'Éter',dachi:'Terra',ido:'Água'};
  lbl.style.cssText=`font-size:7.5px;color:${col};text-align:center;margin-top:1px;letter-spacing:.03em;opacity:.8`;
  lbl.textContent=NAMES[type]||type;
  cell.appendChild(svgEl);cell.appendChild(lbl);
  grid.appendChild(cell);
});
leg.appendChild(grid);
document.getElementById('det-techs').parentNode.appendChild(leg);
}

// ===== NAVIGATION =====
function switchTab(tab){
document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));
document.querySelectorAll('.nav-btn').forEach(b=>b.classList.remove('active'));
document.getElementById('p-'+tab).classList.add('active');
document.querySelector('[data-tab="'+tab+'"]').classList.add('active');
}

document.querySelectorAll('.nav-btn').forEach(btn=>{
btn.onclick=()=>switchTab(btn.dataset.tab);
});

// ===== HELP OVERLAY =====
document.getElementById('help-close').onclick=()=>document.getElementById('help-overlay').classList.remove('open');
document.getElementById('help-overlay').addEventListener('click',e=>{if(e.target===e.currentTarget)e.currentTarget.classList.remove('open');});
// ===== QUICK SEARCH =====
function initSearch(){
const inp=document.getElementById('nav-search');
const drop=document.getElementById('search-drop');
if(!inp||!drop)return;
inp.addEventListener('input',()=>{
  const q=inp.value.trim().toLowerCase();
  drop.innerHTML='';
  if(q.length<2){drop.style.display='none';return;}
  const matches=TECHS.filter(t=>t.name.toLowerCase().includes(q)||t.pt.toLowerCase().includes(q)).slice(0,8);
  if(!matches.length){drop.style.display='none';return;}
  matches.forEach(t=>{
    const div=document.createElement('div');
    div.className='sdrop-item';
    div.innerHTML=`<b>${t.name}</b><span>${t.pt} · <span style="color:${BS[t.belt]}">${t.belt}</span></span>`;
    div.onclick=()=>{
      inp.value='';drop.style.display='none';
      switchTab('constelacao');
      // Wait for tab to be active before showing detail
      requestAnimationFrame(()=>showTechDetail(t));
    };
    drop.appendChild(div);
  });
  drop.style.display='block';
});
inp.addEventListener('keydown',e=>{if(e.key==='Escape'){inp.value='';drop.style.display='none';}});
document.addEventListener('click',e=>{if(!inp.contains(e.target)&&!drop.contains(e.target))drop.style.display='none';});
}

// ===== INIT =====
// ===== ÁUDIO / WEB SPEECH =====
function speak(text,lang='ja-JP'){
  if(!('speechSynthesis' in window))return;
  speechSynthesis.cancel();
  const u=new SpeechSynthesisUtterance(text);
  u.lang=lang; u.rate=0.78; u.pitch=1.05;
  speechSynthesis.speak(u);
}

// ===== CONSTRUTOR AUTO-DEMO =====
let _demoTimer=null,_demoIdx=0,_demoRunning=false;

function initAutoDemo(){
  const container=document.getElementById('const-matches');
  if(!container||document.getElementById('demo-bar'))return;
  const bar=document.createElement('div');bar.className='demo-bar';bar.id='demo-bar';
  bar.innerHTML=
    '<button class="demo-btn" id="demo-play" onclick="toggleDemo()">▶ Apresentação</button>'+
    '<select class="demo-speed" id="demo-speed"><option value="3000">Lento 3s</option><option value="2000" selected>Médio 2s</option><option value="1000">Rápido 1s</option></select>'+
    '<span class="demo-prog" id="demo-prog">—</span>';
  document.getElementById('const-form').after(bar);
}

function toggleDemo(){
  if(_demoRunning)stopDemo();else startDemo();
}

function startDemo(){
  _demoRunning=true;
  document.getElementById('demo-play').textContent='⏸ Pausar';
  document.getElementById('demo-play').classList.add('active');
  const speed=+(document.getElementById('demo-speed')?.value||2000);
  _demoTimer=setInterval(advanceDemo,speed);
  advanceDemo();
}

function stopDemo(){
  _demoRunning=false;
  clearInterval(_demoTimer);_demoTimer=null;
  document.getElementById('demo-play').textContent='▶ Apresentação';
  document.getElementById('demo-play').classList.remove('active');
}

function advanceDemo(){
  const t=TECHS[_demoIdx%TECHS.length];_demoIdx++;
  const prog=document.getElementById('demo-prog');
  if(prog)prog.textContent=(_demoIdx%TECHS.length||TECHS.length)+'/'+TECHS.length;
  // Populate selectors
  const setVal=(id,val)=>{const el=document.getElementById(id);if(el){el.value=val||'';el.disabled=false;}};
  setVal('cs-acao',t.action);
  const bm=t.nodes.find(n=>NMAP[n]?.type==='buki_mao');
  const bp=t.nodes.find(n=>NMAP[n]?.type==='buki_pe');
  const dir=t.nodes.find(n=>NMAP[n]?.type==='direcao');
  const alvo=t.nodes.find(n=>NMAP[n]?.type==='alvo');
  setVal('cs-bukim',bm||''); setVal('cs-bukipe',bp||'');
  setVal('cs-dir',dir||''); setVal('cs-alvo',alvo||'');
  updateConstrutor();
  speak(t.name);
}

// ===== MANDALA DE PALAVRAS — MODE =====
let cvMandalMode='solidos';

function setMandalMode(mode){
  cvMandalMode=mode;
  ['solidos','palavras','implicitos'].forEach(m=>{
    document.getElementById('mt-'+m)?.classList.toggle('on',m===mode);
  });
  initConstellation();
}

function init(){
requestAnimationFrame(()=>requestAnimationFrame(()=>{
  initConstellation();
  initBeltBar();
  renderKaratekaPanel();
}));
initDict();
initKata();renderKata();
initIdo();
renderMath();
renderFontes();
renderGramatica();
initConstrutor();
initAutoDemo();
initSearch();
}
init();
