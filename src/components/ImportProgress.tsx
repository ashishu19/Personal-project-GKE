import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { ImportStatusResponse } from '../api'

interface Props {
  status: ImportStatusResponse
  username: string
  onDone?: () => void
}

export default function ImportProgress({ status, username, onDone }: Props) {
  const navigate = useNavigate()

  useEffect(() => {
    if (status.status === 'done') {
      onDone?.()
      const timer = setTimeout(() => {
        navigate(`/dashboard?username=${encodeURIComponent(username)}`)
      }, 800)
      return () => clearTimeout(timer)
    }
  }, [status.status, username, navigate, onDone])

  const pct = Math.min(100, status.progress_pct)
  const isDone = status.status === 'done'
  const isError = status.status === 'error'

  return (
    <div className="card max-w-lg w-full">
      <div className="flex items-center justify-between mb-3">
        <span className="font-semibold text-gray-200">
          {isDone ? 'Import complete!' : isError ? 'Import failed' : `Importing ${username}'s games…`}
        </span>
        <span className="text-sm text-gray-400">{pct.toFixed(0)}%</span>
      </div>

      <div className="w-full bg-gray-800 rounded-full h-3 overflow-hidden">
        <div
          className={`h-3 rounded-full transition-all duration-500 ${
            isError ? 'bg-red-500' : isDone ? 'bg-emerald-400' : 'bg-emerald-600'
          }`}
          style={{ width: `${pct}%` }}
        />
      </div>

      <p className="mt-3 text-sm text-gray-400">
        {isError
          ? status.error_message || 'Unknown error'
          : `${status.processed_games} / ${status.total_games} games processed`}
      </p>

      {isDone && (
        <p className="mt-2 text-emerald-400 text-sm">Redirecting to dashboard…</p>
      )}
    </div>
  )
}
