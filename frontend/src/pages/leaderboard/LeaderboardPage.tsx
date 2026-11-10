import {
  Badge, Button, Center, Chip, Drawer, Grid, Group, Loader, Popover, SegmentedControl, Select, SimpleGrid, Stack, Switch, Text, TextInput,
} from '@mantine/core'
import { useMediaQuery } from '@mantine/hooks'
import { IconDeviceFloppy } from '@tabler/icons-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { ColumnDef } from '@tanstack/react-table'
import { useMemo, useState } from 'react'
import { bg3, type LeaderboardEntry } from '../../api'
import { SortTable } from '../../components/DataTable'
import { PageHeader, Section, Stat } from '../../components/Layout'
import { chartLayout } from '../../format'
import { Plot } from '../../components/Plot'
import { ACTS, useParty } from '../../party'
import { CHART_TOKENS, SERIES, colorAt, useColors, useScheme, type Scheme } from '../../theme'
import { useUrlList, useUrlState } from '../../urlState'

// Three build sources take the first three colour slots (the ones that stay apart on a scatter); your own party is marked by shape and
// a neutral tone instead of a fourth hue
const SOURCE_SLOT: Record<string, number> = { Preset: 0, 'Build doc': 1, 'Reddit (approx.)': 2 }
const OWN = 'Your party'
const sourceColors = (scheme: Scheme): Record<string, string> => ({
  ...Object.fromEntries(Object.entries(SOURCE_SLOT).map(([s, i]) => [s, SERIES[scheme][i]])), [OWN]: CHART_TOKENS[scheme].text,
})
const VARIANT_SHORT: Record<string, string> = { planned: 'Planned', max_damage: 'Max damage', max_ac: 'Max AC', best_score: 'Best score' }

const PLANNED = ['planned']
const ALL_SOURCES = ['Your party', 'Preset', 'Build doc', 'Reddit (approx.)']

type Row = LeaderboardEntry & { overall: number; d: Record<string, number | null>; rank: Record<string, number> }

const num = (v: number | null | undefined, digits = 1) => (v === null || v === undefined ? '–' : v.toFixed(digits))

export function LeaderboardPage() {
  const party = useParty((s) => s.party)
  const [scenario, setScenario] = useUrlState('scenario', 'reliable')
  const [enemies, setEnemies] = useUrlState('enemies', '1')
  const [variants, setVariants] = useUrlList('variants', PLANNED)
  const [sources, setSources] = useUrlList('sources', ALL_SOURCES)
  const [chartAct, setChartAct] = useUrlState('act', '3')
  const [compare_, setCompare] = useUrlState('compare', '')
  const compareId = compare_ || null
  const setCompareId = (id: string | null) => setCompare(id ?? '')
  const [open, setOpen] = useState<Row | null>(null)
  const [hovered, setHovered] = useState<string | null>(null) // The build under the pointer, in the table or the chart
  const scheme = useScheme()
  const nameRoom = useMediaQuery('(max-width: 48em)') ? 18 : 34 // Characters of a build's name beside its dot
  const SOURCE_COLORS = useMemo(() => sourceColors(scheme), [scheme])
  const [label, setLabel] = useState('')
  const [withVariants, setWithVariants] = useState(false)
  const client = useQueryClient()

  const options = useQuery({ queryKey: ['leaderboard-options'], queryFn: bg3.leaderboardOptions, staleTime: Infinity })
  const entries = useQuery({ queryKey: ['leaderboard', party], queryFn: () => bg3.leaderboard(party), placeholderData: (p) => p })
  const runs = useQuery({ queryKey: ['runs'], queryFn: bg3.runs })
  const compare = useQuery({ queryKey: ['run', compareId], queryFn: () => bg3.run(Number(compareId)), enabled: Boolean(compareId) })
  const save = useMutation({
    mutationFn: () => bg3.saveRun(party, label, withVariants),
    onSuccess: () => { client.invalidateQueries({ queryKey: ['runs'] }); client.invalidateQueries({ queryKey: ['leaderboard'] }) },
  })

  const view = `${scenario}@${enemies}`
  const rows = useMemo<Row[]>(() => {
    const shown = (entries.data ?? []).filter((e) => variants.includes(e.variant) && sources.includes(e.source))
    const best = Object.fromEntries(ACTS.map((a) => [a, Math.max(1e-9, ...shown.map((e) => e.damage[view]?.[a] ?? 0))]))
    const ranks: Record<string, Record<string, number>> = {}
    for (const a of ACTS) {
      [...shown].sort((x, y) => (y.damage[view]?.[a] ?? 0) - (x.damage[view]?.[a] ?? 0)).forEach((e, i) => { (ranks[e.key] ??= {})[a] = i + 1 })
    }
    return shown.map((e) => ({
      ...e, d: e.damage[view] ?? {}, rank: ranks[e.key] ?? {},
      overall: Math.round((100 * ACTS.reduce((t, a) => t + (e.damage[view]?.[a] ?? 0) / best[a], 0)) / 3),
    }))
  }, [entries.data, variants, sources, view])
  const comparison = useMemo(() => Object.fromEntries((compare.data ?? []).map((e) => [e.key, e])), [compare.data])

  const columns = useMemo<ColumnDef<Row, unknown>[]>(() => [
    { id: 'Build', header: 'Build', accessorFn: (r) => r.name, cell: ({ row: { original: r } }) => (
      <Group gap={6} wrap="nowrap">
        <span style={{ width: 8, height: 8, borderRadius: r.source === OWN ? 1 : 4, transform: r.source === OWN ? 'rotate(45deg)' : undefined, background: SOURCE_COLORS[r.source], flexShrink: 0 }} />
        <Text size="xs" fw={r.source === OWN ? 700 : 400} truncate className="build-name">{r.name}</Text>
        {r.variant !== 'planned' && <Badge size="xs" variant="light">{VARIANT_SHORT[r.variant]}</Badge>}
      </Group>
    ) },
    { id: 'Source', header: 'Source', accessorFn: (r) => r.source },
    ...ACTS.map((a): ColumnDef<Row, unknown> => ({ id: `Act ${a}`, header: `Act ${a}`, accessorFn: (r) => r.d[a] ?? null, sortUndefined: 'last',
      cell: ({ row: { original: r } }) => <span style={{ whiteSpace: 'nowrap' }}>{num(r.d[a])} <Text span size="10px" c="dimmed">#{r.rank[a]}</Text></span> })),
    { id: 'Overall', header: 'Overall', accessorFn: (r) => r.overall },
    // One armour class and score column, for the act the chart shows; the other acts are in the column picker
    { id: 'AC', header: `AC (Act ${chartAct})`, accessorFn: (r) => r.ac[chartAct] ?? null },
    { id: 'Score', header: `Score (Act ${chartAct})`, accessorFn: (r) => r.score[chartAct] ?? null, cell: (c) => num(c.getValue() as number, 0) },
    ...ACTS.map((a): ColumnDef<Row, unknown> => ({ id: `AC ${a}`, header: `AC ${a}`, accessorFn: (r) => r.ac[a] ?? null })),
    ...ACTS.map((a): ColumnDef<Row, unknown> => ({ id: `Score ${a}`, header: `Score ${a}`, accessorFn: (r) => r.score[a] ?? null, cell: (c) => num(c.getValue() as number, 0) })),
    { id: 'Fingerprint', header: 'Fingerprint', accessorFn: (r) => r.fingerprint, cell: (c) => <code>{String(c.getValue())}</code> },
    ...(compareId ? [{ id: 'Change', header: 'Change', accessorFn: (r: Row) => {
      const before = comparison[r.key]
      if (!before) return null
      return ACTS.reduce((t, a) => t + (r.d[a] ?? 0) - (before.damage[view]?.[a] ?? 0), 0) / 3
    }, cell: ({ row: { original: r } }: { row: { original: Row } }) => {
      const before = comparison[r.key]
      if (!before) return <Text span size="xs" c="dimmed">–</Text>
      const changed = before.fingerprint !== r.fingerprint
      const deltas = ACTS.map((a) => (r.d[a] ?? 0) - (before.damage[view]?.[a] ?? 0))
      const same = !changed && deltas.every((d) => Math.abs(d) < 0.05)
      return same ? <Text span size="xs" c="dimmed">same</Text>
        : <Text span size="xs" c={changed ? 'yellow' : 'orange'}>{changed ? 'build' : 'model'} {deltas.map((d) => `${d >= 0 ? '+' : ''}${d.toFixed(1)}`).join(' / ')}</Text>
    } } as ColumnDef<Row, unknown>] : []),
  ], [compareId, comparison, view, chartAct, SOURCE_COLORS])

  if (!options.data || !entries.data) return <Center h={300}><Loader /></Center>
  const scenarioInfo = options.data.scenarios.find((s) => s.key === scenario)
  const leader = [...rows].sort((a, b) => b.overall - a.overall)[0]
  const bestIn = (a: string) => [...rows].sort((x, y) => (y.d[a] ?? 0) - (x.d[a] ?? 0))[0]

  const jitter = (r: Row) => (r.ac[chartAct] ?? 0) + ((r.fingerprint.charCodeAt(0) % 7) - 3) * 0.06
  const plotted = rows.filter((r) => r.d[chartAct] !== null && r.ac[chartAct] !== null)
  const surface = CHART_TOKENS[scheme].surface
  const marked = plotted.find((r) => r.key === hovered)
  // The three highest in this act are named on the chart; hover or click any dot for the rest
  const named = [...plotted].sort((a, b) => (b.d[chartAct] ?? 0) - (a.d[chartAct] ?? 0)).slice(0, 3)
  const scatter = {
    data: [
      ...options.data.sources.filter((s) => sources.includes(s)).map((source) => {
        const pts = plotted.filter((r) => r.source === source)
        return {
          type: 'scatter', mode: 'markers', name: source, customdata: pts.map((r) => r.key),
          x: pts.map(jitter), y: pts.map((r) => r.d[chartAct]),
          text: pts.map((r) => `${r.name}${r.variant !== 'planned' ? ` (${VARIANT_SHORT[r.variant]})` : ''}<br>AC ${r.ac[chartAct]}, score ${num(r.score[chartAct], 0)}`),
          hovertemplate: '%{text}<br>%{y:.1f} damage per round<extra></extra>',
          marker: { color: SOURCE_COLORS[source], symbol: source === OWN ? 'diamond' : 'circle', size: pts.map((r) => (source === OWN ? 12 : 8) + (r.score[chartAct] ?? 0) / 10),
            opacity: 0.9, line: { width: 2, color: surface } },
        }
      }),
      ...(marked ? [{ type: 'scatter', mode: 'markers', x: [jitter(marked)], y: [marked.d[chartAct]], hoverinfo: 'skip', showlegend: false,
        marker: { symbol: 'circle-open', size: 26, color: CHART_TOKENS[scheme].text, line: { width: 2 } } }] : []),
    ],
    layout: chartLayout({ xaxis: { title: { text: 'Armour class' } }, yaxis: { title: { text: 'Damage per round' }, rangemode: 'tozero' }, margin: { l: 55, r: 10, t: 10, b: 40 },
      annotations: named.map((r, i) => ({ x: jitter(r), y: r.d[chartAct], text: r.name.length > nameRoom ? `${r.name.slice(0, nameRoom - 2)}…` : r.name, showarrow: true, arrowhead: 0, arrowwidth: 1,
        arrowcolor: CHART_TOKENS[scheme].muted, ax: i % 2 ? 40 : -40, ay: -22 - 6 * i, font: { size: 11 } })) }),
  }
  const byKey = Object.fromEntries(rows.map((r) => [r.key, r]))

  return (
    <>
      <PageHeader title="Leaderboard"
        subtitle={`${rows.length} builds under the same conditions: ${Object.values(options.data.referenceEnemies).join(', ')}, ${options.data.roundsPerFight} round fights`}
        actions={<>
          <Select size="xs" placeholder="Compare with a saved run" clearable w={260} value={compareId} onChange={setCompareId}
            data={(runs.data ?? []).map((r) => ({ value: String(r.id), label: `#${r.id} ${r.created.slice(0, 16).replace('T', ' ')} · ${r.label || r.kind} (${r.count})` }))} />
          {!options.data.readOnly && <Popover width={280} position="bottom-end" withArrow>
            <Popover.Target><Button size="xs" variant="default" leftSection={<IconDeviceFloppy size={14} />} disabled={!party.length}>Save party</Button></Popover.Target>
            <Popover.Dropdown>
              <Stack gap="xs">
                <Text size="xs" c="dimmed">Saves your party's numbers and specs in the local database, to compare against later.</Text>
                <TextInput size="xs" placeholder="Label (optional)" value={label} onChange={(e) => setLabel(e.currentTarget.value)} />
                <Switch size="xs" label="Also search gear variants (about 4 s a member)" checked={withVariants} onChange={(e) => setWithVariants(e.currentTarget.checked)} />
                <Button size="xs" loading={save.isPending} onClick={() => save.mutate()}>Save</Button>
                {save.data && <Text size="xs" c="green">Saved run #{save.data.id} ({save.data.rows} rows)</Text>}
              </Stack>
            </Popover.Dropdown>
          </Popover>}
        </>} />

      <Section padding="sm">
        <Group gap="md" wrap="wrap" align="flex-end">
          <Select size="xs" label="Scenario" w={210} value={scenario} onChange={(v) => v && setScenario(v)} allowDeselect={false}
            data={options.data.scenarios.map((s) => ({ value: s.key, label: s.label }))} />
          <div>
            <Text size="xs" fw={500} mb={2}>Damage vs</Text>
            <SegmentedControl size="xs" value={enemies} onChange={setEnemies}
              data={options.data.enemyCounts.map((n) => ({ value: String(n), label: n === 1 ? '1 enemy' : `${n} (AoE)` }))} />
          </div>
          <div>
            <Text size="xs" fw={500} mb={4}>Gear</Text>
            <Chip.Group multiple value={variants} onChange={setVariants}>
              <Group gap={4}>{options.data.variants.map((v) => <Chip key={v.key} value={v.key} size="xs">{VARIANT_SHORT[v.key]}</Chip>)}</Group>
            </Chip.Group>
          </div>
          <div>
            <Text size="xs" fw={500} mb={4}>Builds</Text>
            <Chip.Group multiple value={sources} onChange={setSources}>
              <Group gap={4}>{options.data.sources.map((s) => <Chip key={s} value={s} size="xs" variant="outline">{s}</Chip>)}</Group>
            </Chip.Group>
          </div>
        </Group>
        {scenarioInfo && <Text size="xs" c="dimmed">{scenarioInfo.note}</Text>}
      </Section>

      <SimpleGrid cols={{ base: 2, md: 4 }} mt="md">
        {leader && <Stat label="Best overall" value={leader.overall} detail={leader.name} color={SOURCE_COLORS[leader.source]}
          help="Average share of the best damage at each act, 100 = best in every act" />}
        {ACTS.map((a) => { const r = bestIn(a); return r && <Stat key={a} label={`Best in Act ${a}`} value={num(r.d[a])} detail={r.name} color={SOURCE_COLORS[r.source]} /> })}
      </SimpleGrid>

      <Grid mt="md" gap="md">
        <Grid.Col span={{ base: 12, lg: 5 }}>
          <Section title="Damage vs armour class" actions={
            <SegmentedControl size="xs" value={chartAct} onChange={setChartAct} data={ACTS.map((a) => ({ value: a, label: `Act ${a}` }))} />}>
            <Text size="xs" c="dimmed" mt={-6}>Up is more damage, right is harder to hit. Bigger marks have a higher overall score, diamonds are your party. Click one for its build.</Text>
            <Plot figure={scatter} height={430} onClick={(p) => { const row = byKey[String(p.customdata)]; if (row) setOpen(row) }}
              onHover={(p) => setHovered(p?.customdata ? String(p.customdata) : null)} />
          </Section>
        </Grid.Col>
        <Grid.Col span={{ base: 12, lg: 7 }}>
          <Section title="Rankings">
            <SortTable title="Leaderboard" data={rows} columns={columns} initialSorting={[{ id: 'Overall', desc: true }]} dense
              hidden={['Source', 'Fingerprint', ...ACTS.flatMap((a) => [`AC ${a}`, `Score ${a}`])]}
              onRowClick={setOpen} onRowHover={(r) => setHovered(r?.key ?? null)} maxHeight={560}
              rowStyle={(r) => (r.key === hovered ? { outline: '1px solid var(--mantine-color-dimmed)', outlineOffset: -1 } : r.source === OWN ? { fontWeight: 700 } : undefined)} />
          </Section>
        </Grid.Col>
      </Grid>

      <BuildDrawer row={open} view={view} scenarios={options.data.scenarios} enemies={enemies} onClose={() => setOpen(null)} />
    </>
  )
}

function BuildDrawer({ row, view, scenarios, enemies, onClose }: { row: Row | null; view: string; scenarios: { key: string; label: string }[]; enemies: string; onClose: () => void }) {
  const colors = useColors()
  if (!row) return <Drawer opened={false} onClose={onClose} />
  const figure = {
    data: scenarios.map((s) => ({ type: 'bar', name: s.label, x: ACTS.map((a) => `Act ${a}`), y: ACTS.map((a) => row.damage[`${s.key}@${enemies}`]?.[a] ?? null),
      marker: { color: colorAt(colors, scenarios.indexOf(s)) }, hovertemplate: `${s.label}: %{y:.1f}<extra></extra>` })),
    layout: chartLayout({ barmode: 'group', yaxis: { title: { text: 'Damage per round' } }, margin: { l: 50, r: 10, t: 10, b: 30 }, legend: { orientation: 'h', y: -0.15, font: { size: 10 } } }),
  }
  return (
    <Drawer opened onClose={onClose} position="right" size="lg" title={<Text fw={600}>{row.name}</Text>}>
      <Stack gap="md">
        <Group gap="xs">
          <Badge variant="light">{row.source}</Badge>
          <Badge variant="outline">{VARIANT_SHORT[row.variant]} gear</Badge>
          <Badge variant="outline" color="gray"><code>{row.fingerprint}</code></Badge>
          {row.same_as && <Text size="xs" c="dimmed">Same build as {row.same_as}</Text>}
        </Group>
        <SimpleGrid cols={3}>
          {ACTS.map((a) => <Stat key={a} label={`Act ${a} · level ${row.levels[a]}`} value={num(row.damage[view]?.[a])} detail={`AC ${row.ac[a] ?? '–'} · score ${num(row.score[a], 0)}`} />)}
        </SimpleGrid>
        <Section title="Damage by scenario">
          <Plot figure={figure} height={300} />
        </Section>
        {row.gear_changes && <Section title="Gear that changes from the planned build"><Text size="sm">{row.gear_changes}</Text></Section>}
        <Section title="Build"><Text size="sm">{row.spec}</Text></Section>
        <Section title="Notes">
          <Stack gap={4}>
            {ACTS.map((a) => <Text key={a} size="xs">Act {a}: advantage {row.advantage_source[a] ? `from ${row.advantage_source[a]}` : 'only from outside help'}
              {row.area?.[view]?.[a] ? `; against groups it uses ${row.area[view][a]}` : ''}</Text>)}
          </Stack>
        </Section>
      </Stack>
    </Drawer>
  )
}
