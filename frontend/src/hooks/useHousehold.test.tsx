import { renderHook } from '@testing-library/react'
import type { ReactNode } from 'react'
import {
  HouseholdContext,
  useHousehold,
  type Household,
  type HouseholdContextValue,
} from '@/hooks/useHousehold'

describe('useHousehold', () => {
  it('throws when used outside HouseholdProvider', () => {
    expect(() => renderHook(() => useHousehold())).toThrow(
      'useHousehold must be used within HouseholdProvider',
    )
  })

  it('returns context value when used inside HouseholdContext.Provider', () => {
    const household: Household = {
      id: 'home-1',
      name: 'Home',
      invite_code: 'INV123',
      role: 'owner',
    }

    const value: HouseholdContextValue = {
      household,
      loading: false,
      refetch: jest.fn(async () => undefined),
      createHousehold: jest.fn(async () => undefined),
      joinHousehold: jest.fn(async () => undefined),
    }

    function Wrapper({ children }: { children: ReactNode }) {
      return <HouseholdContext.Provider value={value}>{children}</HouseholdContext.Provider>
    }

    const { result } = renderHook(() => useHousehold(), { wrapper: Wrapper })

    expect(result.current).toBe(value)
  })
})
