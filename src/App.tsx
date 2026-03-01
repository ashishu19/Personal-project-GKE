import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Landing from './pages/Landing'
import Dashboard from './pages/Dashboard'
import Patterns from './pages/Patterns'
import StyleMatch from './pages/StyleMatch'
import Suggestions from './pages/Suggestions'
import Games from './pages/Games'
import GameReplay from './pages/GameReplay'
import Puzzles from './pages/Puzzles'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/patterns" element={<Patterns />} />
        <Route path="/style" element={<StyleMatch />} />
        <Route path="/suggestions" element={<Suggestions />} />
        <Route path="/games" element={<Games />} />
        <Route path="/games/:gameId" element={<GameReplay />} />
        <Route path="/puzzles" element={<Puzzles />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
