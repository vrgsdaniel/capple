import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/hooks/useAuth'
import { useHousehold } from '@/hooks/useHousehold'
import type { Profile } from '@/hooks/useProfile'
import { ArrowLeft } from 'lucide-react'

interface Props {
  children: React.ReactNode
  backTo?: string
  profile: Profile | null
}

export function AppShell({ children, backTo, profile }: Props) {
  const { signOut } = useAuth()
  const { household } = useHousehold()

  return (
    <div className="min-h-svh bg-background">
      <div className="flex items-center justify-between px-6 py-4 border-b border-border">
        <div className="flex items-center gap-3">
          {backTo && (
            <Link to={backTo}>
              <Button variant="ghost" size="icon" className="h-8 w-8 mr-1">
                <ArrowLeft className="h-4 w-4" />
              </Button>
            </Link>
          )}
          {profile?.avatar_url && (
            <img
              src={profile.avatar_url}
              alt="avatar"
              className="w-8 h-8 rounded-full"
              referrerPolicy="no-referrer"
            />
          )}
          <div>
            <p className="text-sm font-medium">{profile?.name ?? '…'}</p>
            {household && (
              <p className="text-xs text-muted-foreground">{household.name}</p>
            )}
          </div>
        </div>
        <Button variant="ghost" size="sm" onClick={signOut}>Sign out</Button>
      </div>

      {children}
    </div>
  )
}
