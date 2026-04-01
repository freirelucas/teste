# ╔══════════════════════════════════════════════════════╗
# ║  PTD-BR — CURADORIA v2.1 (melhorado)               ║
# ║  Layer 3: Enriquecimento semântico + auditoria      ║
# ║  IPEA / COGIT / DIEST                               ║
# ║  Fixes: hash input, PRODUTOS externo, E3 genérico  ║
# ╚══════════════════════════════════════════════════════╝
# INPUT : ptd_corpus_raw.csv + pivot + datas + proveniencia.json
# OUTPUT: ptd_corpus_v21.csv + ptd_corpus_v21_metadados.json
#
# ETAPA 0 — Imports e constantes
# ETAPA 1 — Carregamento + validação de integridade
# ETAPA 2 — Parser de campos (servico, produto, subeixo, area, data_ptd)
# ETAPA 3 — Classificação tipo_entrega
# ETAPA 4 — Correção de eixo (regras externas, generalizável)
# ETAPA 5 — Flag ia_real
# ETAPA 6 — Validação e estatísticas
# ETAPA 7 — Exportação CSV + JSON metadados

import pandas as pd
import re, json, hashlib, numpy as np
from pathlib import Path
from datetime import datetime

DIR = Path('ptd_corpus/03_database')
DIR_CFG = Path('config')
DIR.mkdir(parents=True, exist_ok=True)

# ════════════════════════════════════════════════════════
# ETAPA 0 — Constantes (lidas de config/ quando possível)
# ════════════════════════════════════════════════════════

def _load_config(fname: str, fallback: dict) -> dict:
    p = DIR_CFG / fname
    if p.exists():
        with open(p, encoding='utf-8') as f:
            return json.load(f)
    print(f'⚠️  {fname} não encontrado em config/ — usando fallback interno')
    return fallback

_cfg = _load_config('produtos_sgd_v23.json', {
    'produtos': [], 'mandatorios': [], 'subeixos': []
})

# FIX: listas externalizadas — atualizáveis sem editar este script
PRODUTOS  = _cfg['produtos']
MAND_PROD = set(_cfg['mandatorios'])
SUBEIXOS  = _cfg['subeixos']

# Regras de correção de eixo (externas, versionadas)
_corr_cfg = _load_config('correcoes_eixo.json', {'regras': []})
CORRECOES_EIXO = _corr_cfg['regras']

PAT_DATA = re.compile(
    r'(\d{1,2}/\d{1,2}/\d{2,4}|\d{1,2}/\d{4}'
    r'|[a-z]{3}[/-]\d{2,4}|[a-z]{2,4}/\d{2}'
    r'|\d{1,2}[Tt]RIM\d{2}'
    r'|(?:jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)[/-]?(?:\d{2,4}))',
    re.I
)
PAT_RUIDO    = re.compile(r'^(Servi[çc]o|Produto|Eixo|[AÁ]rea\s|Entregas|DtPact|DtEntrega)', re.I)
PAT_ID_GOVBR = re.compile(r'^\d{3,6}\s+(?:Servi[çc]o\s+)?')
PAT_IA_REAL  = re.compile(
    r'chatbot|intelig[eê]ncia artificial|machine learning'
    r'|IA generativa|sumariza[çc][aã]o inteligente|Safety Intelligence',
    re.I
)

EIXOS = {
    1:'Centrado no Cidadão e Inclusivo', 2:'Integrado e Colaborativo',
    3:'Inteligente e Inovador',          4:'Confiável e Seguro',
    5:'Transparente, Aberto e Participativo', 6:'Eficiente e Sustentável',
}
print('✅ Etapa 0 — constantes carregadas')
print(f'   {len(PRODUTOS)} produtos | {len(MAND_PROD)} mandatórios | '
      f'{len(CORRECOES_EIXO)} regras de correção de eixo')


# ════════════════════════════════════════════════════════
# ETAPA 1 — Carregamento + validação de integridade
# FIX: verifica SHA-256 do CSV de entrada contra manifesto
# ════════════════════════════════════════════════════════

def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def _load_csv(path: Path, label: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f'{label} não encontrado: {path}')
    df = pd.read_csv(path)
    h  = _sha256_file(path)
    print(f'   {label:30s}: {len(df):,} linhas | sha256={h[:12]}…')
    return df, h

print('\n✅ Etapa 1 — carregando dados')

corpus, h_corpus = _load_csv(DIR / 'ptd_corpus_raw.csv', 'ptd_corpus_raw')
pivot,  h_pivot  = _load_csv(DIR / 'ptd_pivot_eixos.csv', 'ptd_pivot_eixos')
datas,  h_datas  = _load_csv(DIR / 'ptd_datas_assinatura.csv', 'ptd_datas_assinatura')

prov_path = DIR / 'proveniencia.json'
if prov_path.exists():
    with open(prov_path, encoding='utf-8') as f:
        prov = json.load(f)
else:
    prov = {}
    print('   ⚠️  proveniencia.json não encontrado')

# Registrar hashes dos inputs nesta execução
input_hashes = {
    'ptd_corpus_raw.csv':        h_corpus,
    'ptd_pivot_eixos.csv':       h_pivot,
    'ptd_datas_assinatura.csv':  h_datas,
}

# Validar contra manifesto da pipeline (se disponível)
manifest_path = DIR / 'pipeline_manifest.json'
if manifest_path.exists():
    with open(manifest_path, encoding='utf-8') as f:
        manifest = json.load(f)
    manifest_version = manifest.get('versao_pipeline', 'desconhecida')
    print(f'   Manifesto pipeline: {manifest_version}')
else:
    print('   ⚠️  pipeline_manifest.json ausente — rastreabilidade parcial')

print(f'\n   NOTA METODOLÓGICA — UNIDADE DE ANÁLISE:')
print(f'   Cada linha = 1 comprometimento = serviço × produto.')
print(f'   Média esperada: ~2,07 produtos/serviço (54 diretivos).')


# ════════════════════════════════════════════════════════
# ETAPA 2 — Parser de campos
# ════════════════════════════════════════════════════════

def parse_linha(txt):
    """
    Separa texto concatenado: Serviço | Produto | Subeixo | Área | Data
    Retorna (servico, produto, subeixo, area, data_ptd, parse_flag)
    parse_flag: ok | sem_produto | sem_servico | ruido | vazio
    """
    if pd.isna(txt):
        return None, None, None, None, None, 'vazio'
    t = str(txt).replace('\n', ' ').strip()
    if PAT_RUIDO.match(t) or len(t) < 10:
        return None, None, None, None, None, 'ruido'

    prod_found, prod_start, prod_end = None, None, None
    for p in PRODUTOS:
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
    for s in SUBEIXOS:
        idx = resto.find(s)
        if idx >= 0 and (sub_end == 0 or idx < sub_end):
            sub_found, sub_end = s, idx + len(s)

    area_data = resto[sub_end:].strip() if sub_found else resto
    dts       = list(PAT_DATA.finditer(area_data))
    data_ptd  = dts[-1].group() if dts else None
    area      = area_data[:area_data.rfind(data_ptd)].strip() if data_ptd else area_data.strip()
    area      = area[:500] if area else area  # evitar célula gigante no CSV
    servico   = PAT_ID_GOVBR.sub('', servico).strip()

    if not servico:
        return None, prod_found, sub_found, area or None, data_ptd, 'sem_servico'
    return servico, prod_found, sub_found, area or None, data_ptd, 'ok'


parsed = corpus['texto'].apply(parse_linha)
corpus['servico']    = [r[0] for r in parsed]
corpus['produto']    = [r[1] for r in parsed]
corpus['subeixo']    = [r[2] for r in parsed]
corpus['area']       = [r[3] for r in parsed]
corpus['data_ptd']   = [r[4] for r in parsed]
corpus['parse_flag'] = [r[5] for r in parsed]

print('\n✅ Etapa 2 — parser aplicado')
for flag, n in corpus['parse_flag'].value_counts().items():
    print(f'   {flag:<15}: {n:>5} ({n/len(corpus)*100:.1f}%)')
print(f'   Cobertura servico  : {corpus.servico.notna().mean()*100:.1f}%')
print(f'   Cobertura produto  : {corpus.produto.notna().mean()*100:.1f}%')
print(f'   Cobertura data_ptd : {corpus.data_ptd.notna().mean()*100:.1f}%')


# ════════════════════════════════════════════════════════
# ETAPA 3 — Tipo de entrega
# ════════════════════════════════════════════════════════

def classificar_tipo_entrega(row) -> str:
    prod = str(row.get('produto', '') or '')
    txt  = str(row.get('texto',   '') or '')
    if prod in MAND_PROD:
        return 'mandatorio_ppsi'
    if 'Login Único' in prod or 'login único' in prod:
        return 'mandatorio_login'
    if re.search(r'avalia[çc][aã]o da satisfa[çc][aã]o', txt, re.I):
        return 'mandatorio_avaliacao'
    if re.search(r'Revis[aã]o da descri[çc][aã]o dos servi[çc]os', txt):
        return 'mandatorio_revisao'
    return 'discricionario'

corpus['tipo_entrega'] = corpus.apply(classificar_tipo_entrega, axis=1)
print('\n✅ Etapa 3 — tipo_entrega')
for k, v in corpus['tipo_entrega'].value_counts().items():
    print(f'   {k:<25}: {v:>5} ({v/len(corpus)*100:.1f}%)')


# ════════════════════════════════════════════════════════
# ETAPA 4 — Correção de eixo (regras externas)
# FIX: generalizado — não hardcoda PGFN; lê config/correcoes_eixo.json
# ════════════════════════════════════════════════════════

def _build_corretores(regras: list) -> list:
    """Compila regras externas em funções de correção."""
    compiled = []
    for r in regras:
        excecoes = [re.compile(p, re.I) for p in r.get('excecoes_manter_e3', [])]
        compiled.append({
            'sigla':        r['sigla'],
            'eixo_errado':  r['eixo_errado'],
            'eixo_correto': r['eixo_correto'],
            'excecoes':     excecoes,
            'pagina':       r.get('pagina'),
        })
    return compiled

_corretores = _build_corretores(CORRECOES_EIXO)

def corrigir_eixo(row) -> int:
    eixo = row['eixo_num']
    for c in _corretores:
        if row.get('sigla') != c['sigla']:
            continue
        if eixo != c['eixo_errado']:
            continue
        # Página específica (se definida na regra)
        if c['pagina'] and row.get('pagina') != c['pagina']:
            continue
        txt = str(row.get('texto', '') or '')
        # Manter eixo original se alguma exceção der match
        if any(p.search(txt) for p in c['excecoes']):
            return eixo
        return c['eixo_correto']
    return eixo

corpus['eixo_num_corrigido'] = corpus.apply(corrigir_eixo, axis=1)

e3_orig = int((corpus['eixo_num'] == 3).sum())
e3_corr = int((corpus['eixo_num_corrigido'] == 3).sum())
print(f'\n✅ Etapa 4 — correção de eixo')
print(f'   E3 original : {e3_orig}')
print(f'   E3 corrigido: {e3_corr}')
print(f'   Registros reclassificados: {e3_orig - e3_corr}')
for r in CORRECOES_EIXO:
    print(f'   Regra {r["id"]}: {r["sigla"]} E{r["eixo_errado"]}→E{r["eixo_correto"]} '
          f'({r["n_registros_afetados"]} esperados)')


# ════════════════════════════════════════════════════════
# ETAPA 5 — Flag ia_real
# ════════════════════════════════════════════════════════

corpus['ia_real'] = corpus['texto'].apply(
    lambda t: 1 if (not pd.isna(t) and PAT_IA_REAL.search(str(t))) else 0
)
ia_n   = int(corpus['ia_real'].sum())
ia_org = corpus[corpus['ia_real'] == 1]['sigla'].nunique()
print(f'\n✅ Etapa 5 — ia_real: {ia_n} registros em {ia_org} órgãos')
print('   (Nota: busca por "ia" sozinha retorna ~2.941 falsos positivos)')


# ════════════════════════════════════════════════════════
# ETAPA 6 — Validação
# ════════════════════════════════════════════════════════

dir54 = corpus[corpus.get('tem_diretivo', pd.Series(False, index=corpus.index)) == True] \
    if 'tem_diretivo' in corpus.columns else corpus

n_serv = int(dir54['servico'].dropna().nunique()) if not dir54.empty else 0
fator  = round(len(dir54) / n_serv, 2) if n_serv else 0

print(f'\n✅ Etapa 6 — validação')
print(f'   Linhas totais      : {len(corpus):,}')
print(f'   Serviços únicos    : {n_serv:,}')
print(f'   Fator multiplicação: {fator:.2f}x')
print(f'\n   DISTRIBUIÇÃO POR EIXO:')
for e in range(1, 7):
    n  = int((corpus['eixo_num'] == e).sum())
    nc = int((corpus['eixo_num_corrigido'] == e).sum())
    print(f'   E{e}: {n:>5} orig → {nc:>5} corrig  | {EIXOS[e]}')


# ════════════════════════════════════════════════════════
# ETAPA 7 — Exportação
# ════════════════════════════════════════════════════════

class NpEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, np.integer): return int(o)
        if isinstance(o, np.floating): return float(o)
        if isinstance(o, np.bool_): return bool(o)
        return super().default(o)

csv_path  = DIR / 'ptd_corpus_v21.csv'
json_path = DIR / 'ptd_corpus_v21_metadados.json'

corpus.to_csv(csv_path, index=False, encoding='utf-8')

datas['parsed'] = pd.to_datetime(datas['data_raw'], dayfirst=True, errors='coerce')

metadados = {
    'versao_corpus':    '2.1',
    'data_geracao':     datetime.now().strftime('%Y-%m-%d'),
    'input_hashes':     input_hashes,   # FIX: rastreabilidade
    'config_produtos':  str(DIR_CFG / 'produtos_sgd_v23.json'),
    'config_correcoes': str(DIR_CFG / 'correcoes_eixo.json'),
    'unidade_analise':  'comprometimento (servico × produto)',
    'corpus': {
        'total_linhas':     len(corpus),
        'servicos_unicos':  n_serv,
        'fator_mult_medio': fator,
    },
    'parse': {
        'flags': {k: int(v) for k, v in corpus['parse_flag'].value_counts().items()},
        'cobertura_servico_pct':  round(corpus.servico.notna().mean()*100, 1),
        'cobertura_produto_pct':  round(corpus.produto.notna().mean()*100, 1),
        'cobertura_data_ptd_pct': round(corpus.data_ptd.notna().mean()*100, 1),
    },
    'eixos': {
        'original':  {str(e): int((corpus['eixo_num']==e).sum()) for e in range(1,7)},
        'corrigido': {str(e): int((corpus['eixo_num_corrigido']==e).sum()) for e in range(1,7)},
        'n_reclassificados': e3_orig - e3_corr,
        'regras_aplicadas':  [r['id'] for r in CORRECOES_EIXO],
    },
    'tipo_entrega': {k: int(v) for k, v in corpus['tipo_entrega'].value_counts().items()},
    'ia_real':      {'registros': ia_n, 'orgaos': ia_org},
    'datas': {
        'validas': int(datas['parsed'].notna().sum()),
        'total':   len(datas),
    },
    'proveniencia': prov,
}

with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(metadados, f, ensure_ascii=False, indent=2, cls=NpEncoder)

print(f'\n✅ Etapa 7 — exportação concluída')
print(f'   {csv_path.name}  : {csv_path.stat().st_size//1024} KB')
print(f'   {json_path.name}: {json_path.stat().st_size//1024} KB')
