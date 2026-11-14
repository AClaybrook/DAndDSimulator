import { ActionIcon, Badge, Button, Group, SegmentedControl, Stack, Switch, Table, Text, Tooltip } from '@mantine/core'
import { IconCheck, IconPlaylistAdd } from '@tabler/icons-react'
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { bg3, type Build } from '../../api'
import type { FrontierPoint } from '../../api-types'
import { Section } from '../../components/Layout'
import { Plot } from '../../components/Plot'
import { chartLayout } from '../../format'
import { ACTS, useParty } from '../../party'
import { colorAt, useColors } from '../../theme'
import { useSharedEnemy } from './usePlanner'

const SLOT_LABEL: Record<string, string> = { armour: 'Armour', gloves: 'Gloves', helmet: 'Helmet', cloak: 'Cloak', boots: 'Boots', ring_1: 'Ring', ring_2: 'Ring', amulet: 'Amulet', elixir: 'Elixir', coating: 'Coating' }
const describe = (p: FrontierPoint) => p.changes.length ? p.changes.map((c) => `${SLOT_LABEL[c.slot] ?? c.slot}: ${c.name}`).join(', ') : 'Gear as planned'

// The point's gear and elixir on the build at the act (an elixir replaces the one it drinks now)
function withPoint(build: Build, act: string, p: FrontierPoint): Build {
  const gear = Object.fromEntries(p.changes.filter((c) => c.slot !== 'elixir' && c.slot !== 'coating').map((c) => [c.slot, c.key]))
  let list = build.buffs[act] ?? []
  for (const [slot, prefix] of [['elixir', 'elixir:'], ['coating', 'coat:']] as const) {
    const change = p.changes.find((c) => c.slot === slot)
    if (change) list = [...list.filter((b) => !b.startsWith(prefix)), ...(change.key ? [change.key] : [])]
  }
  const buffs = { ...build.buffs, [act]: list }
  return { ...build, equipment: { ...build.equipment, [act]: { ...(build.equipment[act] ?? {}), ...gear } }, buffs }
}

const variantOf = (act: string, p: FrontierPoint) => ({
  name: `AC ${p.ac}: ${describe(p)}`,
  gear: { [act]: Object.fromEntries(p.changes.filter((c) => c.slot !== 'elixir' && c.slot !== 'coating').map((c) => [c.slot, c.key])) },
  buffs: p.changes.filter((c) => (c.slot === 'elixir' || c.slot === 'coating') && c.key).map((c) => c.key),
})

// Gear solver: every gear and elixir combination it tried, damage against armour class, and the Pareto frontier (nothing else has both
// more damage and at least the AC). Use a point, or keep the frontier as variants to compare and rank
export function FrontierTab() {
  const { party, selected, update, enemies, together } = useParty()
  const build = party[selected]
  const { enemy, rounds } = useSharedEnemy()
  const [act, setAct] = useState('3')
  const [skipTaken, setSkipTaken] = useState(true)
  const colors = useColors()
  const result = useQuery({
    queryKey: ['frontier', build, act, enemy, rounds, enemies, skipTaken, together && party],
    queryFn: () => bg3.frontier(build, act, enemy, rounds, enemies, party, selected, skipTaken, together),
    enabled: Boolean(build && enemy), placeholderData: (p) => p, staleTime: Infinity,
  })
  if (!build) return null
  const data = result.data
  const frontier = (data?.points ?? []).filter((p) => p.frontier).sort((a, b) => b.ac - a.ac)
  const rest = (data?.points ?? []).filter((p) => !p.frontier)
  const hover = (p: FrontierPoint) => `AC ${p.ac} · ${p.damage.toFixed(1)} a round<br>${describe(p).replaceAll(', ', '<br>')}${p.drawbacks.length ? `<br>⚠ ${p.drawbacks.join('; ')}` : ''}`
  const figure = data && {
    data: [
      { type: 'scatter', mode: 'markers', name: 'Tried', x: rest.map((p) => p.ac), y: rest.map((p) => p.damage), text: rest.map(hover),
        hovertemplate: '%{text}<extra></extra>', marker: { size: 6, color: 'rgba(140,140,160,0.35)' } },
      { type: 'scatter', mode: 'lines+markers', name: 'Frontier', x: frontier.map((p) => p.ac), y: frontier.map((p) => p.damage), text: frontier.map(hover),
        hovertemplate: '%{text}<extra></extra>', line: { color: colorAt(colors, 0), width: 2, shape: 'hv' }, marker: { size: 10, color: colorAt(colors, 0) } },
      { type: 'scatter', mode: 'markers', name: 'As planned', x: [data.current.ac], y: [data.current.damage], text: [hover(data.current)],
        hovertemplate: '%{text}<extra></extra>', marker: { size: 16, symbol: 'star', color: colorAt(colors, 1) } },
    ],
    layout: chartLayout({ margin: { l: 54, r: 12, t: 8, b: 40 }, showlegend: true, legend: { orientation: 'h', y: -0.22 },
      xaxis: { title: { text: 'Armour class' }, dtick: 1 }, yaxis: { title: { text: `Damage per round${enemies > 1 ? ` (${enemies} enemies)` : ''}` } } }),
  }
  const use = (p: FrontierPoint) => update(selected, (b) => withPoint(b, act, p))
  const keep = (points: FrontierPoint[]) => update(selected, (b) => ({ ...b, variants: [...b.variants, ...points.filter((p) => p.changes.length).map((p) => variantOf(act, p))] }))

  return (
    <Stack gap="md">
      <Section padding="sm" title={<Text fw={600}>Damage vs armour class <Text span size="xs" c="dimmed" fw={400}>· {data ? `${data.points.length} combinations of gear and elixir` : 'searching...'}</Text></Text>}
        actions={<Group gap="xs">
          <Tooltip label="Leave out unique items the rest of the party wears"><Switch size="xs" label="Skip teammates' items" checked={skipTaken} onChange={(e) => setSkipTaken(e.currentTarget.checked)} /></Tooltip>
          <SegmentedControl size="xs" value={act} onChange={setAct} data={ACTS.map((a) => ({ value: a, label: `Act ${a}` }))} />
        </Group>}>
        {figure ? <Plot figure={figure} height={300} /> : <Text size="sm" c="dimmed">Searching (a second or two)...</Text>}
      </Section>
      <Group justify="space-between">
        <Text size="xs" c="dimmed">The frontier: no other combination has more damage at the same or higher AC. Weapons stay as planned</Text>
        <Button size="xs" variant="light" leftSection={<IconPlaylistAdd size={14} />} disabled={!frontier.length} onClick={() => keep(frontier)}>Keep all as variants</Button>
      </Group>
      <Table.ScrollContainer minWidth={560}>
        <Table fz="xs" className="numeric" highlightOnHover striped>
          <Table.Thead>
            <Table.Tr><Table.Th>AC</Table.Th><Table.Th>Damage</Table.Th><Table.Th>Changes from the planned gear</Table.Th><Table.Th /></Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {frontier.map((p, i) => {
              const delta = data ? p.damage - data.current.damage : 0
              return (
                <Table.Tr key={i}>
                  <Table.Td>{p.ac}{data && p.ac !== data.current.ac && <Text span size="10px" c={p.ac > data.current.ac ? 'teal' : 'red'}> {p.ac > data.current.ac ? '+' : ''}{p.ac - data.current.ac}</Text>}</Table.Td>
                  <Table.Td>{p.damage.toFixed(1)}<Text span size="10px" c={delta > 0.05 ? 'teal' : delta < -0.05 ? 'red' : 'dimmed'}> {delta >= 0 ? '+' : ''}{delta.toFixed(1)}</Text></Table.Td>
                  <Table.Td>
                    <Text size="xs">{describe(p)}</Text>
                    {p.drawbacks.map((d) => <Badge key={d} size="xs" color="orange" variant="light">{d}</Badge>)}
                  </Table.Td>
                  <Table.Td>
                    <Group gap={2} wrap="nowrap">
                      <Tooltip label={`Wear this at Act ${act}`}><ActionIcon size="sm" variant="subtle" aria-label="Use" disabled={!p.changes.length} onClick={() => use(p)}><IconCheck size={14} /></ActionIcon></Tooltip>
                      <Tooltip label="Keep as a variant (Variants tab, and the leaderboard's saved variants)"><ActionIcon size="sm" variant="subtle" aria-label="Keep as variant" disabled={!p.changes.length} onClick={() => keep([p])}><IconPlaylistAdd size={14} /></ActionIcon></Tooltip>
                    </Group>
                  </Table.Td>
                </Table.Tr>
              )
            })}
          </Table.Tbody>
        </Table>
      </Table.ScrollContainer>
    </Stack>
  )
}
