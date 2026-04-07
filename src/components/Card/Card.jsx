import './Card.css'

const ACT_LABELS = {
  0: 'Fora da Sequência',
  1: 'Brain of the Firm',
  2: 'Diagnosing the System',
  3: 'Platform for Change',
}

const SUIT_LABELS = {
  circuitos: 'Circuitos',
  territorios: 'Territórios',
  ferramentas: 'Ferramentas',
  sinais: 'Sinais',
}

const SUIT_ICONS = {
  circuitos: '\u21BB',
  territorios: '\u2302',
  ferramentas: '\u2692',
  sinais: '\u2632',
}

export default function Card({ card, isReversed, isRevealed, position, onClick }) {
  return (
    <div
      className={`card ${isRevealed ? 'card--revealed' : ''} ${isReversed && isRevealed ? 'card--reversed' : ''}`}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onClick?.()}
      aria-label={
        isRevealed
          ? `${card.name_pt}${isReversed ? ' (reversa)' : ''}`
          : 'Carta oculta — clique para revelar'
      }
    >
      <div className="card__inner">
        {/* Back face */}
        <div className="card__back">
          <div className="card__back-pattern">
            <div className="card__back-border" />
            <div className="card__back-symbol">&#x2735;</div>
            <span className="card__back-label">TAROT<br />CIBERQUILOMBOLA</span>
          </div>
        </div>

        {/* Front face */}
        <div className={`card__front ${card.suit ? `card__front--${card.suit}` : ''}`}>
          <div className="card__header">
            <span className="card__numeral">{card.numeral}</span>
            <span className={`card__act ${card.suit ? `card__act--${card.suit}` : ''}`}>
              {card.suit
                ? `${SUIT_ICONS[card.suit]} ${SUIT_LABELS[card.suit]}`
                : ACT_LABELS[card.act]}
            </span>
          </div>
          <h3 className="card__name">{card.name_pt}</h3>
          <p className="card__concept">{card.concept_pt}</p>
          {position && (
            <div className="card__position">
              <span className="card__position-label">{position.label}</span>
            </div>
          )}
          <div className="card__footer">
            <p className="card__dito">
              <em>{card.dito_pt}</em>
            </p>
            <p className="card__dito-source">— {card.dito_source}</p>
          </div>
        </div>
      </div>
    </div>
  )
}
