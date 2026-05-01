import { createContext, useContext, useState, useEffect } from 'react'
import api from '@/lib/api'

interface Household {
  id: string
  name: string
  invite_code: string
  role: string
}

interface HouseholdContextValue {
  household: Household | null
  loading: boolean
  refetch: () => Promise<void>
  createHousehold: (name: string) => Promise<void>
  joinHousehold: (inviteCode: string) => Promise<void>
}

const HouseholdContext = createContext<HouseholdContextValue | null>(null)

export function HouseholdProvider({ children }: { children: React.ReactNode }) {
  const [household, setHousehold] = useState<Household | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchHousehold = async () => {
    try {
      const res = await api.get('/api/households/me')
      setHousehold(res.data)
    } catch (err: any) {
      if (err.response?.status === 404) {
        setHousehold(null)
      }
    } finally {
      setLoading(false)
    }
  }

  const createHousehold = async (name: string) => {
    await api.post('/api/households', { name })
    await fetchHousehold()
  }

  const joinHousehold = async (inviteCode: string) => {
    await api.post('/api/households/join', { invite_code: inviteCode })
    await fetchHousehold()
  }

  useEffect(() => {
    fetchHousehold()
  }, [])

  return (
    <HouseholdContext value={{ household, loading, refetch: fetchHousehold, createHousehold, joinHousehold }}>
      {children}
    </HouseholdContext>
  )
}

export function useHousehold() {
  const ctx = useContext(HouseholdContext)
  if (!ctx) throw new Error('useHousehold must be used within HouseholdProvider')
  return ctx
}