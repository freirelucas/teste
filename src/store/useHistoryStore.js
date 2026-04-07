import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useHistoryStore = create(
  persist(
    (set, get) => ({
      readings: [],

      addReading(reading) {
        set((state) => ({
          readings: [
            {
              ...reading,
              id: Date.now(),
              timestamp: new Date().toISOString(),
            },
            ...state.readings,
          ],
        }))
      },

      clearHistory() {
        set({ readings: [] })
      },

      getReading(id) {
        return get().readings.find((r) => r.id === id)
      },
    }),
    {
      name: 'tarot-ciberquilombola-history',
    }
  )
)
