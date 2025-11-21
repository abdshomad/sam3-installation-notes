import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { fetchDataset, fetchImages, uploadImages } from '../api/projects'
import { buildImageUrl } from '../utils/images'

export const DatasetPage = () => {
  const { datasetId } = useParams<{ datasetId: string }>()
  const numericId = Number(datasetId)
  const queryClient = useQueryClient()

  const datasetQuery = useQuery({
    queryKey: ['dataset', numericId],
    queryFn: () => fetchDataset(numericId),
    enabled: Boolean(numericId),
  })

  const imagesQuery = useQuery({
    queryKey: ['images', numericId],
    queryFn: () => fetchImages(numericId),
    enabled: Boolean(numericId),
  })

  const uploadMutation = useMutation({
    mutationFn: (files: FileList) => uploadImages(numericId, files),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['images', numericId] })
    },
  })

  const handleUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (files && files.length) {
      uploadMutation.mutate(files)
      event.target.value = ''
    }
  }

  if (datasetQuery.isLoading) {
    return <p className="text-slate-400">Loading dataset…</p>
  }

  if (!datasetQuery.data) {
    return <p className="text-rose-400">Dataset not found.</p>
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-wide text-slate-500">{datasetQuery.data.slug}</p>
          <h1 className="text-2xl font-semibold text-white">{datasetQuery.data.name}</h1>
          <p className="text-sm text-slate-400">{datasetQuery.data.description}</p>
        </div>
        <Link
          to={`/datasets/${datasetQuery.data.id}/label`}
          className="rounded-lg bg-sky-500 px-4 py-2 text-sm font-medium text-white"
        >
          Open labeler
        </Link>
      </div>

      <div className="rounded-xl border border-dashed border-slate-700 bg-slate-900/50 p-6 text-center">
        <p className="text-sm text-slate-400">Drag images here or click to upload</p>
        <label className="mt-4 inline-flex cursor-pointer items-center rounded-lg bg-slate-800 px-4 py-2 text-sm text-white">
          <input type="file" accept="image/*" multiple className="hidden" onChange={handleUpload} />
          Choose files
        </label>
      </div>

  <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3">
        {imagesQuery.data?.map((image) => (
          <div key={image.id} className="rounded-xl border border-slate-800 bg-slate-900/50 p-3">
            <img
              src={buildImageUrl(image.id)}
              alt={image.original_filename}
              className="h-40 w-full rounded-lg object-cover"
            />
            <p className="mt-2 truncate text-sm text-slate-300">{image.original_filename}</p>
            <div className="mt-2 flex items-center justify-between text-xs text-slate-500">
              <span>
                {image.width}×{image.height}
              </span>
              <Link to={`/datasets/${image.dataset_id}/label?imageId=${image.id}`} className="text-sky-400">
                Label
              </Link>
            </div>
          </div>
        ))}
        {!imagesQuery.data?.length && <p className="text-slate-400">No images uploaded yet.</p>}
      </div>
    </div>
  )
}

