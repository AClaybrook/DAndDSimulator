import { Center, Loader } from '@mantine/core'
import { useEffect, useRef, useState } from 'react'

type PlotlyModule = typeof import('plotly.js-dist-min')

// Plotly is large, load it once on first use so the page itself starts fast
let plotly: Promise<PlotlyModule> | null = null
const loadPlotly = () => (plotly ??= import('plotly.js-dist-min').then((m) => (m as unknown as { default: PlotlyModule }).default ?? m))

export interface Figure { data: object[]; layout: Record<string, unknown> }
export interface PlotClick { customdata?: unknown; pointIndex: number; curveNumber: number }

interface Props {
  figure: Figure
  height?: number | string
  onClick?: (point: PlotClick) => void
  config?: Record<string, unknown>
}

// A Plotly figure drawn with a transparent background to sit on the page
export function Plot({ figure, height = 520, onClick, config }: Props) {
  const ref = useRef<HTMLDivElement>(null)
  const clickRef = useRef(onClick)
  useEffect(() => { clickRef.current = onClick }, [onClick])
  const [ready, setReady] = useState(false)

  useEffect(() => {
    let cancelled = false
    loadPlotly().then((Plotly) => {
      const node = ref.current
      if (cancelled || !node) return
      const layout = { margin: { l: 50, r: 20, t: 50, b: 45 }, ...figure.layout, autosize: true, height: typeof height === 'number' ? height : undefined,
        paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: (figure.layout.plot_bgcolor as string) ?? 'rgba(0,0,0,0)' }
      Plotly.react(node, figure.data as Plotly.Data[], layout as Partial<Plotly.Layout>, { displaylogo: false, responsive: true, ...config })
      const events = node as unknown as { removeAllListeners?: (e: string) => void; on: (e: string, cb: (ev: { points: PlotClick[] }) => void) => void }
      events.removeAllListeners?.('plotly_click')
      events.on('plotly_click', (ev) => ev.points?.[0] && clickRef.current?.(ev.points[0]))
      setReady(true)
    })
    return () => { cancelled = true }
  }, [figure, height, config])

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
