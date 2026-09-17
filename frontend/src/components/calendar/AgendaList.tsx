import { Calendar as CalendarIcon } from 'lucide-react'
import { formatTime, formatWeekdayMonthDay } from '@/lib/calendarDate'
import type { DayItems } from './calendarGrouping'

interface Props {
  itemsByDate: Record<string, DayItems>
  onSelectDay: (iso: string) => void
}

export default function AgendaList({ itemsByDate, onSelectDay }: Props) {
  const days = Object.keys(itemsByDate)
    .filter(iso => itemsByDate[iso].events.length > 0 || itemsByDate[iso].birthdays.length > 0 || itemsByDate[iso].choreDot)
    .sort()

  if (days.length === 0) {
    return (
      <div
        className="mt-6 flex flex-col items-center gap-3 rounded-xl border border-dashed py-12 text-center"
        style={{ borderColor: 'var(--m-border)' }}
      >
        <CalendarIcon size={28} style={{ color: 'var(--m-fg-4)' }} />
        <p className="text-sm" style={{ color: 'var(--m-fg-3)' }}>Nothing coming up</p>
      </div>
    )
  }

  return (
    <div className="mt-4 space-y-3">
      {days.map(iso => {
        const items = itemsByDate[iso]
        return (
          <button
            key={iso}
            type="button"
            onClick={() => onSelectDay(iso)}
            className="flex w-full flex-col gap-1.5 rounded-lg border p-3 text-left transition-colors"
            style={{ borderColor: 'var(--m-border)', background: 'var(--m-bg-2)' }}
          >
            <p className="text-xs font-semibold uppercase tracking-wide" style={{ color: 'var(--m-fg-3)' }}>
              {formatWeekdayMonthDay(iso)}
            </p>
            <div className="flex flex-col gap-1">
              {items.birthdays.map(b => (
                <p key={b.id} className="text-sm" style={{ color: 'var(--m-fg)' }}>
                  🎂 {b.person_name}
                  {b.age != null && <span style={{ color: 'var(--m-fg-3)' }}> · turning {b.age}</span>}
                </p>
              ))}
              {items.events.map(e => (
                <p key={e.id} className="text-sm" style={{ color: 'var(--m-fg)' }}>
                  {e.title}
                  {formatTime(e.start_time) && (
                    <span style={{ color: 'var(--m-fg-3)' }}> · {formatTime(e.start_time)}</span>
                  )}
                  {e.location && <span style={{ color: 'var(--m-fg-3)' }}> · {e.location}</span>}
                </p>
              ))}
              {items.choreDot && (
                <p className="text-sm" style={{ color: 'var(--m-fg-3)' }}>
                  🧽 {items.choreDot.titles.join(', ')}
                </p>
              )}
            </div>
          </button>
        )
      })}
    </div>
  )
}
