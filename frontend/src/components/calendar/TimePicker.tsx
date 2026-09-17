import { useEffect, useRef } from 'react'
import { Clock } from 'lucide-react'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { formatTime } from '@/lib/calendarDate'

const HOURS = Array.from({ length: 12 }, (_, i) => i + 1) // 1..12
const MINUTES = Array.from({ length: 12 }, (_, i) => i * 5) // :00, :05, ... :55
const PERIODS = ['AM', 'PM'] as const
type Period = (typeof PERIODS)[number]

const COLUMN_HEIGHT = 160
const ITEM_HEIGHT = 32
// Pads each column so the first/last item can still scroll-snap to the vertical center.
const COLUMN_PAD = (COLUMN_HEIGHT - ITEM_HEIGHT) / 2

interface Props {
  value: string | null // 'HH:MM' in 24h time, or null/'' when unset
  onChange: (value: string) => void
  placeholder?: string
}

function to24Hour(hour12: number, period: Period): number {
  if (period === 'AM') return hour12 === 12 ? 0 : hour12
  return hour12 === 12 ? 12 : hour12 + 12
}

function from24Hour(hour24: number): { hour12: number; period: Period } {
  const period: Period = hour24 < 12 ? 'AM' : 'PM'
  const hour12 = hour24 % 12 === 0 ? 12 : hour24 % 12
  return { hour12, period }
}

/** A scrolling, snap-to-value time picker (hour / 5-minute / AM-PM columns) — a compact stand-in
 * for a clock dial, rather than a single flat list of all 60 minute values. */
export default function TimePicker({ value, onChange, placeholder = 'Select time' }: Props) {
  const [hour24, minute] = value ? value.split(':').map(Number) : [9, 0]
  const { hour12, period } = from24Hour(hour24)

  const commit = (nextHour12: number, nextMinute: number, nextPeriod: Period) => {
    const h24 = to24Hour(nextHour12, nextPeriod)
    onChange(`${String(h24).padStart(2, '0')}:${String(nextMinute).padStart(2, '0')}`)
  }

  return (
    <Popover>
      <PopoverTrigger asChild>
        <button
          type="button"
          className="flex w-full items-center gap-2 rounded-lg border px-3 py-2 text-sm outline-none transition-colors"
          style={{
            background: 'var(--m-bg-2)',
            borderColor: 'var(--m-border)',
            color: value ? 'var(--m-fg)' : 'var(--m-fg-4)',
          }}
        >
          <Clock size={15} style={{ color: 'var(--m-fg-3)' }} />
          {value ? formatTime(value) : placeholder}
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-2" style={{ background: 'var(--m-bg)', borderColor: 'var(--m-border)' }}>
        <div className="flex gap-1">
          <TimeColumn values={HOURS} selected={hour12} format={String} onSelect={v => commit(v, minute, period)} />
          <TimeColumn
            values={MINUTES}
            selected={minute}
            format={v => String(v).padStart(2, '0')}
            onSelect={v => commit(hour12, v, period)}
          />
          <TimeColumn values={[...PERIODS]} selected={period} format={v => v} onSelect={v => commit(hour12, minute, v)} />
        </div>
      </PopoverContent>
    </Popover>
  )
}

function TimeColumn<T extends string | number>({
  values,
  selected,
  format,
  onSelect,
}: {
  values: T[]
  selected: T
  format: (v: T) => string
  onSelect: (v: T) => void
}) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    containerRef.current
      ?.querySelector<HTMLElement>('[data-selected="true"]')
      ?.scrollIntoView({ block: 'center' })
  }, [])

  return (
    <div
      ref={containerRef}
      className="overflow-y-auto rounded-lg"
      style={{ height: COLUMN_HEIGHT, width: 56, scrollSnapType: 'y mandatory', background: 'var(--m-bg-2)' }}
    >
      <div style={{ paddingBlock: COLUMN_PAD }}>
        {values.map(v => {
          const isSelected = v === selected
          return (
            <button
              key={String(v)}
              type="button"
              data-selected={isSelected}
              onClick={() => onSelect(v)}
              className="flex w-full items-center justify-center text-sm font-medium transition-colors"
              style={{
                height: ITEM_HEIGHT,
                scrollSnapAlign: 'center',
                color: isSelected ? 'var(--m-accent-fg)' : 'var(--m-fg-2)',
                background: isSelected ? 'var(--m-accent)' : 'transparent',
                borderRadius: 8,
              }}
            >
              {format(v)}
            </button>
          )
        })}
      </div>
    </div>
  )
}
