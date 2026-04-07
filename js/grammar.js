// ===== GRAMÁTICA =====
function renderGramatica(){
const div=document.getElementById('gram-root');
if(!div)return;
const NS='http://www.w3.org/2000/svg';

// ---- helpers ----
function mkSvg(w,h){
  const s=document.createElementNS(NS,'svg');
  s.setAttribute('viewBox',`0 0 ${w} ${h}`);
  s.setAttribute('width',w);s.setAttribute('height',h);
  return s;
}
function kanku(size){
  const s=mkSvg(size,size);
  const cx=size/2,cy=size/2,R=size*.43;
  const p=document.createElementNS(NS,'polygon');
  p.setAttribute('points',`${cx},${cy-R} ${cx+R},${cy} ${cx},${cy+R} ${cx-R},${cy}`);
  p.setAttribute('fill','none');p.setAttribute('stroke','#c9a84c');p.setAttribute('stroke-width','1.5');p.setAttribute('opacity','.8');
  const c=document.createElementNS(NS,'circle');
  c.setAttribute('cx',cx);c.setAttribute('cy',cy);c.setAttribute('r',R*.32);
  c.setAttribute('fill','none');c.setAttribute('stroke','#c9a84c');c.setAttribute('stroke-width','1');c.setAttribute('opacity','.8');
  [[cx,cy-R,cx,cy+R],[cx-R,cy,cx+R,cy]].forEach(([x1,y1,x2,y2])=>{
    const l=document.createElementNS(NS,'line');
    l.setAttribute('x1',x1);l.setAttribute('y1',y1);l.setAttribute('x2',x2);l.setAttribute('y2',y2);
    l.setAttribute('stroke','#c9a84c');l.setAttribute('stroke-width','.6');l.setAttribute('opacity','.3');
    s.appendChild(l);
  });
  s.appendChild(p);s.appendChild(c);
  return s;
}

// ---- Section 1: A Fórmula ----
const TYPE_META={
  acao:    {label:'Ação',    element:'Fogo',    solid:'Tetraedro',  role:'Verbo',       ex:'Tsuki · Geri · Uke · Uchi'},
  buki_mao:{label:'Arma·Mão',element:'Fogo+Terra',solid:'Hexagrama',role:'Instrumento', ex:'Seiken · Shuto · Empi · Nukite'},
  buki_pe: {label:'Arma·Pé', element:'Terra',   solid:'Losango',    role:'Instrumento', ex:'Chusoku · Sokuto · Hiza · Kakato'},
  direcao: {label:'Direção', element:'Ar',      solid:'Octaedro',   role:'Advérbio',    ex:'Mae · Mawashi · Yoko · Ushiro'},
  alvo:    {label:'Alvo',    element:'Éter',    solid:'Dodecaedro', role:'Objeto',      ex:'Jodan · Chudan · Gedan · Gammen'},
  dachi:   {label:'Postura', element:'Terra',   solid:'Cubo',       role:'Fundação',    ex:'Zenkutsu · Kiba · Kokutsu · Sanchin'},
  ido:     {label:'Movimento',element:'Água',   solid:'Icosaedro',  role:'Fluxo',       ex:'Okuri · Tobi · Ayumi'},
};

// formula demo with select
const s1=document.createElement('div');s1.className='gram-s';
s1.innerHTML='<h3>I. A Fórmula da Técnica</h3>'+
  '<p>Toda técnica Kyokushin é composta por exatamente <strong style="color:var(--text)">um valor de cada eixo semântico</strong>. A exclusão mútua é absoluta: não existe técnica com dois alvos, duas direções ou duas armas simultaneamente. A combinação de 5 eixos forma uma coordenada única no espaço técnico.</p>';
const demoWrap=document.createElement('div');
demoWrap.className='gram-demo-wrap';
const sel=document.createElement('select');
const _kihon=TECHS.filter(t=>!t.kataOnly);
const _kata=TECHS.filter(t=>t.kataOnly);
const _og1=document.createElement('optgroup');_og1.label='Kihon ('+_kihon.length+')';
_kihon.forEach(t=>{const o=document.createElement('option');o.value=TECHS.indexOf(t);o.textContent=t.name;_og1.appendChild(o);});
sel.appendChild(_og1);
const _og2=document.createElement('optgroup');_og2.label='Kata only ('+_kata.length+')';
_kata.forEach(t=>{const o=document.createElement('option');o.value=TECHS.indexOf(t);o.textContent=t.name;_og2.appendChild(o);});
sel.appendChild(_og2);
const formulaDiv=document.createElement('div');
formulaDiv.id='gram-formula-live';
function updateDemoFormula(){
  const tech=TECHS[+sel.value];if(!tech)return;
  const AXIS_ORDER=['buki_mao','buki_pe','acao','direcao','alvo','ido'];
  const AXIS_LBL={buki_mao:'Arma·Mão',buki_pe:'Arma·Pé',acao:'Ação',direcao:'Direção',alvo:'Alvo',ido:'Ido'};
  const ordered=[...tech.nodes].sort((a,b)=>AXIS_ORDER.indexOf(NMAP[a]?.type)-AXIS_ORDER.indexOf(NMAP[b]?.type));
  let html='<div class="gram-formula" style="margin-bottom:8px">';
  ordered.forEach((nid,i)=>{
    const node=NMAP[nid];if(!node)return;
    const c=NT[node.type];
    if(i>0)html+='<span class="gram-op" style="font-size:16px">·</span>';
    html+=`<div class="gram-slot" style="color:${c};border-color:${c}55;background:${c}12;min-width:52px">
      <div class="gram-slot-lbl" style="color:${c}">${AXIS_LBL[node.type]||node.type}</div>
      <div class="gram-slot-val">${node.label}</div>
      <div style="font-size:9px;color:${c}88;margin-top:1px">${node.pt}</div>
    </div>`;
  });
  if(tech.dachi){
    const d=NMAP[tech.dachi];
    if(d){
      const c=NT.dachi;
      html+=`<span class="gram-sep">|</span><div class="gram-slot" style="color:${c};border-color:${c}55;background:${c}12;min-width:52px">
        <div class="gram-slot-lbl" style="color:${c}">Dachi</div>
        <div class="gram-slot-val">${d.label}</div>
        <div style="font-size:9px;color:${c}88;margin-top:1px">${d.pt}</div>
      </div>`;
    }
  }
  const dIdoId=getIdo(tech.id);
  const dIdoNode=NMAP[dIdoId];
  if(dIdoNode){
    const c=NT.ido;
    html+=`<span class="gram-op" style="font-size:16px">·</span><div class="gram-slot" style="color:${c};border-color:${c}55;background:${c}12;min-width:52px">
      <div class="gram-slot-lbl" style="color:${c}">Ido</div>
      <div class="gram-slot-val">${dIdoNode.label}</div>
      <div style="font-size:9px;color:${c}88;margin-top:1px">${dIdoNode.pt}</div>
    </div>`;
  }
  html+='</div>';
  const beltC=BS[tech.belt]||'#888';
  html+=`<div style="font-size:11px;color:var(--text2)">Faixa: <span style="color:${beltC}">${tech.belt}</span>&emsp;Ação: ${tech.action}</div>`;
  formulaDiv.innerHTML=html;
}
sel.onchange=updateDemoFormula;
demoWrap.appendChild(sel);
demoWrap.appendChild(formulaDiv);
s1.appendChild(demoWrap);
updateDemoFormula();
div.appendChild(s1);

// ---- Section 2: Os Sólidos Platônicos ----
const s2=document.createElement('div');s2.className='gram-s';
s2.innerHTML='<h3>II. Os Sólidos Platônicos e os Eixos</h3>'+
  '<p>Platão (428–348 a.C.) associou os cinco sólidos regulares aos cinco elementos que compõem o cosmos. No Atlas Kyokushin, cada eixo semântico é mapeado a um sólido e elemento — não por decoração, mas porque as propriedades geométricas espelham o papel linguístico do eixo.</p>';
const grid=document.createElement('div');grid.className='gram-grid';
Object.entries(TYPE_META).forEach(([type,meta])=>{
  const col=NT[type];
  const card=document.createElement('div');
  card.className='gram-card';
  card.style.borderTopColor=col;card.style.borderTopWidth='2px';
  const svg=document.createElementNS(NS,'svg');
  svg.setAttribute('viewBox','0 0 48 48');svg.setAttribute('width','48');svg.setAttribute('height','48');
  const grp=document.createElementNS(NS,'g');
  grp.style.cssText=`animation:breathe 4s ease-in-out infinite;transform-box:fill-box;transform-origin:center`;
  renderNodeWireframe(grp,24,24,15,type,col);
  svg.appendChild(grp);
  card.innerHTML=`<div class="gp-kanji" style="font-size:11px;color:${col};letter-spacing:.08em;text-transform:uppercase">${meta.element}</div>`;
  card.insertBefore(svg,card.firstChild);
  const lb=document.createElement('div');lb.className='gc-label';lb.style.color=col;lb.textContent=meta.label;
  const sol=document.createElement('div');sol.className='gc-role';sol.textContent=meta.solid+' · '+meta.role;
  const ex=document.createElement('div');ex.className='gc-ex';ex.textContent=meta.ex;
  card.appendChild(lb);card.appendChild(sol);card.appendChild(ex);
  card.onclick=()=>{highlightType(type);switchTab('constelacao');};
  grid.appendChild(card);
});
s2.appendChild(grid);
div.appendChild(s2);

// ---- Section 3: Posicionalidade ----
const s3=document.createElement('div');s3.className='gram-s';
s3.innerHTML='<h3>III. Posicionalidade em Relação ao Karateca</h3>'+
  '<p>Os eixos de <em style="color:'+NT.alvo+'">Alvo</em> e <em style="color:'+NT.direcao+'">Direção</em> definem coordenadas no espaço tridimensional ao redor do corpo. Alvo é a <strong style="color:var(--text)">latitude</strong> (altura vertical), Direção é o <strong style="color:var(--text)">vetor</strong> (trajetória da técnica). São ortogonais — independentes entre si.</p>';
// SVG posicional: karateca + alturas + direções
const posW=400,posH=280;
const posSvg=mkSvg(posW,posH);
posSvg.style.cssText='width:100%;max-width:'+posW+'px;display:block;margin:12px 0';
// karateca silhoueta (frente, simplificada)
const kx=posW/2,ky=posH/2+10;
function rect(x,y,w,h,col,op){
  const r=document.createElementNS(NS,'rect');
  r.setAttribute('x',x-w/2);r.setAttribute('y',y-h/2);r.setAttribute('width',w);r.setAttribute('height',h);
  r.setAttribute('rx','3');r.setAttribute('fill',col);r.setAttribute('opacity',op||'.18');
  r.setAttribute('stroke',col);r.setAttribute('stroke-width','.6');r.setAttribute('stroke-opacity','.4');
  return r;
}
function txt(x,y,t,col,size,anchor){
  const el=document.createElementNS(NS,'text');
  el.setAttribute('x',x);el.setAttribute('y',y);el.setAttribute('fill',col||'#e8e8ee');
  el.setAttribute('font-size',size||10);el.setAttribute('text-anchor',anchor||'middle');
  el.setAttribute('dominant-baseline','middle');el.setAttribute('font-family','system-ui,sans-serif');
  el.textContent=t;return el;
}
function arrow(x1,y1,x2,y2,col){
  const g=document.createElementNS(NS,'g');
  const l=document.createElementNS(NS,'line');
  l.setAttribute('x1',x1);l.setAttribute('y1',y1);l.setAttribute('x2',x2);l.setAttribute('y2',y2);
  l.setAttribute('stroke',col);l.setAttribute('stroke-width','1.5');l.setAttribute('marker-end','url(#arr)');
  g.appendChild(l);return g;
}
// defs: arrowhead
const defs=document.createElementNS(NS,'defs');
const mk=document.createElementNS(NS,'marker');
mk.setAttribute('id','arr');mk.setAttribute('markerWidth','7');mk.setAttribute('markerHeight','7');
mk.setAttribute('refX','5');mk.setAttribute('refY','3.5');mk.setAttribute('orient','auto');
const mpath=document.createElementNS(NS,'path');
mpath.setAttribute('d','M0,0 L0,7 L7,3.5 z');mpath.setAttribute('fill','#8866ee');
mk.appendChild(mpath);defs.appendChild(mk);posSvg.appendChild(defs);
// body parts
posSvg.appendChild(rect(kx,ky-90,18,18,'#c9a84c',.2)); // cabeça
posSvg.appendChild(rect(kx,ky-60,26,38,'#c9a84c',.14)); // pescoço+jodan
posSvg.appendChild(rect(kx,ky-16,32,44,'#c9a84c',.1)); // chudan
posSvg.appendChild(rect(kx,ky+30,14,30,'#c9a84c',.08)); // abdômen
posSvg.appendChild(rect(kx-10,ky+66,10,32,'#c9a84c',.07)); // perna esq
posSvg.appendChild(rect(kx+10,ky+66,10,32,'#c9a84c',.07)); // perna dir
// altitude bands
[[ky-80,'JODAN','alto · cabeça/rosto',NT.alvo,.18],
 [ky-10,'CHUDAN','médio · tronco/costelas',NT.alvo,.14],
 [ky+58,'GEDAN','baixo · pernas/joelhos',NT.alvo,.1]].forEach(([y,lbl,sub,col,op])=>{
  const ln=document.createElementNS(NS,'line');
  ln.setAttribute('x1',kx-50);ln.setAttribute('y1',y);ln.setAttribute('x2',posW-20);ln.setAttribute('y2',y);
  ln.setAttribute('stroke',col);ln.setAttribute('stroke-width','.6');ln.setAttribute('stroke-dasharray','3,3');ln.setAttribute('opacity',op+.1);
  posSvg.appendChild(ln);
  posSvg.appendChild(txt(posW-18,y,lbl,col,8,'end'));
  posSvg.appendChild(txt(posW-18,y+9,sub,col+'88',7,'end'));
});
// gammen/hizo/kansetsu dots
[[kx+3,ky-83,'gammen','rosto'],[kx+16,ky-28,'hizo','costela'],[kx+16,ky+2,'kansetsu','articulação']].forEach(([x,y,id,pt])=>{
  const c=document.createElementNS(NS,'circle');
  c.setAttribute('cx',x);c.setAttribute('cy',y);c.setAttribute('r','3');
  c.setAttribute('fill',NT.alvo);c.setAttribute('opacity','.6');
  posSvg.appendChild(c);
  posSvg.appendChild(txt(x+5,y,id,NT.alvo+'aa',7,'start'));
});
const dirData=[
  {lbl:'Mae',sub:'frontal',a:-Math.PI/2},
  {lbl:'Ushiro',sub:'posterior',a:Math.PI/2},
  {lbl:'Yoko',sub:'lateral',a:0},
  {lbl:'Mawashi',sub:'circular',a:-Math.PI/4},
  {lbl:'Gyaku',sub:'reverso',a:Math.PI},
  {lbl:'Age',sub:'ascendente',a:-Math.PI*0.35},
  {lbl:'Soto',sub:'fora→dentro',a:-Math.PI*0.65},
];
const dirR=62,dirLx=90,dirLy=posH/2-20;
// draw mini direction compass on left
const dcx=dirLx,dcy=dirLy;
const dcirc=document.createElementNS(NS,'circle');
dcirc.setAttribute('cx',dcx);dcirc.setAttribute('cy',dcy);dcirc.setAttribute('r',dirR);
dcirc.setAttribute('fill','none');dcirc.setAttribute('stroke',NT.direcao);dcirc.setAttribute('stroke-width','.5');dcirc.setAttribute('opacity','.15');
posSvg.appendChild(dcirc);
dirData.forEach((d,i)=>{
  const ax=dcx+dirR*.7*Math.cos(d.a),ay=dcy+dirR*.7*Math.sin(d.a);
  const lx=dcx+dirR*1.1*Math.cos(d.a),ly=dcy+dirR*1.1*Math.sin(d.a);
  const l=document.createElementNS(NS,'line');
  l.setAttribute('x1',dcx);l.setAttribute('y1',dcy);l.setAttribute('x2',ax.toFixed(1));l.setAttribute('y2',ay.toFixed(1));
  l.setAttribute('stroke',NT.direcao);l.setAttribute('stroke-width','1.4');l.setAttribute('opacity','.7');
  posSvg.appendChild(l);
  const labelAnchor=Math.cos(d.a)>0.3?'start':Math.cos(d.a)<-0.3?'end':'middle';
  posSvg.appendChild(txt(lx.toFixed(1),ly.toFixed(1),d.lbl,NT.direcao,8,labelAnchor));
  if(d.sub)posSvg.appendChild(txt(lx.toFixed(1),(+ly+8).toFixed(1),d.sub,NT.direcao+'66',6,labelAnchor));
  // hit area: click direction → highlight in constellation
  const hit=document.createElementNS(NS,'circle');
  hit.setAttribute('cx',lx.toFixed(1));hit.setAttribute('cy',ly.toFixed(1));
  hit.setAttribute('r','14');hit.setAttribute('fill','transparent');hit.style.cursor='pointer';
  const nodeId=d.lbl.toLowerCase();
  hit.onclick=()=>{switchTab('constelacao');
    if(NMAP[nodeId])highlightNode(nodeId); else highlightType('direcao');};
  hit.onmouseenter=()=>{hit.setAttribute('fill',NT.direcao+'22');};
  hit.onmouseleave=()=>{hit.setAttribute('fill','transparent');};
  posSvg.appendChild(hit);
});
posSvg.appendChild(txt(dcx,dcy-dirR*1.3,'DIREÇÃO',NT.direcao,8,'middle'));
posSvg.appendChild(txt(posW-10,20,'ALVO',NT.alvo,8,'end'));
s3.appendChild(posSvg);
const posNote=document.createElement('p');
posNote.style.cssText='font-size:11px;color:var(--text2)';
posNote.innerHTML='<strong style="color:var(--text)">Leitura:</strong> Mawashi Geri Jodan = vetor circular + nível alto. Yoko Geri Chudan = vetor lateral + nível médio. A combinação dos dois eixos posiciona a técnica em qualquer ponto do espaço tridimensional.';
s3.appendChild(posNote);
div.appendChild(s3);

// ---- Section 4: Silêncio Canônico ----
const s4=document.createElement('div');s4.className='gram-s';
s4.innerHTML='<h3>IV. O Silêncio Canônico</h3>'+
  '<p>O espaço teórico de combinações dos <strong style="color:var(--text)">5 eixos de combinação</strong> (arma, ação, direção, alvo — mais dachi contextual) é vastíssimo. O currículo IKO1 canoniza apenas 54 técnicas — uma fração radical.</p>';
const silence=document.createElement('div');silence.className='gram-silence';
// compute counts
const nAcao=NODES.filter(n=>n.type==='acao').length;
const nBmao=NODES.filter(n=>n.type==='buki_mao').length;
const nBpe=NODES.filter(n=>n.type==='buki_pe').length;
const nDir=NODES.filter(n=>n.type==='direcao').length;
const nAlvo=NODES.filter(n=>n.type==='alvo').length;
const nDachi=NODES.filter(n=>n.type==='dachi').length;
const theoretical=(nBmao+nBpe)*nAcao*nDir*nAlvo;
const canonical=TECHS.filter(t=>!t.kataOnly).length;
const pct=(canonical/theoretical*100).toFixed(1);
silence.innerHTML=`<strong>Matemática do Currículo</strong>
(${nBmao}+${nBpe}) armas × ${nAcao} ações × ${nDir} direções × ${nAlvo} alvos = <span style="color:var(--text)">${theoretical.toLocaleString()} combinações teóricas</span><br>
Currículo kihon IKO1: <span style="color:var(--gold)">${canonical} técnicas ensinadas</span> = <strong style="color:var(--gold)">${pct}% do espaço teórico</strong><br><br>
Mas Oyama não escolheu o que ensinar. Escolheu o que <em>não</em> ensinar. O silêncio de ${theoretical-canonical} combinações é o currículo invisível — a contenção que dá forma ao sistema.
<div style="margin-top:8px;font-size:11px">→ Ver análise completa na aba <a href="#" onclick="switchTab('math');return false" style="color:var(--gold)">Matemática</a></div>`;
s4.appendChild(silence);
div.appendChild(s4);

// ---- Section 5: 極真 — Kyokushin ----
const s5=document.createElement('div');s5.className='gram-s';
s5.innerHTML='<h3>V. 極真 — Kyokushin: A Verdade Última</h3>';
const kkCard=document.createElement('div');kkCard.className='gram-kk';
const kkSvg=kanku(80);kkSvg.className='gram-kk-symbol';
const kkText=document.createElement('div');kkText.className='gram-kk-text';
kkText.innerHTML=`
<div class="gram-kanji-hero">極真</div>
<div class="gram-kanji-sub" style="margin-bottom:12px">KYOKUSHIN · きょくしん</div>
<p><strong style="color:var(--text)">極 (Kyoku)</strong> — extremo, último limite, o ponto além do qual não há mais.<br>
<strong style="color:var(--text)">真 (Shin)</strong> — verdade, realidade, aquilo que é genuíno.<br><br>
Kyokushin = <em>a busca extrema pela verdade através do corpo</em>. Não como metáfora — como método.</p>
<blockquote>"O caminho do Kyokushin é a busca da verdade através do treinamento duro. Osu — perseverar sob pressão."<br><span style="font-size:10px;opacity:.6">— Mas Oyama, fundador</span></blockquote>`;
kkCard.appendChild(kkSvg);kkCard.appendChild(kkText);
s5.appendChild(kkCard);
// Kanku explanation
const kkExp=document.createElement('p');
kkExp.style.cssText='font-size:12px;color:var(--text2);line-height:1.7;margin-top:10px';
kkExp.innerHTML='O gesto do <strong style="color:var(--text)">Kanku Dai</strong> — primeiro kata do Shodan — abre os braços formando um losango com os polegares e indicadores apontando para o céu: <strong style="color:var(--gold)">看空</strong> (kan = ver, ku = vazio/céu). Ver através do vazio. O mesmo símbolo está no centro da constelação deste atlas.';
s5.appendChild(kkExp);
// 3 pillars
const pillarsTitle=document.createElement('p');
pillarsTitle.style.cssText='font-size:12px;color:var(--text2);margin-top:12px;margin-bottom:8px';
pillarsTitle.textContent='Os três pilares do Kyokushin:';
s5.appendChild(pillarsTitle);
const pillars=document.createElement('div');pillars.className='gram-3pillar';
[{k:'技',jp:'WAZA',pt:'Técnica',desc:'O movimento preciso. A mecânica do corpo. A gramática desta atlas.'},
 {k:'体',jp:'TAI',pt:'Corpo',desc:'A estrutura física. Condicionamento, estrutura óssea, resistência.'},
 {k:'心',jp:'KOKORO',pt:'Espírito',desc:'A mente que não quebra. A determinação além da dor. OSU.'}
].forEach(p=>{
  const el=document.createElement('div');el.className='gram-pillar';
  el.innerHTML=`<span class="gp-kanji">${p.k}</span><div class="gp-jp">${p.jp}</div><div class="gp-pt">${p.pt}</div><div class="gp-desc">${p.desc}</div>`;
  pillars.appendChild(el);
});
s5.appendChild(pillars);
// lineage
const lin=document.createElement('div');
lin.style.cssText='margin-top:14px;padding:10px 14px;background:var(--bg2);border-radius:8px;border:1px solid var(--border);font-size:11px;color:var(--text2);line-height:1.8';
lin.innerHTML='<strong style="color:var(--text);display:block;margin-bottom:4px;letter-spacing:.06em">LINHAGEM IKO1</strong>Mas Oyama (大山倍達) → IKO Honbu → CBKKO (Brasil) → este atlas<br><span style="opacity:.6">Shihan Choi Bae-Dal (최배달) · 1923–1994 · fundou a Kyokushinkaikan em 1964</span>';
s5.appendChild(lin);
div.appendChild(s5);

// ---- Section 6: Gramática do Silêncio nos Nomes ----
const s6=document.createElement('div');s6.className='gram-s';
s6.innerHTML=`<h3>VI. A Gramática do Silêncio nos Nomes</h3>
<p>Nomes canônicos são <strong style="color:var(--text)">diferenciais mínimos</strong> — mencionam apenas o que distingue a técnica dentro de sua família. O restante é elidido por convenção semântica. A ausência de um eixo no nome não é um vazio: é um pressuposto.</p>`;

const elisionTable=document.createElement('table');elisionTable.className='elision-table';
elisionTable.innerHTML=`<thead><tr>
  <th>Ação</th><th>Presente no nome</th><th>Elidido</th><th>Motivo</th>
</tr></thead><tbody>
<tr><td class="dim-name" style="color:${NT.acao}">Tsuki</td>
  <td><span style="color:${NT.buki_mao}">Arma·Mão</span> + <span style="color:${NT.alvo}">Alvo</span></td>
  <td><span style="color:${NT.direcao}">mae</span> (direção)</td>
  <td>Socos lineares são frontal por definição — <em>mae</em> é o padrão absoluto.</td></tr>
<tr><td class="dim-name" style="color:${NT.acao}">Uchi</td>
  <td><span style="color:${NT.buki_mao}">Arma·Mão</span> + <span style="color:${NT.alvo}">Alvo</span> ou <span style="color:${NT.direcao}">Direção</span></td>
  <td>Raramente elidido — o instrumento é a identidade do golpe percussivo.</td>
  <td>A arma define a forma do arco; sem ela não há distinção.</td></tr>
<tr><td class="dim-name" style="color:${NT.acao}">Geri / Keage</td>
  <td><span style="color:${NT.direcao}">Direção</span> + <span style="color:${NT.acao}">Ação</span></td>
  <td><span style="color:${NT.buki_pe}">Arma·Pé</span> (chusoku / sokuto / kakato)</td>
  <td>A superfície do pé é determinada pela direção: Mae → chusoku, Yoko → sokuto, Ushiro → kakato. Nomes o omitem porque é redundante.</td></tr>
<tr><td class="dim-name" style="color:${NT.acao}">Uke / Barai</td>
  <td><span style="color:${NT.direcao}">Direção</span> + <span style="color:${NT.alvo}">Alvo</span></td>
  <td><span style="color:${NT.buki_mao}">Arma·Mão</span> (antebraço)</td>
  <td>Bloqueios usam o antebraço estrutural por padrão. Quando outra superfície é usada (Shuto, Koken), ela <em>aparece</em> no nome.</td></tr>
</tbody>`;
s6.appendChild(elisionTable);

// Near-duplicate case study
const ndTitle=document.createElement('p');
ndTitle.style.cssText='margin-top:16px;font-size:12px;color:var(--text2);line-height:1.7';
ndTitle.innerHTML='<strong style="color:var(--text)">Paradoxo near-duplicate:</strong> dois nomes distintos que ocupam o mesmo endereço no grafo.';
s6.appendChild(ndTitle);

const ndPair=document.createElement('div');ndPair.className='nd-pair';
[{name:'Uchi Mawashi Geri',pt:'chute circular interno',nodes:['geri','haisoku','mawashi'],diff:'Uchi = arco de <em>dentro para fora</em>. Informação só no nome.'},
 {name:'Soto Mawashi Geri',pt:'chute circular externo',nodes:['geri','haisoku','mawashi'],diff:'Soto = arco de <em>fora para dentro</em>. Mesmo endereço, vetor oposto.'}
].forEach(({name,pt,nodes,diff})=>{
  const c=document.createElement('div');c.className='nd-card';
  const nodesHtml=nodes.map(nid=>{
    const n=NMAP[nid];
    return n?`<span class="nd-node" style="color:${NT[n.type]}">${n.label}</span>`:'';
  }).join('');
  c.innerHTML=`<div class="nd-name">${name}</div>
    <div style="font-size:11px;color:var(--text2);margin-bottom:6px">${pt}</div>
    <div class="nd-nodes">${nodesHtml}</div>
    <div class="nd-diff">${diff}</div>`;
  ndPair.appendChild(c);
});
s6.appendChild(ndPair);

const ndConclusion=document.createElement('div');ndConclusion.className='gram-silence';
ndConclusion.innerHTML='<strong>Consequência:</strong> o grafo de nós captura a <em>estrutura semântica profunda</em> — as dimensões anatômicas e físicas. O nome canônico captura distinções <em>táticas</em> que o grafo não modela. São dois sistemas complementares, não redundantes.';
s6.appendChild(ndConclusion);
div.appendChild(s6);

// ---- Section 7: Reflexão Estética ----
const s7=document.createElement('div');s7.className='gram-s';
s7.innerHTML=`<h3>VII. O Atlas como Fenomenologia</h3>
<p>Este atlas não é um banco de dados — é uma <strong style="color:var(--text)">fenomenologia do movimento</strong>. A constelação não lista técnicas: mapeia o espaço onde elas existem. A diferença é ontológica. Um catálogo pergunta "o que existe?". Uma fenomenologia pergunta "como é possível que isso exista?".</p>
<p>54 de 10.584 combinações teóricas — menos de 0,4% do espaço possível. Oyama não ensinou 10.530 técnicas. A restrição não é pobreza de vocabulário: é <strong style="color:var(--text)">definição de identidade</strong>. O Kyokushin é precisamente o que resta quando tudo o mais é silenciado. O currículo é um ato de exclusão deliberada — uma escultura obtida por subtração.</p>
<p>Os sólidos platônicos não são decoração. São a afirmação de que o corpo, ao se mover, resolve as mesmas geometrias que o universo resolve ao existir. Cada kata é um teorema. Cada técnica é um axioma. A constelação é o diagrama de provas de um sistema que tem cinquenta anos de verificação empírica no tatame.</p>`;

const linkBtn=document.createElement('button');
linkBtn.className='gen-btn';linkBtn.style.cssText='margin-top:14px;font-size:12px;padding:8px 18px';
linkBtn.textContent='→ Explorar no Construtor';
linkBtn.onclick=()=>switchTab('construtor');
s7.appendChild(linkBtn);
div.appendChild(s7);

// ---- Section 8: Elementos Implícitos e suas Cadeias ----
const s8=document.createElement('div');s8.className='gram-s';
s8.innerHTML=`<h3>VIII. O que o Nome Não Diz — Eixos Implícitos</h3>
<p>O nome canônico é um diferencial mínimo: menciona apenas o que distingue a técnica dentro de sua família. O restante é <strong style="color:var(--text)">pressuposição linguística</strong> — o falante nativo sabe; o iniciante não. Esta seção torna explícito o que o nome cala.</p>`;

const chainData=[
  {tech:'Seiken Chudan Tsuki',nodes:['seiken','chudan','tsuki'],implicit:{id:'mae',type:'direcao',label:'Mae'},
   rule:'Tsuki é por definição linear-frontal. A direção <em>mae</em> nunca aparece no nome porque é o vetor padrão absoluto — não há soco "Seiken Chudan Mae Tsuki" porque seria redundante.',
   consequence:'Todos os socos são frontais a não ser que um modificador explícito apareça (Gyaku, Ushiro, Yoko).'},
  {tech:'Mae Geri',nodes:['mae','geri'],implicit:{id:'chusoku',type:'buki_pe',label:'Chusoku'},
   rule:'Geri frontal usa naturalmente a meia-pata (chusoku). A trajetória linear expõe a frente do pé.',
   consequence:'Quando a arma muda, ela aparece: Kakato Geri, Hiza Geri. A ausência de nome de arma ≡ chusoku.'},
  {tech:'Jodan Uke',nodes:['jodan','uke'],implicit:{id:'age',type:'direcao',label:'Age'},
   rule:'Defender contra ataque alto exige movimento ascendente. O vetor <em>age</em> (subida) é ditado pela física — o braço precisa subir para interceptar o ataque ao rosto.',
   consequence:'Jodan Uke <em>como linha</em> vs <em>como triângulo</em> — veja o diagrama abaixo.'},
  {tech:'Chudan Soto Uke',nodes:['chudan','uke'],implicit:{id:'ude',type:'buki_mao',label:'Ude (antebraço)'},
   rule:'Bloqueios usam o antebraço por convenção defensiva. Quando Shuto ou Koken são usados, o nome os menciona explicitamente.',
   consequence:'Shuto Jodan Uke nomeia a arma porque ela é excepcional. Uke sem arma = antebraço.'},
];
const chainDiv=document.createElement('div');chainDiv.className='impl-chain';
chainData.forEach(({tech,nodes,implicit,rule,consequence})=>{
  const row=document.createElement('div');row.className='impl-row';
  const nc=NT[NMAP[implicit.id]?.type]||'#888';
  row.innerHTML=`<div class="impl-left">
    <div class="impl-tech">${tech}</div>
    <div style="font-size:10px;margin-top:3px;display:flex;flex-wrap:wrap;gap:3px">
      ${nodes.map(nid=>{const n=NMAP[nid];return n?`<span style="color:${NT[n.type]};font-size:10px;background:${NT[n.type]}15;padding:1px 6px;border-radius:3px">${n.label}</span>`:''}).join('')}
    </div>
  </div>
  <div class="impl-arrow">→</div>
  <div style="flex:1">
    <div style="font-size:10px;margin-bottom:4px"><span style="color:${nc};background:${nc}18;padding:1px 8px;border-radius:4px;border:1px dashed ${nc}55">+ ${implicit.label} <span style="opacity:.6;font-size:9px">(implícito)</span></span></div>
    <div class="impl-rule">${rule}</div>
    ${consequence?`<div style="font-size:10px;color:var(--gold);margin-top:3px;font-style:italic">${consequence}</div>`:''}
  </div>`;
  chainDiv.appendChild(row);
});
s8.appendChild(chainDiv);

// Jodan Uke: line vs triangle diagram
const diagTitle=document.createElement('p');
diagTitle.style.cssText='margin-top:18px;margin-bottom:8px;font-size:12px;font-weight:600;color:var(--text)';
diagTitle.textContent='Jodan Uke — linha vs triângulo';
s8.appendChild(diagTitle);

const diagP=document.createElement('p');
diagP.style.cssText='font-size:11px;color:var(--text2);line-height:1.7;margin-bottom:10px';
diagP.innerHTML='No <strong style="color:var(--text)">corpus</strong> (esquerda), Jodan Uke tem 2 nós → linha reta. Com o eixo <em>implícito Age</em> (direita), a técnica se completa em triângulo. O mesmo nome, duas geometrias — a segunda é mais honesta semanticamente.';
s8.appendChild(diagP);

const NS8='http://www.w3.org/2000/svg';
const diagSvg=document.createElementNS(NS8,'svg');
diagSvg.setAttribute('viewBox','0 0 360 140');diagSvg.setAttribute('width','100%');
diagSvg.setAttribute('height','140');diagSvg.style.cssText='max-width:420px;display:block;margin:0 auto 16px';

function mkN8(tag,attrs){const e=document.createElementNS(NS8,tag);Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,v));return e;}
function wordNode8(x,y,label,col,ghost){
  const g=document.createElementNS(NS8,'g');
  const circ=mkN8('circle',{cx:x,cy:y,r:22,fill:col+'18',stroke:col,
    'stroke-width':ghost?'1':'1.5','stroke-dasharray':ghost?'4,3':'none',opacity:ghost?'.5':'1'});
  const txt=mkN8('text',{x:x,y:y,'text-anchor':'middle','dominant-baseline':'middle',
    'font-size':10,'font-weight':ghost?'400':'600',fill:col,opacity:ghost?.4:.9,'pointer-events':'none'});
  txt.textContent=label;
  g.appendChild(circ);g.appendChild(txt);return g;
}

// Left panel: corpus (line)
const Lx=85,Ly=70;
const leftG=document.createElementNS(NS8,'g');
// Title
const lt=mkN8('text',{x:Lx,y:15,'text-anchor':'middle','font-size':9,fill:'#99aacc','letter-spacing':'.06em'});
lt.textContent='CORPUS (2 nós)';leftG.appendChild(lt);
// Jodan node (alvo, green, top)
const jX=Lx,jY=38;const uX=Lx,uY=105;
const line1=mkN8('line',{x1:jX,y1:jY,x2:uX,y2:uY,stroke:'#44aa66',
  'stroke-width':1.5,opacity:.45});
leftG.appendChild(line1);
leftG.appendChild(wordNode8(jX,jY,'Jodan',NT.alvo,false));
leftG.appendChild(wordNode8(uX,uY,'Uke',NT.acao,false));
diagSvg.appendChild(leftG);

// Arrow between panels
const midX=178;
const arrowG=document.createElementNS(NS8,'g');
const aLine=mkN8('line',{x1:midX-12,y1:70,x2:midX+12,y2:70,
  stroke:'#c9a84c','stroke-width':1.5,opacity:.6});
const aHead=mkN8('polygon',{points:`${midX+12},67 ${midX+20},70 ${midX+12},73`,
  fill:'#c9a84c',opacity:.6});
arrowG.appendChild(aLine);arrowG.appendChild(aHead);
const plusT=mkN8('text',{x:midX,y:90,'text-anchor':'middle','font-size':8,fill:'#c9a84c',opacity:.5});
plusT.textContent='+ implícito';arrowG.appendChild(plusT);
diagSvg.appendChild(arrowG);

// Right panel: with implicit Age
const Rx=280,Ry=70;
const rightG=document.createElementNS(NS8,'g');
const rt=mkN8('text',{x:Rx,y:15,'text-anchor':'middle','font-size':9,fill:'#99aacc','letter-spacing':'.06em'});
rt.textContent='COM IMPLÍCITO (3 nós)';rightG.appendChild(rt);
const rjX=Rx,rjY=38,ruX=Rx-35,ruY=110,raX=Rx+35,raY=110;
// Filled triangle
const tri=mkN8('polygon',{
  points:`${rjX},${rjY} ${ruX},${ruY} ${raX},${raY}`,
  fill:NT.alvo+'10',stroke:NT.alvo,'stroke-width':1,opacity:.35});
rightG.appendChild(tri);
// Edges
[[rjX,rjY,ruX,ruY,NT.alvo],[rjX,rjY,raX,raY,NT.direcao+'88'],[ruX,ruY,raX,raY,NT.direcao+'55']].forEach(([x1,y1,x2,y2,col])=>{
  rightG.appendChild(mkN8('line',{x1,y1,x2,y2,stroke:col,'stroke-width':1.5,opacity:.4}));
});
rightG.appendChild(wordNode8(rjX,rjY,'Jodan',NT.alvo,false));
rightG.appendChild(wordNode8(ruX,ruY,'Uke',NT.acao,false));
rightG.appendChild(wordNode8(raX,raY,'Age*',NT.direcao,true));
diagSvg.appendChild(rightG);

s8.appendChild(diagSvg);

const s8Note=document.createElement('div');s8Note.className='gram-silence';
s8Note.innerHTML='<strong>Consequência para o Construtor:</strong> no modo <em>Implícitos</em> da Constelação, cada técnica exibe tanto os nós explícitos (sólidos) quanto os implícitos (fantasma/tracejado). Jodan Uke passa de linha a triângulo — a geometria revela a gramática completa.';
s8.appendChild(s8Note);

const consBtn=document.createElement('button');
consBtn.className='gen-btn';consBtn.style.cssText='margin-top:12px;font-size:12px;padding:7px 16px';
consBtn.innerHTML='→ Ver na Constelação (modo Implícitos)';
consBtn.onclick=()=>{switchTab('constelacao');setMandalMode('implicitos');};
s8.appendChild(consBtn);
div.appendChild(s8);
}

