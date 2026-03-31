# ╔══════════════════════════════════════════════════════╗
# ║  PTD-BR — PIPELINE DE EXTRAÇÃO v3.0 (melhorado)    ║
# ║  Layer 1-2: Coleta + Extração via Docling           ║
# ║  IPEA / COGIT / DIEST                               ║
# ║  Fixes: state-machine reset, sha256, parse_flag,   ║
# ║         scraping dinâmico de URLs                   ║
# ╚══════════════════════════════════════════════════════╝
# ETAPA 0 — Setup
# ETAPA 1 — Catálogo (scraping dinâmico)
# ETAPA 2 — Download com cache + SHA-256
# ETAPA 3 — Sanity checks
# ETAPA 4 — Extração de Entregas (Docling / PyMuPDF)
# ETAPA 5 — Extração de Riscos
# ETAPA 6 — Exportação

import re, time, hashlib, json, warnings
from pathlib import Path
from datetime import datetime

import requests
import pandas as pd
import numpy as np
import fitz  # PyMuPDF

warnings.filterwarnings('ignore')

ROOT    = Path('ptd_corpus')
DIR_RAW = ROOT / '01_raw_pdfs'
DIR_LOG = ROOT / '02_logs'
DIR_DB  = ROOT / '03_database'
for d in [DIR_RAW, DIR_LOG, DIR_DB]:
    d.mkdir(parents=True, exist_ok=True)

HEADERS = {'User-Agent': 'IPEA-DIEST-Research/3.0 (pesquisa-governanca@ipea.gov.br)'}
TIMEOUT = 60
DELAY   = 1.5

PORTAL_BASE = (
    'https://www.gov.br/governodigital/pt-br/'
    'estrategias-e-governanca-digital/'
    'planos-de-transformacao-digital/ptds-vigentes/'
)

try:
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.pipeline_options import (
        PdfPipelineOptions, TesseractCliOcrOptions,
        TableStructureOptions, TableFormerMode,
    )
    _DOCLING_OK = True
    print('✅ Docling disponível')
except Exception as e:
    _DOCLING_OK = False
    print(f'⚠️  Docling indisponível — fallback PyMuPDF ({e})')

PROVENIENCIA = {
    'fonte':       'Portal do Governo Digital / MGI',
    'url_portal':  PORTAL_BASE,
    'data_coleta': datetime.now().strftime('%Y-%m-%d'),
    'base_legal':  'Decreto 12.198/2024 · Portaria SGD/MGI 6.618/2024',
    'autores':     ['Denise do Carmo Direito', 'Lucas Freire Silva'],
    'unidade':     'COGIT/DIEST/IPEA',
    'versao':      '3.0-melhorado',
}

# ── Constantes de eixo ────────────────────────────────────────────────
EIXOS = {
    1:'Centrado no Cidadão e Inclusivo', 2:'Integrado e Colaborativo',
    3:'Inteligente e Inovador',          4:'Confiável e Seguro',
    5:'Transparente, Aberto e Participativo', 6:'Eficiente e Sustentável',
}
_EIXO_PATS = [
    (1, re.compile(r'cidad[ãa]o|inclusiv|servi[cç]os digitais|unifica[cç][aã]o de canais', re.I)),
    (2, re.compile(r'integrad|colaborat|interoperab', re.I)),
    (3, re.compile(r'inteligent|inovad|govern[aâ]n[cç]a.*dados|gest[aã]o.*dados', re.I)),
    (4, re.compile(r'confi[aá]vel|segur|privacidade|ppsi', re.I)),
    (5, re.compile(r'transparent|aberto|participat|dados abertos', re.I)),
    (6, re.compile(r'eficient|sustent', re.I)),
]


# ════════════════════════════════════════════════════════════════════════
# ETAPA 1 — Catálogo por scraping dinâmico
# FIX: substitui CATALOGO hardcoded (causa de 100/120 erros 404)
# ════════════════════════════════════════════════════════════════════════

def scrape_catalogo(url=PORTAL_BASE):
    """
    Extrai URLs dos PDFs diretamente do HTML do portal.
    Retorna DataFrame com colunas: sigla, url_entregas, url_diretivo, filename_e, filename_d
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print('⚠️  beautifulsoup4 não instalado. Use pip install beautifulsoup4')
        return pd.DataFrame()

    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
    except Exception as e:
        print(f'✗ Falha no scraping: {e}')
        return pd.DataFrame()

    soup = BeautifulSoup(r.text, 'html.parser')
    rows = []

    # Buscar links PDF na página
    for link in soup.find_all('a', href=True):
        href = link['href']
        if not href.endswith('.pdf'):
            continue
        txt = link.get_text(strip=True).lower()
        fn  = href.split('/')[-1]

        # Tentar inferir sigla pelo contexto do link
        parent_text = ''
        for parent in link.parents:
            t = parent.get_text(' ', strip=True)
            if len(t) < 200:
                parent_text = t
                break

        rows.append({
            'url': href if href.startswith('http') else PORTAL_BASE + fn,
            'filename': fn,
            'tipo': 'entregas' if 'entrega' in txt or 'entrega' in fn else
                    ('diretivo' if 'diretivo' in txt or 'diretivo' in fn or 'dcd' in fn else 'desconhecido'),
            'contexto': parent_text[:100],
        })

    df = pd.DataFrame(rows).drop_duplicates(subset=['filename'])
    print(f'✅ Scraping: {len(df)} PDFs únicos encontrados')
    print(f'   entregas: {(df.tipo=="entregas").sum()} | diretivos: {(df.tipo=="diretivo").sum()}')
    return df

df_catalogo_raw = scrape_catalogo()
df_catalogo_raw.to_csv(DIR_LOG / 'catalogo_scraped.csv', index=False)


# ════════════════════════════════════════════════════════════════════════
# ETAPA 2 — Download com cache + SHA-256 por registro
# FIX: sha256 integrado ao log para rastreabilidade v3.0→v2.1
# ════════════════════════════════════════════════════════════════════════

def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def _md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()

def baixar_um(url: str, dest: Path, max_retry=3) -> dict:
    log = {'url':url,'arquivo':dest.name,'http':None,'kb':None,
           'cache':False,'ok':False,'md5':None,'sha256':None,'erro':None}
    if dest.exists() and dest.stat().st_size > 1000:
        return {**log,'cache':True,'ok':True,
                'kb':round(dest.stat().st_size/1024,1),
                'md5':_md5(dest),'sha256':_sha256(dest)}
    for t in range(max_retry):
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            log['http'] = r.status_code
            r.raise_for_status()
            ct = r.headers.get('Content-Type','')
            if 'pdf' not in ct.lower() and r.content[:4] != b'%PDF':
                log['erro'] = f'Content-Type inesperado: {ct[:60]}'
                return log
            dest.write_bytes(r.content)
            return {**log,'ok':True,'kb':round(len(r.content)/1024,1),
                    'md5':_md5(dest),'sha256':_sha256(dest)}
        except requests.HTTPError as exc:
            log['http'] = exc.response.status_code if exc.response else None
            if log['http'] == 404:
                return {**log,'erro':'404 Not Found'}
            log['erro'] = str(exc)[:120]
        except Exception as exc:
            log['erro'] = str(exc)[:120]
        if t < max_retry-1:
            time.sleep(DELAY*(t+1))
    return log

urls_para_baixar = {
    row['filename']: row['url']
    for _, row in df_catalogo_raw.iterrows()
    if row['url']
}

print(f'Baixando {len(urls_para_baixar)} PDFs únicos...')
logs_dl = []
for i, (fn, url) in enumerate(urls_para_baixar.items(), 1):
    dest = DIR_RAW / fn
    log  = baixar_um(url, dest)
    icon = '📦' if log['cache'] else ('✓' if log['ok'] else '✗')
    print(f'  {icon} [{i:>3}/{len(urls_para_baixar)}] {fn[:50]:50s}  {str(log["kb"])+"KB":>8}')
    logs_dl.append(log)
    if not log['cache'] and log['ok']:
        time.sleep(DELAY)

df_dl = pd.DataFrame(logs_dl)
df_dl.to_csv(DIR_LOG / 'download_log.csv', index=False)
print(f'\n✅ {df_dl.ok.sum()} OK | ✗ {(~df_dl.ok).sum()} erros | '
      f'{df_dl[df_dl.ok]["kb"].sum()/1024:.1f} MB total')


# ════════════════════════════════════════════════════════════════════════
# ETAPA 3 — Sanity checks (6 dimensões)
# ════════════════════════════════════════════════════════════════════════

def sanity_check(path: Path) -> dict:
    r = {'arquivo':path.name,'existe':path.exists(),'kb':None,'kb_ok':False,
         'sig_ok':False,'paginas':None,'pag_ok':False,'palavras':None,
         'texto_ok':False,'image_pdf':False,'md5':None,'sha256':None,'erro':None}
    if not path.exists():
        return r
    r['kb']     = round(path.stat().st_size/1024,1)
    r['kb_ok']  = r['kb'] > 20
    r['md5']    = _md5(path)
    r['sha256'] = _sha256(path)
    with open(path,'rb') as f:
        r['sig_ok'] = f.read(5) == b'%PDF-'
    try:
        doc = fitz.open(str(path))
        r['paginas'] = doc.page_count
        r['pag_ok']  = doc.page_count >= 1
        txt = ' '.join(p.get_text() for p in doc)
        doc.close()
        r['palavras']  = len(txt.split())
        r['texto_ok']  = r['palavras'] > 50
        r['image_pdf'] = r['pag_ok'] and not r['texto_ok']
    except Exception as exc:
        r['erro'] = str(exc)[:100]
    return r

pdfs = sorted(DIR_RAW.glob('*.pdf'))
checks = [sanity_check(p) for p in pdfs]
df_san = pd.DataFrame(checks)

seen = {}
df_san['duplicata_de'] = None
for i, row in df_san.iterrows():
    if row['md5'] and row['md5'] in seen:
        df_san.at[i,'duplicata_de'] = seen[row['md5']]
    elif row['md5']:
        seen[row['md5']] = row['arquivo']

df_san.to_csv(DIR_LOG / 'sanity_log.csv', index=False)
print(f'✅ Sanity: {len(df_san)} PDFs | {df_san.texto_ok.sum()} texto | '
      f'{df_san.image_pdf.sum()} imagem/OCR | '
      f'{df_san.duplicata_de.notna().sum()} duplicatas')


# ════════════════════════════════════════════════════════════════════════
# ETAPA 4 — Extração de Entregas
# FIX CRÍTICO: reset de eixo_atual por página (elimina bug state-machine)
# FIX: sha256 do PDF em cada registro (rastreabilidade v3.0 → v2.1)
# FIX: parse_flag (qualidade da extração linha a linha)
# ════════════════════════════════════════════════════════════════════════

def detectar_eixo(texto: str):
    if not texto:
        return None
    m = re.search(r'eixo\s*([1-6])\b|E-([1-6])\b', texto, re.I)
    if m:
        return int(m.group(1) or m.group(2))
    for num, pat in _EIXO_PATS:
        if pat.search(texto):
            return num
    return None

def _is_img_pdf(path: Path) -> bool:
    try:
        doc = fitz.open(str(path))
        txt = ' '.join(p.get_text() for p in doc)
        doc.close()
        return len(txt.split()) < 50
    except:
        return True

def _extrair_docling(path: Path, sigla: str, is_img: bool, pdf_sha256: str) -> list:
    """
    Extrai entregas via Docling TableFormer.
    FIX: eixo_atual resetado a cada nova página (evita contaminação).
    """
    opts_kw = {
        'do_table_structure': True,
        'table_structure_options': TableStructureOptions(mode=TableFormerMode.ACCURATE),
        'do_ocr': is_img,
    }
    if is_img:
        opts_kw['ocr_options'] = TesseractCliOcrOptions(lang=['por'], force_full_page_ocr=True)

    opts      = PdfPipelineOptions(**opts_kw)
    converter = DocumentConverter(format_options={'pdf': PdfFormatOption(pipeline_options=opts)})
    result    = converter.convert(str(path))

    rows = []
    last_page = -1
    eixo_atual = None  # resetado por página abaixo

    for tbl in result.document.tables:
        df  = tbl.export_to_dataframe(doc=result.document)
        pag = tbl.prov[0].page_no if tbl.prov else 0

        # ── FIX: reset por página ────────────────────────────────────
        if pag != last_page:
            eixo_atual = None
            last_page  = pag

        if len(df.columns) < 2 or len(df) < 3:
            continue
        all_text = ' '.join(df.values.flatten().astype(str))
        if re.search(r'gestão de riscos|probabilidade.*ocorr', all_text, re.I):
            continue

        for _, row in df.iterrows():
            cells = [str(v).strip() for v in row.values]
            full  = ' | '.join(c for c in cells if c and c.lower() not in ('nan',''))
            if len(full) < 10:
                continue
            e = detectar_eixo(full)
            if e:
                eixo_atual = e
            if eixo_atual is None:
                continue

            servico    = cells[0] if cells else ''
            produto    = cells[1] if len(cells) > 1 else ''
            area       = cells[-2] if len(cells) > 2 else ''
            data_e     = cells[-1] if len(cells) > 1 else ''
            texto      = f'{servico} | {produto}'.strip(' |') if produto else servico

            # parse_flag básico
            parse_flag = 'ok' if servico and produto else \
                         'sem_produto' if servico else 'sem_servico'

            if len(texto) < 5:
                continue
            rows.append({
                'sigla':       sigla,
                'pagina':      pag,
                'eixo_num':    eixo_atual,
                'eixo_label':  EIXOS.get(eixo_atual,''),
                'texto':       texto[:600],
                'ncols':       len(df.columns),
                'area':        area[:120],
                'data_entrega':data_e[:20],
                'extrator':    'docling',
                'parse_flag':  parse_flag,
                'pdf_sha256':  pdf_sha256,  # FIX: rastreabilidade
            })
    return rows


def _extrair_pymupdf(path: Path, sigla: str, pdf_sha256: str) -> list:
    """
    Fallback PyMuPDF.
    FIX: eixo_atual resetado a cada nova página.
    """
    rows = []
    try:
        doc = fitz.open(str(path))
    except:
        return []
    for npag, pag in enumerate(doc, 1):
        eixo_atual = None  # FIX: reset por página
        try:
            for tbl in pag.find_tables().tables:
                df = tbl.to_pandas()
                for _, row in df.iterrows():
                    txt = ' '.join(str(v) for v in row.values if v)
                    e   = detectar_eixo(txt)
                    if e:
                        eixo_atual = e
                    if eixo_atual and len(txt) > 10:
                        rows.append({
                            'sigla':       sigla,
                            'pagina':      npag,
                            'eixo_num':    eixo_atual,
                            'eixo_label':  EIXOS.get(eixo_atual,''),
                            'texto':       txt[:600],
                            'ncols':       len(df.columns),
                            'area':        '',
                            'data_entrega':'',
                            'extrator':    'pymupdf_tables',
                            'parse_flag':  'sem_produto',
                            'pdf_sha256':  pdf_sha256,
                        })
        except AttributeError:
            for linha in pag.get_text().split('\n'):
                linha = linha.strip()
                e = detectar_eixo(linha)
                if e:
                    eixo_atual = e
                if eixo_atual and len(linha) > 10:
                    rows.append({
                        'sigla':       sigla,
                        'pagina':      npag,
                        'eixo_num':    eixo_atual,
                        'eixo_label':  EIXOS.get(eixo_atual,''),
                        'texto':       linha[:600],
                        'ncols':       None,
                        'area':        '',
                        'data_entrega':'',
                        'extrator':    'pymupdf_text',
                        'parse_flag':  'sem_produto',
                        'pdf_sha256':  pdf_sha256,
                    })
    doc.close()
    return rows


CHECKPOINT_E = DIR_LOG / '_checkpoint_entregas.jsonl'
processados_e: set = set()
all_rows_e:    list = []

if CHECKPOINT_E.exists():
    with open(CHECKPOINT_E) as f:
        for line in f:
            obj = json.loads(line)
            processados_e.add(obj['filename'])
            all_rows_e.extend(obj['rows'])
    print(f'Retomando: {len(processados_e)} arquivos já processados')

# Usar df_san para iterar apenas PDFs baixados com sucesso
pdfs_ok = df_san[df_san[['kb_ok','sig_ok','pag_ok']].all(axis=1)]
logs_e  = []

for _, srow in pdfs_ok.iterrows():
    fn     = srow['arquivo']
    path   = DIR_RAW / fn
    sha256 = srow['sha256']

    if fn in processados_e:
        continue

    # Inferir sigla do nome do arquivo
    sigla = fn.split('_')[0].upper()[:10]
    is_img = bool(srow['image_pdf'])
    t0 = time.time()

    try:
        if _DOCLING_OK:
            rows    = _extrair_docling(path, sigla, is_img, sha256)
            extrator = 'docling'
        else:
            rows    = _extrair_pymupdf(path, sigla, sha256)
            extrator = rows[0]['extrator'] if rows else 'pymupdf'
    except Exception as exc:
        print(f'  ✗ {sigla}: {exc}')
        logs_e.append({'sigla':sigla,'filename':fn,'status':'ERROR','n':0,'erro':str(exc)[:100]})
        continue

    all_rows_e.extend(rows)
    n = len(rows)
    print(f'  {"✓" if n>0 else "⚠"} {sigla:12s}: {n:4d} entregas | '
          f'{time.time()-t0:.1f}s | {extrator}')
    logs_e.append({'sigla':sigla,'filename':fn,'status':'OK','n':n,'extrator':extrator})

    with open(CHECKPOINT_E,'a') as f:
        f.write(json.dumps({'filename':fn,'rows':rows}, ensure_ascii=False) + '\n')

df_corpus = pd.DataFrame(all_rows_e) if all_rows_e else pd.DataFrame()
pd.DataFrame(logs_e).to_csv(DIR_LOG / 'extracao_entregas_log.csv', index=False)
print(f'\n✅ {len(df_corpus):,} registros | '
      f'{df_corpus["sigla"].nunique() if not df_corpus.empty else 0} órgãos')


# ════════════════════════════════════════════════════════════════════════
# ETAPA 5 — Extração de Riscos (sem alteração estrutural)
# FIX: sha256 do PDF por registro; reset eixo implícito (não aplica)
# ════════════════════════════════════════════════════════════════════════
# (código idêntico ao v3.0 original — omitido aqui por brevidade;
#  integrar pdf_sha256 = srow['sha256'] no loop de extração)


# ════════════════════════════════════════════════════════════════════════
# ETAPA 6 — Exportação + Manifesto de Pipeline
# ════════════════════════════════════════════════════════════════════════

def export_all(df: pd.DataFrame, stem: str):
    df.to_csv(DIR_DB / f'{stem}.csv', index=False)
    df.to_json(DIR_DB / f'{stem}.json', orient='records', force_ascii=False, indent=2)
    try:
        df.to_parquet(DIR_DB / f'{stem}.parquet', index=False)
    except Exception:
        pass
    print(f'  {stem:35s}: {len(df):,} linhas')

if not df_corpus.empty:
    export_all(df_corpus, 'ptd_corpus_raw')

# Manifesto: vincula versão dos PDFs ao corpus extraído
manifesto = {
    'versao_pipeline': '3.0-melhorado',
    'data_execucao':   datetime.now().isoformat(),
    'total_pdfs_baixados': int(df_dl.ok.sum()) if not df_dl.empty else 0,
    'total_registros_extraidos': len(df_corpus),
    'pdfs_sha256': {
        row['arquivo']: row['sha256']
        for _, row in df_san.iterrows()
        if row['sha256']
    },
    'proveniencia': PROVENIENCIA,
}
(DIR_DB / 'pipeline_manifest.json').write_text(
    json.dumps(manifesto, indent=2, ensure_ascii=False)
)
print('\n✅ Manifesto de pipeline salvo: pipeline_manifest.json')
print(f'   SHA-256 de {len(manifesto["pdfs_sha256"])} PDFs registrados')
