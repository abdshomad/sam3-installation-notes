import { useEffect, useRef } from 'react'
import { decodeRLE, renderMaskToCanvas } from '../utils/maskDecoder'

interface Props {
  maskRLE: string
  width: number
  height: number
  displayWidth: number
  displayHeight: number
  color: string
  alpha?: number
}

export const MaskOverlay = ({ maskRLE, width, height, displayWidth, displayHeight, color, alpha = 0.3 }: Props) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    if (!canvasRef.current || !maskRLE) return

    try {
      // Decode RLE mask
      const mask = decodeRLE(maskRLE, width, height)
      
      // Create a temporary canvas for the full-size mask
      const tempCanvas = document.createElement('canvas')
      tempCanvas.width = width
      tempCanvas.height = height
      
      // Render to temporary canvas
      renderMaskToCanvas(tempCanvas, mask, color, alpha)
      
      // Scale to display size
      const ctx = canvasRef.current.getContext('2d')
      if (ctx) {
        canvasRef.current.width = displayWidth
        canvasRef.current.height = displayHeight
        ctx.imageSmoothingEnabled = true
        ctx.drawImage(tempCanvas, 0, 0, width, height, 0, 0, displayWidth, displayHeight)
      }
    } catch (error) {
      console.warn('Failed to render mask overlay:', error)
    }
  }, [maskRLE, width, height, displayWidth, displayHeight, color, alpha])

  if (!maskRLE) return null

  return (
    <canvas
      ref={canvasRef}
      className="absolute left-0 top-0"
      style={{
        width: `${displayWidth}px`,
        height: `${displayHeight}px`,
        imageRendering: 'pixelated',
      }}
    />
  )
}

