import { useEffect, useRef, useState } from 'react'

interface CropRegion {
  x: number
  y: number
  w: number
  h: number
}

interface Props {
  enabled: boolean
  imageWidth: number
  imageHeight: number
  displayWidth: number
  displayHeight: number
  onCrop: (crop: CropRegion) => void
  onCancel: () => void
}

export const CropTool = ({ enabled, imageWidth, imageHeight, displayWidth, displayHeight, onCrop, onCancel }: Props) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const startRef = useRef<{ x: number; y: number } | null>(null)
  const [crop, setCrop] = useState<CropRegion | null>(null)
  const [isDrawing, setIsDrawing] = useState(false)

  // Scale factor to convert display coordinates to normalized [0, 1] coordinates
  const scaleX = imageWidth / displayWidth
  const scaleY = imageHeight / displayHeight

  useEffect(() => {
    if (!enabled) {
      setCrop(null)
      setIsDrawing(false)
      startRef.current = null
    }
  }, [enabled])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && enabled) {
        onCancel()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [enabled, onCancel])

  const handlePointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!enabled || !containerRef.current) return
    e.preventDefault()
    const bounds = containerRef.current.getBoundingClientRect()
    const x = e.clientX - bounds.left
    const y = e.clientY - bounds.top
    startRef.current = { x, y }
    setIsDrawing(true)
    setCrop({ x, y, w: 0, h: 0 })
  }

  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!enabled || !startRef.current || !isDrawing || !containerRef.current) return
    e.preventDefault()
    const bounds = containerRef.current.getBoundingClientRect()
    const x = e.clientX - bounds.left
    const y = e.clientY - bounds.top

    const minX = Math.min(startRef.current.x, x)
    const minY = Math.min(startRef.current.y, y)
    const maxX = Math.max(startRef.current.x, x)
    const maxY = Math.max(startRef.current.y, y)

    setCrop({
      x: Math.max(0, minX),
      y: Math.max(0, minY),
      w: Math.min(displayWidth, maxX) - Math.max(0, minX),
      h: Math.min(displayHeight, maxY) - Math.max(0, minY),
    })
  }

  const handlePointerUp = () => {
    if (!enabled || !crop || !isDrawing) return
    setIsDrawing(false)

    // Convert display coordinates to normalized [0, 1] coordinates
    const normalizedCrop: CropRegion = {
      x: (crop.x / displayWidth) * scaleX,
      y: (crop.y / displayHeight) * scaleY,
      w: (crop.w / displayWidth) * scaleX,
      h: (crop.h / displayHeight) * scaleY,
    }

    // Normalize to [0, 1] range
    normalizedCrop.x = normalizedCrop.x / imageWidth
    normalizedCrop.y = normalizedCrop.y / imageHeight
    normalizedCrop.w = normalizedCrop.w / imageWidth
    normalizedCrop.h = normalizedCrop.h / imageHeight

    // Ensure values are within [0, 1]
    normalizedCrop.x = Math.max(0, Math.min(1, normalizedCrop.x))
    normalizedCrop.y = Math.max(0, Math.min(1, normalizedCrop.y))
    normalizedCrop.w = Math.max(0, Math.min(1, normalizedCrop.w))
    normalizedCrop.h = Math.max(0, Math.min(1, normalizedCrop.h))

    onCrop(normalizedCrop)
  }

  if (!enabled) return null

  return (
    <div
      ref={containerRef}
      className="absolute inset-0 cursor-crosshair"
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      style={{ pointerEvents: 'auto' }}
    >
      {crop && (
        <>
          {/* Dimmed overlay */}
          <div
            className="absolute bg-black/40"
            style={{
              top: 0,
              left: 0,
              width: crop.x,
              height: displayHeight,
            }}
          />
          <div
            className="absolute bg-black/40"
            style={{
              top: 0,
              left: crop.x + crop.w,
              width: displayWidth - (crop.x + crop.w),
              height: displayHeight,
            }}
          />
          <div
            className="absolute bg-black/40"
            style={{
              top: 0,
              left: crop.x,
              width: crop.w,
              height: crop.y,
            }}
          />
          <div
            className="absolute bg-black/40"
            style={{
              top: crop.y + crop.h,
              left: crop.x,
              width: crop.w,
              height: displayHeight - (crop.y + crop.h),
            }}
          />

          {/* Crop box */}
          <div
            className="absolute border-2 border-emerald-400 bg-emerald-400/10"
            style={{
              left: crop.x,
              top: crop.y,
              width: crop.w,
              height: crop.h,
            }}
          >
            {/* Corner handles */}
            <div className="absolute -left-1.5 -top-1.5 h-3 w-3 rounded-full border-2 border-emerald-400 bg-emerald-600" />
            <div className="absolute -right-1.5 -top-1.5 h-3 w-3 rounded-full border-2 border-emerald-400 bg-emerald-600" />
            <div className="absolute -left-1.5 -bottom-1.5 h-3 w-3 rounded-full border-2 border-emerald-400 bg-emerald-600" />
            <div className="absolute -right-1.5 -bottom-1.5 h-3 w-3 rounded-full border-2 border-emerald-400 bg-emerald-600" />
          </div>
        </>
      )}

      {/* Instructions */}
      {!crop && (
        <div className="pointer-events-none absolute bottom-4 left-1/2 w-max -translate-x-1/2 rounded-full bg-slate-900/90 px-4 py-2 text-xs text-slate-300">
          Draw a box to select exemplar region (Press ESC to cancel)
        </div>
      )}
    </div>
  )
}

