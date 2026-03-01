/**
 * Typed API wrappers for all backend endpoints.
 */

const BASE = '/api'

// ─── Types ───────────────────────────────────────────────────────────────────

export interface ImportStartResponse {
  job_id: string
  username: string
  message: string
}

export interface ImportStatusResponse {
  job_id: string
  username: string
  status: 'pending' | 'running' | 'done' | 'error'
  total_games: number
  processed_games: number
  progress_pct: number
  error_message?: string
}

export interface EloPoint {
  date: string
  elo: number
}

export interface OverviewResponse {
  username: string
  total_games: number
  wins: number
  losses: number
  draws: number
  win_rate: number
  avg_cpl?: number
  elo_trend: EloPoint[]
  current_elo?: number
}

export interface PatternStat {
  feature: string
  label: string
  win_rate_with: number
  win_rate_without: number
  delta: number
  sample_size_with: number
  sample_size_without: number
  is_significant: boolean
  elo_relevant: boolean
}

export interface PatternsResponse {
  username: string
  patterns: PatternStat[]
}

export interface OpeningStat {
  eco: string
  name: string
  games: number
  wins: number
  losses: number
  draws: number
  win_rate: number
}

export interface OpeningsResponse {
  username: string
  openings: OpeningStat[]
}

export interface StyleVector {
  piece_exchange_preference: number
  queen_activity: number
  pawn_advance_rate: number
  tactical_complexity: number
  endgame_entry_rate: number
}

export interface StyleMatchResponse {
  username: string
  matched_gm: string
  gm_title: string
  archetype: string
  similarity_score: number
  description: string
  study_tip: string
  user_style_vector: StyleVector
}

export interface GameSummary {
  game_id: string
  user_color: string
  result: string
  user_elo?: number
  opponent_elo?: number
  time_control?: string
  opening_eco?: string
  opening_name?: string
  played_at?: string
  avg_cpl?: number
  blunders: number
  has_evals: boolean
}

export interface GamesListResponse {
  username: string
  total: number
  page: number
  page_size: number
  games: GameSummary[]
}

export interface PositionDetail {
  move_number: number
  fen: string
  eval_score?: number
  best_move?: string
  played_move?: string
  cpl?: number
  is_blunder: boolean
  is_puzzle_candidate: boolean
  clock_seconds?: number
}

export interface GameDetailResponse {
  game_id: string
  username: string
  user_color: string
  result: string
  user_elo?: number
  opponent_elo?: number
  time_control?: string
  opening_eco?: string
  opening_name?: string
  played_at?: string
  raw_pgn?: string
  avg_cpl?: number
  blunders: number
  mistakes: number
  inaccuracies: number
  has_evals: boolean
  positions: PositionDetail[]
}

export interface PuzzleResponse {
  puzzle_id: number
  game_id: string
  move_number: number
  fen: string
  eval_before?: number
  solved: boolean
}

export interface PuzzleSolveResponse {
  correct: boolean
  solution_uci?: string
  solution_san?: string
  explanation: string
}

// ─── API functions ────────────────────────────────────────────────────────────

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, options)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  startImport: (username: string, max = 100): Promise<ImportStartResponse> =>
    apiFetch(`/import/${encodeURIComponent(username)}?max=${max}`, { method: 'POST' }),

  getImportStatus: (jobId: string): Promise<ImportStatusResponse> =>
    apiFetch(`/import/status/${jobId}`),

  getOverview: (username: string): Promise<OverviewResponse> =>
    apiFetch(`/stats/overview?username=${encodeURIComponent(username)}`),

  getPatterns: (username: string): Promise<PatternsResponse> =>
    apiFetch(`/stats/patterns?username=${encodeURIComponent(username)}`),

  getOpenings: (username: string): Promise<OpeningsResponse> =>
    apiFetch(`/stats/openings?username=${encodeURIComponent(username)}`),

  getStyle: (username: string): Promise<StyleMatchResponse> =>
    apiFetch(`/stats/style?username=${encodeURIComponent(username)}`),

  getGames: (
    username: string,
    page = 1,
    pageSize = 20,
    result?: string,
    opening?: string,
  ): Promise<GamesListResponse> => {
    const params = new URLSearchParams({ username, page: String(page), page_size: String(pageSize) })
    if (result) params.set('result', result)
    if (opening) params.set('opening', opening)
    return apiFetch(`/games?${params}`)
  },

  getGame: (gameId: string): Promise<GameDetailResponse> =>
    apiFetch(`/games/${gameId}`),

  getPuzzles: (username: string, limit = 10): Promise<PuzzleResponse[]> =>
    apiFetch(`/puzzles/${encodeURIComponent(username)}?limit=${limit}`),

  solvePuzzle: (puzzleId: number, moveUci: string): Promise<PuzzleSolveResponse> =>
    apiFetch(`/puzzles/${puzzleId}/solve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ move_uci: moveUci }),
    }),

  /** Returns a ReadableStream for streaming suggestions text. */
  getSuggestionsStream: (username: string): Promise<Response> =>
    fetch(`${BASE}/suggestions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username }),
    }),
}
