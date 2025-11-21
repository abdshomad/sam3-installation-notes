import { useState } from 'react'
import { promptImageWithText } from '../api/concepts'

interface Props {
  projectId: number
  imageId: number | undefined
  confidenceThreshold: number
  onSuccess?: (result: { presenceToken: number | null; numInstances: number }) => void
  onError?: (error: Error) => void
}

export const ConceptCommandBar = ({ projectId, imageId, confidenceThreshold, onSuccess, onError }: Props) => {
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [lastResult, setLastResult] = useState<{ presenceToken: number | null; numInstances: number } | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!text.trim() || !imageId || loading) return

    setLoading(true)
    try {
      const result = await promptImageWithText(projectId, imageId, {
        text: text.trim(),
        threshold: confidenceThreshold,
        create_annotations: true,
      })

      setLastResult({
        presenceToken: result.presence_token,
        numInstances: result.num_instances,
      })

      onSuccess?.({
        presenceToken: result.presence_token,
        numInstances: result.num_instances,
      })
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to process concept prompt')
      onError?.(error)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="relative">
      <form onSubmit={handleSubmit} className="relative">
        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a concept to detect (e.g., 'player in red', 'solar panel')..."
          disabled={!imageId || loading}
          className="w-full rounded-lg border border-slate-700 bg-slate-900/60 px-4 py-2 pr-24 text-sm text-white placeholder:text-slate-500 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500 disabled:cursor-not-allowed disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!text.trim() || !imageId || loading}
          className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md border border-sky-600 bg-sky-600 px-3 py-1 text-xs font-medium text-white transition-colors hover:bg-sky-700 disabled:cursor-not-allowed disabled:opacity-30"
        >
          {loading ? 'Processing...' : 'Detect'}
        </button>
      </form>

      {lastResult && (
        <div className="mt-2 flex items-center gap-3 text-xs text-slate-400">
          <span>
            Found <span className="font-medium text-white">{lastResult.numInstances}</span> instances
          </span>
          {lastResult.presenceToken !== null && (
            <span className="flex items-center gap-1">
              Presence:
              <span
                className={`font-medium ${
                  lastResult.presenceToken >= 0.7
                    ? 'text-green-400'
                    : lastResult.presenceToken >= 0.5
                      ? 'text-yellow-400'
                      : 'text-red-400'
                }`}
              >
                {(lastResult.presenceToken * 100).toFixed(1)}%
              </span>
            </span>
          )}
        </div>
      )}
    </div>
  )
}

