/**
 * RLE (Run-Length Encoding) mask decoder for SAM3 annotations.
 * 
 * RLE format: A string of run-length encoded values representing a binary mask.
 * This decoder converts RLE strings to binary masks and can generate SVG paths.
 */

/**
 * Decode RLE string to binary mask array
 * RLE format can be:
 * 1. Space-separated numbers: "count1 count2 count3..." (alternating 0s and 1s)
 * 2. Compressed string format from pycocotools
 * 
 * For SAM3, masks are typically stored as RLE strings from pycocotools format
 */
export function decodeRLE(rle: string, width: number, height: number): boolean[][] {
  const mask: boolean[][] = Array(height)
    .fill(null)
    .map(() => Array(width).fill(false))

  let counts: number[]
  
  // Try to parse as space-separated numbers first
  if (rle.includes(' ')) {
    counts = rle.split(' ').map(Number).filter((n) => !isNaN(n))
  } else {
    // Try to parse as compressed RLE format
    // This is a simplified parser - full pycocotools RLE format is more complex
    // For now, we'll assume it's a space-separated format or handle common cases
    try {
      // If it's a JSON-like array string
      if (rle.startsWith('[') && rle.endsWith(']')) {
        counts = JSON.parse(rle)
      } else {
        // Try splitting by common delimiters
        counts = rle.split(/[,\s]+/).map(Number).filter((n) => !isNaN(n))
      }
    } catch {
      console.warn('Failed to parse RLE format, using fallback')
      return mask
    }
  }

  if (counts.length === 0) {
    return mask
  }

  let currentValue = 0
  let position = 0

  for (const count of counts) {
    const numCount = Math.floor(count)
    if (numCount <= 0) continue
    
    for (let i = 0; i < numCount; i++) {
      const y = Math.floor(position / width)
      const x = position % width
      if (y >= 0 && y < height && x >= 0 && x < width) {
        mask[y][x] = currentValue === 1
      }
      position++
      
      // Safety check to prevent infinite loops
      if (position >= width * height) break
    }
    currentValue = 1 - currentValue
    
    if (position >= width * height) break
  }

  return mask
}

/**
 * Convert binary mask to SVG path for efficient rendering
 */
export function maskToSVGPath(mask: boolean[][], scaleX: number, scaleY: number): string {
  const paths: string[] = []
  const height = mask.length
  const width = mask[0]?.length || 0

  // Simple approach: create rectangles for each pixel (can be optimized with polygon simplification)
  // For better performance, we'll use a simplified approach with larger regions
  const visited = Array(height)
    .fill(null)
    .map(() => Array(width).fill(false))

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      if (mask[y][x] && !visited[y][x]) {
        // Find contiguous region
        const region = findContiguousRegion(mask, visited, x, y, width, height)
        if (region.length > 0) {
          const path = regionToPath(region, scaleX, scaleY)
          paths.push(path)
        }
      }
    }
  }

  return paths.join(' ')
}

/**
 * Find contiguous region of true values
 */
function findContiguousRegion(
  mask: boolean[][],
  visited: boolean[][],
  startX: number,
  startY: number,
  width: number,
  height: number,
): Array<{ x: number; y: number }> {
  const region: Array<{ x: number; y: number }> = []
  const stack: Array<{ x: number; y: number }> = [{ x: startX, y: startY }]

  while (stack.length > 0) {
    const { x, y } = stack.pop()!
    if (x < 0 || x >= width || y < 0 || y >= height || visited[y][x] || !mask[y][x]) {
      continue
    }

    visited[y][x] = true
    region.push({ x, y })

    // Check 4-connected neighbors
    stack.push({ x: x + 1, y })
    stack.push({ x: x - 1, y })
    stack.push({ x, y: y + 1 })
    stack.push({ x, y: y - 1 })
  }

  return region
}

/**
 * Convert region to SVG path (simplified - using bounding box for now)
 * For better quality, use polygon simplification algorithms
 */
function regionToPath(region: Array<{ x: number; y: number }>, scaleX: number, scaleY: number): string {
  if (region.length === 0) return ''

  // Simple approach: create a polygon from the region boundary
  // For better performance, we'll use a simplified convex hull or bounding box
  const minX = Math.min(...region.map((p) => p.x))
  const maxX = Math.max(...region.map((p) => p.x))
  const minY = Math.min(...region.map((p) => p.y))
  const maxY = Math.max(...region.map((p) => p.y))

  // Create a simple rectangle path (can be improved with actual polygon)
  const x1 = minX * scaleX
  const y1 = minY * scaleY
  const x2 = (maxX + 1) * scaleX
  const y2 = (maxY + 1) * scaleY

  return `M ${x1} ${y1} L ${x2} ${y1} L ${x2} ${y2} L ${x1} ${y2} Z`
}

/**
 * Render mask as canvas overlay (more efficient for large masks)
 */
export function renderMaskToCanvas(
  canvas: HTMLCanvasElement,
  mask: boolean[][],
  color: string,
  alpha: number = 0.3,
): void {
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const height = mask.length
  const width = mask[0]?.length || 0
  canvas.width = width
  canvas.height = height

  const imageData = ctx.createImageData(width, height)
  const rgba = hexToRgba(color, alpha)

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const index = (y * width + x) * 4
      if (mask[y][x]) {
        imageData.data[index] = rgba.r
        imageData.data[index + 1] = rgba.g
        imageData.data[index + 2] = rgba.b
        imageData.data[index + 3] = rgba.a
      }
    }
  }

  ctx.putImageData(imageData, 0, 0)
}

function hexToRgba(hex: string, alpha: number): { r: number; g: number; b: number; a: number } {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return { r, g, b, a: Math.round(alpha * 255) }
}

/**
 * Check if annotation has a mask (RLE format)
 */
export function hasMask(annotation: { geometry?: Record<string, any> }): boolean {
  const segmentation = annotation.geometry?.segmentation
  return typeof segmentation === 'string' && segmentation.length > 0
}

/**
 * Get mask data from annotation
 */
export function getMaskData(annotation: { geometry?: Record<string, any> }): string | null {
  const segmentation = annotation.geometry?.segmentation
  if (typeof segmentation === 'string') {
    return segmentation
  }
  return null
}

