import './tasks.css'
import { useState } from 'react'
import { Plus, ClipboardList, Users } from 'lucide-react'
import { useTasks } from '@/hooks/useTasks'
import { useTasksRealtime } from '@/hooks/useTasksRealtime'
import { useHouseholdMembers } from '@/hooks/useHouseholdMembers'
import TaskItem from './TaskItem'
import TaskHistorySection from './TaskHistorySection'
import TaskForm from './TaskForm'
import type { Task, CreateTaskPayload, UpdateTaskPayload } from '@/types/tasks'

interface Props {
  householdId: string
  userId: string
}

export default function TasksTab({ householdId, userId }: Props) {
  const { list, loading, error, refetch, createTask, updateTask, completeTask, deleteTask } = useTasks()
  const { members } = useHouseholdMembers()
  const [editingTask, setEditingTask] = useState<Task | null>(null)
  const [showForm, setShowForm] = useState(false)

  useTasksRealtime(householdId, refetch)

  const handleOpenCreate = () => {
    setEditingTask(null)
    setShowForm(true)
  }

  const handleOpenEdit = (task: Task) => {
    setEditingTask(task)
    setShowForm(true)
  }

  const handleSave = async (payload: CreateTaskPayload | UpdateTaskPayload) => {
    if (editingTask) {
      await updateTask(editingTask.id, payload as UpdateTaskPayload)
    } else {
      await createTask(payload as CreateTaskPayload)
    }
  }

  return (
    <div className="rounded-xl min-h-[400px]" style={{ color: 'var(--m-fg)' }}>
      {/* header */}
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-widest" style={{ color: 'var(--m-fg-3)' }}>Chores</p>
        <div className="flex items-center gap-3">
          <p className="text-xs" style={{ color: 'var(--m-fg-3)' }}>
            {list.active_total} active
          </p>
          <button
            onClick={handleOpenCreate}
            className="flex items-center gap-1 rounded-lg px-2.5 py-1 text-xs font-medium transition-colors"
            style={{ background: 'var(--m-accent)', color: 'var(--m-accent-fg)' }}
          >
            <Plus size={13} strokeWidth={2.5} />
            Add
          </button>
        </div>
      </div>
      <div className="mt-1 flex items-center gap-1.5" style={{ color: 'var(--m-fg-3)' }}>
        <Users size={12} />
        <p className="text-xs">Shared with your household — changes sync live</p>
      </div>

      {/* error */}
      {error && <p className="mt-4 text-sm text-destructive">{error}</p>}

      {/* loading */}
      {loading && (
        <p className="mt-8 text-center text-sm" style={{ color: 'var(--m-fg-4)' }}>Loading…</p>
      )}

      {!loading && (
        <>
          {list.active.length === 0 ? (
            <EmptyState onAdd={handleOpenCreate} />
          ) : (
            <div className="mt-4 space-y-0.5">
              {list.active.map(task => (
                <TaskItem
                  key={task.id}
                  task={task}
                  members={members}
                  currentUserId={userId}
                  onComplete={completeTask}
                  onDelete={deleteTask}
                  onEdit={handleOpenEdit}
                />
              ))}
            </div>
          )}

          <TaskHistorySection
            tasks={list.history}
            total={list.history_total}
            members={members}
            currentUserId={userId}
          />
        </>
      )}

      {showForm && (
        <TaskForm
          task={editingTask}
          members={members}
          currentUserId={userId}
          onSave={handleSave}
          onClose={() => setShowForm(false)}
        />
      )}
    </div>
  )
}

function EmptyState({ onAdd }: { onAdd: () => void }) {
  return (
    <div
      className="mt-6 flex flex-col items-center gap-3 rounded-xl border border-dashed py-12 text-center"
      style={{ borderColor: 'var(--m-border)' }}
    >
      <ClipboardList size={28} style={{ color: 'var(--m-fg-4)' }} />
      <p className="text-sm" style={{ color: 'var(--m-fg-3)' }}>No chores yet</p>
      <button
        onClick={onAdd}
        className="text-xs font-medium transition-colors"
        style={{ color: 'var(--m-accent)' }}
      >
        Add the first one
      </button>
    </div>
  )
}
