import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useImport } from '../hooks/useImport'
import ImportProgress from '../components/ImportProgress'

export default function Landing() {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [maxGames, setMaxGames] = useState(100)
  const { status, isImporting, error, startImport } = useImport()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = username.trim()
    if (!trimmed) return
    try {
      await startImport(trimmed, maxGames)
    } catch {
      // error shown via hook
    }
  }

  const handleSkip = () => {
    const trimmed = username.trim()
    if (trimmed) {
      navigate(`/dashboard?username=${encodeURIComponent(trimmed)}`)
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4">
      <div className="mb-10 text-center">
        <div className="text-6xl mb-4">♟</div>
        <h1 className="text-4xl font-bold text-gray-100 mb-2">Chess Analyzer</h1>
        <p className="text-gray-400 text-lg">
          Import your Lichess games and discover what's holding you back.
        </p>
      </div>

      {!isImporting && !status ? (
        <form onSubmit={handleSubmit} className="card max-w-md w-full space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1.5">
              Lichess Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. DrNykterstein"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-gray-100 placeholder-gray-500 focus:outline-none focus:border-emerald-500 transition-colors"
              autoFocus
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1.5">
              Games to import
            </label>
            <select
              value={maxGames}
              onChange={(e) => setMaxGames(Number(e.target.value))}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-gray-100 focus:outline-none focus:border-emerald-500"
            >
              <option value={25}>25 games (fast)</option>
              <option value={50}>50 games</option>
              <option value={100}>100 games (recommended)</option>
              <option value={200}>200 games</option>
              <option value={300}>300 games (slow)</option>
            </select>
          </div>

          {error && (
            <div className="bg-red-900/30 border border-red-700 rounded-lg p-3 text-red-300 text-sm">
              {error}
            </div>
          )}

          <div className="flex gap-3">
            <button type="submit" className="btn-primary flex-1" disabled={!username.trim()}>
              Import & Analyse
            </button>
            <button
              type="button"
              className="btn-secondary"
              onClick={handleSkip}
              disabled={!username.trim()}
              title="View dashboard for already-imported data"
            >
              View Dashboard
            </button>
          </div>

          <p className="text-xs text-gray-500 text-center">
            Only public games are imported. No login required.
          </p>
        </form>
      ) : (
        status && (
          <ImportProgress status={status} username={username} />
        )
      )}

      <div className="mt-12 grid grid-cols-2 md:grid-cols-4 gap-4 max-w-2xl w-full">
        {[
          { icon: '📊', label: 'Pattern Analysis', desc: 'Win rates per habit' },
          { icon: '♟', label: 'Game Replay', desc: 'Review with evals' },
          { icon: '🧩', label: 'Puzzles', desc: 'From your mistakes' },
          { icon: '🤖', label: 'AI Coach', desc: 'Powered by Claude' },
        ].map((f) => (
          <div key={f.label} className="card text-center py-5">
            <div className="text-3xl mb-2">{f.icon}</div>
            <div className="font-semibold text-gray-200 text-sm">{f.label}</div>
            <div className="text-gray-500 text-xs mt-1">{f.desc}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
