import { useMemo, useState } from 'react'
import { ChevronLeft, ChevronRight, Plus } from 'lucide-react'
import { useCalendar } from '@/hooks/useCalendar'
import { useCalendarRealtime } from '@/hooks/useCalendarRealtime'
import { addDays, addMonths, getMonthGridDays, monthLabel, todayISODate } from '@/lib/calendarDate'
import { groupFeedByDate } from './calendarGrouping'
import MonthGrid from './MonthGrid'
import AgendaList from './AgendaList'
import DayDetailSheet from './DayDetailSheet'
import EventForm from './EventForm'
import BirthdayForm from './BirthdayForm'
import type {
  NativeCalendarFeedEvent,
  BirthdayOccurrence,
  CreateEventPayload,
  UpdateEventPayload,
  CreateBirthdayPayload,
  UpdateBirthdayPayload,
} from '@/types/calendar'

const AGENDA_WINDOW_DAYS = 90

type View = 'month' | 'agenda'

interface Props {
  householdId: string
}

export default function CalendarTab({ householdId }: Props) {
  const today = todayISODate()
  const [{ year, month }, setViewMonth] = useState(() => {
    const now = new Date()
    return { year: now.getFullYear(), month: now.getMonth() + 1 }
  })
  const [view, setView] = useState<View>('month')
  const [selectedDate, setSelectedDate] = useState<string | null>(null)
  const [editingEvent, setEditingEvent] = useState<NativeCalendarFeedEvent | null>(null)
  const [showEventForm, setShowEventForm] = useState(false)
  const [editingBirthday, setEditingBirthday] = useState<BirthdayOccurrence | null>(null)
  const [showBirthdayForm, setShowBirthdayForm] = useState(false)

  const { from, to } = useMemo(() => {
    if (view === 'agenda') {
      return { from: today, to: addDays(today, AGENDA_WINDOW_DAYS) }
    }
    const days = getMonthGridDays(year, month)
    return { from: days[0].iso, to: days[days.length - 1].iso }
  }, [view, year, month, today])

  const {
    feed,
    loading,
    error,
    refetch,
    createEvent,
    updateEvent,
    deleteEvent,
    createBirthday,
    updateBirthday,
    deleteBirthday,
  } = useCalendar(from, to)

  useCalendarRealtime(householdId, refetch)

  const itemsByDate = useMemo(() => groupFeedByDate(feed), [feed])

  const navigateMonth = (delta: number) => setViewMonth(prev => addMonths(prev.year, prev.month, delta))

  const openAddEvent = () => {
    setEditingEvent(null)
    setShowEventForm(true)
  }

  const handleSaveEvent = async (payload: CreateEventPayload | UpdateEventPayload) => {
    if (editingEvent) {
      await updateEvent(editingEvent.id, payload as UpdateEventPayload)
    } else {
      await createEvent(payload as CreateEventPayload)
    }
  }

  const handleSaveBirthday = async (payload: CreateBirthdayPayload | UpdateBirthdayPayload) => {
    if (editingBirthday) {
      await updateBirthday(editingBirthday.id, payload as UpdateBirthdayPayload)
    } else {
      await createBirthday(payload as CreateBirthdayPayload)
    }
  }

  return (
    <div className="rounded-xl min-h-[400px]" style={{ color: 'var(--m-fg)' }}>
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-widest" style={{ color: 'var(--m-fg-3)' }}>Calendar</p>
        <div className="flex gap-1 rounded-lg border p-0.5" style={{ borderColor: 'var(--m-border)' }}>
          <button
            onClick={() => setView('month')}
            className="rounded-md px-2.5 py-1 text-xs font-medium transition-colors"
            style={{
              background: view === 'month' ? 'var(--m-accent)' : 'transparent',
              color: view === 'month' ? 'var(--m-accent-fg)' : 'var(--m-fg-3)',
            }}
          >
            Month
          </button>
          <button
            onClick={() => setView('agenda')}
            className="rounded-md px-2.5 py-1 text-xs font-medium transition-colors"
            style={{
              background: view === 'agenda' ? 'var(--m-accent)' : 'transparent',
              color: view === 'agenda' ? 'var(--m-accent-fg)' : 'var(--m-fg-3)',
            }}
          >
            Agenda
          </button>
        </div>
      </div>

      {view === 'month' && (
        <div className="mt-3 flex items-center justify-between">
          <button onClick={() => navigateMonth(-1)} aria-label="Previous month" style={{ color: 'var(--m-fg-3)' }}>
            <ChevronLeft size={18} />
          </button>
          <p className="text-sm font-semibold" style={{ color: 'var(--m-fg)' }}>{monthLabel(year, month)}</p>
          <button onClick={() => navigateMonth(1)} aria-label="Next month" style={{ color: 'var(--m-fg-3)' }}>
            <ChevronRight size={18} />
          </button>
        </div>
      )}

      {error && <p className="mt-4 text-sm text-destructive">{error}</p>}
      {loading && <p className="mt-8 text-center text-sm" style={{ color: 'var(--m-fg-4)' }}>Loading…</p>}

      {!loading && (
        <div className="mt-4">
          {view === 'month' ? (
            <MonthGrid
              year={year}
              month={month}
              itemsByDate={itemsByDate}
              selectedDate={selectedDate}
              onSelectDay={setSelectedDate}
            />
          ) : (
            <AgendaList itemsByDate={itemsByDate} onSelectDay={setSelectedDate} />
          )}
        </div>
      )}

      <button
        onClick={openAddEvent}
        className="fixed bottom-24 right-6 z-30 flex h-12 w-12 items-center justify-center rounded-full shadow-lg"
        style={{ background: 'var(--m-accent)', color: 'var(--m-accent-fg)' }}
        aria-label="Add event"
      >
        <Plus size={22} />
      </button>

      <DayDetailSheet
        iso={selectedDate}
        items={selectedDate ? itemsByDate[selectedDate] : undefined}
        onClose={() => setSelectedDate(null)}
        onAddEvent={openAddEvent}
        onAddBirthday={() => { setEditingBirthday(null); setShowBirthdayForm(true) }}
        onEditEvent={event => { setEditingEvent(event); setShowEventForm(true) }}
        onDeleteEvent={deleteEvent}
        onEditBirthday={occurrence => { setEditingBirthday(occurrence); setShowBirthdayForm(true) }}
        onDeleteBirthday={deleteBirthday}
      />

      {showEventForm && (
        <EventForm
          event={editingEvent}
          defaultDate={selectedDate ?? today}
          onSave={handleSaveEvent}
          onClose={() => setShowEventForm(false)}
        />
      )}

      {showBirthdayForm && (
        <BirthdayForm
          birthday={editingBirthday}
          defaultDate={selectedDate ?? today}
          onSave={handleSaveBirthday}
          onClose={() => setShowBirthdayForm(false)}
        />
      )}
    </div>
  )
}
