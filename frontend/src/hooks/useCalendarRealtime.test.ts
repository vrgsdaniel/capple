import { renderHook } from '@testing-library/react'
import { useCalendarRealtime } from '@/hooks/useCalendarRealtime'
import { supabase } from '@/lib/supabase'

jest.mock('@/lib/supabase', () => ({
  supabase: {
    channel: jest.fn(),
    removeChannel: jest.fn(),
  },
}))

const mockedSupabase = supabase as unknown as {
  channel: jest.Mock
  removeChannel: jest.Mock
}

describe('useCalendarRealtime', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('does not subscribe when householdId is empty', () => {
    const onUpdate = jest.fn()

    renderHook(() => useCalendarRealtime('', onUpdate))

    expect(mockedSupabase.channel).not.toHaveBeenCalled()
  })

  it('subscribes to calendar_events and calendar_birthdays changes', () => {
    const onUpdate = jest.fn()
    const handlers: Array<() => void> = []

    const channelToken = { id: 'channel-1' }
    const subscribe = jest.fn(() => channelToken)
    const chain: { on: jest.Mock; subscribe: typeof subscribe } = {
      on: jest.fn((...args: [string, object, () => void]) => {
        handlers.push(args[2])
        return chain
      }),
      subscribe,
    }
    mockedSupabase.channel.mockReturnValue(chain)

    const { unmount } = renderHook(() => useCalendarRealtime('home-123', onUpdate))

    expect(mockedSupabase.channel).toHaveBeenCalledWith('calendar-home-123')
    expect(chain.on).toHaveBeenCalledWith(
      'postgres_changes',
      { event: '*', schema: 'app', table: 'calendar_events', filter: 'household_id=eq.home-123' },
      expect.any(Function),
    )
    expect(chain.on).toHaveBeenCalledWith(
      'postgres_changes',
      { event: '*', schema: 'app', table: 'calendar_birthdays', filter: 'household_id=eq.home-123' },
      expect.any(Function),
    )
    expect(subscribe).toHaveBeenCalledTimes(1)

    handlers.forEach(h => h())
    expect(onUpdate).toHaveBeenCalledTimes(2)

    unmount()
    expect(mockedSupabase.removeChannel).toHaveBeenCalledWith(channelToken)
  })
})
