import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import api from '@/lib/api'

interface Props {
  userId: string
  householdId: string
  onLogged: () => void
}

function batteryLabel(v: number): string {
  if (v < 15) return 'Completely drained'
  if (v < 30) return 'Running on empty'
  if (v < 45) return 'Quietly tired'
  if (v < 60) return 'Getting there'
  if (v < 75) return 'Socially content'
  if (v < 88) return 'Energised'
  return 'Fully charged'
}

function batteryColor(v: number): string {
  if (v < 20) return '#f07676'
  if (v < 40) return '#f0c876'
  if (v < 60) return '#d4f076'
  return '#c8f076'
}

export default function BatteryLogger({ onLogged }: Props) {
  const [level, setLevel] = useState(70)
  const [note, setNote] = useState('')
  const [effectiveAt, setEffectiveAt] = useState(
    () => new Date().toISOString().slice(0, 16)
  )
  const [loading, setLoading] = useState(false)
  const [justLogged, setJustLogged] = useState(false)

  const handleLog = async () => {
    setLoading(true)
    try {
      await api.post('/api/battery-logs', {
        level,
        note: note.trim() || null,
        effective_at: new Date(effectiveAt).toISOString(),
      })
      setJustLogged(true)
      setNote('')
      onLogged()
      setTimeout(() => setJustLogged(false), 2000)
    } finally {
      setLoading(false)
    }
  }

  const color = batteryColor(level)

  return (
    <div className="rounded-xl border border-border bg-card p-6 space-y-5">
      <p className="text-xs uppercase tracking-widest text-muted-foreground">
        Your battery
      </p>

      {/* number + label */}
      <div className="flex items-end gap-4">
        <span className="text-6xl font-light tabular-nums"
          style={{ color }}>{level}</span>
        <span className="text-lg text-muted-foreground pb-1">
          {batteryLabel(level)}
        </span>
      </div>

      {/* slider */}
      <div className="space-y-2">
        <input
          type="range" min={0} max={100} value={level}
          onChange={e => setLevel(Number(e.target.value))}
          className="w-full accent-current"
          style={{ accentColor: color }}
        />
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>0 · drained</span>
          <span>50</span>
          <span>100 · energised</span>
        </div>
      </div>

      {/* effective at */}
      <div className="space-y-1">
        <label className="text-xs text-muted-foreground uppercase tracking-widest">
          For when
        </label>
        <input
          type="datetime-local"
          value={effectiveAt}
          onChange={e => setEffectiveAt(e.target.value)}
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
        />
      </div>

      {/* note */}
      <div className="space-y-1">
        <label className="text-xs text-muted-foreground uppercase tracking-widest">
          Note (optional)
        </label>
        <Textarea
          placeholder="Rough day, post-party recovery..."
          value={note}
          onChange={e => setNote(e.target.value)}
          rows={2}
          className="resize-none"
        />
      </div>

      <Button
        className="w-full"
        onClick={handleLog}
        disabled={loading || justLogged}
        style={justLogged ? { background: '#76f0a8', color: '#0c0c0e' } : {}}
      >
        {justLogged ? 'Logged ✓' : loading ? 'Logging...' : 'Log battery'}
      </Button>
    </div>
  )
}
