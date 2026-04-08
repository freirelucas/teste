#!/usr/bin/env python3
"""
PTD-BR — Relatório HTML Autocontido v3.0
IPEA / COGIT / DIEST

Gera um único arquivo HTML sem dependências externas:
- Dashboard de cobertura e qualidade
- Distribuição por eixo EFGD
- Amostra auditável (texto original ↔ campos extraídos)
- Alertas de qualidade
- Proveniência completa

Uso:
    python gerar_relatorio.py
    python gerar_relatorio.py --sample 100   # tamanho da amostra (padrão: 50)
    python gerar_relatorio.py --output relatorio.html

Input:  ptd_corpus/03_database/ptd_corpus_v21.csv   (preferencial)
        ptd_corpus/03_database/ptd_corpus_raw.csv    (fallback)
        ptd_corpus/03_database/pipeline_manifest.json
        ptd_corpus/03_database/proveniencia.json
"""
import sys, json, hashlib, re, os
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np

# Chart.js CDN (fallback gracioso se offline)
CHARTJS_CDN = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js'

# ── Args ──────────────────────────────────────────────────────────────
SAMPLE_N = 50
OUT_FILE = Path('ptd_relatorio_v30.html')
for i, arg in enumerate(sys.argv[1:], 1):
    if arg == '--sample' and i < len(sys.argv) - 1:
        SAMPLE_N = int(sys.argv[i + 1])
    if arg == '--output' and i < len(sys.argv) - 1:
        OUT_FILE = Path(sys.argv[i + 1])

DIR_DB = Path('ptd_corpus/03_database')

# ── Carregar dados ────────────────────────────────────────────────────
corpus_path = DIR_DB / 'ptd_corpus_v21.csv'
if not corpus_path.exists():
    corpus_path = DIR_DB / 'ptd_corpus_raw.csv'
if not corpus_path.exists():
    # Gerar summary mínimo mesmo sem corpus (permite diagnóstico de falha L1-2)
    _dir_db = Path('ptd_corpus/03_database')
    _dir_db.mkdir(parents=True, exist_ok=True)
    _minimal = {
        'ts': _dt.datetime.now().isoformat(timespec='seconds'),
        'stage': 0,
        'stage_label': 'cobertura',
        'n_entregas': 0,
        'n_orgaos': 0,
        'pct_ok': 0.0,
        'orgaos_zero_entregas': [],
        'orgaos_zero_ou_noise': [],
        'top_unmatched_phrases': [],
        'orgs_below_50pct': [],
        'erro': 'corpus_nao_encontrado — Layer 1-2 ou Layer 3 falhou',
    }
    (_dir_db / 'ptd_run_summary.json').write_text(
        json.dumps(_minimal, ensure_ascii=False, indent=2), encoding='utf-8')
    print('WARN: corpus não encontrado — ptd_run_summary.json mínimo gerado para diagnóstico.')
    sys.exit(0)   # não falhar — deixar commit-diagnóstico commitar o summary

corpus = pd.read_csv(corpus_path)
print(f'Corpus: {len(corpus):,} linhas × {len(corpus.columns)} colunas')

prov = {}
prov_path = DIR_DB / 'proveniencia.json'
if prov_path.exists():
    prov = json.loads(prov_path.read_text(encoding='utf-8'))

manifest = {}
mfst_path = DIR_DB / 'pipeline_manifest.json'
if mfst_path.exists():
    manifest = json.loads(mfst_path.read_text(encoding='utf-8'))

meta_path = DIR_DB / 'ptd_corpus_v21_metadados.json'
meta = {}
if meta_path.exists():
    meta = json.loads(meta_path.read_text(encoding='utf-8'))

# ── Métricas ──────────────────────────────────────────────────────────
EIXOS = {1:'Centrado no Cidadão e Inclusivo', 2:'Integrado e Colaborativo',
         3:'Inteligente e Inovador',           4:'Confiável e Seguro',
         5:'Transparente, Aberto e Participativo', 6:'Eficiente e Sustentável'}
CORES = {1:'#1A7F7A', 2:'#0D2B4E', 3:'#D97706',
         4:'#E63946', 5:'#457B9D', 6:'#6A4C93'}

eixo_col = 'eixo_num_corrigido' if 'eixo_num_corrigido' in corpus.columns else 'eixo_num'
eixo_dist = corpus[eixo_col].value_counts().sort_index().to_dict() if eixo_col in corpus.columns else {}
n_orgaos  = corpus['sigla'].nunique() if 'sigla' in corpus.columns else 0
flag_dist = corpus['parse_flag'].value_counts().to_dict() if 'parse_flag' in corpus.columns else {}
n_ok      = flag_dist.get('ok', 0)
pct_ok    = round(n_ok / len(corpus) * 100, 1) if corpus is not None and len(corpus) else 0

# pct_ok_entregas: métrica limpa — apenas linhas de anexo_entregas (exclui diretivo, riscos)
# FIX 2026-04-07: tipo_doc separa o conteúdo real de entregas do restante do PDF
if 'tipo_doc' in corpus.columns:
    _corpus_entregas = corpus[corpus['tipo_doc'] == 'anexo_entregas']
    _n_ok_e = (_corpus_entregas['parse_flag'] == 'ok').sum() if len(_corpus_entregas) else 0
    pct_ok_entregas = round(_n_ok_e / len(_corpus_entregas) * 100, 1) if len(_corpus_entregas) else pct_ok
else:
    pct_ok_entregas = pct_ok  # fallback: corpus sem tipo_doc (run antigo)

# ── Organ groups: expande lead siglas para contar sub-órgãos ─────────
def _load_organ_groups() -> dict:
    p = Path('config/organ_groups.json')
    if p.exists():
        try:
            return json.loads(p.read_text(encoding='utf-8'))
        except Exception:
            pass
    return {}

def _expand_siglas(siglas_corpus: 'set', organ_groups: dict) -> set:
    """Dado o conjunto de siglas do corpus, expande para incluir todos os
    membros de cada grupo. Ex: {'MEC'} → {'MEC','CAPES','EBSERH',...}"""
    lead_to_members = {
        g: set(d['membros'].keys())
        for g, d in organ_groups.get('grupos', {}).items()
    }
    expanded = set(siglas_corpus)
    for sigla in list(siglas_corpus):
        if str(sigla).upper() in lead_to_members:
            expanded |= lead_to_members[str(sigla).upper()]
    return expanded

_organ_groups_cfg  = _load_organ_groups()
_n_orgaos_meta     = _organ_groups_cfg.get('_meta', {}).get('total_orgaos', 91)
_siglas_corpus_set = set(corpus['sigla'].dropna().unique()) if 'sigla' in corpus.columns else set()
_siglas_expandidas = _expand_siglas(_siglas_corpus_set, _organ_groups_cfg)
n_orgaos_expandido = len(_siglas_expandidas)  # conta sub-órgãos de grupos

# Alertas
alertas = []
if pct_ok < 50:
    alertas.append(('WARN', f'Cobertura parse OK baixa: {pct_ok}% — revisar parser ou PRODUTOS'))
if n_orgaos < 80:
    alertas.append(('WARN', f'Apenas {n_orgaos_expandido}/{_n_orgaos_meta} órgãos com dados — verificar scraping e downloads'))
sem_prod = flag_dist.get('sem_produto', 0)
if sem_prod / len(corpus) > 0.3 if len(corpus) else False:
    alertas.append(('WARN', f'{sem_prod} linhas sem produto identificado ({sem_prod/len(corpus)*100:.0f}%) — considerar fuzzy match'))
e3_raw  = corpus['eixo_num'].value_counts().get(3, 0) if 'eixo_num' in corpus.columns else 0
e3_corr = eixo_dist.get(3, 0)
if e3_raw - e3_corr > 10:
    alertas.append(('INFO', f'E3 corrigido: {e3_raw}→{e3_corr} ({e3_raw-e3_corr} registros reclassificados)'))
n_pendente = int((corpus['revisao_status'] == 'pendente').sum()) \
    if 'revisao_status' in corpus.columns else None
n_manual   = int((corpus['revisao_status'] == 'manual').sum()) \
    if 'revisao_status' in corpus.columns else 0
if n_pendente is not None and n_pendente > 0:
    alertas.append(('WARN', f'{n_pendente} registros na fila de revisão humana '
                             f'(ptd_revisao_pendente.csv) | {n_manual} já revisados manualmente'))
if not alertas:
    alertas.append(('OK', 'Nenhum alerta crítico — corpus dentro dos parâmetros esperados'))

# Amostra auditável
sample_flags = ['ok', 'sem_produto', 'ruido']
frames = []
for flag in sample_flags:
    sub = corpus[corpus['parse_flag'] == flag] if 'parse_flag' in corpus.columns else corpus
    n   = max(1, SAMPLE_N // len(sample_flags))
    if len(sub):
        frames.append(sub.sample(min(n, len(sub)), random_state=42))
df_sample = pd.concat(frames).sample(frac=1, random_state=42) if frames else corpus.head(SAMPLE_N)

# ── HTML ──────────────────────────────────────────────────────────────
def esc(s):
    return str(s).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

def badge(txt, cor):
    return f'<span style="background:{cor};color:#fff;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:bold">{esc(txt)}</span>'

def barra(val, total, cor='#1A7F7A'):
    pct = val / total * 100 if total else 0
    return (f'<div style="background:#eee;border-radius:4px;height:14px;margin:2px 0">'
            f'<div style="width:{min(pct,100):.1f}%;background:{cor};height:14px;border-radius:4px"></div>'
            f'</div><small>{val:,} ({pct:.1f}%)</small>')

flag_cores = {'ok':'#1A7F7A','sem_produto':'#D97706','sem_servico':'#E63946',
              'ruido':'#999','vazio':'#ccc'}

# ── Riscos (opcional) ─────────────────────────────────────────────────
riscos_path = DIR_DB / 'ptd_riscos.csv'
df_riscos = pd.read_csv(riscos_path) if riscos_path.exists() else None

def _riscos_section(df_r) -> str:
    """Gera seção HTML de riscos com gráfico Chart.js (probabilidade × impacto)."""
    if df_r is None or df_r.empty:
        return ''
    n_riscos   = len(df_r)
    n_orgaos_r = df_r['sigla'].nunique() if 'sigla' in df_r.columns else '—'
    prob_dist  = df_r['probabilidade'].value_counts().to_dict() if 'probabilidade' in df_r.columns else {}
    imp_dist   = df_r['impacto'].value_counts().to_dict() if 'impacto' in df_r.columns else {}
    trat_dist  = df_r['opcao_tratamento'].value_counts().to_dict() if 'opcao_tratamento' in df_r.columns else {}

    prob_labels = json.dumps(list(prob_dist.keys()))
    prob_vals   = json.dumps(list(prob_dist.values()))
    imp_labels  = json.dumps(list(imp_dist.keys()))
    imp_vals    = json.dumps(list(imp_dist.values()))
    trat_labels = json.dumps(list(trat_dist.keys()))
    trat_vals   = json.dumps(list(trat_dist.values()))
    pal = ['#0D2B4E','#1A7F7A','#D97706','#E63946','#457B9D','#6A4C93']
    cores_r = json.dumps((pal * 10)[:max(len(prob_dist), len(imp_dist), len(trat_dist), 1)])

    return f"""
<div class="card">
  <h2>Análise de Riscos ({n_riscos:,} registros · {n_orgaos_r} órgãos)</h2>
  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px;margin-top:8px">
    <div>
      <h3 style="font-size:13px;color:#0D2B4E;margin-bottom:6px">Probabilidade</h3>
      <div class="chart-wrap" style="height:200px"><canvas id="chartProb"></canvas></div>
    </div>
    <div>
      <h3 style="font-size:13px;color:#0D2B4E;margin-bottom:6px">Impacto</h3>
      <div class="chart-wrap" style="height:200px"><canvas id="chartImp"></canvas></div>
    </div>
    <div>
      <h3 style="font-size:13px;color:#0D2B4E;margin-bottom:6px">Opção de Tratamento</h3>
      <div class="chart-wrap" style="height:200px"><canvas id="chartTrat"></canvas></div>
    </div>
  </div>
  <script>
  (function(){{
    function barH(id, labels, data, bkgs) {{
      new Chart(document.getElementById(id), {{
        type: 'bar',
        data: {{ labels: labels, datasets: [{{ data: data,
          backgroundColor: bkgs, borderWidth: 0, borderRadius: 3 }}] }},
        options: {{ indexAxis: 'y', responsive: true, maintainAspectRatio: false,
          plugins: {{ legend: {{ display: false }} }},
          scales: {{ x: {{ beginAtZero: true, grid: {{ color: '#f0f0f0' }} }},
                    y: {{ grid: {{ display: false }} }} }} }}
      }});
    }}
    var cores = {cores_r};
    barH('chartProb',  {prob_labels},  {prob_vals},  cores);
    barH('chartImp',   {imp_labels},   {imp_vals},   cores);
    barH('chartTrat',  {trat_labels},  {trat_vals},  cores);
  }})();
  </script>
</div>"""

# ── Construir HTML ─────────────────────────────────────────────────────
ts = datetime.now().strftime('%d/%m/%Y %H:%M')
versao_pipeline = manifest.get('versao_pipeline', prov.get('versao', '3.0'))

html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>PTD-BR Corpus — Relatório de Qualidade</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'Segoe UI',Arial,sans-serif;background:#f4f4f4;color:#333;font-size:14px}}
  .header{{background:#0D2B4E;color:#fff;padding:24px 32px}}
  .header h1{{font-size:22px;font-weight:700}}
  .header p{{font-size:13px;opacity:.8;margin-top:4px}}
  .container{{max-width:1200px;margin:24px auto;padding:0 16px}}
  .card{{background:#fff;border-radius:8px;padding:20px;margin-bottom:20px;
          box-shadow:0 1px 4px rgba(0,0,0,.08)}}
  .card h2{{font-size:16px;font-weight:700;color:#0D2B4E;margin-bottom:14px;
             border-bottom:2px solid #1A7F7A;padding-bottom:6px}}
  .kpi-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px}}
  .kpi{{background:#0D2B4E;color:#fff;border-radius:8px;padding:16px;text-align:center}}
  .kpi .val{{font-size:32px;font-weight:700;color:#1A7F7A}}
  .kpi .lbl{{font-size:11px;opacity:.75;margin-top:4px}}
  .alerta{{padding:10px 14px;border-radius:6px;margin:6px 0;font-size:13px}}
  .alerta.OK  {{background:#e8f5e9;border-left:4px solid #1A7F7A}}
  .alerta.WARN{{background:#fff8e1;border-left:4px solid #D97706}}
  .alerta.INFO{{background:#e3f2fd;border-left:4px solid #457B9D}}
  table{{width:100%;border-collapse:collapse;font-size:12px}}
  th{{background:#0D2B4E;color:#fff;padding:7px 10px;text-align:left;font-weight:600}}
  tr:nth-child(even){{background:#f9f9f9}}
  td{{padding:6px 10px;border-bottom:1px solid #eee;vertical-align:top}}
  .eixo-bar{{display:flex;align-items:center;gap:10px;margin:5px 0}}
  .eixo-bar .lbl{{width:200px;font-size:12px}}
  .eixo-bar .track{{flex:1;background:#eee;border-radius:4px;height:18px}}
  .eixo-bar .fill{{height:18px;border-radius:4px;display:flex;align-items:center;
                   padding-left:8px;color:#fff;font-size:11px;font-weight:600}}
  .prov-item{{display:flex;gap:8px;padding:4px 0;font-size:12px;border-bottom:1px solid #f0f0f0}}
  .prov-item .k{{font-weight:600;color:#0D2B4E;min-width:160px}}
  .prov-item .v{{color:#555;word-break:break-all}}
  footer{{text-align:center;padding:24px;color:#999;font-size:11px}}
  .chart-wrap{{position:relative;height:280px;margin-top:8px}}
</style>
<script src="{CHARTJS_CDN}"></script>
</head>
<body>
<div class="header">
  <h1>PTD-BR Corpus — Relatório de Qualidade</h1>
  <p>Pipeline {versao_pipeline} · Gerado em {ts} · IPEA/COGIT/DIEST</p>
</div>
<div class="container">

<!-- KPIs -->
<div class="card">
  <h2>Visão Geral</h2>
  <div class="kpi-grid">
    <div class="kpi"><div class="val">{len(corpus):,}</div><div class="lbl">Registros totais</div></div>
    <div class="kpi"><div class="val">{n_orgaos}</div><div class="lbl">Órgãos com dados</div></div>
    <div class="kpi"><div class="val">{pct_ok:.0f}%</div><div class="lbl">Parse OK</div></div>
    <div class="kpi"><div class="val">{len(eixo_dist)}</div><div class="lbl">Eixos identificados</div></div>
    <div class="kpi"><div class="val">{manifest.get("total_pdfs_baixados", "—")}</div><div class="lbl">PDFs baixados</div></div>
    <div class="kpi"><div class="val">{len(manifest.get("pdfs_sha256", {}))}</div><div class="lbl">PDFs com SHA-256</div></div>
  </div>
</div>

<!-- Alertas -->
<div class="card">
  <h2>Alertas de Qualidade</h2>
  {''.join(f'<div class="alerta {a[0]}"><strong>{a[0]}</strong> — {esc(a[1])}</div>' for a in alertas)}
</div>

<!-- Eixos — Chart.js interativo -->
<div class="card">
  <h2>Distribuição por Eixo EFGD</h2>
  <div class="chart-wrap"><canvas id="chartEixos"></canvas></div>
  <script>
  (function(){{
    var labels = {json.dumps([f'E{e}' for e in sorted(eixo_dist.keys())])};
    var counts = {json.dumps([eixo_dist[e] for e in sorted(eixo_dist.keys())])};
    var bkgs   = {json.dumps([CORES.get(e,'#999') for e in sorted(eixo_dist.keys())])};
    var names  = {json.dumps([EIXOS.get(e,'') for e in sorted(eixo_dist.keys())])};
    new Chart(document.getElementById('chartEixos'), {{
      type: 'bar',
      data: {{ labels: labels, datasets: [{{
        label: 'Registros',
        data: counts, backgroundColor: bkgs,
        borderWidth: 0, borderRadius: 4,
      }}]}},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{
          legend: {{ display: false }},
          tooltip: {{ callbacks: {{ title: function(ctx) {{
            return names[ctx[0].dataIndex];
          }}, label: function(ctx) {{
            var total = counts.reduce(function(a,b){{return a+b}},0);
            return ctx.parsed.y.toLocaleString('pt-BR') + ' (' + (ctx.parsed.y/total*100).toFixed(1) + '%)';
          }} }} }}
        }},
        scales: {{ y: {{ beginAtZero: true, grid: {{ color: '#f0f0f0' }} }},
                  x: {{ grid: {{ display: false }} }} }}
      }}
    }});
  }})();
  </script>
  <!-- Fallback para ambientes sem JS -->
  <noscript>
  {chr(10).join(
      f'<div class="eixo-bar"><div class="lbl">E{e} — {EIXOS.get(e,"")[:28]}</div>'
      f'<div class="track"><div class="fill" style="width:{min(n/len(corpus)*100,100):.1f}%;background:{CORES.get(e,"#999")}">'
      f'{n:,}</div></div><small style="min-width:80px;text-align:right">{n/len(corpus)*100:.1f}%</small></div>'
      for e, n in sorted(eixo_dist.items())
  )}
  </noscript>
</div>

<!-- Parse flags -->
<div class="card">
  <h2>Qualidade do Parser</h2>
  {''.join(
      f'<div style="margin:6px 0"><strong style="color:{flag_cores.get(f,"#333")}">{esc(f)}</strong>'
      f' — {barra(n, len(corpus), flag_cores.get(f,"#999"))}</div>'
      for f, n in sorted(flag_dist.items(), key=lambda x: -x[1])
  ) if flag_dist else '<p>parse_flag não disponível neste corpus</p>'}
</div>

<!-- Amostra auditável -->
<div class="card">
  <h2>Amostra Auditável ({len(df_sample)} registros — texto original ↔ campos extraídos)</h2>
  <div style="overflow-x:auto">
  <table>
    <tr>
      <th>Órgão</th><th>Eixo</th><th>Flag</th>
      <th>Texto original (bruto)</th>
      <th>Serviço extraído</th><th>Produto</th><th>Tipo entrega</th>
    </tr>
    {''.join(
        f'<tr>'
        f'<td><strong>{esc(r.get("sigla",""))}</strong></td>'
        f'<td>{badge("E"+str(r.get(eixo_col,"")), CORES.get(r.get(eixo_col,0),"#999"))}</td>'
        f'<td><span style="color:{flag_cores.get(r.get("parse_flag",""),"#333")}">{esc(r.get("parse_flag",""))}</span></td>'
        f'<td style="max-width:280px;word-break:break-word;font-size:11px">{esc(str(r.get("texto",""))[:180])}</td>'
        f'<td style="max-width:160px;font-size:11px">{esc(str(r.get("servico",""))[:100])}</td>'
        f'<td style="font-size:11px">{esc(str(r.get("produto",""))[:80])}</td>'
        f'<td><small>{esc(str(r.get("tipo_entrega","—")))}</small></td>'
        f'</tr>'
        for _, r in df_sample.iterrows()
    )}
  </table>
  </div>
</div>

{_riscos_section(df_riscos)}

<!-- Proveniência -->
<div class="card">
  <h2>Proveniência e Rastreabilidade</h2>
  {chr(10).join(
      f'<div class="prov-item"><div class="k">{esc(k)}</div><div class="v">{esc(str(v))}</div></div>'
      for k, v in {
          'fonte':           prov.get('fonte','Portal Gov Digital / MGI'),
          'data_coleta':     prov.get('data_coleta','—'),
          'versao_pipeline': versao_pipeline,
          'base_legal':      prov.get('base_legal','Decreto 12.198/2024'),
          'autores':         ', '.join(prov.get('autores',['Denise do Carmo Direito','Lucas Freire Silva'])),
          'unidade':         prov.get('unidade','COGIT/DIEST/IPEA'),
          'n_pdfs_sha256':   str(len(manifest.get('pdfs_sha256',{}))),
          'corpus_sha256':   hashlib.sha256(corpus_path.read_bytes()).hexdigest()[:16] + '…',
          'data_relatorio':  ts,
          'nota':            'Documento de trabalho — não citar sem autorização dos autores',
      }.items()
  )}
</div>

</div>
<footer>PTD-BR Corpus · IPEA/COGIT/DIEST · {ts} · Relatório gerado por gerar_relatorio.py</footer>
</body>
</html>"""

OUT_FILE.write_text(html, encoding='utf-8')
kb = OUT_FILE.stat().st_size // 1024
print(f'✅ Relatório salvo: {OUT_FILE}  ({kb} KB)')
print(f'   Alertas: {sum(1 for a in alertas if a[0]=="WARN")} avisos, '
      f'{sum(1 for a in alertas if a[0]=="OK")} OK')
print(f'   Abra no browser: file://{OUT_FILE.resolve()}')
if os.environ.get('GITHUB_RUN_ID') and os.environ.get('GITHUB_REPOSITORY'):
    _dl = (f"https://github.com/{os.environ['GITHUB_REPOSITORY']}"
           f"/actions/runs/{os.environ['GITHUB_RUN_ID']}")
    print(f'📦 Download: {_dl}')

# ── ptd_run_summary.json — lido pelo assistente IA via MCP após cada run ─────
try:
    _raw_path = DIR_DB / 'ptd_corpus_v21.csv'   # usar corpus classificado (v21) para métricas corretas
    if not _raw_path.exists():
        _raw_path = DIR_DB / 'ptd_corpus_raw.csv'  # fallback: raw tem parse_flag='raw' para todos
    _raw = pd.read_csv(_raw_path) if _raw_path.exists() else corpus

    # ── Carregar política S5 por órgão (Nível -1 de recursão VSM) ────────
    _org_meta_path = Path('config/org_meta.json')
    _org_meta: dict = {}
    if _org_meta_path.exists():
        try:
            _om_raw = json.loads(_org_meta_path.read_text())
            _org_meta = {k: v for k, v in _om_raw.items() if not k.startswith('_')}
        except Exception:
            pass
    _OM_DEFAULT = _org_meta.get('_default', {
        'status': 'ativo', 's5_pct_ok_meta': 80.0,
        'prioridade': 'normal', 'estrategia': 'vocabulario'
    })

    # ── Organ groups: mapa de grupos (já carregado acima como _organ_groups_cfg) ─
    # Reutiliza _organ_groups_cfg, _siglas_expandidas, _n_orgaos_meta definidos na seção de métricas

    _por_orgao = []
    for _sig, _g in _raw.groupby('sigla'):
        _ext = _g['extrator'].mode()[0] if 'extrator' in _g.columns and len(_g) else None

        # parse_flag metrics (Stage 1)
        _flags = _g['parse_flag'].value_counts().to_dict() if 'parse_flag' in _g.columns else {}
        _n = max(len(_g), 1)
        _pct_ok_org   = round(_flags.get('ok', 0) / _n * 100, 1)
        _sem_prod_n   = int(_flags.get('sem_produto', 0))
        _sem_prod_pct = round(_sem_prod_n / _n * 100, 1)

        # col_map_ok rate (Stage 2) — proporção de linhas com headers reconhecidos
        _col_ok_rate  = round(
            _g['col_map_ok'].mean() * 100, 1
        ) if 'col_map_ok' in _g.columns and len(_g) else None

        # Headers reais de tabelas não reconhecidas (diagnóstico S4)
        _unrecognized_headers: list = []
        if 'col_headers_raw' in _g.columns:
            _raw_hdrs = (_g[_g['col_headers_raw'].notna() & (_g['col_headers_raw'] != '')]
                         ['col_headers_raw'].unique().tolist())
            _unrecognized_headers = [h for h in _raw_hdrs if h][:5]

        # VSM Nível -1: política S5 por órgão
        _om = _org_meta.get(str(_sig), _OM_DEFAULT)
        _vsm_status_org = _om.get('status', 'ativo')
        _s5_meta_org    = _om.get('s5_pct_ok_meta', _OM_DEFAULT.get('s5_pct_ok_meta', 80.0))
        _vsm_gap        = round(_pct_ok_org - float(_s5_meta_org), 1) if _s5_meta_org is not None else None

        _por_orgao.append({
            'sigla':          _sig,
            'n_entregas':     int(len(_g)),
            'extrator':       str(_ext) if _ext is not None else None,
            'status':         'ok' if len(_g) > 0 else 'zero',
            # Stage 1 — parse quality
            'pct_ok':         _pct_ok_org,
            'sem_produto_n':  _sem_prod_n,
            'sem_produto_pct': _sem_prod_pct,
            # Stage 2 — field recognition
            'col_map_ok_rate':       _col_ok_rate,
            'unrecognized_headers':  _unrecognized_headers,
            # VSM Nível -1: S5 por órgão
            'vsm_status':     _vsm_status_org,
            'vsm_s5_meta':    _s5_meta_org,
            'vsm_gap_pp':     _vsm_gap,
            'vsm_estrategia': _om.get('estrategia'),
            'vsm_prioridade': _om.get('prioridade', 'normal'),
            # Triple Index (Beer/ViableOS): Actuality / Capability / Potentiality
            'triple_actuality':    _pct_ok_org,
            'triple_capability':   _col_ok_rate,   # max atingível sem mudar estrutura
            'triple_potentiality': float(_s5_meta_org) if _s5_meta_org else 80.0,
            'triple_gap_type': (
                # FIX 2026-04-07: usar fallback 100 quando _col_ok_rate é None
                # para não retornar null/ruido em órgãos com col_map não rastreado
                'ocr'         if (_g['texto'].isna().mean() > 0.5 if 'texto' in _g.columns else False) else
                'col_keys'    if ((_col_ok_rate if _col_ok_rate is not None else 100) < 60) else
                'vocabulario' if ((_col_ok_rate if _col_ok_rate is not None else 0) >= 60
                                  and _pct_ok_org < 80) else
                'ruido'
            ),
        })

    _cob_path = DIR_DB / 'ptd_cobertura_passos.csv'
    _cob = pd.read_csv(_cob_path) if _cob_path.exists() else None
    _zero_sig = (list(_cob[_cob['p6_entregas'] == 0]['sigla'])
                 if _cob is not None else [])
    _extratores = (_raw['extrator'].value_counts().to_dict()
                   if 'extrator' in _raw.columns else {})

    # ── Orgs "noise-only": têm rows mas pct_ok == 0 → ainda no Stage 0 ──
    # Órgãos com status=excluir (ex: ABNT-NBR-1) NÃO bloqueiam Stage 0
    _excluidos = {o['sigla'] for o in _por_orgao if o.get('vsm_status') == 'excluir'}
    _zero_or_noise = [s for s in list(_zero_sig) if s not in _excluidos] + [
        o['sigla'] for o in _por_orgao
        if o['n_entregas'] > 0 and o['pct_ok'] == 0 and o.get('vsm_status') != 'excluir'
    ]

    # ── Top frases não-identificadas (sinal para S1 vocab fix) ─────────
    _top_unmatched: list = []
    _top_unmatched_por_sigla: dict = {}
    if 'parse_flag' in _raw.columns and 'servico' in _raw.columns:
        import re as _re
        _pat_phrase = _re.compile(
            r'[A-ZÁÀÃÂÉÊÍÓÔÕÚÜÇ][a-záàãâéêíóôõúüç]+(?:\s+[A-ZÁÀÃÂÉÊÍÓÔÕÚÜÇa-záàãâéêíóôõúüç]+){1,4}')

        # Global: bigramas/trigramas mais frequentes em sem_produto
        _sem_prod_rows = _raw[_raw['parse_flag'] == 'sem_produto']['servico'].dropna()
        if len(_sem_prod_rows):
            _phrase_count: dict = {}
            for _txt in _sem_prod_rows.str[:120]:
                for _m in _pat_phrase.finditer(str(_txt)):
                    _p = _m.group(0).strip()
                    if len(_p) > 15:
                        _phrase_count[_p] = _phrase_count.get(_p, 0) + 1
            _top_unmatched = [
                {'phrase': p, 'count': c}
                for p, c in sorted(_phrase_count.items(), key=lambda x: -x[1])[:20]
                if c >= 5
            ]

        # Por sigla: top-5 frases para cada org com linhas sem_produto
        _sigla_col = 'sigla' if 'sigla' in _raw.columns else None
        if _sigla_col:
            _sem_rows = _raw[_raw['parse_flag'] == 'sem_produto']
            for _sig, _grp in _sem_rows.groupby(_sigla_col):
                if len(_grp) < 2:
                    continue
                _pc: dict = {}
                for _txt in _grp['servico'].dropna().str[:120]:
                    for _m in _pat_phrase.finditer(str(_txt)):
                        _p = _m.group(0).strip()
                        if len(_p) > 10:
                            _pc[_p] = _pc.get(_p, 0) + 1
                _top5 = [{'phrase': p, 'count': c}
                         for p, c in sorted(_pc.items(), key=lambda x: -x[1])[:5]
                         if c >= 2]
                if _top5:
                    _top_unmatched_por_sigla[str(_sig)] = _top5

    # Detectar estágio atual da iteração de qualidade
    _n_zero = len(_zero_or_noise)
    _sem_prod_global = round(
        sum(o['sem_produto_n'] for o in _por_orgao) / max(len(_raw), 1) * 100, 1)
    _col_ok_global   = round(
        float(np.nanmean([o['col_map_ok_rate'] for o in _por_orgao
                          if o['col_map_ok_rate'] is not None])), 1
    ) if any(o['col_map_ok_rate'] is not None for o in _por_orgao) else None

    # Orgs com pct_ok < 50% e pelo menos 30 rows — bloqueiam Stage 1
    _orgs_below_50 = [
        {'sigla': o['sigla'], 'pct_ok': o['pct_ok'], 'n': o['n_entregas']}
        for o in _por_orgao if o['n_entregas'] >= 30 and o['pct_ok'] < 50
    ]

    if _n_zero > 0:
        _stage = 0   # cobertura
    elif pct_ok < 90 or _orgs_below_50:
        _stage = 1   # parse quality / sem_produto
    elif _col_ok_global is not None and _col_ok_global < 70:
        _stage = 2   # reconhecimento de colunas
    else:
        _stage = 3   # riscos / completo

    _stage_labels = {0: 'cobertura', 1: 'parse_quality',
                     2: 'field_recognition', 3: 'riscos_coverage'}

    # ── Cobertura documental: preservação raw → v21 por sha256 ───────────
    # Verifica que os textos originais foram preservados no corpus final
    _doc_coverage: dict = {
        'cobertura_documental_pct': None,
        'texto_nao_nulo_pct': None,
        'pdfs_com_perda': [],
        'pdfs_analisados': 0,
    }
    try:
        _manifest_path = DIR_DB / 'pipeline_manifest.json'
        if _manifest_path.exists():
            _manifest = json.loads(_manifest_path.read_text())
            _rows_por_sha_raw = _manifest.get('rows_por_sha256', {})
            _texto_nao_nulo_raw = _manifest.get('texto_nao_nulo_pct', None)
            if _rows_por_sha_raw and not corpus.empty and 'pdf_sha256' in corpus.columns:
                _rows_v21 = corpus.groupby('pdf_sha256').size().to_dict()
                _preservacoes = []
                _pdfs_com_perda = []
                for sha, n_raw in _rows_por_sha_raw.items():
                    n_v21 = _rows_v21.get(sha, 0)
                    pct_pres = round(n_v21 / n_raw * 100, 1) if n_raw else 100.0
                    _preservacoes.append(pct_pres)
                    if pct_pres < 95.0:
                        # Encontrar nome do arquivo para este sha
                        _fname = next((k for k, v in _manifest.get('pdfs_sha256', {}).items()
                                       if v == sha), sha[:12])
                        _pdfs_com_perda.append({'arquivo': _fname, 'sha256': sha[:12],
                                                'n_raw': n_raw, 'n_v21': n_v21,
                                                'preservacao_pct': pct_pres})
                _doc_coverage = {
                    'cobertura_documental_pct': round(sum(_preservacoes) / len(_preservacoes), 1)
                        if _preservacoes else None,
                    'texto_nao_nulo_pct': _texto_nao_nulo_raw,
                    'pdfs_com_perda': sorted(_pdfs_com_perda, key=lambda x: x['preservacao_pct']),
                    'pdfs_analisados': len(_preservacoes),
                }
    except Exception as _e_cov:
        _doc_coverage['erro'] = str(_e_cov)

    # ── Cobertura de riscos (segundo corpus do propósito: entregas + riscos) ─
    _riscos_path = DIR_DB / 'ptd_riscos.csv'
    _risco_coverage: dict = {'cobertura_riscos_pct': None, 'n_orgaos_com_riscos': 0, 'n_riscos_total': 0}
    try:
        if _riscos_path.exists():
            _df_riscos = pd.read_csv(_riscos_path)
            _n_org_risco = int(_df_riscos['sigla'].nunique()) if 'sigla' in _df_riscos.columns else 0
            _n_riscos    = int(len(_df_riscos))
            _cobertura_r = round(_n_org_risco / max(n_orgaos, 1) * 100, 1) if n_orgaos > 0 else 0.0
            # Por sigla: n_riscos
            _riscos_por_sigla = _df_riscos.groupby('sigla').size().to_dict() if 'sigla' in _df_riscos.columns else {}
            # Adicionar n_riscos ao por_orgao
            for _o in _por_orgao:
                _o['n_riscos'] = int(_riscos_por_sigla.get(_o['sigla'], 0))
            _risco_coverage = {
                'cobertura_riscos_pct': _cobertura_r,
                'n_orgaos_com_riscos':  _n_org_risco,
                'n_riscos_total':       _n_riscos,
                'meta_cobertura_riscos': 80.0,
                'abaixo_meta':          _cobertura_r < 80.0,
            }
    except Exception as _e_r:
        _risco_coverage['erro'] = str(_e_r)

    _summary = {
        'run_id':               os.environ.get('GITHUB_RUN_ID', 'local'),
        'timestamp':            datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        'branch':               os.environ.get('GITHUB_REF_NAME', 'local'),
        'stage':                _stage,
        'stage_label':          _stage_labels[_stage],
        'n_orgaos':             int(n_orgaos),             # siglas distintas no corpus (leads)
        'n_orgaos_expandido':   int(n_orgaos_expandido),   # inclui sub-órgãos de grupos
        'n_orgaos_meta':        int(_n_orgaos_meta),        # total oficial do portal (91)
        'n_registros_raw':      int(len(_raw)),
        'n_registros_v21':      int(len(corpus)),
        'pct_ok':               float(pct_ok),
        'pct_ok_entregas':      float(pct_ok_entregas),  # só linhas de anexo_entregas
        'sem_produto_pct':      _sem_prod_global,
        'col_map_ok_rate':      _col_ok_global,
        'extratores':           {str(k): int(v) for k, v in _extratores.items()},
        # Corpus de riscos (segundo componente do propósito)
        'risco_coverage':       _risco_coverage,
        # Preservação documental
        'doc_coverage':         _doc_coverage,
        # Stage 0: zero ou noise-only
        'orgaos_zero_entregas': _zero_sig,
        'orgaos_zero_ou_noise': _zero_or_noise,
        # Stage 1: parse quality signals
        'orgs_below_50pct':          _orgs_below_50,
        'top_unmatched_phrases':     _top_unmatched,
        'top_unmatched_por_sigla':   _top_unmatched_por_sigla,
        'por_orgao':                 _por_orgao,
        # VSM Nível -1: órgãos excluídos por política S5 local
        'orgaos_excluidos':          sorted(_excluidos),
        # Organ groups: siglas expandidas a partir do corpus
        'siglas_corpus':             sorted(_siglas_corpus_set),
        'siglas_expandidas':         sorted(_siglas_expandidas),
    }
    _summary_path = DIR_DB / 'ptd_run_summary.json'
    _summary_path.write_text(
        json.dumps(_summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'📊 Diagnóstico salvo: {_summary_path}')
except Exception as _e:
    print(f'⚠ ptd_run_summary.json não gerado: {_e}')
