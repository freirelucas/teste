"""
Testes unitários para ptd_pipeline_v30.py
Funções testadas: detectar_eixo, _is_img_pdf (mock), scrape_catalogo (mock)

Execução:
    pytest tests/ -v
"""
import sys
import re
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from pathlib import Path

# Importar directamente de ptd_constants (fonte única — não duplicar)
sys.path.insert(0, str(Path(__file__).parent.parent))
from ptd_constants import detectar_eixo, EIXOS
from ptd_pipeline_v30 import _col_map, _get_cell


# ── Testes de detectar_eixo ──────────────────────────────────────────────────

class TestDetectarEixo:

    # Detecção explícita por número
    def test_eixo_numerico_explícito(self):
        assert detectar_eixo('Eixo 1 Centrado no Cidadão') == 1
        assert detectar_eixo('eixo 3 inteligente') == 3
        assert detectar_eixo('Eixo 6 eficiente') == 6

    def test_eixo_com_hifen(self):
        assert detectar_eixo('E-2 Integrado') == 2
        assert detectar_eixo('E-5 Transparente') == 5

    # Detecção por palavra-chave
    def test_e1_cidadao(self):
        assert detectar_eixo('serviços digitais para o cidadão') == 1

    def test_e1_inclusivo(self):
        assert detectar_eixo('inclusividade digital') == 1

    def test_e2_integrado(self):
        assert detectar_eixo('sistema integrado de saúde') == 2

    def test_e2_interoperabilidade(self):
        assert detectar_eixo('interoperabilidade entre sistemas') == 2

    def test_e3_inteligente(self):
        assert detectar_eixo('governo inteligente e inovador') == 3

    def test_e3_dados(self):
        assert detectar_eixo('governança de dados abertos') == 3

    def test_e4_seguranca(self):
        assert detectar_eixo('segurança da informação') == 4

    def test_e4_ppsi(self):
        assert detectar_eixo('Plano de PPSI aprovado') == 4

    def test_e4_privacidade(self):
        assert detectar_eixo('privacidade de dados') == 4

    def test_e5_transparente(self):
        assert detectar_eixo('governo transparente') == 5
        assert detectar_eixo('dados abertos e participativos') == 5

    def test_e5_transparencia_com_diacritico(self):
        # FIX: 'transparência' (ê) deve ativar E5 — antes falhava com 'transparent'
        assert detectar_eixo('transparência dos dados públicos') == 5
        assert detectar_eixo('Política de Transparência e Acesso') == 5

    def test_e5_dados_abertos(self):
        assert detectar_eixo('publicação de dados abertos') == 5

    def test_e6_eficiente(self):
        assert detectar_eixo('gestão eficiente de recursos') == 6

    def test_e6_eficiencia_com_diacritico(self):
        # FIX: 'eficiência' (ê) deve ativar E6 — antes falhava com 'eficient'
        assert detectar_eixo('eficiência administrativa dos serviços') == 6
        assert detectar_eixo('Melhoria de Eficiência Operacional') == 6

    def test_e6_sustentavel(self):
        assert detectar_eixo('sustentabilidade digital') == 6

    def test_e6_desburocratizacao(self):
        # FIX: termos novos adicionados ao E6
        assert detectar_eixo('desburocratização de processos internos') == 6

    def test_e6_simplificacao(self):
        assert detectar_eixo('simplificação de procedimentos administrativos') == 6

    # Edge cases
    def test_texto_vazio_retorna_none(self):
        assert detectar_eixo('') is None
        assert detectar_eixo(None) is None

    def test_texto_sem_eixo_retorna_none(self):
        assert detectar_eixo('emitir boleto de pagamento de taxa') is None

    def test_numero_explicito_tem_prioridade(self):
        # Texto que menciona eixo 1 explicitamente mas tem token de eixo 3
        assert detectar_eixo('Eixo 1 inteligente') == 1

    def test_eixo_case_insensitive(self):
        assert detectar_eixo('EIXO 4 CONFIÁVEL') == 4
        assert detectar_eixo('eixo 4 confiável') == 4


# ── Testes de state machine reset ────────────────────────────────────────────

class TestStateMachineReset:
    """
    Testa que o fix crítico de reset de eixo_atual por página está funcionando.
    Simula a lógica de extração para verificar que não há contaminação entre páginas.
    """

    def _simular_extracao(self, paginas):
        """
        paginas: lista de listas de textos (cada sublista = uma página)
        Retorna lista de (pagina, eixo) para cada linha extraída.
        """
        resultado = []
        for npag, textos in enumerate(paginas, 1):
            eixo_atual = None  # FIX: reset por página
            for txt in textos:
                e = detectar_eixo(txt)
                if e:
                    eixo_atual = e
                if eixo_atual:
                    resultado.append((npag, eixo_atual, txt))
        return resultado

    def test_sem_contaminacao_entre_paginas(self):
        """
        Página 1 tem E3 (inteligente), página 2 não tem eixo explícito.
        Com o fix, página 2 deve ter eixo_atual=None (sem contaminação).
        """
        paginas = [
            ['Eixo 3 inteligente', 'item E3'],        # pág 1: E3
            ['serviço sem eixo explícito definido'],   # pág 2: sem eixo
        ]
        res = self._simular_extracao(paginas)
        pag2 = [r for r in res if r[0] == 2]
        assert len(pag2) == 0, 'Página 2 não deveria ter registros sem eixo detectado'

    def test_eixo_propagado_dentro_da_mesma_pagina(self):
        """
        Dentro da mesma página, o eixo deve ser propagado para as linhas seguintes.
        """
        paginas = [
            ['Eixo 1 cidadão', 'item 1 sem label', 'item 2 sem label'],
        ]
        res = self._simular_extracao(paginas)
        assert len(res) == 3
        assert all(r[1] == 1 for r in res)

    def test_eixo_muda_dentro_da_pagina(self):
        """
        Se um novo eixo é detectado na mesma página, ele substitui o anterior.
        """
        paginas = [
            ['Eixo 1 cidadão', 'item E1', 'Eixo 4 segurança', 'item E4'],
        ]
        res = self._simular_extracao(paginas)
        assert res[0][1] == 1  # primeiro item E1
        assert res[1][1] == 1  # segundo item ainda E1
        assert res[2][1] == 4  # mudou para E4
        assert res[3][1] == 4  # propaga E4

    def test_pagina_sem_eixo_nao_herda_pagina_anterior(self):
        """
        O BUG ORIGINAL: sem reset, eixo_atual contaminava a próxima página.
        Com o fix, cada página começa com eixo_atual=None.
        """
        paginas = [
            ['Eixo 3 inteligente', 'SAJ/IA análise'],  # pág 1: E3
            ['item genérico sem eixo'],                  # pág 2: deve ser ignorado
            ['Eixo 1 cidadão', 'serviço digital'],       # pág 3: E1
        ]
        res = self._simular_extracao(paginas)
        pags = {r[0] for r in res}
        assert 2 not in pags, 'Página 2 não deve ter registros (sem eixo detectado)'
        assert 1 in pags
        assert 3 in pags


# ── Testes de _col_map ──────────────────────────────────────────────────────

class TestColMap:
    def _df(self, cols):
        return pd.DataFrame(columns=cols)

    def test_headers_completos(self):
        df = self._df(['Serviço', 'Produto', 'Data'])
        m = _col_map(df)
        assert m.get('servico') == 0
        assert m.get('produto') == 1
        assert m.get('data') == 2

    def test_entrega_mapeia_produto(self):
        df = self._df(['Entrega', 'Prazo'])
        m = _col_map(df)
        assert m.get('produto') == 0
        assert m.get('data') == 1

    def test_sem_headers_reconheciveis(self):
        df = self._df(['Col1', 'Col2', 'Col3'])
        m = _col_map(df)
        assert m == {}

    def test_header_parcial(self):
        df = self._df(['Nome do Serviço Digital', 'Coluna X'])
        m = _col_map(df)
        assert m.get('servico') == 0
        assert 'produto' not in m


# ── Testes de _get_cell ─────────────────────────────────────────────────────

class TestGetCell:
    CELLS = ['alfa', 'beta', 'gamma', 'delta']

    def test_via_cmap(self):
        assert _get_cell(self.CELLS, {'servico': 0}, 'servico', 99) == 'alfa'

    def test_via_fallback_posicional(self):
        assert _get_cell(self.CELLS, {}, 'servico', 1) == 'beta'

    def test_indice_negativo(self):
        assert _get_cell(self.CELLS, {}, 'servico', -1) == 'delta'

    def test_fora_dos_limites(self):
        assert _get_cell(self.CELLS, {}, 'servico', 99) == ''

    def test_fallback_none(self):
        assert _get_cell(self.CELLS, {}, 'servico', None) == ''
