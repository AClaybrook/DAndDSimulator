import { Center, Loader, useComputedColorScheme } from '@mantine/core'
import { useEffect, useRef, useState } from 'react'

type PlotlyModule = typeof import('plotly.js-dist-min')

// Plotly is large, load it once on first use so the page itself starts fast
let plotly: Promise<PlotlyModule> | null = null
const loadPlotly = () => (plotly ??= import('plotly.js-dist-min').then((m) => (m as unknown as { default: PlotlyModule }).default ?? m))

export interface Figure { data: object[]; layout: Record<string, unknown> }

// Figures come in dark colours (the backend's plotly_dark template, chartLayout); the light theme swaps text, grid and hover colours
function forLightTheme(layout: Record<string, unknown>): Record<string, unknown> {
  const axis = { gridcolor: 'rgba(0,0,0,0.08)', zerolinecolor: 'rgba(0,0,0,0.2)', linecolor: 'rgba(0,0,0,0.25)', tickfont: { color: '#444' } }
  const light: Record<string, unknown> = {
    ...layout, template: undefined, font: { ...(layout.font as object), color: '#333' },
    hoverlabel: { bgcolor: '#fff', bordercolor: '#ccc', font: { color: '#222' } },
    legend: { ...(layout.legend as object), font: { color: '#333' } },
  }
  for (const key of Object.keys(layout).filter((k) => /^[xy]axis\d*$/.test(k))) light[key] = { ...(layout[key] as object), ...axis }
  if (!Object.keys(layout).some((k) => /^[xy]axis/.test(k))) Object.assign(light, { xaxis: axis, yaxis: axis })
  return light
}
export interface PlotClick { customdata?: unknown; pointIndex: number; curveNumber: number }

interface Props {
  figure: Figure
  height?: number | string
  onClick?: (point: PlotClick) => void
  config?: Record<string, unknown>
  keepColors?: boolean // A figure with its own background (the item map), drawn the same in both themes
}

// A Plotly figure drawn with a transparent background to sit on the page
export function Plot({ figure, height = 520, onClick, config, keepColors }: Props) {
  const scheme = useComputedColorScheme('dark')
  const ref = useRef<HTMLDivElement>(null)
  const clickRef = useRef(onClick)
  useEffect(() => { clickRef.current = onClick }, [onClick])
  const [ready, setReady] = useState(false)

  useEffect(() => {
    let cancelled = false
    loadPlotly().then((Plotly) => {
      const node = ref.current
      if (cancelled || !node) return
      const base = scheme === 'light' && !keepColors ? forLightTheme(figure.layout) : figure.layout
      const layout = { margin: { l: 50, r: 20, t: 50, b: 45 }, ...base, autosize: true, height: typeof height === 'number' ? height : undefined,
        paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: (figure.layout.plot_bgcolor as string) ?? 'rgba(0,0,0,0)' }
      Plotly.react(node, figure.data as Plotly.Data[], layout as Partial<Plotly.Layout>, { displaylogo: false, responsive: true, ...config })
      const events = node as unknown as { removeAllListeners?: (e: string) => void; on: (e: string, cb: (ev: { points: PlotClick[] }) => void) => void }
      events.removeAllListeners?.('plotly_click')
      events.on('plotly_click', (ev) => ev.points?.[0] && clickRef.current?.(ev.points[0]))
      setReady(true)
    })
    return () => { cancelled = true }
  }, [figure, height, config, scheme, keepColors])

  useEffect(() => {
    const node = ref.current
    if (!node) return
    const observer = new ResizeObserver(() => loadPlotly().then((Plotly) => node.isConnected && node.offsetWidth && Plotly.Plots.resize(node)))
    observer.observe(node)
    return () => observer.disconnect()
  }, [])

  return (
    <div style={{ position: 'relative', minHeight: height, height: typeof height === 'string' ? height : undefined }}>
      {!ready && <Center style={{ position: 'absolute', inset: 0 }}><Loader /></Center>}
      <div ref={ref} style={{ width: '100%', height: '100%' }} />
    </div>
  )
}
