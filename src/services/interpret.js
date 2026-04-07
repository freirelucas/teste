const SUIT_LABELS = {
  circuitos: 'Circuitos',
  territorios: 'Territórios',
  ferramentas: 'Ferramentas',
  sinais: 'Sinais',
}

const SUIT_VSM = {
  circuitos: 'Informação & Feedback',
  territorios: 'Ambiente & Identidade',
  ferramentas: 'Operação & Ação',
  sinais: 'Comunicação & Algedonia',
}

const SYSTEM_PROMPT = `Você é o oráculo do Tarot CiberQuilombola — um sistema de diagnóstico que cruza a cibernética organizacional de Stafford Beer (Viable System Model) com o pensamento quilombola de Antônio Bispo dos Santos (Nego Bispo).

O deck tem 78 cartas:
- 22 Arcanos Maiores — conceitos fundamentais do VSM
- 56 Arcanos Menores em 4 naipes:
  • Circuitos (Informação & Feedback / Oralidade)
  • Territórios (Ambiente & Identidade / Terra & Lugar)
  • Ferramentas (Operação & Ação / Trabalho coletivo)
  • Sinais (Comunicação & Algedonia / Tambor & Canto)

Regras:
- NUNCA faça previsões. Isto é DIAGNÓSTICO, não adivinhação.
- Use linguagem direta, concreta, sistêmica.
- Conecte cada carta ao conceito cibernético que ela representa.
- Para Arcanos Menores, considere o naipe como contexto: ele indica o aspecto do VSM em foco.
- Quando houver citação de Bispo, traga o pensamento quilombola como contraponto.
- Aponte contradições, loops de feedback quebrados, variedade insuficiente.
- Termine com uma pergunta diagnóstica que force reflexão.
- Seja breve: máximo 3 parágrafos por carta, 1 parágrafo de síntese final.
- Escreva em português brasileiro.`

function buildLocalInterpretation(drawnCards, reversed, spread) {
  const lines = []
  lines.push(`## Diagnóstico: ${spread.name_pt}\n`)

  drawnCards.forEach((card, i) => {
    const pos = spread.positions[i]
    const isReversed = reversed[i]
    lines.push(`### ${pos.label} — ${card.numeral} ${card.name_pt}${isReversed ? ' (Reversa)' : ''}\n`)

    if (card.suit) {
      lines.push(`*Naipe: ${SUIT_LABELS[card.suit]} — ${SUIT_VSM[card.suit]}*\n`)
    }

    lines.push(`**${card.concept_pt}**\n`)

    if (isReversed) {
      lines.push(`${card.reversal_pt}\n`)
    } else {
      lines.push(`*${pos.description}*\n`)
      lines.push(`${card.diagnostic_question_pt}\n`)
    }

    lines.push(`> Sinal algedônico: ${card.algedonic_pt}\n`)

    if (card.anchor_beer) {
      lines.push(`> _"${card.anchor_beer}"_ — Beer\n`)
    }
    if (card.anchor_bispo) {
      lines.push(`> _"${card.anchor_bispo}"_ — Bispo\n`)
    }

    lines.push(`_${card.dito_pt}_ — ${card.dito_source}\n`)
    lines.push('')
  })

  lines.push('---\n')
  lines.push('**Pergunta diagnóstica final:** Olhando para este conjunto de cartas como um sistema: onde está o loop de feedback quebrado? Que variedade não está sendo absorvida?\n')

  return lines.join('\n')
}

export async function interpret(drawnCards, reversed, spread, apiKey) {
  // Always generate local fallback first
  const localResult = buildLocalInterpretation(drawnCards, reversed, spread)

  if (!apiKey) {
    return { text: localResult, source: 'local' }
  }

  const userPrompt = drawnCards
    .map((card, i) => {
      const pos = spread.positions[i]
      const rev = reversed[i] ? ' [REVERSA]' : ''
      const suitInfo = card.suit ? ` [${SUIT_LABELS[card.suit]}]` : ''
      return `Posição "${pos.label}": ${card.numeral} ${card.name_pt}${rev}${suitInfo} — ${card.concept_pt}`
    })
    .join('\n')

  try {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
        'anthropic-dangerous-direct-browser-access': 'true',
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-6-20250514',
        max_tokens: 2048,
        system: SYSTEM_PROMPT,
        messages: [
          {
            role: 'user',
            content: `Modo de leitura: ${spread.name_pt}\n\nCartas sorteadas:\n${userPrompt}\n\nFaça o diagnóstico sistêmico.`,
          },
        ],
      }),
    })

    if (!response.ok) {
      console.warn('API error, falling back to local interpretation')
      return { text: localResult, source: 'local' }
    }

    const data = await response.json()
    const aiText = data.content?.[0]?.text
    if (!aiText) {
      return { text: localResult, source: 'local' }
    }

    return { text: aiText, source: 'api' }
  } catch (err) {
    console.warn('API unavailable, using local interpretation:', err.message)
    return { text: localResult, source: 'local' }
  }
}
