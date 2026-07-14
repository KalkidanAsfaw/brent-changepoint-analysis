// Chart color tokens (validated palette — see docs in repo README).
// Light/dark are separately selected steps, not an automatic flip.
import { useEffect, useState } from 'react'

const light = {
  price: '#2a78d6', // categorical slot 1 (blue)
  volatility: '#1baf7a', // categorical slot 2 (aqua)
  up: '#2a78d6', // diverging cool pole
  down: '#e34948', // diverging warm pole
  breakLine: '#4a3aa7', // violet — detected change points
  eventLine: '#898781', // muted — researched events
  eventSelected: '#e34948',
  grid: '#e1e0d9',
  axis: '#c3c2b7',
  ink: '#0b0b0b',
  inkSecondary: '#52514e',
  inkMuted: '#898781',
  surface: '#fcfcfb',
}

const dark = {
  price: '#3987e5',
  volatility: '#199e70',
  up: '#3987e5',
  down: '#e66767',
  breakLine: '#9085e9',
  eventLine: '#898781',
  eventSelected: '#e66767',
  grid: '#2c2c2a',
  axis: '#383835',
  ink: '#ffffff',
  inkSecondary: '#c3c2b7',
  inkMuted: '#898781',
  surface: '#1a1a19',
}

export function useTheme() {
  const mq = window.matchMedia('(prefers-color-scheme: dark)')
  const [isDark, setIsDark] = useState(mq.matches)
  useEffect(() => {
    const onChange = (e) => setIsDark(e.matches)
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [])
  return isDark ? dark : light
}
