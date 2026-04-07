import { useReadingStore } from '../../store/useReadingStore'
import Card from '../Card/Card.jsx'
import './Spread.css'

export default function Spread() {
  const { spread, drawnCards, reversed, revealed, phase, drawCards, revealCard, reset } =
    useReadingStore()

  if (!spread) {
    return (
      <div className="spread__empty">
        <p className="spread__prompt">Selecione um modo de leitura acima para começar o diagnóstico.</p>
      </div>
    )
  }

  const hasCards = drawnCards.length > 0

  return (
    <div className="spread">
      <div className="spread__info">
        <h2 className="spread__title">{spread.name_pt}</h2>
        <p className="spread__description">{spread.description_pt}</p>
      </div>

      {!hasCards && (
        <button className="spread__draw-btn" onClick={drawCards}>
          &#x2735; SORTEAR {spread.card_count} {spread.card_count === 1 ? 'CARTA' : 'CARTAS'}
        </button>
      )}

      {hasCards && (
        <div className={`spread__grid spread__grid--${spread.id}`}>
          {drawnCards.map((card, i) => (
            <div key={card.id} className="spread__slot">
              <Card
                card={card}
                isReversed={reversed[i]}
                isRevealed={!!revealed[i]}
                position={spread.positions[i]}
                onClick={() => !revealed[i] && revealCard(i)}
              />
              <span className="spread__slot-label">{spread.positions[i].label}</span>
            </div>
          ))}
        </div>
      )}

      {hasCards && phase === 'drawing' && (
        <p className="spread__hint">Clique em cada carta para revelá-la.</p>
      )}

      {hasCards && (
        <button className="spread__reset-btn" onClick={reset}>
          &#x21BB; Recomeçar
        </button>
      )}
    </div>
  )
}
