import { useReadingStore } from '../../store/useReadingStore'
import spreads from '../../data/spreads.json'
import './Shell.css'

export default function Shell({ children }) {
  const { mode, setMode, reset, phase } = useReadingStore()

  return (
    <div className="shell">
      <header className="shell__header">
        <div className="shell__title-group">
          <h1 className="shell__title cursor-blink">TAROT CIBERNÉTICO</h1>
          <p className="shell__subtitle">diagnóstico sistêmico · Beer × Bispo</p>
        </div>
      </header>

      <nav className="shell__nav">
        {spreads.map((spread) => (
          <button
            key={spread.id}
            className={`shell__nav-btn ${mode === spread.id ? 'shell__nav-btn--active' : ''}`}
            onClick={() => {
              if (phase !== 'idle' && mode !== spread.id) {
                reset()
              }
              setMode(spread.id)
            }}
          >
            <span className="shell__nav-count">{spread.card_count}</span>
            <span className="shell__nav-label">{spread.name_pt}</span>
          </button>
        ))}
      </nav>

      <main className="shell__main">{children}</main>

      <footer className="shell__footer">
        <div className="shell__quote">
          <p>&ldquo;The purpose of a system is what it does.&rdquo;</p>
          <cite>— Stafford Beer</cite>
        </div>
        <div className="shell__quote">
          <p>&ldquo;A terra não é uma só. Cada terra tem seu jeito de ser terra.&rdquo;</p>
          <cite>— Antônio Bispo dos Santos</cite>
        </div>
      </footer>
    </div>
  )
}
