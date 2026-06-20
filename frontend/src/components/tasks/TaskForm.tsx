import { useState } from 'react'
import { X } from 'lucide-react'
import type { Task, CreateTaskPayload, UpdateTaskPayload, AssigneeType, Frequency } from '@/types/tasks'

interface Props {
  task?: Task | null
  currentUserId: string
  onSave: (payload: CreateTaskPayload | UpdateTaskPayload) => Promise<void>
  onClose: () => void
}

const FREQUENCIES: { value: Frequency; label: string }[] = [
  { value: 'daily', label: 'Daily' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'monthly', label: 'Monthly' },
]

export default function TaskForm({ task, currentUserId, onSave, onClose }: Props) {
  const isEdit = !!task

  const [name, setName] = useState(task?.name ?? '')
  const [assigneeType, setAssigneeType] = useState<AssigneeType>(
    (task as (Task & { _assignToMe?: boolean }) | null)?._assignToMe
      ? 'specific'
      : (task?.assignee_type ?? 'none')
  )
  const [dueDate, setDueDate] = useState(task?.due_date ?? '')
  const [frequency, setFrequency] = useState<Frequency | ''>(task?.frequency ?? '')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) { setError('Name is required.'); return }
    setSaving(true)
    setError(null)
    try {
      const payload: CreateTaskPayload = {
        name: name.trim(),
        assignee_type: assigneeType,
        assignee_id: assigneeType === 'specific' ? currentUserId : null,
        due_date: dueDate || null,
        frequency: (frequency as Frequency) || null,
      }
      await onSave(payload)
      onClose()
    } catch {
      setError('Could not save chore. Please try again.')
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
        {/* header */}
        <div className="mb-5 flex items-center justify-between">
          <h2 className="text-base font-semibold" style={{ color: 'var(--m-fg)' }}>
            {isEdit ? 'Edit Chore' : 'New Chore'}
          </h2>
          <button
            onClick={onClose}
            className="rounded p-1"
            style={{ color: 'var(--m-fg-4)' }}
            aria-label="Close"
          >
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* name */}
          <div>
            <label className="mb-1 block text-xs font-medium" style={{ color: 'var(--m-fg-3)' }}>
              Name <span style={{ color: 'var(--m-love)' }}>*</span>
            </label>
            <input
              autoFocus
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="e.g. Vacuum living room"
              className="w-full rounded-lg border px-3 py-2 text-sm outline-none transition-colors"
              style={{
                background: 'var(--m-bg-2)',
                borderColor: 'var(--m-border)',
                color: 'var(--m-fg)',
              }}
              onFocus={e => (e.currentTarget.style.borderColor = 'var(--m-accent)')}
              onBlur={e => (e.currentTarget.style.borderColor = 'var(--m-border)')}
            />
          </div>

          {/* assignee */}
          <div>
            <label className="mb-1 block text-xs font-medium" style={{ color: 'var(--m-fg-3)' }}>
              Assigned to
            </label>
            <div className="flex gap-2">
              {(['none', 'specific', 'all'] as AssigneeType[]).map(type => (
                <button
                  key={type}
                  type="button"
                  onClick={() => setAssigneeType(type)}
                  className="flex-1 rounded-lg border py-1.5 text-xs font-medium transition-all"
                  style={{
                    borderColor: assigneeType === type ? 'var(--m-accent)' : 'var(--m-border)',
                    background: assigneeType === type ? 'var(--m-accent)' : 'var(--m-bg-2)',
                    color: assigneeType === type ? 'var(--m-accent-fg)' : 'var(--m-fg-2)',
                  }}
                >
                  {type === 'none' ? 'No one' : type === 'specific' ? 'Me' : '🏠 Everyone'}
                </button>
              ))}
            </div>
          </div>

          {/* due date */}
          <div>
            <label className="mb-1 block text-xs font-medium" style={{ color: 'var(--m-fg-3)' }}>
              Due date <span style={{ color: 'var(--m-fg-4)' }}>(optional)</span>
            </label>
            <input
              type="date"
              value={dueDate}
              onChange={e => setDueDate(e.target.value)}
              className="w-full rounded-lg border px-3 py-2 text-sm outline-none transition-colors"
              style={{
                background: 'var(--m-bg-2)',
                borderColor: 'var(--m-border)',
                color: dueDate ? 'var(--m-fg)' : 'var(--m-fg-4)',
              }}
              onFocus={e => (e.currentTarget.style.borderColor = 'var(--m-accent)')}
              onBlur={e => (e.currentTarget.style.borderColor = 'var(--m-border)')}
            />
          </div>

          {/* frequency */}
          <div>
            <label className="mb-1 block text-xs font-medium" style={{ color: 'var(--m-fg-3)' }}>
              Frequency <span style={{ color: 'var(--m-fg-4)' }}>(optional)</span>
            </label>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setFrequency('')}
                className="rounded-lg border px-3 py-1.5 text-xs font-medium transition-all"
                style={{
                  borderColor: frequency === '' ? 'var(--m-accent)' : 'var(--m-border)',
                  background: frequency === '' ? 'var(--m-accent)' : 'var(--m-bg-2)',
                  color: frequency === '' ? 'var(--m-accent-fg)' : 'var(--m-fg-2)',
                }}
              >
                None
              </button>
              {FREQUENCIES.map(f => (
                <button
                  key={f.value}
                  type="button"
                  onClick={() => setFrequency(f.value)}
                  className="flex-1 rounded-lg border py-1.5 text-xs font-medium transition-all"
                  style={{
                    borderColor: frequency === f.value ? 'var(--m-accent)' : 'var(--m-border)',
                    background: frequency === f.value ? 'var(--m-accent)' : 'var(--m-bg-2)',
                    color: frequency === f.value ? 'var(--m-accent-fg)' : 'var(--m-fg-2)',
                  }}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          {error && <p className="text-sm" style={{ color: 'var(--m-love)' }}>{error}</p>}

          <button
            type="submit"
            disabled={saving}
            className="mt-2 w-full rounded-lg py-2.5 text-sm font-semibold transition-opacity disabled:opacity-50"
            style={{ background: 'var(--m-accent)', color: 'var(--m-accent-fg)' }}
          >
            {saving ? 'Saving…' : isEdit ? 'Save Changes' : 'Add Chore'}
          </button>
        </form>
      </div>
    </div>
  )
}
