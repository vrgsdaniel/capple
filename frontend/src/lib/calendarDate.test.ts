import { addDays, addMonths, getMonthGridDays, toISODate } from '@/lib/calendarDate'

describe('calendarDate', () => {
  it('builds an ISO date from local components', () => {
    expect(toISODate(2026, 9, 5)).toBe('2026-09-05')
  })

  it('wraps months across year boundaries', () => {
    expect(addMonths(2026, 12, 1)).toEqual({ year: 2027, month: 1 })
    expect(addMonths(2026, 1, -1)).toEqual({ year: 2025, month: 12 })
  })

  it('adds days across month boundaries', () => {
    expect(addDays('2026-09-28', 5)).toBe('2026-10-03')
  })

  it('produces a 42-day grid starting on Sunday and covering the whole month', () => {
    const days = getMonthGridDays(2026, 9)
    expect(days).toHaveLength(42)
    const inMonth = days.filter(d => d.inCurrentMonth)
    expect(inMonth).toHaveLength(30)
    expect(inMonth[0].iso).toBe('2026-09-01')
    expect(inMonth[inMonth.length - 1].iso).toBe('2026-09-30')
  })
})
