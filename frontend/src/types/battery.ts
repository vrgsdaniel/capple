export interface BatteryLog {
  id: string
  user_id: string
  household_id: string
  level: number
  note: string | null
  effective_at: string
  logged_at: string
}

export interface DailyAverage {
  date: string
  avg: number
}