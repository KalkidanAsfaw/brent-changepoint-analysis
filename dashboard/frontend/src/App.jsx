import { useEffect, useMemo, useState } from 'react'
import { downsample, fetchChangepoints, fetchEvents, fetchIndicators, fetchPrices } from './api'
import { ImpactChart, PriceChart, VolatilityChart } from './charts'
import { useTheme } from './theme'

const FULL = { start: '1987-05-20', end: '2022-11-14' }

const PRESETS = [
  { label: 'Full history', ...FULL },
  { label: '2008 crisis', start: '2008-01-01', end: '2009-06-30' },
  { label: 'OPEC price war', start: '2014-01-01', end: '2015-12-31' },
  { label: 'COVID-19', start: '2019-10-01', end: '2020-12-31' },
  { label: '2022 invasion', start: '2021-12-01', end: '2022-06-30' },
]

function FilterBar({ range, setRange, categories, category, setCategory }) {
  return (
    <div className="filter-row">
      {PRESETS.map((p) => (
        <button key={p.label}
          className={range.start === p.start && range.end === p.end ? 'preset active' : 'preset'}
          onClick={() => setRange({ start: p.start, end: p.end })}>
          {range.start === p.start && range.end === p.end ? '✓ ' : ''}{p.label}
        </button>
      ))}
      <span className="custom-range">
        <input type="date" value={range.start} min={FULL.start} max={range.end}
               onChange={(e) => setRange({ ...range, start: e.target.value })} />
        <span>–</span>
        <input type="date" value={range.end} min={range.start} max={FULL.end}
               onChange={(e) => setRange({ ...range, end: e.target.value })} />
      </span>
      <select value={category} onChange={(e) => setCategory(e.target.value)}>
        <option value="All">All event categories</option>
        {categories.map((c) => <option key={c} value={c}>{c}</option>)}
      </select>
    </div>
  )
}

function BreakCards({ changepoints, onZoom, selected }) {
  return (
    <div className="cards">
      {Object.entries(changepoints).map(([name, cp]) => {
        const up = cp.price_change_pct >= 0
        return (
          <button key={name} onClick={() => onZoom(name, cp)}
                  className={selected === name ? 'card active' : 'card'}>
            <div className="card-title">{name}</div>
            <div className="card-date">break: {cp.change_date}</div>
            <div className="card-value">
              ${cp.mean_price_before.toFixed(0)} → ${cp.mean_price_after.toFixed(0)}
              <span className={up ? 'delta up' : 'delta down'}>
                {up ? '+' : ''}{cp.price_change_pct}%
              </span>
            </div>
            <div className="card-sub">
              volatility {(cp.ann_vol_before * 100).toFixed(0)}% → {(cp.ann_vol_after * 100).toFixed(0)}%
              · P(vol ↑) {(cp.p_vol_increased * 100).toFixed(0)}%
            </div>
          </button>
        )
      })}
    </div>
  )
}

export default function App() {
  const theme = useTheme()
  const [range, setRange] = useState(PRESETS[0])
  const [category, setCategory] = useState('All')
  const [prices, setPrices] = useState([])
  const [events, setEvents] = useState([])
  const [changepoints, setChangepoints] = useState({})
  const [indicators, setIndicators] = useState(null)
  const [selectedEvent, setSelectedEvent] = useState(null)
  const [selectedBreak, setSelectedBreak] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([fetchEvents(), fetchChangepoints(), fetchIndicators(30)])
      .then(([ev, cp, ind]) => { setEvents(ev); setChangepoints(cp); setIndicators(ind) })
      .catch((e) => setError(String(e)))
  }, [])

  useEffect(() => {
    setLoading(true)
    fetchPrices(range.start, range.end)
      .then((rows) => setPrices(downsample(rows)))
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false))
  }, [range])

  const categories = useMemo(
    () => [...new Set(events.map((e) => e.category))].sort(), [events])

  const inRange = (d) => d >= range.start && d <= range.end
  const visibleEvents = events.filter(
    (e) => inRange(e.date) && (category === 'All' || e.category === category))
  const visibleBreaks = Object.values(changepoints).filter((c) => inRange(c.change_date))
  const visibleVol = (indicators?.rolling_volatility ?? []).filter((v) => inRange(v.date))
  const visibleImpacts = (indicators?.event_impacts ?? []).filter(
    (e) => inRange(e.date) && (category === 'All' || e.category === category))

  const zoomToBreak = (name, cp) => {
    setSelectedBreak(name)
    const [lo, hi] = cp.change_date_hdi_95 ?? [cp.change_date, cp.change_date]
    const pad = (d, days) => {
      const t = new Date(d); t.setDate(t.getDate() + days)
      return t.toISOString().slice(0, 10)
    }
    setRange({ start: pad(lo, -120), end: pad(hi, 120) })
  }

  if (error) return <main className="page"><p className="error">Backend unreachable: {error}</p></main>

  return (
    <main className="page">
      <header>
        <h1>Brent Oil Price — Change Point Explorer</h1>
        <p className="subtitle">
          Bayesian structural breaks vs. geopolitical, OPEC, and economic events ·
          Birhan Energies
        </p>
      </header>

      <FilterBar range={range} setRange={setRange} categories={categories}
                 category={category} setCategory={setCategory} />

      <BreakCards changepoints={changepoints} onZoom={zoomToBreak} selected={selectedBreak} />

      <section className="panel" style={{ opacity: loading ? 0.5 : 1 }}>
        <h2>Daily price (USD/bbl)</h2>
        <p className="legend">
          <span className="key" style={{ background: theme.price }} /> price
          <span className="key dashed" style={{ borderColor: theme.eventLine }} /> event
          <span className="key dashed" style={{ borderColor: theme.breakLine }} /> detected break
        </p>
        <PriceChart rows={prices} events={visibleEvents} breaks={visibleBreaks}
                    selectedEvent={selectedEvent} theme={theme} />
      </section>

      <div className="two-col">
        <section className="panel">
          <h2>30-day rolling volatility (annualized)</h2>
          <VolatilityChart rows={visibleVol} theme={theme} />
        </section>

        <section className="panel">
          <h2>Avg price change ±30 days around each event</h2>
          <p className="hint">Click a bar to highlight the event on the price chart.</p>
          <ImpactChart impacts={visibleImpacts} selectedEvent={selectedEvent}
                       onSelect={(e) => setSelectedEvent(e)} theme={theme} />
        </section>
      </div>

      {selectedEvent && (
        <section className="panel detail">
          <h2>{selectedEvent.name} — {selectedEvent.date}</h2>
          <p>
            Avg price ${selectedEvent.avg_price_before} → ${selectedEvent.avg_price_after}
            &nbsp;({selectedEvent.pct_change > 0 ? '+' : ''}{selectedEvent.pct_change}% over ±30 days).
            &nbsp;{events.find((ev) => ev.name === selectedEvent.name)?.description}
          </p>
          <button className="preset" onClick={() => setSelectedEvent(null)}>Clear highlight</button>
        </section>
      )}

      <footer>
        Change points from a PyMC Bayesian switch-point model on daily log returns.
        Temporal association with events is not proof of causation.
      </footer>
    </main>
  )
}
