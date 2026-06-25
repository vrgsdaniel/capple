import { useState } from 'react'
import { Check, Trash2, Pencil } from 'lucide-react'
import type { Task } from '@/types/tasks'
import type { HouseholdMembers } from '@/types/household'

interface Props {
  task: Task
  members: HouseholdMembers | null
  currentUserId: string
  onComplete: (id: string) => Promise<void>
  onDelete: (id: string) => Promise<void>
  onEdit: (task: Task) => void
}

function resolveAssigneeName(task: Task, members: HouseholdMembers | null, currentUserId: string): string {
  if (task.assignee_type !== 'specific') return ''
  if (task.assignee_id === currentUserId) return 'Me'
  const match = members?.others.find(m => m.id === task.assignee_id)
  return match?.name ?? 'Someone'
}

function dueDateLabel(dateStr: string): { text: string; overdue: boolean } {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const due = new Date(dateStr + 'T00:00:00')
  const diff = Math.round((due.getTime() - today.getTime()) / 86_400_000)
  if (diff < 0) return { text: `${Math.abs(diff)}d overdue`, overdue: true }
  if (diff === 0) return { text: 'Due today', overdue: false }
  if (diff === 1) return { text: 'Due tomorrow', overdue: false }
  if (diff < 7) return { text: `Due in ${diff} days`, overdue: false }
  return { text: `Due ${due.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}`, overdue: false }
}

function Chip({ children, color = 'var(--m-fg-3)' }: { children: React.ReactNode; color?: string }) {
  return (
    <span
      className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px]"
      style={{ background: 'var(--m-bg-3)', color }}
    >
      {children}
    </span>
  )
}

const FREQUENCY_LABEL: Record<string, string> = {
  daily: 'Daily',
  weekly: 'Weekly',
  monthly: 'Monthly',
}

export default function TaskItem({ task, members, currentUserId, onComplete, onDelete, onEdit }: Props) {
  const [leaving, setLeaving] = useState(false)
  const [checked, setChecked] = useState(false)

  const handleComplete = () => {
    if (leaving) return
    setChecked(true)
    setLeaving(true)
    setTimeout(() => onComplete(task.id), 220)
  }

  const dueInfo = task.due_date ? dueDateLabel(task.due_date) : null
  const assigneeName = resolveAssigneeName(task, members, currentUserId)

  return (
    <div
      className="task-item group relative flex items-center gap-3 rounded-lg px-1 py-2.5 transition-all duration-[220ms]"
      style={{
        opacity: leaving ? 0 : 1,
        transform: leaving ? 'translateX(8px)' : 'translateX(0)',
      }}
      onDoubleClick={() => onEdit(task)}
    >
      {/* complete button */}
      <button
        onClick={handleComplete}
        className="flex shrink-0 items-center justify-center rounded-full transition-all duration-150"
        style={{
          width: 22,
          height: 22,
          border: checked ? 'none' : '1.75px solid var(--m-fg-4)',
          background: checked ? 'var(--m-accent)' : 'transparent',
        }}
        aria-label="Mark complete"
      >
        {checked && <Check size={13} strokeWidth={2.5} color="var(--m-accent-fg)" />}
      </button>

      {/* name + meta */}
      <div className="flex flex-1 flex-col min-w-0">
        <span className="truncate text-[14.5px]" style={{ color: 'var(--m-fg)' }}>{task.name}</span>
        <div className="mt-0.5 flex flex-wrap items-center gap-1.5">
          {/* due date always first */}
          {dueInfo && (
            <Chip color={dueInfo.overdue ? 'var(--m-love)' : 'var(--m-fg-3)'}>
              {dueInfo.text}
            </Chip>
          )}
          {/* assignee */}
          {task.assignee_type === 'all' && <Chip>🏠 Everyone</Chip>}
          {task.assignee_type === 'specific' && (
            <Chip>{assigneeName}</Chip>
          )}
          {/* frequency */}
          {task.frequency && (
            <Chip>{FREQUENCY_LABEL[task.frequency]}</Chip>
          )}
        </div>
      </div>

      {/* action buttons — revealed on hover */}
      <div className="flex shrink-0 items-center gap-0.5 opacity-0 transition-opacity duration-120 group-hover:opacity-100 [@media(pointer:coarse)]:opacity-100">
        <button
          onClick={e => { e.stopPropagation(); onEdit(task) }}
          className="rounded p-1.5 transition-colors"
          style={{ color: 'var(--m-fg-4)' }}
          onMouseEnter={e => (e.currentTarget.style.color = 'var(--m-fg-2)')}
          onMouseLeave={e => (e.currentTarget.style.color = 'var(--m-fg-4)')}
          aria-label="Edit"
        >
          <Pencil size={14} />
        </button>
        <button
          onClick={e => { e.stopPropagation(); onDelete(task.id) }}
          className="rounded p-1.5 transition-colors"
          style={{ color: 'var(--m-fg-4)' }}
          onMouseEnter={e => (e.currentTarget.style.color = 'var(--m-love)')}
          onMouseLeave={e => (e.currentTarget.style.color = 'var(--m-fg-4)')}
          aria-label="Delete"
        >
          <Trash2 size={14} />
        </button>
      </div>
    </div>
  )
}
