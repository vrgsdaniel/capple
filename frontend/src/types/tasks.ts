export type AssigneeType = 'none' | 'specific' | 'all'
export type Frequency = 'daily' | 'weekly' | 'monthly'

export interface Task {
  id: string
  household_id: string
  name: string
  assignee_type: AssigneeType
  assignee_id: string | null
  due_date: string | null
  frequency: Frequency | null
  created_by: string
  created_at: string
  updated_at: string
  completed_at: string | null
}

export interface TaskList {
  active: Task[]
  history: Task[]
  active_total: number
  history_total: number
  page: number
  page_size: number
}

export interface CreateTaskPayload {
  name: string
  assignee_type: AssigneeType
  assignee_id?: string | null
  due_date?: string | null
  frequency?: Frequency | null
}

export interface UpdateTaskPayload {
  name?: string
  assignee_type?: AssigneeType
  assignee_id?: string | null
  due_date?: string | null
  frequency?: Frequency | null
}
