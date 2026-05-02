import { useAuth } from '@/hooks/useAuth'
import { useHousehold } from '@/hooks/useHousehold'
import { useEffect, useState } from 'react'
import api from '@/lib/api'
import { Button } from '@/components/ui/button'

interface Profile {
  id: string
  name: string
  avatar_url: string
}

export default function Dashboard() {
  const { signOut } = useAuth()
  const { household } = useHousehold()
  const [profile, setProfile] = useState<Profile | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.get('/api/me')
      .then(res => setProfile(res.data))
      .catch(() => setError('Could not reach the server. Is the backend running?'))
  }, [])

  return (
    <div className="flex min-h-svh items-center justify-center bg-background">
      <div className="text-center space-y-4">
        {error ? (
          <p className="text-destructive text-sm">{error}</p>
        ) : profile ? (
          <>
            {profile.avatar_url && (
              <img
                src={profile.avatar_url}
                alt="avatar"
                className="w-16 h-16 rounded-full mx-auto"
              />
            )}
            <h1 className="text-2xl font-semibold">
              Hello, {profile.name} 👋
            </h1>
            {household && (
              <p className="text-muted-foreground">{household.name}</p>
            )}
          </>
        ) : (
          <p className="text-muted-foreground">Loading profile...</p>
        )}
        <Button variant="outline" onClick={signOut}>
          Sign out
        </Button>
      </div>
    </div>
  )
}