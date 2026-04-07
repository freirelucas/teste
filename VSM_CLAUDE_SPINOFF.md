# VSM + INFOSET — Framework para Configurar Claude com Consciência Cibernética

> **Spin-off do projeto PTD-BR Pipeline** — IPEA/COGIT/DIEST, 2026  
> Baseado em: Stafford Beer (1972, 1979, 1985), *Beyond Dispute* (1994), Team Syntegrity  
> Aplicado a: Configuração de agentes Claude para projetos complexos autônomos

---

## Por que cibernética + Claude?

O PTD-BR Pipeline foi construído com a arquitetura VSM (Viable System Model) de Stafford Beer
como espinha dorsal. Após 155 iterações autônomas, a lição central é:

> **Sistemas que sabem o que são (identidade) e o que precisam aprender (inteligência) convergem.
> Sistemas que executam sem consciência sistêmica travam em loops vazios.**

O loop vazio de 154 iterações (watcher sem progresso) ocorreu porque o S4 (Inteligência)
não estava operacional — o sistema não sabia o que não sabia. Este spin-off codifica
como configurar um assistente Claude desde o início com essa consciência.

---

## Parte 1 — VSM em 5 minutos

O **Viable System Model** de Stafford Beer modela qualquer sistema viável em 5 subsistemas:

| Sistema | Função | Pergunta central |
|---------|--------|-----------------|
| **S1 — Operações** | Faz o trabalho primário | "O que estamos produzindo?" |
| **S2 — Coordenação** | Sincroniza as operações | "Como evitamos conflitos entre S1s?" |
| **S3 — Gestão** | Controla recursos e performance | "Estamos no caminho certo?" |
| **S3* — Auditoria** | Verifica independentemente | "A gestão está vendo a realidade?" |
| **S4 — Inteligência** | Monitora o ambiente externo | "O mundo mudou? Precisamos adaptar?" |
| **S5 — Política** | Define identidade e propósito | "Por que existimos? O que não é negociável?" |

**Lei de Ashby (Requisite Variety)**: O controlador precisa ter variedade ≥ à do ambiente.
Se o ambiente é complexo e o controlador é simples, o sistema entra em colapso.

**Princípio de Beer**: "The purpose of a system is what it does" (POSIWID).
Não o que diz que faz — o que *de fato* produz.

---

## Parte 2 — INFOSET e Team Syntegrity

Em *Beyond Dispute* (1994), Beer propõe o **Syntegrity** como protocolo para
grupos tomarem decisões complexas sem hierarquia:

### Estrutura INFOSET (Icosahedron)

- 30 participantes, 12 temas, estrutura de icosaedro
- Cada participante é membro ativo de 2 temas e interessado em 4 outros
- Conversas rodam em paralelo → síntese emergente sem voto majoritário
- **Critério de closure**: quando todos os critérios de uma rede de temas se auto-referenciam

### O que isso significa para agentes de IA?

Cada **agente** pode ser configurado como um "participante" do INFOSET, com:
- **2 temas de foco** (o que ele opera e classifica)
- **4 temas de interesse** (o que ele monitora como sensor)
- **Protocolo de resolução**: sem hierarquia, por resonância emergente entre perspectivas

Aplicação prática: em vez de um agente monolítico que "faz tudo", configurar
múltiplos agentes com papéis VSM específicos que interagem via `ptd_run_summary.json`.

---

## Parte 3 — Como configurar Claude com VSM-Awareness desde o início

### 3.1 CLAUDE.md mínimo com VSM

Todo projeto que usa Claude de forma contínua deve ter um `CLAUDE.md` com:

```markdown
## Arquitetura VSM deste projeto

| Sistema | Implementação | Status |
|---------|--------------|--------|
| S1 — Operações | [script que executa] | ativo/inativo |
| S2 — Coordenação | [config files] | ativo/inativo |
| S3 — Gestão | [watcher/CI] | ativo/inativo |
| S3* — Auditoria | [sensor/relatorio] | ativo/inativo |
| S4 — Inteligência | [meta-learning/sinais] | ativo/inativo |
| S5 — Política | [critérios de sucesso] | ativo/inativo |

## Propósito declarado (S5)
[1 frase: o sistema existe para...]

## Critérios de sucesso mensuráveis
[3–5 métricas com valores-alvo e thresholds de escalação]

## Loop de aprendizado
[Como o sistema aprende: L-A por ciclo, L-B meta, L-C global]
```

### 3.2 Prompt de inicialização VSM

Ao iniciar uma nova sessão Claude em um projeto complexo, use este prompt:

```
Este projeto usa a arquitetura VSM de Stafford Beer.
Antes de qualquer ação, identifique:

1. S5: Qual é o propósito declarado? (CLAUDE.md ou contexto)
2. S3: Qual é o estado atual das métricas principais?
3. S4: O que o sistema não sabe que não sabe? (gaps de sensor)
4. Gap VSM: Qual sistema está mais fraco? Onde está o gargalo?

Só depois responda à questão operacional.
```

### 3.3 Diagnóstico VSM rápido

Ao encontrar um problema em qualquer projeto, mapeie para o VSM antes de propor solução:

| Sintoma | Sistema VSM problemático | Diagnóstico |
|---------|------------------------|-------------|
| Loop sem progresso | S4 ausente ou S3* cego | Sensor não enxerga a realidade |
| Ações corretas mas sem efeito | S2 fraco (coordenação) | Partes do S1 não estão sincronizadas |
| Progresso mas direção errada | S5 implícito ou ambíguo | Propósito não está operacionalizado |
| Boa execução, ambiente mudou | S4 desatualizado | Inteligência não monitora o exterior |
| Gestão diz "ok", realidade diz "não" | S3* ausente | Auditoria independente necessária |

### 3.4 O anti-padrão da "bomba de ação"

> "Fazer mais" sem diagnóstico sistêmico é o anti-padrão fundamental.

O PTD-BR Pipeline executou 154 iterações sem progresso porque S3 (watcher) tomava ações
baseadas em S3* (sensor) cego. A solução não foi "fazer mais iterações" — foi expandir
a visão do sensor (S3*) para que S4 pudesse emergir.

**Regra prática para Claude**: antes de propor uma solução, verificar se o problema
está no nível correto do VSM. Se S4 está cego, nenhuma ação de S1 resolve.

---

## Parte 4 — Template de settings.json para projetos com VSM

Coloque em `.claude/settings.json` do seu projeto:

```json
{
  "vsm_context": {
    "s5_purpose": "Descreva o propósito em 1 frase",
    "s5_criteria": [
      "métrica_1 >= threshold_1",
      "métrica_2 >= threshold_2",
      "métrica_3 <= threshold_3"
    ],
    "s4_sensor_files": [
      "path/to/summary.json",
      "path/to/learning_signals.json"
    ],
    "s3_controller": "path/to/watcher ou CI config",
    "current_bottleneck": "S4 | S3* | S2 | S1"
  },
  "learning_loops": {
    "L_A": "Por execução — o que aprender a cada ciclo",
    "L_B": "Meta — a cada N ciclos, analisar trajetória",
    "L_C": "Global — acumulador longitudinal de sinais"
  }
}
```

---

## Parte 5 — INFOSET para Projetos Multi-Agente

Para projetos que usam múltiplos agentes Claude em paralelo (Agent SDK), aplicar INFOSET:

### Mapeamento VSM → Papéis de agente

```
Agente S1-Ops:    executa operações (ex: download, extração)
Agente S2-Coord:  mantém config compartilhada consistente
Agente S3-Mgmt:   monitora métricas e toma decisões de controle
Agente S3*-Audit: verifica independentemente se S3 vê a realidade
Agente S4-Intel:  analisa ambiente externo e propõe adaptações
```

### Protocolo de interação (INFOSET-inspired)

1. **Nenhum agente tem visão completa** — cada um vê apenas seu subsistema
2. **Saídas são JSON estruturado** — legível por outros agentes
3. **Síntese é emergente** — o agente S5 (humano ou meta-agente) integra as visões
4. **Critério de closure**: quando os sinais de S1, S3* e S4 convergem para a mesma causa

### Exemplo de fluxo multi-agente PTD-BR

```
Agente S3*-Audit lê ptd_corpus_v21.csv → reporta: pct_ok=75.5%, INCRA col_map=0%
    ↓
Agente S4-Intel lê ptd_learning_signals.json → analisa slope → propõe: mudar estratégia para col_keys
    ↓
Agente S2-Coord atualiza config/col_keys_extra.json com keywords INCRA
    ↓
Agente S3-Mgmt commita + triggera próxima execução
    ↓
Agente S1-Ops executa pipeline com novo col_keys
    ↓
loop
```

---

## Parte 6 — Princípios de Beer para Agentes de IA

### Princípio 1: Requisite Variety
O agente precisa ter complexidade ≥ à do problema.
**Implicação**: um Claude com contexto VSM estruturado resolve mais do que sem ele.

### Princípio 2: POSIWID
"O propósito do sistema é o que ele faz" — não o que diz que faz.
**Implicação**: medir o que o sistema *produz*, não o que *afirma*. pct_ok > promessas.

### Princípio 3: Recursividade
Cada S1 é também um sistema viável — contém S1-S5 internamente.
**Implicação**: cada subagente deve também ter S3 (auto-monitoramento) e S4 (adaptação).

### Princípio 4: Algedônica (sinal de dor/prazer)
Sinais de alarme devem poder bypassar S3 e ir direto ao S5.
**Implicação**: condições críticas (pct_ok < 30%, colapso de extração) devem escalar
diretamente ao operador humano, sem esperar o próximo ciclo normal.

### Princípio 5: Canais de informação (não gestão)
S3 não gerencia S1 diretamente — envia parâmetros via S2.
**Implicação**: o watcher não edita o pipeline diretamente — edita `config/` que o pipeline lê.

---

## Parte 7 — Checklist de configuração VSM para novo projeto Claude

Ao iniciar um novo projeto autônomo com Claude:

- [ ] **S5**: Escrever propósito em 1 frase e 3–5 critérios mensuráveis no CLAUDE.md
- [ ] **S4**: Definir o que será monitorado externamente (mercado, dados, usuários, feedback)
- [ ] **S3***: Criar sensor independente do pipeline (arquivo JSON com diagnóstico legível por IA)
- [ ] **S3**: Definir o loop de controle (watcher, CI, cron) e a máquina de estados
- [ ] **S2**: Separar config do código (config/ ou settings.json) para que S3 parametrize S1
- [ ] **S1**: Definir unidades de operação independentes (por órgão, por PDF, por usuário)
- [ ] **Anti-padrão**: Verificar que S3 não age diretamente sobre S1 (bypassa S2)
- [ ] **Loop learning**: Definir L-A (por ciclo), L-B (meta), L-C (global)
- [ ] **Algedônica**: Definir condição de escalação urgente ao S5 (humano)

---

## Referências

- Beer, S. (1972). *Brain of the Firm*. Allen Lane.
- Beer, S. (1979). *The Heart of Enterprise*. Wiley.
- Beer, S. (1985). *Diagnosing the System for Organizations*. Wiley.
- Beer, S. (1994). *Beyond Dispute: The Invention of Team Syntegrity*. Wiley.
- Espejo, R. & Harnden, R. (1989). *The Viable System Model*. Wiley.
- Espejo, R. & Reyes, A. (2011). *Organizational Systems*. Springer.

---

## Aplicação imediata — prompt para Claude

Para usar este framework agora, cole no início de qualquer sessão de projeto complexo:

```
Estou trabalhando em [nome do projeto]. Antes de qualquer coisa, faça o diagnóstico VSM:

S5 (Propósito): [descreva]
S4 (O que o sistema não sabe?): [sinais externos que deveria monitorar]
S3* (Sensor): [arquivo ou dado que reporta a realidade atual]
S3 (Gestão): [o que controla o loop autônomo]
S2 (Coordenação): [config compartilhada]
S1 (Operações): [unidades de trabalho]

Dado o estado atual ([métrica principal] = [valor]), qual sistema VSM é o gargalo?
Qual a próxima ação de MAIOR ALAVANCAGEM no nível correto do VSM?
```

---

## Parte 8 — Implementação Concreta: Hooks do Claude Code

A chave para tornar o VSM operacional no Claude Code é o sistema de **hooks**.
Cada canal VSM mapeia para um tipo de hook:

| Canal VSM | Hook Claude Code | Função |
|-----------|-----------------|--------|
| S5 — Política | `PreToolUse` (operações destrutivas) | Bloqueia ações inconstitucionais |
| S4 — Inteligência | `SessionStart` | Injeta contexto ambiental atual |
| S3 — Gestão | `UserPromptSubmit` | Verifica prioridades e recursos |
| S3* — Auditoria | `PostToolUse` | Log independente de toda ação |
| S2 — Coordenação | `PreToolUse` (recursos compartilhados) | Previne conflitos concorrentes |
| Algedônico (dor) | `Stop` com `decision: "block"` | Bloqueia parada prematura |
| Algedônico (prazer) | `PostToolUse` → wins.log | Registra conclusões bem-sucedidas |

### `.claude/settings.json` — Configuração VSM completa

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [{
          "type": "command",
          "command": ".claude/hooks/s4_inject_environment.sh",
          "timeout": 10,
          "statusMessage": "S4: Carregando contexto ambiental..."
        }]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [{
          "type": "command",
          "command": ".claude/hooks/s3_priority_check.sh",
          "timeout": 5,
          "statusMessage": "S3: Verificando prioridades e restrições..."
        }]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash|Write|Edit",
        "hooks": [{
          "type": "command",
          "command": ".claude/hooks/s2_coordination_check.sh",
          "timeout": 10,
          "statusMessage": "S2: Verificando coordenação..."
        }]
      },
      {
        "matcher": "Bash",
        "hooks": [{
          "type": "command",
          "command": ".claude/hooks/s5_policy_guard.sh",
          "timeout": 5,
          "statusMessage": "S5: Verificando política constitucional..."
        }]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash|Write|Edit",
        "hooks": [{
          "type": "command",
          "command": ".claude/hooks/s3star_audit_log.sh",
          "timeout": 5,
          "statusMessage": "S3*: Registrando para auditoria..."
        }]
      }
    ],
    "Stop": [
      {
        "hooks": [{
          "type": "command",
          "command": ".claude/hooks/algedonic_completion_check.sh",
          "timeout": 30,
          "statusMessage": "Verificando conclusão antes de parar..."
        }]
      }
    ]
  }
}
```

### Scripts de hook essenciais

**S4 — Injeção de ambiente** (`.claude/hooks/s4_inject_environment.sh`):
```bash
#!/bin/bash
# S4: Outside and Then — injeta estado ambiental ao iniciar sessão
BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
LAST_COMMIT=$(git log -1 --format="%h %s" 2>/dev/null || echo "sem git")
SUMMARY=""
if [ -f "ptd_run_summary.json" ]; then
  PCT_OK=$(jq -r '.pct_ok // "?"' ptd_run_summary.json 2>/dev/null)
  SUMMARY="pct_ok: $PCT_OK%"
fi

jq -n \
  --arg branch "$BRANCH" \
  --arg commit "$LAST_COMMIT" \
  --arg summary "$SUMMARY" \
  '{hookSpecificOutput: {hookEventName: "SessionStart",
    additionalContext: "S4 ESTADO AMBIENTAL:\nBranch: \($branch)\nÚltimo commit: \($commit)\n\($summary)\n\nRequisite variety: ajuste a complexidade da resposta à do problema."}}'
```

**S5 — Guarda de política** (`.claude/hooks/s5_policy_guard.sh`):
```bash
#!/bin/bash
# S5: Bloqueia operações inconstitucionais
INPUT=$(cat /dev/stdin)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Force push para main é sempre bloqueado
if echo "$COMMAND" | grep -qE "push.*--force.*(main|master)"; then
  jq -n '{hookSpecificOutput: {hookEventName: "PreToolUse",
    permissionDecision: "deny",
    permissionDecisionReason: "S5 POLÍTICA: Force push para main é constitucionalmente proibido."}}'
  exit 2
fi
exit 0
```

**Algedônico — Verificação de conclusão** (`.claude/hooks/algedonic_completion_check.sh`):
```bash
#!/bin/bash
# Canal algedônico: verifica se tarefa realmente concluiu antes de parar
# Se output contém ALGEDONIC: ou TODO: incompleto, bloqueia parada
TRANSCRIPT_PATH=$(cat /dev/stdin | jq -r '.transcript_path // empty')
if [ -n "$TRANSCRIPT_PATH" ] && grep -qE "ALGEDONIC:|TODO \(pendente\)" "$TRANSCRIPT_PATH" 2>/dev/null; then
  echo '{"decision": "block", "reason": "Sinal algedônico detectado ou trabalho incompleto. Resolva antes de parar."}'
  exit 2
fi
# Registra conclusão como sinal de prazer
echo "$(date -Iseconds) TASK_COMPLETE" >> .claude/wins.log 2>/dev/null
exit 0
```

### Protocolo Vollzug (ViableOS)

Para projetos multi-agente com risco de amnésia de contexto:

1. **Quittung** (30 min): Agente confirma recebimento da diretiva
2. **Vollzug** (prazo definido): Agente executa e confirma
3. **Report** (com evidência): Agente entrega prova de conclusão

Timeouts escalam automaticamente para o operador humano (algedônico).

---

## Glossário VSM ↔ IA

| Termo | Definição Beer | Tradução para agentes IA |
|-------|---------------|------------------------|
| **Viable system** | Sistema autônomo que sobrevive em ambiente mutável | Agente que adapta a tarefas novas sem reprogramação |
| **Requisite Variety** | Controlador precisa ter variedade ≥ do ambiente (Ashby) | Se tarefa excede capacidade: decompor ou escalar |
| **Algedônico** | Canal rápido dor/prazer que bypassa hierarquia | `Stop` hook com exit 2 (dor); wins.log (prazer) |
| **POSIWID** | "O propósito do sistema é o que ele faz" | Julgar agente por logs, não por intenções declaradas |
| **Homeostato S3↔S4** | Tensão entre explorar agora (S3) e adaptar ao futuro (S4) | Equilíbrio entre execução e aprendizado |
| **Recursão** | Sistemas viáveis contêm sistemas viáveis internamente | Sub-agentes têm seu próprio CLAUDE.md/S1-S5 |
| **INFOSET** | Conjunto de agentes com preocupação e conhecimento compartilhados | Pool de agentes para domínio-problema com protocolo de cross-pollination |
| **Syntegrity** | Protocolo icosaédrico para inteligência coletiva sem hierarquia | Decomposição multi-agente com papéis Member/Critic/Observer |
| **S3*** | Auditoria esporádica independente que bypassa auto-reporte | Agente verificador usando modelo LLM diferente |

---

## Referências

### Obras de Stafford Beer
- Beer, S. (1972). *Brain of the Firm*. Allen Lane.
- Beer, S. (1979). *The Heart of Enterprise*. Wiley.
- Beer, S. (1985). *Diagnosing the System for Organizations*. Wiley.
- Beer, S. (1994). *Beyond Dispute: The Invention of Team Syntegrity*. Wiley. ISBN 0-471-94451-3.

### VSM aplicado a agentes IA (2025–2026)
- Gorelkin, M. "Stafford Beer's Viable Model for Building Enterprise Agentic Systems". *Medium*, 2025.
- Fearne, A. "Applying VSM to Create Autonomous AI Organisations". *Medium*, 2025.
- Kellogg, T. "Viable Systems: How to Build a Fully Autonomous Agent". *Strix Research*, Jan 2026.
- Kellogg, T. "The Levels of Agentic Coding". *Strix Research*, Jan 2026.
- Enderle, P. "Your Multi-Agent Framework Handles Operations. What About the Other Five?" *DEV.to*, 2025.
- Nhilbert. *Viable System Generator* (ViableOS). agent.nhilbert.de, 2026.

### Syntegrity e Malik
- Truss, J. & Leonard, A. "Team Syntegrity: A New Methodology for Group Work". *Academia.edu*.
- Espejo, R. & Reyes, A. (2011). *Organizational Systems*. Springer.
- Pfiffner, M. "From Workshop to Syntegration". Malik Management, St. Gallen.
- Malik Management. "Malik Syntegration InfoSheet". malik-management.com, 2024.
- Nittbaur, G. "Stafford Beer's Syntegration as Renascence of the Ancient Greek Agora". *JUKM*, 2003.

---

## Parte 9 — Syntegration com Menos Atores (Fredmund Malik)

Fredmund Malik (Malik Management, St. Gallen) é o principal sistematizador das versões
menores da Syntegrity de Beer, registradas como **"Syntegration"** (marca Malik).
A chave: trocar o icosaedro por outros **sólidos de Platão** menores.

### Famílias geométricas e tamanhos

| Sólido | Vértices (tópicos) | Arestas (posições) | Participantes | Faces | Tipo |
|--------|-------------------|-------------------|--------------|-------|------|
| **Tetraedro** | 4 | 6 | ~6 | 4 | mínimo viável |
| **Octaedro** | 6 | 12 | ~12–15 | 8 | grupos pequenos |
| **Cubo** | 8 | 12 | ~16–24 | 6 | grupos médios (sem papel Critic) |
| **Icosaedro** (Beer) | 12 | 30 | 30 | 20 | protocolo original |

**Regra de escala**: vértices = nº de tópicos; arestas = nº de posições de participante.
O papel de **Critic** emerge naturalmente quando faces triangulares se opõem (octaedro, icosaedro).
No cubo (faces quadradas), o papel Critic some — só Member e Observer. Isso reduz tensão
adversarial mas acelera convergência em grupos já alinhados.

### Tetraedro — Syntegration mínima (6 participantes, 4 tópicos)

```
      T1
     /  \
   T2 -- T4
     \  /
      T3

Cada participante: Member de 1 tópico + Observer dos outros 3
Sem papel Critic (ausência de face triangular oposta ao mesmo vértice)
Funciona para: equipes de produto, squads, duplas de pesquisa
```

**Para agentes Claude**: 4 agentes paralelos, cada um com 1 tópico principal,
monitorando os outros 3 via arquivo de estado compartilhado (`syntegration_state.json`).

### Octaedro — Syntegration pequena (12–15 participantes, 6 tópicos)

```
         T1
        /|\ 
      T2-+-T3
      |  |  |   ← anel equatorial
      T4-+-T5
        \|/
         T6

Papel por participante:
  Member:   1 tópico (principal)
  Critic:   1 tópico (adversarial, vértice oposto)
  Observer: 4 tópicos restantes
```

**Propriedade-chave do octaedro**: cada vértice tem exatamente 4 vizinhos (grau 4),
garantindo simetria máxima. A tensão Member↔Critic é natural: vértices opostos no
octaedro são os mais distantes na topologia — pressão adversarial máxima.

**Para agentes**: 6 agentes, cada um com 1 tópico primário e 1 vértice oposto como
tópico Critic. Máximo de tensão produtiva com mínimo de participantes.

---

## Parte 10 — Geometria e Comunicação Assíncrona

### Por que a geometria importa para comunicação assíncrona?

Em comunicação síncrona (reunião), a topologia do sólido governa *quem fala com quem*.
Em comunicação **assíncrona** (agentes, mensagens, commits), a geometria governa algo
diferente e mais profundo: **em quantos passos uma informação alcança todos os nós**.

Isso é o **diâmetro** do grafo. Menor diâmetro = informação mais rápida.

### Tabela de propriedades para comunicação assíncrona

| Sólido | Diâmetro | Grau nodal | Propagação info | Latência async |
|--------|----------|-----------|----------------|----------------|
| Tetraedro | 1 | 3 | Qualquer nó alcança todos em 1 passo | Mínima |
| Octaedro | 2 | 4 | 2 passos máximo entre qualquer par | Baixa |
| Cubo | 3 | 3 | 3 passos (mais lento entre opostos) | Média |
| Icosaedro | 3 | 5 | 3 passos, alta resiliência (5 caminhos) | Média, mas resiliente |
| Rede plana n×n | O(√n) | 2–4 | Cresce com n² participantes | Alta |
| Grafo completo | 1 | n-1 | Instantâneo, mas n² conexões | Zero, custo alto |

**Insight principal**: o icosaedro não é o mais rápido — é o **mais resiliente**.
5 caminhos independentes entre qualquer par de nós significa que pode perder até
4 conexões e ainda propagar informação. Para agentes que podem falhar ou ficar offline,
isso é crucial.

### Padrões de comunicação assíncrona por sólido

#### Tetraedro assíncrono (4 agentes / tópicos)
```
Rodada 0: Cada agente escreve Statement inicial → shared/T{n}_v0.md
Rodada 1: Cada agente lê os outros 3 → escreve síntese → shared/T{n}_v1.md
Rodada 2: Convergência — todos leem v1 de todos → Statement final
Total: 2 rodadas assíncronas → 3 documentos por tópico
```

#### Octaedro assíncrono (6 agentes / tópicos)
```
Rodada 0: Member escreve Statement → T{n}_member.md
Rodada 1: Critic lê Statement do oposto → escreve crítica → T{n}_critic.md
Rodada 2: Member lê crítica → revisa → T{n}_v2.md
Rodada 3: Observer integra ambos os lados → T{n}_synthesis.md
Total: 4 rodadas, 4 documentos por tópico — tensão adversarial explícita
```

#### Icosaedro assíncrono (12 tópicos, Beer digital)
```
Rodada 0: 12 Members escrevem Statements (paralelo)
Rodada 1: 12 Critics leem e escrevem críticas (paralelo)
Rodada 2: 8 Observers integram pares (paralelo)
Rodada 3: Síntese global via meta-agente S4
Total: 4 rodadas — Beer digital com 12 agentes simultâneos
```

### Implementação para agentes Claude (octaedro async)

```python
# syntegration_octahedron.py — 6 agentes, 4 rodadas assíncronas

TOPICS = ['t1', 't2', 't3', 't4', 't5', 't6']
# Opostos no octaedro: cada tópico tem 1 oposto
OPPOSITES = {'t1':'t6', 't2':'t5', 't3':'t4', 't4':'t3', 't5':'t2', 't6':'t1'}

def round0_member(topic: str, agent_output: str):
    """Agente escreve Statement inicial sobre seu tópico."""
    Path(f'syntegration/{topic}_member.md').write_text(agent_output)

def round1_critic(topic: str, agent_output: str):
    """Agente lê Statement do tópico oposto e escreve crítica."""
    opposite = OPPOSITES[topic]
    context = Path(f'syntegration/{opposite}_member.md').read_text()
    # Claude lê context e escreve crítica adversarial
    Path(f'syntegration/{topic}_critic.md').write_text(agent_output)

def round2_revision(topic: str, agent_output: str):
    """Member revisa Statement à luz da crítica recebida."""
    Path(f'syntegration/{topic}_v2.md').write_text(agent_output)

def round3_synthesis(meta_output: str):
    """Meta-agente (S4) integra todos os tópicos revisados."""
    Path('syntegration/final_synthesis.md').write_text(meta_output)
```

### Regra geométrica para escolha de estrutura async

```
Grupo pequeno (2–6 agentes):   Tetraedro — 1 rodada, custo mínimo
Grupo médio (6–15 agentes):    Octaedro — 4 rodadas, tensão adversarial
Grupo grande (15–30 agentes):  Icosaedro — 4 rodadas, máxima resiliência
Acima de 30:                   Recursão — INFOSET de INFOSETs (Beer)
```

**Para o PTD-BR (~90 órgãos)**: usar octaedro de 6 meta-tópicos (um por eixo EFGD),
onde cada agente é responsável por 1 eixo como Member e critica o eixo oposto.
Meta-agente S4 integra na Rodada 3.

---

## Texto completo no GitHub

🔗 **[VSM_CLAUDE_SPINOFF.md — branch claude/setup-docling-pipeline-g11gg](https://github.com/freirelucas/teste/blob/claude/setup-docling-pipeline-g11gg/VSM_CLAUDE_SPINOFF.md)**

---

*Este documento é o spin-off conceitual do PTD-BR Pipeline.
Template reutilizável: copie `.claude/settings.json` + hooks + seção CLAUDE.md
para qualquer projeto de automação autônoma com loops de aprendizado.*

**PTD-BR Pipeline — IPEA/COGIT/DIEST — 2026**
