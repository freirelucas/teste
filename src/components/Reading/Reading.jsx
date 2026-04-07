import { useState } from 'react'
import { marked } from 'marked'
import { useReadingStore } from '../../store/useReadingStore'
import { useHistoryStore } from '../../store/useHistoryStore'
import { interpret } from '../../services/interpret'
import './Reading.css'

marked.setOptions({ breaks: true, gfm: true })

export default function Reading() {
  const { spread, drawnCards, reversed, interpretation, setInterpretation, setPhase, reset } =
    useReadingStore()
  const { addReading } = useHistoryStore()
  const [loading, setLoading] = useState(false)
  const [apiKey, setApiKey] = useState('')
  const [showApiInput, setShowApiInput] = useState(false)
  const [saved, setSaved] = useState(false)

  if (!spread || drawnCards.length === 0) return null

  async function handleInterpret(useApi) {
    setLoading(true)
    setPhase('interpreting')
    try {
      const key = useApi ? apiKey : null
      const result = await interpret(drawnCards, reversed, spread, key)
      setInterpretation(result.text)
    } catch {
      setInterpretation('Erro ao gerar interpretação. Tente novamente.')
    } finally {
      setLoading(false)
    }
  }

  function handleSave() {
    addReading({
      mode: spread.id,
      spreadName: spread.name_pt,
      cards: drawnCards.map((c, i) => ({
        id: c.id,
        name: c.name_pt,
        reversed: !!reversed[i],
        position: spread.positions[i].label,
      })),
      interpretation,
    })
    setSaved(true)
  }

  return (
    <div className="reading">
      {!interpretation && !loading && (
        <div className="reading__actions">
          <button className="reading__btn reading__btn--local" onClick={() => handleInterpret(false)}>
            &#x25B6; Diagnóstico Local
          </button>

          <div className="reading__divider">ou</div>

          {!showApiInput ? (
            <button
              className="reading__btn reading__btn--api"
              onClick={() => setShowApiInput(true)}
            >
              &#x2728; Diagnóstico com IA
            </button>
          ) : (
            <div className="reading__api-input">
              <label htmlFor="api-key" className="reading__api-label">
                Anthropic API Key (nunca é armazenada):
              </label>
              <input
                id="api-key"
                type="password"
                className="reading__input"
                placeholder="sk-ant-..."
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
              />
              <button
                className="reading__btn reading__btn--api"
                onClick={() => handleInterpret(true)}
                disabled={!apiKey}
              >
                &#x2728; Interpretar com Claude
              </button>
            </div>
          )}
        </div>
      )}

      {loading && (
        <div className="reading__loading">
          <span className="reading__spinner" />
          <p>Processando diagnóstico sistêmico...</p>
        </div>
      )}

      {interpretation && (
        <div className="reading__result">
          <div
            className="reading__text"
            dangerouslySetInnerHTML={{ __html: marked.parse(interpretation) }}
          />
          <div className="reading__result-actions">
            {!saved ? (
              <button className="reading__btn" onClick={handleSave}>
                Salvar no Histórico
              </button>
            ) : (
              <span className="reading__saved">Salvo no histórico local</span>
            )}
            <button className="reading__btn reading__btn--reset" onClick={reset}>
              Nova Leitura
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
