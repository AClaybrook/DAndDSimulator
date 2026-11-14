// Unit tests of the front end's own logic (no browser): chart building, label placement, formatting, gear carried between acts
import { describe, expect, it } from 'vitest'
import type { Build, DistributionChart, LinesChart, SweepChart } from './api'
import { classLine, formatValue, spread, toCsv } from './format'
import { placeLabels } from './pages/map/labels'
import { drawChart } from './pages/simulator/charts'
import { equipmentAt } from './party'
import { uniqueName } from './store'
import { SERIES, colorAt, themed, withAlpha } from './theme'

const build = (changes: Partial<Build>): Build => ({
  name: 'Tav', preset: 'fighter_gwm', equipment: {}, buffs: {}, conditions: [], levels: {}, character: null, carried: [], roles: [], variants: [], advantage: false, assumptions: {}, ...changes,
})

describe('gear', () => {
  it('carries items into later acts until a slot changes or is cleared', () => {
    const b = build({ equipment: { '1': { melee_main: 'sword', ring_1: 'band' }, '2': { melee_main: 'glaive', ring_1: '' }, '3': { helmet: 'helm' } } })
    expect(equipmentAt(b, '1')).toEqual({ melee_main: 'sword', ring_1: 'band' })
    expect(equipmentAt(b, '2')).toEqual({ melee_main: 'glaive' })
    expect(equipmentAt(b, '3')).toEqual({ melee_main: 'glaive', helmet: 'helm' })
  })
})

describe('formatting', () => {
  it('spreads labels at least a gap apart, keeping their order', () => {
    expect(spread([82, 80, 45, 30], 6)).toEqual([86, 80, 45, 30])
    expect(spread([10, 10, 10], 5)).toEqual([10, 15, 20])
    expect(spread([], 5)).toEqual([])
  })
  it('writes CSV cells with commas and quotes safely', () => {
    expect(toCsv(['Build', 'Note'], [['A, B', 'said "hi"'], ['C', ['x', 'y']]])).toBe('Build,Note\n"A, B","said ""hi"""\nC,x; y')
  })
  it('formats table values', () => {
    expect([formatValue(3), formatValue(3.14159), formatValue(null), formatValue(['a', 'b'])]).toEqual(['3', '3.14', '', 'a, b'])
  })
  it('names a custom character by its classes', () => {
    const custom = build({ character: { name: 'Tav', race: 'Human', scores: {}, bonus: {}, classes: [['paladin', 'Oath of Vengeance', 7], ['warlock', 'The Hexblade', 5]],
      feats: [], fighting_styles: [], routine: 'two_handed', cantrip: '', spell: '', toggles: {}, level_order: [], boons: {}, respec: {} } })
    expect(classLine(custom, { presets: [] } as never)).toBe('Paladin 7 (Oath of Vengeance) / Warlock 5 (The Hexblade)')
  })
  it('keeps names unique', () => {
    expect(uniqueName('Fighter', ['Rogue'])).toBe('Fighter')
    expect(uniqueName('Fighter', ['Fighter', 'Fighter (2)'])).toBe('Fighter (3)')
  })
})

describe('theme', () => {
  it('has eight colour slots in both themes and wraps past them', () => {
    expect(SERIES.dark).toHaveLength(8)
    expect(SERIES.light).toHaveLength(8)
    expect(colorAt(SERIES.dark, 9)).toBe(SERIES.dark[1])
    expect(withAlpha('#3987e5', 0.5)).toBe('rgba(57,135,229,0.5)')
  })
  it('colours every axis of a figure, keeping its own settings', () => {
    const layout = themed({ xaxis: { title: 'Damage' }, yaxis2: { range: [0, 1] } }, 'light')
    expect((layout.xaxis as { title: { text: string } }).title.text).toBe('Damage')
    expect((layout.yaxis2 as { range: number[]; gridcolor: string }).range).toEqual([0, 1])
    expect((layout.yaxis2 as { gridcolor: string }).gridcolor).toBe((layout.yaxis as { gridcolor: string }).gridcolor)
  })
})

describe('map labels', () => {
  it('puts a name above its marker when nothing is in the way', () => {
    expect(placeLabels([{ x: 100, y: 100, text: 'Sword', size: 10 }], 1)).toEqual(['top center'])
  })
  it('moves a name that would cover another marker or name', () => {
    const places = placeLabels([{ x: 100, y: 100, text: 'Very Heavy Greataxe', size: 10 }, { x: 100, y: 88, text: '', size: 10 }, { x: 104, y: 100, text: 'Steelforged Sword', size: 10 }], 1)
    expect(places[0]).not.toBe('top center') // The second marker sits right above the first
    expect(new Set([places[0], places[2]]).size).toBe(2) // Two names next to each other go to different sides
  })
})

describe('simulator charts', () => {
  const series = (name: string, owner: number) => ({ name, owner, start: [0, 10, 20], percent: [5, 60, 35], box: { q1: 10, median: 12, q3: 20, low: 0, high: 25, mean: 14 },
    curve: { kind: 'exact' as const, start: [0, 10, 20], percent: [5, 60, 35] }, stats: { mean: 14, sd: 5, skew: 0.1, allMiss: 0.05 } })
  it('draws one row per character, coloured by the character and not its position', () => {
    const chart: DistributionChart = { kind: 'distribution', title: 'Damage per round', xTitle: 'Damage', binWidth: 10, series: [series('B', 1), series('A', 0)] }
    const { figure, height } = drawChart(chart, SERIES.dark)
    const bars = figure.data.filter((t) => (t as { type: string }).type === 'bar') as { yaxis: string; marker: { color: string } }[]
    expect(bars.map((b) => b.yaxis)).toEqual(['y', 'y2'])
    expect(bars[0].marker.color).toBe(withAlpha(SERIES.dark[1], 0.5))
    expect((figure.layout.annotations as { text: string }[])[0].text).toContain('all miss 5.0%')
    expect(height).toBeGreaterThan(240)
    expect((drawChart(chart, SERIES.dark, true).figure.layout.annotations as { text: string }[])[0].text).toBe('<b>B</b>  14')
  })
  it('labels up to four lines at their ends, and leaves that to the legend on a narrow screen', () => {
    const chart: LinesChart = { kind: 'lines', title: '', xTitle: 'Round', yTitle: '%', x: [1, 2], yMax: 100, unit: '%', series: [{ name: 'A', owner: 0, y: [10, 90] }, { name: 'B', owner: 1, y: [20, 91] }] }
    const labels = drawChart(chart, SERIES.dark).figure.layout.annotations as { y: number; text: string }[]
    expect(labels.map((l) => l.text)).toEqual(['A', 'B'])
    expect(labels[1].y - labels[0].y).toBeGreaterThanOrEqual(6) // Spread apart
    expect(drawChart(chart, SERIES.dark, true).figure.layout.annotations).toEqual([])
  })
  it('gives attacks of one character its colour and different dashes', () => {
    const line = (name: string, owner: number) => ({ name, owner, x: [10, 11], mean: [5, 4], median: [5, 4], q1: [3, 2], q3: [7, 6] })
    const chart: SweepChart = { kind: 'sweep', title: '', xTitle: 'Armor Class', yTitle: 'Damage', series: [line('A: Slash', 0), line('A: Stab', 0), line('B: Bolt', 1)] }
    const lines = drawChart(chart, SERIES.light).figure.data.filter((t) => (t as { name?: string }).name) as { line: { color: string; dash: string } }[]
    expect(lines.map((l) => l.line.color)).toEqual([SERIES.light[0], SERIES.light[0], SERIES.light[1]])
    expect(lines[0].line.dash).not.toBe(lines[1].line.dash)
  })
})
