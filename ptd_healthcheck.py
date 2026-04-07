#!/usr/bin/env python3
"""
PTD-BR — Health Check do Ambiente e dos Outputs
IPEA / COGIT / DIEST

Uso: python ptd_healthcheck.py
     python ptd_healthcheck.py --outputs   # verifica CSVs gerados

Retorna código de saída 0 (tudo OK) ou 1 (há falhas críticas).
"""
import sys, subprocess, importlib, hashlib, json
from pathlib import Path

# ── Cores ANSI ────────────────────────────────────────────────────────
OK   = '\033[92m✅\033[0m'
WARN = '\033[93m⚠️ \033[0m'
FAIL = '\033[91m✗ \033[0m'
INFO = '\033[94mℹ️ \033[0m'

checks_pass = 0
checks_warn = 0
checks_fail = 0

def check(label, passed, msg='', warn=False):
    global checks_pass, checks_warn, checks_fail
    if passed:
        print(f'  {OK} {label}')
        checks_pass += 1
    elif warn:
        print(f'  {WARN} {label}  ← {msg}')
        checks_warn += 1
    else:
        print(f'  {FAIL} {label}  ← {msg}')
        checks_fail += 1

# ════════════════════════════════════════════════════════════════════
# BLOCO 1 — Python e versão
# ════════════════════════════════════════════════════════════════════
print('\n── Python ─────────────────────────────────────────────────')
vi = sys.version_info
check(f'Python {vi.major}.{vi.minor}.{vi.micro}',
      vi >= (3, 10),
      'Requer Python 3.10+')

# ════════════════════════════════════════════════════════════════════
# BLOCO 2 — Dependências Python
# ════════════════════════════════════════════════════════════════════
print('\n── Dependências Python ─────────────────────────────────────')
DEPS = {
    'pandas':    ('2.0', 'pandas'),
    'numpy':     ('1.24', 'numpy'),
    'requests':  ('2.31', 'requests'),
    'fitz':      ('1.23', 'PyMuPDF'),
    'pyarrow':   ('12.0', 'pyarrow'),
    'pptx':      ('1.0',  'python-pptx'),
    'bs4':       ('4.12', 'beautifulsoup4'),
    'matplotlib':('3.7',  'matplotlib'),
    'seaborn':   ('0.12', 'seaborn'),
}
for mod, (min_ver, pip_name) in DEPS.items():
    try:
        m = importlib.import_module(mod)
        ver = getattr(m, '__version__', '?')
        check(f'{pip_name} {ver}', True)
    except ImportError:
        check(pip_name, False, f'pip install {pip_name}')

# Docling (opcional mas preferencial)
try:
    from docling.document_converter import DocumentConverter
    check('docling (TableFormer)', True)
    _docling = True
except ImportError:
    check('docling', False,
          'pip install docling  — usando fallback PyMuPDF', warn=True)
    _docling = False

# ════════════════════════════════════════════════════════════════════
# BLOCO 3 — Tesseract (OCR para PDFs tarjados)
# ════════════════════════════════════════════════════════════════════
print('\n── Tesseract OCR ───────────────────────────────────────────')
try:
    r = subprocess.run(['tesseract', '--version'],
                       capture_output=True, text=True, timeout=5)
    ver = r.stdout.split('\n')[0]
    check(f'tesseract {ver}', True)
except Exception:
    check('tesseract', False,
          'apt-get install tesseract-ocr tesseract-ocr-por', warn=True)

try:
    r = subprocess.run(['tesseract', '--list-langs'],
                       capture_output=True, text=True, timeout=5)
    has_por = 'por' in r.stdout + r.stderr
    check('tesseract idioma "por" instalado', has_por,
          'apt-get install tesseract-ocr-por', warn=not has_por)
except Exception:
    check('tesseract idioma "por"', False, warn=True)

# ════════════════════════════════════════════════════════════════════
# BLOCO 4 — Arquivos de configuração
# ════════════════════════════════════════════════════════════════════
print('\n── Config ──────────────────────────────────────────────────')
DIR_CFG = Path('config')
for fname in ['produtos_sgd_v23.json', 'correcoes_eixo.json']:
    p = DIR_CFG / fname
    if p.exists():
        try:
            json.loads(p.read_text(encoding='utf-8'))
            check(f'config/{fname}  (JSON válido)', True)
        except json.JSONDecodeError as e:
            check(f'config/{fname}', False, f'JSON inválido: {e}')
    else:
        check(f'config/{fname}', False, 'Arquivo ausente')

# ════════════════════════════════════════════════════════════════════
# BLOCO 5 — Outputs gerados (opcional, --outputs)
# ════════════════════════════════════════════════════════════════════
if '--outputs' in sys.argv or '--full' in sys.argv:
    print('\n── Outputs do pipeline ─────────────────────────────────────')
    DIR_DB = Path('ptd_corpus/03_database')

    expected = {
        'ptd_corpus_raw.csv':       (10_000, 'corpus de entregas'),
        'ptd_pivot_eixos.csv':      (500,    'pivot sigla × eixo'),
        'ptd_datas_assinatura.csv': (200,    'datas de assinatura'),
        'proveniencia.json':        (100,    'proveniência'),
        'pipeline_manifest.json':   (500,    'manifesto SHA-256'),
    }
    for fname, (min_bytes, desc) in expected.items():
        p = DIR_DB / fname
        if not p.exists():
            check(f'{fname} ({desc})', False, 'Arquivo não encontrado')
        elif p.stat().st_size < min_bytes:
            check(f'{fname} ({desc})', False,
                  f'Muito pequeno ({p.stat().st_size} bytes < {min_bytes})')
        else:
            kb = p.stat().st_size // 1024
            check(f'{fname}  [{kb} KB]', True)

    # Consistência pivot × corpus
    corpus_p = DIR_DB / 'ptd_corpus_raw.csv'
    pivot_p  = DIR_DB / 'ptd_pivot_eixos.csv'
    if corpus_p.exists() and pivot_p.exists():
        try:
            import pandas as pd
            corpus = pd.read_csv(corpus_p, usecols=['sigla'])
            pivot  = pd.read_csv(pivot_p,  usecols=['sigla'])
            c_sig  = set(corpus['sigla'].unique())
            p_sig  = set(pivot['sigla'].unique())
            only_corpus = c_sig - p_sig
            check(f'Consistência siglas corpus ↔ pivot  '
                  f'({len(c_sig)} siglas)',
                  len(only_corpus) == 0,
                  f'{len(only_corpus)} siglas no corpus sem pivot: '
                  f'{sorted(only_corpus)[:5]}',
                  warn=len(only_corpus) > 0)
        except Exception as e:
            check('Consistência corpus ↔ pivot', False, str(e))

    # Manifesto integridade
    manifest_p = DIR_DB / 'pipeline_manifest.json'
    if manifest_p.exists():
        try:
            m = json.loads(manifest_p.read_text())
            n_sha = len(m.get('pdfs_sha256', {}))
            check(f'Manifesto  [{n_sha} PDFs com SHA-256]',
                  n_sha > 0, 'Nenhum PDF registrado')
        except Exception as e:
            check('Manifesto JSON', False, str(e))

# ════════════════════════════════════════════════════════════════════
# RESUMO
# ════════════════════════════════════════════════════════════════════
total = checks_pass + checks_warn + checks_fail
print(f'\n{"─"*55}')
print(f'  {OK} {checks_pass}/{total} OK   '
      f'{WARN} {checks_warn} avisos   '
      f'{FAIL} {checks_fail} falhas')
if checks_fail == 0 and checks_warn == 0:
    print('  🚀 Ambiente pronto para execução do pipeline.')
elif checks_fail == 0:
    print('  ⚡ Ambiente funcional — avisos não impedem execução.')
else:
    print('  ⛔ Corrija as falhas antes de rodar o pipeline.')
print(f'{"─"*55}\n')

sys.exit(0 if checks_fail == 0 else 1)
