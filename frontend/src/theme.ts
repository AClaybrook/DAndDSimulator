// Chart colours for both themes: one categorical palette (the same eight hues stepped for each surface, checked for colour vision
// deficiencies and contrast), and the text and grid tones Plotly figures are drawn with
import { useComputedColorScheme } from '@mantine/core'

export type Scheme = 'dark' | 'light'

// A series keeps its slot (a character's colour follows the character, not its rank). Eight slots, like the simulator's eight characters
export const SERIES: Record<Scheme, string[]> = {
  dark: ['#3987e5', '#d95926', '#199e70', '#c98500', '#d55181', '#008300', '#9085e9', '#e66767'],
  light: ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#6250d6', '#e34948'],
}

export const CHART_TOKENS: Record<Scheme, { text: string; muted: string; grid: string; zero: string; line: string; hoverBg: string; hoverBorder: string; surface: string }> = {
  dark: { text: '#d5d7e0', muted: '#9a9db0', grid: 'rgba(255,255,255,0.07)', zero: 'rgba(255,255,255,0.18)', line: 'rgba(255,255,255,0.2)', hoverBg: '#2a2b3d', hoverBorder: '#4d4f66', surface: '#1f202e' },
  light: { text: '#2b2c33', muted: '#676a78', grid: 'rgba(0,0,0,0.07)', zero: 'rgba(0,0,0,0.2)', line: 'rgba(0,0,0,0.25)', hoverBg: '#ffffff', hoverBorder: '#c9cad3', surface: '#ffffff' },
}

export const useScheme = (): Scheme => useComputedColorScheme('dark')
export const useColors = () => SERIES[useScheme()]
export const colorAt = (colors: string[], index: number) => colors[((index % colors.length) + colors.length) % colors.length]

// '#3987e5' with an alpha, for bands and fills
export function withAlpha(hex: string, alpha: number) {
  const n = parseInt(hex.slice(1), 16)
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${alpha})`
}

// Figures only say what to draw; text, grid and hover colours come from the theme here, so every chart follows the light/dark switch
export function themed(layout: Record<string, unknown>, scheme: Scheme): Record<string, unknown> {
  const t = CHART_TOKENS[scheme]
  const axis = { gridcolor: t.grid, zerolinecolor: t.zero, linecolor: t.line, tickfont: { color: t.muted }, automargin: true }
  const out: Record<string, unknown> = {
    ...layout,
    font: { family: 'inherit', size: 12, color: t.text, ...(layout.font as object) },
    hoverlabel: { bgcolor: t.hoverBg, bordercolor: t.hoverBorder, font: { color: t.text }, ...(layout.hoverlabel as object) },
    legend: { ...(layout.legend as object), font: { color: t.text } },
  }
  const keys = new Set(['xaxis', 'yaxis', ...Object.keys(layout).filter((k) => /^[xy]axis\d*$/.test(k))])
  for (const key of keys) {
    const own = (layout[key] ?? {}) as Record<string, unknown>
    const title = typeof own.title === 'string' ? { text: own.title } : (own.title as object | undefined)
    out[key] = { ...axis, ...own, ...(title ? { title: { ...title, font: { color: t.muted, size: 12 } } } : {}) }
  }
  return out
}
