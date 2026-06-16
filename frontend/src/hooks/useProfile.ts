import { useState, useEffect } from 'react'
import api from '@/lib/api'

export interface Profile {
  id: string
  name: string
  avatar_url: string
}

export function useProfile() {
  const [profile, setProfile] = useState<Profile | null>(null)

  useEffect(() => {
    let cancelled = false
    api.get('/api/me')
      .then(res => { if (!cancelled) setProfile(res.data) })
      .catch(() => {})
    return () => { cancelled = true }
  }, [])

  return profile
}
