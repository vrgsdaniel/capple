import { getMonthGridDays, todayISODate } from '@/lib/calendarDate'
import type { DayItems } from './calendarGrouping'

const WEEKDAY_LABELS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
const MAX_TITLES_PER_DAY = 3

interface Props {
  year: number
  month: number
  itemsByDate: Record<string, DayItems>
  selectedDate: string | null
  onSelectDay: (iso: string) => void
}

export default function MonthGrid({ year, month, itemsByDate, selectedDate, onSelectDay }: Props) {
  const days = getMonthGridDays(year, month)
  const today = todayISODate()

  return (
    <div>
      <div className="grid grid-cols-7 gap-1 pb-1">
        {WEEKDAY_LABELS.map(label => (
          <div key={label} className="text-center text-[11px] font-medium" style={{ color: 'var(--m-fg-4)' }}>
            {label}
          </div>
        ))}
      </div>
      <div className="grid grid-cols-7 gap-1">
        {days.map(({ iso, day, inCurrentMonth }) => {
          const items = itemsByDate[iso]
          const titles = [
            ...(items?.birthdays ?? []).map(b => `🎂 ${b.person_name}`),
            ...(items?.events ?? []).map(e => e.title),
          ]
          const isToday = iso === today
          const isSelected = iso === selectedDate

          return (
            <button
              key={iso}
              type="button"
              onClick={() => onSelectDay(iso)}
              className="flex min-h-[64px] flex-col items-stretch rounded-lg border p-1 text-left transition-colors"
              style={{
                borderColor: isSelected ? 'var(--m-accent)' : 'var(--m-border)',
                background: isSelected ? 'var(--m-accent)' : 'var(--m-bg-2)',
                opacity: inCurrentMonth ? 1 : 0.4,
              }}
            >
              <div className="flex items-center justify-between">
                <span
                  className="text-xs font-medium"
                  style={{
                    color: isSelected ? 'var(--m-accent-fg)' : 'var(--m-fg-2)',
                    ...(isToday && !isSelected ? { color: 'var(--m-accent)', fontWeight: 700 } : {}),
                  }}
                >
                  {day}
                </span>
                {items?.choreDot && (
                  <span
                    className="rounded px-1 text-[10px] font-medium"
                    style={{
                      background: isSelected ? 'var(--m-accent-fg)' : 'var(--m-bg)',
                      color: isSelected ? 'var(--m-accent)' : 'var(--m-fg-3)',
                    }}
                  >
                    🧽 {items.choreDot.count}
                  </span>
                )}
              </div>
              <div className="mt-0.5 flex flex-col gap-0.5">
                {titles.slice(0, MAX_TITLES_PER_DAY).map((title, i) => (
                  <span
                    key={i}
                    className="truncate text-[10px] leading-tight"
                    style={{ color: isSelected ? 'var(--m-accent-fg)' : 'var(--m-fg-3)' }}
                  >
                    {title}
                  </span>
                ))}
                {titles.length > MAX_TITLES_PER_DAY && (
                  <span
                    className="text-[10px] leading-tight"
                    style={{ color: isSelected ? 'var(--m-accent-fg)' : 'var(--m-fg-4)' }}
                  >
                    +{titles.length - MAX_TITLES_PER_DAY} more
                  </span>
                )}
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
