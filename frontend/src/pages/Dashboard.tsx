import { useAuth } from '@/hooks/useAuth'
import { useHousehold } from '@/hooks/useHousehold'
import { useEffect, useState } from 'react'
import api from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import BatteryTab from '@/components/battery/BatteryTab'
import MealsTab from '@/components/meals/MealsTab'
import ChatDrawer from '@/components/chat/ChatDrawer'

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
    <div className="min-h-svh bg-background">
      {/* top bar */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-border">
        <div className="flex items-center gap-3">
          {profile?.avatar_url && (
            <img src={profile.avatar_url} alt="avatar"
              className="w-8 h-8 rounded-full"/>
          )}
          <div>
            <p className="text-sm font-medium">{profile?.name ?? '...'}</p>
            {household && (
              <p className="text-xs text-muted-foreground">{household.name}</p>
            )}
          </div>
        </div>
        <Button variant="ghost" size="sm" onClick={signOut}>Sign out</Button>
      </div>

      {error && (
        <p className="text-destructive text-sm text-center mt-8">{error}</p>
      )}

      {/* tabs */}
      <div className="max-w-3xl mx-auto px-4 py-6">
        <Tabs defaultValue="battery">
          <TabsList className="mb-6">
            <TabsTrigger value="battery">⚡ Battery</TabsTrigger>
            <TabsTrigger value="meals">🍽 Meals</TabsTrigger>
            <TabsTrigger value="activities" disabled>📅 Activities</TabsTrigger>
          </TabsList>

          <TabsContent value="battery">
            {profile && household && (
              <BatteryTab
                userId={profile.id}
                userName={profile.name}
                householdId={household.id}
              />
            )}
          </TabsContent>

          <TabsContent value="meals">
            <MealsTab />
          </TabsContent>
        </Tabs>
      </div>
      <ChatDrawer />
    </div>
  )
}