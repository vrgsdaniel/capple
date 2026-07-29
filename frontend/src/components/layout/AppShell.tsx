import { Link, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator } from '@/components/ui/dropdown-menu'
import { useAuth } from '@/hooks/useAuth'
import { useHousehold } from '@/hooks/useHousehold'
import type { Profile } from '@/hooks/useProfile'
import { ArrowLeft, Settings, Home, User, LogOut } from 'lucide-react'

interface Props {
  children: React.ReactNode
  backTo?: string
  profile: Profile | null
}

export function AppShell({ children, backTo, profile }: Props) {
  const { signOut } = useAuth()
  const { household } = useHousehold()
  const navigate = useNavigate()

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

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="flex items-center gap-3 rounded-lg px-1 py-0.5 hover:bg-muted transition-colors outline-none focus-visible:ring-2 focus-visible:ring-ring">
                {profile?.avatar_url ? (
                  <img
                    src={profile.avatar_url}
                    alt="avatar"
                    className="w-8 h-8 rounded-full"
                    referrerPolicy="no-referrer"
                  />
                ) : (
                  <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center text-sm font-medium">
                    {profile?.name?.[0]?.toUpperCase() ?? '?'}
                  </div>
                )}
                <div className="text-left">
                  <p className="text-sm font-medium leading-none">{profile?.name ?? '…'}</p>
                  {household && (
                    <p className="text-xs text-muted-foreground mt-0.5">{household.name}</p>
                  )}
                </div>
              </button>
            </DropdownMenuTrigger>

            <DropdownMenuContent align="start">
              <DropdownMenuItem disabled className="gap-2 opacity-40 cursor-default">
                <Settings className="w-4 h-4" />
                Settings
                <span className="ml-auto text-xs text-muted-foreground">soon</span>
              </DropdownMenuItem>
              <DropdownMenuItem onSelect={() => navigate('/household')} className="gap-2">
                <Home className="w-4 h-4" />
                Household
              </DropdownMenuItem>
              <DropdownMenuItem onSelect={() => navigate('/account')} className="gap-2">
                <User className="w-4 h-4" />
                Account
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onSelect={signOut} className="gap-2 text-destructive focus:text-destructive">
                <LogOut className="w-4 h-4" />
                Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {children}
    </div>
  )
}
