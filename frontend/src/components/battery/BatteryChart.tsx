import {
  AreaChart, Area, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid
} from 'recharts'
import type { DailyAverage } from '@/types/battery'

interface Props {
  data: DailyAverage[]
  label: string
  color: string
  empty?: boolean
}

export default function BatteryChart({ data, label, color, empty }: Props) {
  const avg = data.length
    ? Math.round(data.reduce((s, d) => s + d.avg, 0) / data.length)
    : null

  return (
    <div className="rounded-xl border border-border bg-card p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full" style={{ background: color }}/>
          <span className="text-xs uppercase tracking-widest text-muted-foreground">
            {label}
          </span>
        </div>
        {avg !== null && (
          <span className="text-xs text-muted-foreground">
            avg <span className="text-foreground">{avg}</span>
          </span>
        )}
      </div>

      {empty || data.length === 0 ? (
        <div className="h-32 flex items-center justify-center">
          <p className="text-xs text-muted-foreground">No data yet</p>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={128}>
          <AreaChart data={data} margin={{ top: 4, right: 4, left: -24, bottom: 0 }}>
            <defs>
              <linearGradient id={`grad-${label}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={color} stopOpacity={0.2}/>
                <stop offset="100%" stopColor={color} stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2a35" vertical={false}/>
            <XAxis
              dataKey="date"
              tick={{ fontSize: 9, fill: '#555' }}
              tickFormatter={d => d.slice(5)}
              tickLine={false}
              axisLine={false}
              interval="preserveStartEnd"
            />
            <YAxis
              domain={[0, 100]}
              tick={{ fontSize: 9, fill: '#555' }}
              tickLine={false}
              axisLine={false}
              ticks={[0, 50, 100]}
            />
            <Tooltip
              contentStyle={{
                background: '#141418',
                border: '1px solid #2a2a35',
                borderRadius: 6,
                fontSize: 11,
              }}
              labelFormatter={l => l}
              formatter={(v) => [v ?? 0, 'avg']}
            />
            <Area
              type="monotone"
              dataKey="avg"
              stroke={color}
              strokeWidth={1.5}
              fill={`url(#grad-${label})`}
              dot={false}
              activeDot={{ r: 3, fill: color }}
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}