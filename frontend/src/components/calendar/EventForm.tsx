import { useState } from 'react'
import { X } from 'lucide-react'
import TimePicker from './TimePicker'
import type { NativeCalendarFeedEvent, CreateEventPayload, UpdateEventPayload } from '@/types/calendar'

interface Props {
  event?: NativeCalendarFeedEvent | null
  defaultDate: string
  onSave: (payload: CreateEventPayload | UpdateEventPayload) => Promise<void>
  onClose: () => void
}

// Only the fields that actually changed from `original`, so a save doesn't overwrite fields the
// backend's own patch semantics would otherwise leave untouched (see UpdateEventRequest). The
// backend requires start_time/end_time to be patched as a unit, so they're included together
// whenever either one changes.
function diffEventPayload(original: NativeCalendarFeedEvent, next: CreateEventPayload): UpdateEventPayload {
  const patch: UpdateEventPayload = {}
  if (next.title !== original.title) patch.title = next.title
  if (next.event_date !== original.event_date) patch.event_date = next.event_date
  const originalStart = original.start_time?.slice(0, 5) ?? null
  const originalEnd = original.end_time?.slice(0, 5) ?? null
  if (next.start_time !== originalStart || next.end_time !== originalEnd) {
    patch.start_time = next.start_time
    patch.end_time = next.end_time
  }
  if (next.location !== original.location) patch.location = next.location
  if (next.description !== original.description) patch.description = next.description
  return patch
}

export default function EventForm({ event, defaultDate, onSave, onClose }: Props) {
  const isEdit = !!event

  const [title, setTitle] = useState(event?.title ?? '')
  const [eventDate, setEventDate] = useState(event?.event_date ?? defaultDate)
  const [allDay, setAllDay] = useState(event ? !event.start_time : true)
  const [startTime, setStartTime] = useState(event?.start_time?.slice(0, 5) ?? '')
  const [endTime, setEndTime] = useState(event?.end_time?.slice(0, 5) ?? '')
  const [location, setLocation] = useState(event?.location ?? '')
  const [description, setDescription] = useState(event?.description ?? '')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim()) { setError('Title is required.'); return }
    if (!allDay && startTime && endTime && endTime < startTime) {
      setError('End time must be after start time.')
      return
    }
    setSaving(true)
    setError(null)
    try {
      const nextValues: CreateEventPayload = {
        title: title.trim(),
        event_date: eventDate,
        start_time: allDay ? null : startTime || null,
        end_time: allDay ? null : endTime || null,
        location: location.trim() || null,
        description: description.trim() || null,
      }
      const payload = event ? diffEventPayload(event, nextValues) : nextValues
      if (event && Object.keys(payload).length === 0) {
        onClose()
        return
      }
      await onSave(payload)
      onClose()
    } catch {
      setError('Could not save event. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-40 flex items-end justify-center" onClick={onClose}>
      <div className="absolute inset-0" style={{ background: 'rgba(0,0,0,0.3)' }} />
      <div
        className="relative z-50 w-full max-w-lg rounded-t-2xl p-6 pb-8"
        style={{ background: 'var(--m-bg)' }}
        onClick={e => e.stopPropagation()}
      >
        <div className="mb-5 flex items-center justify-between">
          <h2 className="text-base font-semibold" style={{ color: 'var(--m-fg)' }}>
            {isEdit ? 'Edit Event' : 'New Event'}
          </h2>
          <button onClick={onClose} className="rounded p-1" style={{ color: 'var(--m-fg-4)' }} aria-label="Close">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-xs font-medium" style={{ color: 'var(--m-fg-3)' }}>
              Title <span style={{ color: 'var(--m-love)' }}>*</span>
            </label>
            <input
              autoFocus
              value={title}
              onChange={e => setTitle(e.target.value)}
              placeholder="e.g. Dentist appointment"
              className="w-full rounded-lg border px-3 py-2 text-sm outline-none transition-colors"
              style={{ background: 'var(--m-bg-2)', borderColor: 'var(--m-border)', color: 'var(--m-fg)' }}
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium" style={{ color: 'var(--m-fg-3)' }}>
              Date
            </label>
            <input
              type="date"
              value={eventDate}
              onChange={e => setEventDate(e.target.value)}
              className="w-full rounded-lg border px-3 py-2 text-sm outline-none transition-colors"
              style={{ background: 'var(--m-bg-2)', borderColor: 'var(--m-border)', color: 'var(--m-fg)' }}
            />
          </div>

          <div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setAllDay(true)}
                className="flex-1 rounded-lg border py-1.5 text-xs font-medium transition-all"
                style={{
                  borderColor: allDay ? 'var(--m-accent)' : 'var(--m-border)',
                  background: allDay ? 'var(--m-accent)' : 'var(--m-bg-2)',
                  color: allDay ? 'var(--m-accent-fg)' : 'var(--m-fg-2)',
                }}
              >
                All day
              </button>
              <button
                type="button"
                onClick={() => setAllDay(false)}
                className="flex-1 rounded-lg border py-1.5 text-xs font-medium transition-all"
                style={{
                  borderColor: !allDay ? 'var(--m-accent)' : 'var(--m-border)',
                  background: !allDay ? 'var(--m-accent)' : 'var(--m-bg-2)',
                  color: !allDay ? 'var(--m-accent-fg)' : 'var(--m-fg-2)',
                }}
              >
                Specific time
              </button>
            </div>

            {!allDay && (
              <div className="mt-2 flex gap-2">
                <div className="flex-1">
                  <TimePicker value={startTime} onChange={setStartTime} placeholder="Start time" />
                </div>
                <div className="flex-1">
                  <TimePicker value={endTime} onChange={setEndTime} placeholder="End time" />
                </div>
              </div>
            )}
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium" style={{ color: 'var(--m-fg-3)' }}>
              Location <span style={{ color: 'var(--m-fg-4)' }}>(optional)</span>
            </label>
            <input
              value={location}
              onChange={e => setLocation(e.target.value)}
              className="w-full rounded-lg border px-3 py-2 text-sm outline-none transition-colors"
              style={{ background: 'var(--m-bg-2)', borderColor: 'var(--m-border)', color: 'var(--m-fg)' }}
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium" style={{ color: 'var(--m-fg-3)' }}>
              Description <span style={{ color: 'var(--m-fg-4)' }}>(optional)</span>
            </label>
            <textarea
              value={description}
              onChange={e => setDescription(e.target.value)}
              rows={3}
              className="w-full rounded-lg border px-3 py-2 text-sm outline-none transition-colors"
              style={{ background: 'var(--m-bg-2)', borderColor: 'var(--m-border)', color: 'var(--m-fg)' }}
            />
          </div>

          {error && <p className="text-sm" style={{ color: 'var(--m-love)' }}>{error}</p>}

          <button
            type="submit"
            disabled={saving}
            className="mt-2 w-full rounded-lg py-2.5 text-sm font-semibold transition-opacity disabled:opacity-50"
            style={{ background: 'var(--m-accent)', color: 'var(--m-accent-fg)' }}
          >
            {saving ? 'Saving…' : isEdit ? 'Save Changes' : 'Add Event'}
          </button>
        </form>
      </div>
    </div>
  )
}
