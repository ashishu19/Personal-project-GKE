import { useState, useCallback } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { Chess, Square } from 'chess.js'
import { api, PuzzleResponse, PuzzleSolveResponse } from '../api'
import ChessBoard from '../components/ChessBoard'
import { useQuery } from '../hooks/useQuery'

export default function Puzzles() {
  const [params] = useSearchParams()
  const username = params.get('username') || ''
  const { data: puzzles, loading, error } = useQuery(() => api.getPuzzles(username, 10), [username])

  const [currentIdx, setCurrentIdx] = useState(0)
  const [selectedFrom, setSelectedFrom] = useState<Square | null>(null)
  const [result, setResult] = useState<PuzzleSolveResponse | null>(null)
  const [checking, setChecking] = useState(false)

  const currentPuzzle: PuzzleResponse | undefined = puzzles?.[currentIdx]

  const handleSquareClick = useCallback(async (square: Square) => {
    if (!currentPuzzle || result) return

    if (!selectedFrom) {
      setSelectedFrom(square)
      return
    }

    // Try the move
    const uci = `${selectedFrom}${square}`
    setSelectedFrom(null)
    setChecking(true)

    try {
      const res = await api.solvePuzzle(currentPuzzle.puzzle_id, uci)
      setResult(res)
    } catch (e) {
      console.error(e)
    } finally {
      setChecking(false)
    }
  }, [currentPuzzle, result, selectedFrom])

  const handleNext = () => {
    setCurrentIdx((i) => i + 1)
    setResult(null)
    setSelectedFrom(null)
  }

  const highlightSquares: Record<string, { backgroundColor: string }> = {}
  if (selectedFrom) {
    highlightSquares[selectedFrom] = { backgroundColor: 'rgba(255, 255, 0, 0.4)' }
    // Highlight legal moves
    if (currentPuzzle) {
      try {
        const chess = new Chess(currentPuzzle.fen)
        chess.moves({ square: selectedFrom, verbose: true }).forEach((m) => {
          highlightSquares[m.to] = { backgroundColor: 'rgba(52, 211, 153, 0.3)' }
        })
      } catch {
        // ignore
      }
    }
  }

  // Show solution arrow after attempt
  const arrowSquares: Array<[string, string]> = []
  if (result && result.solution_uci && result.solution_uci.length >= 4) {
    arrowSquares.push([result.solution_uci.slice(0, 2), result.solution_uci.slice(2, 4)])
  }

  // Determine board orientation based on whose turn it is in puzzle FEN
  const boardOrientation: 'white' | 'black' = (() => {
    if (!currentPuzzle?.fen) return 'white'
    try {
      const chess = new Chess(currentPuzzle.fen)
      return chess.turn() === 'w' ? 'white' : 'black'
    } catch {
      return 'white'
    }
  })()

  return (
    <div className="min-h-screen">
      <nav className="border-b border-gray-800 px-6 py-4 flex items-center gap-4">
        <Link to={`/dashboard?username=${encodeURIComponent(username)}`}
          className="text-gray-400 hover:text-gray-100 text-sm">← Dashboard</Link>
        <h1 className="text-lg font-semibold text-gray-100">Puzzles</h1>
        <span className="text-emerald-400 text-sm ml-auto">{username}</span>
      </nav>

      <main className="max-w-2xl mx-auto px-6 py-8">
        <p className="text-gray-400 text-sm mb-6">
          These positions come from your own games — moments where you blundered but a better move existed.
          Find the best move!
        </p>

        {loading && <div className="text-gray-500 animate-pulse">Loading puzzles…</div>}
        {error && <div className="text-red-400 text-sm">{error}</div>}

        {puzzles && puzzles.length === 0 && (
          <div className="card text-center py-10 text-gray-500">
            No puzzles available yet. Import more games with engine evaluations to generate puzzles.
          </div>
        )}

        {currentPuzzle && (
          <div className="space-y-5">
            <div className="flex items-center justify-between">
              <span className="text-gray-400 text-sm">
                Puzzle {currentIdx + 1} of {puzzles?.length ?? 0}
              </span>
              <Link
                to={`/games/${currentPuzzle.game_id}?username=${encodeURIComponent(username)}`}
                className="text-emerald-400 text-sm hover:text-emerald-300"
              >
                View full game →
              </Link>
            </div>

            <div className="card text-sm text-gray-400">
              {boardOrientation === 'white' ? '⬜ White' : '⬛ Black'} to move.
              {currentPuzzle.eval_before != null && (
                <span className="ml-2">Position eval before: {currentPuzzle.eval_before > 0 ? '+' : ''}{currentPuzzle.eval_before.toFixed(2)}</span>
              )}
            </div>

            <div className="flex justify-center">
              <ChessBoard
                fen={currentPuzzle.fen}
                orientation={boardOrientation}
                onSquareClick={checking ? undefined : handleSquareClick}
                highlightSquares={highlightSquares}
                arrowSquares={arrowSquares}
                width={440}
              />
            </div>

            {checking && (
              <div className="text-center text-gray-400 text-sm animate-pulse">Checking…</div>
            )}

            {result && (
              <div className={`card border-2 ${result.correct ? 'border-emerald-600 bg-emerald-900/20' : 'border-red-700 bg-red-900/20'}`}>
                <div className="text-lg font-bold mb-2">
                  {result.correct ? '✅ Correct!' : '❌ Incorrect'}
                </div>
                <p className="text-gray-300 text-sm">{result.explanation}</p>

                {currentIdx < (puzzles?.length ?? 0) - 1 ? (
                  <button onClick={handleNext} className="btn-primary mt-4">
                    Next Puzzle →
                  </button>
                ) : (
                  <p className="text-gray-500 text-sm mt-4">You've completed all puzzles! Import more games for new ones.</p>
                )}
              </div>
            )}

            {!result && (
              <p className="text-center text-gray-600 text-xs">
                Click a piece to select, then click a destination square.
              </p>
            )}
          </div>
        )}
      </main>
    </div>
  )
}
