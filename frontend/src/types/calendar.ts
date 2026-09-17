export interface CalendarEvent {
  id: string
  household_id: string
  title: string
  event_date: string
  start_time: string | null
  end_time: string | null
  location: string | null
  description: string | null
  created_by: string
  created_at: string
  updated_at: string
}

export interface NativeCalendarFeedEvent extends CalendarEvent {
  source: 'native'
}

// Reserved for Phase 2 (Google Calendar read integration) — the backend feed does not emit
// any event with source: 'google' yet, but the client's union stays ready for it.
export interface GoogleCalendarFeedEvent {
  source: 'google'
  id: string
  user_id: string
  calendar_id: string
  title: string
  start: string
  end: string
}

export type CalendarFeedEvent = NativeCalendarFeedEvent | GoogleCalendarFeedEvent

export interface CreateEventPayload {
  title: string
  event_date: string
  start_time?: string | null
  end_time?: string | null
  location?: string | null
  description?: string | null
}

export interface UpdateEventPayload {
  title?: string
  event_date?: string
  start_time?: string | null
  end_time?: string | null
  location?: string | null
  description?: string | null
}

export interface Birthday {
  id: string
  household_id: string
  person_name: string
  birth_month: number
  birth_day: number
  birth_year: number | null
  show_year: boolean
  created_by: string
  created_at: string
  updated_at: string
}

export interface CreateBirthdayPayload {
  person_name: string
  birth_month: number
  birth_day: number
  birth_year?: number | null
  show_year?: boolean | null
}

export interface UpdateBirthdayPayload {
  person_name?: string
  birth_month?: number
  birth_day?: number
  birth_year?: number | null
  show_year?: boolean | null
}

export interface BirthdayOccurrence {
  id: string
  person_name: string
  birth_month: number
  birth_day: number
  birth_year: number | null
  occurrence_date: string
  age: number | null
  show_year: boolean
}

export interface ChoreDot {
  count: number
  titles: string[]
}

export interface CalendarFeed {
  events: CalendarFeedEvent[]
  birthdays: BirthdayOccurrence[]
  chore_dots: Record<string, ChoreDot>
  range_from: string
  range_to: string
}

export const EMPTY_CALENDAR_FEED: CalendarFeed = {
  events: [],
  birthdays: [],
  chore_dots: {},
  range_from: '',
  range_to: '',
}
