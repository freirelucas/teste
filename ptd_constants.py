# ╔══════════════════════════════════════════════════════╗
# ║  PTD-BR — Constantes compartilhadas                ║
# ║  Fonte única de verdade para EIXOS, padrões e dirs ║
# ║  IPEA / COGIT / DIEST                               ║
# ╚══════════════════════════════════════════════════════╝
# Importado por: ptd_pipeline_v30.py, ptd_corpus_v21.py, tests/
# Não executa código ao ser importado.

from pathlib import Path
import re
from typing import Optional

# ── Diretórios de trabalho ────────────────────────────────────────────────────
DIR_ROOT = Path('ptd_corpus')
DIR_RAW  = DIR_ROOT / '01_raw_pdfs'
DIR_LOG  = DIR_ROOT / '02_logs'
DIR_DB   = DIR_ROOT / '03_database'

# ── Portal de coleta (fonte única — não duplicar nos scripts) ─────────────────
# ATENÇÃO: URL sem /ptds-vigentes/ — essa subpágina é legada (~18 PDFs antigos)
# A página principal lista todos os ~90 órgãos com PTD vigente (~180 PDFs)
PORTAL_BASE = (
    'https://www.gov.br/governodigital/pt-br/'
    'estrategias-e-governanca-digital/'
    'planos-de-transformacao-digital'
)

# ── Eixos EFGD (Estratégia Federal de Governo Digital) ───────────────────────
EIXOS: dict[int, str] = {
    1: 'Centrado no Cidadão e Inclusivo',
    2: 'Integrado e Colaborativo',
    3: 'Inteligente e Inovador',
    4: 'Confiável e Seguro',
    5: 'Transparente, Aberto e Participativo',
    6: 'Eficiente e Sustentável',
}

# ── Padrões de detecção por palavras-chave (fallback após regex numérico) ─────
# FIX E5: transpar(?:en|ên) captura "transparente" E "transparência"
# FIX E6: efici[eê]n captura "eficiente" E "eficiência"
_EIXO_PATS: list[tuple[int, re.Pattern]] = [
    (1, re.compile(r'cidad[ãa]o|inclusiv|servi[cç]os digitais|unifica[cç][aã]o de canais', re.I)),
    (2, re.compile(r'integrad|colaborat|interoperab', re.I)),
    (3, re.compile(r'inteligent|inovad|govern[aâ]n[cç]a.*dados|gest[aã]o.*dados', re.I)),
    (4, re.compile(r'confi[aá]vel|segur|privacidade|ppsi', re.I)),
    (5, re.compile(r'transpar(?:en|ên)|aberto|participat|dados abertos', re.I)),
    (6, re.compile(r'efici[eê]n|eficient|sustent|desburocrat|simplifica[çc]', re.I)),
]

# ── Regex numérica: "Eixo 3", "E-4", "E.2" ───────────────────────────────────
_PAT_EIXO_NUM = re.compile(r'eixo\s*([1-6])\b|E[-.]([1-6])\b', re.I)


def detectar_eixo(texto: str) -> Optional[int]:
    """Detecta o número do eixo (1-6) em um texto de cabeçalho ou linha.

    Tenta primeiro padrão numérico explícito ("Eixo 3", "E-4"),
    depois cai nos padrões por palavras-chave (_EIXO_PATS).
    Retorna None se nenhum eixo for detectado.
    """
    if not texto:
        return None
    m = _PAT_EIXO_NUM.search(texto)
    if m:
        return int(m.group(1) or m.group(2))
    for num, pat in _EIXO_PATS:
        if pat.search(texto):
            return num
    return None
