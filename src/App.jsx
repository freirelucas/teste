import { useReadingStore } from './store/useReadingStore'
import Shell from './components/Shell/Shell.jsx'
import Spread from './components/Spread/Spread.jsx'
import Reading from './components/Reading/Reading.jsx'

export default function App() {
  const phase = useReadingStore((s) => s.phase)

  return (
    <Shell>
      <Spread />
      {(phase === 'reading' || phase === 'interpreting') && <Reading />}
    </Shell>
  )
}
