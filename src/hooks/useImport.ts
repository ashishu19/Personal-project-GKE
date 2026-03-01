import { useState, useCallback, useRef } from 'react'
import { api, ImportStatusResponse } from '../api'

interface UseImportReturn {
  jobId: string | null
  status: ImportStatusResponse | null
  isImporting: boolean
  error: string | null
  startImport: (username: string, max?: number) => Promise<string>
  stopPolling: () => void
}

export function useImport(): UseImportReturn {
  const [jobId, setJobId] = useState<string | null>(null)
  const [status, setStatus] = useState<ImportStatusResponse | null>(null)
  const [isImporting, setIsImporting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }, [])

  const startImport = useCallback(async (username: string, max = 100): Promise<string> => {
    setError(null)
    setIsImporting(true)

    try {
      const response = await api.startImport(username, max)
      setJobId(response.job_id)

      // Start polling
      const poll = async () => {
        try {
          const s = await api.getImportStatus(response.job_id)
          setStatus(s)
          if (s.status === 'done' || s.status === 'error') {
            stopPolling()
            setIsImporting(false)
            if (s.status === 'error') {
              setError(s.error_message || 'Import failed')
            }
          }
        } catch (e) {
          stopPolling()
          setIsImporting(false)
          setError(e instanceof Error ? e.message : 'Polling failed')
        }
      }

      await poll()
      intervalRef.current = setInterval(poll, 2000)

      return response.job_id
    } catch (e) {
      setIsImporting(false)
      const msg = e instanceof Error ? e.message : 'Import failed'
      setError(msg)
      throw new Error(msg)
    }
  }, [stopPolling])

  return { jobId, status, isImporting, error, startImport, stopPolling }
}
