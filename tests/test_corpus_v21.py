"""
Testes unitários para ptd_corpus_v21.py
Funções testadas: parse_linha, classificar_tipo_entrega, corrigir_eixo

Execução:
    pytest tests/ -v
"""
import sys, re, json
from pathlib import Path
import pytest

# ── Fixtures de config mínima ─────────────────────────────────────────────────
PRODUTOS_MOCK = [
    'Plano de Segurança da Informação (PPSI)',
    'Login Único',
    'Serviços Digitais e Melhoria da Qualidade',
    'Disponibilização em Acesso Digital',
]
MAND_PROD_MOCK = {'Plano de Segurança da Informação (PPSI)'}
SUBEIXOS_MOCK  = ['Serviços Digitais', 'Governança de Dados', 'Segurança da Informação']

PAT_DATA = re.compile(
    r'(\d{1,2}/\d{1,2}/\d{2,4}'
    r'|\d{1,2}/\d{4}'
    r'|\d[TtQq][/.\-]?\d{2,4}'
    r'|\d{1,2}[ºo°]?\s*[Tt]rim(?:estre)?[/.\-]?\d{2,4}'
    r'|\d{1,2}[Tt]RIM\d{2}'
    r'|(?:jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)[./\-]?\d{2,4}'
    r'|(?:janeiro|fevereiro|mar[çc]o|abril|maio|junho|julho|agosto'
    r'|setembro|outubro|novembro|dezembro)\s*(?:de\s*)?\d{2,4}'
    r'|\b(202[0-9])\b)',
    re.I
)
PAT_RUIDO    = re.compile(r'^(Servi[çc]o|Produto|Eixo|[AÁ]rea\s|Entregas|DtPact|DtEntrega)', re.I)
PAT_ID_GOVBR = re.compile(r'^\d{3,6}\s+(?:Servi[çc]o\s+)?')

def _parse_linha(txt, produtos=PRODUTOS_MOCK, subeixos=SUBEIXOS_MOCK):
    """Cópia isolada de parse_linha para testes sem efeitos de borda."""
    import pandas as pd
    if pd.isna(txt):
        return None, None, None, None, None, 'vazio'
    t = str(txt).replace('\n', ' ').strip()
    if PAT_RUIDO.match(t) or len(t) < 10:
        return None, None, None, None, None, 'ruido'

    prod_found, prod_start, prod_end = None, None, None
    for p in produtos:
        idx = t.find(p)
        if idx >= 0 and (prod_start is None or idx < prod_start):
            prod_found, prod_start, prod_end = p, idx, idx + len(p)

    if prod_start is not None:
        servico = t[:prod_start].strip()
        resto   = t[prod_end:].strip()
    else:
        s = PAT_ID_GOVBR.sub('', t).strip()
        return s or None, None, None, None, None, 'sem_produto'

    sub_found, sub_end = None, 0
    for s in subeixos:
        idx = resto.find(s)
        if idx >= 0 and (sub_end == 0 or idx < sub_end):
            sub_found, sub_end = s, idx + len(s)

    area_data = resto[sub_end:].strip() if sub_found else resto
    dts       = list(PAT_DATA.finditer(area_data))
    data_ptd  = dts[-1].group() if dts else None
    area      = area_data[:area_data.rfind(data_ptd)].strip() if data_ptd else area_data.strip()
    area      = area[:500] if area else area
    servico   = PAT_ID_GOVBR.sub('', servico).strip()

    if not servico:
        return None, prod_found, sub_found, area or None, data_ptd, 'sem_servico'
    return servico, prod_found, sub_found, area or None, data_ptd, 'ok'


# ── Testes de parse_linha ─────────────────────────────────────────────────────

class TestParseLinha:

    def test_linha_completa(self):
        txt = ('Consultar débitos Disponibilização em Acesso Digital '
               'Serviços Digitais Gestão Digital jun/25')
        servico, produto, subeixo, area, data, flag = _parse_linha(txt)
        assert flag == 'ok'
        assert 'Consultar débitos' in servico
        assert produto == 'Disponibilização em Acesso Digital'
        assert subeixo == 'Serviços Digitais'
        assert data == 'jun/25'

    def test_sem_produto(self):
        txt = 'Emitir certidão negativa de débitos sem produto reconhecido'
        _, produto, _, _, _, flag = _parse_linha(txt)
        assert flag == 'sem_produto'
        assert produto is None

    def test_vazio(self):
        import numpy as np
        resultado = _parse_linha(np.nan)
        assert resultado[-1] == 'vazio'

    def test_ruido_cabecalho(self):
        txt = 'Serviço Digital descrição xyz'
        _, _, _, _, _, flag = _parse_linha(txt)
        assert flag == 'ruido'

    def test_texto_curto_ruido(self):
        _, _, _, _, _, flag = _parse_linha('abc')
        assert flag == 'ruido'

    def test_sem_servico(self):
        # Produto aparece no início — sem serviço antes
        txt = 'Login Único Serviços Digitais Área X jun/25'
        servico, produto, _, _, _, flag = _parse_linha(txt)
        assert flag == 'sem_servico'
        assert servico is None
        assert produto == 'Login Único'

    def test_area_truncada_em_500(self):
        # Área muito longa deve ser truncada em 500 chars
        area_longa = 'X' * 1000
        txt = f'Meu Serviço Disponibilização em Acesso Digital {area_longa} jun/25'
        _, _, _, area, _, flag = _parse_linha(txt)
        if area is not None:
            assert len(area) <= 500

    def test_id_govbr_removido(self):
        # IDs numéricos tipo "12345 Serviço" devem ser removidos
        txt = '12345 Serviço Consultar débitos Disponibilização em Acesso Digital Serviços Digitais jun/25'
        servico, _, _, _, _, flag = _parse_linha(txt)
        assert flag == 'ok'
        assert not servico.startswith('12345')

    def test_data_variados_formatos(self):
        # Formatos suportados pelo PAT_DATA
        # Nota: texto não pode começar com "Serviço" (PAT_RUIDO)
        formatos = ['jun/25', 'jun/2025', '06/2025', '2TRIM25', 'Jun-2025']
        for fmt in formatos:
            txt = f'Emitir certidão Disponibilização em Acesso Digital Serviços Digitais {fmt}'
            _, _, _, _, data, flag = _parse_linha(txt)
            assert data is not None, f'data não detectada para formato: {fmt}'

    def test_data_trimestre_barra(self):
        # FIX: formato "2T/2025" antes não era capturado
        formatos = ['2T/2025', '3T/25', '1T2026', '4Q/2025']
        for fmt in formatos:
            txt = f'Emitir certidão Disponibilização em Acesso Digital Serviços Digitais {fmt}'
            _, _, _, _, data, flag = _parse_linha(txt)
            assert data is not None, f'data não detectada para trimestre: {fmt}'

    def test_data_mes_extenso(self):
        # FIX: nomes completos de mês antes não eram capturados
        formatos = ['março de 2025', 'janeiro/2026', 'outubro 2025']
        for fmt in formatos:
            txt = f'Emitir certidão Disponibilização em Acesso Digital Serviços Digitais {fmt}'
            _, _, _, _, data, flag = _parse_linha(txt)
            assert data is not None, f'data não detectada para mês extenso: {fmt}'

    def test_data_ano_isolado(self):
        # Ano isolado deve ser capturado como último recurso
        txt = 'Emitir certidão Disponibilização em Acesso Digital Serviços Digitais 2025'
        _, _, _, _, data, _ = _parse_linha(txt)
        assert data is not None

    def test_multiplos_produtos_pega_primeiro(self):
        # Quando dois produtos estão no texto, deve pegar o de menor índice
        # Nota: texto NÃO pode começar com "Serviço" (seria capturado por PAT_RUIDO)
        txt = ('Consultar débitos Login Único e também '
               'Disponibilização em Acesso Digital Serviços Digitais jun/25')
        _, produto, _, _, _, flag = _parse_linha(txt)
        assert flag == 'ok'
        assert produto == 'Login Único'


# ── Testes de classificar_tipo_entrega ───────────────────────────────────────

def _classificar(produto='', texto='', mand_prod=MAND_PROD_MOCK):
    row = {'produto': produto, 'texto': texto}
    if produto in mand_prod:
        return 'mandatorio_ppsi'
    if 'Login Único' in produto or 'login único' in produto:
        return 'mandatorio_login'
    if re.search(r'avalia[çc][aã]o da satisfa[çc][aã]o', texto, re.I):
        return 'mandatorio_avaliacao'
    if re.search(r'Revis[aã]o da descri[çc][aã]o dos servi[çc]os', texto):
        return 'mandatorio_revisao'
    return 'discricionario'


class TestClassificarTipoEntrega:

    def test_mandatorio_ppsi(self):
        assert _classificar(produto='Plano de Segurança da Informação (PPSI)') == 'mandatorio_ppsi'

    def test_mandatorio_login(self):
        assert _classificar(produto='Login Único') == 'mandatorio_login'
        assert _classificar(produto='login único') == 'mandatorio_login'

    def test_mandatorio_avaliacao(self):
        assert _classificar(texto='Avaliação da satisfação do usuário') == 'mandatorio_avaliacao'
        assert _classificar(texto='avaliação da satisfação') == 'mandatorio_avaliacao'

    def test_mandatorio_revisao(self):
        assert _classificar(texto='Revisão da descrição dos serviços digitais') == 'mandatorio_revisao'

    def test_discricionario(self):
        assert _classificar(produto='Disponibilização em Acesso Digital',
                            texto='Emitir certidão negativa') == 'discricionario'


# ── Testes de corrigir_eixo (state machine reset) ────────────────────────────

def _build_corretores_mock(regras):
    compiled = []
    for r in regras:
        excecoes = [re.compile(p, re.I) for p in r.get('excecoes_manter_e3', [])]
        compiled.append({
            'sigla': r['sigla'], 'eixo_errado': r['eixo_errado'],
            'eixo_correto': r['eixo_correto'], 'excecoes': excecoes,
            'pagina': r.get('pagina'),
        })
    return compiled

def _corrigir_eixo(row, corretores):
    eixo = row['eixo_num']
    for c in corretores:
        if row.get('sigla') != c['sigla']:
            continue
        if eixo != c['eixo_errado']:
            continue
        if c['pagina'] and row.get('pagina') != c['pagina']:
            continue
        txt = str(row.get('texto', '') or '')
        if any(p.search(txt) for p in c['excecoes']):
            return eixo
        return c['eixo_correto']
    return eixo

REGRA_PGFN = {
    'id': 'PGFN-E3-PAG8-2025',
    'sigla': 'PGFN',
    'eixo_errado': 3,
    'eixo_correto': 1,
    'pagina': 8,
    'excecoes_manter_e3': [r'sumariza', r'SAJ.*IA', r'intelig.*artificial'],
    'n_registros_afetados': 21,
}
CORRETORES_MOCK = _build_corretores_mock([REGRA_PGFN])


class TestCorrigirEixo:

    def test_correcao_basica(self):
        row = {'sigla': 'PGFN', 'eixo_num': 3, 'pagina': 8,
               'texto': 'Regularizar débito junto à PGFN'}
        assert _corrigir_eixo(row, CORRETORES_MOCK) == 1

    def test_excecao_saj_ia(self):
        row = {'sigla': 'PGFN', 'eixo_num': 3, 'pagina': 8,
               'texto': 'SAJ/IA análise automática de processos'}
        assert _corrigir_eixo(row, CORRETORES_MOCK) == 3  # mantém E3

    def test_excecao_sumariza(self):
        row = {'sigla': 'PGFN', 'eixo_num': 3, 'pagina': 8,
               'texto': 'sumarização de documentos'}
        assert _corrigir_eixo(row, CORRETORES_MOCK) == 3

    def test_excecao_inteligencia_artificial(self):
        row = {'sigla': 'PGFN', 'eixo_num': 3, 'pagina': 8,
               'texto': 'inteligência artificial aplicada'}
        assert _corrigir_eixo(row, CORRETORES_MOCK) == 3

    def test_pagina_errada_nao_corrige(self):
        row = {'sigla': 'PGFN', 'eixo_num': 3, 'pagina': 5,
               'texto': 'Regularizar débito'}
        assert _corrigir_eixo(row, CORRETORES_MOCK) == 3  # não aplica regra

    def test_sigla_diferente_nao_corrige(self):
        row = {'sigla': 'ANPD', 'eixo_num': 3, 'pagina': 8,
               'texto': 'Regularizar débito'}
        assert _corrigir_eixo(row, CORRETORES_MOCK) == 3

    def test_eixo_correto_nao_altera(self):
        row = {'sigla': 'PGFN', 'eixo_num': 1, 'pagina': 8,
               'texto': 'Qualquer texto'}
        assert _corrigir_eixo(row, CORRETORES_MOCK) == 1

    def test_sem_regras_nao_altera(self):
        row = {'sigla': 'PGFN', 'eixo_num': 3, 'pagina': 8,
               'texto': 'Regularizar débito'}
        assert _corrigir_eixo(row, []) == 3  # sem corretores = sem alteração
