import { act, renderHook, waitFor } from '@testing-library/react'
import api from '@/lib/api'
import { useBatteryLogs } from '@/hooks/useBatteryLogs'
import type { BatteryLog } from '@/types/battery'

jest.mock('@/lib/api', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
  },
}))

const mockedApi = api as unknown as {
  get: jest.Mock<Promise<{ data: BatteryLog[] }>>
}

function makeLog(overrides?: Partial<BatteryLog>): BatteryLog {
  return {
    id: 'log-1',
    user_id: 'user-1',
    household_id: 'home-1',
    level: 78,
    note: null,
    effective_at: '2026-05-25T10:00:00.000Z',
    logged_at: '2026-05-25T10:00:00.000Z',
    ...overrides,
  }
}

describe('useBatteryLogs', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('loads logs on mount', async () => {
    const logs = [makeLog()]
    mockedApi.get.mockResolvedValue({ data: logs })

    const { result } = renderHook(() => useBatteryLogs('7d'))

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.error).toBeNull()
    expect(result.current.logs).toEqual(logs)
    expect(mockedApi.get).toHaveBeenCalledWith(
      '/api/battery-logs',
      expect.objectContaining({
        params: expect.objectContaining({
          start: expect.any(String),
          end: expect.any(String),
        }),
      }),
    )
  })

  it('sets error when load fails', async () => {
    mockedApi.get.mockRejectedValue(new Error('network fail'))

    const { result } = renderHook(() => useBatteryLogs('30d'))

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.logs).toEqual([])
    expect(result.current.error).toBe('Could not load battery logs.')
  })

  it('refetches logs when refetch is called', async () => {
    mockedApi.get
      .mockResolvedValueOnce({ data: [makeLog({ id: 'log-1', level: 50 })] })
      .mockResolvedValueOnce({ data: [makeLog({ id: 'log-2', level: 90 })] })

    const { result } = renderHook(() => useBatteryLogs('7d'))

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.logs).toEqual([makeLog({ id: 'log-1', level: 50 })])

    await act(async () => {
      await result.current.refetch()
    })

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.logs).toEqual([makeLog({ id: 'log-2', level: 90 })])
    expect(mockedApi.get).toHaveBeenCalledTimes(2)
  })

  it('refetches when range changes', async () => {
    type Range = '7d' | '30d' | '12m'

    mockedApi.get
      .mockResolvedValueOnce({ data: [makeLog({ id: 'first' })] })
      .mockResolvedValueOnce({ data: [makeLog({ id: 'second' })] })

    const { result, rerender } = renderHook(
      ({ range }: { range: Range }) => useBatteryLogs(range),
      { initialProps: { range: '7d' } },
    )

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    rerender({ range: '30d' })

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.logs).toEqual([makeLog({ id: 'second' })])
    expect(mockedApi.get).toHaveBeenCalledTimes(2)
  })
})
