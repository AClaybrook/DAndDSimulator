// Formatting helpers shared by pages (kept out of component files so fast refresh works)
import type { Build, PlannerOptions, Value } from './api'

export const formatValue = (v: Value) =>
  typeof v === 'number' ? (Number.isInteger(v) ? String(v) : v.toFixed(2)) : Array.isArray(v) ? v.join(', ') : String(v ?? '')

// Layout shared by the charts drawn in the browser: a legend under the plot. Colours come from the theme (components/Plot)
export function chartLayout(extra: Record<string, unknown> = {}): Record<string, unknown> {
  return { legend: { orientation: 'h', y: -0.18 }, ...extra }
}

// Moves labels apart so names at the ends of lines don't sit on top of each other: in order, each at least minGap above the one before
export function spread(values: number[], minGap: number): number[] {
  const out = [...values]
  let last = -Infinity
  for (const [v, i] of values.map((v, i) => [v, i]).sort((a, b) => a[0] - b[0])) {
    out[i] = Math.max(v, last + minGap)
    last = out[i]
  }
  return out
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
