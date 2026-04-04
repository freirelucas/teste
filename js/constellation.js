// Build edges for constellation: star from nodes[0] (hub=buki) to all semantic dimensions
function buildEdges(){
const edges=[];
TECHS.forEach(t=>{
  const ns=t.nodes.filter(id=>NMAP[id]);
  const hub=ns[0];
  for(let i=1;i<ns.length;i++){
    edges.push({source:hub,target:ns[i],tech:t});
  }
  // dachi: postura — fundação (outer ring)
  if(t.dachi&&NMAP[t.dachi])
    edges.push({source:hub,target:t.dachi,tech:t});
  // ido: movimento — fluxo (mid ring)
  const idoId=getIdo(t.id);
  if(NMAP[idoId])
    edges.push({source:hub,target:idoId,tech:t});
});
return edges;
}

// ===== FORCE SIMULATION =====
let SIM_NODES=null, SIM_EDGES=null, SIM_W=0, SIM_H=0;

function clusterCenter(type,W,H){
const m={
  acao:{x:W*.50,y:H*.18},
  buki_mao:{x:W*.18,y:H*.42},
  buki_pe:{x:W*.82,y:H*.42},
  direcao:{x:W*.50,y:H*.72},
  alvo:{x:W*.50,y:H*.50},
  dachi:{x:W*.18,y:H*.78},
  ido:{x:W*.82,y:H*.78},
};
return m[type]||{x:W*.5,y:H*.5};
}

function fixedLayout(nodes,W,H){
const cx=W/2,cy=H/2,half=Math.min(W,H)/2;
const r0=half*.22,r1=half*.47,r2=half*.78;
const RING0=['alvo'];
const RING1=['acao','direcao','ido'];
const RING2=['buki_mao','buki_pe','dachi'];
const GAP=0.14;
function placeRing(ring,r,startA){
  const byType={};
  ring.forEach(n=>{if(!byType[n.type])byType[n.type]=[];byType[n.type].push(n);});
  const typeOrder=[...new Set(ring.map(n=>n.type))];
  const totalArc=Math.PI*2-typeOrder.length*GAP;
  const total=ring.length;
  let a=startA;
  typeOrder.forEach(type=>{
    const g=byType[type]||[];
    const arc=(g.length/total)*totalArc;
    const step=arc/g.length;
    g.forEach((n,i)=>{
      const ang=a+step*(i+.5);
      n.x=cx+r*Math.cos(ang);
      n.y=cy+r*Math.sin(ang);
      n.vx=0;n.vy=0;
    });
    a+=arc+GAP;
  });
}
const ring0=nodes.filter(n=>RING0.includes(n.type));
const ring1=nodes.filter(n=>RING1.includes(n.type));
const ring2=nodes.filter(n=>RING2.includes(n.type));
ring1.sort((a,b)=>RING1.indexOf(a.type)-RING1.indexOf(b.type));
ring2.sort((a,b)=>RING2.indexOf(a.type)-RING2.indexOf(b.type));
placeRing(ring0,r0,-Math.PI/2);
placeRing(ring1,r1,-Math.PI/2);
placeRing(ring2,r2,-Math.PI/2);
}

function runForce(nodes,edges,W,H){
// init positions
nodes.forEach(n=>{
  const c=clusterCenter(n.type,W,H);
  n.x=c.x+(Math.random()-.5)*120;
  n.y=c.y+(Math.random()-.5)*120;
  n.vx=0;n.vy=0;
});
// build node index
const ni={};nodes.forEach(n=>ni[n.id]=n);
const iters=350;
for(let it=0;it<iters;it++){
  const alpha=1-it/iters;
  // repulsion O(n^2) with cutoff
  for(let i=0;i<nodes.length;i++){
    for(let j=i+1;j<nodes.length;j++){
      const dx=nodes[j].x-nodes[i].x,dy=nodes[j].y-nodes[i].y;
      const d2=dx*dx+dy*dy+1;
      const f=Math.min(350*350/d2,12);
      const d=Math.sqrt(d2);
      nodes[i].vx-=dx/d*f*alpha;nodes[i].vy-=dy/d*f*alpha;
      nodes[j].vx+=dx/d*f*alpha;nodes[j].vy+=dy/d*f*alpha;
    }
  }
  // spring along edges
  edges.forEach(e=>{
    const s=ni[e.source],t=ni[e.target];
    if(!s||!t)return;
    const dx=t.x-s.x,dy=t.y-s.y;
    const d=Math.sqrt(dx*dx+dy*dy)||1;
    const rest=90;const f=(d-rest)*.045*alpha;
    s.vx+=dx/d*f;s.vy+=dy/d*f;
    t.vx-=dx/d*f;t.vy-=dy/d*f;
  });
  // cluster pull
  nodes.forEach(n=>{
    const c=clusterCenter(n.type,W,H);
    n.vx+=(c.x-n.x)*.012*alpha;
    n.vy+=(c.y-n.y)*.012*alpha;
  });
  // apply + damp
  nodes.forEach(n=>{
    n.vx*=.82;n.vy*=.82;
    n.x+=n.vx;n.y+=n.vy;
    n.x=Math.max(28,Math.min(W-28,n.x));
    n.y=Math.max(28,Math.min(H-28,n.y));
  });
}
}

// ===== CONSTELLATION RENDER =====
let cvPan={x:0,y:0},cvScale=1,cvDrag=null;
let activeNodeId=null;

function initConstellation(){
const wrap=document.getElementById('cv-wrap');
const svg=document.getElementById('cv');
const W=wrap.clientWidth||900,H=wrap.clientHeight||700;
svg.setAttribute('width',W);svg.setAttribute('height',H);
svg.setAttribute('viewBox','0 0 '+W+' '+H);

const nodes=NODES.map(n=>Object.assign({},n));
const edges=buildEdges();
cvMode==='chord'?chordLayout(nodes,W,H):fixedLayout(nodes,W,H);
SIM_NODES=nodes;SIM_EDGES=edges;SIM_W=W;SIM_H=H;

renderSVG(svg,nodes,edges,W,H);
setupCvEvents(svg,W,H);
}

// ===== GEOMETRY HELPERS =====
function polyPoints(cx,cy,r,sides,rot){
rot=rot||0;let pts='';
for(let i=0;i<sides;i++){
  const a=(i/sides)*Math.PI*2-Math.PI/2+rot*Math.PI/180;
  pts+=(cx+r*Math.cos(a)).toFixed(2)+','+(cy+r*Math.sin(a)).toFixed(2)+' ';
}
return pts.trim();
}
function starPoints(cx,cy,r,rot){
rot=rot||0;const ri=r*.42;let pts='';
for(let i=0;i<10;i++){
  const a=(i/10)*Math.PI*2-Math.PI/2+rot*Math.PI/180;
  const rc=i%2===0?r:ri;
  pts+=(cx+rc*Math.cos(a)).toFixed(2)+','+(cy+rc*Math.sin(a)).toFixed(2)+' ';
}
return pts.trim();
}
function shapePts(cx,cy,r,cfg){
return cfg.star?starPoints(cx,cy,r,cfg.rot):polyPoints(cx,cy,r,cfg.sides,cfg.rot);
}
function renderClusterHalos(g,W,H){
const hg=document.createElementNS('http://www.w3.org/2000/svg','g');
hg.setAttribute('pointer-events','none');
const NS='http://www.w3.org/2000/svg';
const cx=W/2,cy=H/2,half=Math.min(W,H)/2;
const RING_R={alvo:half*.22,acao:half*.47,direcao:half*.47,ido:half*.47,
  buki_mao:half*.78,buki_pe:half*.78,dachi:half*.78};
Object.entries(NT).forEach(([type,col])=>{
  const ns=SIM_NODES.filter(n=>n.type===type);
  if(!ns.length)return;
  const r=RING_R[type];if(!r)return;
  const angles=ns.map(n=>Math.atan2(n.y-cy,n.x-cx)).sort((a,b)=>a-b);
  const pad=0.18;
  const a1=angles[0]-pad,a2=angles[angles.length-1]+pad;
  const x1=(cx+r*Math.cos(a1)).toFixed(1),y1=(cy+r*Math.sin(a1)).toFixed(1);
  const x2=(cx+r*Math.cos(a2)).toFixed(1),y2=(cy+r*Math.sin(a2)).toFixed(1);
  const large=a2-a1>Math.PI?1:0;
  const path=document.createElementNS(NS,'path');
  path.setAttribute('d',`M${x1},${y1} A${r},${r} 0 ${large},1 ${x2},${y2}`);
  path.setAttribute('fill','none');
  path.setAttribute('stroke',col);
  path.setAttribute('stroke-width','28');
  path.setAttribute('stroke-opacity','.07');
  path.setAttribute('stroke-linecap','round');
  hg.appendChild(path);
  // Type label at arc midpoint
  const amid=(a1+a2)/2;
  const lr=r+(type==='alvo'?-28:28);
  const txt=document.createElementNS(NS,'text');
  txt.setAttribute('x',(cx+lr*Math.cos(amid)).toFixed(1));
  txt.setAttribute('y',(cy+lr*Math.sin(amid)).toFixed(1));
  txt.setAttribute('text-anchor','middle');txt.setAttribute('dominant-baseline','middle');
  txt.setAttribute('font-size','8.5');txt.setAttribute('fill',col);txt.setAttribute('opacity','.4');
  txt.setAttribute('pointer-events','none');txt.setAttribute('letter-spacing','.06em');
  txt.textContent=type.replace('_','-').toUpperCase();
  hg.appendChild(txt);
});
g.insertBefore(hg,g.firstChild);
}

// Draw 3D wireframe projection of Platonic solid for a node
function renderNodeWireframe(grp,cx,cy,r,type,col){
const NS='http://www.w3.org/2000/svg';
function mk(tag,attrs){
  const e=document.createElementNS(NS,tag);
  Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,String(v)));
  return e;
}
function wline(x1,y1,x2,y2){
  return mk('line',{x1:x1.toFixed(1),y1:y1.toFixed(1),x2:x2.toFixed(1),y2:y2.toFixed(1),
    stroke:'#0b0b10','stroke-width':'1',opacity:'.55','pointer-events':'none'});
}
function filled(pts,op){
  return mk('polygon',{points:pts,fill:col,opacity:op||'.82',stroke:'#0b0b10','stroke-width':'1.2'});
}
function ring(pts){
  return mk('polygon',{points:pts,fill:'none',stroke:col,'stroke-width':'1.5',opacity:'.45','pointer-events':'none'});
}
function verts(sides,rotDeg,rad){
  const arr=[];
  for(let i=0;i<sides;i++){
    const a=(i/sides)*Math.PI*2-Math.PI/2+(rotDeg||0)*Math.PI/180;
    arr.push({x:cx+(rad||r)*Math.cos(a),y:cy+(rad||r)*Math.sin(a)});
  }
  return arr;
}
if(type==='acao'){
  // Tetraedro/Fogo: triângulo + 3 medianas ao centróide
  const v=verts(3,-90);
  grp.appendChild(ring(polyPoints(cx,cy,r*1.6,3,-90)));
  grp.appendChild(filled(polyPoints(cx,cy,r,3,-90)));
  v.forEach(p=>grp.appendChild(wline(cx,cy,p.x,p.y)));
  grp.appendChild(mk('circle',{cx:cx.toFixed(1),cy:cy.toFixed(1),r:2.2,fill:'#0b0b10',opacity:'.6','pointer-events':'none'}));
}else if(type==='dachi'){
  // Cubo/Terra: hexágono + 3 linhas isométricas ao centro
  const v=verts(6,0);
  grp.appendChild(ring(polyPoints(cx,cy,r*1.5,6,0)));
  grp.appendChild(filled(polyPoints(cx,cy,r,6,0)));
  [0,2,4].forEach(i=>grp.appendChild(wline(cx,cy,v[i].x,v[i].y)));
}else if(type==='direcao'){
  // Octaedro/Ar: losango + 2 diagonais (4 triângulos)
  const v=verts(4,0);
  grp.appendChild(ring(polyPoints(cx,cy,r*1.5,4,0)));
  grp.appendChild(filled(polyPoints(cx,cy,r,4,0)));
  grp.appendChild(wline(v[0].x,v[0].y,v[2].x,v[2].y));
  grp.appendChild(wline(v[1].x,v[1].y,v[3].x,v[3].y));
}else if(type==='ido'){
  // Icosaedro/Água: pentagrama + pentágono interno
  grp.appendChild(ring(starPoints(cx,cy,r*1.55,-90)));
  grp.appendChild(filled(starPoints(cx,cy,r,-90)));
  grp.appendChild(mk('polygon',{points:polyPoints(cx,cy,r*.42,5,-90),fill:'none',
    stroke:'#0b0b10','stroke-width':'0.8',opacity:'.5','pointer-events':'none'}));
}else if(type==='alvo'){
  // Dodecaedro/Éter: pentágono + pentágono interno + 5 radiais
  const vo=verts(5,-90);const vi=verts(5,-90,r*.52);
  grp.appendChild(ring(polyPoints(cx,cy,r*1.5,5,-90)));
  grp.appendChild(filled(polyPoints(cx,cy,r,5,-90)));
  grp.appendChild(mk('polygon',{points:polyPoints(cx,cy,r*.52,5,-90),fill:'none',
    stroke:'#0b0b10','stroke-width':'0.8',opacity:'.5','pointer-events':'none'}));
  vo.forEach((p,i)=>grp.appendChild(wline(p.x,p.y,vi[i].x,vi[i].y)));
}else if(type==='buki_mao'){
  // Hexagrama (Fogo+Terra): dois triângulos sobrepostos
  grp.appendChild(ring(polyPoints(cx,cy,r*1.5,6,0)));
  grp.appendChild(mk('polygon',{points:polyPoints(cx,cy,r,3,-90),fill:col,opacity:'.72',stroke:'#0b0b10','stroke-width':'1'}));
  grp.appendChild(mk('polygon',{points:polyPoints(cx,cy,r,3,90),fill:col,opacity:'.72',stroke:'#0b0b10','stroke-width':'1'}));
}else if(type==='buki_pe'){
  // Losango+Cruz: losango + cruz central
  const v=verts(4,0);
  grp.appendChild(ring(polyPoints(cx,cy,r*1.5,4,0)));
  grp.appendChild(filled(polyPoints(cx,cy,r,4,0)));
  grp.appendChild(wline(v[0].x,v[0].y,v[2].x,v[2].y));
  grp.appendChild(wline(v[1].x,v[1].y,v[3].x,v[3].y));
}else{
  grp.appendChild(ring(polyPoints(cx,cy,r*1.4,6,0)));
  grp.appendChild(filled(polyPoints(cx,cy,r,6,0)));
}
}

function renderSVG(svg,nodes,edges,W,H){
svg.innerHTML='';
// Background: concentric ring guides aligned with data rings (alvo / verb / instrument)
const bg=document.createElementNS('http://www.w3.org/2000/svg','g');
bg.setAttribute('pointer-events','none');
const _half=Math.min(W,H)/2;
[{r:_half*.22,sw:'0.6',op:'.10'},{r:_half*.47,sw:'1',op:'.14'},{r:_half*.78,sw:'1',op:'.10'},
 {r:_half*1.05,sw:'0.5',op:'.04'},{r:_half*1.28,sw:'0.4',op:'.03'}].forEach(({r,sw,op})=>{
  const c=document.createElementNS('http://www.w3.org/2000/svg','circle');
  c.setAttribute('cx',W/2);c.setAttribute('cy',H/2);c.setAttribute('r',r.toFixed(1));
  c.setAttribute('fill','none');c.setAttribute('stroke','#c9a84c');
  c.setAttribute('stroke-width',sw);c.setAttribute('opacity',op);
  bg.appendChild(c);
});
svg.appendChild(bg);
// Kan-ku (看空) — diamond + inner circle at canvas center, Kyokushin symbol
const kk=document.createElementNS('http://www.w3.org/2000/svg','g');
kk.setAttribute('pointer-events','none');
const kkR=Math.min(W,H)*.46,kkCx=W/2,kkCy=H/2;
const kkD=document.createElementNS('http://www.w3.org/2000/svg','polygon');
kkD.setAttribute('points',`${kkCx},${(kkCy-kkR).toFixed(1)} ${(kkCx+kkR).toFixed(1)},${kkCy} ${kkCx},${(kkCy+kkR).toFixed(1)} ${(kkCx-kkR).toFixed(1)},${kkCy}`);
kkD.setAttribute('fill','none');kkD.setAttribute('stroke','#c9a84c');
kkD.setAttribute('stroke-width','1.5');kkD.setAttribute('opacity','.11');
kk.appendChild(kkD);
const kkC=document.createElementNS('http://www.w3.org/2000/svg','circle');
kkC.setAttribute('cx',kkCx);kkC.setAttribute('cy',kkCy);
kkC.setAttribute('r',(Math.min(W,H)*.14).toFixed(1));
kkC.setAttribute('fill','none');kkC.setAttribute('stroke','#c9a84c');
kkC.setAttribute('stroke-width','1');kkC.setAttribute('opacity','.11');
kk.appendChild(kkC);
[[kkCx,kkCy-kkR,kkCx,kkCy+kkR],[kkCx-kkR,kkCy,kkCx+kkR,kkCy]].forEach(([x1,y1,x2,y2])=>{
  const l=document.createElementNS('http://www.w3.org/2000/svg','line');
  [['x1',x1],['y1',y1],['x2',x2],['y2',y2]].forEach(([k,v])=>l.setAttribute(k,v));
  l.setAttribute('stroke','#c9a84c');l.setAttribute('stroke-width','.6');l.setAttribute('opacity','.04');
  kk.appendChild(l);
});
svg.appendChild(kk);
const ni={};nodes.forEach(n=>ni[n.id]=n);
const g=document.createElementNS('http://www.w3.org/2000/svg','g');
g.setAttribute('id','cv-g');
svg.appendChild(g);

// Cluster halos (background geometric shapes per semantic group)
if(cvMandalMode==='solidos')renderClusterHalos(g,W,H);

// Edges (hidden in Palavras/Implícitos modes — polygons replace them)
const eg=document.createElementNS('http://www.w3.org/2000/svg','g');
eg.setAttribute('id','cv-edges');
if(cvMandalMode!=='solidos')eg.setAttribute('display','none');
g.appendChild(eg);
edges.forEach((e,i)=>{
  const s=ni[e.source],t=ni[e.target];
  if(!s||!t)return;
  const sType=NMAP[e.source]&&NMAP[e.source].type;
  const tType=NMAP[e.target]&&NMAP[e.target].type;
  const isBukiAcao=((sType==='buki_mao'||sType==='buki_pe')&&tType==='acao')||
    (sType==='acao'&&(tType==='buki_mao'||tType==='buki_pe'));
  const isDirecao=sType==='direcao'||tType==='direcao';
  const isAlvo=sType==='alvo'||tType==='alvo';
  const isDachi=sType==='dachi'||tType==='dachi';
  const isIdo=sType==='ido'||tType==='ido';
  const sw=e.tech.kataOnly?'1':isBukiAcao?'2.2':isAlvo?'1.1':isDachi?'1.0':isIdo?'0.8':'1.4';
  const op='.05';
  const dash=e.tech.kataOnly?'5,4':isDirecao&&!e.tech.kataOnly?'4,3':isIdo?'3,3':'none';
  const ti=TECHS.indexOf(e.tech);
  const col=BS[e.tech.belt]||'#444';
  if(cvMode==='chord'){
    const cpx=((s.x+t.x)/2*.25+W/2*.75).toFixed(1);
    const cpy=((s.y+t.y)/2*.25+H/2*.75).toFixed(1);
    const dStr=`M${s.x.toFixed(1)},${s.y.toFixed(1)} Q${cpx},${cpy} ${t.x.toFixed(1)},${t.y.toFixed(1)}`;
    const line=document.createElementNS('http://www.w3.org/2000/svg','path');
    line.setAttribute('d',dStr);line.setAttribute('fill','none');
    line.setAttribute('stroke',col);line.setAttribute('stroke-width',sw);
    line.setAttribute('stroke-dasharray',dash);line.setAttribute('opacity',op);
    line.setAttribute('data-ti',ti);line.style.cursor='pointer';
    eg.appendChild(line);
    const hit=document.createElementNS('http://www.w3.org/2000/svg','path');
    hit.setAttribute('d',dStr);hit.setAttribute('fill','none');
    hit.setAttribute('stroke','transparent');hit.setAttribute('stroke-width','10');
    hit.setAttribute('data-ti',ti);hit.style.cursor='pointer';
    eg.appendChild(hit);
  }else{
  const line=document.createElementNS('http://www.w3.org/2000/svg','line');
  line.setAttribute('x1',s.x);line.setAttribute('y1',s.y);
  line.setAttribute('x2',t.x);line.setAttribute('y2',t.y);
  line.setAttribute('stroke',col);
  line.setAttribute('stroke-width',sw);
  line.setAttribute('stroke-dasharray',dash);
  line.setAttribute('opacity',op);
  line.setAttribute('data-ti',ti);
  line.style.cursor='pointer';
  eg.appendChild(line);

  // invisible fat hit area
  const hit=document.createElementNS('http://www.w3.org/2000/svg','line');
  hit.setAttribute('x1',s.x);hit.setAttribute('y1',s.y);
  hit.setAttribute('x2',t.x);hit.setAttribute('y2',t.y);
  hit.setAttribute('stroke','transparent');
  hit.setAttribute('stroke-width','10');
  hit.setAttribute('data-ti',ti);
  hit.style.cursor='pointer';
  eg.appendChild(hit);
  }
});

// Nodes — 3D wireframe projections of Platonic solids per semantic/grammatical type
const ng=document.createElementNS('http://www.w3.org/2000/svg','g');
ng.setAttribute('id','cv-nodes');
g.appendChild(ng);
nodes.forEach(n=>{
  const deg=NODE_DEGREE[n.id]||1;
  const norm=deg/_maxDeg; // 0..1
  const baseR=n.type==='acao'?20:17;
  const r=Math.round(baseR*(0.75+0.5*norm)); // scale 75%..125% of base
  const col=NT[n.type];
  const grp=document.createElementNS('http://www.w3.org/2000/svg','g');
  grp.setAttribute('data-nid',n.id);
  grp.setAttribute('data-type',n.type);
  grp.style.cursor='pointer';
  if(cvMandalMode==='solidos'){
    renderNodeWireframe(grp,n.x,n.y,r,n.type,col);
    ng.appendChild(grp);
    const txt=document.createElementNS('http://www.w3.org/2000/svg','text');
    txt.setAttribute('x',n.x);txt.setAttribute('y',n.y+r+13);
    txt.setAttribute('text-anchor','middle');txt.setAttribute('font-size','9.5');
    txt.setAttribute('fill','#99aacc');txt.setAttribute('pointer-events','none');
    txt.textContent=n.label;
    ng.appendChild(txt);
  } else {
    // Palavras / Implícitos: word label node (circle + text)
    const wr=18+Math.round(norm*8);
    const bg=document.createElementNS('http://www.w3.org/2000/svg','circle');
    bg.setAttribute('cx',n.x);bg.setAttribute('cy',n.y);bg.setAttribute('r',wr);
    bg.setAttribute('fill',col+'18');bg.setAttribute('stroke',col);
    bg.setAttribute('stroke-width','1.2');bg.setAttribute('opacity','.85');
    grp.appendChild(bg);
    const wt=document.createElementNS('http://www.w3.org/2000/svg','text');
    wt.setAttribute('x',n.x);wt.setAttribute('y',n.y);
    wt.setAttribute('text-anchor','middle');wt.setAttribute('dominant-baseline','middle');
    wt.setAttribute('font-size','10');wt.setAttribute('font-weight','600');
    wt.setAttribute('fill',col);wt.setAttribute('pointer-events','none');
    wt.textContent=n.label;
    grp.appendChild(wt);
    ng.appendChild(grp);
    // PT label below
    const pt=document.createElementNS('http://www.w3.org/2000/svg','text');
    pt.setAttribute('x',n.x);pt.setAttribute('y',n.y+wr+10);
    pt.setAttribute('text-anchor','middle');pt.setAttribute('font-size','7.5');
    pt.setAttribute('fill',col+'88');pt.setAttribute('pointer-events','none');
    pt.textContent=n.pt;ng.appendChild(pt);
  }
});
// ── Palavras / Implícitos: technique polygon layer ──
if(cvMandalMode!=='solidos'){
  const pg=document.createElementNS('http://www.w3.org/2000/svg','g');
  pg.setAttribute('id','cv-polys');
  // Insert before nodes group
  g.insertBefore(pg,ng);
  TECHS.forEach((tech,ti)=>{
    const pts=tech.nodes.map(nid=>ni[nid]).filter(Boolean);
    if(!pts.length)return;
    const beltCol=BS[tech.belt]||'#888';
    if(pts.length===1){
      // Single node: dot
      const c=document.createElementNS('http://www.w3.org/2000/svg','circle');
      c.setAttribute('cx',pts[0].x);c.setAttribute('cy',pts[0].y);c.setAttribute('r',6);
      c.setAttribute('fill',beltCol);c.setAttribute('opacity','.06');
      c.setAttribute('data-ti',ti);pg.appendChild(c);
    } else if(pts.length===2){
      // Two nodes: line (like Jodan Uke)
      const ln=document.createElementNS('http://www.w3.org/2000/svg','line');
      ln.setAttribute('x1',pts[0].x);ln.setAttribute('y1',pts[0].y);
      ln.setAttribute('x2',pts[1].x);ln.setAttribute('y2',pts[1].y);
      ln.setAttribute('stroke',beltCol);ln.setAttribute('stroke-width','1.5');
      ln.setAttribute('opacity','.18');ln.setAttribute('data-ti',ti);
      // Fat hit area
      const hit=ln.cloneNode();hit.setAttribute('stroke-width','12');hit.setAttribute('opacity','0');
      hit.setAttribute('data-ti',ti);hit.style.cursor='pointer';
      pg.appendChild(ln);pg.appendChild(hit);
    } else {
      // Polygon
      const ptsStr=pts.map(p=>p.x.toFixed(1)+','+p.y.toFixed(1)).join(' ');
      const poly=document.createElementNS('http://www.w3.org/2000/svg','polygon');
      poly.setAttribute('points',ptsStr);
      poly.setAttribute('fill',beltCol);poly.setAttribute('fill-opacity','.04');
      poly.setAttribute('stroke',beltCol);poly.setAttribute('stroke-width','1.2');
      poly.setAttribute('opacity','.2');poly.setAttribute('data-ti',ti);
      const hit=poly.cloneNode();hit.setAttribute('fill-opacity','0');
      hit.setAttribute('stroke-width','12');hit.setAttribute('opacity','0');
      hit.setAttribute('data-ti',ti);hit.style.cursor='pointer';
      pg.appendChild(poly);pg.appendChild(hit);
    }
  });
  // Implícitos: add ghost edges + ghost nodes for implied axes
  if(cvMandalMode==='implicitos'){
    const ghostG=document.createElementNS('http://www.w3.org/2000/svg','g');
    ghostG.setAttribute('id','cv-ghosts');g.insertBefore(ghostG,ng);
    // Ghost node: ude (antebraço) — implied buki_mao for uke/barai
    // Position it near centroid of uke/barai nodes
    const ukeNodes=TECHS.filter(t=>t.action==='uke'||t.action==='barai')
      .flatMap(t=>t.nodes.map(id=>ni[id]).filter(Boolean));
    if(ukeNodes.length){
      const gx=ukeNodes.reduce((s,n)=>s+n.x,0)/ukeNodes.length;
      const gy=ukeNodes.reduce((s,n)=>s+n.y,0)/ukeNodes.length-45;
      const gc=document.createElementNS('http://www.w3.org/2000/svg','circle');
      gc.setAttribute('cx',gx.toFixed(1));gc.setAttribute('cy',gy.toFixed(1));gc.setAttribute('r',20);
      gc.setAttribute('fill','none');gc.setAttribute('stroke',NT.buki_mao);
      gc.setAttribute('stroke-width','1');gc.setAttribute('stroke-dasharray','5,4');gc.setAttribute('opacity','.3');
      ghostG.appendChild(gc);
      const gt=document.createElementNS('http://www.w3.org/2000/svg','text');
      gt.setAttribute('x',gx.toFixed(1));gt.setAttribute('y',gy.toFixed(1));
      gt.setAttribute('text-anchor','middle');gt.setAttribute('dominant-baseline','middle');
      gt.setAttribute('font-size','9');gt.setAttribute('font-style','italic');
      gt.setAttribute('fill',NT.buki_mao);gt.setAttribute('opacity','.35');gt.setAttribute('pointer-events','none');
      gt.textContent='Ude*';ghostG.appendChild(gt);
      // Dashed edges from uke techs to ghost ude
      TECHS.filter(t=>(t.action==='uke'||t.action==='barai')&&!t.nodes.some(id=>NMAP[id]?.type==='buki_mao')).forEach(t=>{
        const techPts=t.nodes.map(id=>ni[id]).filter(Boolean);
        if(!techPts.length)return;
        const tx=techPts.reduce((s,n)=>s+n.x,0)/techPts.length;
        const ty=techPts.reduce((s,n)=>s+n.y,0)/techPts.length;
        const el=document.createElementNS('http://www.w3.org/2000/svg','line');
        el.setAttribute('x1',tx.toFixed(1));el.setAttribute('y1',ty.toFixed(1));
        el.setAttribute('x2',gx.toFixed(1));el.setAttribute('y2',gy.toFixed(1));
        el.setAttribute('stroke',NT.buki_mao);el.setAttribute('stroke-width','1');
        el.setAttribute('stroke-dasharray','4,4');el.setAttribute('opacity','.15');
        ghostG.appendChild(el);
      });
    }
    // Dashed edges: tsuki → mae (already in graph)
    TECHS.filter(t=>t.action==='tsuki'&&!t.nodes.includes('mae')&&!t.nodes.includes('gyaku')&&!t.nodes.includes('yoko')).forEach(t=>{
      const maeN=ni['mae'];if(!maeN)return;
      const techPts=t.nodes.map(id=>ni[id]).filter(Boolean);if(!techPts.length)return;
      const tx=techPts.reduce((s,n)=>s+n.x,0)/techPts.length;
      const ty=techPts.reduce((s,n)=>s+n.y,0)/techPts.length;
      const el=document.createElementNS('http://www.w3.org/2000/svg','line');
      el.setAttribute('x1',tx.toFixed(1));el.setAttribute('y1',ty.toFixed(1));
      el.setAttribute('x2',maeN.x.toFixed(1));el.setAttribute('y2',maeN.y.toFixed(1));
      el.setAttribute('stroke',NT.direcao);el.setAttribute('stroke-width','1');
      el.setAttribute('stroke-dasharray','4,4');el.setAttribute('opacity','.12');
      ghostG.appendChild(el);
    });
    // Dashed edges: geri (no buki_pe) → chusoku/sokuto/kakato
    TECHS.filter(t=>t.action==='geri'&&!t.nodes.some(id=>NMAP[id]?.type==='buki_pe')).forEach(t=>{
      const dir=t.nodes.find(id=>NMAP[id]?.type==='direcao');
      const implied=dir==='yoko'?'sokuto':dir==='ushiro'?'kakato':'chusoku';
      const impN=ni[implied];if(!impN)return;
      const techPts=t.nodes.map(id=>ni[id]).filter(Boolean);if(!techPts.length)return;
      const tx=techPts.reduce((s,n)=>s+n.x,0)/techPts.length;
      const ty=techPts.reduce((s,n)=>s+n.y,0)/techPts.length;
      const el=document.createElementNS('http://www.w3.org/2000/svg','line');
      el.setAttribute('x1',tx.toFixed(1));el.setAttribute('y1',ty.toFixed(1));
      el.setAttribute('x2',impN.x.toFixed(1));el.setAttribute('y2',impN.y.toFixed(1));
      el.setAttribute('stroke',NT.buki_pe);el.setAttribute('stroke-width','1');
      el.setAttribute('stroke-dasharray','4,4');el.setAttribute('opacity','.12');
      ghostG.appendChild(el);
    });
  }
}
}

function setupCvEvents(svg,W,H){
const tip=document.getElementById('tip');
const ni={};SIM_NODES.forEach(n=>ni[n.id]=n);

// Edge hover
svg.addEventListener('mousemove',ev=>{
  const el=ev.target;
  const ti=el.dataset&&el.dataset.ti;
  if(ti!==undefined&&ti!==''){
    const tech=TECHS[+ti];
    if(tech){
      tip.style.opacity='1';
      tip.style.left=(ev.pageX+14)+'px';
      tip.style.top=(ev.pageY-10)+'px';
      tip.innerHTML='<b>'+tech.name+'</b>'
        +'<div style="font-size:11px;color:var(--text2);margin:2px 0">'+tech.pt+'</div>'
        +(tech.desc?'<div style="font-size:11px;line-height:1.4;margin-top:4px;color:var(--text)">'+tech.desc.slice(0,115)+(tech.desc.length>115?'…':'')+'</div>':'')
        +'<br><span class="belt-pill" style="background:'+BS[tech.belt]+'20;color:'+BS[tech.belt]+'">'+tech.belt+'</span>'
        +(tech.kataOnly?'<span style="font-size:10px;color:var(--text2);margin-left:6px">kata only</span>':'');
    }
  } else {
    tip.style.opacity='0';
  }
});
svg.addEventListener('mouseleave',()=>tip.style.opacity='0');

// Edge click → show tech in tooltip fixed
svg.addEventListener('click',ev=>{
  const el=ev.target;
  const ti=el.dataset&&el.dataset.ti;
  // Walk up DOM to find data-nid (now on <g> wrapper around polygons)
  let nidEl=el;
  while(nidEl&&nidEl!==svg&&!(nidEl.dataset&&nidEl.dataset.nid))nidEl=nidEl.parentElement;
  const nid=nidEl&&nidEl.dataset&&nidEl.dataset.nid;
  if(nid){
    showNodeDetail(nid);
  } else if(ti!==undefined&&ti!==''){
    showTechDetail(TECHS[+ti]);
  } else {
    renderKaratekaPanel();
  }
});

// Pan/zoom
let drag=null;
svg.addEventListener('mousedown',ev=>{if(ev.button===0)drag={x:ev.clientX-cvPan.x,y:ev.clientY-cvPan.y}});
window.addEventListener('mouseup',()=>drag=null);
window.addEventListener('mousemove',ev=>{
  if(!drag)return;
  cvPan.x=ev.clientX-drag.x;cvPan.y=ev.clientY-drag.y;
  const g=document.getElementById('cv-g');
  if(g)g.setAttribute('transform','translate('+cvPan.x+','+cvPan.y+') scale('+cvScale+')');
});
svg.addEventListener('wheel',ev=>{
  ev.preventDefault();
  const factor=ev.deltaY<0?1.12:.89;
  cvScale=Math.max(.25,Math.min(4,cvScale*factor));
  const g=document.getElementById('cv-g');
  if(g)g.setAttribute('transform','translate('+cvPan.x+','+cvPan.y+') scale('+cvScale+')');
},{passive:false});
}

