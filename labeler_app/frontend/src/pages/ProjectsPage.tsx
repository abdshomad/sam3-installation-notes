import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { createProject, fetchProjects } from '../api/projects'

export const ProjectsPage = () => {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const queryClient = useQueryClient()

  const { data: projects, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: fetchProjects,
  })

  const createMutation = useMutation({
    mutationFn: () => createProject({ name, description }),
    onSuccess: () => {
      setName('')
      setDescription('')
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    if (!name.trim()) return
    createMutation.mutate()
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-white">Projects</h1>
        <p className="text-sm text-slate-400">Create datasets and manage label schemas.</p>
      </div>

      <form onSubmit={handleSubmit} className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
        <h2 className="text-lg font-medium text-white">New project</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <input
            className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-sky-500"
            placeholder="Project name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <input
            className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-sky-500"
            placeholder="Description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>
        <button
          className="mt-4 rounded-lg bg-sky-500 px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
          disabled={createMutation.isPending}
        >
          Create project
        </button>
      </form>

      <div className="grid gap-4 md:grid-cols-2">
        {isLoading && <p className="text-slate-400">Loading projects…</p>}
        {projects?.map((project) => (
          <Link
            to={`/projects/${project.id}`}
            key={project.id}
            className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 transition hover:border-sky-500"
          >
            <p className="text-sm uppercase tracking-wide text-slate-500">{project.slug}</p>
            <h3 className="text-xl font-semibold text-white">{project.name}</h3>
            <p className="text-sm text-slate-400">{project.description}</p>
          </Link>
        ))}
      </div>
    </div>
  )
}

