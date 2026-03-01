import { useState } from 'react'
import { useSearchParams, Link, useNavigate } from 'react-router-dom'
import { api, GameSummary } from '../api'
import { useQuery } from '../hooks/useQuery'

function ResultBadge({ result }: { result: string }) {
  if (result === 'win') return <span className="badge-win">Win</span>
  if (result === 'loss') return <span className="badge-loss">Loss</span>
  return <span className="badge-draw">Draw</span>
}

export default function Games() {
  const [params] = useSearchParams()
  const username = params.get('username') || ''
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const [resultFilter, setResultFilter] = useState('')

  const { data, loading, error } = useQuery(
    () => api.getGames(username, page, 20, resultFilter || undefined),
    [username, page, resultFilter],
  )

  return (
    <div className="min-h-screen">
      <nav className="border-b border-gray-800 px-6 py-4 flex items-center gap-4">
        <Link to={`/dashboard?username=${encodeURIComponent(username)}`}
          className="text-gray-400 hover:text-gray-100 text-sm">← Dashboard</Link>
        <h1 className="text-lg font-semibold text-gray-100">Games</h1>
        <span className="text-emerald-400 text-sm ml-auto">{username}</span>
      </nav>

      <main className="max-w-5xl mx-auto px-6 py-8">
        {/* Filters */}
        <div className="flex gap-3 mb-6">
          {['', 'win', 'draw', 'loss'].map((r) => (
            <button
              key={r}
              onClick={() => { setResultFilter(r); setPage(1) }}
              className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                resultFilter === r
                  ? 'bg-emerald-700 text-white'
                  : 'bg-gray-800 text-gray-400 hover:text-gray-100'
              }`}
            >
              {r === '' ? 'All' : r.charAt(0).toUpperCase() + r.slice(1) + 's'}
            </button>
          ))}
        </div>

        {loading && <div className="text-gray-500 animate-pulse">Loading games…</div>}
        {error && <div className="text-red-400 text-sm">{error}</div>}

        {data && (
          <>
            <div className="card overflow-hidden p-0">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-gray-400 border-b border-gray-800 bg-gray-900/50">
                    <th className="text-left px-4 py-3">Result</th>
                    <th className="text-left px-4 py-3">Opening</th>
                    <th className="text-right px-4 py-3">ELO</th>
                    <th className="text-right px-4 py-3">CPL</th>
                    <th className="text-right px-4 py-3">Blunders</th>
                    <th className="text-right px-4 py-3">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {data.games.map((g: GameSummary) => (
                    <tr
                      key={g.game_id}
                      onClick={() => navigate(`/games/${g.game_id}?username=${encodeURIComponent(username)}`)}
                      className="border-b border-gray-800/50 hover:bg-gray-800/40 cursor-pointer transition-colors"
                    >
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <ResultBadge result={g.result} />
                          <span className="text-gray-500 text-xs">{g.user_color}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 max-w-xs">
                        <div className="text-gray-200 truncate">{g.opening_name || '—'}</div>
                        <div className="text-gray-500 text-xs font-mono">{g.opening_eco || ''}</div>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <span className="text-gray-300">{g.user_elo ?? '?'}</span>
                        {g.opponent_elo && (
                          <span className="text-gray-600 text-xs ml-1">vs {g.opponent_elo}</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        {g.has_evals && g.avg_cpl != null ? (
                          <span className={g.avg_cpl > 100 ? 'text-red-400' : g.avg_cpl > 50 ? 'text-yellow-400' : 'text-emerald-400'}>
                            {g.avg_cpl.toFixed(0)}
                          </span>
                        ) : (
                          <span className="text-gray-600">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        {g.blunders > 0 ? (
                          <span className="text-red-400 font-semibold">{g.blunders}</span>
                        ) : (
                          <span className="text-gray-600">0</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right text-gray-500 text-xs">
                        {g.played_at ? new Date(g.played_at).toLocaleDateString() : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between mt-4">
              <span className="text-gray-500 text-sm">
                {data.total} games total
              </span>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="btn-secondary text-sm disabled:opacity-40"
                >
                  ← Prev
                </button>
                <span className="text-gray-400 text-sm px-3 py-2">
                  Page {page} of {Math.ceil(data.total / 20)}
                </span>
                <button
                  onClick={() => setPage((p) => p + 1)}
                  disabled={page * 20 >= data.total}
                  className="btn-secondary text-sm disabled:opacity-40"
                >
                  Next →
                </button>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  )
}
