import { renderHook } from '@testing-library/react'
import { useBatteryRealtime } from '@/hooks/useBatteryRealtime'
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

describe('useBatteryRealtime', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('does not subscribe when householdId is empty', () => {
    const onUpdate = jest.fn()

    renderHook(() => useBatteryRealtime('', onUpdate))

    expect(mockedSupabase.channel).not.toHaveBeenCalled()
    expect(mockedSupabase.removeChannel).not.toHaveBeenCalled()
  })

  it('subscribes to battery_logs changes and invokes onUpdate', () => {
    const onUpdate = jest.fn()
    let realtimeHandler: (() => void) | undefined

    const channelToken = { id: 'channel-1' }
    const subscribe = jest.fn(() => channelToken)
    const on = jest.fn((...args: [string, object, () => void]) => {
      realtimeHandler = args[2]
      return { subscribe }
    })

    mockedSupabase.channel.mockReturnValue({ on })

    const { unmount } = renderHook(() => useBatteryRealtime('home-123', onUpdate))

    expect(mockedSupabase.channel).toHaveBeenCalledWith('battery-home-123')
    expect(on).toHaveBeenCalledWith(
      'postgres_changes',
      {
        event: '*',
        schema: 'public',
        table: 'battery_logs',
        filter: 'household_id=eq.home-123',
      },
      expect.any(Function),
    )
    expect(subscribe).toHaveBeenCalledTimes(1)

    expect(realtimeHandler).toBeDefined()
    realtimeHandler?.()
    expect(onUpdate).toHaveBeenCalledTimes(1)

    unmount()
    expect(mockedSupabase.removeChannel).toHaveBeenCalledWith(channelToken)
  })

  it('removes previous channel when householdId changes', () => {
    const onUpdate = jest.fn()

    const firstChannelToken = { id: 'channel-1' }
    const secondChannelToken = { id: 'channel-2' }

    const firstOn = jest.fn(() => ({
      subscribe: jest.fn(() => firstChannelToken),
    }))

    const secondOn = jest.fn(() => ({
      subscribe: jest.fn(() => secondChannelToken),
    }))

    mockedSupabase.channel
      .mockReturnValueOnce({ on: firstOn })
      .mockReturnValueOnce({ on: secondOn })

    const { rerender, unmount } = renderHook(
      ({ householdId }) => useBatteryRealtime(householdId, onUpdate),
      { initialProps: { householdId: 'home-1' } },
    )

    rerender({ householdId: 'home-2' })

    expect(mockedSupabase.removeChannel).toHaveBeenCalledWith(firstChannelToken)

    unmount()
    expect(mockedSupabase.removeChannel).toHaveBeenCalledWith(secondChannelToken)
    expect(mockedSupabase.removeChannel).toHaveBeenCalledTimes(2)
  })
})
