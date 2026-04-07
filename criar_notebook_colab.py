"""Gera PTD_BR_Corpus_Colab.ipynb usando nbformat."""
import nbformat as nbf

nb = nbf.v4.new_notebook()
nb.metadata = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.10.0"},
    "colab": {"name": "PTD_BR_Corpus_Colab.ipynb", "provenance": []}
}

def md(src):  return nbf.v4.new_markdown_cell(src)
def code(src): return nbf.v4.new_code_cell(src)

REPO = "https://github.com/freirelucas/teste"
BRANCH = "claude/setup-docling-pipeline-g11gg"

# ── CÉLULA 1 — Capa ───────────────────────────────────────────────────
nb.cells.append(md(f"""# PTD-BR Corpus — Pipeline Completo
## Planos de Transformação Digital do Governo Federal Brasileiro

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/freirelucas/teste/blob/{BRANCH}/PTD_BR_Corpus_Colab.ipynb)
&nbsp;
[![GitHub](https://img.shields.io/badge/GitHub-freirelucas%2Fteste-blue?logo=github)](https://github.com/freirelucas/teste/tree/{BRANCH})

**IPEA / COGIT / DIEST**
Autores: Denise do Carmo Direito · Lucas Freire Silva
Base legal: Decreto nº 12.198/2024 · Portaria SGD/MGI nº 6.618/2024

---

### O que este notebook faz

Executa o pipeline completo de coleta e estruturação dos PTDs em **4 etapas**:

| Etapa | Descrição | Tempo estimado |
|-------|-----------|---------------|
| **Setup** | Clona repositório, instala dependências | ~5 min |
| **Layer 1-2** | Scraping do portal + download + extração via Docling | ~30–90 min |
| **Layer 3** | Curadoria semântica (parser, correção de eixo, IA) | ~1 min |
| **Relatório** | HTML autocontido + PPTX + download | ~1 min |

> **Dica:** Use *Runtime → Run all* para execução completa.
> PDFs são salvos no Google Drive se montado (célula 2).

---

### Unidade de análise
Cada linha = **1 comprometimento = 1 serviço × 1 produto** (média: 2,07 produtos/serviço).
"""))

# ── CÉLULA 2 — Setup e dependências ──────────────────────────────────
nb.cells.append(md("## Célula 1 — Setup do Ambiente"))
nb.cells.append(code("""\
import os, sys

# ── Clonar repositório ────────────────────────────────────────────────
REPO   = "https://github.com/freirelucas/teste"
BRANCH = "claude/setup-docling-pipeline-g11gg"
REPO_DIR = "/content/ptd_br"

if not os.path.exists(REPO_DIR):
    print("Clonando repositório...")
    os.system(f"git clone --branch {BRANCH} --depth 1 {REPO} {REPO_DIR}")
else:
    print("Repositório já clonado — atualizando...")
    os.system(f"cd {REPO_DIR} && git pull")

os.chdir(REPO_DIR)
print(f"Diretório: {os.getcwd()}")
print("Arquivos:", os.listdir("."))
"""))

nb.cells.append(code("""\
# ── Instalar dependências Python ──────────────────────────────────────
print("Instalando dependências (aguarde ~3 min)...")
import subprocess

# Remover conflito de versão do typer
subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "typer-slim"],
               capture_output=True)

subprocess.run([sys.executable, "-m", "pip", "install", "-q",
    "docling>=2.5", "docling-ibm-models",
    "pandas>=2.0", "numpy>=1.24", "pyarrow>=12", "openpyxl",
    "PyMuPDF>=1.23", "requests>=2.31", "beautifulsoup4>=4.12",
    "python-pptx>=1.0", "matplotlib>=3.7", "seaborn>=0.12",
    "typer==0.21.0"
], check=False)

print("✅ Dependências Python instaladas")
"""))

nb.cells.append(code("""\
# ── Tesseract OCR (PDFs tarjados/imagem) ─────────────────────────────
import subprocess
result = subprocess.run(["apt-get", "install", "-y", "-q",
                         "tesseract-ocr", "tesseract-ocr-por"],
                        capture_output=True, text=True)
if result.returncode == 0:
    print("✅ Tesseract + idioma 'por' instalados")
else:
    print("⚠️  Tesseract não instalado — PDFs tarjados não terão OCR")
    print(result.stderr[:200])
"""))

# ── CÉLULA 3 — Google Drive (opcional) ───────────────────────────────
nb.cells.append(md("## Célula 2 — Google Drive (opcional)\n\nMonte o Drive para persistir os PDFs e outputs entre sessões.\n**Se pular esta célula, os dados ficam apenas na sessão atual.**"))
nb.cells.append(code("""\
# ── Montar Google Drive (opcional) ───────────────────────────────────
USAR_DRIVE = False   # mude para True para persistir dados

if USAR_DRIVE:
    from google.colab import drive
    drive.mount('/content/drive')
    DRIVE_DIR = '/content/drive/MyDrive/PTD_BR_Corpus'
    import os
    os.makedirs(DRIVE_DIR, exist_ok=True)

    # Criar symlink para que o pipeline salve no Drive
    import os
    target = os.path.join(os.getcwd(), 'ptd_corpus')
    if not os.path.exists(target):
        os.symlink(DRIVE_DIR, target)
    print(f"✅ Drive montado — outputs em: {DRIVE_DIR}")
else:
    print("ℹ️  Drive não montado — dados ficam em /content/ptd_br/ptd_corpus/")
"""))

# ── CÉLULA 4 — Healthcheck ────────────────────────────────────────────
nb.cells.append(md("## Célula 3 — Verificação do Ambiente"))
nb.cells.append(code("""\
# ── Healthcheck — confirma que tudo está pronto ───────────────────────
import subprocess, sys
result = subprocess.run([sys.executable, "ptd_healthcheck.py"],
                        capture_output=False, text=True)
print("Código de saída:", result.returncode)
print("0 = pronto | 1 = há falhas críticas")
"""))

# ── CÉLULA 5 — Test mode ─────────────────────────────────────────────
nb.cells.append(md("""\
## Célula 4 — Test Mode (recomendado antes da extração completa)

Baixa 3 PDFs representativos e valida toda a pipeline em ~3 minutos.
**Execute esta célula antes da extração completa para confirmar que o ambiente está OK.**
"""))
nb.cells.append(code("""\
import subprocess, sys
result = subprocess.run([sys.executable, "ptd_test_pipeline.py", "--verbose"],
                        capture_output=False, text=True)
print("Código de saída:", result.returncode)
print("PASS=0 (pronto para extração completa) | FAIL=1 (corrigir antes)")
"""))

# ── CÉLULA 6 — Layer 1-2 ─────────────────────────────────────────────
nb.cells.append(md("""\
## Célula 5 — Layer 1-2: Extração Completa

Executa scraping do portal + download de ~90 PDFs + extração via Docling.

⏱️ **Tempo estimado:** 30–90 min (depende da velocidade da rede e disponibilidade do Docling/GPU)

O pipeline tem checkpoint incremental — se interrompido, retoma de onde parou.
"""))
nb.cells.append(code("""\
import subprocess, sys

print("Iniciando extração completa...")
print("Acompanhe o progresso abaixo:\\n")

# Rodar com output em tempo real
proc = subprocess.Popen(
    [sys.executable, "ptd_pipeline_v30.py"],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    text=True, bufsize=1
)
for line in proc.stdout:
    print(line, end='', flush=True)
proc.wait()
print(f"\\nCódigo de saída: {proc.returncode}")
"""))

# ── CÉLULA 7 — Layer 3 ───────────────────────────────────────────────
nb.cells.append(md("""\
## Célula 6 — Layer 3: Curadoria Semântica

Parser de campos, correção de eixo E3, classificação mandatório/discricionário, flag IA real.
**~1 minuto.**
"""))
nb.cells.append(code("""\
import subprocess, sys
proc = subprocess.Popen(
    [sys.executable, "ptd_corpus_v21.py"],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
)
for line in proc.stdout:
    print(line, end='', flush=True)
proc.wait()
print(f"\\nCódigo de saída: {proc.returncode}")
"""))

# ── CÉLULA 8 — Relatório + validação ─────────────────────────────────
nb.cells.append(md("## Célula 7 — Relatório de Qualidade e Validação"))
nb.cells.append(code("""\
import subprocess, sys
subprocess.run([sys.executable, "gerar_relatorio.py"], check=False)
subprocess.run([sys.executable, "gerar_apresentacao.py"], check=False)

# Verificar outputs
from pathlib import Path
DIR_DB = Path("ptd_corpus/03_database")
print("\\n" + "="*50)
print("OUTPUTS GERADOS:")
for f in sorted(DIR_DB.glob("*.*")):
    print(f"  {f.name:40s} {f.stat().st_size//1024:5d} KB")

# Healthcheck dos outputs
subprocess.run([sys.executable, "ptd_healthcheck.py", "--outputs"], check=False)
"""))

# ── CÉLULA 9 — Visualização inline ────────────────────────────────────
nb.cells.append(md("## Célula 8 — Visualização do Corpus (inline)"))
nb.cells.append(code("""\
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

DIR_DB = Path("ptd_corpus/03_database")

corpus_path = DIR_DB / "ptd_corpus_v21.csv"
if not corpus_path.exists():
    corpus_path = DIR_DB / "ptd_corpus_raw.csv"

corpus = pd.read_csv(corpus_path)
print(f"Corpus: {len(corpus):,} linhas × {len(corpus.columns)} colunas")
print(f"Órgãos: {corpus['sigla'].nunique()}")

EIXOS = {1:'Centrado no Cidadão', 2:'Integrado', 3:'Inteligente',
         4:'Confiável',           5:'Transparente', 6:'Eficiente'}
CORES = ['#1A7F7A','#0D2B4E','#D97706','#E63946','#457B9D','#6A4C93']

eixo_col = 'eixo_num_corrigido' if 'eixo_num_corrigido' in corpus.columns else 'eixo_num'
eixo_dist = corpus[eixo_col].value_counts().sort_index()

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle('PTD-BR Corpus — Distribuição por Eixo EFGD', fontsize=14, fontweight='bold')

# Gráfico de barras horizontal
labels = [f'E{e} — {EIXOS.get(e, "")}' for e in eixo_dist.index]
axes[0].barh(labels, eixo_dist.values, color=CORES[:len(eixo_dist)])
for i, v in enumerate(eixo_dist.values):
    axes[0].text(v + 10, i, f'{v:,}', va='center', fontsize=10)
axes[0].set_title('Entregas por eixo', fontweight='bold')
axes[0].spines[['top', 'right']].set_visible(False)

# Top 15 órgãos
top15 = corpus.groupby('sigla').size().nlargest(15)
axes[1].barh(top15.index[::-1], top15.values[::-1], color='#0D2B4E')
axes[1].set_title('Top 15 órgãos por registros', fontweight='bold')
axes[1].spines[['top', 'right']].set_visible(False)

plt.tight_layout()
plt.savefig('ptd_corpus_overview.png', dpi=120, bbox_inches='tight')
plt.show()

# Tabela resumo
if 'parse_flag' in corpus.columns:
    print("\\nQualidade do parser:")
    print(corpus['parse_flag'].value_counts().to_string())
if 'tipo_entrega' in corpus.columns:
    print("\\nTipo de entrega:")
    print(corpus['tipo_entrega'].value_counts().to_string())
"""))

# ── CÉLULA 10 — Amostra do corpus ────────────────────────────────────
nb.cells.append(md("## Célula 9 — Amostra do Corpus (10 linhas por eixo)"))
nb.cells.append(code("""\
cols_show = ['sigla', eixo_col, 'servico', 'produto', 'tipo_entrega', 'parse_flag']
cols_show = [c for c in cols_show if c in corpus.columns]

for eixo in sorted(corpus[eixo_col].dropna().unique()):
    sub = corpus[corpus[eixo_col] == eixo]
    print(f"\\n{'='*60}")
    print(f"EIXO {int(eixo)} — {EIXOS.get(int(eixo), '')}  ({len(sub):,} registros)")
    print('='*60)
    display(sub[cols_show].head(3))
"""))

# ── CÉLULA 11 — Download ──────────────────────────────────────────────
nb.cells.append(md("""\
## Célula 10 — Download dos Arquivos

Baixa os outputs direto do Colab para o seu computador.
"""))
nb.cells.append(code("""\
from google.colab import files
from pathlib import Path

DIR_DB = Path("ptd_corpus/03_database")

downloads = [
    DIR_DB / "ptd_corpus_v21.csv",
    DIR_DB / "ptd_corpus_v21_metadados.json",
    DIR_DB / "ptd_riscos.csv",
    DIR_DB / "pipeline_manifest.json",
    Path("ptd_relatorio_v30.html"),
    Path("apresentacao_ptd_corpus.pptx"),
]

print("Iniciando downloads...")
for f in downloads:
    if f.exists():
        print(f"  ⬇️  {f.name}  ({f.stat().st_size//1024} KB)")
        files.download(str(f))
    else:
        print(f"  ⚠️  {f.name} não encontrado — rode as células anteriores primeiro")
"""))

# ── CÉLULA 12 — Como citar ────────────────────────────────────────────
nb.cells.append(md("""\
---

## Como citar

**ABNT:**
DIREITO, Denise do Carmo; SILVA, Lucas Freire.
*PTD-BR: Corpus de Planos de Transformação Digital do Governo Federal Brasileiro.*
Brasília: IPEA/COGIT/DIEST, 2026. Disponível em: https://github.com/freirelucas/teste.

**BibTeX:**
```bibtex
@misc{ptdbr2026,
  author  = {Direito, Denise do Carmo and Silva, Lucas Freire},
  title   = {{PTD-BR}: Corpus de Planos de Transformação Digital do Governo Federal Brasileiro},
  year    = {2026},
  publisher = {IPEA/COGIT/DIEST},
  url     = {https://github.com/freirelucas/teste}
}
```

> Documento de trabalho — não citar sem autorização dos autores.
"""))

# ── Salvar ────────────────────────────────────────────────────────────
out = "PTD_BR_Corpus_Colab.ipynb"
nbf.write(nb, out)
import os
print(f"✅ Notebook salvo: {out}  ({os.path.getsize(out)//1024} KB)")
print(f"   {len(nb.cells)} células")
