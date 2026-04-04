import { create } from 'zustand'
import cards from '../data/cards.json'
import spreads from '../data/spreads.json'

function shuffleFisherYates(arr) {
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

export const useReadingStore = create((set, get) => ({
  mode: null,
  spread: null,
  drawnCards: [],
  reversed: {},
  revealed: {},
  phase: 'idle', // idle | drawing | reading | interpreting
  interpretation: null,

  setMode(modeId) {
    const spread = spreads.find((s) => s.id === modeId)
    if (!spread) return
    set({
      mode: modeId,
      spread,
      drawnCards: [],
      reversed: {},
      revealed: {},
      phase: 'idle',
      interpretation: null,
    })
  },

  drawCards() {
    const { spread } = get()
    if (!spread) return

    const pool = spread.deck === 'major'
      ? cards.filter((c) => c.arcana === 'major')
      : cards
    const shuffled = shuffleFisherYates(pool)
    const drawn = shuffled.slice(0, spread.card_count)
    const rev = {}
    drawn.forEach((card, i) => {
      rev[i] = Math.random() < 0.3
    })

    set({
      drawnCards: drawn,
      reversed: rev,
      revealed: {},
      phase: 'drawing',
      interpretation: null,
    })
  },

  revealCard(index) {
    set((state) => ({
      revealed: { ...state.revealed, [index]: true },
    }))
    // Check if all cards revealed
    const { spread, revealed } = get()
    const allRevealed =
      spread &&
      Array.from({ length: spread.card_count }, (_, i) => i).every(
        (i) => i === index || revealed[i]
      )
    if (allRevealed) {
      set({ phase: 'reading' })
    }
  },

  setInterpretation(text) {
    set({ interpretation: text, phase: 'reading' })
  },

  setPhase(phase) {
    set({ phase })
  },

  reset() {
    set({
      mode: null,
      spread: null,
      drawnCards: [],
      reversed: {},
      revealed: {},
      phase: 'idle',
      interpretation: null,
    })
  },
}))
