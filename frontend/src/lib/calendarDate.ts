// Event dates are naive "YYYY-MM-DD" strings with no timezone (see feature-plan-calendar.md
// §0). Always build/read them from local Y/M/D components — never round-trip through
// `new Date('YYYY-MM-DD')`, which parses as UTC and can shift a day off in the browser's
// local timezone.

export function toISODate(year: number, month: number, day: number): string {
  const mm = String(month).padStart(2, '0')
  const dd = String(day).padStart(2, '0')
  return `${year}-${mm}-${dd}`
}

export function todayISODate(): string {
  const now = new Date()
  return toISODate(now.getFullYear(), now.getMonth() + 1, now.getDate())
}

export function parseISODate(iso: string): { year: number; month: number; day: number } {
  const [year, month, day] = iso.split('-').map(Number)
  return { year, month, day }
}

export function addDays(iso: string, delta: number): string {
  const { year, month, day } = parseISODate(iso)
  const d = new Date(year, month - 1, day + delta)
  return toISODate(d.getFullYear(), d.getMonth() + 1, d.getDate())
}

export function addMonths(year: number, month: number, delta: number): { year: number; month: number } {
  const total = (year * 12 + (month - 1)) + delta
  return { year: Math.floor(total / 12), month: (((total % 12) + 12) % 12) + 1 }
}

export function monthLabel(year: number, month: number): string {
  return new Date(year, month - 1, 1).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
}

export interface MonthGridDay {
  iso: string
  day: number
  inCurrentMonth: boolean
}

/** 42-cell grid (6 weeks, Sunday-first) covering the given month plus lead/trail days. */
export function getMonthGridDays(year: number, month: number): MonthGridDay[] {
  const firstOfMonth = new Date(year, month - 1, 1)
  const startWeekday = firstOfMonth.getDay()
  const daysInMonth = new Date(year, month, 0).getDate()
  const { year: prevYear, month: prevMonth } = addMonths(year, month, -1)
  const daysInPrevMonth = new Date(prevYear, prevMonth, 0).getDate()

  const days: MonthGridDay[] = []

  for (let i = startWeekday - 1; i >= 0; i--) {
    const day = daysInPrevMonth - i
    days.push({ iso: toISODate(prevYear, prevMonth, day), day, inCurrentMonth: false })
  }

  for (let day = 1; day <= daysInMonth; day++) {
    days.push({ iso: toISODate(year, month, day), day, inCurrentMonth: true })
  }

  const { year: nextYear, month: nextMonth } = addMonths(year, month, 1)
  let nextDay = 1
  while (days.length < 42) {
    days.push({ iso: toISODate(nextYear, nextMonth, nextDay), day: nextDay, inCurrentMonth: false })
    nextDay++
  }

  return days
}

export function formatMonthDay(iso: string): string {
  const { year, month, day } = parseISODate(iso)
  return new Date(year, month - 1, day).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

export function formatWeekdayMonthDay(iso: string): string {
  const { year, month, day } = parseISODate(iso)
  return new Date(year, month - 1, day).toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  })
}

export function formatTime(time: string | null): string | null {
  if (!time) return null
  const [h, m] = time.split(':').map(Number)
  return new Date(2000, 0, 1, h, m).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
}
