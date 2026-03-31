#!/usr/bin/env python3
"""
PTD-BR — Test Mode (3 PDFs representativos)
IPEA / COGIT / DIEST

Roda o pipeline completo em 3 PDFs de teste para validar
ambiente e lógica antes da execução completa (2-6h).

Uso:
    python ptd_test_pipeline.py              # baixa PDFs de teste
    python ptd_test_pipeline.py --local      # usa PDFs já em 01_raw_pdfs/
    python ptd_test_pipeline.py --verbose    # mostra extração linha a linha

PASS = pipeline funcionando corretamente
WARN = funcionando com fallback (ex: sem Docling → PyMuPDF)
FAIL = erro que impede execução completa
"""
import sys, time, json, re, hashlib, warnings
from pathlib import Path

warnings.filterwarnings('ignore')

DIR_TEST = Path('ptd_test_mode')
DIR_TEST.mkdir(exist_ok=True)

OK   = '\033[92m PASS\033[0m'
WARN = '\033[93m WARN\033[0m'
FAIL = '\033[91m FAIL\033[0m'
SEP  = '─' * 55

results = []

def resultado(etapa, status, msg='', detalhe=''):
    icon = {'PASS': OK, 'WARN': WARN, 'FAIL': FAIL}[status]
    print(f'{icon}  {etapa}')
    if msg:
        print(f'       {msg}')
    if detalhe and ('--verbose' in sys.argv or status == 'FAIL'):
        print(f'       → {detalhe}')
    results.append((etapa, status, msg))

# ════════════════════════════════════════════════════════════════════
# PDFs de teste: 3 representativos (pequenos, públicos, acessíveis)
# 1. CGU  — PDF normal, bem estruturado
# 2. ANPD — PDF com tabelas simples
# 3. ITI  — PDF menor, boa cobertura de texto
# ════════════════════════════════════════════════════════════════════
PORTAL = ('https://www.gov.br/governodigital/pt-br/'
          'estrategias-e-governanca-digital/'
          'planos-de-transformacao-digital/ptds-vigentes/')

TEST_PDFS = [
    {
        'sigla': 'CGU',
        'filename': 'cgu_ptd_anexo_de_entregas_pactuadas_assinado_assinado_assinadocopia_tarjada.pdf',
        'tipo': 'entregas',
        'expect_min_rows': 5,
    },
    {
        'sigla': 'ANPD',
        'filename': 'anpd_ptd_2025_2027_anexo_de_entregas_assinado_assinado_assinadocopia_tarjada.pdf',
        'tipo': 'entregas',
        'expect_min_rows': 3,
    },
    {
        'sigla': 'ITI',
        'filename': 'iti_anexo_de_entregas_assinado.pdf',
        'tipo': 'entregas',
        'expect_min_rows': 2,
    },
]

# ════════════════════════════════════════════════════════════════════
# ETAPA T1 — Download dos PDFs de teste
# ════════════════════════════════════════════════════════════════════
print(f'\n{SEP}')
print(f'  PTD-BR TEST MODE — {len(TEST_PDFS)} PDFs')
print(f'{SEP}')
print('\n[T1] Download dos PDFs de teste')

import requests

HEADERS = {'User-Agent': 'IPEA-DIEST-Research/3.0-test'}
TIMEOUT = 30
pdfs_ok = []

for spec in TEST_PDFS:
    dest = DIR_TEST / spec['filename']

    # Reusar PDF já baixado (em test_mode ou em raw_pdfs)
    raw_copy = Path('ptd_corpus/01_raw_pdfs') / spec['filename']
    if '--local' in sys.argv and raw_copy.exists():
        import shutil
        shutil.copy2(raw_copy, dest)

    if dest.exists() and dest.stat().st_size > 1000:
        print(f'  📦 {spec["sigla"]:8s} (cache)')
        pdfs_ok.append(spec)
        continue

    url = PORTAL + spec['filename']
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        if r.content[:4] != b'%PDF':
            resultado(f'Download {spec["sigla"]}', 'FAIL',
                      f'Resposta não é PDF (HTTP {r.status_code})')
            continue
        dest.write_bytes(r.content)
        kb = len(r.content) // 1024
        print(f'  ✓  {spec["sigla"]:8s} ({kb} KB)')
        pdfs_ok.append(spec)
    except Exception as e:
        resultado(f'Download {spec["sigla"]}', 'WARN',
                  f'Não foi possível baixar: {e}',
                  'Rode com --local se PDFs já estão em 01_raw_pdfs/')

if not pdfs_ok:
    resultado('Download', 'FAIL', 'Nenhum PDF disponível para teste')
    sys.exit(1)

resultado(f'Download ({len(pdfs_ok)}/{len(TEST_PDFS)} PDFs)',
          'PASS' if len(pdfs_ok) == len(TEST_PDFS) else 'WARN')

# ════════════════════════════════════════════════════════════════════
# ETAPA T2 — Sanity checks
# ════════════════════════════════════════════════════════════════════
print(f'\n[T2] Sanity checks')
import fitz

for spec in pdfs_ok:
    path = DIR_TEST / spec['filename']
    try:
        doc = fitz.open(str(path))
        npag = doc.page_count
        txt  = ' '.join(p.get_text() for p in doc)
        doc.close()
        nwords = len(txt.split())
        is_img = nwords < 50
        status = 'WARN' if is_img else 'PASS'
        msg    = f'{npag} pág · {nwords} palavras'
        if is_img:
            msg += '  ← PDF imagem, OCR necessário'
        resultado(f'Sanity {spec["sigla"]:8s} {msg}', status)
        spec['is_img']  = is_img
        spec['n_pages'] = npag
    except Exception as e:
        resultado(f'Sanity {spec["sigla"]}', 'FAIL', str(e))
        spec['is_img'] = False

# ════════════════════════════════════════════════════════════════════
# ETAPA T3 — Extração (Docling ou PyMuPDF)
# ════════════════════════════════════════════════════════════════════
print(f'\n[T3] Extração de tabelas')

EIXOS = {1:'Centrado no Cidadão', 2:'Integrado', 3:'Inteligente',
         4:'Confiável', 5:'Transparente', 6:'Eficiente'}
_EIXO_PATS = [
    (1, re.compile(r'cidad[ãa]o|inclusiv|servi[cç]os digitais', re.I)),
    (2, re.compile(r'integrad|colaborat|interoperab', re.I)),
    (3, re.compile(r'inteligent|inovad|govern.*dados', re.I)),
    (4, re.compile(r'confi[aá]vel|segur|privacidade|ppsi', re.I)),
    (5, re.compile(r'transparent|aberto|dados abertos', re.I)),
    (6, re.compile(r'eficient|sustent', re.I)),
]

def detectar_eixo(texto):
    m = re.search(r'eixo\s*([1-6])\b', texto, re.I)
    if m: return int(m.group(1))
    for num, pat in _EIXO_PATS:
        if pat.search(texto): return num
    return None

try:
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.pipeline_options import (
        PdfPipelineOptions, TableStructureOptions, TableFormerMode)
    _docling = True
except ImportError:
    _docling = False

import pandas as pd

all_rows = []

for spec in pdfs_ok:
    path   = DIR_TEST / spec['filename']
    sha256 = hashlib.sha256(path.read_bytes()).hexdigest()[:12]
    t0     = time.time()
    rows   = []
    extrator = None

    try:
        if _docling:
            opts = PdfPipelineOptions(
                do_table_structure=True,
                table_structure_options=TableStructureOptions(mode=TableFormerMode.ACCURATE),
                do_ocr=spec.get('is_img', False),
            )
            conv   = DocumentConverter(format_options={'pdf': PdfFormatOption(pipeline_options=opts)})
            result = conv.convert(str(path))
            eixo_atual = None
            last_page  = -1
            for tbl in result.document.tables:
                df  = tbl.export_to_dataframe(doc=result.document)
                pag = tbl.prov[0].page_no if tbl.prov else 0
                if pag != last_page:          # reset por página (fix crítico)
                    eixo_atual = None
                    last_page  = pag
                if len(df.columns) < 2 or len(df) < 2:
                    continue
                for _, row in df.iterrows():
                    cells = [str(v).strip() for v in row.values]
                    full  = ' | '.join(c for c in cells if c and c.lower() != 'nan')
                    if len(full) < 10:
                        continue
                    e = detectar_eixo(full)
                    if e: eixo_atual = e
                    if eixo_atual:
                        rows.append({'sigla': spec['sigla'], 'eixo': eixo_atual,
                                     'texto': full[:200], 'sha256': sha256})
            extrator = 'docling'
        else:
            raise ImportError('docling não disponível')

    except Exception:
        # Fallback PyMuPDF
        extrator = 'pymupdf'
        try:
            doc = fitz.open(str(path))
            for npag, pag in enumerate(doc, 1):
                eixo_atual = None               # reset por página
                try:
                    for tbl in pag.find_tables().tables:
                        df = tbl.to_pandas()
                        for _, row in df.iterrows():
                            txt = ' '.join(str(v) for v in row.values if v)
                            e   = detectar_eixo(txt)
                            if e: eixo_atual = e
                            if eixo_atual and len(txt) > 10:
                                rows.append({'sigla': spec['sigla'],
                                             'eixo': eixo_atual,
                                             'texto': txt[:200],
                                             'sha256': sha256})
                except AttributeError:
                    pass
            doc.close()
        except Exception as e2:
            resultado(f'Extração {spec["sigla"]}', 'FAIL', str(e2))
            continue

    elapsed = time.time() - t0
    n = len(rows)
    min_exp = spec['expect_min_rows']

    if n >= min_exp:
        status = 'PASS'
        msg = f'{n} registros | {extrator} | {elapsed:.1f}s'
    elif n > 0:
        status = 'WARN'
        msg = f'{n} registros (esperado ≥{min_exp}) | {extrator}'
    else:
        status = 'FAIL'
        msg = f'0 registros extraídos | {extrator}'

    resultado(f'Extração {spec["sigla"]:8s} {msg}', status)
    all_rows.extend(rows)

# ════════════════════════════════════════════════════════════════════
# ETAPA T4 — Verificação do corpus de teste
# ════════════════════════════════════════════════════════════════════
print(f'\n[T4] Verificação do corpus de teste')

df_test = pd.DataFrame(all_rows)

if df_test.empty:
    resultado('Corpus de teste', 'FAIL', 'Nenhum registro extraído')
else:
    n_eixos = df_test['eixo'].nunique()
    n_siglas = df_test['sigla'].nunique()
    resultado(
        f'Corpus  {len(df_test)} registros | '
        f'{n_siglas} órgãos | {n_eixos} eixos distintos',
        'PASS' if n_eixos >= 2 else 'WARN',
        '' if n_eixos >= 2 else 'Poucos eixos detectados — revisar PDFs de teste'
    )

    out = DIR_TEST / 'test_corpus.csv'
    df_test.to_csv(out, index=False)
    print(f'       Corpus de teste salvo em: {out}')

    if '--verbose' in sys.argv:
        print('\n  Amostra (5 primeiras linhas):')
        for _, r in df_test.head(5).iterrows():
            print(f'    E{r["eixo"]} | {r["sigla"]} | {r["texto"][:80]}…')

# ════════════════════════════════════════════════════════════════════
# RESUMO FINAL
# ════════════════════════════════════════════════════════════════════
print(f'\n{SEP}')
n_pass = sum(1 for _, s, _ in results if s == 'PASS')
n_warn = sum(1 for _, s, _ in results if s == 'WARN')
n_fail = sum(1 for _, s, _ in results if s == 'FAIL')
total  = len(results)

print(f'  PASS {n_pass}/{total}   WARN {n_warn}   FAIL {n_fail}')

if n_fail == 0 and n_warn == 0:
    print('  🚀 Pipeline pronto — pode rodar ptd_pipeline_v30.py')
elif n_fail == 0:
    print('  ⚡ Pipeline funcional com avisos — verifique os WARNs')
    print('     PDFs imagem: instale tesseract-ocr-por para OCR')
    print('     Sem Docling:  pip install docling  para melhor extração')
else:
    print('  ⛔ Corrija as falhas antes de rodar o pipeline completo')
print(f'{SEP}\n')

sys.exit(0 if n_fail == 0 else 1)
