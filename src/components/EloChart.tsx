import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { EloPoint } from '../api'

interface Props {
  data: EloPoint[]
}

export default function EloChart({ data }: Props) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-gray-500 text-sm">
        No ELO history available
      </div>
    )
  }

  const minElo = Math.min(...data.map((d) => d.elo)) - 50
  const maxElo = Math.max(...data.map((d) => d.elo)) + 50

  // Thin out labels for readability
  const tickIndices = new Set<number>()
  if (data.length <= 10) {
    data.forEach((_, i) => tickIndices.add(i))
  } else {
    for (let i = 0; i < data.length; i += Math.floor(data.length / 6)) {
      tickIndices.add(i)
    }
    tickIndices.add(data.length - 1)
  }

  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
        <XAxis
          dataKey="date"
          tick={{ fill: '#6b7280', fontSize: 11 }}
          tickFormatter={(v, i) => (tickIndices.has(i) ? v.slice(5) : '')}
          interval={0}
        />
        <YAxis
          domain={[minElo, maxElo]}
          tick={{ fill: '#6b7280', fontSize: 11 }}
          width={45}
        />
        <Tooltip
          contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8 }}
          labelStyle={{ color: '#9ca3af' }}
          itemStyle={{ color: '#34d399' }}
        />
        <Line
          type="monotone"
          dataKey="elo"
          stroke="#34d399"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4, fill: '#34d399' }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
