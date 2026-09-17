import type { CalendarFeed, NativeCalendarFeedEvent, BirthdayOccurrence, ChoreDot } from '@/types/calendar'

export interface DayItems {
  events: NativeCalendarFeedEvent[]
  birthdays: BirthdayOccurrence[]
  choreDot?: ChoreDot
}

/** Groups a feed's events/birthdays/chore_dots by their ISO date, for month-grid and agenda rendering. */
export function groupFeedByDate(feed: CalendarFeed): Record<string, DayItems> {
  // A null-prototype object so a feed date string can never resolve to Object.prototype
  // members (e.g. "__proto__", "constructor") when used as a key.
  const byDate: Record<string, DayItems> = Object.create(null)

  const get = (iso: string): DayItems => {
    if (!byDate[iso]) byDate[iso] = { events: [], birthdays: [] }
    return byDate[iso]
  }

  for (const event of feed.events) {
    if (event.source !== 'native') continue
    get(event.event_date).events.push(event)
  }

  for (const birthday of feed.birthdays) {
    get(birthday.occurrence_date).birthdays.push(birthday)
  }

  for (const [iso, dot] of Object.entries(feed.chore_dots)) {
    get(iso).choreDot = dot
  }

  return byDate
}
