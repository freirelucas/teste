#!/usr/bin/env python3
"""
gerar_dashboard_s3.py — Dashboard do Sistema 3 (Gestão) do VSM PTD-BR
Visualiza metaparâmetros, curva de aprendizado, sinal algedônico e insights S4.
Saída: ptd_corpus/03_database/ptd_dashboard_s3.html
"""
from pathlib import Path
import json
from datetime import datetime

DB   = Path('ptd_corpus/03_database')
LOG  = Path('ptd_corpus/02_logs')
OUT  = DB / 'ptd_dashboard_s3.html'

# ── Carregamento ──────────────────────────────────────────────────────────────

def _load_json(path: Path, default=None):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except Exception:
            pass
    return default if default is not None else {}


def _load_all():
    d = {}
    d['params']   = _load_json(Path('config/s3_meta_parameters.json'))
    d['signals']  = _load_json(Path('ptd_learning_signals.json'))
    d['summary']  = _load_json(DB / 'ptd_run_summary.json')
    d['stage']    = _load_json(LOG / 'stage_status.json')

    # Iteração atual do .trigger_debug
    d['iteration'] = 155
    t = Path('.trigger_debug')
    if t.exists():
        for line in t.read_text().splitlines():
            if 'iteration' in line:
                try: d['iteration'] = int(line.split(':')[-1].strip())
                except Exception: pass
    return d


# ── SVG: curva de pct_ok ao longo das iterações ──────────────────────────────

def _svg_learning_curve(history: list) -> str:
    if not history:
        return '<p style="color:#9ca3af">Sem histórico de iterações ainda.</p>'
    W, H, PAD = 600, 200, 40
    vals = [e.get('pct_ok', 0) for e in history[-50:]]  # últimas 50
    iters = [e.get('iteration', i) for i, e in enumerate(history[-50:])]
    if not vals:
        return ''
    min_v, max_v = min(vals), max(vals)
    rng = max(max_v - min_v, 1)
    chart_w = W - PAD * 2
    chart_h = H - PAD * 2

    def px(i, n): return PAD + i / max(n - 1, 1) * chart_w
    def py(v):    return PAD + chart_h - (v - min_v) / rng * chart_h

    n = len(vals)
    pts = ' '.join(f'{px(i,n):.1f},{py(v):.1f}' for i, v in enumerate(vals))
    # Linha de meta (90%)
    meta_y = py(90) if 90 >= min_v else py(max_v)
    # Linha de tendência atual
    last_v  = round(vals[-1], 1) if vals else 0
    first_v = round(vals[0],  1) if vals else 0

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" style="font-family:sans-serif">',
        f'<rect x="{PAD}" y="{PAD}" width="{chart_w}" height="{chart_h}" fill="#f9fafb" rx="4" stroke="#e5e7eb"/>',
        # Meta 90%
        f'<line x1="{PAD}" y1="{meta_y:.1f}" x2="{W-PAD}" y2="{meta_y:.1f}" stroke="#10b981" stroke-dasharray="5,3" stroke-width="1.5"/>',
        f'<text x="{W-PAD+4}" y="{meta_y:.1f}+4" font-size="10" fill="#10b981">meta 90%</text>',
        # Curva principal
        f'<polyline points="{pts}" fill="none" stroke="#3b82f6" stroke-width="2"/>',
        # Ponto atual
        f'<circle cx="{px(n-1,n):.1f}" cy="{py(vals[-1]):.1f}" r="4" fill="#3b82f6"/>',
        # Labels eixos
        f'<text x="{PAD}" y="{H-8}" font-size="10" fill="#6b7280">iter {iters[0]}</text>',
        f'<text x="{W-PAD-20}" y="{H-8}" font-size="10" fill="#6b7280">iter {iters[-1]}</text>',
        f'<text x="{PAD-38}" y="{py(min_v)+4:.1f}" font-size="10" fill="#6b7280">{min_v:.0f}%</text>',
        f'<text x="{PAD-38}" y="{py(max_v)+4:.1f}" font-size="10" fill="#6b7280">{max_v:.0f}%</text>',
        f'<text x="{W/2-30}" y="14" font-size="11" font-weight="bold" fill="#374151">pct_ok: {first_v}% → {last_v}%</text>',
        '</svg>',
    ]
    return '\n'.join(lines)


# ── CSS ───────────────────────────────────────────────────────────────────────
CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',system-ui,sans-serif;background:#0f172a;color:#e2e8f0;line-height:1.5}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px;padding:24px}
.card{background:#1e293b;border-radius:12px;padding:20px;border:1px solid #334155}
.card h2{font-size:0.85rem;text-transform:uppercase;letter-spacing:1px;color:#64748b;margin-bottom:12px}
.card h3{font-size:1rem;font-weight:700;color:#f1f5f9;margin-bottom:8px}
.kpi-row{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:8px}
.kpi{background:#0f172a;border-radius:8px;padding:12px 16px;text-align:center;flex:1;min-width:100px}
.kpi .val{font-size:1.8rem;font-weight:800;color:#38bdf8}
.kpi .lbl{font-size:0.75rem;color:#64748b;margin-top:2px}
table{width:100%;border-collapse:collapse;font-size:0.83rem}
th{background:#0f172a;color:#94a3b8;padding:6px 10px;text-align:left;font-weight:600}
td{padding:6px 10px;border-bottom:1px solid #1e293b;color:#cbd5e1}
tr:hover td{background:#1e293b}
.badge{display:inline-block;padding:2px 8px;border-radius:999px;font-size:0.75rem;font-weight:600}
.ok{background:#064e3b;color:#6ee7b7}.warn{background:#451a03;color:#fcd34d}.fail{background:#450a0a;color:#fca5a5}
.algedonico{background:#7f1d1d;border:1px solid #ef4444;border-radius:12px;padding:16px;margin:8px 0}
.algedonico.safe{background:#052e16;border-color:#22c55e}
.insight{background:#0f172a;border-left:3px solid #3b82f6;padding:10px 14px;margin:8px 0;border-radius:0 6px 6px 0}
.insight .at{font-size:0.75rem;color:#64748b}
.strategy-chip{display:inline-block;background:#1e40af;color:#bfdbfe;padding:4px 12px;border-radius:999px;font-weight:700;font-size:0.9rem}
header{background:#1e293b;border-bottom:1px solid #334155;padding:16px 24px;display:flex;align-items:center;gap:16px}
header h1{font-size:1.3rem;font-weight:800;color:#f1f5f9}
header .sub{font-size:0.8rem;color:#64748b}
.param-row{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #1e293b;font-size:0.85rem}
.param-key{color:#94a3b8}
.param-val{color:#38bdf8;font-family:monospace;font-weight:600}
"""

# ── Seções ────────────────────────────────────────────────────────────────────

def _card_kpis(d: dict) -> str:
    s = d['summary']
    it = d['iteration']
    pct = s.get('pct_ok', 0)
    stage = s.get('stage_label', '?')
    n = s.get('n_registros_v21', 0)
    sem_prod = s.get('sem_produto_pct', 0)
    badge = 'ok' if pct >= 80 else ('warn' if pct >= 60 else 'fail')
    # Riscos — segundo componente do propósito
    rc = s.get('risco_coverage', {})
    n_riscos = rc.get('n_riscos_total', 0)
    cob_riscos = rc.get('cobertura_riscos_pct')
    riscos_badge = ('ok' if cob_riscos and cob_riscos >= 80 else
                    'warn' if cob_riscos and cob_riscos >= 50 else 'fail')
    riscos_val = f"{cob_riscos}%" if cob_riscos is not None else "—"
    return f"""
<div class="card" style="grid-column:1/-1">
  <h2>Painel de Controle S3 — Sistema 3 (Gestão)</h2>
  <p style="font-size:12px;color:#6b7280;margin-bottom:8px">
    Propósito: corpus de <strong>entregas</strong> + <strong>riscos</strong> dos PTDs disponíveis no Portal gov.br
  </p>
  <div class="kpi-row">
    <div class="kpi"><div class="val">{it}</div><div class="lbl">Iteração atual</div></div>
    <div class="kpi"><div class="val"><span class="badge {badge}">{pct}%</span></div><div class="lbl">pct_ok entregas</div></div>
    <div class="kpi"><div class="val">{n:,}</div><div class="lbl">Entregas v21</div></div>
    <div class="kpi"><div class="val"><span class="badge {riscos_badge}">{riscos_val}</span></div><div class="lbl">Cobertura riscos</div></div>
    <div class="kpi"><div class="val">{n_riscos:,}</div><div class="lbl">Riscos extraídos</div></div>
    <div class="kpi"><div class="val">{sem_prod}%</div><div class="lbl">sem_produto</div></div>
    <div class="kpi"><div class="val">{stage}</div><div class="lbl">Stage atual</div></div>
  </div>
</div>"""


def _card_learning_curve(d: dict) -> str:
    history = d['signals'].get('run_history', [])
    svg = _svg_learning_curve(history)
    n_hist = len(history)
    return f"""
<div class="card" style="grid-column:span 2">
  <h2>Curva de Aprendizado (L-C)</h2>
  <h3>pct_ok ao longo das iterações ({n_hist} entradas)</h3>
  {svg}
</div>"""


def _card_strategy(d: dict) -> str:
    signals = d['signals']
    cs = signals.get('current_strategy', {})
    focus = cs.get('focus', '?')
    auto_add = cs.get('auto_add_threshold', '?')
    review   = cs.get('review_threshold', '?')
    priority = cs.get('priority_siglas', [])
    history  = signals.get('run_history', [])

    # Calcular slope das últimas 10 iterações
    recent_vals = [e.get('pct_ok', 0) for e in history[-10:] if e.get('pct_ok') is not None]
    slope = 0.0
    if len(recent_vals) >= 2:
        n = len(recent_vals)
        xs = list(range(n)); xm = sum(xs)/n; ym = sum(recent_vals)/n
        num = sum((x-xm)*(y-ym) for x,y in zip(xs,recent_vals))
        den = sum((x-xm)**2 for x in xs)
        slope = round(num/den, 3) if den else 0.0

    slope_badge = 'ok' if slope >= 0.3 else ('warn' if slope >= 0.1 else 'fail')
    pri_str = ', '.join(priority[:5]) if priority else '—'
    return f"""
<div class="card">
  <h2>Estratégia S4 (L-B)</h2>
  <h3>Estratégia atual: <span class="strategy-chip">{focus}</span></h3>
  <div class="param-row"><span class="param-key">Slope pct_ok (últimas 10 iter)</span>
    <span class="badge {slope_badge}">{slope:+.3f} pp/iter</span></div>
  <div class="param-row"><span class="param-key">auto_add_threshold</span>
    <span class="param-val">{auto_add}</span></div>
  <div class="param-row"><span class="param-key">review_threshold</span>
    <span class="param-val">{review}</span></div>
  <div class="param-row"><span class="param-key">Siglas prioritárias</span>
    <span class="param-val" style="font-size:0.8rem">{pri_str}</span></div>
</div>"""


def _card_algedonico(d: dict) -> str:
    params = d['params'].get('algedonico', {})
    max_iters = params.get('max_iters_sem_progresso', 15)
    min_prog   = params.get('progresso_minimo_pp', 0.5)
    history    = d['signals'].get('run_history', [])

    # Contar iterações consecutivas sem progresso >= min_prog
    iters_sem = 0
    for entry in reversed(history):
        if entry.get('delta', 0) < min_prog:
            iters_sem += 1
        else:
            break

    pct_alg = round(iters_sem / max(max_iters, 1) * 100)
    is_ativo = iters_sem >= max_iters
    cls = 'algedonico' if is_ativo else 'algedonico safe'
    sym = '🚨' if is_ativo else '✅'
    status = f'ATIVO — escalação S5 necessária!' if is_ativo else f'Inativo ({iters_sem}/{max_iters} iters)'

    return f"""
<div class="card">
  <h2>Sinal Algedônico</h2>
  <div class="{cls}">
    <div style="font-size:1.4rem">{sym} {status}</div>
    <div style="margin-top:8px;font-size:0.85rem;color:#94a3b8">
      {iters_sem} iterações sem progresso ≥ {min_prog}pp<br>
      Threshold: {max_iters} iterações
    </div>
    <div style="margin-top:10px;background:#0f172a;border-radius:6px;height:8px;overflow:hidden">
      <div style="height:100%;width:{min(pct_alg,100)}%;background:{'#ef4444' if is_ativo else '#22c55e'};transition:width .3s"></div>
    </div>
  </div>
</div>"""


def _card_doc_coverage(d: dict) -> str:
    cov = d['summary'].get('doc_coverage', {})
    pct = cov.get('cobertura_documental_pct')
    txt_pct = cov.get('texto_nao_nulo_pct')
    perdas  = cov.get('pdfs_com_perda', [])
    n_anal  = cov.get('pdfs_analisados', 0)

    if pct is None:
        return f"""<div class="card"><h2>Cobertura Documental</h2>
<p style="color:#64748b">Execute o pipeline primeiro para gerar pipeline_manifest.json com rows_por_sha256.</p></div>"""

    badge = 'ok' if pct >= 95 else ('warn' if pct >= 80 else 'fail')
    rows_perda = ''
    for p in perdas[:5]:
        rows_perda += f'<tr><td>{p["arquivo"][:30]}</td><td>{p["n_raw"]}</td><td>{p["n_v21"]}</td><td><span class="badge fail">{p["preservacao_pct"]}%</span></td></tr>'

    return f"""
<div class="card">
  <h2>Cobertura Documental (S3*)</h2>
  <div class="kpi-row">
    <div class="kpi"><div class="val"><span class="badge {badge}">{pct}%</span></div><div class="lbl">Linhas preservadas raw→v21</div></div>
    <div class="kpi"><div class="val">{txt_pct or '?'}%</div><div class="lbl">Texto não-nulo</div></div>
    <div class="kpi"><div class="val">{n_anal}</div><div class="lbl">PDFs analisados</div></div>
  </div>
  {'<h3 style="margin-top:12px">PDFs com perda &gt; 5%</h3><table><tr><th>Arquivo</th><th>n_raw</th><th>n_v21</th><th>Preservação</th></tr>' + rows_perda + '</table>' if perdas else '<p style="color:#22c55e;margin-top:8px">✅ Todos os PDFs com cobertura ≥ 95%</p>'}
</div>"""


def _card_meta_insights(d: dict) -> str:
    insights = d['signals'].get('meta_insights', [])
    if not insights:
        return f"""<div class="card"><h2>Meta-Insights S4 (L-B)</h2>
<p style="color:#64748b">Nenhum meta-insight ainda. Gerado a cada 10 iterações pelo meta_learning.py.</p></div>"""

    items = ''
    for ins in reversed(insights[-5:]):
        at  = ins.get('at_iteration', '?')
        strat = f"{ins.get('strategy_prev','?')} → {ins.get('strategy_next','?')}"
        slope = ins.get('slope_pct_ok_per_iter', 0)
        reas  = ins.get('reasoning', '')
        items += f"""<div class="insight">
  <div class="at">Iteração {at} | slope={slope:+.3f}pp | {strat}</div>
  <div style="margin-top:4px;font-size:0.88rem">{reas}</div>
</div>"""

    return f"""
<div class="card">
  <h2>Meta-Insights S4 (últimos 5)</h2>
  {items}
</div>"""


def _card_meta_params(d: dict) -> str:
    from datetime import datetime, timezone
    p = d['params']
    pa = p.get('parada_automatica', {})

    # Calcular tempo restante até deadline
    deadline_str = pa.get('deadline_iso', '')
    tempo_restante = ''
    if deadline_str:
        try:
            deadline_dt = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            delta = deadline_dt - now
            if delta.total_seconds() > 0:
                h = int(delta.total_seconds() // 3600)
                m = int((delta.total_seconds() % 3600) // 60)
                tempo_restante = f'{h}h{m:02d}min restantes'
            else:
                tempo_restante = '⚠ PRAZO VENCIDO'
        except Exception:
            tempo_restante = deadline_str

    parada_html = ''
    if pa.get('ativo'):
        cor = '#1e3a1e' if 'VENCIDO' not in tempo_restante else '#3a1e1e'
        border = '#16a34a' if 'VENCIDO' not in tempo_restante else '#dc2626'
        parada_html = f"""
<div style="background:{cor};border:1px solid {border};border-radius:8px;padding:12px;margin-bottom:12px">
  <div style="color:#4ade80;font-weight:700;font-size:0.85rem">🕐 PARADA AUTOMÁTICA ATIVA</div>
  <div class="param-row"><span class="param-key">Deadline</span><span class="param-val">{deadline_str}</span></div>
  <div class="param-row"><span class="param-key">Tempo restante</span><span class="param-val">{tempo_restante}</span></div>
  <div class="param-row"><span class="param-key">Slope mínimo</span><span class="param-val">{pa.get('min_slope_para_continuar','?')} pp/iter</span></div>
  <div class="param-row"><span class="param-key">Janela slope</span><span class="param-val">últimas {pa.get('slope_window','20')} iterações</span></div>
  <div class="param-row"><span class="param-key">Meta sucesso</span><span class="param-val">pct_ok ≥ {pa.get('pct_ok_sucesso','90')}%</span></div>
</div>"""

    rows = ''
    flat = {
        'vocab.auto_add_threshold': p.get('vocab_expansion', {}).get('auto_add_threshold', '?'),
        'vocab.review_threshold':   p.get('vocab_expansion', {}).get('review_threshold', '?'),
        'qualidade.pct_ok_meta':    p.get('qualidade', {}).get('pct_ok_meta', '?'),
        'qualidade.sem_produto_max':p.get('qualidade', {}).get('sem_produto_max_pct', '?'),
        'aprendizado.slope_forte':  p.get('aprendizado', {}).get('slope_forte', '?'),
        'aprendizado.slope_fraco':  p.get('aprendizado', {}).get('slope_fraco', '?'),
        'aprendizado.janela':       p.get('aprendizado', {}).get('janela_meta_learning', '?'),
        'algedonico.max_iters':     p.get('algedonico', {}).get('max_iters_sem_progresso', '?'),
        'doc_coverage.min_pct':     p.get('doc_coverage', {}).get('preservacao_minima_pct', '?'),
    }
    for k, v in flat.items():
        rows += f'<div class="param-row"><span class="param-key">{k}</span><span class="param-val">{v}</span></div>'

    return f"""
<div class="card">
  <h2>Metaparâmetros S2 (config/s3_meta_parameters.json)</h2>
  {parada_html}
  {rows}
  <p style="margin-top:12px;font-size:0.75rem;color:#475569">Edite config/s3_meta_parameters.json para ajustar. Lido automaticamente pelo watcher e meta_learning.py.</p>
</div>"""


def _card_por_orgao(d: dict) -> str:
    orgs = d['summary'].get('por_orgao', [])
    if not orgs:
        return ''
    stalled = [o for o in orgs if o.get('pct_ok', 100) < 60][:8]
    rows = ''
    for o in stalled:
        pok = o.get('pct_ok', 0)
        badge = 'warn' if pok >= 40 else 'fail'
        col_ok = o.get('col_map_ok_rate')
        col_str = f"{col_ok}%" if col_ok is not None else '—'
        rows += f'<tr><td><strong>{o["sigla"]}</strong></td><td>{o["n_entregas"]}</td><td><span class="badge {badge}">{pok}%</span></td><td>{col_str}</td></tr>'

    return f"""
<div class="card">
  <h2>Órgãos Estagnados (pct_ok &lt; 60%)</h2>
  <table><tr><th>Sigla</th><th>n</th><th>pct_ok</th><th>col_map_ok</th></tr>
  {rows if rows else '<tr><td colspan="4" style="color:#22c55e">Nenhum órgão abaixo de 60%</td></tr>'}
  </table>
</div>"""


def _card_vsm_tree(d: dict) -> str:
    """Card de recursão VSM: 3 níveis (IPEA → Pipeline → Por-órgão)."""
    orgs = d['summary'].get('por_orgao', [])
    excluidos = set(d['summary'].get('orgaos_excluidos', []))
    zero_noise = set(d['summary'].get('orgaos_zero_ou_noise', []))
    pct_ok_global = d['summary'].get('pct_ok', 0)

    # Nível -1: badges por órgão
    def _badge_org(o: dict) -> str:
        sig = o['sigla']
        vsm_st = o.get('vsm_status', 'ativo')
        pok = o.get('pct_ok', 0)
        meta = o.get('vsm_s5_meta') or 80.0
        gap = o.get('vsm_gap_pp')
        pri = o.get('vsm_prioridade', 'normal')
        estrategia = o.get('vsm_estrategia', '—')

        if vsm_st == 'excluir':
            color = '#6b7280'; label = 'excluído'
        elif sig in zero_noise:
            color = '#ef4444'; label = 'noise-only'
        elif pok >= float(meta):
            color = '#22c55e'; label = 'convergido'
        elif pok >= float(meta) * 0.8:
            color = '#f59e0b'; label = 'progredindo'
        else:
            color = '#ef4444'; label = 'abaixo meta'

        pri_icon = {'alta': '🔴', 'media': '🟡', 'normal': '🟢', 'nenhuma': '⬜'}.get(pri, '')
        tip = f"pct_ok={pok}% | meta={meta}% | gap={gap:+.1f}pp | {estrategia}" if gap is not None else f"pct_ok={pok}% | {estrategia}"
        return (f'<span title="{tip}" style="display:inline-block;margin:2px;padding:2px 6px;'
                f'border-radius:4px;font-size:11px;background:{color}22;color:{color};'
                f'border:1px solid {color}66">{pri_icon}{sig}</span>')

    # Separar órgãos por status
    orgs_excluidos = [o for o in orgs if o.get('vsm_status') == 'excluir']
    orgs_noise = [o for o in orgs if o['sigla'] in zero_noise and o.get('vsm_status') != 'excluir']
    orgs_ativos = [o for o in orgs if o.get('vsm_status') != 'excluir' and o['sigla'] not in zero_noise]
    orgs_convergidos = [o for o in orgs_ativos if o.get('pct_ok', 0) >= (o.get('vsm_s5_meta') or 80.0)]
    orgs_progress = [o for o in orgs_ativos if o not in orgs_convergidos]

    badges_noise = ''.join(_badge_org(o) for o in orgs_noise) or '<em style="color:#6b7280">nenhum</em>'
    badges_progress = ''.join(_badge_org(o) for o in sorted(orgs_progress, key=lambda x: x.get('pct_ok', 0))[:20])
    badges_conv = ''.join(_badge_org(o) for o in orgs_convergidos[:20])
    badges_excl = ''.join(_badge_org(o) for o in orgs_excluidos) or '<em style="color:#6b7280">nenhum</em>'

    # Resumo Nível -1
    n_total = len(orgs)
    n_conv = len(orgs_convergidos)
    n_noise = len(orgs_noise)
    n_excl = len(orgs_excluidos)

    return f"""
<div class="card" style="grid-column: span 2">
  <h2>Recursão VSM — 3 Níveis (Beer)</h2>
  <p style="color:#9ca3af;font-size:12px;margin-bottom:12px">
    <em>"Um sistema viável contém sistemas viáveis e está contido por sistemas viáveis."</em>
  </p>

  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:16px">
    <div style="background:#1f2937;border-radius:8px;padding:12px;border-left:3px solid #6366f1">
      <div style="font-size:11px;color:#9ca3af;text-transform:uppercase">Nível +1 — IPEA</div>
      <div style="font-size:13px;margin-top:6px">
        <strong>S5</strong>: mandato de pesquisa IPEA<br>
        <strong>S4</strong>: inteligência EFGD federal<br>
        <strong>S3</strong>: gestão COGIT/DIEST<br>
        <strong>S1</strong>: <span style="color:#6366f1">PTD-BR Pipeline ← nós</span>
      </div>
    </div>
    <div style="background:#1f2937;border-radius:8px;padding:12px;border-left:3px solid #22c55e">
      <div style="font-size:11px;color:#9ca3af;text-transform:uppercase">Nível 0 — Pipeline</div>
      <div style="font-size:13px;margin-top:6px">
        <strong>S5</strong>: s3_meta_parameters.json<br>
        <strong>S4</strong>: meta_learning.py<br>
        <strong>S3</strong>: watcher.yml<br>
        <strong>S3*</strong>: gerar_relatorio.py<br>
        <strong>S1</strong>: {n_total} órgãos (<span style="color:#22c55e">{pct_ok_global:.1f}% pct_ok</span>)
      </div>
    </div>
    <div style="background:#1f2937;border-radius:8px;padding:12px;border-left:3px solid #f59e0b">
      <div style="font-size:11px;color:#9ca3af;text-transform:uppercase">Nível -1 — Por-órgão</div>
      <div style="font-size:13px;margin-top:6px">
        <strong>S5</strong>: config/org_meta.json<br>
        <strong>S4</strong>: per_sigla_strategy<br>
        <strong>S3</strong>: slope per-sigla<br>
        <strong>S1</strong>: {n_conv} convergidos / {n_total - n_excl} ativos
      </div>
    </div>
  </div>

  <div style="margin-bottom:10px">
    <span style="font-size:12px;color:#ef4444;font-weight:600">Noise-only ({n_noise}) — bloqueiam Stage 0:</span><br>
    <div style="margin-top:4px">{badges_noise}</div>
  </div>
  <div style="margin-bottom:10px">
    <span style="font-size:12px;color:#f59e0b;font-weight:600">Em progresso ({len(orgs_progress)}):</span><br>
    <div style="margin-top:4px">{badges_progress if badges_progress else '<em style="color:#6b7280">nenhum</em>'}</div>
  </div>
  <div style="margin-bottom:10px">
    <span style="font-size:12px;color:#22c55e;font-weight:600">Convergidos ({n_conv}):</span><br>
    <div style="margin-top:4px">{badges_conv if badges_conv else '<em style="color:#6b7280">nenhum ainda</em>'}</div>
  </div>
  <div>
    <span style="font-size:12px;color:#6b7280;font-weight:600">Excluídos por S5 ({n_excl}) — não contam nas métricas:</span><br>
    <div style="margin-top:4px">{badges_excl}</div>
  </div>
</div>"""


# ── Montagem ──────────────────────────────────────────────────────────────────

def _render(d: dict) -> str:
    ts = datetime.now().strftime('%d/%m/%Y %H:%M')
    it = d['iteration']
    cards = '\n'.join([
        _card_kpis(d),
        _card_vsm_tree(d),
        _card_learning_curve(d),
        _card_algedonico(d),
        _card_doc_coverage(d),
        _card_strategy(d),
        _card_meta_insights(d),
        _card_meta_params(d),
        _card_por_orgao(d),
    ])
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta http-equiv="refresh" content="300">
  <title>PTD-BR — Dashboard S3 | Iter {it}</title>
  <style>{CSS}</style>
</head>
<body>
<header>
  <div>
    <h1>PTD-BR Pipeline — Dashboard S3 (Gestão)</h1>
    <div class="sub">Iteração {it} · Gerado em {ts} · Auto-refresh 5min · VSM S3/S4 monitor</div>
  </div>
</header>
<div class="grid">
{cards}
</div>
</body>
</html>"""


def main():
    print('Carregando dados S3...')
    d = _load_all()
    n_hist = len(d['signals'].get('run_history', []))
    n_insights = len(d['signals'].get('meta_insights', []))
    pct = d['summary'].get('pct_ok', '?')
    print(f'  pct_ok={pct}% | {n_hist} runs | {n_insights} meta-insights')
    print('Gerando dashboard...')
    html = _render(d)
    DB.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding='utf-8')
    size_kb = OUT.stat().st_size // 1024
    print(f'Dashboard S3: {OUT} ({size_kb} KB)')


if __name__ == '__main__':
    main()
