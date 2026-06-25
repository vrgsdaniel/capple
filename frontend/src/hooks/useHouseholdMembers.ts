import { useEffect, useState } from 'react'
import api from '@/lib/api'
import type { HouseholdMembers } from '@/types/household'

let cachedMembers: HouseholdMembers | null = null
let hasCache = false
let inFlightRequest: Promise<HouseholdMembers | null> | null = null

async function fetchHouseholdMembers(): Promise<HouseholdMembers | null> {
  if (hasCache) return cachedMembers
  if (inFlightRequest) return inFlightRequest

  inFlightRequest = (async () => {
    try {
      const res = await api.get<HouseholdMembers>('/api/household/members')
      cachedMembers = res.data
      hasCache = true
      return res.data
    } catch {
      return null
    } finally {
      inFlightRequest = null
    }
  })()

  return inFlightRequest
}

export function __resetHouseholdMembersCacheForTests() {
  cachedMembers = null
  hasCache = false
  inFlightRequest = null
}

export function useHouseholdMembers(): { members: HouseholdMembers | null; loading: boolean } {
  const [members, setMembers] = useState<HouseholdMembers | null>(hasCache ? cachedMembers : null)
  const [loading, setLoading] = useState(!hasCache)

  useEffect(() => {
    let cancelled = false

    const run = async () => {
      const result = await fetchHouseholdMembers()
      if (cancelled) return
      setMembers(result)
      setLoading(false)
    }

    run()
    return () => { cancelled = true }
  }, [])

  return { members, loading }
}