import { renderHook, waitFor } from '@testing-library/react'
import api from '@/lib/api'
import { useCalendar } from '@/hooks/useCalendar'
import type { CalendarFeed } from '@/types/calendar'

jest.mock('@/lib/api', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
    patch: jest.fn(),
    delete: jest.fn(),
  },
}))

const mockedApi = api as unknown as {
  get: jest.Mock
  post: jest.Mock
  patch: jest.Mock
  delete: jest.Mock
}

function makeFeed(): CalendarFeed {
  return {
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
    birthdays: [],
    chore_dots: {},
    range_from: '2026-09-01',
    range_to: '2026-09-30',
  }
}

describe('useCalendar', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('loads the feed for the given range', async () => {
    const feed = makeFeed()
    mockedApi.get.mockResolvedValue({ data: feed })

    const { result } = renderHook(() => useCalendar('2026-09-01', '2026-09-30'))

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.feed).toEqual(feed)
    expect(mockedApi.get).toHaveBeenCalledWith('/api/calendar/events', {
      params: { from: '2026-09-01', to: '2026-09-30' },
    })
  })

  it('sets an error when the fetch fails', async () => {
    mockedApi.get.mockRejectedValue(new Error('network fail'))

    const { result } = renderHook(() => useCalendar('2026-09-01', '2026-09-30'))

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.error).toBe('Could not load the calendar.')
  })

  it('refetches after creating an event', async () => {
    const feed = makeFeed()
    mockedApi.get.mockResolvedValue({ data: feed })
    mockedApi.post.mockResolvedValue({ data: {} })

    const { result } = renderHook(() => useCalendar('2026-09-01', '2026-09-30'))

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    await result.current.createEvent({ title: 'Trip', event_date: '2026-09-25' })

    expect(mockedApi.post).toHaveBeenCalledWith('/api/calendar/events', {
      title: 'Trip',
      event_date: '2026-09-25',
    })
    expect(mockedApi.get).toHaveBeenCalledTimes(2)
  })
})
