import {
  Badge, Button, Center, Chip, Drawer, Grid, Group, Loader, Popover, SegmentedControl, Select, SimpleGrid, Stack, Switch, Text, TextInput,
} from '@mantine/core'
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
import { useUrlList, useUrlState } from '../../urlState'

const SOURCE_COLORS: Record<string, string> = { 'Your party': '#FFD23F', Preset: '#636EFA', 'Build doc': '#00CC96', 'Reddit (approx.)': '#EF553B' }
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
        <span style={{ width: 8, height: 8, borderRadius: 4, background: SOURCE_COLORS[r.source], flexShrink: 0 }} />
        <Text size="xs" fw={r.source === 'Your party' ? 700 : 400} truncate maw={280}>{r.name}</Text>
        {r.variant !== 'planned' && <Badge size="xs" variant="light">{VARIANT_SHORT[r.variant]}</Badge>}
      </Group>
    ) },
    { id: 'Source', header: 'Source', accessorFn: (r) => r.source },
    ...ACTS.map((a): ColumnDef<Row, unknown> => ({ id: `Act ${a}`, header: `Act ${a}`, accessorFn: (r) => r.d[a] ?? null, sortUndefined: 'last',
      cell: ({ row: { original: r } }) => <span>{num(r.d[a])} <Text span size="xs" c="dimmed">#{r.rank[a]}</Text></span> })),
    { id: 'Overall', header: 'Overall', accessorFn: (r) => r.overall },
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
  ], [compareId, comparison, view])

  if (!options.data || !entries.data) return <Center h={300}><Loader /></Center>
  const scenarioInfo = options.data.scenarios.find((s) => s.key === scenario)
  const leader = [...rows].sort((a, b) => b.overall - a.overall)[0]
  const bestIn = (a: string) => [...rows].sort((x, y) => (y.d[a] ?? 0) - (x.d[a] ?? 0))[0]

  const scatter = {
    data: options.data.sources.filter((s) => sources.includes(s)).map((source) => {
      const pts = rows.filter((r) => r.source === source && r.d[chartAct] !== null && r.ac[chartAct] !== null)
      return {
        type: 'scatter', mode: 'markers', name: source,
        x: pts.map((r) => (r.ac[chartAct] ?? 0) + ((r.fingerprint.charCodeAt(0) % 7) - 3) * 0.06), y: pts.map((r) => r.d[chartAct]),
        text: pts.map((r) => `${r.name}${r.variant !== 'planned' ? ` (${VARIANT_SHORT[r.variant]})` : ''}<br>AC ${r.ac[chartAct]}, score ${num(r.score[chartAct], 0)}`),
        hovertemplate: '%{text}<br>%{y:.1f} damage per round<extra></extra>',
        marker: { color: SOURCE_COLORS[source], size: pts.map((r) => 6 + (r.score[chartAct] ?? 0) / 6), opacity: 0.85,
          line: { width: source === 'Your party' ? 2 : 0.5, color: source === 'Your party' ? '#888' : 'rgba(0,0,0,0.4)' } },
      }
    }),
    layout: chartLayout({ xaxis: { title: { text: 'Armour class' } }, yaxis: { title: { text: 'Damage per round' } }, margin: { l: 55, r: 10, t: 10, b: 40 } }),
  }

  return (
    <>
      <PageHeader title="Leaderboard"
        subtitle={`${rows.length} builds under the same conditions: ${Object.values(options.data.referenceEnemies).join(', ')}, ${options.data.roundsPerFight} round fights`}
        actions={<>
          <Select size="xs" placeholder="Compare with a saved run" clearable w={260} value={compareId} onChange={setCompareId}
            data={(runs.data ?? []).map((r) => ({ value: String(r.id), label: `#${r.id} ${r.created.slice(0, 16).replace('T', ' ')} · ${r.label || r.kind} (${r.count})` }))} />
          <Popover width={280} position="bottom-end" withArrow>
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
          </Popover>
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
              <Group gap={4}>{options.data.sources.map((s) => <Chip key={s} value={s} size="xs" color={SOURCE_COLORS[s]}>{s}</Chip>)}</Group>
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
            <Text size="xs" c="dimmed" mt={-6}>Up is more damage, right is harder to hit. Bigger dots have a higher overall score.</Text>
            <Plot figure={scatter} height={430} />
          </Section>
        </Grid.Col>
        <Grid.Col span={{ base: 12, lg: 7 }}>
          <Section title="Rankings">
            <SortTable title="Leaderboard" data={rows} columns={columns} initialSorting={[{ id: 'Overall', desc: true }]} hidden={['Source', 'Fingerprint', 'Score 1', 'Score 2']}
              onRowClick={setOpen} maxHeight={480}
              rowStyle={(r) => (r.source === 'Your party' ? { background: 'rgba(255,210,63,0.08)' } : undefined)} />
          </Section>
        </Grid.Col>
      </Grid>

      <BuildDrawer row={open} view={view} scenarios={options.data.scenarios} enemies={enemies} onClose={() => setOpen(null)} />
    </>
  )
}

function BuildDrawer({ row, view, scenarios, enemies, onClose }: { row: Row | null; view: string; scenarios: { key: string; label: string }[]; enemies: string; onClose: () => void }) {
  if (!row) return <Drawer opened={false} onClose={onClose} />
  const figure = {
    data: scenarios.map((s) => ({ type: 'bar', name: s.label, x: ACTS.map((a) => `Act ${a}`), y: ACTS.map((a) => row.damage[`${s.key}@${enemies}`]?.[a] ?? null),
      hovertemplate: `${s.label}: %{y:.1f}<extra></extra>` })),
    layout: chartLayout({ barmode: 'group', yaxis: { title: { text: 'Damage per round' } }, margin: { l: 50, r: 10, t: 10, b: 30 }, legend: { orientation: 'h', y: -0.15, font: { size: 10 } } }),
  }
  return (
    <Drawer opened onClose={onClose} position="right" size="lg" title={<Text fw={600}>{row.name}</Text>}>
      <Stack gap="md">
        <Group gap="xs">
          <Badge variant="light" color={SOURCE_COLORS[row.source]}>{row.source}</Badge>
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
