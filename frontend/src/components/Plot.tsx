import { Center, Loader } from '@mantine/core'
import { useEffect, useRef, useState } from 'react'

type PlotlyModule = typeof import('plotly.js-dist-min')

// Plotly is large, load it once on first use so the page itself starts fast
let plotly: Promise<PlotlyModule> | null = null
const loadPlotly = () => (plotly ??= import('plotly.js-dist-min').then((m) => (m as unknown as { default: PlotlyModule }).default ?? m))

interface Props {
  figure: { data: object[]; layout: Record<string, unknown> }
  height?: number
}

// A Plotly figure from the backend, drawn with a transparent background to sit on the page
export function Plot({ figure, height = 520 }: Props) {
  const ref = useRef<HTMLDivElement>(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    let cancelled = false
    loadPlotly().then((Plotly) => {
      if (cancelled || !ref.current) return
      const layout = { ...figure.layout, autosize: true, height, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)', margin: { l: 50, r: 20, t: 50, b: 45 } }
      Plotly.react(ref.current, figure.data as Plotly.Data[], layout as Partial<Plotly.Layout>, { displaylogo: false, responsive: true })
      setReady(true)
    })
    return () => { cancelled = true }
  }, [figure, height])

  useEffect(() => {
    const node = ref.current
    if (!node) return
    const observer = new ResizeObserver(() => loadPlotly().then((Plotly) => node.isConnected && Plotly.Plots.resize(node)))
    observer.observe(node)
    return () => observer.disconnect()
  }, [])

  return (
    <div style={{ position: 'relative', minHeight: height }}>
      {!ready && <Center style={{ position: 'absolute', inset: 0 }}><Loader /></Center>}
      <div ref={ref} style={{ width: '100%' }} />
    </div>
  )
}
