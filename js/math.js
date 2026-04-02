// ===== MATH / ENTROPY =====
function renderMath(){
const div=document.getElementById('math-content');
const _nBmao=NODES.filter(n=>n.type==='buki_mao').length;
const _nBpe=NODES.filter(n=>n.type==='buki_pe').length;
const _nAcao=NODES.filter(n=>n.type==='acao').length;
const _nDir=NODES.filter(n=>n.type==='direcao').length;
const _nAlvo=NODES.filter(n=>n.type==='alvo').length;
const _theoretical=(_nBmao+_nBpe)*_nAcao*_nDir*_nAlvo;
const _canonPct=(54/_theoretical*100).toFixed(1);
// Helper: SVG donut segment (cx,cy,r,startAngle,endAngle,color)
function donutArc(cx,cy,r,a1,a2,col,sw){
  const x1=cx+r*Math.cos(a1),y1=cy+r*Math.sin(a1);
  const x2=cx+r*Math.cos(a2),y2=cy+r*Math.sin(a2);
  const large=a2-a1>Math.PI?1:0;
  return `<path d="M${x1.toFixed(1)},${y1.toFixed(1)} A${r},${r} 0 ${large},1 ${x2.toFixed(1)},${y2.toFixed(1)}"
    fill="none" stroke="${col}" stroke-width="${sw||14}" stroke-linecap="butt"/>`;
}
// Helper: polyline for charts
function sparkline(pts,col,fill){
  const p=pts.map(([x,y])=>x.toFixed(1)+','+y.toFixed(1)).join(' ');
  return (fill?`<polygon points="${p} ${pts[pts.length-1][0].toFixed(1)},${pts[0][1].toFixed(1)} ${pts[0][0].toFixed(1)},${pts[0][1].toFixed(1)}" fill="${col}" fill-opacity=".12" stroke="none"/>`:'')
    +`<polyline points="${p}" fill="none" stroke="${col}" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"/>`;
}

div.innerHTML=`
<div class="math-s">
<h3>1. Funil de Complexidade</h3>
<p>O kihon seleciona 54 técnicas de um espaço teórico de ~${_theoretical.toLocaleString('pt-BR')} combinações (6 eixos semânticos: ${_nBmao}+${_nBpe} armas × ${_nAcao} ações × ${_nDir} direções × ${_nAlvo} alvos). Mais de ${(100-_canonPct).toFixed(1)}% são silêncios canônicos — escolhas deliberadas de Mas Oyama.</p>
<svg viewBox="0 0 420 130" style="width:100%;max-width:420px;display:block;margin:12px 0">
${(()=>{
  const rows=[['Espaço teórico (6 eixos)',_theoretical,'#334'],[' Corpus canônico IKO',54,'#c9a84c'],['  Kihon branca→amarela',42,'#8899bb'],['   Kihon faixa branca',31,'#33aa66']];
  const maxW=340;const H=24;const gap=6;
  return rows.map(([l,v,col],i)=>{
    const w=Math.max(4,Math.round(Math.sqrt(v/_theoretical)*maxW));
    const y=i*(H+gap);const x=(maxW-w)/2+40;
    const pct=i===0?'100%':(v/_theoretical*100).toFixed(1)+'%';
    return `<rect x="${x}" y="${y}" width="${w}" height="${H}" fill="${col}" rx="3"/>
<text x="38" y="${y+16}" text-anchor="end" font-size="10" fill="#7788aa">${v.toLocaleString('pt-BR')}</text>
<text x="${x+w+6}" y="${y+16}" font-size="10" fill="${col}">${pct}</text>`;
  }).join('');
})()}
<text x="210" y="126" text-anchor="middle" font-size="9" fill="#556677">escala √ — proporcional à "área" de possibilidades</text>
</svg>
<div class="insight"><strong>${_canonPct}% canonizado.</strong> Cada técnica do kihon representa ~${Math.round(_theoretical/54)} possibilidades não canonizadas. O silêncio é tão informativo quanto a escolha.</div>
</div>

<div class="math-s">
<h3>2. Exclusões Mútuas</h3>
<p>18% dos pares teóricos são excluídos. Fórmula: Pares válidos(N) = N×(N−1)×0,82</p>
<div style="display:flex;gap:20px;align-items:center;flex-wrap:wrap;margin:12px 0">
<svg viewBox="0 0 120 120" style="width:120px;flex-shrink:0">
${(()=>{
  const cx=60,cy=60,r=44,sw=18;
  const segs=[['Válidos (82%)',0.82,'#33aa66'],['Anatômico',0.045,'#e06060'],['Postural',0.068,'#cc7722'],['Espacial',0.022,'#4488dd'],['Pedagógico',0.045,'#8844dd']];
  let a=-Math.PI/2;let out='';
  segs.forEach(([l,f,col])=>{
    const a2=a+f*Math.PI*2;
    out+=donutArc(cx,cy,r,a,a2,col,sw);
    a=a2;
  });
  return out+'<text x="60" y="55" text-anchor="middle" font-size="13" font-weight="700" fill="#e8e8ee">82%</text><text x="60" y="70" text-anchor="middle" font-size="9" fill="#7788aa">válidos</text>';
})()}
</svg>
<div style="font-size:11px;color:var(--text2);line-height:1.8">
<span style="color:#33aa66">■</span> Válidos: 82% dos pares<br>
<span style="color:#e06060">■</span> Anatômico: câmara incompatível<br>
<span style="color:#cc7722">■</span> Postural: dachi incompatível<br>
<span style="color:#4488dd">■</span> Espacial: desequilíbrio de eixo<br>
<span style="color:#8844dd">■</span> Pedagógico: sem contexto de renraku
</div></div>
<table>
<tr><th>Par excluído</th><th>Razão</th></tr>
<tr><td>Mae Keage → Mae Geri (mesma perna)</td><td>Perna não recolheu para câmara</td></tr>
<tr><td>Ushiro Geri → Ushiro Geri</td><td>Dupla rotação 180° = perda de eixo</td></tr>
<tr><td>Tettsui → Oi Tsuki (sem mudar dachi)</td><td>Kiba Dachi ≠ Zenkutsu Dachi</td></tr>
<tr><td>Uke → Uke (sem kaeshi)</td><td>IKO: bloquear→bloquear não é renraku</td></tr>
</table>
</div>

<div class="math-s">
<h3>3. O Paradoxo da Canonização</h3>
<p>O vocabulário cresce devagar (31→54). As combinações explodem exponencialmente (480→1.370.880). O mesmo sistema gera ambas as curvas.</p>
<svg viewBox="0 0 420 140" style="width:100%;max-width:420px;display:block;margin:12px 0">
${(()=>{
  const belts=['B','L','Az','Am','V','M','S'];
  const pool=[31,37,42,47,47,52,54];
  const sess=[480,3200,15000,38000,38000,92000,1370880];
  const W=380,H=100,ox=20,oy=10;
  const n=belts.length;
  // Vocab line (left axis, linear)
  const maxP=54;
  const vpts=pool.map((v,i)=>[ox+i*(W/(n-1)),oy+H-(v/maxP)*H]);
  // Sessions line (right axis, log)
  const maxLog=Math.log10(1370880);const minLog=Math.log10(480);
  const spts=sess.map((v,i)=>[ox+i*(W/(n-1)),oy+H-((Math.log10(v)-minLog)/(maxLog-minLog))*H]);
  // Belt labels
  const labs=belts.map((b,i)=>`<text x="${(ox+i*(W/(n-1))).toFixed(0)}" y="${oy+H+14}" text-anchor="middle" font-size="9" fill="#556677">${b}</text>`).join('');
  // Axis labels
  const axL=`<text x="2" y="${oy+H/2}" text-anchor="middle" font-size="9" fill="#8899bb" transform="rotate(-90,8,${oy+H/2})">vocab</text>`;
  const axR=`<text x="415" y="${oy+H/2}" text-anchor="middle" font-size="9" fill="#c9a84c" transform="rotate(90,415,${oy+H/2})">sessões</text>`;
  return sparkline(vpts,'#8899bb',true)+sparkline(spts,'#c9a84c',true)+labs+axL+axR
    +`<text x="${ox}" y="${oy-2}" font-size="8" fill="#8899bb">31 téc.</text>`
    +`<text x="${ox+W}" y="${oy-2}" text-anchor="end" font-size="8" fill="#8899bb">54 téc.</text>`
    +`<text x="${ox}" y="${oy+H+28}" font-size="8" fill="#c9a84c">480 sessões</text>`
    +`<text x="${ox+W}" y="${oy+H+28}" text-anchor="end" font-size="8" fill="#c9a84c">1,37M sessões</text>`;
})()}
</svg>
<div class="insight"><strong>Paradoxo:</strong> Verde = Amarela em pool técnico (47 cada). Mas as sessões são idênticas (38.000). O exame de verde não adiciona vocabulário — adiciona profundidade: footwork, kumite, kata longos. H(vocab) cresce 16%; H(sessões) cresce 3.450×.</div>
</div>

<div class="math-s">
<h3>4. Funil Combinatório — 5 Blocos do Shodan</h3>
<p>Ido-geiko de 5 blocos: renraku sem repetição de família. A cada bloco o universo diminui.</p>
<svg viewBox="0 0 420 110" style="width:100%;max-width:420px;display:block;margin:12px 0">
${(()=>{
  const blocks=[[1,24,'Bloco 1'],[2,20,'Bloco 2'],[3,17,'Bloco 3'],[4,14,'Bloco 4'],[5,12,'Bloco 5']];
  const maxN=24;const barH=14;const gap=4;const maxW=260;const ox=80;
  return blocks.map(([i,n,l],idx)=>{
    const w=Math.round((n/maxN)*maxW);
    const y=idx*(barH+gap);
    return `<text x="${ox-4}" y="${y+11}" text-anchor="end" font-size="10" fill="#7788aa">${l}</text>`
      +`<rect x="${ox}" y="${y}" width="${w}" height="${barH}" fill="#c9a84c" opacity="${0.4+idx*0.1}" rx="2"/>`
      +`<text x="${ox+w+5}" y="${y+11}" font-size="10" fill="#c9a84c">${n} opções</text>`;
  }).join('')
  +`<text x="${ox}" y="98" font-size="10" fill="#e8d5a3" font-weight="600">24×20×17×14×12 = 1.370.880 sessões distintas</text>`
  +`<text x="${ox}" y="110" font-size="9" fill="#7788aa">≈ 137.000 são "boas sessões" (10% com equilíbrio jodan/chudan/gedan + mão/pé)</text>`;
})()}
</svg>
</div>

<div class="math-s">
<h3>5. Crescimento Exponencial por Exame</h3>
<p>O número de sessões de treino possíveis cresce em ordens de magnitude a cada faixa. A escala é logarítmica — cada degrau = ×10.</p>
<svg viewBox="0 0 420 130" style="width:100%;max-width:420px;display:block;margin:12px 0">
${(()=>{
  const data=[['Branca',480,'#8899bb'],['Azul',15000,'#4488ee'],['Amarela',38000,'#ddaa22'],['Verde',38000,'#33aa66'],['Marrom',92000,'#aa6633'],['Shodan',1370880,'#e8d5a3']];
  const W=360,H=90,ox=40,oy=10;const n=data.length;
  const minL=2,maxL=7;// log10 range 100 to 10M
  function ly(v){return oy+H-((Math.log10(v)-minL)/(maxL-minL))*H;}
  const pts=data.map(([l,v],i)=>[ox+i*(W/(n-1)),ly(v)]);
  // Grid lines at 10^2 to 10^6
  const grid=[2,3,4,5,6,7].map(e=>{
    const y=ly(Math.pow(10,e));
    const label=e<7?'10'+String.fromCharCode(0x2070+e):'10⁷';
    return `<line x1="${ox}" y1="${y.toFixed(0)}" x2="${ox+W}" y2="${y.toFixed(0)}" stroke="#1e1e30" stroke-width="1"/>`
      +`<text x="${ox-4}" y="${(y+4).toFixed(0)}" text-anchor="end" font-size="8" fill="#445566">${label}</text>`;
  }).join('');
  const labels=data.map(([l,v,col],i)=>{
    const x=ox+i*(W/(n-1));const y=ly(v);
    return `<circle cx="${x.toFixed(0)}" cy="${y.toFixed(0)}" r="4" fill="${col}"/>`
      +`<text x="${x.toFixed(0)}" y="${oy+H+14}" text-anchor="middle" font-size="9" fill="${col}">${l.slice(0,2)}</text>`;
  }).join('');
  return grid+sparkline(pts,'#c9a84c',true)+labels
    +`<text x="${ox+W}" y="${ly(1370880)-8}" text-anchor="end" font-size="9" fill="#e8d5a3">Shodan: ×31× Amarela</text>`;
})()}
</svg>
<div class="insight"><strong>Verde = Amarela:</strong> mesmo pool (47), mesmas sessões (38.000). O salto para Shodan (1,37M) é qualitativo — o sistema passa de vocabulário a navegação.</div>
</div>

<div class="math-s">
<h3>6. Silêncios Canônicos</h3>
<p>96,4% do espaço teórico não foi canonizado. Os silêncios revelam a gramática tanto quanto as escolhas.</p>
<svg viewBox="0 0 420 38" style="width:100%;max-width:420px;display:block;margin:8px 0">
${(()=>{
  const cats=[['Válidas, não canonizadas',3,'#c9a84c'],['Válida parcial (só kata)',1,'#8844dd'],['Inválida (biomecânica)',1,'#cc4444']];
  let x=0;const total=5;const W=380;const H=18;
  return cats.map(([l,n,col])=>{
    const w=Math.round((n/total)*W);
    const out=`<rect x="${x}" y="0" width="${w}" height="${H}" fill="${col}" opacity=".7" rx="2"/>`
      +`<text x="${x+w/2}" y="13" text-anchor="middle" font-size="9" fill="#0b0b10" font-weight="600">${n}</text>`
      +`<text x="${x+w/2}" y="32" text-anchor="middle" font-size="9" fill="${col}">${l}</text>`;
    x+=w+2;return out;
  }).join('');
})()}
</svg>
<table>
<tr><th>Combinação</th><th>Status</th><th>Por que vazio</th></tr>
<tr><td>Seiken Ushiro Tsuki</td><td style="color:#c9a84c">Válida, não canon.</td><td>Em Pinan San como Ushiro Tsuki — fora do kihon geiko</td></tr>
<tr><td>Shuto Mae Tsuki</td><td style="color:#cc4444">Inválida</td><td>Shuto é percussão lateral; trajetória tsuki incompatível</td></tr>
<tr><td>Empi Jodan</td><td style="color:#8844dd">Parcial (kata)</td><td>Age Empi só em kata — requer distância de clinch</td></tr>
<tr><td>Haisoku Ushiro Geri</td><td style="color:#c9a84c">Válida, não canon.</td><td>Kakato é a arma canônica para ushiro</td></tr>
<tr><td>Tettsui Jodan</td><td style="color:#c9a84c">Válida, não canon.</td><td>Em Pinan Ni; fora do kihon por requerer Kiba Dachi</td></tr>
</table>
</div>`;
}

