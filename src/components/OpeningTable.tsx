import { OpeningStat } from '../api'

interface Props {
  openings: OpeningStat[]
}

export default function OpeningTable({ openings }: Props) {
  if (openings.length === 0) {
    return <p className="text-gray-500 text-sm">No opening data available.</p>
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-gray-400 border-b border-gray-800">
            <th className="text-left py-2 pr-4">ECO</th>
            <th className="text-left py-2 pr-4">Opening</th>
            <th className="text-right py-2 pr-4">Games</th>
            <th className="text-right py-2 pr-4">W/D/L</th>
            <th className="text-right py-2">Win%</th>
          </tr>
        </thead>
        <tbody>
          {openings.map((o) => (
            <tr key={o.eco} className="border-b border-gray-800/50 hover:bg-gray-800/30">
              <td className="py-2 pr-4 font-mono text-xs text-gray-400">{o.eco}</td>
              <td className="py-2 pr-4 text-gray-200 max-w-xs truncate">{o.name}</td>
              <td className="py-2 pr-4 text-right text-gray-300">{o.games}</td>
              <td className="py-2 pr-4 text-right text-gray-400">
                <span className="text-emerald-400">{o.wins}</span>/
                <span className="text-gray-400">{o.draws}</span>/
                <span className="text-red-400">{o.losses}</span>
              </td>
              <td className="py-2 text-right">
                <span
                  className={`font-semibold ${
                    o.win_rate >= 0.55
                      ? 'text-emerald-400'
                      : o.win_rate <= 0.4
                      ? 'text-red-400'
                      : 'text-gray-300'
                  }`}
                >
                  {Math.round(o.win_rate * 100)}%
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
