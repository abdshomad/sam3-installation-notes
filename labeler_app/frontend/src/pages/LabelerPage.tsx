import { useEffect, useMemo } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useParams, useSearchParams } from 'react-router-dom'
import classNames from 'classnames'
import {
  createAnnotation,
  fetchAnnotations,
  fetchDataset,
  fetchImages,
  fetchLabelClasses,
} from '../api/projects'
import { useWorkspaceStore } from '../store/useWorkspaceStore'
import { AnnotationCanvas } from '../components/AnnotationCanvas'

export const LabelerPage = () => {
  const { datasetId } = useParams<{ datasetId: string }>()
  const numericId = Number(datasetId)
  const queryClient = useQueryClient()
  const [searchParams, setSearchParams] = useSearchParams()
  const selectedImageId = Number(searchParams.get('imageId') || 0)

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

  const projectId = datasetQuery.data?.project_id

  const classesQuery = useQuery({
    queryKey: ['labelClasses', projectId],
    queryFn: () => fetchLabelClasses(projectId as number),
    enabled: Boolean(projectId),
  })

  const activeImageId = useMemo(() => {
    if (selectedImageId) return selectedImageId
    if (imagesQuery.data?.length) return imagesQuery.data[0].id
    return undefined
  }, [imagesQuery.data, selectedImageId])

  useEffect(() => {
    if (!selectedImageId && imagesQuery.data?.length) {
      setSearchParams({ imageId: String(imagesQuery.data[0].id) }, { replace: true })
    }
  }, [imagesQuery.data, selectedImageId, setSearchParams])

  const annotationsQuery = useQuery({
    queryKey: ['annotations', activeImageId],
    queryFn: () => fetchAnnotations(activeImageId as number),
    enabled: Boolean(activeImageId),
  })

  const { selectedClassId, setSelectedClassId } = useWorkspaceStore()

  useEffect(() => {
    if (!selectedClassId && classesQuery.data?.length) {
      setSelectedClassId(classesQuery.data[0].id)
    }
  }, [classesQuery.data, selectedClassId, setSelectedClassId])

  const selectedClass = classesQuery.data?.find((labelClass) => labelClass.id === selectedClassId)
  const activeImage = imagesQuery.data?.find((img) => img.id === activeImageId)

  const createAnnotationMutation = useMutation({
    mutationFn: (geometry: Record<string, unknown>) =>
      createAnnotation({
        image_id: activeImageId as number,
        label_class_id: selectedClassId as number,
        annotation_type: 'bbox',
        geometry,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['annotations', activeImageId] })
    },
  })

  const handleCreateAnnotation = async (geometry: Record<string, unknown>) => {
    if (!selectedClassId || !activeImageId) return
    await createAnnotationMutation.mutateAsync(geometry)
  }

  const goToImage = (imageId: number) => {
    setSearchParams({ imageId: String(imageId) }, { replace: true })
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[260px,1fr,200px]">
      <aside className="space-y-4 rounded-xl border border-slate-800 bg-slate-900/40 p-4">
        <div>
          <p className="text-xs uppercase tracking-wide text-slate-500">Label classes</p>
          <div className="mt-3 space-y-2">
            {classesQuery.data?.map((labelClass) => (
              <button
                key={labelClass.id}
                type="button"
                className={classNames(
                  'flex w-full items-center justify-between rounded-lg border px-3 py-2 text-sm',
                  selectedClassId === labelClass.id ? 'border-sky-500 bg-slate-800 text-white' : 'border-slate-700 text-slate-300',
                )}
                onClick={() => setSelectedClassId(labelClass.id)}
              >
                <span>{labelClass.name}</span>
                <span className="h-3 w-3 rounded-sm" style={{ backgroundColor: labelClass.color }} />
              </button>
            ))}
            {!classesQuery.data?.length && <p className="text-xs text-slate-500">Create classes in the project page.</p>}
          </div>
        </div>

        <div>
          <p className="text-xs uppercase tracking-wide text-slate-500">Images</p>
          <div className="mt-2 max-h-[60vh] space-y-2 overflow-y-auto pr-2">
            {imagesQuery.data?.map((image) => (
              <button
                type="button"
                key={image.id}
                className={classNames(
                  'w-full rounded-lg border px-3 py-2 text-left text-sm',
                  activeImageId === image.id ? 'border-sky-500 bg-slate-800 text-white' : 'border-slate-800 text-slate-300',
                )}
                onClick={() => goToImage(image.id)}
              >
                {image.original_filename}
              </button>
            ))}
          </div>
        </div>
      </aside>

      <div className="space-y-4">
        <div className="flex items-center justify-between text-sm text-slate-400">
          <div>
            <p>{datasetQuery.data?.name}</p>
            <p className="text-xs text-slate-500">Selected class: {selectedClass?.name || 'None'}</p>
          </div>
          <div className="space-x-2">
            <button
              className="rounded-lg border border-slate-600 px-3 py-1 text-xs text-white disabled:opacity-30"
              disabled={!imagesQuery.data || !activeImageId}
              onClick={() => {
                if (!imagesQuery.data || !activeImageId) return
                const currentIndex = imagesQuery.data.findIndex((img) => img.id === activeImageId)
                if (currentIndex > 0) {
                  goToImage(imagesQuery.data[currentIndex - 1].id)
                }
              }}
            >
              Previous
            </button>
            <button
              className="rounded-lg border border-slate-600 px-3 py-1 text-xs text-white disabled:opacity-30"
              disabled={!imagesQuery.data || !activeImageId}
              onClick={() => {
                if (!imagesQuery.data || !activeImageId) return
                const currentIndex = imagesQuery.data.findIndex((img) => img.id === activeImageId)
                if (currentIndex < imagesQuery.data.length - 1) {
                  goToImage(imagesQuery.data[currentIndex + 1].id)
                }
              }}
            >
              Next
            </button>
          </div>
        </div>

        <AnnotationCanvas
          image={activeImage}
          annotations={annotationsQuery.data}
          selectedClass={selectedClass}
          classes={classesQuery.data}
          onCreate={handleCreateAnnotation}
        />
      </div>

      <aside className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
        <p className="text-xs uppercase tracking-wide text-slate-500">Annotations</p>
        <div className="mt-2 space-y-2 text-sm text-slate-300">
          {annotationsQuery.data?.map((annotation) => {
            const label = classesQuery.data?.find((cls) => cls.id === annotation.label_class_id)
            const bbox = annotation.geometry?.bbox
            return (
              <div key={annotation.id} className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">
                <p className="font-medium">{label?.name || 'Class'}</p>
                {bbox && <p className="text-xs text-slate-500">bbox: {bbox.map((v: number) => Math.round(v)).join(', ')}</p>}
              </div>
            )
          })}
          {!annotationsQuery.data?.length && <p className="text-xs text-slate-500">No annotations yet.</p>}
        </div>
      </aside>
    </div>
  )
}

