#!/usr/bin/env python3
"""gerar_relatorio_qualidade.py — Relatório HTML de qualidade do pipeline PTD-BR."""
import json, subprocess, sys
from datetime import datetime
from pathlib import Path

DIR_DB = Path("ptd_corpus/03_database")
DIR_DB.mkdir(parents=True, exist_ok=True)
OUT = DIR_DB / "ptd_relatorio_qualidade.html"

def _load_run_summary():
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

summary = _load_run_summary()
po      = summary.get("por_orgao", [])
pct_ok          = summary.get("pct_ok", 0.0)
pct_ok_entregas = summary.get("pct_ok_entregas", pct_ok)
n_orgaos        = summary.get("n_orgaos", len(po))
sem_produto_pct = summary.get("sem_produto_pct", 0.0)
stage           = summary.get("stage", 0)
stage_label     = summary.get("stage_label", "cobertura")
run_id          = summary.get("run_id", "local")
ts              = summary.get("timestamp", datetime.now().isoformat()[:10])
top_unmatched   = summary.get("top_unmatched_phrases", [])[:15]

def classify(v):
    col = v.get("col_map_ok_rate") or 100
    pct = v.get("pct_ok") or 0
    if col < 50: return "A", "col_keys"
    if pct >= 80: return "C", "ok"
    return "B", "col_keys" if col < 60 else "vocabulario"

def recomendacao(cl, gap):
    if cl == "A": return "Fix col_keys_extra.json"
    if cl == "C": return "Convergido — manter"
    if gap == "vocabulario": return "Expandir vocabulário"
    if gap == "col_keys": return "Fix col_keys_extra.json"
    return "Investigar"

SUBEIXOS = {"Projetos Especiais","Segurança e Privacidade","Governança e Gestão de Dados","Serviços Digitais e Melhoria da"}
PRODUTOS_AUSENTES = {"Integração à ferramenta de avaliação","Integração ao SEI","Integração ao Pagtesouro","Construção de diagnóstico","Evolução do serviço","Integração de avaliação","Implementação da Política de Governança"}
CONTAMINACAO = {"Representante da Ouvidoria do órgão","Gerente de Relacionamento","Ismael Alves Pereira Filho","Luciene Sicuti Damazo"}

def classify_phrase(p):
    if p in SUBEIXOS: return "🏷️ Sub-eixo (não é produto)", "#6c757d"
    if p in PRODUTOS_AUSENTES: return "📦 Produto ausente no vocab", "#dc6c00"
    if p in CONTAMINACAO: return "🚫 Contaminação", "#dc3545"
    return "❓ Investigar", "#555"

def bar_html(pct):
    w = min(max(int(pct), 0), 100)
    bg = "#28a745" if pct >= 80 else "#fd7e14" if pct >= 50 else "#dc3545"
    return (f'<div style="background:#e9ecef;border-radius:4px;height:14px;width:110px;display:inline-block">'
            f'<div style="background:{bg};width:{w}%;height:100%;border-radius:4px"></div></div>'
            f'<span style="margin-left:5px;font-size:12px">{pct:.1f}%</span>')

def badge(txt, color):
    return f'<span style="background:{color};color:#fff;padding:1px 7px;border-radius:10px;font-size:11px">{txt}</span>'

ERROS = [
    ("E1","Contaminação","#dc3545","Tabelas de risco como entregas — filtro fraco (linha 519) usava regex em vez de _is_risk_table()","17 órgãos","~150","✅ Corrigido 2026-04-07"),
    ("E2","Contaminação","#fd7e14","Signatários extraídos como serviços — PAT_SIGNATARIO parcial","6 órgãos","~80","✅ Parcial"),
    ("E3","Parser","#198754","ANATEL: 'Serviço digital: X' → ruido (PAT_RUIDO muito amplo). Fix: strip prefixo.","ANATEL","~30","✅ Corrigido 2026-04-07"),
    ("E4","Sigla falsa","#dc3545","_sigla_de_fn extraía 'ASSINADO' de mda-documento-diretivo-assinado_ptd-... — MDA perdido","MDA","83 linhas","🔴 Fix no pipeline, aguarda run"),
    ("E5","Sigla falsa","#dc3545","_sigla_de_fn extraía '21' de ptd_21_24_mcom-... — MCOM parcial","MCOM","12 linhas","🔴 Fix no pipeline, aguarda run"),
    ("E6","Diagnóstico watcher","#dc3545","N_ZERO>0 → problem_type=cobertura (OCR) para todos. MMULHERES (col_map=100%) precisa de vocab, não OCR.","4 órgãos","loop errado","🔴 Corrigido watcher.yml 2026-04-07"),
    ("E7","triple_gap_type","#dc3545","triple_gap_type=null para pct_ok=0 quando _col_ok_rate=None. Fix: fallback explícito.","4 órgãos","diagnóstico perdido","🔴 Corrigido gerar_relatorio.py 2026-04-07"),
    ("E8","Vocabulário","#ffc107","Integração ao SEI (44x), Integração ao Pagtesouro (42x), Construção de diagnóstico (54x)","20+ órgãos","140+","🟡 Pendente"),
    ("E9","Contaminação","#ffc107","Nomes de pessoas no top_unmatched: Ismael Alves Pereira Filho (24x), Luciene Sicuti Damazo (23x)","vários","47","🟡 Pendente filtro"),
    ("E10","col_map","#ffc107","INPI (20.6%), FUNDACENTRO (44.4%), INCRA (23.8%) — headers não reconhecidos","3 órgãos","n/a","🟡 Pendente col_keys"),
]

orgao_rows = []
for v in sorted(po, key=lambda x: x.get("pct_ok") or 0):
    sig = v.get("sigla",""); pct = v.get("pct_ok") or 0; col = v.get("col_map_ok_rate") or 0
    n = v.get("n_entregas",0); sp = v.get("sem_produto_pct") or 0
    cl, gap = classify(v); rec = recomendacao(cl, gap)
    cl_color = {"A":"#dc3545","B":"#fd7e14","C":"#198754"}[cl]
    orgao_rows.append(
        f"<tr><td><b>{sig}</b></td><td>{badge(f'Cluster {cl}',cl_color)}</td>"
        f"<td>{bar_html(pct)}</td><td style='text-align:center'>{col:.1f}%</td>"
        f"<td style='text-align:center'>{n}</td><td style='text-align:center'>{sp:.1f}%</td>"
        f"<td><small>{gap}</small></td><td><small>{rec}</small></td></tr>"
    )

phrase_rows = []
for p in top_unmatched:
    ph = p.get("phrase",""); cnt = p.get("count",0)
    cls, color = classify_phrase(ph)
    phrase_rows.append(f"<tr><td style='font-weight:600'>{cnt}</td><td>{ph}</td><td style='color:{color}'>{cls}</td></tr>")

SUB_ORGAOS = {
    "MD":["CEX","CM","COMAER","CENSIPAM","FOSORIO","HFA"],
    "MEC":["CAPES","EBSERH","FNDE","FUNDAJ","IBC","INEP","INES"],
    "MMA":["IBAMA","ICMBio","SFB","JBRJ"],
    "MIDR":["CODEVASF","SUDAM","SUDECO","SUDENE"],
    "MDA":["CONAB"], "MT":["ANTT","DNIT"], "MF":["RFB","STN","PGFN"],
}
sub_rows = [
    f"<tr><td><b>{lead}</b></td><td>{', '.join(subs)}</td><td style='text-align:center'>{len(subs)}</td><td><small>Herda do lead — sem PDF próprio</small></td></tr>"
    for lead,subs in SUB_ORGAOS.items()
]

stage_colors = {0:"#dc3545",1:"#fd7e14",2:"#0d6efd",3:"#198754"}
sc = stage_colors.get(stage,"#6c757d")

HTML = f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8"><title>PTD-BR — Qualidade</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f8f9fa;color:#212529}}
header{{background:#0d2b4e;color:#fff;padding:28px 40px}}
header h1{{font-size:22px;font-weight:800}}
header p{{font-size:12px;opacity:.7;margin-top:3px}}
.kpis{{display:flex;gap:16px;margin-top:18px;flex-wrap:wrap}}
.kpi{{background:rgba(255,255,255,.12);border-radius:8px;padding:12px 18px;min-width:120px}}
.kpi .val{{font-size:28px;font-weight:800}}
.kpi .lbl{{font-size:10px;opacity:.7;margin-top:2px;text-transform:uppercase;letter-spacing:.5px}}
.c{{max-width:1200px;margin:0 auto;padding:28px 20px}}
section{{background:#fff;border-radius:10px;padding:24px;margin-bottom:20px;box-shadow:0 1px 4px rgba(0,0,0,.08)}}
section h2{{font-size:17px;font-weight:700;margin-bottom:14px;padding-bottom:10px;border-bottom:2px solid #e9ecef}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{background:#f1f3f5;padding:9px 11px;text-align:left;font-weight:600;border-bottom:2px solid #dee2e6}}
td{{padding:8px 11px;border-bottom:1px solid #f4f5f6;vertical-align:middle}}
tr:hover td{{background:#fafbfc}}
.box{{border-left:4px solid #0d6efd;background:#e8f0fe;padding:12px 16px;border-radius:0 8px 8px 0;margin-bottom:14px;font-size:13px;line-height:1.6}}
.warn{{border-color:#fd7e14;background:#fff4e6}}
.grid3{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}
.card{{border:2px solid #dee2e6;border-radius:8px;padding:16px}}
.card h3{{font-size:14px;font-weight:700;margin-bottom:8px}}
.card ul{{padding-left:16px;font-size:13px;line-height:1.7}}
code{{background:#f1f3f5;padding:1px 5px;border-radius:3px;font-size:12px}}
footer{{text-align:center;padding:18px;font-size:11px;color:#aaa}}
@media(max-width:800px){{.grid3{{grid-template-columns:1fr}}}}
</style></head><body>
<header>
  <h1>PTD-BR — Relatório de Qualidade</h1>
  <p>Pipeline de Planos de Transformação Digital · run {run_id} · {ts}</p>
  <div class="kpis">
    <div class="kpi"><div class="val">{pct_ok:.1f}%</div><div class="lbl">pct_ok global</div></div>
    <div class="kpi"><div class="val">{pct_ok_entregas:.1f}%</div><div class="lbl">pct_ok entregas</div></div>
    <div class="kpi"><div class="val">{n_orgaos}</div><div class="lbl">órgãos</div></div>
    <div class="kpi"><div class="val">{91-n_orgaos}</div><div class="lbl">ausentes</div></div>
    <div class="kpi"><div class="val">{sem_produto_pct:.1f}%</div><div class="lbl">sem_produto</div></div>
    <div class="kpi"><div class="val" style="color:{sc}">Stage {stage}</div><div class="lbl">{stage_label}</div></div>
  </div>
</header>
<div class="c">

<section>
  <h2>O que mede pct_ok</h2>
  <div class="box"><b>pct_ok = n_ok / n_total</b> onde n_total inclui <em>todos</em> os tipos de linha:
  Anexo de Entregas (alvo) + Documento Diretivo (objetivos, governança) + resquícios de tabelas de risco + signatários.<br><br>
  <b>pct_ok_entregas</b> ({pct_ok_entregas:.1f}%) usa apenas <code>tipo_doc == 'anexo_entregas'</code> — métrica limpa do propósito do pipeline.
  {"A diferença entre os dois é " + f"{abs(pct_ok-pct_ok_entregas):.1f}pp — indica contaminação relevante." if abs(pct_ok-pct_ok_entregas) > 0.5 else "Ambos iguais: corpus sem coluna tipo_doc (run antigo) ou contaminação residual mínima."}
  </div>
  <p style="font-size:13px;color:#555">Meta S5: pct_ok ≥ 90%. Roteiro: Stage 0 (zeros) → Stage 1 (vocab, sem_produto &lt; 20%) → Stage 2 (col_map) → Stage 3 (riscos ≥ 80%).</p>
</section>

<section>
  <h2>Erros Identificados e Status</h2>
  <table><thead><tr><th>ID</th><th>Tipo</th><th>Descrição</th><th>Afeta</th><th>Ocorr.</th><th>Status</th></tr></thead><tbody>
""" + "".join(
    f'<tr><td><b>{e[0]}</b></td><td><span style="background:{e[2]};color:#fff;padding:1px 7px;border-radius:10px;font-size:11px">{e[1]}</span></td>'
    f'<td style="max-width:380px;font-size:12px">{e[3]}</td><td style="font-size:12px">{e[4]}</td><td style="text-align:center">{e[5]}</td>'
    f'<td style="white-space:nowrap;font-size:12px;color:{e[2]}">{e[6]}</td></tr>'
    for e in ERROS
) + f"""
  </tbody></table>
</section>

<section>
  <h2>Estado por Órgão ({len(po)} no corpus, meta: 91)</h2>
  <p style="font-size:12px;color:#555;margin-bottom:10px">
    <span style="color:#dc3545">■</span> Cluster A: col_map &lt; 50% &nbsp;
    <span style="color:#fd7e14">■</span> Cluster B: pct_ok &lt; 80% &nbsp;
    <span style="color:#198754">■</span> Cluster C: convergido (≥ 80%)
  </p>
  <div style="overflow-x:auto"><table>
    <thead><tr><th>Sigla</th><th>Cluster</th><th>pct_ok</th><th>col_map%</th><th>n</th><th>sem_prod%</th><th>gap_type</th><th>Recomendação</th></tr></thead>
    <tbody>{"".join(orgao_rows)}</tbody>
  </table></div>
</section>

<section>
  <h2>Top Frases Não-Identificadas</h2>
  <p style="font-size:12px;color:#555;margin-bottom:10px">Frases do campo <code>servico</code> em linhas <code>sem_produto</code>. Sub-eixos e contaminações NÃO devem entrar no vocab.</p>
  <table style="max-width:680px">
    <thead><tr><th>Count</th><th>Frase</th><th>Classificação</th></tr></thead>
    <tbody>{"".join(phrase_rows)}</tbody>
  </table>
</section>

<section>
  <h2>Estratégia de Evolução</h2>
  <div class="grid3">
    <div class="card" style="border-color:#dc3545">
      <h3 style="color:#dc3545">🔴 Cluster A — col_map</h3>
      <p style="font-size:12px;margin-bottom:8px">5 órgãos · col_map &lt; 50%</p>
      <ul><li>INPI (20.6%) — headers ilegíveis</li><li>INCRA (23.8%) — sem padrão</li><li>FUNDACENTRO (44.4%) — datas como header</li><li>FCP (43.8%) — tabela não padronizada</li><li><b>Ação:</b> col_keys_extra.json por sigla</li><li><b>ROI:</b> ~8pp global</li></ul>
    </div>
    <div class="card" style="border-color:#fd7e14">
      <h3 style="color:#fd7e14">🟠 Cluster B — vocab</h3>
      <p style="font-size:12px;margin-bottom:8px">42 órgãos · pct_ok &lt; 80%</p>
      <ul><li>Adicionar: Integração ao SEI (44x), Integração ao Pagtesouro (42x), Construção de diagnóstico (54x)</li><li>Variantes MD: "Fornecer Acesso Digital", "Integrar ao Login Único"</li><li>Filtrar: nomes de pessoas, Gerente de Relacionamento</li><li><b>Ação:</b> expandir vocab + reativar watcher</li><li><b>ROI:</b> ~12pp global</li></ul>
    </div>
    <div class="card" style="border-color:#198754">
      <h3 style="color:#198754">🟢 Cluster C — convergidos</h3>
      <p style="font-size:12px;margin-bottom:8px">18 órgãos · pct_ok ≥ 80%</p>
      <ul><li>ANVISA 85.1%, MGI 87.8%, PF 95.7%, MT 96.6%</li><li>Manter — não regredir</li><li>Expandir sub-órgãos virtuais via organ_groups.json</li><li><b>Ação:</b> monitorar + validar sub-órgãos</li></ul>
    </div>
  </div>
  <div class="box" style="margin-top:18px">
    <b>Próximo passo:</b> Run completo com fixes de sigla (MDA aparecerá).
    Validar que MMULHERES recebe diagnóstico <code>vocabulario</code> (não cobertura/OCR).
    Reativar watcher após confirmação.
  </div>
</section>

<section>
  <h2>26 Órgãos Ausentes — Anatomia do Gap (91 - {n_orgaos} = {91-n_orgaos})</h2>
  <div class="box warn">27 são <b>sub-órgãos virtuais</b> sem PDF próprio — herdam do lead.
  MDA estava ausente por bug em <code>_sigla_de_fn</code> (corrigido 2026-04-07).
  PRF é NOVO (sem PDF no catálogo ainda).</div>
  <table><thead><tr><th>Lead</th><th>Sub-órgãos (virtuais)</th><th>Qtd</th><th>Status</th></tr></thead>
  <tbody>{"".join(sub_rows)}</tbody></table>
</section>

</div>
<footer>PTD-BR Pipeline · Gerado em {datetime.now().strftime("%Y-%m-%d %H:%M")} · run {run_id}</footer>
</body></html>"""

OUT.write_text(HTML, encoding="utf-8")
print(f"OK: {OUT} ({OUT.stat().st_size//1024}KB)")
