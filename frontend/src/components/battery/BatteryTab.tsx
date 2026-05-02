import { useState } from 'react'
import { useBatteryLogs, toDailyAverages } from '@/hooks/useBatteryLogs'
import BatteryLogger from '@/components/battery/BatteryLogger'
import BatteryChart from '@/components/battery/BatteryChart'
import { Button } from '@/components/ui/button'
import { useBatteryRealtime } from '@/hooks/useBatteryRealtime'

interface Props {
  userId: string
  userName: string
  householdId: string
}

type Range = '7d' | '30d' | '12m'

export default function BatteryTab({ userId, userName, householdId }: Props) {
  const [range, setRange] = useState<Range>('30d')
  const { logs, loading, refetch } = useBatteryLogs(range)
  useBatteryRealtime(householdId, refetch)
  const { you, partner } = toDailyAverages(logs, userId)

  return (
    <div className="space-y-6">
      {/* logger */}
      <BatteryLogger
        userId={userId}
        householdId={householdId}
        onLogged={refetch}
      />

      {/* range selector */}
      <div className="flex items-center justify-between">
        <p className="text-xs text-muted-foreground uppercase tracking-widest">
          History
        </p>
        <div className="flex gap-1">
          {(['7d', '30d', '12m'] as Range[]).map(r => (
            <Button
              key={r}
              size="sm"
              variant={range === r ? 'default' : 'ghost'}
              onClick={() => setRange(r)}
              className="text-xs h-7 px-3"
            >
              {r}
            </Button>
          ))}
        </div>
      </div>

      {/* charts */}
      {loading ? (
        <p className="text-muted-foreground text-sm">Loading...</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <BatteryChart
            data={you}
            label={userName}
            color="#c8f076"
          />
          <BatteryChart
            data={partner}
            label="Partner"
            color="#76c8f0"
            empty={partner.length === 0}
          />
        </div>
      )}
    </div>
  )
}