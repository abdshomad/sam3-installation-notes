import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createBatchJob, getBatchJobStatus, type BatchLabelRequest } from '../api/batch'

interface Props {
  projectId: number
  datasetId: number
  isOpen: boolean
  onClose: () => void
  defaultThreshold?: number
}

export const BatchLabelingDialog = ({
  projectId,
  datasetId,
  isOpen,
  onClose,
  defaultThreshold = 0.7,
}: Props) => {
  const queryClient = useQueryClient()
  const [conceptText, setConceptText] = useState('')
  const [threshold, setThreshold] = useState(defaultThreshold)
  const [skipEmpty, setSkipEmpty] = useState(true)
  const [createAnnotations, setCreateAnnotations] = useState(true)
  const [jobId, setJobId] = useState<string | null>(null)

  const createJobMutation = useMutation({
    mutationFn: (request: BatchLabelRequest) => createBatchJob(projectId, datasetId, request),
    onSuccess: (data) => {
      setJobId(data.job_id)
      // Start polling for job status
      pollJobStatus(data.job_id)
      // Invalidate queries to refresh data after job completes
      queryClient.invalidateQueries({ queryKey: ['images', datasetId] })
      queryClient.invalidateQueries({ queryKey: ['annotations'] })
    },
    onError: (error) => {
      console.error('Batch job creation error:', error)
    },
  })

  const pollJobStatus = async (id: string) => {
    const poll = async () => {
      try {
        const status = await getBatchJobStatus(id)
        if (status.status === 'completed' || status.status === 'failed') {
          queryClient.invalidateQueries({ queryKey: ['images', datasetId] })
          queryClient.invalidateQueries({ queryKey: ['annotations'] })
          return
        }
        // Continue polling if still processing
        if (status.status === 'processing' || status.status === 'pending') {
          setTimeout(poll, 2000) // Poll every 2 seconds
        }
      } catch (error) {
        console.error('Error polling job status:', error)
      }
    }
    poll()
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!conceptText.trim()) return

    createJobMutation.mutate({
      concept_text: conceptText.trim(),
      threshold,
      skip_empty: skipEmpty,
      create_annotations: createAnnotations,
    })
  }

  const handleClose = () => {
    setJobId(null)
    setConceptText('')
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="w-full max-w-lg rounded-xl border border-slate-700 bg-slate-900 p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-white">Batch Auto-Labeling</h2>
          <button
            type="button"
            onClick={handleClose}
            className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-white"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {jobId ? (
          <div className="space-y-4">
            <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
              <p className="mb-2 text-sm font-medium text-white">Batch job created</p>
              <p className="text-xs text-slate-400">
                Job ID: <span className="font-mono text-slate-300">{jobId}</span>
              </p>
              <p className="mt-2 text-xs text-slate-400">
                Processing in background. Annotations will appear automatically when complete.
              </p>
            </div>
            <button
              type="button"
              onClick={handleClose}
              className="w-full rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-700"
            >
              Close
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="concept" className="mb-2 block text-sm font-medium text-slate-300">
                Concept Text
              </label>
              <input
                id="concept"
                type="text"
                value={conceptText}
                onChange={(e) => setConceptText(e.target.value)}
                placeholder="e.g., 'solar panel', 'player in red'"
                className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
                required
                autoFocus
              />
              <p className="mt-1 text-xs text-slate-500">
                This prompt will be applied to all images in the dataset
              </p>
            </div>

            <div>
              <label htmlFor="threshold" className="mb-2 block text-sm font-medium text-slate-300">
                Confidence Threshold: {threshold.toFixed(2)}
              </label>
              <input
                id="threshold"
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={threshold}
                onChange={(e) => setThreshold(parseFloat(e.target.value))}
                className="w-full"
              />
              <p className="mt-1 text-xs text-slate-500">
                Only annotations above this threshold will be created
              </p>
            </div>

            <div className="space-y-2">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={skipEmpty}
                  onChange={(e) => setSkipEmpty(e.target.checked)}
                  className="rounded border-slate-700 bg-slate-800 text-sky-600 focus:ring-sky-500"
                />
                <span className="text-sm text-slate-300">Skip empty images</span>
              </label>
              <p className="ml-6 text-xs text-slate-500">
                Skip images where the concept is not detected (faster processing)
              </p>
            </div>

            <div className="space-y-2">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={createAnnotations}
                  onChange={(e) => setCreateAnnotations(e.target.checked)}
                  className="rounded border-slate-700 bg-slate-800 text-sky-600 focus:ring-sky-500"
                />
                <span className="text-sm text-slate-300">Create annotations in database</span>
              </label>
              <p className="ml-6 text-xs text-slate-500">
                Automatically save detected annotations to the dataset
              </p>
            </div>

            <div className="flex gap-3">
              <button
                type="button"
                onClick={handleClose}
                className="flex-1 rounded-lg border border-slate-700 px-4 py-2 text-sm font-medium text-slate-300 hover:bg-slate-800"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={!conceptText.trim() || createJobMutation.isPending}
                className="flex-1 rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {createJobMutation.isPending ? 'Creating...' : 'Start Batch Job'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}

