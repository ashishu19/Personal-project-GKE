import { PatternStat } from '../api'

interface Props {
  pattern: PatternStat
}

export default function PatternCard({ pattern }: Props) {
  const deltaPct = Math.round(pattern.delta * 100)
  const withPct = Math.round(pattern.win_rate_with * 100)
  const withoutPct = Math.round(pattern.win_rate_without * 100)
  const isPositive = deltaPct > 0

  return (
    <div className={`card border-l-4 ${isPositive ? 'border-l-emerald-500' : 'border-l-red-500'}`}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold text-gray-100">{pattern.label}</h3>
          {!pattern.is_significant && (
            <span className="text-xs text-yellow-500 mt-0.5 block">
              Emerging pattern (low sample)
            </span>
          )}
        </div>
        <span
          className={`text-xl font-bold shrink-0 ${isPositive ? 'text-emerald-400' : 'text-red-400'}`}
        >
          {isPositive ? '+' : ''}{deltaPct}%
        </span>
      </div>

      <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
        <div className="bg-gray-800 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-emerald-400">{withPct}%</div>
          <div className="text-gray-400 text-xs mt-1">Win rate WITH</div>
          <div className="text-gray-500 text-xs">{pattern.sample_size_with} games</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-gray-300">{withoutPct}%</div>
          <div className="text-gray-400 text-xs mt-1">Win rate WITHOUT</div>
          <div className="text-gray-500 text-xs">{pattern.sample_size_without} games</div>
        </div>
      </div>
    </div>
  )
}
