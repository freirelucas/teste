# TAROT CIBERQUILOMBOLA

**Diagnóstico sistêmico cruzando o VSM de Stafford Beer com o pensamento quilombola de Antônio Bispo dos Santos.**

> "The purpose of a system is what it does." — Stafford Beer
>
> "A terra não é uma só. Cada terra tem seu jeito de ser terra." — Antônio Bispo dos Santos

## O que é

O Tarot CiberQuilombola **não é adivinhação — é diagnóstico**. Usa os 22 Arcanos Maiores como lentes cibernéticas para examinar sistemas (organizações, projetos, comunidades, relações). Cada carta mapeia a um conceito real da cibernética organizacional de Beer, entrelaçado com o pensamento quilombola de Nego Bispo.

## Funciona sem backend

- 100% no browser via GitHub Pages
- Zero dependências proprietárias (React + Vite + Zustand, todos MIT)
- Dados abertos em `cards.json` — reutilizável por qualquer projeto
- Interpretação local funciona offline
- API da Anthropic é opcional (graceful degradation)

## Modos de leitura

| Modo | Cartas | Descrição |
|------|--------|-----------|
| Diagnóstico Pessoal | 3 | Situação, obstáculo, caminho |
| Modelo de Sistema Viável | 5 | Mapeado a S1–S5 de Beer |
| Sintegridade | 12 | Estrutura icosaédrica não-hierárquica |
| Plataforma para Mudança | 13 | Diagnóstico completo de organização |
| Sinal Algedônico | 1 | Dor ou prazer? Direto ao ponto. |

## Rodar localmente

```bash
npm install
npm run dev
```

Para usar com IA (opcional):
```bash
echo "VITE_ANTHROPIC_API_KEY=sk-ant-..." > .env
npm run dev
```

## Estrutura do Tarot

```
src/
  data/
    cards.json        22 Arcanos Maiores com dados reais de Beer/Bispo
    spreads.json      5 modos de leitura
  components/
    Card/             Carta com flip animation e verso Cybersyn
    Shell/            Interface terminal (header, nav, footer)
    Spread/           Layout de cartas por modo
    Reading/          Interpretação (local ou IA)
  store/
    useReadingStore   Estado da tiragem ativa
    useHistoryStore   Histórico persistido em LocalStorage
  services/
    interpret.js      Anthropic API + fallback local
  styles/
    tokens.css        Design tokens (palette Cybersyn)
    base.css          Reset + tipografia IBM Plex Mono
```

## Referências

- Beer, S. (1972). *Brain of the Firm*. Allen Lane.
- Beer, S. (1985). *Diagnosing the System for Organizations*. Wiley.
- Beer, S. (1975). *Platform for Change*. Wiley.
- Beer, S. (1994). *Beyond Dispute: The Invention of Team Syntegrity*. Wiley.
- Santos, A. B. (2015). *Colonização, Quilombos: Modos e Significações*. INCTI/UnB.

## Contribuir

Contribuições são bem-vindas. Veja `docs/minor-arcana-spec.md` para a especificação dos 56 Arcanos Menores (próxima fase). Abra uma issue para discutir antes de submeter um PR.

## Licença

Código: MIT. Dados (`cards.json`, `spreads.json`): CC-BY-SA 4.0.

---

# PTD-BR — Corpus de Planos de Transformação Digital

**IPEA / COGIT / DIEST**
Autores: Denise do Carmo Direito · Lucas Freire Silva
Versão: 3.0-melhorado · Base legal: Decreto nº 12.198/2024 · Portaria SGD/MGI nº 6.618/2024

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/freirelucas/teste/blob/claude/setup-docling-pipeline-g11gg/PTD_BR_Corpus_Colab.ipynb)
[![Healthcheck](https://github.com/freirelucas/teste/actions/workflows/healthcheck.yml/badge.svg)](https://github.com/freirelucas/teste/actions/workflows/healthcheck.yml)

> Documento de trabalho — não citar sem autorização dos autores.

---

## O que é

Pipeline completo de coleta, extração e estruturação dos **Planos de Transformação Digital (PTDs)** da Administração Pública Federal (90 órgãos, ciclo 2025–2027), publicados no Portal do Governo Digital (SGD/MGI).

Produz dois corpus estruturados:
- **Corpus de Entregas** — 5.825+ metas digitais por eixo da EFGD 2024–2027
- **Corpus de Riscos** — matrizes de gestão de risco dos Documentos Diretivos

## Arquitetura

```
Layer 1-2  ptd_pipeline_v30.py   Coleta + Extração (PDF → CSV)
Layer 3    ptd_corpus_v21.py     Curadoria semântica (CSV → corpus analítico)
Config     config/               Taxonomias e regras de auditoria versionadas
```

## Pré-requisitos

```bash
# Python 3.10+
pip install -r requirements.txt

# Para PDFs de imagem (tarjados):
apt-get install -y tesseract-ocr tesseract-ocr-por
```

## Execução

### Layer 1-2 — Extração (rode primeiro)

```bash
python ptd_pipeline_v30.py
```

**Outputs em `ptd_corpus/03_database/`:**

| Arquivo | Descrição |
|---------|-----------|
| `ptd_corpus_raw.csv` | Corpus bruto de entregas com `pdf_sha256` |
| `ptd_pivot_eixos.csv` | Pivot sigla × eixo — **input obrigatório Layer 3** |
| `ptd_datas_assinatura.csv` | Datas por PDF — **input obrigatório Layer 3** |
| `ptd_riscos.csv` | Matriz de riscos com categorias ordinais |
| `ptd_acoes_dict.csv` | Dicionário de ações de tratamento |
| `ptd_riscos_acoes.csv` | Bridge risco × ação |
| `proveniencia.json` | Metadados completos de proveniência |
| `pipeline_manifest.json` | SHA-256 de todos os PDFs processados |

Logs em `ptd_corpus/02_logs/`: download, sanity checks, extração, checkpoints.

### Layer 3 — Curadoria (rode após Layer 1-2)

```bash
python ptd_corpus_v21.py
```

**Outputs adicionais:**

| Arquivo | Descrição |
|---------|-----------|
| `ptd_corpus_v21.csv` | Corpus enriquecido: `servico`, `produto`, `subeixo`, `area`, `data_ptd`, `parse_flag`, `tipo_entrega`, `eixo_num_corrigido`, `ia_real` |
| `ptd_corpus_v21_metadados.json` | Estatísticas, hashes de input, regras aplicadas |

### Gerar apresentação

```bash
python gerar_apresentacao.py
# → apresentacao_ptd_corpus.pptx (10 slides)
```

## Unidade de análise

Cada linha do corpus = **1 comprometimento = 1 serviço × 1 produto**.
Um mesmo serviço pode pactar N produtos → N linhas.
Média observada: ~2,07 produtos/serviço (54 diretivos).
Design intencional do template v2.3 SGD — não é ruído.

## Configuração

Editar sem alterar código Python:

| Arquivo | Quando atualizar |
|---------|-----------------|
| `config/produtos_sgd_v23.json` | Novo ciclo PTD com template SGD atualizado |
| `config/correcoes_eixo.json` | Nova auditoria manual identificar contaminação de eixo |

## Reprodutibilidade

- Todos os PDFs têm SHA-256 registrado em `pipeline_manifest.json`
- CSVs de input do Layer 3 têm SHA-256 validados na carga (`input_hashes` no metadados JSON)
- Checkpoints JSONL em `02_logs/` permitem retomar extração interrompida

## Estrutura de diretórios

```
ptd_corpus/
  01_raw_pdfs/          PDFs baixados do portal
  02_logs/              Logs, checkpoints, sanity checks
  03_database/          Outputs estruturados (CSV, JSON, Parquet)
config/
  produtos_sgd_v23.json Taxonomia de produtos SGD v2.3
  correcoes_eixo.json   Regras de correção de eixo (auditoria manual)
ptd_pipeline_v30.py     Layer 1-2: coleta e extração
ptd_corpus_v21.py       Layer 3: curadoria semântica
gerar_apresentacao.py   Gerador de apresentação PPTX
requirements.txt        Dependências Python
```

## Fixes v3.0-melhorado vs versão anterior

| Severidade | Problema original | Correção |
|---|---|---|
| 🔴 Crítico | State machine sem reset por página (21 registros PGFN E3→E1 errado) | `eixo_atual = None` a cada nova página |
| 🔴 Crítico | 100/120 URLs com 404 (CATALOGO hardcoded) | Scraping dinâmico do portal HTML |
| 🟡 Médio | `PRODUTOS` e regras de correção hardcoded | Externalizados em `config/` |
| 🟠 Menor | Sem rastreabilidade PDF→registro | `pdf_sha256` por linha + `pipeline_manifest.json` |
| 🟠 Menor | Layer 3 sem inputs (pivot/datas) gerados pelo Layer 2 | `ptd_pivot_eixos.csv` e `ptd_datas_assinatura.csv` gerados no ETAPA 6 |