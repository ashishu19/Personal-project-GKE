import { useState, useEffect } from 'react'
import { api } from '../api'

function useQuery<T>(fetcher: () => Promise<T>, deps: unknown[]) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    fetcher()
      .then((d) => { if (!cancelled) setData(d) })
      .catch((e) => { if (!cancelled) setError(e instanceof Error ? e.message : 'Failed') })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  return { data, loading, error }
}

export function useOverview(username: string) {
  return useQuery(() => api.getOverview(username), [username])
}

export function usePatterns(username: string) {
  return useQuery(() => api.getPatterns(username), [username])
}

export function useOpenings(username: string) {
  return useQuery(() => api.getOpenings(username), [username])
}

export function useStyle(username: string) {
  return useQuery(() => api.getStyle(username), [username])
}
