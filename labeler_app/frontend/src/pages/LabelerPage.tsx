import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useParams, useSearchParams } from 'react-router-dom'
import classNames from 'classnames'
import {
  createAnnotation,
  fetchAnnotations,
  fetchDataset,
  fetchImages,
  fetchLabelClasses,
  fetchProject,
} from '../api/projects'
import { useWorkspaceStore } from '../store/useWorkspaceStore'
import { AnnotationCanvas } from '../components/AnnotationCanvas'
import { ConceptCommandBar } from '../components/ConceptCommandBar'
import { ConfidenceBadge } from '../components/ConfidenceIndicator'
import { CropTool } from '../components/CropTool'
import { BatchLabelingDialog } from '../components/BatchLabelingDialog'
import { promptImageWithExemplar } from '../api/concepts'

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

  const projectQuery = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => fetchProject(projectId as number),
    enabled: Boolean(projectId),
  })

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
  const [cropMode, setCropMode] = useState(false)
  const [imageMetrics, setImageMetrics] = useState<{
    naturalWidth: number
    naturalHeight: number
    displayWidth: number
    displayHeight: number
  } | null>(null)
  const [batchDialogOpen, setBatchDialogOpen] = useState(false)

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

  const handleCropComplete = async (crop: { x: number; y: number; w: number; h: number }) => {
    if (!projectId || !activeImageId) return

    setCropMode(false)
    try {
      await promptImageWithExemplar(projectId, activeImageId, {
        crop,
        type: 'positive',
        create_annotations: true,
      })
      queryClient.invalidateQueries({ queryKey: ['annotations', activeImageId] })
      queryClient.invalidateQueries({ queryKey: ['labelClasses', projectId] })
    } catch (error) {
      console.error('Exemplar prompt error:', error)
      // TODO: Show error toast
    }
  }

  const handleImageMetricsUpdate = (metrics: {
    naturalWidth: number
    naturalHeight: number
    displayWidth: number
    displayHeight: number
  }) => {
    setImageMetrics(metrics)
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
        <div className="space-y-3">
          {projectId && (
            <ConceptCommandBar
              projectId={projectId}
              imageId={activeImageId}
              confidenceThreshold={projectQuery.data?.confidence_threshold ?? 0.7}
              onSuccess={() => {
                queryClient.invalidateQueries({ queryKey: ['annotations', activeImageId] })
                queryClient.invalidateQueries({ queryKey: ['labelClasses', projectId] })
              }}
              onError={(error) => {
                console.error('Concept prompt error:', error)
                // TODO: Show error toast
              }}
            />
          )}
          <div className="flex items-center justify-between text-sm text-slate-400">
            <div>
              <p>{datasetQuery.data?.name}</p>
              <p className="text-xs text-slate-500">Selected class: {selectedClass?.name || 'None'}</p>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setBatchDialogOpen(true)}
                className="rounded-lg border border-sky-600 bg-sky-600/20 px-3 py-1 text-xs font-medium text-sky-400 hover:bg-sky-600/30"
                title="Batch auto-label entire dataset"
              >
                Batch Label
              </button>
              <button
                type="button"
                onClick={() => {
                  setCropMode(!cropMode)
                }}
                className={`rounded-lg border px-3 py-1 text-xs font-medium transition-colors ${cropMode
                  ? 'border-emerald-600 bg-emerald-600/20 text-emerald-400 hover:bg-emerald-600/30'
                  : 'border-slate-600 bg-slate-900/60 text-slate-300 hover:bg-slate-800'
                  }`}
                title="Crop exemplar for visual search"
              >
                {cropMode ? 'Cancel Crop' : 'Crop Exemplar'}
              </button>
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
          </div>
        </div>

        <div className="relative">
          <AnnotationCanvas
            image={activeImage}
            annotations={annotationsQuery.data}
            selectedClass={cropMode ? undefined : selectedClass}
            classes={classesQuery.data}
            onCreate={handleCreateAnnotation}
            onMetricsUpdate={handleImageMetricsUpdate}
            cropMode={cropMode}
            onCropCancel={() => setCropMode(false)}
          />
          {cropMode && imageMetrics && (
            <CropTool
              enabled={cropMode}
              imageWidth={imageMetrics.naturalWidth}
              imageHeight={imageMetrics.naturalHeight}
              displayWidth={imageMetrics.displayWidth}
              displayHeight={imageMetrics.displayHeight}
              onCrop={handleCropComplete}
              onCancel={() => setCropMode(false)}
            />
          )}
        </div>
      </div>

      <aside className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
        <p className="text-xs uppercase tracking-wide text-slate-500">Annotations</p>
        <div className="mt-2 space-y-2 text-sm text-slate-300">
          {annotationsQuery.data?.map((annotation) => {
            const label = classesQuery.data?.find((cls) => cls.id === annotation.label_class_id)
            const bbox = annotation.geometry?.bbox
            const conceptText = annotation.concept_text
            const isAIGenerated = annotation.is_ai_generated
            return (
              <div
                key={annotation.id}
                className={`rounded-lg border p-3 ${annotation.presence_score != null && annotation.presence_score < 0.7
                  ? 'border-yellow-500/50 bg-yellow-900/20'
                  : 'border-slate-800 bg-slate-900/60'
                  }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <p className="font-medium">{label?.name || 'Class'}</p>
                      {isAIGenerated && (
                        <span className="text-xs text-sky-400" title="AI Generated">
                          AI
                        </span>
                      )}
                    </div>
                    {conceptText && (
                      <p className="mt-1 text-xs text-slate-400 italic">&quot;{conceptText}&quot;</p>
                    )}
                    {bbox && (
                      <p className="mt-1 text-xs text-slate-500">bbox: {bbox.map((v: number) => Math.round(v)).join(', ')}</p>
                    )}
                  </div>
                  {annotation.presence_score !== null && (
                    <ConfidenceBadge score={annotation.presence_score ?? null} />
                  )}
                </div>
              </div>
            )
          })}
          {!annotationsQuery.data?.length && <p className="text-xs text-slate-500">No annotations yet.</p>}
        </div>
        {projectId && datasetQuery.data && (
          <BatchLabelingDialog
            projectId={projectId}
            datasetId={numericId}
            isOpen={batchDialogOpen}
            onClose={() => setBatchDialogOpen(false)}
            defaultThreshold={projectQuery.data?.confidence_threshold ?? 0.7}
          />
        )}
      </aside>
    </div>
  )
}
