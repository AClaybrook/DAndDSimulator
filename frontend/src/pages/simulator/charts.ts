// Plotly figures for the simulator's chart data (api/charts.py). Colours follow the character (series.owner), never the rank
import type { Chart, DistributionChart, LinesChart, SweepChart } from '../../api'
import type { Figure } from '../../components/Plot'
import { spread } from '../../format'
import { colorAt, withAlpha } from '../../theme'

export interface Drawn { figure: Figure; height: number }

const DASHES = ['solid', 'dash', 'dot', 'dashdot', 'longdash']
const num = (v: number) => (Number.isInteger(v) ? String(v) : v.toFixed(1))

// One row per series on a shared damage axis, so overlapping distributions stay readable: bars are the simulated rounds, the line the
// exact distribution (or a smooth fit), the band the middle half of rounds and the dotted line the mean
export function distributionFigure(chart: DistributionChart, colors: string[], compact = false): Drawn {
  const n = chart.series.length
  const w = chart.binWidth
  const gap = n > 1 ? 0.04 : 0
  const row = (1 - gap * (n - 1)) / Math.max(n, 1)
  const data: object[] = []
  const layout: Record<string, unknown> = { showlegend: false, bargap: 0, hovermode: 'x unified', hoversubplots: 'axis', margin: { l: 12, r: 12, t: 6, b: 44 } }
  const annotations: object[] = []
  const shapes: object[] = []
  chart.series.forEach((s, i) => {
    const axis = i === 0 ? 'y' : `y${i + 1}`
    const top = 1 - i * (row + gap)
    const color = colorAt(colors, s.owner)
    const peak = Math.max(...s.percent, ...(s.curve?.percent ?? []), 1e-9)
    // Headroom above the tallest bar for the row's label
    layout[i === 0 ? 'yaxis' : `yaxis${i + 1}`] = { domain: [Math.max(top - row, 0), top], range: [0, peak * 1.45], showticklabels: false, showgrid: false, fixedrange: true }
    const range = (v: number) => (w === 1 ? `${v}` : `${v} to ${v + w - 1}`)
    data.push({
      type: 'bar', name: s.name, x: s.start.map((v) => v + (w - 1) / 2), y: s.percent, width: w, yaxis: axis, marker: { color: withAlpha(color, 0.5), line: { width: 0 } },
      text: s.start.map(range), textposition: 'none', hovertemplate: s.curve?.kind === 'exact' ? undefined : `${s.name}: %{y:.2f}% of rounds<extra></extra>`,
      hoverinfo: s.curve?.kind === 'exact' ? 'skip' : undefined,
    })
    if (s.curve) {
      data.push({
        type: 'scatter', mode: 'lines', name: s.name, x: s.curve.start.map((v) => v + (w - 1) / 2), y: s.curve.percent, yaxis: axis, line: { color, width: 2 },
        hovertemplate: s.curve.kind === 'exact' ? `${s.name}: %{y:.2f}% of rounds<extra></extra>` : undefined, hoverinfo: s.curve.kind === 'exact' ? undefined : 'skip',
      })
    }
    const miss = s.stats.allMiss != null && s.stats.allMiss >= 0.0005 ? ` · all miss ${(100 * s.stats.allMiss).toFixed(1)}%` : ''
    annotations.push({
      xref: 'paper', yref: 'paper', x: 0, y: top, xanchor: 'left', yanchor: 'top', showarrow: false, align: 'left',
      text: compact ? `<b>${s.name}</b>  ${num(s.stats.mean)}` : `<b>${s.name}</b>  mean ${num(s.stats.mean)} · half of rounds ${num(s.box.q1)} to ${num(s.box.q3)}${miss}`,
    })
    shapes.push({ type: 'rect', xref: 'x', yref: `${axis} domain`, x0: s.box.q1, x1: s.box.q3, y0: 0, y1: 0.69, fillcolor: withAlpha(color, 0.12), line: { width: 0 }, layer: 'below' })
    shapes.push({ type: 'line', xref: 'x', yref: `${axis} domain`, x0: s.stats.mean, x1: s.stats.mean, y0: 0, y1: 0.69, line: { color, width: 1.5, dash: 'dot' } })
  })
  layout.xaxis = { title: { text: chart.xTitle }, anchor: n > 1 ? `y${n}` : 'y', rangemode: 'tozero', zeroline: false }
  return { figure: { data, layout: { ...layout, annotations, shapes } }, height: Math.min(Math.max(n * 160 + 56, 320), 1600) }
}

// Labels at the right end of each line when there are few enough to read; the legend stays for every chart with two or more series
function endLabels(series: { name: string; owner: number; x: number; y: number }[], colors: string[], top: number, compact = false) {
  if (series.length > 4 || compact) return [] // On a narrow screen the legend names the lines, the plot keeps the width
  const ys = spread(series.map((s) => s.y), top * 0.06)
  return series.map((s, i) => ({ x: s.x, y: ys[i], xanchor: 'left', yanchor: 'middle', xshift: 8, showarrow: false, text: s.name, font: { size: 11, color: colorAt(colors, s.owner) } }))
}

// A swept parameter: each line is the mean with the middle half of rounds as a band. Attacks of one character share its colour
export function sweepFigure(chart: SweepChart, colors: string[], compact = false): Drawn {
  const data: object[] = []
  const seen: Record<number, number> = {}
  for (const s of chart.series) {
    const color = colorAt(colors, s.owner)
    const dash = DASHES[(seen[s.owner] = (seen[s.owner] ?? -1) + 1) % DASHES.length]
    data.push({ type: 'scatter', mode: 'lines', x: s.x, y: s.q3, line: { width: 0 }, hoverinfo: 'skip', showlegend: false, legendgroup: s.name })
    data.push({ type: 'scatter', mode: 'lines', x: s.x, y: s.q1, line: { width: 0 }, fill: 'tonexty', fillcolor: withAlpha(color, chart.series.length > 4 ? 0.06 : 0.12),
      hoverinfo: 'skip', showlegend: false, legendgroup: s.name })
    data.push({ type: 'scatter', mode: 'lines+markers', name: s.name, legendgroup: s.name, x: s.x, y: s.mean, line: { color, width: 2, dash }, marker: { size: 6, color },
      customdata: s.q1.map((q, i) => [q, s.q3[i], s.median[i]]),
      hovertemplate: `${s.name}: %{y:.1f} (half of rounds %{customdata[0]:.0f} to %{customdata[1]:.0f})<extra></extra>` })
  }
  const labels = endLabels(chart.series.map((s) => ({ name: s.name, owner: s.owner, x: s.x[s.x.length - 1], y: s.mean[s.mean.length - 1] })), colors,
    Math.max(1, ...chart.series.flatMap((s) => s.q3)), compact)
  const layout = {
    hovermode: 'x unified', showlegend: chart.series.length > 1, legend: { orientation: 'h', y: -0.2 }, annotations: labels,
    margin: { l: 50, r: labels.length ? 150 : 16, t: 8, b: 44 }, xaxis: { title: { text: chart.xTitle }, dtick: 1 }, yaxis: { title: { text: chart.yTitle }, rangemode: 'tozero' },
  }
  return { figure: { data, layout }, height: 460 }
}

// A value per round for each character: the chance the enemy is down by each round, or the damage in each round of a fight
export function linesFigure(chart: LinesChart, colors: string[], compact = false): Drawn {
  const data = chart.series.map((s) => ({
    type: 'scatter', mode: 'lines+markers', name: s.name, x: chart.x, y: s.y, line: { color: colorAt(colors, s.owner), width: 2 }, marker: { size: 8, color: colorAt(colors, s.owner) },
    hovertemplate: `${s.name}: %{y:.1f}${chart.unit}<extra></extra>`,
  }))
  const labels = endLabels(chart.series.map((s) => ({ name: s.name, owner: s.owner, x: chart.x[chart.x.length - 1], y: s.y[s.y.length - 1] })), colors,
    chart.yMax ?? Math.max(1, ...chart.series.flatMap((s) => s.y)), compact)
  const layout = {
    hovermode: 'x unified', showlegend: chart.series.length > 1, legend: { orientation: 'h', y: -0.2 }, annotations: labels,
    margin: { l: 50, r: labels.length ? 150 : 16, t: 8, b: 44 }, xaxis: { title: { text: chart.xTitle }, dtick: 1 },
    yaxis: { title: { text: chart.yTitle }, rangemode: 'tozero', ...(chart.yMax ? { range: [0, chart.yMax * 1.03] } : {}) },
  }
  return { figure: { data, layout }, height: 440 }
}

// compact: a narrow screen, so shorter labels and the legend instead of names at the line ends
export function drawChart(chart: Chart, colors: string[], compact = false): Drawn {
  if (chart.kind === 'distribution') return distributionFigure(chart, colors, compact)
  if (chart.kind === 'sweep') return sweepFigure(chart, colors, compact)
  return linesFigure(chart, colors, compact)
}
