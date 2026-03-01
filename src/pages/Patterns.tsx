import { useSearchParams, Link } from 'react-router-dom'
import { usePatterns } from '../hooks/useStats'
import PatternCard from '../components/PatternCard'

export default function Patterns() {
  const [params] = useSearchParams()
  const username = params.get('username') || ''
  const { data, loading, error } = usePatterns(username)

  return (
    <div className="min-h-screen">
      <nav className="border-b border-gray-800 px-6 py-4 flex items-center gap-4">
        <Link to={`/dashboard?username=${encodeURIComponent(username)}`}
          className="text-gray-400 hover:text-gray-100 text-sm">← Dashboard</Link>
        <h1 className="text-lg font-semibold text-gray-100">Pattern Analysis</h1>
        <span className="text-emerald-400 text-sm ml-auto">{username}</span>
      </nav>

      <main className="max-w-4xl mx-auto px-6 py-8">
        <p className="text-gray-400 mb-6 text-sm">
          How each habit correlates with your win rate. Patterns with fewer than 10 games
          are marked as low-confidence.
        </p>

        {loading && <div className="text-gray-500 animate-pulse">Analysing patterns…</div>}
        {error && <div className="text-red-400 text-sm">{error}</div>}

        {data && (
          <div className="space-y-4">
            {data.patterns.length === 0 ? (
              <p className="text-gray-500">No patterns found. Import more games to see results.</p>
            ) : (
              data.patterns.map((p) => (
                <PatternCard key={p.feature} pattern={p} />
              ))
            )}
          </div>
        )}
      </main>
    </div>
  )
}
