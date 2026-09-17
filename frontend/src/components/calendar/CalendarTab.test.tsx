import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import CalendarTab from './CalendarTab'
import { useCalendar } from '@/hooks/useCalendar'
import { useCalendarRealtime } from '@/hooks/useCalendarRealtime'
import type { CalendarFeed } from '@/types/calendar'

jest.mock('@/hooks/useCalendar', () => ({
  useCalendar: jest.fn(),
}))

jest.mock('@/hooks/useCalendarRealtime', () => ({
  useCalendarRealtime: jest.fn(),
}))

const mockedUseCalendar = useCalendar as jest.MockedFunction<typeof useCalendar>
const mockedUseCalendarRealtime = useCalendarRealtime as jest.MockedFunction<typeof useCalendarRealtime>

function makeFeed(overrides: Partial<CalendarFeed> = {}): CalendarFeed {
  return {
    events: [],
    birthdays: [],
    chore_dots: {},
    range_from: '2026-09-01',
    range_to: '2026-10-12',
    ...overrides,
  }
}

function makeCalendarApi(feed: CalendarFeed) {
  return {
    feed,
    loading: false,
    error: null,
    refetch: jest.fn(),
    createEvent: jest.fn().mockResolvedValue(undefined),
    updateEvent: jest.fn().mockResolvedValue(undefined),
    deleteEvent: jest.fn().mockResolvedValue(undefined),
    createBirthday: jest.fn().mockResolvedValue(undefined),
    updateBirthday: jest.fn().mockResolvedValue(undefined),
    deleteBirthday: jest.fn().mockResolvedValue(undefined),
  }
}

describe('CalendarTab', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedUseCalendarRealtime.mockImplementation(() => undefined)
  })

  it('renders the month grid by default and switches to the agenda view', () => {
    const api = makeCalendarApi(makeFeed())
    mockedUseCalendar.mockReturnValue(api)

    render(<CalendarTab householdId="household-1" />)

    expect(screen.getByText('Month')).toBeInTheDocument()
    expect(screen.getByText('Agenda')).toBeInTheDocument()

    fireEvent.click(screen.getByText('Agenda'))
    expect(screen.getByText('Nothing coming up')).toBeInTheDocument()
  })

  it('creates a new event through the floating add button', async () => {
    const api = makeCalendarApi(makeFeed())
    mockedUseCalendar.mockReturnValue(api)

    render(<CalendarTab householdId="household-1" />)

    fireEvent.click(screen.getByLabelText('Add event'))
    expect(screen.getByText('New Event')).toBeInTheDocument()

    fireEvent.change(screen.getByPlaceholderText('e.g. Dentist appointment'), {
      target: { value: 'Dentist' },
    })
    fireEvent.click(screen.getByText('Add Event'))

    await waitFor(() => {
      expect(api.createEvent).toHaveBeenCalledWith(
        expect.objectContaining({ title: 'Dentist' }),
      )
    })
  })

  it('opens the day-detail sheet for a day with an event and can edit/delete it', async () => {
    const feed = makeFeed({
      events: [
        {
          source: 'native',
          id: 'event-1',
          household_id: 'household-1',
          title: 'Dentist',
          event_date: '2026-09-20',
          start_time: '10:00:00',
          end_time: null,
          location: null,
          description: null,
          created_by: 'user-1',
          created_at: '2026-09-01T00:00:00Z',
          updated_at: '2026-09-01T00:00:00Z',
        },
      ],
    })
    const api = makeCalendarApi(feed)
    mockedUseCalendar.mockReturnValue(api)

    // Freeze "today" so the month grid renders September 2026, matching the fixture's dates.
    jest.useFakeTimers().setSystemTime(new Date(2026, 8, 15))

    render(<CalendarTab householdId="household-1" />)

    fireEvent.click(screen.getByText('20'))
    expect(screen.getAllByText('Dentist').length).toBeGreaterThan(0)

    fireEvent.click(screen.getByLabelText('Delete event'))
    await waitFor(() => {
      expect(api.deleteEvent).toHaveBeenCalledWith('event-1')
    })

    jest.useRealTimers()
  })
})
