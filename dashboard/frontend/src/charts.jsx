import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { snapDate } from './api'

const axisTick = (t) => ({ fill: t.inkMuted, fontSize: 11 })

function ChartTooltip({ active, payload, label, unit, theme }) {
  if (!active || !payload?.length) return null
  return (
    <div className="tooltip">
      <div className="tooltip-date">{label}</div>
      {payload.map((p) => (
        <div key={p.dataKey} className="tooltip-row">
          <span className="tooltip-key" style={{ background: p.stroke || p.fill }} />
          <strong style={{ color: theme.ink }}>
            {typeof p.value === 'number' ? p.value.toLocaleString() : p.value}
            {unit}
          </strong>
          <span>{p.name}</span>
        </div>
      ))}
    </div>
  )
}

export function PriceChart({ rows, events, breaks, selectedEvent, theme }) {
  const dates = rows.map((r) => r.date)
  return (
    <ResponsiveContainer width="100%" height={340}>
      <LineChart data={rows} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
        <CartesianGrid stroke={theme.grid} vertical={false} />
        <XAxis dataKey="date" tick={axisTick(theme)} stroke={theme.axis}
               minTickGap={60} tickLine={false} />
        <YAxis tick={axisTick(theme)} stroke={theme.axis} tickLine={false}
               width={44} domain={['auto', 'auto']} />
        <Tooltip content={<ChartTooltip unit=" $/bbl" theme={theme} />} cursor={{ stroke: theme.axis }} />
        {events.map((ev) => {
          const x = snapDate(dates, ev.date)
          if (!x) return null
          const selected = selectedEvent?.name === ev.name
          return (
            <ReferenceLine key={ev.name} x={x}
              stroke={selected ? theme.eventSelected : theme.eventLine}
              strokeDasharray="4 4" strokeWidth={selected ? 2 : 1}
              label={selected ? {
                value: ev.name, angle: -90, position: 'insideTopLeft',
                fill: theme.eventSelected, fontSize: 11,
              } : undefined}
            />
          )
        })}
        {breaks.map((b) => {
          const x = snapDate(dates, b.change_date)
          if (!x) return null
          return (
            <ReferenceLine key={b.change_date} x={x} stroke={theme.breakLine}
                           strokeWidth={2} strokeDasharray="2 3" />
          )
        })}
        <Line type="monotone" dataKey="price" name="Brent price"
              stroke={theme.price} strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
      </LineChart>
    </ResponsiveContainer>
  )
}

export function VolatilityChart({ rows, theme }) {
  return (
    <ResponsiveContainer width="100%" height={180}>
      <LineChart data={rows} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
        <CartesianGrid stroke={theme.grid} vertical={false} />
        <XAxis dataKey="date" tick={axisTick(theme)} stroke={theme.axis}
               minTickGap={60} tickLine={false} />
        <YAxis tick={axisTick(theme)} stroke={theme.axis} tickLine={false}
               width={44} tickFormatter={(v) => `${Math.round(v * 100)}%`} />
        <Tooltip
          content={<ChartTooltip unit="" theme={theme} />}
          cursor={{ stroke: theme.axis }}
          formatter={(v) => `${(v * 100).toFixed(0)}%`}
        />
        <Line type="monotone" dataKey="volatility" name="Annualized volatility (30d)"
              stroke={theme.volatility} strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
      </LineChart>
    </ResponsiveContainer>
  )
}

export function ImpactChart({ impacts, selectedEvent, onSelect, theme }) {
  const height = Math.max(220, impacts.length * 26)
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={impacts} layout="vertical"
                margin={{ top: 4, right: 40, bottom: 0, left: 8 }}>
        <CartesianGrid stroke={theme.grid} horizontal={false} />
        <XAxis type="number" tick={axisTick(theme)} stroke={theme.axis}
               tickLine={false} tickFormatter={(v) => `${v}%`} />
        <YAxis type="category" dataKey="name" width={210}
               tick={{ fill: theme.inkSecondary, fontSize: 11 }}
               stroke={theme.axis} tickLine={false} />
        <Tooltip content={<ChartTooltip unit="%" theme={theme} />}
                 cursor={{ fill: 'transparent' }} />
        <ReferenceLine x={0} stroke={theme.axis} />
        <Bar dataKey="pct_change" name="Avg price change (±30d)"
             radius={[0, 4, 4, 0]} barSize={12}
             onClick={(d) => onSelect(d)} cursor="pointer">
          {impacts.map((e) => (
            <Cell key={e.name}
                  fill={e.pct_change >= 0 ? theme.up : theme.down}
                  stroke={selectedEvent?.name === e.name ? theme.ink : 'none'}
                  strokeWidth={1.5} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
