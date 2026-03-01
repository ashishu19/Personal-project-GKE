import { useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { useStyle } from '../hooks/useStats'
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip } from 'recharts'

export default function StyleMatch() {
  const [params] = useSearchParams()
  const username = params.get('username') || ''
  const { data, loading, error } = useStyle(username)
  const [revealed, setRevealed] = useState(false)

  const radarData = data
    ? [
        { metric: 'Exchange Seeking', value: Math.round((data.user_style_vector.piece_exchange_preference + 1) * 50) },
        { metric: 'Queen Activity', value: Math.round(data.user_style_vector.queen_activity * 100) },
        { metric: 'Pawn Advances', value: Math.round(data.user_style_vector.pawn_advance_rate * 100) },
        { metric: 'Tactical Play', value: Math.round(data.user_style_vector.tactical_complexity * 100) },
        { metric: 'Endgame Entry', value: Math.round(data.user_style_vector.endgame_entry_rate * 100) },
      ]
    : []

  return (
    <div className="min-h-screen">
      <nav className="border-b border-gray-800 px-6 py-4 flex items-center gap-4">
        <Link to={`/dashboard?username=${encodeURIComponent(username)}`}
          className="text-gray-400 hover:text-gray-100 text-sm">← Dashboard</Link>
        <h1 className="text-lg font-semibold text-gray-100">Style Match</h1>
        <span className="text-emerald-400 text-sm ml-auto">{username}</span>
      </nav>

      <main className="max-w-3xl mx-auto px-6 py-10">
        {loading && <div className="text-gray-500 animate-pulse text-center mt-20">Computing style match…</div>}

        {error && (
          <div className="card border-yellow-700 text-yellow-300 text-sm mt-10">
            {error} — Import more games for a style match.
          </div>
        )}

        {data && (
          <div className="space-y-8">
            {/* Radar chart */}
            <div className="card">
              <h2 className="font-semibold text-gray-200 mb-4 text-center">Your Style Profile</h2>
              <ResponsiveContainer width="100%" height={280}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#374151" />
                  <PolarAngleAxis dataKey="metric" tick={{ fill: '#9ca3af', fontSize: 12 }} />
                  <Radar dataKey="value" stroke="#34d399" fill="#34d399" fillOpacity={0.2} />
                  <Tooltip
                    contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8 }}
                    formatter={(v: number) => [`${v}%`, '']}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>

            {/* GM Match reveal */}
            <div className="card text-center">
              <p className="text-gray-400 text-sm mb-4">Your playstyle most closely matches…</p>

              {!revealed ? (
                <button
                  onClick={() => setRevealed(true)}
                  className="btn-primary px-12 py-3 text-lg"
                >
                  Reveal My GM Match ✨
                </button>
              ) : (
                <div className="space-y-4">
                  <div className="text-5xl">♛</div>
                  <h2 className="text-3xl font-bold text-emerald-400">{data.matched_gm}</h2>
                  <div className="text-gray-400">
                    <span className="font-mono text-emerald-600 mr-2">{data.gm_title}</span>
                    {data.archetype}
                  </div>
                  <div className="text-sm text-gray-500">
                    Similarity: {Math.round(data.similarity_score * 100)}%
                  </div>

                  <div className="bg-gray-800 rounded-xl p-5 text-left mt-4">
                    <p className="text-gray-200 text-sm leading-relaxed">{data.description}</p>
                  </div>

                  <div className="bg-emerald-900/20 border border-emerald-800 rounded-xl p-4 text-left">
                    <h3 className="text-emerald-400 font-semibold mb-2 text-sm">📚 Study Tip</h3>
                    <p className="text-gray-300 text-sm leading-relaxed">{data.study_tip}</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
