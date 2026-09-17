import { useState } from 'react'
import { X } from 'lucide-react'
import { parseISODate, todayISODate } from '@/lib/calendarDate'
import type { BirthdayOccurrence, CreateBirthdayPayload, UpdateBirthdayPayload } from '@/types/calendar'

interface Props {
  birthday?: BirthdayOccurrence | null
  defaultDate?: string
  onSave: (payload: CreateBirthdayPayload | UpdateBirthdayPayload) => Promise<void>
  onClose: () => void
}

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
]

// Leap-year-safe day count (2000 is a leap year) since the calendar has no birth year yet
// when the user is still picking the month/day.
function daysInMonth(month: number): number {
  return new Date(2000, month, 0).getDate()
}

// Only the fields that actually changed from `original`. The backend requires birth_month,
// birth_day and birth_year to be patched together (see UpdateBirthdayRequest), so all three —
// plus the show_year that's derived from them — go together whenever any of them changes.
function diffBirthdayPayload(original: BirthdayOccurrence, next: CreateBirthdayPayload): UpdateBirthdayPayload {
  const patch: UpdateBirthdayPayload = {}
  if (next.person_name !== original.person_name) patch.person_name = next.person_name
  const dateChanged =
    next.birth_month !== original.birth_month ||
    next.birth_day !== original.birth_day ||
    next.birth_year !== original.birth_year
  if (dateChanged) {
    patch.birth_month = next.birth_month
    patch.birth_day = next.birth_day
    patch.birth_year = next.birth_year
    patch.show_year = next.show_year
  }
  return patch
}

export default function BirthdayForm({ birthday, defaultDate, onSave, onClose }: Props) {
  const isEdit = !!birthday
  const defaultMonthDay = parseISODate(defaultDate ?? todayISODate())

  const [personName, setPersonName] = useState(birthday?.person_name ?? '')
  const [birthMonth, setBirthMonth] = useState(birthday?.birth_month ?? defaultMonthDay.month)
  const [birthDay, setBirthDay] = useState(birthday?.birth_day ?? defaultMonthDay.day)
  const [birthYear, setBirthYear] = useState(birthday?.birth_year != null ? String(birthday.birth_year) : '')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!personName.trim()) { setError('Name is required.'); return }
    if (birthDay < 1 || birthDay > daysInMonth(birthMonth)) {
      setError(`${MONTHS[birthMonth - 1]} only has ${daysInMonth(birthMonth)} days.`)
      return
    }
    setSaving(true)
    setError(null)
    try {
      const year = birthYear.trim() ? Number(birthYear.trim()) : null
      const nextValues: CreateBirthdayPayload = {
        person_name: personName.trim(),
        birth_month: birthMonth,
        birth_day: birthDay,
        birth_year: year,
        show_year: year != null,
      }
      const payload = birthday ? diffBirthdayPayload(birthday, nextValues) : nextValues
      if (birthday && Object.keys(payload).length === 0) {
        onClose()
        return
      }
      await onSave(payload)
      onClose()
    } catch {
      setError('Could not save birthday. Please try again.')
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
            {isEdit ? 'Edit Birthday' : 'New Birthday'}
          </h2>
          <button onClick={onClose} className="rounded p-1" style={{ color: 'var(--m-fg-4)' }} aria-label="Close">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-xs font-medium" style={{ color: 'var(--m-fg-3)' }}>
              Name <span style={{ color: 'var(--m-love)' }}>*</span>
            </label>
            <input
              autoFocus
              value={personName}
              onChange={e => setPersonName(e.target.value)}
              placeholder="e.g. Grandma Rose"
              className="w-full rounded-lg border px-3 py-2 text-sm outline-none transition-colors"
              style={{ background: 'var(--m-bg-2)', borderColor: 'var(--m-border)', color: 'var(--m-fg)' }}
            />
          </div>

          <div className="flex gap-2">
            <div className="flex-1">
              <label className="mb-1 block text-xs font-medium" style={{ color: 'var(--m-fg-3)' }}>
                Month
              </label>
              <select
                value={birthMonth}
                onChange={e => setBirthMonth(Number(e.target.value))}
                className="w-full rounded-lg border px-3 py-2 text-sm outline-none transition-colors"
                style={{ background: 'var(--m-bg-2)', borderColor: 'var(--m-border)', color: 'var(--m-fg)' }}
              >
                {MONTHS.map((label, i) => (
                  <option key={label} value={i + 1}>{label}</option>
                ))}
              </select>
            </div>
            <div className="w-20">
              <label className="mb-1 block text-xs font-medium" style={{ color: 'var(--m-fg-3)' }}>
                Day
              </label>
              <input
                type="number"
                min={1}
                max={daysInMonth(birthMonth)}
                value={birthDay}
                onChange={e => setBirthDay(Number(e.target.value))}
                className="w-full rounded-lg border px-3 py-2 text-sm outline-none transition-colors"
                style={{ background: 'var(--m-bg-2)', borderColor: 'var(--m-border)', color: 'var(--m-fg)' }}
              />
            </div>
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium" style={{ color: 'var(--m-fg-3)' }}>
              Year <span style={{ color: 'var(--m-fg-4)' }}>(optional — shows their age)</span>
            </label>
            <input
              type="number"
              min={1900}
              placeholder="e.g. 1990"
              value={birthYear}
              onChange={e => setBirthYear(e.target.value)}
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
            {saving ? 'Saving…' : isEdit ? 'Save Changes' : 'Add Birthday'}
          </button>
        </form>
      </div>
    </div>
  )
}
