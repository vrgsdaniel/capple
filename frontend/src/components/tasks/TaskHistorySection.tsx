import { useState } from 'react'
import { ChevronDown, History } from 'lucide-react'
import type { Task } from '@/types/tasks'
import type { HouseholdMembers } from '@/types/household'

interface Props {
  tasks: Task[]
  total: number
  members: HouseholdMembers | null
  currentUserId: string
}

function resolveAssigneeName(task: Task, members: HouseholdMembers | null, currentUserId: string): string {
  if (task.assignee_type !== 'specific') return ''
  if (task.assignee_id === currentUserId) return 'Me'
  const match = members?.others.find(m => m.id === task.assignee_id)
  return match?.name ?? 'Someone'
}

function completedLabel(dateStr: string): string {
  const diff = Math.floor((Date.now() - new Date(dateStr).getTime()) / 86_400_000)
  if (diff === 0) return 'Today'
  if (diff === 1) return 'Yesterday'
  if (diff < 7) return `${diff} days ago`
  return new Date(dateStr).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

function Chip({ children }: { children: React.ReactNode }) {
  return (
    <span
      className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px]"
      style={{ background: 'var(--m-bg-3)', color: 'var(--m-fg-4)' }}
    >
      {children}
    </span>
  )
}

export default function TaskHistorySection({ tasks, total, members, currentUserId }: Props) {
  const [open, setOpen] = useState(false)

  if (total === 0) return null

  return (
    <div className="mt-6 border-t pt-4" style={{ borderColor: 'var(--m-border)' }}>
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        className="flex w-full items-center gap-2 text-left transition-colors"
        style={{ color: 'var(--m-fg-3)' }}
        onMouseEnter={e => (e.currentTarget.style.color = 'var(--m-fg-2)')}
        onMouseLeave={e => (e.currentTarget.style.color = 'var(--m-fg-3)')}
      >
        <History size={14} />
        <span className="text-sm">Completed · {total}</span>
        <ChevronDown
          size={14}
          className="ml-auto transition-transform duration-150"
          style={{ transform: open ? 'rotate(180deg)' : 'rotate(0deg)' }}
        />
      </button>

      {open && (
        <div className="mt-3 space-y-1">
          {tasks.map(task => {
            const assigneeName = resolveAssigneeName(task, members, currentUserId)
            return (
              <div
                key={task.id}
                className="flex items-center gap-3 rounded-lg px-1 py-2"
              >
                <div className="flex flex-1 flex-col min-w-0">
                  <span className="truncate text-sm line-through" style={{ color: 'var(--m-fg-3)' }}>
                    {task.name}
                  </span>
                  <div className="mt-0.5 flex flex-wrap items-center gap-1.5">
                    {task.assignee_type === 'all' && <Chip>🏠 Everyone</Chip>}
                    {task.assignee_type === 'specific' && <Chip>{assigneeName}</Chip>}
                  </div>
                </div>
                {task.completed_at && (
                  <span className="shrink-0 text-xs" style={{ color: 'var(--m-fg-4)' }}>
                    {completedLabel(task.completed_at)}
                  </span>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
