import { useState, useEffect, useCallback } from 'react'
import { useParams, useSearchParams, Link } from 'react-router-dom'
import { Chess } from 'chess.js'
import { api, GameDetailResponse, PositionDetail } from '../api'
import ChessBoard from '../components/ChessBoard'

const START_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

function EvalBar({ score }: { score?: number }) {
  if (score == null) return null
  const clamped = Math.max(-5, Math.min(5, score))
  const whitePct = Math.round(((clamped + 5) / 10) * 100)
  return (
    <div className="w-6 h-full rounded overflow-hidden bg-gray-800 flex flex-col" title={`Eval: ${score > 0 ? '+' : ''}${score.toFixed(2)}`}>
      <div style={{ height: `${100 - whitePct}%` }} className="bg-gray-900 transition-all duration-200" />
      <div style={{ height: `${whitePct}%` }} className="bg-gray-100 transition-all duration-200" />
    </div>
  )
}

export default function GameReplay() {
  const { gameId } = useParams<{ gameId: string }>()
  const [searchParams] = useSearchParams()
  const username = searchParams.get('username') || ''

  const [game, setGame] = useState<GameDetailResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [moveIndex, setMoveIndex] = useState(-1) // -1 = starting position

  useEffect(() => {
    if (!gameId) return
    api.getGame(gameId)
      .then(setGame)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [gameId])

  const positions: PositionDetail[] = game?.positions ?? []
  const currentFen = moveIndex === -1 ? START_FEN : positions[moveIndex]?.fen ?? START_FEN
  const currentPos = moveIndex >= 0 ? positions[moveIndex] : null
  const currentEval = currentPos?.eval_score

  const canPrev = moveIndex > -1
  const canNext = moveIndex < positions.length - 1

  const goTo = useCallback((idx: number) => {
    setMoveIndex(Math.max(-1, Math.min(positions.length - 1, idx)))
  }, [positions.length])

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'ArrowLeft') goTo(moveIndex - 1)
      if (e.key === 'ArrowRight') goTo(moveIndex + 1)
      if (e.key === 'ArrowUp') goTo(-1)
      if (e.key === 'ArrowDown') goTo(positions.length - 1)
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [moveIndex, goTo, positions.length])

  // Highlight squares
  const highlightSquares: Record<string, { backgroundColor: string }> = {}
  if (currentPos?.is_blunder) {
    const uci = currentPos.played_move
    if (uci && uci.length >= 4) {
      highlightSquares[uci.slice(0, 2)] = { backgroundColor: 'rgba(239, 68, 68, 0.4)' }
      highlightSquares[uci.slice(2, 4)] = { backgroundColor: 'rgba(239, 68, 68, 0.5)' }
    }
  }

  // Best move arrow
  const arrowSquares: Array<[string, string]> = []
  if (currentPos?.best_move && currentPos.best_move.length >= 4) {
    arrowSquares.push([currentPos.best_move.slice(0, 2), currentPos.best_move.slice(2, 4)])
  }

  // Build move labels using chess.js SAN from positions
  const chess = new Chess()
  const moveSans: string[] = []
  for (const pos of positions) {
    if (pos.played_move) {
      try {
        const promotion = pos.played_move[4] as 'q' | 'r' | 'b' | 'n' | undefined
        const result = chess.move({ from: pos.played_move.slice(0, 2), to: pos.played_move.slice(2, 4), promotion })
        moveSans.push(result.san)
      } catch {
        moveSans.push(pos.played_move)
      }
    }
  }

  return (
    <div className="min-h-screen">
      <nav className="border-b border-gray-800 px-6 py-4 flex items-center gap-4">
        <Link to={`/games?username=${encodeURIComponent(username)}`}
          className="text-gray-400 hover:text-gray-100 text-sm">← Games</Link>
        <h1 className="text-lg font-semibold text-gray-100">Game Replay</h1>
        {game && (
          <span className="text-gray-500 text-sm">
            {game.opening_name || 'Unknown Opening'} ·{' '}
            <span className={game.result === 'win' ? 'text-emerald-400' : game.result === 'loss' ? 'text-red-400' : 'text-gray-400'}>
              {game.result}
            </span>
          </span>
        )}
      </nav>

      {loading && <div className="p-8 text-gray-500 animate-pulse">Loading game…</div>}
      {error && <div className="p-8 text-red-400">{error}</div>}

      {game && (
        <div className="flex gap-0 h-[calc(100vh-65px)]">
          {/* Eval bar */}
          <div className="p-3 flex flex-col justify-center" style={{ width: 40 }}>
            <EvalBar score={currentEval} />
          </div>

          {/* Board */}
          <div className="flex flex-col items-center justify-center p-4">
            <ChessBoard
              fen={currentFen}
              orientation={game.user_color as 'white' | 'black'}
              highlightSquares={highlightSquares}
              arrowSquares={arrowSquares}
              width={480}
            />

            {/* Controls */}
            <div className="flex items-center gap-3 mt-4">
              <button onClick={() => goTo(-1)} className="btn-secondary text-xs px-3">⏮</button>
              <button onClick={() => goTo(moveIndex - 1)} disabled={!canPrev} className="btn-secondary text-xs px-3 disabled:opacity-40">←</button>
              <span className="text-gray-500 text-xs w-24 text-center">
                Move {moveIndex === -1 ? 0 : Math.floor(moveIndex / 2) + 1}
                {moveIndex >= 0 && (moveIndex % 2 === 0 ? ' (White)' : ' (Black)')}
              </span>
              <button onClick={() => goTo(moveIndex + 1)} disabled={!canNext} className="btn-secondary text-xs px-3 disabled:opacity-40">→</button>
              <button onClick={() => goTo(positions.length - 1)} className="btn-secondary text-xs px-3">⏭</button>
            </div>
            <p className="text-gray-600 text-xs mt-2">Arrow keys to navigate</p>

            {/* Current move annotation */}
            {currentPos && (
              <div className={`mt-3 px-4 py-2 rounded-lg text-sm text-center w-full max-w-sm ${
                currentPos.is_blunder ? 'bg-red-900/30 text-red-300 border border-red-800' :
                currentPos.cpl && currentPos.cpl > 50 ? 'bg-yellow-900/20 text-yellow-300' :
                'bg-gray-800/50 text-gray-400'
              }`}>
                {currentPos.is_blunder && '⚠️ Blunder · '}
                {currentPos.cpl != null && `CPL: ${currentPos.cpl.toFixed(0)}`}
                {currentPos.eval_score != null && ` · Eval: ${currentPos.eval_score > 0 ? '+' : ''}${currentPos.eval_score.toFixed(2)}`}
                {currentPos.clock_seconds != null && ` · Clock: ${Math.floor(currentPos.clock_seconds / 60)}:${String(Math.floor(currentPos.clock_seconds % 60)).padStart(2, '0')}`}
              </div>
            )}
          </div>

          {/* Move list */}
          <div className="flex-1 border-l border-gray-800 overflow-y-auto p-4">
            <h3 className="text-sm font-semibold text-gray-400 mb-3">Moves</h3>
            <div className="space-y-0.5">
              {positions.map((pos, i) => {
                const fullMove = Math.floor(i / 2) + 1
                const isWhite = i % 2 === 0
                const isActive = i === moveIndex
                const san = moveSans[i] || pos.played_move || '?'

                return (
                  <div key={i} className="flex">
                    {isWhite && (
                      <span className="text-gray-600 text-xs w-8 flex-shrink-0 pt-1.5">{fullMove}.</span>
                    )}
                    <button
                      onClick={() => setMoveIndex(i)}
                      className={`flex-1 text-left px-2 py-1 rounded text-sm transition-colors ${
                        isActive
                          ? 'bg-emerald-800 text-emerald-100'
                          : pos.is_blunder
                          ? 'text-red-400 hover:bg-gray-800'
                          : 'text-gray-300 hover:bg-gray-800'
                      }`}
                    >
                      {san}
                      {pos.is_blunder && <span className="ml-1 text-xs">⚠</span>}
                    </button>
                    {!isWhite && <div className="w-full" />}
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
