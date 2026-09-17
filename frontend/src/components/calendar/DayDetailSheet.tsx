import { Pencil, Trash2, X } from 'lucide-react'
import { formatTime, formatWeekdayMonthDay } from '@/lib/calendarDate'
import type { NativeCalendarFeedEvent, BirthdayOccurrence } from '@/types/calendar'
import type { DayItems } from './calendarGrouping'

interface Props {
  iso: string | null
  items: DayItems | undefined
  onClose: () => void
  onAddEvent: () => void
  onAddBirthday: () => void
  onEditEvent: (event: NativeCalendarFeedEvent) => void
  onDeleteEvent: (eventId: string) => void
  onEditBirthday: (occurrence: BirthdayOccurrence) => void
  onDeleteBirthday: (birthdayId: string) => void
}

export default function DayDetailSheet({
  iso,
  items,
  onClose,
  onAddEvent,
  onAddBirthday,
  onEditEvent,
  onDeleteEvent,
  onEditBirthday,
  onDeleteBirthday,
}: Props) {
  if (!iso) return null

  const events = items?.events ?? []
  const birthdays = items?.birthdays ?? []
  const choreDot = items?.choreDot

  return (
    <div className="fixed inset-0 z-40 flex items-end justify-center" onClick={onClose}>
      <div className="absolute inset-0" style={{ background: 'rgba(0,0,0,0.3)' }} />
      <div
        className="relative z-50 w-full max-w-lg rounded-t-2xl p-6 pb-8"
        style={{ background: 'var(--m-bg)' }}
        onClick={e => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-semibold" style={{ color: 'var(--m-fg)' }}>
            {formatWeekdayMonthDay(iso)}
          </h2>
          <button onClick={onClose} className="rounded p-1" style={{ color: 'var(--m-fg-4)' }} aria-label="Close">
            <X size={18} />
          </button>
        </div>

        <div className="flex gap-2">
          <button
            onClick={onAddEvent}
            className="flex-1 rounded-lg py-2 text-xs font-medium transition-colors"
            style={{ background: 'var(--m-accent)', color: 'var(--m-accent-fg)' }}
          >
            + Event
          </button>
          <button
            onClick={onAddBirthday}
            className="flex-1 rounded-lg border py-2 text-xs font-medium transition-colors"
            style={{ borderColor: 'var(--m-border)', color: 'var(--m-fg-2)' }}
          >
            + Birthday
          </button>
        </div>

        <div className="mt-4 max-h-[50vh] space-y-2 overflow-y-auto">
          {birthdays.length === 0 && events.length === 0 && !choreDot && (
            <p className="py-6 text-center text-sm" style={{ color: 'var(--m-fg-4)' }}>Nothing scheduled</p>
          )}

          {birthdays.map(b => (
            <div
              key={b.id}
              className="flex items-center justify-between rounded-lg border px-3 py-2"
              style={{ borderColor: 'var(--m-border)', background: 'var(--m-bg-2)' }}
            >
              <div>
                <p className="text-sm font-medium" style={{ color: 'var(--m-fg)' }}>🎂 {b.person_name}</p>
                {b.age != null && (
                  <p className="text-xs" style={{ color: 'var(--m-fg-3)' }}>Turning {b.age}</p>
                )}
              </div>
              <div className="flex items-center gap-2">
                <button onClick={() => onEditBirthday(b)} aria-label="Edit birthday" style={{ color: 'var(--m-fg-3)' }}>
                  <Pencil size={15} />
                </button>
                <button onClick={() => onDeleteBirthday(b.id)} aria-label="Delete birthday" style={{ color: 'var(--m-love)' }}>
                  <Trash2 size={15} />
                </button>
              </div>
            </div>
          ))}

          {events.map(e => (
            <div
              key={e.id}
              className="flex items-center justify-between rounded-lg border px-3 py-2"
              style={{ borderColor: 'var(--m-border)', background: 'var(--m-bg-2)' }}
            >
              <div>
                <p className="text-sm font-medium" style={{ color: 'var(--m-fg)' }}>{e.title}</p>
                <p className="text-xs" style={{ color: 'var(--m-fg-3)' }}>
                  {formatTime(e.start_time) ?? 'All day'}
                  {formatTime(e.end_time) ? ` – ${formatTime(e.end_time)}` : ''}
                  {e.location ? ` · ${e.location}` : ''}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button onClick={() => onEditEvent(e)} aria-label="Edit event" style={{ color: 'var(--m-fg-3)' }}>
                  <Pencil size={15} />
                </button>
                <button onClick={() => onDeleteEvent(e.id)} aria-label="Delete event" style={{ color: 'var(--m-love)' }}>
                  <Trash2 size={15} />
                </button>
              </div>
            </div>
          ))}

          {choreDot && (
            <div className="rounded-lg border px-3 py-2" style={{ borderColor: 'var(--m-border)', background: 'var(--m-bg-2)' }}>
              <p className="text-xs font-medium" style={{ color: 'var(--m-fg-3)' }}>🧽 Chores due</p>
              <ul className="mt-1 list-disc space-y-0.5 pl-4 text-sm" style={{ color: 'var(--m-fg)' }}>
                {choreDot.titles.map(title => (
                  <li key={title}>{title}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
