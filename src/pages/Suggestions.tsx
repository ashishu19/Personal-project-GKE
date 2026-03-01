import { useState, useEffect, useRef } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { api } from '../api'

const STORAGE_KEY = (u: string) => `chess-suggestions-${u}`

export default function Suggestions() {
  const [params] = useSearchParams()
  const username = params.get('username') || ''
  const [text, setText] = useState(() => localStorage.getItem(STORAGE_KEY(username)) || '')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  const fetchSuggestions = async () => {
    if (!username) return
    setLoading(true)
    setError(null)
    setText('')

    try {
      const response = await api.getSuggestionsStream(username)
      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: response.statusText }))
        throw new Error(err.detail || `HTTP ${response.status}`)
      }

      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      let accumulated = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const chunk = decoder.decode(value, { stream: true })
        accumulated += chunk
        setText(accumulated)
      }

      localStorage.setItem(STORAGE_KEY(username), accumulated)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to get suggestions')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [text])

  // Simple markdown-ish rendering: bold **x**, headers ## x
  const renderText = (raw: string) => {
    return raw.split('\n').map((line, i) => {
      if (line.startsWith('## ')) {
        return <h2 key={i} className="text-lg font-bold text-emerald-400 mt-4 mb-2">{line.slice(3)}</h2>
      }
      if (line.startsWith('### ')) {
        return <h3 key={i} className="font-semibold text-gray-200 mt-3 mb-1">{line.slice(4)}</h3>
      }
      if (line.startsWith('- ') || line.startsWith('• ')) {
        return (
          <li key={i} className="ml-4 text-gray-300 text-sm list-disc">
            {renderInline(line.slice(2))}
          </li>
        )
      }
      if (line.trim() === '') return <br key={i} />
      return <p key={i} className="text-gray-300 text-sm leading-relaxed">{renderInline(line)}</p>
    })
  }

  const renderInline = (text: string) => {
    const parts = text.split(/(\*\*[^*]+\*\*)/g)
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} className="text-gray-100 font-semibold">{part.slice(2, -2)}</strong>
      }
      return part
    })
  }

  return (
    <div className="min-h-screen">
      <nav className="border-b border-gray-800 px-6 py-4 flex items-center gap-4">
        <Link to={`/dashboard?username=${encodeURIComponent(username)}`}
          className="text-gray-400 hover:text-gray-100 text-sm">← Dashboard</Link>
        <h1 className="text-lg font-semibold text-gray-100">AI Coach</h1>
        <span className="text-emerald-400 text-sm ml-auto">{username}</span>
      </nav>

      <main className="max-w-2xl mx-auto px-6 py-8">
        <p className="text-gray-400 text-sm mb-6">
          Personalised improvement advice based on your game patterns, powered by Claude AI.
        </p>

        {!text && !loading && (
          <div className="card text-center py-12">
            <div className="text-4xl mb-4">🤖</div>
            <p className="text-gray-400 mb-6">Ready to analyse your chess and give you a tailored improvement plan.</p>
            <button onClick={fetchSuggestions} className="btn-primary">
              Get My Improvement Plan
            </button>
          </div>
        )}

        {error && (
          <div className="bg-red-900/30 border border-red-700 rounded-lg p-4 text-red-300 text-sm mb-4">
            {error}
          </div>
        )}

        {(text || loading) && (
          <div className="card">
            <div ref={containerRef} className="space-y-1 max-h-[60vh] overflow-y-auto pr-2">
              {renderText(text)}
              {loading && (
                <span className="inline-block w-2 h-4 bg-emerald-400 animate-pulse ml-0.5" />
              )}
            </div>

            {!loading && text && (
              <div className="flex gap-3 mt-6 pt-4 border-t border-gray-800">
                <button onClick={fetchSuggestions} className="btn-secondary text-sm">
                  ↺ Regenerate
                </button>
                <button
                  onClick={() => { localStorage.removeItem(STORAGE_KEY(username)); setText('') }}
                  className="text-gray-500 hover:text-gray-400 text-sm transition-colors"
                >
                  Clear
                </button>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}
