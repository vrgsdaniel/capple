import { useState, useEffect, useCallback } from 'react'
import api from '@/lib/api'
import type {
  CalendarFeed,
  CalendarEvent,
  Birthday,
  CreateEventPayload,
  UpdateEventPayload,
  CreateBirthdayPayload,
  UpdateBirthdayPayload,
} from '@/types/calendar'
import { EMPTY_CALENDAR_FEED } from '@/types/calendar'

export function useCalendar(from: string, to: string) {
  const [feed, setFeed] = useState<CalendarFeed>(EMPTY_CALENDAR_FEED)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Loading only guards the very first fetch — switching month/view keeps the current feed
  // on screen until the new range resolves, rather than flashing a loading state.
  const fetchFeed = useCallback(async (cancelledRef?: { current: boolean }) => {
    try {
      const res = await api.get<CalendarFeed>('/api/calendar/events', { params: { from, to } })
      if (!cancelledRef?.current) { setFeed(res.data); setError(null) }
    } catch {
      if (!cancelledRef?.current) setError('Could not load the calendar.')
    } finally {
      if (!cancelledRef?.current) setLoading(false)
    }
  }, [from, to])

  useEffect(() => {
    const cancelledRef = { current: false }
    fetchFeed(cancelledRef)
    return () => { cancelledRef.current = true }
  }, [fetchFeed])

  const createEvent = async (payload: CreateEventPayload) => {
    await api.post<CalendarEvent>('/api/calendar/events', payload)
    await fetchFeed()
  }

  const updateEvent = async (eventId: string, payload: UpdateEventPayload) => {
    await api.patch<CalendarEvent>(`/api/calendar/events/${eventId}`, payload)
    await fetchFeed()
  }

  const deleteEvent = async (eventId: string) => {
    await api.delete(`/api/calendar/events/${eventId}`)
    await fetchFeed()
  }

  const createBirthday = async (payload: CreateBirthdayPayload) => {
    await api.post<Birthday>('/api/calendar/birthdays', payload)
    await fetchFeed()
  }

  const updateBirthday = async (birthdayId: string, payload: UpdateBirthdayPayload) => {
    await api.patch<Birthday>(`/api/calendar/birthdays/${birthdayId}`, payload)
    await fetchFeed()
  }

  const deleteBirthday = async (birthdayId: string) => {
    await api.delete(`/api/calendar/birthdays/${birthdayId}`)
    await fetchFeed()
  }

  return {
    feed,
    loading,
    error,
    refetch: fetchFeed,
    createEvent,
    updateEvent,
    deleteEvent,
    createBirthday,
    updateBirthday,
    deleteBirthday,
  }
}
