import { Chessboard } from 'react-chessboard'
import { Square } from 'chess.js'

interface Props {
  fen: string
  orientation?: 'white' | 'black'
  onSquareClick?: (square: Square) => void
  highlightSquares?: { [square: string]: { backgroundColor: string } }
  lastMove?: { from: string; to: string }
  arrowSquares?: Array<[string, string]>
  width?: number
}

export default function ChessBoard({
  fen,
  orientation = 'white',
  onSquareClick,
  highlightSquares = {},
  lastMove,
  arrowSquares = [],
  width,
}: Props) {
  const customSquareStyles: Record<string, React.CSSProperties> = { ...highlightSquares }
  if (lastMove) {
    customSquareStyles[lastMove.from] = { backgroundColor: 'rgba(255, 255, 0, 0.3)' }
    customSquareStyles[lastMove.to] = { backgroundColor: 'rgba(255, 255, 0, 0.4)' }
  }

  const customArrows: Array<[Square, Square, string?]> = arrowSquares.map(
    ([from, to]) => [from as Square, to as Square, 'rgba(52, 211, 153, 0.8)'],
  )

  return (
    <Chessboard
      position={fen}
      boardOrientation={orientation}
      onSquareClick={onSquareClick}
      customSquareStyles={customSquareStyles}
      customArrows={customArrows}
      boardWidth={width}
      customDarkSquareStyle={{ backgroundColor: '#b58863' }}
      customLightSquareStyle={{ backgroundColor: '#f0d9b5' }}
    />
  )
}
