import { createContext, useContext } from 'react'

export interface Household {
  id: string
  name: string
  invite_code: string
  role: string
}

export interface HouseholdContextValue {
  household: Household | null
  loading: boolean
  refetch: () => Promise<void>
  createHousehold: (name: string) => Promise<void>
  joinHousehold: (inviteCode: string) => Promise<void>
}

export const HouseholdContext = createContext<HouseholdContextValue | null>(null)

export function useHousehold() {
  const ctx = useContext(HouseholdContext)
  if (!ctx) throw new Error('useHousehold must be used within HouseholdProvider')
  return ctx
}