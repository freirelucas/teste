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

import re, time, hashlib, json, warnings, logging, argparse as _ap, threading, os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as _FuturesTimeout
from pathlib import Path
from datetime import datetime
from typing import Optional

from ptd_constants import EIXOS, _EIXO_PATS, detectar_eixo as _detectar_eixo_const, PORTAL_BASE

import requests
import pandas as pd
import numpy as np
import fitz  # PyMuPDF

warnings.filterwarnings('ignore')

# ── Argumentos de linha de comando ───────────────────────────────────
_parser = _ap.ArgumentParser(description='PTD-BR pipeline v3.0')
_parser.add_argument('--force-download', action='store_true', default=False,
                     help='Limpa checkpoints e re-processa todos os PDFs')
_parser.add_argument('--max-pdfs', type=int, default=0,
                     help='Limitar a N PDFs no loop de extração (0 = sem limite)')
_parser.add_argument('--siglas', type=str, default='',
                     help='Siglas separadas por vírgula para modo debug (ex: AGU,FUNAI,MD)')
_parser.add_argument('--skip-download', action='store_true', default=False,
                     help='Pula scraping e download; usa PDFs já presentes em DIR_RAW '
                          '(Estágios 1-4: só re-extrai, não re-baixa)')
_args, _       = _parser.parse_known_args()  # parse_known_args: ignora args do pytest/outros
FORCE_DOWNLOAD = _args.force_download
MAX_PDFS       = _args.max_pdfs
SIGLAS_DEBUG   = {s.strip().upper() for s in _args.siglas.split(',') if s.strip()}
SKIP_DOWNLOAD  = _args.skip_download
PDF_TIMEOUT    = int(os.getenv('PTD_PDF_TIMEOUT', '3600'))  # 1h default, override via env

ROOT    = Path('ptd_corpus')
DIR_RAW = ROOT / '01_raw_pdfs'
DIR_LOG = ROOT / '02_logs'
DIR_DB  = ROOT / '03_database'
for d in [DIR_RAW, DIR_LOG, DIR_DB]:
    d.mkdir(parents=True, exist_ok=True)

# ── Logging centralizado ─────────────────────────────────────────────
_log_file = DIR_LOG / f'pipeline_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%H:%M:%S',
    handlers=[
        logging.FileHandler(_log_file, encoding='utf-8'),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger('ptd_pipeline')

HEADERS = {'User-Agent': 'IPEA-DIEST-Research/3.0 (pesquisa-governanca@ipea.gov.br)'}
TIMEOUT = 60
DELAY   = 1.5

# PORTAL_BASE importado de ptd_constants.py (fonte única)

try:
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.pipeline_options import (
        PdfPipelineOptions, TesseractCliOcrOptions,
        TableStructureOptions, TableFormerMode,
    )
    _DOCLING_OK = True
    logger.info('Docling disponível')
except Exception as e:
    _DOCLING_OK = False
    logger.warning(f'Docling indisponível — fallback PyMuPDF ({e})')

try:
    from ptd_ocr_fallback import extrair_ocr as _extrair_ocr_fallback
    _OCR_FALLBACK_OK = True
    logger.info('OCR fallback (pytesseract) disponível')
except Exception as _e:   # ImportError ou NameError (PIL ausente em anotações)
    _OCR_FALLBACK_OK = False
    logger.warning(f'OCR fallback indisponível ({type(_e).__name__}: {_e})')

PROVENIENCIA = {
    'fonte':       'Portal do Governo Digital / MGI',
    'url_portal':  PORTAL_BASE,
    'data_coleta': datetime.now().strftime('%Y-%m-%d'),
    'base_legal':  'Decreto 12.198/2024 · Portaria SGD/MGI 6.618/2024',
    'autores':     ['Denise do Carmo Direito', 'Lucas Freire Silva'],
    'unidade':     'COGIT/DIEST/IPEA',
    'versao':      '3.0-melhorado',
}

# ── Constantes de eixo — importadas de ptd_constants.py (fonte única) ────────
# EIXOS e _EIXO_PATS importados acima; reatribuídos para compatibilidade local
# (não duplicar — qualquer alteração vai para ptd_constants.py)


# ════════════════════════════════════════════════════════════════════════
# ETAPA 1 — Catálogo por scraping dinâmico
# FIX: substitui CATALOGO hardcoded (causa de 100/120 erros 404)
# ════════════════════════════════════════════════════════════════════════

def scrape_catalogo(url: str = PORTAL_BASE) -> 'pd.DataFrame':
    """
    Extrai URLs dos PDFs diretamente do HTML do portal.
    Retorna DataFrame com colunas: sigla, url_entregas, url_diretivo, filename_e, filename_d
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        logger.warning('beautifulsoup4 não instalado. Use pip install beautifulsoup4')
        return pd.DataFrame()

    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
    except Exception as e:
        logger.error(f'Falha no scraping: {e}')
        return pd.DataFrame()

    soup = BeautifulSoup(r.text, 'html.parser')
    rows = []

    # Buscar links PDF na página
    # O portal Plone adiciona sufixo /view — remover antes de processar
    for link in soup.find_all('a', href=True):
        href = link['href']
        # Normalizar URL: remover sufixo /view
        clean = href.rstrip('/').removesuffix('/view')
        if not clean.lower().endswith('.pdf'):
            continue
        txt = link.get_text(strip=True).lower()
        fn  = clean.split('/')[-1]
        # Excluir guias/orientações que não são PTDs de órgãos
        if re.search(r'guia\d*[-_]?\d*passos|template[-_]ptd|modelo[-_]ptd'
                     r'|abnt[-_]nbr', fn, re.I):
            logger.info(f'Ignorado (guia/template/norma): {fn}')
            continue
        # URL de download: usar href limpo; completar se relativo
        if clean.startswith('http'):
            download_url = clean
        else:
            download_url = 'https://www.gov.br' + clean

        # Tentar inferir sigla pelo contexto do link
        parent_text = ''
        for parent in link.parents:
            t = parent.get_text(' ', strip=True)
            if len(t) < 200:
                parent_text = t
                break

        rows.append({
            'url': download_url,
            'filename': fn,
            'tipo': 'entregas' if 'entrega' in txt or 'entrega' in fn else
                    ('diretivo' if 'diretivo' in txt or 'diretivo' in fn or 'dcd' in fn else 'desconhecido'),
            'contexto': parent_text[:100],
        })

    df = pd.DataFrame(rows).drop_duplicates(subset=['filename'])
    logger.info(f'Scraping: {len(df)} PDFs únicos | '
                f'entregas: {(df.tipo=="entregas").sum()} | diretivos: {(df.tipo=="diretivo").sum()}')
    return df

if SKIP_DOWNLOAD:
    # Reusar catálogo do run anterior (se existir) ou criar vazio
    _cat_prev = DIR_LOG / 'catalogo_scraped.csv'
    if _cat_prev.exists():
        df_catalogo_raw = pd.read_csv(_cat_prev)
        logger.info(f'--skip-download: reutilizando catálogo com {len(df_catalogo_raw)} entradas')
    else:
        df_catalogo_raw = pd.DataFrame(columns=['filename','url','tipo','sigla'])
        logger.info('--skip-download: sem catálogo anterior, usando PDFs em DIR_RAW diretamente')
else:
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

def baixar_um(url: str, dest: Path, max_retry: int = 3) -> dict:
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

if SKIP_DOWNLOAD:
    # Usar PDFs já presentes em DIR_RAW — iteração de qualidade sem re-download
    _pdfs_presentes = sorted(DIR_RAW.glob('*.pdf'))
    logs_dl = [{'url': '', 'arquivo': p.name, 'cache': True, 'ok': True,
                'kb': round(p.stat().st_size / 1024, 1)} for p in _pdfs_presentes]
    df_dl = pd.DataFrame(logs_dl)
    logger.info(f'--skip-download: {len(_pdfs_presentes)} PDFs em DIR_RAW (sem scraping/download)')
else:
    urls_para_baixar = {
        row['filename']: row['url']
        for _, row in df_catalogo_raw.iterrows()
        if row['url']
    }

    logger.info(f'Baixando {len(urls_para_baixar)} PDFs únicos...')
    logs_dl = []
    for i, (fn, url) in enumerate(urls_para_baixar.items(), 1):
        dest = DIR_RAW / fn
        log  = baixar_um(url, dest)
        icon = '📦' if log['cache'] else ('✓' if log['ok'] else '✗')
        lvl  = logging.INFO if log['ok'] else logging.WARNING
        logger.log(lvl, f'{icon} [{i:>3}/{len(urls_para_baixar)}] {fn[:50]:50s}  {str(log["kb"])+"KB":>8}')
        logs_dl.append(log)
        if not log['cache'] and log['ok']:
            time.sleep(DELAY)

    df_dl = pd.DataFrame(logs_dl) if logs_dl else pd.DataFrame(columns=['url','arquivo','cache','ok','kb'])
    df_dl.to_csv(DIR_LOG / 'download_log.csv', index=False)
    logger.info(f'{df_dl.ok.sum()} OK | {(~df_dl.ok).sum()} erros | '
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
if df_san.empty:
    logger.info('Sanity: 0 PDFs em DIR_RAW (download ainda não executado)')
else:
    logger.info(f'Sanity: {len(df_san)} PDFs | {df_san.texto_ok.sum()} texto | '
                f'{df_san.image_pdf.sum()} imagem/OCR | '
                f'{df_san.duplicata_de.notna().sum()} duplicatas')


# ════════════════════════════════════════════════════════════════════════
# ETAPA 4 — Extração de Entregas
# FIX CRÍTICO: reset de eixo_atual por página (elimina bug state-machine)
# FIX: sha256 do PDF em cada registro (rastreabilidade v3.0 → v2.1)
# FIX: parse_flag (qualidade da extração linha a linha)
# ════════════════════════════════════════════════════════════════════════

def detectar_eixo(texto: str) -> Optional[int]:
    """Wrapper para ptd_constants.detectar_eixo (fonte única de padrões)."""
    return _detectar_eixo_const(texto)

def _is_img_pdf(path: Path) -> bool:
    try:
        doc = fitz.open(str(path))
        txt = ' '.join(p.get_text() for p in doc)
        doc.close()
        return len(txt.split()) < 50
    except Exception:
        return True

# ── Column-aware extraction ────────────────────────────────────────────────────
# Padrões de palavras-chave para identificar colunas pelo header
# (mesmo padrão já usado em _parse_risk_df para tabelas de risco)
_COL_KEYS: dict[str, tuple] = {
    'servico': ('serviço', 'servi', 'nome do servi', 'descri', 'ação', 'acao',
                'atividade', 'meta', 'iniciativa', 'objeto'),
    'produto': ('produto', 'entrega', 'item'),
    'subeixo': ('subeixo', 'sub-eixo', 'diretriz'),
    'area':    ('área', 'area', 'setor', 'unidade'),
    'data':    ('data', 'prazo', 'previsão', 'previsao', 'dt_'),
}

def _col_map(df: pd.DataFrame) -> dict[str, Optional[int]]:
    """Mapeia nomes de colunas do DataFrame a campos semânticos.

    Retorna dict {field: col_index | None}.
    Se nenhum header reconhecível, retorna dict vazio (fallback posicional).
    """
    col_names = [str(c).lower().strip() for c in df.columns]
    result: dict[str, Optional[int]] = {}
    for field, keywords in _COL_KEYS.items():
        for idx, name in enumerate(col_names):
            if any(k in name for k in keywords):
                result[field] = idx
                break
    return result

def _get_cell(cells: list[str], cmap: dict, field: str, fallback_idx: Optional[int]) -> str:
    """Retorna célula por header (cmap) ou por índice posicional (fallback)."""
    idx = cmap.get(field, fallback_idx)
    if idx is None:
        return ''
    if idx < 0:
        idx = len(cells) + idx  # índice negativo → posição relativa ao fim
    if 0 <= idx < len(cells):
        return cells[idx]
    return ''

def _sigla_de_fn(fn: str) -> str:
    """Infere sigla do órgão a partir do nome do arquivo.
    - URL-decode ('%28' → '(', etc.)
    - Pula prefixo 'ptd_'  →  ptd_aneel_... → ANEEL
    - Corta sufixo após '-' →  midr-docdiretivo → MIDR
    - Extrai [A-Z0-9] inicial → MF(RFB) → MF
    - Padrão prefixo-SIGLA: anexo-de-entregas-mcom_ptd-... → MCOM
    """
    from urllib.parse import unquote as _uq
    # palavras genéricas que não são siglas de órgão
    _NON_SIGLA = frozenset({'PTD', 'ANEXO', 'DOC', 'PLANO', 'COPIA', 'TARJADA',
                             'PLANOS', 'DOCS', 'ARQUIVO', 'FILE', 'FORM', 'VERSAO'})
    parts = _uq(fn).split('_')
    # Padrão ptd_SIGLA_... (mais comum)
    if parts[0].lower() == 'ptd' and len(parts) > 1:
        raw   = parts[1]
        clean = re.sub(r'[-].*', '', raw).upper()
        m = re.match(r'^[A-Z0-9]+', clean)
        return (m.group(0) if m else clean)[:10]
    # Padrão prefixo-SIGLA_ptd-... (ex: anexo-de-entregas-mcom_ptd-25_27-...)
    # Varrer até 4 parts procurando candidato a sigla válido
    for part in parts[:4]:
        # cada part pode ter sub-partes separadas por '-'; testar de trás pra frente
        subparts = part.split('-')
        for sub in reversed(subparts):
            candidate = sub.upper()
            if re.match(r'^[A-Z]{2,12}$', candidate) and candidate not in _NON_SIGLA:
                return candidate[:10]
    # Fallback original
    raw   = parts[0]
    clean = re.sub(r'[-].*', '', raw).upper()
    m = re.match(r'^[A-Z0-9]+', clean)
    return (m.group(0) if m else clean)[:10]

# ── Estrutura CGREP: tipo_doc e passo_ptd ────────────────────────────────────
def _tipo_doc(fn: str) -> str:
    """Classifica o tipo de documento PTD pelo nome do arquivo."""
    f = fn.lower()
    if re.search(r'anexo.{0,15}entrega|entrega.{0,10}assinado', f): return 'anexo_entregas'
    if re.search(r'doc.{0,8}diretivo|docdiretivo',               f): return 'doc_diretivo'
    if re.search(r'plano.{0,15}transform|ptd.{0,5}\d{4}',        f): return 'plano_completo'
    return 'outro'

_TIPO_PASSO: dict[str, int] = {
    'anexo_entregas': 6, 'doc_diretivo': 6, 'plano_completo': 6, 'outro': 6,
}
_PASSO_LABEL: dict[int, str] = {
    6: 'Elaboração do Plano de Entregas',
    7: 'Identificação de Riscos',
}

# ── Watchdog: heartbeat para PDFs lentos ─────────────────────────────────────
def _watchdog(fn: str, stop: threading.Event,
              interval: int = 60, warn_after: int = 300) -> None:
    """Loga aviso a cada `interval` s depois de `warn_after` s de processamento."""
    t0 = time.time()
    while not stop.wait(interval):
        el = time.time() - t0
        if el >= warn_after:
            logger.warning(f'⟳ Processando {fn} há {el/60:.0f} min...')

# ── Caixa de resumo de fase ───────────────────────────────────────────────────
def _fase_box(titulo: str, n_total: int, n_ok: int, n_warn: int,
              dur_s: float, extra: str = '') -> None:
    w = 62
    linha_proc = f'  Processados: {n_total:<4}  |  \u2713 {n_ok}  \u26a0 {n_warn}'
    linha_dur  = f'  Duração: {dur_s/60:.1f} min'
    logger.info('\u2554' + '\u2550' * w + '\u2557')
    logger.info(f'\u2551{titulo:^{w}}\u2551')
    logger.info(f'\u2551{linha_proc:<{w}}\u2551')
    logger.info(f'\u2551{linha_dur:<{w}}\u2551')
    if extra:
        logger.info(f'\u2551  {extra:<{w-2}}\u2551')
    logger.info('\u255a' + '\u2550' * w + '\u255d')


def _extrair_docling(path: Path, sigla: str, is_img: bool, pdf_sha256: str,
                     nome_pdf: str = '', url_fonte: str = '',
                     converter=None) -> list:
    """
    Extrai entregas via Docling TableFormer.
    FIX: eixo_atual resetado a cada nova página (evita contaminação).
    """
    if converter is not None:
        _cv = converter
    else:
        opts_kw = {
            'do_table_structure': True,
            'table_structure_options': TableStructureOptions(mode=TableFormerMode.ACCURATE),
            'do_ocr': is_img,
        }
        if is_img:
            opts_kw['ocr_options'] = TesseractCliOcrOptions(lang=['por'], force_full_page_ocr=True)
        opts = PdfPipelineOptions(**opts_kw)
        _cv  = DocumentConverter(format_options={'pdf': PdfFormatOption(pipeline_options=opts)})

    try:
        with ThreadPoolExecutor(max_workers=1) as _ex:
            _fut = _ex.submit(_cv.convert, str(path))
            result = _fut.result(timeout=PDF_TIMEOUT)
    except _FuturesTimeout:
        logger.error(f'TIMEOUT ({PDF_TIMEOUT}s): {nome_pdf} — pulando')
        return []

    rows = []
    last_page = -1
    eixo_atual = None  # resetado por página abaixo

    for tbl_idx, tbl in enumerate(result.document.tables):
        df  = tbl.export_to_dataframe(doc=result.document)
        pag = tbl.prov[0].page_no if tbl.prov else 0

        # ── FIX: reset por página ────────────────────────────────────
        if pag != last_page:
            eixo_atual = None
            last_page  = pag

        if len(df.columns) < 2 or len(df) < 2:  # threshold 3→2: aceita tabelas com 1 linha de dados (MD, MEC, FIOCRUZ)
            continue
        all_text = ' '.join(df.values.flatten().astype(str))
        if re.search(r'gestão de riscos|probabilidade.*ocorr', all_text, re.I):
            continue

        # Detectar mapeamento por header (FIX: column-aware extraction)
        cmap = _col_map(df)
        has_headers = bool(cmap)

        for row_idx, (_, row) in enumerate(df.iterrows()):
            cells = [str(v).strip() for v in row.values]
            full  = ' | '.join(c for c in cells if c and c.lower() not in ('nan',''))
            if len(full) < 10:
                continue
            e = detectar_eixo(full)
            if e:
                eixo_atual = e
            if eixo_atual is None:
                continue

            # Extrair campos por header quando disponível, posicional como fallback
            servico = _get_cell(cells, cmap, 'servico', 0)
            produto = _get_cell(cells, cmap, 'produto', 1 if len(cells) > 1 else None)
            area    = _get_cell(cells, cmap, 'area',   -2 if len(cells) > 2 else None)
            data_e  = _get_cell(cells, cmap, 'data',   -1 if len(cells) > 1 else None)

            texto = full  # linha completa — necessário para Aho-Corasick do Layer 3

            # parse_flag básico (será sobrescrito pelo Layer 3)
            parse_flag = 'raw'

            if len(texto) < 5:
                continue
            _td = _tipo_doc(nome_pdf)
            rows.append({
                'sigla':        sigla,
                'pagina':       pag,
                'eixo_num':     eixo_atual,
                'eixo_label':   EIXOS.get(eixo_atual,''),
                'texto':        texto[:600],
                'ncols':        len(df.columns),
                'area':         area[:120],
                'data_entrega': data_e[:20],
                'col_map_ok':   has_headers,
                'extrator':     'docling',
                'parse_flag':   parse_flag,
                'pdf_sha256':   pdf_sha256,
                # ── estrutura CGREP ───────────────────────────────────
                'tipo_doc':     _td,
                'passo_ptd':    _TIPO_PASSO.get(_td, 6),
                'passo_label':  _PASSO_LABEL[_TIPO_PASSO.get(_td, 6)],
                # ── rastreabilidade fina ──────────────────────────────
                'tabela_idx':   tbl_idx,
                'linha_tabela': row_idx,
                'nome_pdf':     nome_pdf,
                'url_fonte':    url_fonte,
            })

    # ── Orçamento de pixels (Docling) ──────────────────────────────────
    # Estima cobertura comparando área total das tabelas extraídas com
    # a área total das páginas do documento (proxy sem re-renderizar).
    try:
        _total_area = sum(
            (p.size.width * p.size.height)
            for p in result.document.pages.values()
            if p.size
        )
        _covered_area = 0.0
        for tbl in result.document.tables:
            for prov in (tbl.prov or []):
                b = prov.bbox
                _covered_area += abs((b.r - b.l) * (b.t - b.b))
        if _total_area > 0:
            _px_cov = round(_covered_area / _total_area * 100, 1)
            logger.info(f'  pixel_budget (Docling) {nome_pdf}: {_px_cov:.1f}% '
                        f'(área tabelas/{_total_area:.0f} px²)')
    except Exception:
        pass   # pixel_budget é informativo, não bloqueia

    return rows


def _extrair_pymupdf(path: Path, sigla: str, pdf_sha256: str,
                     nome_pdf: str = '', url_fonte: str = '') -> list:
    """
    Fallback PyMuPDF.
    FIX: eixo_atual resetado a cada nova página.
    """
    rows = []
    try:
        doc = fitz.open(str(path))
    except Exception:
        return []
    for npag, pag in enumerate(doc, 1):
        eixo_atual = None  # FIX: reset por página
        try:
            for tbl_idx, tbl in enumerate(pag.find_tables().tables):
                df = tbl.to_pandas()
                for row_idx, (_, row) in enumerate(df.iterrows()):
                    txt = ' '.join(str(v) for v in row.values if v)
                    e   = detectar_eixo(txt)
                    if e:
                        eixo_atual = e
                    if eixo_atual and len(txt) > 10:
                        _td = _tipo_doc(nome_pdf)
                        rows.append({
                            'sigla':        sigla,
                            'pagina':       npag,
                            'eixo_num':     eixo_atual,
                            'eixo_label':   EIXOS.get(eixo_atual,''),
                            'texto':        txt[:600],
                            'ncols':        len(df.columns),
                            'area':         '',
                            'data_entrega': '',
                            'extrator':     'pymupdf_tables',
                            'parse_flag':   'sem_produto',
                            'pdf_sha256':   pdf_sha256,
                            'tipo_doc':     _td,
                            'passo_ptd':    _TIPO_PASSO.get(_td, 6),
                            'passo_label':  _PASSO_LABEL[_TIPO_PASSO.get(_td, 6)],
                            'tabela_idx':   tbl_idx,
                            'linha_tabela': row_idx,
                            'nome_pdf':     nome_pdf,
                            'url_fonte':    url_fonte,
                        })
        except AttributeError:
            for row_idx, linha in enumerate(pag.get_text().split('\n')):
                linha = linha.strip()
                e = detectar_eixo(linha)
                if e:
                    eixo_atual = e
                if eixo_atual and len(linha) > 10:
                    _td = _tipo_doc(nome_pdf)
                    rows.append({
                        'sigla':        sigla,
                        'pagina':       npag,
                        'eixo_num':     eixo_atual,
                        'eixo_label':   EIXOS.get(eixo_atual,''),
                        'texto':        linha[:600],
                        'ncols':        None,
                        'area':         '',
                        'data_entrega': '',
                        'extrator':     'pymupdf_text',
                        'parse_flag':   'sem_produto',
                        'pdf_sha256':   pdf_sha256,
                        'tipo_doc':     _td,
                        'passo_ptd':    _TIPO_PASSO.get(_td, 6),
                        'passo_label':  _PASSO_LABEL[_TIPO_PASSO.get(_td, 6)],
                        'tabela_idx':   0,
                        'linha_tabela': row_idx,
                        'nome_pdf':     nome_pdf,
                        'url_fonte':    url_fonte,
                    })
    doc.close()
    return rows


CHECKPOINT_E = DIR_LOG / '_checkpoint_entregas.jsonl'
_CHECKPOINT_R = DIR_LOG / '_checkpoint_riscos.jsonl'  # antecipado para --force-download
processados_e: set = set()
all_rows_e:    list = []

if FORCE_DOWNLOAD:
    for _ck in (CHECKPOINT_E, _CHECKPOINT_R):
        if _ck.exists():
            _ck.unlink()
            logger.info(f'--force-download: checkpoint removido → {_ck.name}')

if CHECKPOINT_E.exists():
    with open(CHECKPOINT_E) as f:
        for line in f:
            obj = json.loads(line)
            processados_e.add(obj['filename'])
            all_rows_e.extend(obj['rows'])
    print(f'Retomando: {len(processados_e)} arquivos já processados')

# URL lookup para rastreabilidade (filename → url_fonte)
_cat_path = DIR_LOG / 'catalogo_scraped.csv'
url_por_arquivo: dict = {}
if _cat_path.exists():
    _cat = pd.read_csv(_cat_path)
    url_por_arquivo = dict(zip(_cat['filename'], _cat['url']))

# Usar df_san para iterar apenas PDFs baixados com sucesso
pdfs_ok = df_san[df_san[['kb_ok','sig_ok','pag_ok']].all(axis=1)]
if SIGLAS_DEBUG:
    pdfs_ok = pdfs_ok[pdfs_ok['arquivo'].apply(_sigla_de_fn).isin(SIGLAS_DEBUG)]
    logger.info(f'--siglas (debug): {len(pdfs_ok)} PDFs de {sorted(SIGLAS_DEBUG)}')
if MAX_PDFS > 0:
    pdfs_ok = pdfs_ok.head(MAX_PDFS)
    logger.info(f'--max-pdfs: limitando extração a {len(pdfs_ok)} PDFs')
logs_e   = []
total_e  = len(pdfs_ok)
_fase_t0 = time.time()
_n_ok_e  = 0
_n_wn_e  = 0

# Converter singletons — instanciados 1× por fase (evita 770 recarregamentos de peso)
if _DOCLING_OK:
    _opts_plain = PdfPipelineOptions(
        do_table_structure=True,
        table_structure_options=TableStructureOptions(mode=TableFormerMode.ACCURATE),
        do_ocr=False)
    _opts_ocr = PdfPipelineOptions(
        do_table_structure=True,
        table_structure_options=TableStructureOptions(mode=TableFormerMode.ACCURATE),
        do_ocr=True,
        ocr_options=TesseractCliOcrOptions(lang=['por'], force_full_page_ocr=True))
    _converter_plain = DocumentConverter(format_options={'pdf': PdfFormatOption(pipeline_options=_opts_plain)})
    _converter_ocr   = DocumentConverter(format_options={'pdf': PdfFormatOption(pipeline_options=_opts_ocr)})
    logger.info('DocumentConverter instanciado (singleton × 2: plain + OCR)')
else:
    _converter_plain = _converter_ocr = None

for _i, (_, srow) in enumerate(pdfs_ok.iterrows(), 1):
    fn     = srow['arquivo']
    path   = DIR_RAW / fn
    sha256 = srow['sha256']

    if fn in processados_e:
        continue

    sigla  = _sigla_de_fn(fn)
    is_img = bool(srow['image_pdf'])
    t0 = time.time()
    logger.info(f'[{_i}/{total_e}] → {fn}')

    _stop_e = threading.Event()
    _wdog_e = threading.Thread(target=_watchdog, args=(fn, _stop_e), daemon=True)
    _wdog_e.start()
    try:
        _url = url_por_arquivo.get(fn, '')
        if _DOCLING_OK:
            _cv = _converter_ocr if is_img else _converter_plain
            rows     = _extrair_docling(path, sigla, is_img, sha256,
                                        nome_pdf=fn, url_fonte=_url, converter=_cv)
            extrator = 'docling'
        else:
            rows     = _extrair_pymupdf(path, sigla, sha256,
                                        nome_pdf=fn, url_fonte=_url)
            extrator = rows[0]['extrator'] if rows else 'pymupdf'

        # Fallback pytesseract para PDFs imagem onde Docling retorna vazio
        if not rows and is_img and _OCR_FALLBACK_OK:
            logger.info(f'  → OCR fallback (pytesseract) para {sigla}')
            rows     = _extrair_ocr_fallback(path, sigla, sha256,
                                             nome_pdf=fn, url_fonte=_url)
            extrator = 'pytesseract_ocr'
            if rows:
                logger.info(f'  → OCR fallback: {len(rows)} linhas extraídas')
            else:
                logger.warning(f'  → OCR fallback: 0 linhas — {fn}')
    except Exception as exc:
        logger.error(f'{sigla}: {exc}')
        logs_e.append({'sigla':sigla,'filename':fn,'status':'ERROR','n':0,'erro':str(exc)[:100]})
        _n_wn_e += 1
        continue
    finally:
        _stop_e.set()

    all_rows_e.extend(rows)
    n = len(rows)
    elapsed = time.time() - t0
    _avg_s  = (time.time() - _fase_t0) / _i
    _eta    = _avg_s * (total_e - _i)
    _eta_s  = f'{int(_eta//60)}min' if _eta > 90 else f'{_eta:.0f}s'
    lvl = logging.INFO if n > 0 else logging.WARNING
    logger.log(lvl, f'[{_i}/{total_e}] {"✓" if n>0 else "⚠"} {sigla:<10}: '
                    f'{n:4d} entregas | {elapsed:.1f}s | ETA ~{_eta_s}')
    if n > 0: _n_ok_e += 1
    else:     _n_wn_e += 1
    logs_e.append({'sigla':sigla,'filename':fn,'status':'OK','n':n,'extrator':extrator})

    with open(CHECKPOINT_E,'a') as f:
        f.write(json.dumps({'filename':fn,'rows':rows}, ensure_ascii=False) + '\n')

df_corpus = pd.DataFrame(all_rows_e) if all_rows_e else pd.DataFrame()
pd.DataFrame(logs_e).to_csv(DIR_LOG / 'extracao_entregas_log.csv', index=False)
n_orgaos_e = df_corpus['sigla'].nunique() if not df_corpus.empty else 0
logger.info(f'{len(df_corpus):,} registros | {n_orgaos_e} órgãos')
_fase_box('ENTREGAS — fase concluída', total_e, _n_ok_e, _n_wn_e,
          time.time() - _fase_t0,
          f'{len(df_corpus):,} registros | {n_orgaos_e} órgãos')


# ════════════════════════════════════════════════════════════════════════
# ETAPA 5 — Extração de Riscos via Docling
# FIX: pdf_sha256 por registro; usa df_san para iterar diretivos
# ════════════════════════════════════════════════════════════════════════

PROB_MAP  = {'praticamente certo':'Praticamente certo','muito provável':'Muito provável',
             'provável':'Provável','pouco provável':'Pouco provável',
             'improvável':'Improvável','raro':'Raro'}
IMP_MAP   = {'muito alto':'Muito alto','alto':'Alto','médio':'Médio',
             'medio':'Médio','baixo':'Baixo','muito baixo':'Muito baixo'}
TREAT_MAP = {'mitigar':'Mitigar','miigar':'Mitigar','nitigar':'Mitigar',
             'transferir':'Transferir','aceitar':'Aceitar',
             'evitar':'Evitar','eliminar':'Eliminar','compartilhar':'Compartilhar'}
ACAO_ALFA = re.compile(r'\b(A\d{1,2})\b')
ACAO_NUM  = re.compile(r'\b(\d{1,2})\b')

def _norm(text: str, mapping: dict) -> str:
    key = re.sub(r'\s+', ' ', str(text).strip().lower())
    return mapping.get(key, str(text).strip())

def _extract_codes(text: str, tmpl: str) -> list:
    if tmpl == 'alfa':
        return list(dict.fromkeys(ACAO_ALFA.findall(text)))
    nums = [n for n in ACAO_NUM.findall(str(text)) if 1 <= int(n) <= 24]
    return [f'N{n}' for n in dict.fromkeys(nums)]

def _is_risk_table(df: pd.DataFrame) -> bool:
    all_text = ' '.join(df.values.flatten().astype(str)).lower()
    return (3 <= len(df.columns) <= 8) and (
        bool(re.search(r'provável|certo|improvável|raro', all_text)) or
        bool(re.search(r'mitigar|transferir|aceitar|evitar', all_text)))

def _detect_tmpl(df: pd.DataFrame) -> str:
    t = ' '.join(df.values.flatten().astype(str))
    if len(re.findall(r'\b5\.\d{1,2}\b', t)) > 2 and len(ACAO_ALFA.findall(t)) > 2:
        return 'alfa'
    if len(re.findall(r'\b5\.\d{1,2}\b', t)) > 2:
        return 'alfa'
    if len(re.findall(r'^[A-Z]\s', t, re.M)) > 2:
        return 'letra'
    return 'livre'

def _parse_risk_df(df: pd.DataFrame, sigla: str, fname: str, pdf_sha256: str):
    tmpl = _detect_tmpl(df)
    rows = []
    acoes_dict = {}
    col_names = [str(c).lower() for c in df.columns]

    def _col(*keys):
        for i, c in enumerate(col_names):
            if any(k in c for k in keys):
                return i
        return None

    i_desc = _col('risco', 'descrição', 'id')
    i_prob = _col('probabilidade', 'prob')
    i_imp  = _col('impacto', 'imp')
    i_trt  = _col('tratamento', 'opção', 'opcao')
    i_ac   = _col('ações', 'acoes', 'acao', 'mitigação')

    for _, row in df.iterrows():
        cells = [str(v).strip() for v in row.values]
        desc  = cells[i_desc] if i_desc is not None else cells[0]
        if not desc or len(desc) < 3 or desc.lower() == 'nan':
            continue
        dm = re.match(r'^(A\d{1,2}|\d{1,2})[.\-)\s](.{15,})', desc)
        if dm:
            k = dm.group(1)
            if not k.startswith('A'):
                k = f'N{k}'
            acoes_dict[k] = dm.group(2)[:150]
            continue
        prob   = _norm(cells[i_prob] if i_prob is not None else '', PROB_MAP)
        imp    = _norm(cells[i_imp]  if i_imp  is not None else '', IMP_MAP)
        trt    = _norm(cells[i_trt]  if i_trt  is not None else '', TREAT_MAP)
        ac_raw = cells[i_ac] if i_ac is not None else ''
        full   = ' '.join(cells)
        if not prob:
            pm = re.search(r'(Praticamente certo|Muito prov[aá]vel|Pouco prov[aá]vel|'
                           r'Improv[aá]vel|Prov[aá]vel|Raro)', full, re.I)
            if pm:
                prob = _norm(pm.group(1), PROB_MAP)
        if not trt:
            tm = re.search(r'(Mitigar|Miigar|Transferir|Aceitar|Evitar|Eliminar)', full, re.I)
            if tm:
                trt = _norm(tm.group(1), TREAT_MAP)
        if not imp:
            im = re.search(r'\b(Muito alto|Muito baixo|Alto|M[eé]dio|Baixo)\b', full, re.I)
            if im:
                imp = _norm(im.group(1), IMP_MAP)
        codes = _extract_codes(ac_raw or full, tmpl)
        rows.append({
            'sigla': sigla, 'arquivo': fname, 'template': tmpl,
            'risco_desc': desc[:300], 'probabilidade': prob,
            'impacto': imp, 'opcao_tratamento': trt,
            'n_acoes': len(codes), 'acoes_refs': ','.join(codes),
            'pdf_sha256': pdf_sha256,
        })
    return rows, acoes_dict


CHECKPOINT_R = DIR_LOG / '_checkpoint_riscos.jsonl'
processados_r: set = set()
all_riscos:    list = []
all_acoes_r:   list = []
bridge:        list = []

if CHECKPOINT_R.exists():
    with open(CHECKPOINT_R) as f:
        for line in f:
            obj = json.loads(line)
            processados_r.add(obj['filename'])
            all_riscos.extend(obj['riscos'])
            all_acoes_r.extend(obj.get('acoes_raw', []))
            bridge.extend(obj.get('bridge', []))
    print(f'Retomando riscos: {len(processados_r)} arquivos já processados')

# Diretivos: PDFs cujo nome sugere documento diretivo
diretivo_pats = re.compile(r'diretivo|dcd|doc_dir', re.I)
pdfs_diretivos = df_san[
    df_san[['kb_ok', 'sig_ok', 'pag_ok']].all(axis=1) &
    df_san['arquivo'].apply(lambda x: bool(diretivo_pats.search(str(x))))
]
if SIGLAS_DEBUG:
    pdfs_diretivos = pdfs_diretivos[
        pdfs_diretivos['arquivo'].apply(_sigla_de_fn).isin(SIGLAS_DEBUG)
    ]

logs_r   = []
risco_id = len(all_riscos)
total_r  = len(pdfs_diretivos)
_fase_t0_r = time.time()
_n_ok_r  = 0
_n_wn_r  = 0

for _j, (_, srow) in enumerate(pdfs_diretivos.iterrows(), 1):
    fn     = srow['arquivo']
    path   = DIR_RAW / fn
    sha256 = srow['sha256']
    sigla = _sigla_de_fn(fn)

    if fn in processados_r:
        continue

    is_img = bool(srow['image_pdf'])
    t0 = time.time()
    all_r: list = []
    all_a: dict = {}
    logger.info(f'[{_j}/{total_r}] → {fn}')

    _stop_r = threading.Event()
    _wdog_r = threading.Thread(target=_watchdog, args=(fn, _stop_r), daemon=True)
    _wdog_r.start()
    try:
        if _DOCLING_OK:
            _cv_r = _converter_ocr if is_img else _converter_plain
            try:
                with ThreadPoolExecutor(max_workers=1) as _ex_r:
                    _fut_r = _ex_r.submit(_cv_r.convert, str(path))
                    res = _fut_r.result(timeout=PDF_TIMEOUT)
            except _FuturesTimeout:
                logger.error(f'TIMEOUT ({PDF_TIMEOUT}s): {fn} — pulando')
                _n_wn_r += 1
                continue
            for tbl in res.document.tables:
                df_t = tbl.export_to_dataframe(doc=res.document)
                if _is_risk_table(df_t):
                    r, a = _parse_risk_df(df_t, sigla, fn, sha256)
                    all_r.extend(r)
                    all_a.update(a)
            extrator = 'docling'
        else:
            RISK_SEC = re.compile(r'^\s*5\s*[-—]\s*GESTÃO\s+DE\s+RISCO', re.I | re.M)
            doc = fitz.open(str(path))
            for pag in doc:
                if not RISK_SEC.search(pag.get_text()):
                    continue
                try:
                    for tbl in pag.find_tables().tables:
                        df_t = tbl.to_pandas()
                        if _is_risk_table(df_t):
                            r, a = _parse_risk_df(df_t, sigla, fn, sha256)
                            all_r.extend(r)
                            all_a.update(a)
                except AttributeError:
                    pass
            doc.close()
            extrator = 'pymupdf'
    except Exception as exc:
        logger.error(f'{sigla}: {exc}')
        logs_r.append({'sigla': sigla, 'filename': fn, 'status': 'ERROR',
                       'n_riscos': 0, 'erro': str(exc)[:100]})
        _n_wn_r += 1
        continue
    finally:
        _stop_r.set()

    # Adicionar passo CGREP + risco_id a cada risco
    _td_r = _tipo_doc(fn)
    for i, r in enumerate(all_r):
        r['risco_id']   = risco_id + i
        r['tipo_doc']   = _td_r
        r['passo_ptd']  = 7
        r['passo_label'] = _PASSO_LABEL[7]
    risco_id += len(all_r)
    all_riscos.extend(all_r)

    for cod, txt in all_a.items():
        aid = f'{sigla}__{cod}'
        all_acoes_r.append({'sigla': sigla, 'acao_id': aid, 'codigo': cod,
                            'texto': txt,
                            'tipo': 'alfa' if cod.startswith('A') else 'numerico'})
    for r in all_r:
        for cod in r.get('acoes_refs', '').split(','):
            cod = cod.strip()
            if cod:
                bridge.append({'risco_id': r['risco_id'], 'sigla': sigla,
                               'acao_id': f'{sigla}__{cod}', 'codigo': cod})

    n = len(all_r)
    elapsed_r = time.time() - t0
    _avg_r    = (time.time() - _fase_t0_r) / _j
    _eta_r    = _avg_r * (total_r - _j)
    _eta_rs   = f'{int(_eta_r//60)}min' if _eta_r > 90 else f'{_eta_r:.0f}s'
    lvl_r = logging.INFO if n > 0 else logging.WARNING
    logger.log(lvl_r, f'[{_j}/{total_r}] {"✓" if n>0 else "⚠"} {sigla:<10}: '
                      f'{n:3d} riscos | {elapsed_r:.1f}s | ETA ~{_eta_rs}')
    if n > 0: _n_ok_r += 1
    else:     _n_wn_r += 1
    logs_r.append({'sigla': sigla, 'filename': fn, 'status': 'OK',
                   'n_riscos': n, 'extrator': extrator})

    with open(CHECKPOINT_R, 'a') as f:
        f.write(json.dumps({
            'filename': fn, 'riscos': all_r,
            'acoes_raw': [a for a in all_acoes_r if a['sigla'] == sigla],
            'bridge':    [b for b in bridge        if b['sigla'] == sigla],
        }, ensure_ascii=False) + '\n')

df_riscos = pd.DataFrame(all_riscos) if all_riscos else pd.DataFrame()
df_acoes  = (pd.DataFrame(all_acoes_r).drop_duplicates(subset=['acao_id'])
             if all_acoes_r else pd.DataFrame())
df_bridge = pd.DataFrame(bridge) if bridge else pd.DataFrame()
n_orgaos_r = df_riscos['sigla'].nunique() if not df_riscos.empty else 0
_fase_box('RISCOS — fase concluída', total_r, _n_ok_r, _n_wn_r,
          time.time() - _fase_t0_r,
          f'{len(df_riscos)} riscos | {n_orgaos_r} órgãos')
pd.DataFrame(logs_r).to_csv(DIR_LOG / 'extracao_riscos_log.csv', index=False)
logger.info(f'{len(df_riscos)} riscos | {len(df_acoes)} ações | {len(df_bridge)} relações')


# ════════════════════════════════════════════════════════════════════════
# ETAPA 6 — Exportação + Tabelas auxiliares + Manifesto
# FIX: gera ptd_pivot_eixos.csv e ptd_datas_assinatura.csv
#      que são inputs obrigatórios do ptd_corpus_v21.py
# ════════════════════════════════════════════════════════════════════════

def export_all(df: pd.DataFrame, stem: str):
    df.to_csv(DIR_DB / f'{stem}.csv', index=False)
    df.to_json(DIR_DB / f'{stem}.json', orient='records', force_ascii=False, indent=2)
    try:
        df.to_parquet(DIR_DB / f'{stem}.parquet', index=False)
    except Exception:
        pass
    logger.info(f'{stem:35s}: {len(df):,} linhas')

# ── Corpus de entregas ────────────────────────────────────────────────
if not df_corpus.empty:
    export_all(df_corpus, 'ptd_corpus_raw')

    # ptd_pivot_eixos.csv — input do ptd_corpus_v21.py
    meta_cols = ['sigla']
    for col in ['grupo', 'compartilhado', 'tem_diretivo']:
        if col not in df_corpus.columns:
            df_corpus[col] = None

    dens = (df_corpus.groupby(['sigla', 'eixo_num'])
            .size().reset_index(name='n'))
    pivot = (dens.pivot_table(index='sigla', columns='eixo_num',
                              values='n', fill_value=0).reset_index())
    pivot.columns = (['sigla'] +
                     [f'eixo_{int(c)}' for c in pivot.columns[1:]])
    pivot['total']          = pivot.filter(like='eixo_').sum(axis=1)
    pivot['n_eixos_ativos'] = (pivot.filter(like='eixo_') > 0).sum(axis=1)
    for col in ['grupo', 'compartilhado', 'tem_diretivo']:
        if col in df_corpus.columns:
            m = df_corpus.drop_duplicates('sigla').set_index('sigla')[col]
            pivot[col] = pivot['sigla'].map(m)
    pivot = pivot.sort_values('total', ascending=False)
    export_all(pivot, 'ptd_pivot_eixos')

    # ptd_datas_assinatura.csv — input do ptd_corpus_v21.py
    DATE_PATS = [
        re.compile(r'pactuad[ao]\s+em\s+(\d{1,2}[/.]\d{1,2}[/.]\d{2,4})', re.I),
        re.compile(r'Bras[ií]lia.*?(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})', re.I),
        re.compile(r'(\d{1,2}[/.]\d{1,2}[/.]202[4-9])'),
    ]
    rows_d = []
    for fn in df_corpus['pdf_sha256'].dropna().index if 'pdf_sha256' in df_corpus.columns \
            else []:
        pass  # fallback: iterate PDFs directly
    for path in sorted(DIR_RAW.glob('*.pdf')):
        data = None
        try:
            doc = fitz.open(str(path))
            txt = ' '.join(p.get_text() for p in list(doc)[:5])
            doc.close()
            for pat in DATE_PATS:
                m = pat.search(txt)
                if m:
                    data = m.group(1).strip()
                    break
        except Exception:
            pass
        # Associar a todas as siglas que usam este PDF
        fn = path.name
        siglas_pdf = df_corpus[df_corpus.get('pdf_sha256', pd.Series(dtype=str)).notna() |
                                pd.Series(True, index=df_corpus.index)
                                ]['sigla'].unique() \
            if df_corpus.empty else \
            df_corpus[df_corpus.get('texto', pd.Series(dtype=str)).notna()
                      ]['sigla'].unique()
        # Simpler: one row per unique PDF-filename association
        rows_d.append({'arquivo': fn, 'data_raw': data})

    df_datas = pd.DataFrame(rows_d).drop_duplicates(subset=['arquivo'])
    export_all(df_datas, 'ptd_datas_assinatura')

# ── Corpus de riscos ──────────────────────────────────────────────────
ORD_PROB  = ['Improvável','Raro','Pouco provável','Provável',
             'Muito provável','Praticamente certo']
ORD_IMP   = ['Muito baixo','Baixo','Médio','Alto','Muito alto']
ORD_TREAT = ['Aceitar','Evitar','Eliminar','Transferir','Compartilhar','Mitigar']

if not df_riscos.empty:
    df_r = df_riscos.copy()
    df_r['probabilidade_cat']    = pd.Categorical(df_r['probabilidade'],
                                                   categories=ORD_PROB, ordered=True)
    df_r['impacto_cat']          = pd.Categorical(df_r['impacto'],
                                                   categories=ORD_IMP, ordered=True)
    df_r['opcao_tratamento_cat'] = pd.Categorical(df_r['opcao_tratamento'],
                                                   categories=ORD_TREAT)
    export_all(df_r, 'ptd_riscos')

if not df_acoes.empty:
    if not df_bridge.empty:
        freq = (df_bridge.groupby('acao_id')
                .agg(n_riscos=('risco_id', 'nunique'),
                     n_orgaos=('sigla', 'nunique')).reset_index())
        df_acoes = df_acoes.merge(freq, on='acao_id', how='left')
    df_acoes = df_acoes.sort_values('n_orgaos', ascending=False, na_position='last')
    export_all(df_acoes, 'ptd_acoes_dict')

if not df_bridge.empty:
    export_all(df_bridge, 'ptd_riscos_acoes')

# ── Proveniência ──────────────────────────────────────────────────────
PROVENIENCIA.update({
    'n_entregas':      len(df_corpus) if not df_corpus.empty else 0,
    'n_orgaos':        df_corpus['sigla'].nunique() if not df_corpus.empty else 0,
    'n_riscos':        len(df_riscos) if not df_riscos.empty else 0,
    'versao_pipeline': '3.0-melhorado',
})
(DIR_DB / 'proveniencia.json').write_text(
    json.dumps(PROVENIENCIA, indent=2, ensure_ascii=False))

# ── Manifesto final ───────────────────────────────────────────────────
manifesto = {
    'versao_pipeline':          '3.0-melhorado',
    'data_execucao':            datetime.now().isoformat(),
    'total_pdfs_baixados':      int(df_dl.ok.sum()) if not df_dl.empty else 0,
    'total_registros_extraidos': len(df_corpus),
    'total_riscos':             len(df_riscos),
    'outputs': {
        'ptd_corpus_raw.csv':        'corpus bruto de entregas com sha256',
        'ptd_pivot_eixos.csv':       'pivot sigla × eixo — input ptd_corpus_v21',
        'ptd_datas_assinatura.csv':  'datas por PDF — input ptd_corpus_v21',
        'ptd_riscos.csv':            'matriz de riscos com categorias ordinais',
        'ptd_acoes_dict.csv':        'dicionário de ações de tratamento',
        'ptd_riscos_acoes.csv':      'bridge risco × ação',
        'proveniencia.json':         'metadados de proveniência completos',
        'pipeline_manifest.json':    'sha256 de todos os PDFs processados',
    },
    'pdfs_sha256': {
        row['arquivo']: row['sha256']
        for _, row in df_san.iterrows()
        if row['sha256']
    },
    'proveniencia': PROVENIENCIA,
}
(DIR_DB / 'pipeline_manifest.json').write_text(
    json.dumps(manifesto, indent=2, ensure_ascii=False))
logger.info(f'Manifesto salvo: pipeline_manifest.json | SHA-256 de {len(manifesto["pdfs_sha256"])} PDFs')
logger.info('=' * 50)
logger.info('PTD-BR v3.0-melhorado — PIPELINE CONCLUÍDO')
logger.info('=' * 50)
for stem, desc in manifesto["outputs"].items():
    p = DIR_DB / stem
    if p.exists():
        logger.info(f'{stem:40s} {p.stat().st_size//1024:4d} KB')
_run_url = None
if os.environ.get('GITHUB_RUN_ID') and os.environ.get('GITHUB_REPOSITORY'):
    _run_url = (f"https://github.com/{os.environ['GITHUB_REPOSITORY']}"
                f"/actions/runs/{os.environ['GITHUB_RUN_ID']}")
    logger.info(f'📦 Artefatos: {_run_url}')
logger.info('=' * 50)
