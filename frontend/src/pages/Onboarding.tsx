import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useHousehold } from '@/hooks/useHousehold'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

type Mode = 'choose' | 'create' | 'join'

export default function Onboarding() {
  const [mode, setMode] = useState<Mode>('choose')
  const [householdName, setHouseholdName] = useState('')
  const [inviteCode, setInviteCode] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { createHousehold, joinHousehold } = useHousehold()

  const handleCreate = async () => {
    if (!householdName.trim()) return
    setLoading(true)
    setError(null)
    try {
      await createHousehold(householdName)
      navigate('/')
    } catch {
      setError('Could not create household. Please try again.')
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
      navigate('/')
    } catch {
      setError('Invalid invite code. Check with your partner.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-svh items-center justify-center bg-background">
      <Card className="w-full max-w-sm">

        {mode === 'choose' && (
          <>
            <CardHeader className="text-center">
              <CardTitle className="text-2xl">Welcome to Capple</CardTitle>
              <CardDescription>Set up your household to get started</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              <Button onClick={() => setMode('create')}>
                Create a household
              </Button>
              <Button variant="outline" onClick={() => setMode('join')}>
                Join with invite code
              </Button>
            </CardContent>
          </>
        )}

        {mode === 'create' && (
          <>
            <CardHeader>
              <CardTitle>Create household</CardTitle>
              <CardDescription>Give your home a name</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              <Input
                placeholder="e.g. Casa Vargas"
                value={householdName}
                onChange={e => setHouseholdName(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleCreate()}
              />
              {error && <p className="text-destructive text-sm">{error}</p>}
              <Button onClick={handleCreate} disabled={loading || !householdName.trim()}>
                {loading ? 'Creating...' : 'Create'}
              </Button>
              <Button variant="ghost" onClick={() => setMode('choose')}>
                Back
              </Button>
            </CardContent>
          </>
        )}

        {mode === 'join' && (
          <>
            <CardHeader>
              <CardTitle>Join household</CardTitle>
              <CardDescription>Enter the invite code from your partner</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              <Input
                placeholder="e.g. a1b2c3d4"
                value={inviteCode}
                onChange={e => setInviteCode(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleJoin()}
              />
              {error && <p className="text-destructive text-sm">{error}</p>}
              <Button onClick={handleJoin} disabled={loading || !inviteCode.trim()}>
                {loading ? 'Joining...' : 'Join'}
              </Button>
              <Button variant="ghost" onClick={() => setMode('choose')}>
                Back
              </Button>
            </CardContent>
          </>
        )}

      </Card>
    </div>
  )
}