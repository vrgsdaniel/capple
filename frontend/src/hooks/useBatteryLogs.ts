import { useState, useEffect, useCallback } from 'react'
import api from '@/lib/api'
import type { BatteryLog, DailyAverage } from '@/types/battery'

function getRangeStart(range: '7d' | '30d' | '12m'): Date {
  const d = new Date()
  if (range === '7d')  d.setDate(d.getDate() - 7)
  if (range === '30d') d.setDate(d.getDate() - 30)
  if (range === '12m') d.setMonth(d.getMonth() - 12)
  return d
}

export function useBatteryLogs(range: '7d' | '30d' | '12m') {
  const [logs, setLogs] = useState<BatteryLog[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchLogs = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const start = getRangeStart(range)
      const end = new Date()
      const res = await api.get('/api/battery-logs', {
        params: {
          start: start.toISOString(),
          end: end.toISOString(),
        }
      })
      setLogs(res.data)
    } catch {
      setError('Could not load battery logs.')
    } finally {
      setLoading(false)
    }
  }, [range])

  useEffect(() => {
    let cancelled = false
    const run = async () => {
      setLoading(true)
      setError(null)
      try {
        const start = getRangeStart(range)
        const end = new Date()
        const res = await api.get('/api/battery-logs', {
          params: {
            start: start.toISOString(),
            end: end.toISOString(),
          }
        })
        if (!cancelled) setLogs(res.data)
      } catch {
        if (!cancelled) setError('Could not load battery logs.')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    run()
    return () => { cancelled = true }
  }, [range])

  return { logs, loading, error, refetch: fetchLogs }
}

// Group logs by user and compute daily averages
export function toDailyAverages(
  logs: BatteryLog[],
  userId: string
): { you: DailyAverage[], partner: DailyAverage[] } {
  const byUser: Record<string, Record<string, number[]>> = {}

  for (const log of logs) {
    const day = log.effective_at.split('T')[0]
    if (!byUser[log.user_id]) byUser[log.user_id] = {}
    if (!byUser[log.user_id][day]) byUser[log.user_id][day] = []
    byUser[log.user_id][day].push(log.level)
  }

  const toAvg = (userLogs: Record<string, number[]>): DailyAverage[] =>
    Object.entries(userLogs)
      .map(([date, levels]) => ({
        date,
        avg: Math.round(levels.reduce((a, b) => a + b, 0) / levels.length)
      }))
      .sort((a, b) => a.date.localeCompare(b.date))

  const userIds = Object.keys(byUser)
  const partnerId = userIds.find(id => id !== userId) ?? ''

  return {
    you: byUser[userId] ? toAvg(byUser[userId]) : [],
    partner: partnerId && byUser[partnerId] ? toAvg(byUser[partnerId]) : [],
  }
}