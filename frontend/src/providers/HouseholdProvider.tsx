import { useState, useEffect } from 'react'
import axios from 'axios'
import api from '@/lib/api'
import { HouseholdContext, HouseholdConflictError, type Household } from '@/hooks/useHousehold'

export function HouseholdProvider({ children }: { children: React.ReactNode }) {
  const [household, setHousehold] = useState<Household | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    api.get('/api/households/me')
      .then(res => { if (!cancelled) setHousehold(res.data) })
      .catch((err: unknown) => {
        if (!cancelled && axios.isAxiosError(err) && err.response?.status === 404) setHousehold(null)
      })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [])

  const fetchHousehold = async () => {
    try {
      const res = await api.get('/api/households/me')
      setHousehold(res.data)
    } catch (err: unknown) {
      if (axios.isAxiosError(err) && err.response?.status === 404) {
        setHousehold(null)
      }
    } finally {
      setLoading(false)
    }
  }

  const createHousehold = async (name: string) => {
    try {
      await api.post('/api/households', { name })
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 409) {
        throw new HouseholdConflictError(err.response.data?.detail ?? 'You already belong to a household.')
      }
      throw err
    }
    await fetchHousehold()
  }

  const joinHousehold = async (inviteCode: string) => {
    try {
      await api.post('/api/households/join', { invite_code: inviteCode })
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 409) {
        throw new HouseholdConflictError(err.response.data?.detail ?? 'You already belong to a household.')
      }
      throw err
    }
    await fetchHousehold()
  }

  return (
    <HouseholdContext value={{ household, loading, refetch: fetchHousehold, createHousehold, joinHousehold }}>
      {children}
    </HouseholdContext>
  )
}
