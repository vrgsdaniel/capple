import { useState, useEffect, useCallback } from 'react'
import api from '@/lib/api'
import type { Task, TaskList, CreateTaskPayload, UpdateTaskPayload } from '@/types/tasks'

const EMPTY_LIST: TaskList = {
  active: [],
  history: [],
  active_total: 0,
  history_total: 0,
  page: 1,
  page_size: 20,
}

export function useTasks() {
  const [list, setList] = useState<TaskList>(EMPTY_LIST)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchTasks = useCallback(async () => {
    try {
      const res = await api.get<TaskList>('/api/tasks')
      setList(res.data)
      setError(null)
    } catch {
      setError('Could not load chores.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    api.get<TaskList>('/api/tasks')
      .then(res => { if (!cancelled) { setList(res.data); setError(null) } })
      .catch(() => { if (!cancelled) setError('Could not load chores.') })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [])

  const createTask = async (payload: CreateTaskPayload) => {
    await api.post<Task>('/api/tasks', payload)
    await fetchTasks()
  }

  const updateTask = async (taskId: string, payload: UpdateTaskPayload) => {
    await api.patch<Task>(`/api/tasks/${taskId}`, payload)
    await fetchTasks()
  }

  const completeTask = async (taskId: string) => {
    // optimistic: remove from active immediately
    setList(prev => ({
      ...prev,
      active: prev.active.filter(t => t.id !== taskId),
      active_total: prev.active_total - 1,
    }))
    try {
      await api.post<Task>(`/api/tasks/${taskId}/complete`)
      await fetchTasks()
    } catch {
      await fetchTasks() // revert
    }
  }

  const deleteTask = async (taskId: string) => {
    // optimistic: remove from active immediately
    setList(prev => ({
      ...prev,
      active: prev.active.filter(t => t.id !== taskId),
      active_total: prev.active_total - 1,
    }))
    try {
      await api.delete(`/api/tasks/${taskId}`)
    } catch {
      await fetchTasks() // revert
    }
  }

  return {
    list,
    loading,
    error,
    refetch: fetchTasks,
    createTask,
    updateTask,
    completeTask,
    deleteTask,
  }
}
