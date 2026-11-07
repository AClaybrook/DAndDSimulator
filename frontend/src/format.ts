// Formatting helpers shared by pages (kept out of component files so fast refresh works)
import type { Build, PlannerOptions, Value } from './api'

export const formatValue = (v: Value) =>
  typeof v === 'number' ? (Number.isInteger(v) ? String(v) : v.toFixed(2)) : Array.isArray(v) ? v.join(', ') : String(v ?? '')

// Plotly layout for charts drawn in the browser, matching the dark theme of the backend's figures
export function chartLayout(extra: Record<string, unknown> = {}): Record<string, unknown> {
  const axis = { gridcolor: 'rgba(255,255,255,0.08)', zerolinecolor: 'rgba(255,255,255,0.15)', linecolor: 'rgba(255,255,255,0.2)' }
  return {
    font: { color: '#C9C9C9', family: 'inherit', size: 12 },
    hoverlabel: { bgcolor: '#25262b', bordercolor: '#444', font: { color: '#eee' } },
    legend: { orientation: 'h', y: -0.18 },
    ...extra,
    xaxis: { ...axis, ...(extra.xaxis as object) },
    yaxis: { ...axis, ...(extra.yaxis as object) },
  }
}

export function classLine(build: Build, options: PlannerOptions) {
  const classes = (build.character as { classes?: [string, string, number][] } | null)?.classes
  if (classes?.length) return classes.map(([c, sub, n]) => `${c[0].toUpperCase()}${c.slice(1)} ${n}${sub ? ` (${sub})` : ''}`).join(' / ')
  return options.presets.find((p) => p.key === build.preset)?.label ?? build.preset
}

// Saves text as a file in the browser's downloads
export function download(filename: string, text: string, type = 'text/csv') {
  const url = URL.createObjectURL(new Blob([text], { type }))
  const link = Object.assign(document.createElement('a'), { href: url, download: filename })
  link.click()
  URL.revokeObjectURL(url)
}

const csvCell = (v: unknown) => {
  const text = Array.isArray(v) ? v.join('; ') : String(v ?? '')
  return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text
}

export const toCsv = (columns: string[], rows: unknown[][]) => [columns, ...rows].map((r) => r.map(csvCell).join(',')).join('\n')

export const fileName = (title: string) => `${title.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '') || 'table'}.csv`
