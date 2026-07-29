import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import { useAuth } from '@/hooks/useAuth'
import { useHousehold } from '@/hooks/useHousehold'
import { useProfile } from '@/hooks/useProfile'
import { AppShell } from '@/components/layout/AppShell'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  AlertDialog,
  AlertDialogTrigger,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogFooter,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogAction,
  AlertDialogCancel,
} from '@/components/ui/alert-dialog'
import api from '@/lib/api'

export default function AccountPage() {
  const profile = useProfile()
  const { user, signOut } = useAuth()
  const { household } = useHousehold()
  const navigate = useNavigate()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const isOwner = household?.role === 'owner'

  const handleDeleteAccount = async () => {
    setBusy(true)
    setError(null)
    try {
      await api.delete('/api/me')
      await signOut()
      navigate('/login', { replace: true })
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 409) {
        setError('You must delete your household before deleting your account.')
      } else {
        setError('Something went wrong. Please try again.')
      }
    } finally {
      setBusy(false)
    }
  }

  return (
    <AppShell profile={profile} backTo="/">
      <div className="max-w-2xl mx-auto px-6 py-8 flex flex-col gap-6">
        <h1 className="text-2xl font-semibold">Account</h1>

        {/* Profile info */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">Profile</CardTitle>
          </CardHeader>
          <CardContent className="flex items-center gap-4 pt-0">
            {profile?.avatar_url ? (
              <img
                src={profile.avatar_url}
                alt="avatar"
                className="w-14 h-14 rounded-full"
                referrerPolicy="no-referrer"
              />
            ) : (
              <div className="w-14 h-14 rounded-full bg-muted flex items-center justify-center text-lg font-medium">
                {profile?.name?.[0]?.toUpperCase() ?? '?'}
              </div>
            )}
            <div className="flex flex-col gap-0.5">
              <p className="font-medium">{profile?.name ?? '…'}</p>
              <p className="text-sm text-muted-foreground">{user?.email ?? '…'}</p>
            </div>
          </CardContent>
        </Card>

        {/* Danger zone */}
        <div className="rounded-xl border border-destructive/30 p-5 flex flex-col gap-4">
          <p className="text-sm font-medium text-destructive">Danger zone</p>

          {isOwner && (
            <p className="text-sm text-muted-foreground">
              You own a household. You must{' '}
              <button
                className="underline text-foreground"
                onClick={() => navigate('/household')}
              >
                delete your household
              </button>{' '}
              before you can delete your account.
            </p>
          )}

          {error && <p className="text-sm text-destructive">{error}</p>}

          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="destructive" disabled={busy}>
                Delete account
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Delete your account?</AlertDialogTitle>
                <AlertDialogDescription>
                  This is permanent and cannot be undone. All your data will be deleted.
                  {isOwner && (
                    <span className="mt-2 block font-medium text-destructive">
                      You must delete your household first.
                    </span>
                  )}
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction
                  className="bg-destructive text-white hover:bg-destructive/90"
                  onClick={handleDeleteAccount}
                  disabled={busy}
                >
                  Delete account
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </div>
    </AppShell>
  )
}
