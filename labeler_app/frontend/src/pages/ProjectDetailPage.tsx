import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import {
  createDataset,
  createLabelClass,
  fetchDatasets,
  fetchLabelClasses,
  fetchProject,
} from '../api/projects'

const DEFAULT_COLORS = ['#ec4899', '#a855f7', '#3b82f6', '#22d3ee', '#10b981', '#f59e0b', '#ef4444']

export const ProjectDetailPage = () => {
  const { projectId } = useParams<{ projectId: string }>()
  const projectNumericId = Number(projectId)
  const queryClient = useQueryClient()

  const [datasetName, setDatasetName] = useState('')
  const [datasetDesc, setDatasetDesc] = useState('')
  const [className, setClassName] = useState('')
  const [classColor, setClassColor] = useState(DEFAULT_COLORS[0])
  const [hotkey, setHotkey] = useState('')

  const projectQuery = useQuery({
    queryKey: ['project', projectNumericId],
    queryFn: () => fetchProject(projectNumericId),
    enabled: Boolean(projectNumericId),
  })

  const classesQuery = useQuery({
    queryKey: ['labelClasses', projectNumericId],
    queryFn: () => fetchLabelClasses(projectNumericId),
    enabled: Boolean(projectNumericId),
  })

  const datasetQuery = useQuery({
    queryKey: ['datasets', projectNumericId],
    queryFn: () => fetchDatasets(projectNumericId),
    enabled: Boolean(projectNumericId),
  })

  const datasetMutation = useMutation({
    mutationFn: () => createDataset(projectNumericId, { name: datasetName, description: datasetDesc }),
    onSuccess: () => {
      setDatasetName('')
      setDatasetDesc('')
      queryClient.invalidateQueries({ queryKey: ['datasets', projectNumericId] })
    },
  })

  const classMutation = useMutation({
    mutationFn: () => createLabelClass(projectNumericId, { name: className, color: classColor, hotkey }),
    onSuccess: () => {
      setClassName('')
      setHotkey('')
      queryClient.invalidateQueries({ queryKey: ['labelClasses', projectNumericId] })
    },
  })

  const handleDatasetSubmit = (event: FormEvent) => {
    event.preventDefault()
    if (!datasetName.trim()) return
    datasetMutation.mutate()
  }

  const handleClassSubmit = (event: FormEvent) => {
    event.preventDefault()
    if (!className.trim()) return
    classMutation.mutate()
  }

  if (projectQuery.isLoading) {
    return <p className="text-slate-400">Loading project…</p>
  }

  if (!projectQuery.data) {
    return <p className="text-rose-400">Project not found.</p>
  }

  return (
    <div className="space-y-8">
      <div>
        <p className="text-sm uppercase tracking-wide text-slate-500">{projectQuery.data.slug}</p>
        <h1 className="text-2xl font-semibold text-white">{projectQuery.data.name}</h1>
        <p className="text-sm text-slate-400">{projectQuery.data.description}</p>
      </div>

      <section className="grid gap-6 md:grid-cols-2">
        <form onSubmit={handleDatasetSubmit} className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
          <h2 className="text-lg font-medium text-white">New dataset</h2>
          <div className="mt-4 space-y-3">
            <input
              className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-sky-500"
              placeholder="Dataset name"
              value={datasetName}
              onChange={(e) => setDatasetName(e.target.value)}
            />
            <textarea
              className="h-20 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-sky-500"
              placeholder="Description"
              value={datasetDesc}
              onChange={(e) => setDatasetDesc(e.target.value)}
            />
          </div>
          <button className="mt-4 rounded-lg bg-sky-500 px-4 py-2 text-sm font-medium text-white">Create dataset</button>
        </form>

        <form onSubmit={handleClassSubmit} className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
          <h2 className="text-lg font-medium text-white">Label class</h2>
          <div className="mt-4 space-y-3">
            <input
              className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-sky-500"
              placeholder="Class name"
              value={className}
              onChange={(e) => setClassName(e.target.value)}
            />
            <div className="flex gap-2">
              {DEFAULT_COLORS.map((color) => (
                <button
                  key={color}
                  type="button"
                  style={{ backgroundColor: color }}
                  className={`h-9 flex-1 rounded-lg border ${classColor === color ? 'border-white' : 'border-transparent'}`}
                  onClick={() => setClassColor(color)}
                />
              ))}
            </div>
            <input
              className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-sky-500"
              placeholder="Hotkey (optional)"
              value={hotkey}
              onChange={(e) => setHotkey(e.target.value)}
            />
          </div>
          <button className="mt-4 rounded-lg bg-emerald-500 px-4 py-2 text-sm font-medium text-white">
            Save label class
          </button>
        </form>
      </section>

      <section>
        <h2 className="text-lg font-semibold text-white">Label schema</h2>
        <div className="mt-3 flex flex-wrap gap-3">
          {classesQuery.data?.map((labelClass) => (
            <div
              key={labelClass.id}
              className="flex items-center gap-3 rounded-lg border border-slate-800 bg-slate-900/50 px-4 py-2 text-sm text-white"
            >
              <span className="h-4 w-4 rounded-full" style={{ backgroundColor: labelClass.color }} />
              <span>{labelClass.name}</span>
              {labelClass.hotkey && <span className="rounded bg-slate-800 px-1.5 py-0.5 text-xs text-slate-400">{labelClass.hotkey}</span>}
            </div>
          ))}
          {!classesQuery.data?.length && <p className="text-sm text-slate-500">No classes defined yet.</p>}
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold text-white">Datasets</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          {datasetQuery.data?.map((dataset) => (
            <div key={dataset.id} className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
              <p className="text-sm uppercase tracking-wide text-slate-500">{dataset.slug}</p>
              <h3 className="text-xl font-semibold text-white">{dataset.name}</h3>
              <p className="text-sm text-slate-400">{dataset.description}</p>
              <div className="mt-4 flex gap-3">
                <Link
                  to={`/datasets/${dataset.id}`}
                  className="rounded-lg border border-slate-700 px-4 py-2 text-sm text-white hover:border-sky-500"
                >
                  Manage
                </Link>
                <Link
                  to={`/datasets/${dataset.id}/label`}
                  className="rounded-lg bg-sky-500 px-4 py-2 text-sm font-medium text-white"
                >
                  Open labeler
                </Link>
              </div>
            </div>
          ))}
          {!datasetQuery.data?.length && <p className="text-slate-400">No datasets yet.</p>}
        </div>
      </section>
    </div>
  )
}

