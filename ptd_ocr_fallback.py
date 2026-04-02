# ╔══════════════════════════════════════════════════════╗
# ║  PTD-BR — OCR Fallback (pytesseract + PyMuPDF)     ║
# ║  Chamado automaticamente quando Docling retorna     ║
# ║  rows == [] para PDFs com image_pdf = True          ║
# ║  IPEA / COGIT / DIEST                               ║
# ╚══════════════════════════════════════════════════════╝
#
# Componentes incorporados do script fornecido pelo usuário:
#   - render_page()       → PDF page → PIL Image com DPI + rotação
#   - is_content_page()   → descarta páginas em branco por threshold de pixels
#   - ocr_page()          → pytesseract → lista de linhas
#   - parse_lines_to_rows() → linhas → dicts de entrega (usa detectar_eixo de ptd_constants)
#   - OCR_CONFIG          → metadados de rotação por sigla
#   - segment_md()        → fatiamento de PDF multi-órgão (MD cobre MD+CENSIPAM+HFA)
#
# NÃO incorporado do script original:
#   - EIXO_MAP            → usar detectar_eixo() de ptd_constants
#   - sigla_from_filename() → usar _sigla_de_fn() do pipeline principal
#   - fonte_ocr campo     → campo fora do schema; usar extrator='pytesseract_ocr'
#   - run_ocr_all()       → lógica de orquestração pertence ao pipeline principal

import re
import logging
from pathlib import Path
from typing import Optional

try:
    import fitz          # PyMuPDF
    import numpy as np
    import pytesseract
    from PIL import Image
    _OCR_DEPS_OK = True
except ImportError as _e:
    _OCR_DEPS_OK = False
    logging.getLogger('ptd').warning(
        f'ptd_ocr_fallback: dependências ausentes ({_e}) — OCR fallback desativado')

from ptd_constants import detectar_eixo

logger = logging.getLogger('ptd')

# ── Configuração por sigla: rotação necessária (graus anti-horário) ───────────
# INCRA e FUNDACENTRO têm PDFs digitalizados em modo paisagem (90° ou 270°)
OCR_CONFIG: dict[str, dict] = {},
    'FUNAI':       {'rot': 0},
    'ITI':         {'rot': 0},
    'SGPR':        {'rot': 0},
    'INCRA':       {'rot': 270},
    'FUNDACENTRO': {'rot': 270},
    'MCOM':        {'rot': 0},
}


def render_page(pdf_path: Path, page_idx: int,
                dpi: int = 200, rotate_image: int = 0) -> 'Image.Image':
    """Renderiza uma página do PDF como PIL Image.

    Extraído do script do usuário (render_page).
    Usa fitz.Matrix para escalar pelo DPI e PIL.Image.rotate para corrigir orientação.
    """
    doc  = fitz.open(str(pdf_path))
    page = doc[page_idx]
    mat  = fitz.Matrix(dpi / 72, dpi / 72)
    pix  = page.get_pixmap(matrix=mat, alpha=False)
    img  = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
    doc.close()
    if rotate_image:
        img = img.rotate(rotate_image, expand=True)
    return img


def is_content_page(img: 'Image.Image',
                    dark_threshold: int = 200,
                    min_dark_pct: float = 1.0) -> bool:
    """Retorna True se a página tem conteúdo (não é branca/vazia).

    Extraído do script do usuário (is_content_page).
    Conta pixels escuros (valor < dark_threshold em escala de cinza).
    min_dark_pct = porcentagem mínima de pixels escuros para considerar com conteúdo.
    """
    arr   = np.array(img.convert('L'))
    dark  = (arr < dark_threshold).sum()
    total = arr.size
    return (dark / total * 100) >= min_dark_pct


def ocr_page(img: Image.Image) -> list[str]:
    """Roda pytesseract na imagem e retorna linhas não-vazias."""
    raw = pytesseract.image_to_string(img, lang='por', config='--psm 6')
    return [line.strip() for line in raw.splitlines() if line.strip()]


def parse_lines_to_rows(lines: list[str], sigla: str, pagina: int,
                        nome_pdf: str = '', url_fonte: str = '',
                        sha256: str = '') -> list[dict]:
    """Converte linhas OCR em dicts de entrega compatíveis com o schema do corpus.

    Adaptado do script do usuário (parse_lines_to_rows):
    - EIXO_MAP substituído por detectar_eixo() de ptd_constants
    - extrator='pytesseract_ocr' (sem campo fonte_ocr separado)
    - Heurística: linha com >= 6 tokens e sem número isolado de página é candidata a entrega
    """
    rows: list[dict] = []
    eixo_atual: Optional[int] = None

    for line in lines:
        eixo = detectar_eixo(line)
        if eixo:
            eixo_atual = eixo
            continue

        tokens = line.split()
        if len(tokens) < 6:
            continue

        # Descarta linhas que são apenas número de página ou cabeçalho curto
        if re.fullmatch(r'\d{1,3}', line):
            continue

        rows.append({
            'sigla':        sigla,
            'servico':      line[:200],
            'produto':      '',
            'area':         '',
            'data_entrega': '',
            'eixo':         eixo_atual,
            'pagina':       pagina,
            'nome_pdf':     nome_pdf,
            'url_fonte':    url_fonte,
            'sha256_pdf':   sha256,
            'extrator':     'pytesseract_ocr',
            'tipo_doc':     'plano_completo',
            'passo_ptd':    6,
            'passo_label':  'Elaboração do Plano de Entregas',
        })
    return rows


def pixel_budget(img: 'Image.Image',
                 dark_threshold: int = 200) -> dict:
    """Calcula o orçamento de pixels de uma página.

    Retorna um dict com:
      - total_dark:   pixels escuros (conteúdo gráfico total)
      - covered:      pixels em regiões de texto reconhecido pelo OCR
      - coverage_pct: percentual do conteúdo coberto pelo parser

    Conceito: o "orçamento" é o total de pixels escuros (elementos gráficos
    — texto, tabelas, figuras). O parser "debita" os pixels das regiões de
    texto que efetivamente reconhece. coverage_pct baixo indica que o
    documento tem muito conteúdo que o OCR não capturou.
    """
    if not _OCR_DEPS_OK:
        return {'total_dark': 0, 'covered': 0, 'coverage_pct': 0.0}

    arr = np.array(img.convert('L'))
    total_dark = int((arr < dark_threshold).sum())

    if total_dark == 0:
        return {'total_dark': 0, 'covered': 0, 'coverage_pct': 100.0}

    # Usar pytesseract image_to_data para obter bounding boxes por palavra
    try:
        data = pytesseract.image_to_data(
            img, lang='por', config='--psm 6',
            output_type=pytesseract.Output.DICT)
    except Exception:
        return {'total_dark': total_dark, 'covered': 0, 'coverage_pct': 0.0}

    # Máscara de pixels "cobertos" pelas regiões reconhecidas
    covered_mask = np.zeros(arr.shape, dtype=bool)
    for i, conf in enumerate(data['conf']):
        if int(conf) < 30:   # descartar reconhecimentos de baixa confiança
            continue
        x, y = data['left'][i], data['top'][i]
        w, h = data['width'][i], data['height'][i]
        if w > 0 and h > 0:
            covered_mask[y:y+h, x:x+w] = True

    # Pixels escuros que estão dentro de regiões reconhecidas
    covered_dark = int(((arr < dark_threshold) & covered_mask).sum())
    coverage_pct = round(covered_dark / total_dark * 100, 1)

    return {
        'total_dark': total_dark,
        'covered':    covered_dark,
        'coverage_pct': coverage_pct,
    }


def extrair_ocr(path: Path, sigla: str, sha256: str,
                nome_pdf: str = '', url_fonte: str = '',
                dpi: int = 200) -> list[dict]:
    """Extrai entregas de um PDF-imagem via pytesseract.

    Ponto de entrada chamado pelo pipeline quando Docling retorna rows == [].
    Usa OCR_CONFIG para obter rotação correta por sigla.
    Retorna [] silenciosamente se dependências não estiverem instaladas.
    Loga pixel_budget por página para rastrear cobertura de extração.
    """
    if not _OCR_DEPS_OK:
        return []
    cfg = OCR_CONFIG.get(sigla.upper(), {})
    rot = cfg.get('rot', 0)
    dpi = cfg.get('dpi', dpi)
    doc = fitz.open(str(path))
    n_pages = len(doc)
    doc.close()

    all_rows: list[dict] = []
    total_dark_all, covered_all = 0, 0

    for idx in range(n_pages):
        try:
            img = render_page(path, idx, dpi=dpi, rotate_image=rot)
        except Exception as exc:
            logger.warning(f'OCR render_page falhou p.{idx+1} de {nome_pdf}: {exc}')
            continue

        if not is_content_page(img):
            continue

        budget = pixel_budget(img)
        total_dark_all += budget['total_dark']
        covered_all    += budget['covered']

        lines = ocr_page(img)
        rows  = parse_lines_to_rows(lines, sigla, idx + 1,
                                    nome_pdf=nome_pdf, url_fonte=url_fonte,
                                    sha256=sha256)
        all_rows.extend(rows)

    if total_dark_all > 0:
        doc_coverage = round(covered_all / total_dark_all * 100, 1)
        logger.info(f'  pixel_budget {sigla}: {doc_coverage:.1f}% '
                    f'({covered_all:,}/{total_dark_all:,} px escuros cobertos)')
    return all_rows


def segment_md(pdf_path: Path, page_map: dict[str, tuple[int, int]],
               sha256: str = '', url_fonte: str = '') -> dict[str, list[dict]]:
    """Fatia PDF multi-órgão em seções por sigla.

    Incorporado do script do usuário (segment_md).
    page_map: {'MD': (0, 15), 'CENSIPAM': (16, 22), 'HFA': (23, 30)}
    Retorna dict sigla → lista de dicts de entrega.

    NOTA: page_map deve ser fornecido manualmente após inspeção do PDF.
    Esta função está disponível mas NÃO é chamada automaticamente — requer
    validação humana dos intervalos de página.
    """
    result: dict[str, list[dict]] = {}
    for sigla, (start, end) in page_map.items():
        rows: list[dict] = []
        for idx in range(start, end + 1):
            try:
                img = render_page(pdf_path, idx)
            except Exception as exc:
                logger.warning(f'segment_md render_page falhou p.{idx+1}: {exc}')
                continue
            if not is_content_page(img):
                continue
            lines = ocr_page(img)
            rows.extend(parse_lines_to_rows(
                lines, sigla, idx + 1,
                nome_pdf=pdf_path.name, url_fonte=url_fonte, sha256=sha256,
            ))
        result[sigla] = rows
    return result
