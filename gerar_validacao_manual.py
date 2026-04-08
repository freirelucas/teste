#!/usr/bin/env python3
"""gerar_validacao_manual.py — Interface HTML para revisão manual do corpus PTD-BR.

Lê ptd_revisao_pendente.csv e gera uma página interativa onde o revisor pode:
  - Classificar cada item (ok | ruido | vocab_add | col_keys | skip)
  - Filtrar por sigla, parse_flag ou busca livre
  - Exportar as decisões como JSON (para alimentar config/revisoes_manuais.json)

Uso:
    python gerar_validacao_manual.py
    # Abre ptd_corpus/03_database/ptd_validacao_manual.html no browser
"""
import json, csv, html as html_mod
from datetime import datetime
from pathlib import Path

DIR_DB  = Path("ptd_corpus/03_database")
DIR_DB.mkdir(parents=True, exist_ok=True)
SRC_CSV = DIR_DB / "ptd_revisao_pendente.csv"
OUT     = DIR_DB / "ptd_validacao_manual.html"

# ── Carregar dados ────────────────────────────────────────────────────────────
rows = []
if SRC_CSV.exists():
    with open(SRC_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

siglas = sorted({r.get("sigla", "") for r in rows if r.get("sigla", "")})
flags  = sorted({r.get("parse_flag", "") for r in rows if r.get("parse_flag", "")})
n_rows = len(rows)

# ── Serializar linhas como JSON para embed no HTML ───────────────────────────
rows_json = json.dumps(rows, ensure_ascii=False)
ts = datetime.now().strftime("%Y-%m-%d %H:%M")

html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PTD-BR — Validação Manual ({ts})</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:system-ui,sans-serif;background:#f4f5f7;color:#1a1a2e}}
header{{background:#1a1a2e;color:#fff;padding:16px 24px;display:flex;align-items:center;gap:16px}}
header h1{{font-size:18px;font-weight:600}}
header .meta{{font-size:13px;opacity:.7;margin-left:auto}}
.toolbar{{background:#fff;border-bottom:1px solid #e0e0e0;padding:12px 24px;display:flex;gap:12px;flex-wrap:wrap;align-items:center;position:sticky;top:0;z-index:10}}
.toolbar select,.toolbar input{{padding:6px 10px;border:1px solid #ccc;border-radius:6px;font-size:13px}}
.toolbar input{{flex:1;min-width:180px}}
.btn{{padding:7px 14px;border:none;border-radius:6px;font-size:13px;cursor:pointer;font-weight:500}}
.btn-primary{{background:#2563eb;color:#fff}}.btn-primary:hover{{background:#1d4ed8}}
.btn-success{{background:#16a34a;color:#fff}}.btn-success:hover{{background:#15803d}}
.btn-danger{{background:#dc2626;color:#fff}}.btn-danger:hover{{background:#b91c1c}}
.counter{{font-size:13px;color:#555;margin-left:auto;white-space:nowrap}}
.container{{max-width:1400px;margin:0 auto;padding:16px 24px}}
.card{{background:#fff;border:1px solid #e0e0e0;border-radius:8px;margin-bottom:10px;transition:border-color .15s}}
.card:hover{{border-color:#2563eb}}
.card-header{{padding:10px 16px;display:flex;align-items:center;gap:10px;cursor:pointer;user-select:none}}
.card-body{{padding:0 16px 14px;display:none}}
.card.expanded .card-body{{display:block}}
.badge{{font-size:11px;padding:2px 8px;border-radius:12px;font-weight:600}}
.badge-sem_produto{{background:#fef3c7;color:#92400e}}
.badge-sem_servico{{background:#fee2e2;color:#991b1b}}
.badge-ruido{{background:#f3f4f6;color:#6b7280}}
.badge-ok{{background:#d1fae5;color:#065f46}}
.sigla-tag{{font-size:12px;background:#e0e7ff;color:#3730a3;padding:2px 8px;border-radius:4px;font-weight:600}}
.texto-preview{{font-size:12px;color:#374151;max-width:600px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.texto-full{{font-size:13px;color:#374151;line-height:1.6;background:#f9fafb;padding:10px;border-radius:6px;margin-bottom:10px;white-space:pre-wrap;word-break:break-word;max-height:200px;overflow-y:auto}}
.field-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:8px;margin-bottom:10px}}
.field{{font-size:12px}}.field label{{color:#6b7280;display:block;margin-bottom:2px}}
.field span{{color:#111;font-weight:500}}
.decision-bar{{display:flex;gap:8px;flex-wrap:wrap}}
.dec-btn{{padding:5px 14px;border:2px solid transparent;border-radius:20px;font-size:12px;cursor:pointer;font-weight:600;transition:all .15s;background:#f3f4f6;color:#374151}}
.dec-btn:hover,.dec-btn.active{{border-color:currentColor}}
.dec-btn.vocab_add{{color:#2563eb}}.dec-btn.vocab_add.active{{background:#eff6ff}}
.dec-btn.ruido_confirm{{color:#dc2626}}.dec-btn.ruido_confirm.active{{background:#fef2f2}}
.dec-btn.col_keys{{color:#d97706}}.dec-btn.col_keys.active{{background:#fffbeb}}
.dec-btn.ok_confirm{{color:#16a34a}}.dec-btn.ok_confirm.active{{background:#f0fdf4}}
.dec-btn.skip{{color:#6b7280}}.dec-btn.skip.active{{background:#f9fafb}}
.note-input{{margin-top:8px;width:100%;padding:5px 8px;border:1px solid #e0e0e0;border-radius:6px;font-size:12px;font-family:inherit}}
.progress-bar{{height:4px;background:#e0e0e0;border-radius:2px;margin-bottom:4px}}
.progress-fill{{height:100%;background:#2563eb;border-radius:2px;transition:width .3s}}
.stats-row{{display:flex;gap:16px;margin-bottom:12px;flex-wrap:wrap}}
.stat-box{{background:#fff;border:1px solid #e0e0e0;border-radius:8px;padding:12px 16px;min-width:130px;text-align:center}}
.stat-box .val{{font-size:24px;font-weight:700;color:#1a1a2e}}
.stat-box .lbl{{font-size:11px;color:#6b7280;margin-top:2px}}
.hidden{{display:none !important}}
#export-panel{{background:#fff;border:1px solid #22c55e;border-radius:8px;padding:16px;margin-bottom:16px;display:none}}
#export-panel h3{{font-size:14px;font-weight:600;margin-bottom:8px;color:#15803d}}
#export-panel pre{{font-size:11px;background:#f9fafb;padding:8px;border-radius:4px;max-height:180px;overflow:auto}}
</style>
</head>
<body>
<header>
  <h1>PTD-BR — Validação Manual</h1>
  <span class="meta">Gerado em {ts} · {n_rows} itens em revisão</span>
</header>

<div class="toolbar">
  <select id="fil-sigla" onchange="applyFilters()">
    <option value="">Todas as siglas</option>
    {''.join(f'<option value="{s}">{s}</option>' for s in siglas)}
  </select>
  <select id="fil-flag" onchange="applyFilters()">
    <option value="">Todos os flags</option>
    {''.join(f'<option value="{f}">{f}</option>' for f in flags)}
  </select>
  <select id="fil-decision" onchange="applyFilters()">
    <option value="">Qualquer decisão</option>
    <option value="__sem_decisao__">Sem decisão</option>
    <option value="vocab_add">vocab_add</option>
    <option value="ruido_confirm">ruido_confirm</option>
    <option value="col_keys">col_keys</option>
    <option value="ok_confirm">ok_confirm</option>
    <option value="skip">skip</option>
  </select>
  <input type="text" id="fil-texto" placeholder="Buscar no texto..." oninput="applyFilters()">
  <span class="counter" id="counter">-- de {n_rows}</span>
  <button class="btn btn-success" onclick="exportJson()">⬇ Exportar JSON</button>
  <button class="btn btn-primary" onclick="marcarTodosSkip()">Skip todos visíveis</button>
</div>

<div class="container">
  <div class="stats-row" id="stats-row">
    <div class="stat-box"><div class="val" id="stat-total">{n_rows}</div><div class="lbl">Total</div></div>
    <div class="stat-box"><div class="val" id="stat-revisados">0</div><div class="lbl">Revisados</div></div>
    <div class="stat-box"><div class="val" id="stat-vocab">0</div><div class="lbl">vocab_add</div></div>
    <div class="stat-box"><div class="val" id="stat-ruido">0</div><div class="lbl">ruido</div></div>
    <div class="stat-box"><div class="val" id="stat-colkeys">0</div><div class="lbl">col_keys</div></div>
    <div class="stat-box"><div class="val" id="stat-ok">0</div><div class="lbl">ok_confirm</div></div>
  </div>
  <div class="progress-bar"><div class="progress-fill" id="progress" style="width:0%"></div></div>

  <div id="export-panel">
    <h3>JSON exportado — salve como config/revisoes_manuais.json</h3>
    <pre id="export-preview"></pre>
  </div>

  <div id="list"></div>
</div>

<script>
const ALL_ROWS = {rows_json};
const decisions = {{}};  // sha256+idx → decisao
const notes     = {{}};

function esc(s){{ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }}

function renderCards(rows){{
  const list = document.getElementById('list');
  list.innerHTML = '';
  rows.forEach((r, vi) => {{
    const idx = r.__idx;
    const dec = decisions[idx] || '';
    const note = notes[idx] || '';
    const flagClass = 'badge-' + (r.parse_flag || 'sem_produto');
    const card = document.createElement('div');
    card.className = 'card' + (dec ? '' : '');
    card.dataset.idx = idx;
    card.innerHTML = `
      <div class="card-header" onclick="toggleCard(this)">
        <span class="sigla-tag">${{esc(r.sigla)}}</span>
        <span class="badge ${{flagClass}}">${{esc(r.parse_flag)}}</span>
        <span class="texto-preview">${{esc((r.texto||'').slice(0,120))}}</span>
        ${{dec ? `<span class="badge badge-ok" style="margin-left:auto">${{dec}}</span>` : ''}}
      </div>
      <div class="card-body">
        <div class="texto-full">${{esc(r.texto||'')}}</div>
        <div class="field-grid">
          <div class="field"><label>Serviço</label><span>${{esc(r.servico||'—')}}</span></div>
          <div class="field"><label>Produto</label><span>${{esc(r.produto||'—')}}</span></div>
          <div class="field"><label>Eixo</label><span>${{esc(r.eixo_num||'—')}}</span></div>
          <div class="field"><label>Área</label><span>${{esc(r.area||'—')}}</span></div>
          <div class="field"><label>Página</label><span>${{esc(r.pagina||'—')}}</span></div>
          <div class="field"><label>SHA256</label><span style="font-size:10px;word-break:break-all">${{esc((r.pdf_sha256||'').slice(0,16))}}…</span></div>
        </div>
        <div class="decision-bar">
          <span style="font-size:12px;color:#6b7280;align-self:center">Decisão:</span>
          <button class="dec-btn vocab_add ${{dec==='vocab_add'?'active':''}}" onclick="setDec(${{idx}},'vocab_add',this)">➕ vocab_add</button>
          <button class="dec-btn ruido_confirm ${{dec==='ruido_confirm'?'active':''}}" onclick="setDec(${{idx}},'ruido_confirm',this)">🗑 ruido</button>
          <button class="dec-btn col_keys ${{dec==='col_keys'?'active':''}}" onclick="setDec(${{idx}},'col_keys',this)">🔧 col_keys</button>
          <button class="dec-btn ok_confirm ${{dec==='ok_confirm'?'active':''}}" onclick="setDec(${{idx}},'ok_confirm',this)">✅ ok</button>
          <button class="dec-btn skip ${{dec==='skip'?'active':''}}" onclick="setDec(${{idx}},'skip',this)">⏭ skip</button>
        </div>
        <input type="text" class="note-input" placeholder="Nota (opcional)..." value="${{esc(note)}}"
               oninput="notes[${{idx}}]=this.value" />
      </div>
    `;
    list.appendChild(card);
  }});
}}

function toggleCard(header){{
  const card = header.parentElement;
  card.classList.toggle('expanded');
}}

function setDec(idx, dec, btn){{
  decisions[idx] = dec;
  const card = document.querySelector(`[data-idx="${{idx}}"]`);
  card.querySelectorAll('.dec-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  // atualizar badge no header
  const badgeEl = card.querySelector('.card-header .badge-ok');
  if(badgeEl) {{ badgeEl.textContent = dec; }}
  else {{
    const span = document.createElement('span');
    span.className = 'badge badge-ok';
    span.style.marginLeft = 'auto';
    span.textContent = dec;
    card.querySelector('.card-header').appendChild(span);
  }}
  updateStats();
}}

let visibleRows = [];

function applyFilters(){{
  const sigla = document.getElementById('fil-sigla').value;
  const flag  = document.getElementById('fil-flag').value;
  const texto = document.getElementById('fil-texto').value.toLowerCase();
  const dec   = document.getElementById('fil-decision').value;

  visibleRows = ALL_ROWS.filter(r => {{
    if(sigla && r.sigla !== sigla) return false;
    if(flag  && r.parse_flag !== flag) return false;
    if(texto && !(r.texto||'').toLowerCase().includes(texto) &&
               !(r.servico||'').toLowerCase().includes(texto)) return false;
    if(dec === '__sem_decisao__' && decisions[r.__idx]) return false;
    if(dec && dec !== '__sem_decisao__' && decisions[r.__idx] !== dec) return false;
    return true;
  }});
  document.getElementById('counter').textContent = visibleRows.length + ' de {n_rows}';
  renderCards(visibleRows);
  updateStats();
}}

function updateStats(){{
  const vals = Object.values(decisions);
  document.getElementById('stat-revisados').textContent = vals.filter(v=>v&&v!=='skip').length;
  document.getElementById('stat-vocab').textContent = vals.filter(v=>v==='vocab_add').length;
  document.getElementById('stat-ruido').textContent = vals.filter(v=>v==='ruido_confirm').length;
  document.getElementById('stat-colkeys').textContent = vals.filter(v=>v==='col_keys').length;
  document.getElementById('stat-ok').textContent = vals.filter(v=>v==='ok_confirm').length;
  const pct = Math.round(vals.filter(v=>v).length / {n_rows} * 100);
  document.getElementById('progress').style.width = pct + '%';
}}

function marcarTodosSkip(){{
  visibleRows.forEach(r => {{ if(!decisions[r.__idx]) decisions[r.__idx] = 'skip'; }});
  applyFilters();
}}

function exportJson(){{
  const out = {{
    schema_version: 1,
    exportado_em: new Date().toISOString(),
    n_itens: {n_rows},
    n_revisados: Object.values(decisions).filter(v=>v&&v!=='skip').length,
    revisoes: ALL_ROWS
      .filter(r => decisions[r.__idx] && decisions[r.__idx] !== 'skip')
      .map(r => ({{
        pdf_sha256: r.pdf_sha256,
        sigla: r.sigla,
        texto_inicio: (r.texto||'').slice(0,60),
        parse_flag_original: r.parse_flag,
        decisao: decisions[r.__idx],
        nota: notes[r.__idx] || '',
        servico_sugerido: r.servico || '',
        produto_sugerido: r.produto || '',
      }}))
  }};
  const blob = new Blob([JSON.stringify(out, null, 2)], {{type:'application/json'}});
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href = url; a.download = 'revisoes_manuais_{datetime.now().strftime("%Y%m%d_%H%M")}.json';
  a.click(); URL.revokeObjectURL(url);

  // preview
  const panel = document.getElementById('export-panel');
  panel.style.display = 'block';
  document.getElementById('export-preview').textContent =
    JSON.stringify(out, null, 2).slice(0, 800) + '\\n...';
}}

// Inicializar
ALL_ROWS.forEach((r, i) => r.__idx = i);
visibleRows = ALL_ROWS.slice();
renderCards(visibleRows);
updateStats();
</script>
</body>
</html>"""

OUT.write_text(html_content, encoding="utf-8")
print(f"✅ {OUT}")
print(f"   {n_rows} itens · {len(siglas)} siglas · {len(flags)} tipos de flag")
print(f"   Abrir: python -m http.server 8080 e acessar http://localhost:8080/{OUT}")
