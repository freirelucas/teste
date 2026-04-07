// ===== CONSTRUTOR PT→JP =====
// Elision rules: canonical names omit "obvious" or "default" axes
// TSUKI: mentions buki_mao + alvo, drops mae (default direction)
// GERI/KEAGE: mentions direcao, drops buki_pe (standard foot weapons), drops alvo if chudan
// UKE/BARAI: mentions direcao + alvo, drops buki unless shuto/koken
// UCHI: mentions buki_mao + alvo or direcao
const ELISION_RULES={
  tsuki:{keep:['buki_mao','alvo'],optional:['direcao'],drop_if:{direcao:'mae'},order:['buki_mao','alvo','direcao','acao']},
  uchi: {keep:['buki_mao'],choose:['alvo','direcao'],order:['buki_mao','alvo','direcao','acao']},
  geri: {keep:['direcao'],optional:['alvo'],buki_pe_only:['hiza','kansetsu'],drop_if:{alvo:'chudan'},order:['alvo','direcao','buki_pe','acao']},
  keage:{keep:['direcao'],buki_pe_only:['hiza'],order:['direcao','buki_pe','acao']},
  uke:  {keep:['direcao','alvo'],buki_mao_only:['shuto','koken'],order:['buki_mao','direcao','alvo','acao']},
  barai:{keep:['alvo'],optional:['direcao'],buki_mao_only:['shuto'],order:['buki_mao','alvo','direcao','acao']},
};

function buildCanonicalName(acao,bukim,bukipe,dir,alvo){
  if(!acao)return null;
  const L=id=>id&&NMAP[id]?NMAP[id].label:null;
  const r=ELISION_RULES[acao]||{order:['buki_mao','buki_pe','direcao','alvo','acao']};
  const parts=[];
  if(acao==='tsuki'){
    if(bukim)parts.push(L(bukim));
    if(alvo)parts.push(L(alvo));
    if(dir&&dir!=='mae')parts.push(L(dir));
    parts.push(L(acao));
  } else if(acao==='uchi'){
    if(bukim)parts.push(L(bukim));
    if(alvo)parts.push(L(alvo));
    else if(dir)parts.push(L(dir));
    parts.push(L(acao));
  } else if(acao==='geri'||acao==='keage'){
    if(alvo&&alvo!=='chudan')parts.push(L(alvo));
    if(dir)parts.push(L(dir));
    if(bukipe&&['hiza','kansetsu'].includes(bukipe))parts.push(L(bukipe));
    parts.push(L(acao));
  } else if(acao==='uke'){
    if(bukim&&['shuto','koken'].includes(bukim))parts.push(L(bukim));
    if(dir&&dir!=='mae')parts.push(L(dir));
    if(alvo)parts.push(L(alvo));
    parts.push(L(acao));
  } else if(acao==='barai'){
    if(bukim&&['shuto'].includes(bukim))parts.push(L(bukim));
    if(alvo)parts.push(L(alvo));
    if(dir&&dir!=='mae')parts.push(L(dir));
    parts.push(L(acao));
  } else {
    [bukim,bukipe,dir,alvo,acao].filter(Boolean).forEach(id=>parts.push(L(id)));
  }
  return parts.filter(Boolean).join(' ');
}

function buildPtName(acao,bukim,bukipe,dir,alvo){
  const P=id=>id&&NMAP[id]?NMAP[id].pt:null;
  return [P(bukim)||P(bukipe),P(dir),P(alvo),P(acao)].filter(Boolean).join(' + ');
}

function findCorpusMatch(acao,bukim,bukipe,dir,alvo){
  const selected=[acao,bukim,bukipe,dir,alvo].filter(Boolean);
  if(!selected.length)return[];
  return TECHS.map(t=>{
    const tn=t.nodes.filter(Boolean);
    const hits=selected.filter(n=>tn.includes(n)).length;
    const exact=hits===selected.length&&selected.length===tn.length;
    return{t,hits,exact};
  }).filter(x=>x.hits>0).sort((a,b)=>b.hits-a.hits||(b.exact?1:-1)-(a.exact?1:-1)).slice(0,4);
}

function _axisLabel(id,type,presentInName,rule){
  if(!id)return null;
  const n=NMAP[id];if(!n)return null;
  // Determine if this axis is in the name, implied, or absent
  let state='absent';
  if(presentInName)state='present';
  else if(rule){
    if(rule.keep&&rule.keep.includes(type))state='implied';
  }
  return{id,label:n.label,pt:n.pt,type,state};
}

function updateConstrutor(){
  const acao=document.getElementById('cs-acao').value||null;
  const bukim=document.getElementById('cs-bukim').value||null;
  const bukipe=document.getElementById('cs-bukipe').value||null;
  const dir=document.getElementById('cs-dir').value||null;
  const alvo=document.getElementById('cs-alvo').value||null;

  // Mutual exclusion
  const bmSel=document.getElementById('cs-bukim');
  const bpSel=document.getElementById('cs-bukipe');
  if(bukim){bpSel.value='';bpSel.disabled=true;}else bpSel.disabled=false;
  if(bukipe){bmSel.value='';bmSel.disabled=true;}else bmSel.disabled=false;

  const result=document.getElementById('const-result');
  const matches=document.getElementById('const-matches');

  if(!acao){
    result.innerHTML='<span class="const-empty">Selecione uma ação para começar</span>';
    matches.innerHTML='';return;
  }

  const jpName=buildCanonicalName(acao,bukim,bukipe,dir,alvo);
  const ptName=buildPtName(acao,bukim,bukipe,dir,alvo);

  // Build axes display: which are present/implied/absent
  const r=ELISION_RULES[acao]||{};
  // Determine what's in the name
  const inName=[];
  if(acao==='tsuki'){if(bukim)inName.push(bukim);if(alvo)inName.push(alvo);if(dir&&dir!=='mae')inName.push(dir);}
  else if(acao==='uchi'){if(bukim)inName.push(bukim);if(alvo)inName.push(alvo);else if(dir)inName.push(dir);}
  else if(acao==='geri'||acao==='keage'){if(alvo&&alvo!=='chudan')inName.push(alvo);if(dir)inName.push(dir);if(bukipe&&['hiza','kansetsu'].includes(bukipe))inName.push(bukipe);}
  else if(acao==='uke'){if(bukim&&['shuto','koken'].includes(bukim))inName.push(bukim);if(dir&&dir!=='mae')inName.push(dir);if(alvo)inName.push(alvo);}
  else if(acao==='barai'){if(alvo)inName.push(alvo);if(dir&&dir!=='mae')inName.push(dir);}
  inName.push(acao);

  const axes=[];
  const addAxis=(id,type)=>{
    if(!id)return;
    const n=NMAP[id];if(!n)return;
    const inN=inName.includes(id);
    const implied=!inN&&(id===acao||(type==='buki_pe'&&(acao==='geri'||acao==='keage')&&!['hiza','kansetsu'].includes(id))||(type==='buki_mao'&&(acao==='uke'||acao==='barai')&&!['shuto','koken'].includes(id))||(id==='mae'&&acao==='tsuki'));
    axes.push({id,label:n.label,pt:n.pt,type,state:inN?'present':implied?'implied':'absent'});
  };
  addAxis(bukim,'buki_mao');addAxis(bukipe,'buki_pe');
  addAxis(dir,'direcao');addAxis(alvo,'alvo');addAxis(acao,'acao');

  const axHtml=axes.map(a=>`<span class="const-axis ${a.state}" title="${a.pt} · ${a.state==='present'?'no nome':a.state==='implied'?'implícito':'ausente/padrão'}">${a.label}</span>`).join('');

  const elisionMsg={
    tsuki:'<strong>Tsuki:</strong> weapon + target + action. Direção <em>mae</em> é elidida (padrão para socos lineares).',
    uchi:'<strong>Uchi:</strong> weapon + target/direction + action.',
    geri:'<strong>Geri:</strong> direction + action. Arma de pé (chusoku/sokuto/kakato) é elidida — padrão implícito pelo tipo.',
    keage:'<strong>Keage:</strong> direction + action. Mesmo princípio do geri.',
    uke:'<strong>Uke:</strong> direction + target + action. Arma de mão elidida — o antebraço é a arma por convenção defensiva.',
    barai:'<strong>Barai:</strong> target + action. Direção <em>mae</em> elidida se frontal.',
  }[acao]||'';

  result.innerHTML=`
    <div class="const-name-jp">${jpName}</div>
    <div class="const-name-pt">${ptName}</div>
    <div class="const-axes">${axHtml}</div>
    ${elisionMsg?'<div class="const-elision">'+elisionMsg+'</div>':''}`;

  // Corpus matches
  const found=findCorpusMatch(acao,bukim,bukipe,dir,alvo);
  if(!found.length){matches.innerHTML='<div style="font-size:12px;color:var(--text2);opacity:.6">Nenhuma técnica no corpus com estes componentes.</div>';return;}
  matches.innerHTML='<div class="const-matches-title">No corpus</div>';
  found.forEach(({t,hits,exact})=>{
    const scoreLabel=exact?'✓ exato':`${hits}/${[acao,bukim,bukipe,dir,alvo].filter(Boolean).length} eixos`;
    const d=document.createElement('div');d.className='const-match';
    d.innerHTML=`<span class="const-match-score${exact?' const-match-exact':''}">${scoreLabel}</span>`+
      `<div><div style="font-size:13px;font-weight:600">${t.name}</div>`+
      `<div style="font-size:11px;color:var(--text2)">${t.pt} · <span style="color:${BS[t.belt]}">${t.belt}</span></div></div>`;
    d.onclick=()=>{switchTab('constelacao');requestAnimationFrame(()=>showTechDetail(t));};
    document.getElementById('const-matches').appendChild(d);
  });
}

function initConstrutor(){
  const form=document.getElementById('const-form');
  if(!form||form.dataset.init)return;
  form.dataset.init='1';

  const acaoNodes=NODES.filter(n=>n.type==='acao');
  const bukimNodes=NODES.filter(n=>n.type==='buki_mao');
  const bukipeNodes=NODES.filter(n=>n.type==='buki_pe');
  const dirNodes=NODES.filter(n=>n.type==='direcao');
  const alvoNodes=NODES.filter(n=>n.type==='alvo');

  function mkSel(id,nodes,placeholder,col){
    const label=document.createElement('label');label.textContent=placeholder;
    const sel=document.createElement('select');sel.id=id;
    const opt0=document.createElement('option');opt0.value='';opt0.textContent='— '+placeholder;
    sel.appendChild(opt0);
    nodes.forEach(n=>{
      const o=document.createElement('option');o.value=n.id;
      o.textContent=n.label+' ('+n.pt+')';sel.appendChild(o);
    });
    sel.style.borderColor=col+'44';
    sel.addEventListener('change',updateConstrutor);
    const wrap=document.createElement('div');wrap.className='const-field';
    wrap.appendChild(label);wrap.appendChild(sel);return wrap;
  }

  const grid=document.createElement('div');grid.className='const-grid';
  grid.appendChild(mkSel('cs-acao',acaoNodes,'Ação *',NT.acao));
  grid.appendChild(mkSel('cs-bukim',bukimNodes,'Arma de Mão',NT.buki_mao));
  grid.appendChild(mkSel('cs-bukipe',bukipeNodes,'Arma de Pé',NT.buki_pe));
  grid.appendChild(mkSel('cs-dir',dirNodes,'Direção',NT.direcao));
  grid.appendChild(mkSel('cs-alvo',alvoNodes,'Alvo',NT.alvo));

  const hint=document.createElement('p');
  hint.style.cssText='font-size:11px;color:var(--text2);margin:0 0 12px;line-height:1.6';
  hint.innerHTML='Selecione os componentes. O construtor aplica as <strong style="color:var(--text)">regras de elisão</strong> canônicas — os eixos omitidos do nome por convenção são marcados como <em>implícitos</em>.';

  form.appendChild(hint);form.appendChild(grid);
}

