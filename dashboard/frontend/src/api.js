async function getJSON(url) {
  const resp = await fetch(url)
  if (!resp.ok) throw new Error(`${url} -> ${resp.status}`)
  return resp.json()
}

export const fetchPrices = (start, end) =>
  getJSON(`/api/prices?start=${start}&end=${end}`)

export const fetchEvents = () => getJSON('/api/events')

export const fetchChangepoints = () => getJSON('/api/changepoints')

export const fetchIndicators = (windowDays = 30) =>
  getJSON(`/api/indicators?window=${windowDays}`)

// Thin long series so the chart stays responsive; keeps first & last points.
export function downsample(rows, maxPoints = 1500) {
  if (rows.length <= maxPoints) return rows
  const step = Math.ceil(rows.length / maxPoints)
  return rows.filter((_, i) => i % step === 0 || i === rows.length - 1)
}

// Snap a target date to the nearest trading day present in the data,
// so reference lines land on real axis positions.
export function snapDate(dates, target) {
  if (!dates.length) return null
  let best = dates[0]
  let bestDelta = Infinity
  const t = new Date(target).getTime()
  for (const d of dates) {
    const delta = Math.abs(new Date(d).getTime() - t)
    if (delta < bestDelta) {
      bestDelta = delta
      best = d
    }
  }
  return bestDelta <= 45 * 86400e3 ? best : null
}
