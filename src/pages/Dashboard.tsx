import { useSearchParams, Link } from 'react-router-dom'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'
import { useOverview, usePatterns } from '../hooks/useStats'
import EloChart from '../components/EloChart'
import PatternCard from '../components/PatternCard'

const NAV_LINKS = [
  { to: '/patterns', label: '📊 Patterns' },
  { to: '/games', label: '♟ Games' },
  { to: '/puzzles', label: '🧩 Puzzles' },
  { to: '/style', label: '🎭 Style Match' },
  { to: '/suggestions', label: '🤖 AI Coach' },
]

export default function Dashboard() {
  const [params] = useSearchParams()
  const username = params.get('username') || ''
  const { data: overview, loading: ovLoading, error: ovError } = useOverview(username)
  const { data: patterns } = usePatterns(username)

  if (!username) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-400 mb-4">No username specified.</p>
          <Link to="/" className="btn-primary">Go to Import</Link>
        </div>
      </div>
    )
  }

  const topPatterns = patterns?.patterns?.filter((p) => p.is_significant).slice(0, 3) ?? []

  const pieData = overview
    ? [
        { name: 'Wins', value: overview.wins, color: '#34d399' },
        { name: 'Draws', value: overview.draws, color: '#6b7280' },
        { name: 'Losses', value: overview.losses, color: '#f87171' },
      ]
    : []

  return (
    <div className="min-h-screen">
      {/* Nav */}
      <nav className="border-b border-gray-800 px-6 py-4 flex items-center gap-6">
        <Link to="/" className="text-xl font-bold text-gray-100">♟ Chess Analyzer</Link>
        <span className="text-gray-600">/</span>
        <span className="text-emerald-400 font-semibold">{username}</span>
        <div className="ml-auto flex gap-3">
          {NAV_LINKS.map((l) => (
            <Link key={l.to} to={`${l.to}?username=${encodeURIComponent(username)}`}
              className="text-sm text-gray-400 hover:text-gray-100 transition-colors">
              {l.label}
            </Link>
          ))}
        </div>
      </nav>

      <main className="max-w-6xl mx-auto px-6 py-8 space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-100">{username}</h1>
            {overview && (
              <p className="text-gray-400 mt-1">
                {overview.current_elo ? `ELO ${overview.current_elo} · ` : ''}
                {overview.total_games} games analysed
              </p>
            )}
          </div>
          <Link to={`/games?username=${encodeURIComponent(username)}`}
            className="btn-secondary text-sm">
            View All Games →
          </Link>
        </div>

        {ovError && (
          <div className="card border-red-800 text-red-300 text-sm">
            {ovError} — Try importing games first.
          </div>
        )}

        {ovLoading && (
          <div className="text-gray-500 animate-pulse">Loading overview…</div>
        )}

        {overview && (
          <>
            {/* Stats row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: 'Total Games', value: overview.total_games },
                { label: 'Win Rate', value: `${Math.round(overview.win_rate * 100)}%` },
                { label: 'Avg CPL', value: overview.avg_cpl ? overview.avg_cpl.toFixed(1) : '—' },
                { label: 'Current ELO', value: overview.current_elo ?? '—' },
              ].map((s) => (
                <div key={s.label} className="card text-center">
                  <div className="text-3xl font-bold text-emerald-400">{s.value}</div>
                  <div className="text-gray-400 text-sm mt-1">{s.label}</div>
                </div>
              ))}
            </div>

            {/* Charts row */}
            <div className="grid md:grid-cols-3 gap-6">
              <div className="card md:col-span-2">
                <h2 className="font-semibold text-gray-200 mb-4">ELO Trend</h2>
                <EloChart data={overview.elo_trend} />
              </div>

              <div className="card">
                <h2 className="font-semibold text-gray-200 mb-4">Results</h2>
                <ResponsiveContainer width="100%" height={160}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={45}
                      outerRadius={70}
                      dataKey="value"
                    >
                      {pieData.map((entry) => (
                        <Cell key={entry.name} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8 }}
                      itemStyle={{ color: '#d1d5db' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
                <div className="flex justify-center gap-4 mt-2 text-xs">
                  <span className="text-emerald-400">● W:{overview.wins}</span>
                  <span className="text-gray-400">● D:{overview.draws}</span>
                  <span className="text-red-400">● L:{overview.losses}</span>
                </div>
              </div>
            </div>

            {/* Top patterns */}
            {topPatterns.length > 0 && (
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="font-semibold text-gray-200">Top Patterns</h2>
                  <Link to={`/patterns?username=${encodeURIComponent(username)}`}
                    className="text-sm text-emerald-400 hover:text-emerald-300">
                    View all →
                  </Link>
                </div>
                <div className="grid md:grid-cols-3 gap-4">
                  {topPatterns.map((p) => (
                    <PatternCard key={p.feature} pattern={p} />
                  ))}
                </div>
              </div>
            )}

            {/* Quick links */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Link to={`/style?username=${encodeURIComponent(username)}`}
                className="card hover:border-emerald-700 transition-colors text-center cursor-pointer">
                <div className="text-2xl mb-1">🎭</div>
                <div className="font-medium text-gray-200 text-sm">Style Match</div>
                <div className="text-gray-500 text-xs mt-1">Which GM are you?</div>
              </Link>
              <Link to={`/puzzles?username=${encodeURIComponent(username)}`}
                className="card hover:border-emerald-700 transition-colors text-center cursor-pointer">
                <div className="text-2xl mb-1">🧩</div>
                <div className="font-medium text-gray-200 text-sm">Puzzles</div>
                <div className="text-gray-500 text-xs mt-1">From your mistakes</div>
              </Link>
              <Link to={`/suggestions?username=${encodeURIComponent(username)}`}
                className="card hover:border-emerald-700 transition-colors text-center cursor-pointer">
                <div className="text-2xl mb-1">🤖</div>
                <div className="font-medium text-gray-200 text-sm">AI Coach</div>
                <div className="text-gray-500 text-xs mt-1">Get improvement tips</div>
              </Link>
              <Link to={`/games?username=${encodeURIComponent(username)}`}
                className="card hover:border-emerald-700 transition-colors text-center cursor-pointer">
                <div className="text-2xl mb-1">♟</div>
                <div className="font-medium text-gray-200 text-sm">Games</div>
                <div className="text-gray-500 text-xs mt-1">Browse & replay</div>
              </Link>
            </div>
          </>
        )}
      </main>
    </div>
  )
}
