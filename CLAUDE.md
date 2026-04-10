# CLAUDE.md — PTD-BR Pipeline

Guia para assistentes de IA trabalhando neste repositório.

## O que é este projeto

Pipeline autônomo de extração e estruturação dos **Planos de Trabalho Departamental (PTD)**
de órgãos do Governo Federal Brasileiro. Processa ~130 PDFs de ~90 órgãos e produz um
corpus analítico estruturado com entregas, produtos, eixos EFGD e riscos.

**Stack**: Python 3.10+, Docling, pytesseract, pandas, Aho-Corasick, GitHub Actions.

---

## Arquitetura em 3 camadas

```
L1+L2  ptd_pipeline_v30.py    Scraping → Download → Extração de tabelas → col_map
L3     ptd_corpus_v21.py      Classificação semântica via Aho-Corasick
       gerar_relatorio.py     Sensor: HTML + ptd_run_summary.json (diagnóstico para IA)
```

O loop de aprendizado autônomo é gerenciado por `.github/workflows/watcher.yml`, que roda
a cada 5 minutos, lê o diagnóstico do último run e aplica fixes parametrizados.

### Arquitetura VSM (Viable System Model) — Nível 0

| Sistema | Implementação | Status |
|---------|--------------|--------|
| S1 — Operações | pipeline por órgão/PDF | ✅ |
| S2 — Coordenação | `config/` + `s3_meta_parameters.json` | ✅ |
| S3 — Gestão | `watcher.yml` + `gerar_dashboard_s3.py` | ✅ |
| S3* — Auditoria | `gerar_relatorio.py` + doc_coverage | ✅ |
| S4 — Inteligência | `meta_learning.py` + `ptd_learning_signals.json` | ⚠ acumulando |
| S5 — Política | operador + thresholds em `s3_meta_parameters.json` | ✅ |

### Recursão VSM — 3 Níveis (Beer)

> "Um sistema viável contém sistemas viáveis e está contido por sistemas viáveis."

```
Nível +1 (pipeline como S1 do IPEA)
  S5: mandato de pesquisa IPEA
  S4: inteligência sobre transformação digital federal
  S3: gestão COGIT/DIEST
  S1: PTD-BR Pipeline ← somos nós

Nível 0 (pipeline — atual)
  S5: config/s3_meta_parameters.json + operador (pct_ok ≥ 90%)
  S4: meta_learning.py + ptd_learning_signals.json
  S3: watcher.yml + gerar_dashboard_s3.py
  S3*: gerar_relatorio.py
  S2: config/ (vocab global, col_keys, correções)
  S1: extração por órgão (90 unidades S1)

Nível -1 (por-órgão — implementado em 2026-04-06)
  S5: config/org_meta.json (meta própria, exclusão, prioridade por sigla)
  S4: per_sigla_strategy em meta_learning.py → estratégia por órgão
  S3: slope per-sigla monitorado por _stalled_siglas()
  S3*: vsm_status, vsm_gap_pp, vsm_prioridade em por_orgao do run_summary
  S2: col_keys_extra[sigla] (config/col_keys_extra.json)
  S1: extração por PDF individual dentro do órgão
```

**`config/org_meta.json`** — S5 por órgão (Nível -1):
- `status`: `ativo` | `excluir` — órgãos excluídos não bloqueiam Stage 0 nem alimentam vocab
- `s5_pct_ok_meta`: meta individual de pct_ok (padrão: 80%)
- `estrategia`: `vocabulario` | `col_keys` | `ocr` — estratégia prioritária por órgão
- `prioridade`: `alta` | `media` | `normal` | `nenhuma`
- `_default`: política padrão aplicada a órgãos sem entrada explícita

---

## Executar localmente

```bash
# Instalar dependências
pip install -r requirements.txt
apt-get install tesseract-ocr tesseract-ocr-por   # OCR para PDFs-imagem

# Layer 1-2: extração (coleta scraping → CSV bruto)
python ptd_pipeline_v30.py

# Com opções:
python ptd_pipeline_v30.py --force-download       # limpa checkpoints, reprocessa tudo
python ptd_pipeline_v30.py --siglas AGU,FUNAI,ITI # filtra por órgão (modo debug)
python ptd_pipeline_v30.py --skip-download        # usa PDFs já baixados
python ptd_pipeline_v30.py --max-pdfs 10          # limita a N PDFs

# Layer 3: curadoria semântica (CSV bruto → corpus classificado)
python ptd_corpus_v21.py

# Validar ambiente
python ptd_healthcheck.py

# Smoke test (3 PDFs)
python ptd_test_pipeline.py --local
```

---

## Estrutura de arquivos

### Python — o que cada arquivo faz

| Arquivo | Papel |
|---------|-------|
| `ptd_pipeline_v30.py` | L1+L2: coleta, download, sanity, extração Docling/OCR, col_map, export |
| `ptd_corpus_v21.py` | L3: parser Aho-Corasick, parse_flag, correção de eixos, export corpus |
| `ptd_ocr_fallback.py` | OCR via pytesseract para PDFs-imagem; `OCR_CONFIG` por sigla |
| `gerar_relatorio.py` | Sensor: HTML dashboard + `ptd_run_summary.json` para o watcher |
| `ptd_constants.py` | **Fonte única de verdade**: eixos EFGD, padrões regex, diretórios |
| `ptd_healthcheck.py` | Valida ambiente: deps, Tesseract, configs, outputs (exit 0/1) |
| `ptd_test_pipeline.py` | Smoke test em 3 PDFs representativos |
| `gerar_apresentacao.py` | Gera PPTX do corpus |

### Config — o que cada arquivo controla

| Arquivo | Quando editar |
|---------|--------------|
| `config/produtos_sgd_v23.json` | Novo ciclo PTD ou vocabulário insuficiente. **Ordem importa**: mais específico primeiro. Pode ser auto-expandido pelo watcher. |
| `config/correcoes_eixo.json` | Nova auditoria manual de contaminação de eixo. Documenta causa, n_registros, exceções. |
| `config/col_keys_extra.json` | Keywords extras de colunas por sigla (gerado dinamicamente pelo watcher no futuro). |
| `config/revisoes_manuais.csv` | Overrides manuais de parse para linhas específicas (por pdf_sha256 + posição). |

### GitHub Actions

| Workflow | Trigger | Função |
|----------|---------|--------|
| `pipeline.yml` | push em `.trigger_debug` ou manual | Executa extração (debug ~20min / completo ~4h) |
| `watcher.yml` | cron `*/5 * * * *` | Loop autônomo: monitora → classifica → trata → re-dispara |
| `healthcheck.yml` | push em `.py` ou `requirements.txt` | CI: pytest + healthcheck |

### Diretórios de output (gerados, não commitar)

```
ptd_corpus/
  01_raw_pdfs/          PDFs baixados
  02_logs/              Logs + checkpoints JSONL (recovery)
  03_database/          CSVs e JSONs finais
```

---

## ⚠ Arquivos que NÃO devem ser editados manualmente

| Arquivo | Criado por | Risco se editar |
|---------|-----------|----------------|
| `.trigger_debug` | `ptd-watcher[bot]` | Quebra o loop autônomo |
| `ocr_states.json` | `watcher.yml` | State machine OCR perde estado |
| `ocr_config_dynamic.json` | `watcher.yml` | Gerado a cada iteração, sobrescrito |
| `ptd_ocr_fallback.py` (bloco `OCR_CONFIG`) | `watcher.yml` via regex | Watcher reescreve a cada ciclo |
| `ptd_corpus/02_logs/_checkpoint_*.jsonl` | pipeline | Se deletar, pipeline re-processa tudo |
| `.last_processed` (branch pipeline-outputs) | `watcher.yml` | Watcher reprocessa run já visto |

---

## Branch de desenvolvimento

**Branch ativo**: `claude/setup-docling-pipeline-g11gg`

O `watcher.yml` commita fixes neste branch automaticamente. Sempre rebase antes de push:

```bash
git pull origin claude/setup-docling-pipeline-g11gg --rebase
git push -u origin claude/setup-docling-pipeline-g11gg
```

O branch `pipeline-outputs` é **orphan** e contém apenas diagnósticos:
`ptd_run_summary.json`, `last_run.json`, `ocr_states.json`, `stage_status.json`.

---

## Secrets necessários

| Secret | Para que serve |
|--------|----------------|
| `WORKFLOW_PAT` | Watcher faz push com este token; `GITHUB_TOKEN` padrão não dispara outros workflows |

---

## Fluxo de dados completo

```
Portal gov.br → scraping URLs
    ↓
Download PDFs → ptd_corpus/01_raw_pdfs/
    ↓
Sanity check (tamanho, páginas, texto vs imagem)
    ↓
Extração Docling (ou pytesseract fallback)
    ↓ col_map: headers da tabela → campos semânticos (servico/produto/area/data)
    ↓ col_map_ok: bool por linha
    ↓
ptd_corpus_raw.csv  (parse_flag='raw' em tudo)
    ↓
ptd_corpus_v21.py: Aho-Corasick contra produtos_sgd_v23.json
    ↓
parse_flag: ok | sem_produto | sem_servico | ruido | vazio
    ↓
ptd_corpus_v21.csv          (corpus classificado)
ptd_revisao_pendente.csv    (parse_flag != ok — ~9.159 linhas, corpus de aprendizado do S4)
    ↓
gerar_relatorio.py → ptd_run_summary.json → watcher → próximo fix
```

---

## Convenções de código

- **Prefixo `ptd_`**: todos os outputs de dados
- **Prefixo `_`**: variáveis/funções internas ao módulo
- **Sufixo `_vN`**: versão (pipeline_v30, corpus_v21)
- **Constantes em MAIÚSCULA**: `EIXOS`, `PORTAL_BASE`, `DIR_RAW`, `OCR_CONFIG`
- **Logging**: `logger = logging.getLogger('ptd_pipeline')` — duplo handler (arquivo + stdout)
- **Formato de log**: `HH:MM:SS LEVELNAME-8s mensagem` (`datefmt='%H:%M:%S'`)
- **Constantes compartilhadas**: sempre importar de `ptd_constants.py`, nunca redefinir

---

## Loop cibernético autônomo (watcher)

O watcher classifica o problema **antes** de aplicar qualquer tratamento:

| `problem_type` | Condição | Ação |
|---------------|----------|------|
| `cobertura` | `orgaos_zero_ou_noise > 0` | Avança state machine OCR (DPI, rotação) |
| `vocabulario` | `sem_produto_pct > 20%` | Expande `config/produtos_sgd_v23.json` via `top_unmatched_phrases` |
| `qualidade` | pct_ok baixo sem cobertura | Escalação para revisão humana |

**Importante**: não modificar o bloco `OCR_CONFIG` em `ptd_ocr_fallback.py` manualmente
durante iterações ativas — o watcher sobrescreve a cada ciclo quando `problem_type=cobertura`.

O watcher **não toca em OCR quando o problema é vocabulário**. Essa separação é central.

---

## Diagnóstico rápido

```bash
# Ver último run e métricas
git fetch origin pipeline-outputs
git show origin/pipeline-outputs:ptd_run_summary.json | python3 -m json.tool

# Ver iteration counter
cat .trigger_debug

# Dashboard S3 (abre no browser)
python gerar_dashboard_s3.py && open ptd_corpus/03_database/ptd_dashboard_s3.html

# Relatório técnico completo
python gerar_relatorio_tecnico.py && open ptd_corpus/03_database/ptd_relatorio_tecnico_v1.html

# Ver log do último run (se artefato baixado)
grep -E 'ERROR|WARNING|extraídas|pct_ok' ptd_debug.log
```

---

## Estado atual (2026-04-06)

- **Iteração**: 166
- **Stage**: 0 — cobertura (noise-only: ABNT-NBR-1 excluído por S5; ANS-PLANO, MD, MDA-DOCUME, MEC ainda ativos)
- **pct_ok**: 75.5% (meta: ≥ 90%) · **sem_produto_pct**: 21.6%
- **Sensor**: `top_unmatched_por_sigla` operacional — watcher vê frases por órgão
- **S4**: `meta_learning.py` ativo · `ptd_learning_signals.json` acumulando · `per_sigla_strategy` implementado
- **S3**: `gerar_dashboard_s3.py` com card de recursão VSM · Sinal algedônico (Step E) ativo
- **S3\***: `doc_coverage` no `ptd_run_summary.json` · `vsm_status/gap/prioridade` por órgão
- **Nível -1 VSM**: `config/org_meta.json` criado — ABNT-NBR-1 marcado como `excluir`

### Arquitetura VSM — estado dos sistemas

| Sistema | Implementação | Status |
|---------|--------------|--------|
| S1 — Operações | `ptd_pipeline_v30.py` por órgão/PDF | ✅ `rows_por_sha256` no manifesto |
| S2 — Coordenação | `config/` + `config/s3_meta_parameters.json` | ✅ metaparâmetros centralizados |
| S3 — Gestão | `watcher.yml` · `gerar_dashboard_s3.py` | ✅ Step E (algedônico) + card VSM tree |
| S3\* — Auditoria | `gerar_relatorio.py` · `doc_coverage` · `vsm_gap_pp` por org | ✅ cobertura documental + nível -1 |
| S4 — Inteligência | `meta_learning.py` · `ptd_learning_signals.json` · `per_sigla_strategy` | ⚠ acumulando (pipeline precisa rodar) |
| S5 — Política | `s3_meta_parameters.json` + `config/org_meta.json` (por órgão) | ✅ nível -1 implementado |

### Próximos objetivos

1. **Stage 0 → 1**: ABNT-NBR-1 excluído; restam 4 noise-only (ANS-PLANO, MD, MDA-DOCUME, MEC)
2. **sem_produto_pct 21.6% → < 20%**: watcher expandir vocab via `top_unmatched_por_sigla` (já funcionando)
3. **S4 acumular histórico**: pipeline precisa rodar para `ptd_learning_signals.json` ter entradas
4. **doc_coverage**: verificar preservação após próximo run completo

Plano arquitetural completo: `.claude/plans/validated-doodling-stearns.md`

