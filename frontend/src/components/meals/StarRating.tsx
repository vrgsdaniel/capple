import { useId, useState } from 'react'

interface StarSvgProps {
  fillRatio: number
  size?: number
}

function StarSvg({ fillRatio, size = 12 }: StarSvgProps) {
  const uid = useId()
  const clipId = `sc${uid.replace(/[^a-zA-Z0-9]/g, 'x')}`
  const pts =
    '12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2'
  const clamped = Math.max(0, Math.min(1, fillRatio))

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      style={{ flexShrink: 0, display: 'block' }}
    >
      <defs>
        <clipPath id={clipId}>
          <rect x="0" y="0" width={24 * clamped} height="24" />
        </clipPath>
      </defs>
      <polygon
        points={pts}
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinejoin="round"
      />
      {clamped > 0 && (
        <polygon
          points={pts}
          fill="currentColor"
          clipPath={`url(#${clipId})`}
        />
      )}
    </svg>
  )
}

interface StarDisplayProps {
  rating: number
  size?: number
}

export function StarDisplay({ rating, size = 12 }: StarDisplayProps) {
  return (
    <span className="meals-stars accent">
      {[0, 1, 2, 3, 4].map(i => (
        <StarSvg
          key={i}
          fillRatio={Math.max(0, Math.min(1, rating - i))}
          size={size}
        />
      ))}
    </span>
  )
}

interface StarInputProps {
  value: number
  onChange: (v: number) => void
}

export function StarInput({ value, onChange }: StarInputProps) {
  const [hover, setHover] = useState(0)
  const display = hover || value

  return (
    <div className="meals-star-input" onMouseLeave={() => setHover(0)}>
      {[1, 2, 3, 4, 5].map(n => (
        <button
          key={n}
          type="button"
          className={n <= display ? 'active' : ''}
          onMouseEnter={() => setHover(n)}
          onClick={() => onChange(n === value ? 0 : n)}
          aria-label={`Rate ${n} stars`}
        >
          <StarSvg fillRatio={n <= display ? 1 : 0} size={20} />
        </button>
      ))}
    </div>
  )
}
