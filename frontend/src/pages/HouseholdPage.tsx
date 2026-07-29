import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Copy, Check, Home, Users, Key } from 'lucide-react'
import axios from 'axios'
import { useHousehold, HouseholdConflictError } from '@/hooks/useHousehold'
import { useHouseholdMembers, invalidateHouseholdMembersCache } from '@/hooks/useHouseholdMembers'
import { AppShell } from '@/components/layout/AppShell'
import { useProfile } from '@/hooks/useProfile'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
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

export default function HouseholdPage() {
  const profile = useProfile()
  const { household, createHousehold, joinHousehold, leaveHousehold, deleteHousehold } = useHousehold()

  return (
    <AppShell profile={profile} backTo="/">
      <div className="max-w-2xl mx-auto px-6 py-8 flex flex-col gap-6">
        <h1 className="text-2xl font-semibold">Household</h1>
        {household ? (
          <HouseholdView
            leaveHousehold={leaveHousehold}
            deleteHousehold={deleteHousehold}
          />
        ) : (
          <HouseholdSetup
            createHousehold={createHousehold}
            joinHousehold={joinHousehold}
          />
        )}
      </div>
    </AppShell>
  )
}

// ─── Household view (already in a household) ──────────────────────────────────

function HouseholdView({
  leaveHousehold,
  deleteHousehold,
}: {
  leaveHousehold: () => Promise<void>
  deleteHousehold: () => Promise<void>
}) {
  const { household } = useHousehold()
  const { members } = useHouseholdMembers()
  const navigate = useNavigate()
  const [copied, setCopied] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  if (!household) return null

  const isOwner = household.role === 'owner'
  const allMembers = members ? [members.me, ...members.others] : []

  const copyInviteCode = async () => {
    await navigator.clipboard.writeText(household.invite_code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleLeave = async () => {
    setBusy(true)
    setActionError(null)
    try {
      await leaveHousehold()
      invalidateHouseholdMembersCache()
      // household is now null — page re-renders to setup view
    } catch (err) {
      setActionError(axios.isAxiosError(err) ? (err.response?.data?.detail ?? 'Something went wrong.') : 'Something went wrong.')
    } finally {
      setBusy(false)
    }
  }

  const handleDelete = async () => {
    setBusy(true)
    setActionError(null)
    try {
      await deleteHousehold()
      invalidateHouseholdMembersCache()
      navigate('/')
    } catch (err) {
      setActionError(axios.isAxiosError(err) ? (err.response?.data?.detail ?? 'Something went wrong.') : 'Something went wrong.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      {/* Household info */}
      <Card>
        <CardContent className="flex items-center gap-4 pt-4">
          <div className="flex items-center justify-center w-10 h-10 rounded-full bg-muted">
            <Home className="w-5 h-5 text-muted-foreground" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-medium truncate">{household.name}</p>
            <p className="text-xs text-muted-foreground capitalize">{household.role}</p>
          </div>
        </CardContent>
      </Card>

      {/* Members */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
            <Users className="w-4 h-4" />
            Members
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3 pt-0">
          {allMembers.length === 0 && (
            <p className="text-sm text-muted-foreground">Loading…</p>
          )}
          {allMembers.map((m, i) => (
            <div key={m.id} className="flex items-center gap-3">
              {m.avatar_url ? (
                <img src={m.avatar_url} alt={m.name} className="w-8 h-8 rounded-full" referrerPolicy="no-referrer" />
              ) : (
                <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center text-xs font-medium">
                  {m.name?.[0]?.toUpperCase()}
                </div>
              )}
              <span className="text-sm">{m.name}</span>
              {i === 0 && <span className="ml-auto text-xs text-muted-foreground">you</span>}
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Invite code (owner only) */}
      {isOwner && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
              <Key className="w-4 h-4" />
              Invite code
            </CardTitle>
          </CardHeader>
          <CardContent className="flex items-center gap-2 pt-0">
            <code className="flex-1 rounded-lg bg-muted px-3 py-2 text-sm font-mono tracking-wider">
              {household.invite_code}
            </code>
            <Button variant="ghost" size="icon" onClick={copyInviteCode} aria-label="Copy invite code">
              {copied ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Danger zone */}
      <div className="rounded-xl border border-destructive/30 p-5 flex flex-col gap-4">
        <p className="text-sm font-medium text-destructive">Danger zone</p>

        {actionError && (
          <p className="text-sm text-destructive">{actionError}</p>
        )}

        {isOwner ? (
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="destructive" disabled={busy}>Delete household</Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Delete household?</AlertDialogTitle>
                <AlertDialogDescription>
                  This will permanently delete <strong>{household.name}</strong> and remove all members.
                  All shared data (grocery lists, tasks, battery logs) will be lost.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction
                  className="bg-destructive text-white hover:bg-destructive/90"
                  onClick={handleDelete}
                >
                  Delete
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        ) : (
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="destructive" disabled={busy}>Leave household</Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Leave household?</AlertDialogTitle>
                <AlertDialogDescription>
                  You will be removed from <strong>{household.name}</strong>.
                  You can re-join later with an invite code.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction
                  className="bg-destructive text-white hover:bg-destructive/90"
                  onClick={handleLeave}
                >
                  Leave
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        )}
      </div>
    </>
  )
}

// ─── Setup view (not yet in a household) ─────────────────────────────────────

type SetupMode = 'choose' | 'create' | 'join'

function HouseholdSetup({
  createHousehold,
  joinHousehold,
}: {
  createHousehold: (name: string) => Promise<void>
  joinHousehold: (code: string) => Promise<void>
}) {
  const [mode, setMode] = useState<SetupMode>('choose')
  const [householdName, setHouseholdName] = useState('')
  const [inviteCode, setInviteCode] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleCreate = async () => {
    if (!householdName.trim()) return
    setLoading(true)
    setError(null)
    try {
      await createHousehold(householdName.trim())
      invalidateHouseholdMembersCache()
      // household is now set — page re-renders to HouseholdView
    } catch (err) {
      setError(err instanceof HouseholdConflictError ? err.message : 'Could not create household. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleJoin = async () => {
    if (!inviteCode.trim()) return
    setLoading(true)
    setError(null)
    try {
      await joinHousehold(inviteCode.trim())
      invalidateHouseholdMembersCache()
    } catch (err) {
      setError(err instanceof HouseholdConflictError ? err.message : 'Invalid invite code. Check with your partner.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card className="w-full">
      {mode === 'choose' && (
        <>
          <CardHeader>
            <CardTitle>No household yet</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <Button onClick={() => setMode('create')}>Create a household</Button>
            <Button variant="outline" onClick={() => setMode('join')}>Join with invite code</Button>
          </CardContent>
        </>
      )}

      {mode === 'create' && (
        <>
          <CardHeader>
            <CardTitle>Create household</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <Input
              placeholder="e.g. The Smith Family"
              value={householdName}
              onChange={e => setHouseholdName(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleCreate()}
            />
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button onClick={handleCreate} disabled={loading || !householdName.trim()}>
              {loading ? 'Creating…' : 'Create'}
            </Button>
            <Button variant="ghost" onClick={() => { setMode('choose'); setError(null) }}>Back</Button>
          </CardContent>
        </>
      )}

      {mode === 'join' && (
        <>
          <CardHeader>
            <CardTitle>Join household</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <Input
              placeholder="Invite code"
              value={inviteCode}
              onChange={e => setInviteCode(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleJoin()}
            />
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button onClick={handleJoin} disabled={loading || !inviteCode.trim()}>
              {loading ? 'Joining…' : 'Join'}
            </Button>
            <Button variant="ghost" onClick={() => { setMode('choose'); setError(null) }}>Back</Button>
          </CardContent>
        </>
      )}
    </Card>
  )
}
