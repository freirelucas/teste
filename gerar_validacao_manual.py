#!/usr/bin/env python3
"""gerar_validacao_manual.py — 200 amostras por máximo ganho de informação.

Seleciona os 200 itens do corpus de revisão que maximizam o aprendizado do
sistema por turno de validação humana. Cada decisão humana é sinal S5→S4.

Heurística de scoring:
  freq_gain  = frase não-matched de alta frequência → 1 label aqui afeta N similares
  organ_gain = órgão abaixo da meta → descoberta vale mais
  flag_gain  = ruido/sem_servico → calibrar filtros críticos

Uso:
    python gerar_validacao_manual.py
    # → ptd_corpus/03_database/ptd_validacao_manual.html
"""
import json, csv, subprocess, re
from datetime import datetime
from pathlib import Path

DIR_DB  = Path("ptd_corpus/03_database")
DIR_DB.mkdir(parents=True, exist_ok=True)
SRC_CSV = DIR_DB / "ptd_revisao_pendente.csv"
OUT     = DIR_DB / "ptd_validacao_manual.html"
N_MAX   = 200   # amostras por turno

# ── 1. Carregar dados ─────────────────────────────────────────────────────────
rows: list[dict] = []
if SRC_CSV.exists():
    with open(SRC_CSV, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(r)

# ── 2. Carregar run_summary para contexto de scoring ─────────────────────────
def _load_summary() -> dict:
    local = DIR_DB / "ptd_run_summary.json"
    if local.exists():
        try:
            return json.loads(local.read_text(encoding="utf-8"))
        except Exception:
            pass
    try:
        r = subprocess.run(
            ["git", "show", "origin/pipeline-outputs:ptd_run_summary.json"],
            capture_output=True, text=True, timeout=15
        )
        if r.returncode == 0:
            return json.loads(r.stdout)
    except Exception:
        pass
    return {}

summary = _load_summary()
top_unmatched: list[dict] = summary.get("top_unmatched_phrases", [])
organ_pcts: dict[str, float] = {
    o["sigla"]: float(o.get("pct_ok", 100))
    for o in summary.get("por_orgao", [])
    if "sigla" in o
}

# ── 3. Scoring por ganho de informação ───────────────────────────────────────
def _score(row: dict) -> tuple[float, str]:
    """Retorna (score, motivo) para o item."""
    texto  = (row.get("texto")   or "").lower()
    servico = (row.get("servico") or "").lower()
    sigla   = row.get("sigla", "")
    flag    = row.get("parse_flag", "")

    freq_gain  = 0.0
    motivo_freq = ""
    for p in top_unmatched:
        phrase = p["phrase"].lower()
        cnt    = int(p.get("count", 1))
        if phrase in servico or phrase in texto:
            gain = cnt * 2.0
            if gain > freq_gain:
                freq_gain   = gain
                motivo_freq = f"frase '{p['phrase']}' freq={cnt}"
            break   # só o melhor match

    pct = organ_pcts.get(sigla, 80.0)
    organ_gain = max(0.0, (50 - pct) * 3) if pct < 50 else max(0.0, (80 - pct) * 1)

    flag_gain = 40.0 if flag == "ruido" else (20.0 if flag == "sem_servico" else 0.0)

    score  = freq_gain + organ_gain + flag_gain
    motivo = motivo_freq or (f"órgão pct_ok={pct:.0f}%" if organ_gain > 0 else f"flag={flag}")
    return score, motivo

# Calcular scores
scored = [(row, *_score(row)) for row in rows]   # (row, score, motivo)

# ── 4. Selecionar 200 com deduplicação por diversidade ────────────────────────
def _select(scored: list, n: int = N_MAX) -> list[dict]:
    """Seleciona até N itens garantindo diversidade de frase e sigla."""
    sorted_items = sorted(scored, key=lambda x: x[1], reverse=True)

    phrase_count: dict[str, int] = {}
    sigla_count:  dict[str, int] = {}
    selected: list[dict] = []

    for row, score, motivo in sorted_items:
        if len(selected) >= n:
            break
        sigla  = row.get("sigla", "")
        servico = (row.get("servico") or "").lower()

        # Limite por sigla
        if sigla_count.get(sigla, 0) >= 10:
            continue

        # Limite por frase de alta frequência
        best_phrase_key = ""
        for p in top_unmatched:
            phrase = p["phrase"].lower()
            if phrase in servico or phrase in (row.get("texto") or "").lower():
                best_phrase_key = phrase
                break
        if best_phrase_key and phrase_count.get(best_phrase_key, 0) >= 3:
            continue

        row["_ig_score"]    = round(score, 1)
        row["_ig_motivo"]   = motivo
        row["_ig_rank"]     = len(selected) + 1
        row["_pct_ok_org"]  = round(organ_pcts.get(row.get("sigla",""), -1), 1)
        selected.append(row)

        sigla_count[sigla] = sigla_count.get(sigla, 0) + 1
        if best_phrase_key:
            phrase_count[best_phrase_key] = phrase_count.get(best_phrase_key, 0) + 1

    return selected

selected = _select(scored)
n_sel    = len(selected)

# ── 5. Gerar HTML ─────────────────────────────────────────────────────────────
rows_json = json.dumps(selected, ensure_ascii=False)
ts        = datetime.now().strftime("%Y-%m-%d %H:%M")
ts_export = datetime.now().strftime("%Y%m%d_%H%M")
n_total   = len(rows)

html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>PTD-BR — Validação ({ts})</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:system-ui,sans-serif;background:#f0f2f5;color:#111827;font-size:14px}}
header{{background:#111827;color:#fff;padding:14px 24px;display:flex;align-items:center;gap:12px}}
header h1{{font-size:16px;font-weight:700;letter-spacing:-.3px}}
.meta{{font-size:12px;opacity:.6;margin-left:auto}}
/* toolbar */
.toolbar{{background:#fff;border-bottom:1px solid #e5e7eb;padding:10px 20px;
  display:flex;gap:10px;flex-wrap:wrap;align-items:center;position:sticky;top:0;z-index:20;
  box-shadow:0 1px 4px rgba(0,0,0,.06)}}
.toolbar select,.toolbar input[type=text]{{
  padding:5px 9px;border:1px solid #d1d5db;border-radius:6px;font-size:13px;
  background:#fff;color:#111}}
.toolbar input[type=text]{{flex:1;min-width:160px}}
.stats{{display:flex;gap:16px;align-items:center;font-size:13px;color:#4b5563}}
.stats b{{color:#111827}}
.btn{{padding:6px 14px;border:none;border-radius:6px;font-size:13px;cursor:pointer;
  font-weight:600;transition:opacity .15s}}
.btn:hover{{opacity:.85}}
.btn-export{{background:#16a34a;color:#fff}}
.btn-skip{{background:#e5e7eb;color:#374151}}
/* cards */
.container{{max-width:900px;margin:0 auto;padding:14px 20px}}
.card{{background:#fff;border:1px solid #e5e7eb;border-radius:10px;margin-bottom:8px;
  transition:border-color .15s,box-shadow .15s}}
.card:hover{{border-color:#6366f1;box-shadow:0 2px 8px rgba(99,102,241,.08)}}
.card.correto{{border-left:4px solid #16a34a}}
.card.incorreto{{border-left:4px solid #dc2626}}
/* card header */
.ch{{padding:10px 14px;display:flex;align-items:center;gap:8px;cursor:pointer;user-select:none}}
.ch:active{{background:#f9fafb}}
.rank{{font-size:11px;color:#9ca3af;min-width:30px;font-weight:700}}
.badge{{font-size:11px;padding:2px 7px;border-radius:10px;font-weight:700;white-space:nowrap}}
.b-sem_produto{{background:#fef9c3;color:#854d0e}}
.b-sem_servico{{background:#fee2e2;color:#991b1b}}
.b-ruido{{background:#f3f4f6;color:#6b7280}}
.sigla{{font-size:11px;background:#e0e7ff;color:#3730a3;padding:2px 7px;border-radius:5px;font-weight:700}}
.ig-badge{{font-size:10px;background:#f0fdf4;color:#166534;padding:1px 6px;border-radius:8px;
  white-space:nowrap;margin-left:auto}}
.preview{{font-size:12px;color:#6b7280;overflow:hidden;text-overflow:ellipsis;
  white-space:nowrap;max-width:360px}}
.dec-badge{{font-size:12px;padding:2px 8px;border-radius:8px;font-weight:700;white-space:nowrap}}
.dec-badge.c{{background:#dcfce7;color:#15803d}}
.dec-badge.i{{background:#fee2e2;color:#b91c1c}}
/* card body */
.cb{{display:none;padding:0 14px 14px}}
.card.open .cb{{display:block}}
.texto-box{{font-size:13px;color:#374151;background:#f9fafb;padding:10px;border-radius:7px;
  white-space:pre-wrap;word-break:break-word;max-height:180px;overflow-y:auto;
  line-height:1.6;margin-bottom:10px}}
.fields{{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:6px;
  margin-bottom:12px}}
.field label{{font-size:11px;color:#9ca3af;display:block;margin-bottom:1px}}
.field span{{font-size:12px;color:#111;font-weight:600}}
.ig-info{{font-size:11px;color:#6366f1;background:#eef2ff;padding:4px 10px;border-radius:6px;
  margin-bottom:12px;display:inline-block}}
/* decision */
.dec-row{{display:flex;gap:10px;align-items:center;margin-bottom:8px}}
.toggle-btn{{padding:8px 20px;border:2px solid #e5e7eb;border-radius:24px;
  font-size:13px;font-weight:700;cursor:pointer;background:#fff;
  transition:all .15s;color:#6b7280}}
.toggle-btn.correto-btn.active{{border-color:#16a34a;background:#f0fdf4;color:#15803d}}
.toggle-btn.incorreto-btn.active{{border-color:#dc2626;background:#fef2f2;color:#b91c1c}}
.toggle-btn:hover{{border-color:#6366f1}}
textarea.fb{{width:100%;padding:7px 10px;border:1px solid #e5e7eb;border-radius:7px;
  font-size:12px;font-family:inherit;resize:vertical;min-height:56px;
  color:#374151;line-height:1.5}}
textarea.fb:focus{{outline:none;border-color:#6366f1}}
/* progress */
.prog-bar{{height:3px;background:#e5e7eb;border-radius:2px;margin-bottom:2px}}
.prog-fill{{height:100%;background:#6366f1;border-radius:2px;transition:width .3s}}
/* export panel */
#ep{{background:#f0fdf4;border:1px solid #86efac;border-radius:8px;
  padding:14px;margin-bottom:14px;display:none}}
#ep h3{{font-size:13px;font-weight:700;color:#15803d;margin-bottom:6px}}
#ep pre{{font-size:11px;background:#fff;padding:8px;border-radius:5px;
  max-height:160px;overflow:auto;border:1px solid #d1fae5}}
</style>
</head>
<body>
<header>
  <h1>PTD-BR — Validação Manual · Ganho de Informação</h1>
  <span class="meta">{ts} · {n_sel} amostras de {n_total} itens</span>
</header>

<div class="toolbar">
  <select id="fil-sigla" onchange="filter()">
    <option value="">Todas as siglas</option>
  </select>
  <select id="fil-flag" onchange="filter()">
    <option value="">Todos os flags</option>
    <option value="sem_produto">sem_produto</option>
    <option value="sem_servico">sem_servico</option>
    <option value="ruido">ruido</option>
  </select>
  <select id="fil-dec" onchange="filter()">
    <option value="">Qualquer estado</option>
    <option value="__sem__">Sem avaliação</option>
    <option value="correto">✅ Correto</option>
    <option value="incorreto">❌ Incorreto</option>
  </select>
  <input type="text" id="fil-q" placeholder="Buscar texto..." oninput="filter()">
  <div class="stats">
    <span>Aval: <b id="s-aval">0</b></span>
    <span>✅ <b id="s-ok">0</b></span>
    <span>❌ <b id="s-err">0</b></span>
  </div>
  <button class="btn btn-export" onclick="exportJson()">⬇ Exportar JSON</button>
</div>

<div class="container">
  <div class="prog-bar"><div class="prog-fill" id="prog" style="width:0%"></div></div>
  <div id="ep">
    <h3>JSON exportado — feed de volta ao sistema</h3>
    <pre id="ep-pre"></pre>
  </div>
  <div id="list"></div>
</div>

<script>
const ROWS = {rows_json};
const dec  = {{}};  // idx → 'correto'|'incorreto'|null
const fb   = {{}};  // idx → string

// populate sigla filter
(function(){{
  const s = new Set(ROWS.map(r=>r.sigla||''));
  const sel = document.getElementById('fil-sigla');
  [...s].sort().forEach(v=>{{ const o=document.createElement('option'); o.value=o.textContent=v; sel.appendChild(o); }});
}})();

function esc(s){{ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }}

function renderList(rows){{
  const list = document.getElementById('list');
  list.innerHTML='';
  rows.forEach(r=>{{
    const i   = r._ig_rank-1;
    const d   = dec[i]||'';
    const flagCls = 'b-'+(r.parse_flag||'sem_produto');
    const cardCls = d ? ' '+d : '';
    const decBadge = d==='correto'
      ? '<span class="dec-badge c">✅ correto</span>'
      : d==='incorreto' ? '<span class="dec-badge i">❌ incorreto</span>' : '';
    const div = document.createElement('div');
    div.className = 'card'+cardCls;
    div.dataset.i = i;
    div.innerHTML = `
      <div class="ch" onclick="toggle(${{i}},this)">
        <span class="rank">#${{r._ig_rank}}</span>
        <span class="sigla">${{esc(r.sigla)}}</span>
        <span class="badge ${{flagCls}}">${{esc(r.parse_flag)}}</span>
        <span class="preview">${{esc((r.texto||'').slice(0,100))}}</span>
        <span class="ig-badge">IG ${{r._ig_score}}</span>
        ${{decBadge}}
      </div>
      <div class="cb">
        <div class="texto-box">${{esc(r.texto||'')}}</div>
        <div class="fields">
          <div class="field"><label>Serviço</label><span>${{esc(r.servico||'—')}}</span></div>
          <div class="field"><label>Produto</label><span>${{esc(r.produto||'—')}}</span></div>
          <div class="field"><label>Eixo</label><span>${{esc(r.eixo_num||'—')}}</span></div>
          <div class="field"><label>Área</label><span>${{esc(r.area||'—')}}</span></div>
          <div class="field"><label>Página</label><span>${{esc(r.pagina||'—')}}</span></div>
          <div class="field"><label>Órgão pct_ok</label><span>${{esc(String(r._pct_ok_org||'?'))}}</span></div>
        </div>
        <div class="ig-info">🎯 Motivo IG: ${{esc(r._ig_motivo||'')}} · score=${{r._ig_score}}</div>
        <div class="dec-row">
          <button class="toggle-btn correto-btn ${{d==='correto'?'active':''}}"
                  onclick="setDec(${{i}},'correto',this)">✅ Correto</button>
          <button class="toggle-btn incorreto-btn ${{d==='incorreto'?'active':''}}"
                  onclick="setDec(${{i}},'incorreto',this)">❌ Incorreto</button>
        </div>
        <textarea class="fb" placeholder="Feedback (opcional): o que está errado, sugestão de correção..."
                  oninput="fb[${{i}}]=this.value">${{esc(fb[i]||'')}}</textarea>
      </div>`;
    list.appendChild(div);
  }});
}}

function toggle(i, header){{
  const card = header.parentElement;
  card.classList.toggle('open');
}}

function setDec(i, d, btn){{
  dec[i]=d;
  const card = document.querySelector(`[data-i="${{i}}"]`);
  card.className = 'card open '+d;
  card.querySelectorAll('.toggle-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  // update header badge
  let badge = card.querySelector('.dec-badge');
  if(!badge){{ badge=document.createElement('span'); card.querySelector('.ch').appendChild(badge); }}
  badge.className='dec-badge '+(d==='correto'?'c':'i');
  badge.textContent=d==='correto'?'✅ correto':'❌ incorreto';
  updateStats();
}}

let visible=[];

function filter(){{
  const sig = document.getElementById('fil-sigla').value;
  const flg = document.getElementById('fil-flag').value;
  const dfl = document.getElementById('fil-dec').value;
  const q   = document.getElementById('fil-q').value.toLowerCase();
  visible = ROWS.filter(r=>{{
    const i=r._ig_rank-1;
    if(sig && r.sigla!==sig) return false;
    if(flg && r.parse_flag!==flg) return false;
    if(dfl==='__sem__' && dec[i]) return false;
    if(dfl==='correto' && dec[i]!=='correto') return false;
    if(dfl==='incorreto' && dec[i]!=='incorreto') return false;
    if(q && !(r.texto||'').toLowerCase().includes(q) && !(r.servico||'').toLowerCase().includes(q)) return false;
    return true;
  }});
  renderList(visible);
  updateStats();
}}

function updateStats(){{
  const n_ok  = Object.values(dec).filter(v=>v==='correto').length;
  const n_err = Object.values(dec).filter(v=>v==='incorreto').length;
  document.getElementById('s-aval').textContent = n_ok+n_err;
  document.getElementById('s-ok').textContent   = n_ok;
  document.getElementById('s-err').textContent  = n_err;
  const pct = Math.round((n_ok+n_err)/{n_sel}*100);
  document.getElementById('prog').style.width = pct+'%';
}}

function exportJson(){{
  const revisoes = ROWS
    .filter((_,i)=>dec[i])
    .map((r,_)=>{{
      const i=r._ig_rank-1;
      return {{
        rank_ig:            r._ig_rank,
        ig_score:           r._ig_score,
        ig_motivo:          r._ig_motivo,
        pdf_sha256:         r.pdf_sha256,
        sigla:              r.sigla,
        parse_flag_original:r.parse_flag,
        correto:            dec[i]==='correto',
        feedback:           fb[i]||'',
        texto_inicio:       (r.texto||'').slice(0,80),
        servico:            r.servico||'',
        produto:            r.produto||'',
      }};
    }});
  const out={{
    schema_version:2,
    exportado_em:new Date().toISOString(),
    n_amostras_apresentadas:{n_sel},
    n_total_corpus:{n_total},
    n_avaliados:revisoes.length,
    n_corretos:revisoes.filter(r=>r.correto).length,
    n_incorretos:revisoes.filter(r=>!r.correto).length,
    revisoes
  }};
  const blob=new Blob([JSON.stringify(out,null,2)],{{type:'application/json'}});
  const url=URL.createObjectURL(blob);
  const a=document.createElement('a');
  a.href=url; a.download='ptd_feedback_{ts_export}.json'; a.click();
  URL.revokeObjectURL(url);
  document.getElementById('ep').style.display='block';
  document.getElementById('ep-pre').textContent=JSON.stringify(out,null,2).slice(0,600)+'\\n...';
}}

// init
ROWS.forEach((r,i)=>{{ r._ig_rank=r._ig_rank||i+1; }});
visible=ROWS.slice();
renderList(visible);
updateStats();
</script>
</body>
</html>"""

OUT.write_text(html, encoding="utf-8")
n_flags = {r.get("parse_flag","") for r in selected}
print(f"✅  {OUT}")
print(f"    {n_sel} amostras (de {n_total}) · flags: {n_flags}")
print(f"    Score máx: {selected[0]['_ig_score'] if selected else 0} — {selected[0].get('_ig_motivo','') if selected else ''}")
print(f"    Score mín: {selected[-1]['_ig_score'] if selected else 0}")
siglas_rep = sorted({r['sigla'] for r in selected})
print(f"    Siglas ({len(siglas_rep)}): {', '.join(siglas_rep[:15])}{'…' if len(siglas_rep)>15 else ''}")
