interface Props {
  score: number
  threshold?: number
  size?: 'sm' | 'md' | 'lg'
  showValue?: boolean
}

export const ConfidenceIndicator = ({ score, threshold = 0.7, size = 'md', showValue = true }: Props) => {
  const getColor = () => {
    if (score >= threshold) return 'bg-green-500'
    if (score >= threshold * 0.7) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  const getTextColor = () => {
    if (score >= threshold) return 'text-green-400'
    if (score >= threshold * 0.7) return 'text-yellow-400'
    return 'text-red-400'
  }

  const getBorderColor = () => {
    if (score >= threshold) return 'border-green-500'
    if (score >= threshold * 0.7) return 'border-yellow-500'
    return 'border-red-500'
  }

  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return 'h-1'
      case 'md':
        return 'h-2'
      case 'lg':
        return 'h-3'
      default:
        return 'h-2'
    }
  }

  const isLowConfidence = score < threshold

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 overflow-hidden rounded-full bg-slate-700">
        <div
          className={`${getColor()} ${getSizeClasses()} transition-all duration-300`}
          style={{ width: `${Math.min(score * 100, 100)}%` }}
        />
      </div>
      {showValue && (
        <span className={`text-xs font-medium ${getTextColor()}`}>{(score * 100).toFixed(1)}%</span>
      )}
      {isLowConfidence && (
        <span className="text-xs text-yellow-400" title="Low confidence - may need review">
          ⚠️
        </span>
      )}
    </div>
  )
}

interface ConfidenceBadgeProps {
  score: number | null
  threshold?: number
  className?: string
}

export const ConfidenceBadge = ({ score, threshold = 0.7, className = '' }: ConfidenceBadgeProps) => {
  if (score === null) return null

  const isHigh = score >= threshold
  const isMedium = score >= threshold * 0.7

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${
        isHigh
          ? 'bg-green-500/20 text-green-400 border border-green-500/30'
          : isMedium
            ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
            : 'bg-red-500/20 text-red-400 border border-red-500/30'
      } ${className}`}
      title={`Confidence: ${(score * 100).toFixed(1)}%`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {(score * 100).toFixed(0)}%
    </span>
  )
}

