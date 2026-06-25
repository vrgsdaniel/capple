import { renderHook, waitFor } from '@testing-library/react'
import api from '@/lib/api'
import { __resetHouseholdMembersCacheForTests, useHouseholdMembers } from '@/hooks/useHouseholdMembers'
import type { HouseholdMembers } from '@/types/household'

jest.mock('@/lib/api', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
  },
}))

const mockedApi = api as unknown as {
  get: jest.Mock<Promise<{ data: HouseholdMembers }>>
}

function makeMembers(): HouseholdMembers {
  return {
    me: {
      id: 'user-1',
      name: 'Daniel',
      avatar_url: null,
    },
    others: [
      {
        id: 'user-2',
        name: 'Laura',
        avatar_url: 'https://example.com/avatar.png',
      },
    ],
  }
}

describe('useHouseholdMembers', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    __resetHouseholdMembersCacheForTests()
  })

  it('loads members on mount', async () => {
    const members = makeMembers()
    mockedApi.get.mockResolvedValue({ data: members })

    const { result } = renderHook(() => useHouseholdMembers())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.members).toEqual(members)
    expect(mockedApi.get).toHaveBeenCalledWith('/api/household/members')
  })

  it('returns null members when fetch fails', async () => {
    mockedApi.get.mockRejectedValue(new Error('network fail'))

    const { result } = renderHook(() => useHouseholdMembers())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.members).toBeNull()
  })

  it('uses cached members for subsequent mounts', async () => {
    const members = makeMembers()
    mockedApi.get.mockResolvedValue({ data: members })

    const first = renderHook(() => useHouseholdMembers())

    await waitFor(() => {
      expect(first.result.current.loading).toBe(false)
    })

    expect(first.result.current.members).toEqual(members)
    expect(mockedApi.get).toHaveBeenCalledTimes(1)

    const second = renderHook(() => useHouseholdMembers())

    expect(second.result.current.loading).toBe(false)
    expect(second.result.current.members).toEqual(members)
    expect(mockedApi.get).toHaveBeenCalledTimes(1)
  })
})