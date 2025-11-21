import { useEffect, useMemo, useRef, useState } from 'react'
import type { Annotation, ImageAsset, LabelClass } from '../types'
import { buildImageUrl } from '../utils/images'
import { hasMask, getMaskData } from '../utils/maskDecoder'
import { MaskOverlay } from './MaskOverlay'

type Props = {
  image: ImageAsset | undefined
  annotations: Annotation[] | undefined
  selectedClass: LabelClass | undefined
  classes: LabelClass[] | undefined
  onCreate: (geometry: Record<string, unknown>) => Promise<void>
  onMetricsUpdate?: (metrics: ImageMetrics) => void
  cropMode?: boolean
  onCropCancel?: () => void
}

interface ImageMetrics {
  naturalWidth: number
  naturalHeight: number
  displayWidth: number
  displayHeight: number
}

export const AnnotationCanvas = ({
  image,
  annotations,
  selectedClass,
  classes,
  onCreate,
  onMetricsUpdate,
  cropMode = false,
  onCropCancel,
}: Props) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const startRef = useRef<{ x: number; y: number } | null>(null)
  const [draftBox, setDraftBox] = useState<{ x: number; y: number; w: number; h: number } | null>(null)
  const [metrics, setMetrics] = useState<ImageMetrics>({
    naturalWidth: image?.width || 1,
    naturalHeight: image?.height || 1,
    displayWidth: 1,
    displayHeight: 1,
  })

  useEffect(() => {
    setMetrics((prev) => ({
      ...prev,
      naturalWidth: image?.width || prev.naturalWidth,
      naturalHeight: image?.height || prev.naturalHeight,
    }))
  }, [image?.width, image?.height])

  const handleImageLoad = (event: React.SyntheticEvent<HTMLImageElement>) => {
    const { naturalWidth, naturalHeight } = event.currentTarget
    const rect = event.currentTarget.getBoundingClientRect()
    const newMetrics = {
      naturalWidth,
      naturalHeight,
      displayWidth: rect.width,
      displayHeight: rect.height,
    }
    setMetrics(newMetrics)
    onMetricsUpdate?.(newMetrics)
  }

  const handlePointerDown = (event: React.PointerEvent<HTMLDivElement>) => {
    if (cropMode || !selectedClass || !containerRef.current) return
    const bounds = containerRef.current.getBoundingClientRect()
    const x = event.clientX - bounds.left
    const y = event.clientY - bounds.top
    startRef.current = { x, y }
    setDraftBox({ x, y, w: 0, h: 0 })
  }

  const handlePointerMove = (event: React.PointerEvent<HTMLDivElement>) => {
    if (cropMode || !startRef.current || !containerRef.current) return
    const bounds = containerRef.current.getBoundingClientRect()
    const x = event.clientX - bounds.left
    const y = event.clientY - bounds.top
    setDraftBox({
      x: Math.min(startRef.current.x, x),
      y: Math.min(startRef.current.y, y),
      w: Math.abs(x - startRef.current.x),
      h: Math.abs(y - startRef.current.y),
    })
  }

  const handlePointerUp = async () => {
    if (cropMode || !startRef.current || !draftBox || !selectedClass) return
    startRef.current = null
    setDraftBox(null)

    if (draftBox.w < 4 || draftBox.h < 4) return
    const scaleX = metrics.naturalWidth / metrics.displayWidth
    const scaleY = metrics.naturalHeight / metrics.displayHeight

    const bbox = [
      Math.round(draftBox.x * scaleX),
      Math.round(draftBox.y * scaleY),
      Math.round(draftBox.w * scaleX),
      Math.round(draftBox.h * scaleY),
    ]
    await onCreate({ bbox, area: bbox[2] * bbox[3] })
  }

  const colorMap = useMemo(() => {
    const map = new Map<number, string>()
    classes?.forEach((labelClass) => map.set(labelClass.id, labelClass.color))
    return map
  }, [classes])

  const scaleX = metrics.displayWidth / metrics.naturalWidth
  const scaleY = metrics.displayHeight / metrics.naturalHeight

  const annotationRects = useMemo(() => {
    if (!annotations || !metrics.displayWidth) return []
    return annotations
      .map((annotation) => {
        const bbox = annotation.geometry?.bbox
        if (!bbox) return null
        const [x, y, w, h] = bbox
        return {
          id: annotation.id,
          style: {
            left: (x / metrics.naturalWidth) * metrics.displayWidth,
            top: (y / metrics.naturalHeight) * metrics.displayHeight,
            width: (w / metrics.naturalWidth) * metrics.displayWidth,
            height: (h / metrics.naturalHeight) * metrics.displayHeight,
          },
          labelClassId: annotation.label_class_id,
        }
      })
      .filter(Boolean) as Array<{ id: number; style: Record<string, number>; labelClassId: number }>
  }, [annotations, metrics])

  const annotationMasks = useMemo(() => {
    if (!annotations || !metrics.displayWidth || !image) return []
    return annotations
      .map((annotation) => {
        if (!hasMask(annotation)) return null
        const maskRLE = getMaskData(annotation)
        if (!maskRLE) return null

        return {
          id: annotation.id,
          maskRLE,
          color: colorMap.get(annotation.label_class_id) || '#f97316',
        }
      })
      .filter(Boolean) as Array<{ id: number; maskRLE: string; color: string }>
  }, [annotations, metrics, colorMap, image])

  if (!image) {
    return (
      <div className="flex h-full items-center justify-center rounded-xl border border-slate-800 bg-slate-900/40 text-slate-400">
        Select an image to start labeling
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      className="relative h-[70vh] w-full cursor-crosshair select-none overflow-hidden rounded-xl border border-slate-800 bg-slate-950"
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
    >
      <img
        src={buildImageUrl(image.id)}
        alt={image.original_filename}
        className="h-full w-full object-contain"
        onLoad={handleImageLoad}
      />
      <div className="pointer-events-none absolute inset-0">
        {/* Render masks as canvas overlays */}
        {annotationMasks.map((mask) => (
          <MaskOverlay
            key={mask.id}
            maskRLE={getMaskData(annotations?.find((a) => a.id === mask.id)!) || ''}
            width={metrics.naturalWidth}
            height={metrics.naturalHeight}
            displayWidth={metrics.displayWidth}
            displayHeight={metrics.displayHeight}
            color={mask.color}
          />
        ))}
        {/* Fallback to bounding boxes if no masks */}
        {annotationRects.map((rect) => (
          <div
            key={rect.id}
            className="absolute rounded border text-xs uppercase tracking-wide"
            style={{
              ...rect.style,
              borderColor: colorMap.get(rect.labelClassId) || '#f97316',
              backgroundColor: `${(colorMap.get(rect.labelClassId) || '#f97316')}33`,
            }}
          />
        ))}
        {draftBox && (
          <div
            className="absolute rounded border border-emerald-400 bg-emerald-400/20"
            style={{ left: draftBox.x, top: draftBox.y, width: draftBox.w, height: draftBox.h }}
          />
        )}
      </div>
      {!cropMode && !selectedClass && (
        <div className="pointer-events-none absolute bottom-4 left-1/2 w-max -translate-x-1/2 rounded-full bg-slate-900/80 px-4 py-1 text-xs text-slate-300">
          Select a label class to add annotations
        </div>
      )}
    </div>
  )
}

