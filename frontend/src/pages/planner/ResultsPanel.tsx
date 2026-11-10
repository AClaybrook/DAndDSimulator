import { Badge, Button, Checkbox, Collapse, Group, MultiSelect, NumberInput, Select, Stack, Table, Tabs, Text, Tooltip, UnstyledButton } from '@mantine/core'
import { useDebouncedValue, useMediaQuery } from '@mantine/hooks'
import { IconChevronDown, IconChevronRight, IconWand } from '@tabler/icons-react'
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { bg3, type Deconflict, type DeconflictStep, type Evaluation, type MemberResult, type PlannerOptions } from '../../api'
import { Section } from '../../components/Layout'
import { chartLayout, spread } from '../../format'
import { Plot } from '../../components/Plot'
import { ACTS, useParty } from '../../party'
import { colorAt, useColors } from '../../theme'
import { useSharedEnemy } from './usePlanner'

const MAX_LINES = 8 // One colour slot per line, so the party and the compared builds share eight

// Results: the party's damage across the acts first, then conflicts and how the party works together.
// The damage numbers themselves live on the party cards above; this panel is the picture and the detail behind them
export function ResultsPanel({ options, evaluation }: { options: PlannerOptions; evaluation: Evaluation | undefined }) {
  const { party, selected, enemies, attackBonus } = useParty()
  const colors = useColors()
  const conflicts = evaluation?.conflicts ?? []
  const member = evaluation?.members[selected]
  const { enemy, rounds } = useSharedEnemy()
  // Example builds drawn next to the party (dashed), each evaluated on its own against the same enemy
  const [compare, setCompare] = useState<string[]>([])
  const compared = useQuery({
    queryKey: ['compare', compare, enemy, rounds, attackBonus],
    queryFn: async () => {
      const builds = await Promise.all(compare.map((name) => bg3.example(name)))
      return (await Promise.all(builds.map((b) => bg3.evaluate([b], enemy, rounds, attackBonus)))).map((e) => e.members[0])
    },
    enabled: compare.length > 0 && Boolean(enemy),
    placeholderData: (previous) => previous,
  })
  // A name short enough to sit beside the line: 'Light Cleric: Spirit Guardians + ...' -> 'Light Cleric'
  const short = (name: string) => { const s = name.split(' (')[0].split(':')[0]; return s.length > 20 ? `${s.slice(0, 19)}…` : s }
  const line = (m: MemberResult, color: string, width: number, dash?: string) => ({
    type: 'scatter', mode: 'lines+markers', name: m.name, x: ACTS.map((a) => `Act ${a}`), y: ACTS.map((a) => m.acts[a].damage[enemies - 1]),
    customdata: ACTS.map((a) => m.acts[a].level), line: { color, width, dash }, marker: { size: dash ? 6 : 8, color },
    hovertemplate: `${m.name} (level %{customdata}): %{y:.1f}<extra></extra>`,
  })
  const members = evaluation?.members ?? []
  const others = compare.length ? (compared.data ?? []) : []
  const lines = [...members.map((m, i) => ({ m, i })), ...others.map((m, i) => ({ m, i: party.length + i }))]
  // A name at the end of each line while there are few enough to read; with more, the legend names them
  const last = ACTS[ACTS.length - 1]
  const ends = lines.map(({ m }) => m.acts[last].damage[enemies - 1])
  const top = Math.max(1, ...lines.flatMap(({ m }) => ACTS.map((a) => m.acts[a].damage[enemies - 1])))
  const narrow = useMediaQuery('(max-width: 48em)')
  const labels = lines.length <= 4 && !narrow ? spread(ends, top * 0.075).map((y, k) => ({
    x: `Act ${last}`, y, xanchor: 'left', xshift: 8, showarrow: false, text: short(lines[k].m.name), font: { size: 11, color: colorAt(colors, lines[k].i) },
  })) : []
  const figure = {
    data: [
      ...members.map((m, i) => line(m, colorAt(colors, i), i === selected ? 3.5 : 2)),
      ...others.map((m, i) => line(m, colorAt(colors, party.length + i), 2, 'dash')),
    ],
    layout: chartLayout({ margin: { l: 46, r: labels.length ? 110 : 12, t: 8, b: 30 }, hovermode: 'x unified', annotations: labels,
      yaxis: { rangemode: 'tozero', title: { text: `Damage per round${enemies > 1 ? `, ${enemies} enemies` : ''}` } },
      showlegend: labels.length === 0 && lines.length > 1, legend: { orientation: 'h', y: -0.16, font: { size: 11 } } }),
  }

  return (
    <Tabs defaultValue="damage" keepMounted={false}>
      <Tabs.List mb="sm">
        <Tabs.Tab value="damage">Damage</Tabs.Tab>
        <Tabs.Tab value="conflicts" rightSection={conflicts.length ? <Badge size="xs" color="orange">{conflicts.length}</Badge> : null}>Conflicts</Tabs.Tab>
        <Tabs.Tab value="party">Party</Tabs.Tab>
      </Tabs.List>
      <Tabs.Panel value="damage">
        <Stack gap="sm">
          <Plot figure={figure} height={lines.length > 4 ? 360 : 300} />
          <MultiSelect size="xs" searchable clearable placeholder="Compare with example builds..." data={options.examples.map((e) => e.name)}
            value={compare} onChange={setCompare} maxValues={Math.max(MAX_LINES - party.length, 0)} rightSection={compared.isFetching ? <Text size="10px" c="dimmed">…</Text> : undefined} />
          {member && <ScoreView member={member} options={options} />}
        </Stack>
      </Tabs.Panel>
      <Tabs.Panel value="conflicts">
        {!conflicts.length ? <Text size="sm" c="dimmed">No equipment conflicts.</Text> : (
          <Stack gap="xs">
            {conflicts.some((c) => c.kind === 'shared') && <Settle />}
            {ACTS.map((a) => conflicts.filter((c) => c.act === a)).map((list, i) => list.length > 0 && (
              <div key={i}>
                <Text size="xs" fw={600} c="dimmed" tt="uppercase">Act {ACTS[i]}</Text>
                {list.map((c, j) => (
                  <Text key={j} size="sm" c={['shared', 'story'].includes(c.kind) ? 'orange' : undefined}>
                    {c.message}{Object.keys(c.gains).length ? `. Adds ${Object.entries(c.gains).map(([n, g]) => `${n.split(' (')[0]} ${g >= 0 ? '+' : ''}${g.toFixed(1)}`).join(', ')}` : ''}
                  </Text>
                ))}
              </div>
            ))}
          </Stack>
        )}
      </Tabs.Panel>
      <Tabs.Panel value="party"><PartyAnalysisView options={options} count={party.length} /></Tabs.Panel>
    </Tabs>
  )
}

// Settles the items several characters wear: whoever gains the most damage from an item keeps it, the others get the best item for
// that slot nobody wears. Shown as a proposal first; each swap lists other options to pick instead
function Settle() {
  const { party, replace, update } = useParty()
  const { enemy, rounds } = useSharedEnemy()
  const [plan, setPlan] = useState<Deconflict | null>(null)
  const [busy, setBusy] = useState(false)
  const propose = async () => {
    setBusy(true)
    try { setPlan(await bg3.deconflict(party, enemy, rounds)) } finally { setBusy(false) }
  }
  const applyAll = () => {
    plan?.party.forEach((b, i) => replace(i, b))
    setPlan(null)
  }
  // One swap with another of its options: that member's slot at that act, the rest of the proposal untouched
  const pick = (step: DeconflictStep, key: string) => {
    const index = party.findIndex((b) => b.name === step.member)
    if (index >= 0) update(index, (b) => ({ ...b, equipment: { ...b.equipment, [step.act]: { ...(b.equipment[step.act] ?? {}), [step.slotKey]: key } } }))
    setPlan(null)
  }
  if (!plan) {
    return (
      <Group gap="xs">
        <Button size="xs" variant="light" leftSection={<IconWand size={14} />} loading={busy} onClick={propose}>Settle shared items</Button>
        <Text size="xs" c="dimmed">Proposes who keeps each contested item and what the others wear instead</Text>
      </Group>
    )
  }
  return (
    <Section padding="sm" title="Proposed swaps" actions={<>
      <Button size="compact-xs" onClick={applyAll}>Apply all</Button>
      <Button size="compact-xs" variant="default" onClick={() => setPlan(null)}>Cancel</Button>
    </>}>
      {plan.steps.map((s, i) => (
        <div key={i}>
          <Text size="sm">
            <Text span size="xs" c="dimmed">Act {s.act} · </Text><b>{s.item}</b> stays with {s.keeper.split(' (')[0]}. {s.member.split(' (')[0]}'s {s.slot.toLowerCase()}:{' '}
            {s.replacement ? <b>{s.replacement}</b> : 'left empty (nothing else found by this act adds damage)'}
            <Text span size="xs" c="dimmed"> · {s.cost >= 0 ? `gives up ${s.cost.toFixed(1)}` : `gains ${(-s.cost).toFixed(1)}`} a round</Text>
          </Text>
          {s.alternatives.length > 1 && (
            <Group gap={4} mt={2}>
              <Text size="xs" c="dimmed">Or:</Text>
              {s.alternatives.slice(1).map((a) => (
                <Tooltip key={a.key} label={`Wear ${a.item} there instead (+${a.gain.toFixed(1)} a round over an empty slot)`}>
                  <Button size="compact-xs" variant="default" onClick={() => pick(s, a.key)}>{a.item} +{a.gain.toFixed(1)}</Button>
                </Tooltip>
              ))}
            </Group>
          )}
        </div>
      ))}
      {plan.remaining > 0 && <Text size="xs" c="dimmed">{plan.remaining} other conflict{plan.remaining === 1 ? '' : 's'} (story choices, slots, concentration) are yours to decide.</Text>}
    </Section>
  )
}

// The selected character's all round score: one stacked bar per act (each part's share of the 0-100 total), the numbers on demand
function ScoreView({ member, options }: { member: MemberResult; options: PlannerOptions }) {
  const colors = useColors()
  const [open, setOpen] = useState(false)
  const parts = Object.keys(options.partLabels)
  const weightSum = parts.reduce((n, p) => n + options.scoreWeights[p], 0)
  const acts = [...ACTS].reverse() // Plotly draws the first category at the bottom
  const figure = {
    data: parts.map((part, i) => ({
      type: 'bar', orientation: 'h', name: options.partLabels[part], y: acts.map((a) => `Act ${a}`),
      x: acts.map((a) => (member.acts[a].scoreParts[part] * options.scoreWeights[part]) / weightSum),
      marker: { color: colorAt(colors, i), line: { color: 'rgba(0,0,0,0)', width: 0 } },
      customdata: acts.map((a) => [member.acts[a].scoreParts[part], options.scoreWeights[part], member.acts[a].scoreNotes[part]]),
      hovertemplate: `${options.partLabels[part]}: %{customdata[0]} of 100, weight %{customdata[1]}<br>%{customdata[2]}<extra></extra>`,
    })),
    layout: chartLayout({ barmode: 'stack', bargap: 0.35, margin: { l: 44, r: 40, t: 4, b: 28 }, xaxis: { range: [0, 100], dtick: 25 },
      legend: { orientation: 'h', y: -0.28, font: { size: 11 }, traceorder: 'normal' },
      annotations: acts.map((a) => ({ x: member.acts[a].score, y: `Act ${a}`, text: `<b>${member.acts[a].score.toFixed(0)}</b>`, showarrow: false, xanchor: 'left', xshift: 6 })) }),
  }
  return (
    <Section padding="sm" title={<Text fw={600}>Overall score <Text span size="xs" c="dimmed" fw={400}>· {member.name.split(' (')[0]}, 0 to 100</Text></Text>}>
      <Plot figure={figure} height={170} />
      <UnstyledButton onClick={() => setOpen((o) => !o)}>
        <Group gap={4}>{open ? <IconChevronDown size={14} /> : <IconChevronRight size={14} />}<Text size="xs" c="dimmed">The numbers, armour class and how each part is scored</Text></Group>
      </UnstyledButton>
      <Collapse expanded={open}>
        <Table fz="xs" className="numeric">
          <Table.Thead><Table.Tr><Table.Th />{ACTS.map((a) => <Table.Th key={a}>Act {a} · level {member.acts[a].level}</Table.Th>)}</Table.Tr></Table.Thead>
          <Table.Tbody>
            <Table.Tr><Table.Td fw={700}>Total</Table.Td>{ACTS.map((a) => <Table.Td key={a} fw={700}>{member.acts[a].score.toFixed(0)}</Table.Td>)}</Table.Tr>
            {parts.map((part) => (
              <Table.Tr key={part}>
                <Table.Td c="dimmed">{options.partLabels[part]} <Text span size="10px">×{options.scoreWeights[part]}</Text></Table.Td>
                {ACTS.map((a) => <Table.Td key={a}><Tooltip label={member.acts[a].scoreNotes[part]} multiline w={260}><span>{member.acts[a].scoreParts[part]}</span></Tooltip></Table.Td>)}
              </Table.Tr>
            ))}
            <Table.Tr>
              <Table.Td c="dimmed">Armour class</Table.Td>
              {ACTS.map((a) => (
                <Table.Td key={a}>
                  <Tooltip multiline w={300} label={member.acts[a].acParts.map((p) => `${p.source} ${p.value}`).join(' + ')}>
                    <span>{member.acts[a].ac} · hit {Math.round(100 * member.acts[a].hitChance)}%</span>
                  </Tooltip>
                </Table.Td>
              ))}
            </Table.Tr>
          </Table.Tbody>
        </Table>
      </Collapse>
    </Section>
  )
}

function PartyAnalysisView({ options, count }: { options: PlannerOptions; count: number }) {
  const party = useParty((s) => s.party)
  const { enemy, rounds } = useSharedEnemy()
  const colors = useColors()
  const [act, setAct] = useState('2')
  const [hp, setHp] = useState<number>(300)
  const [active, setActive] = useState<string[] | null>(null)
  const [key] = useDebouncedValue(JSON.stringify({ party, act, hp, active, enemy, rounds }), 300)
  const analysis = useQuery({
    queryKey: ['party', key], queryFn: () => bg3.party(party, act, active, enemy, rounds, hp), enabled: count > 0 && Boolean(enemy), placeholderData: (p) => p,
  })
  const a = analysis.data
  if (!a) return null
  const roles = Object.keys(options.roleLabels).filter((r) => options.coreRoles.includes(r) || a.roles.some((m) => r in m.roles))
  const fight = {
    data: [{ type: 'bar', x: a.fight.down_by_round.map((_, i) => i + 1), y: a.fight.down_by_round.map((p) => 100 * p), marker: { color: colorAt(colors, 2) },
      hovertemplate: 'Down by round %{x}: %{y:.0f}%<extra></extra>' }],
    layout: chartLayout({ margin: { l: 40, r: 10, t: 10, b: 35 }, yaxis: { range: [0, 100], title: { text: '% of fights' } }, xaxis: { title: { text: 'Enemy down by round' }, dtick: 1 } }),
  }
  return (
    <Stack gap="sm">
      <Group gap="xs">
        <Select size="xs" w={140} value={act} onChange={(v) => v && setAct(v)} allowDeselect={false} data={options.acts.map((x) => ({ value: x.key, label: x.label }))} />
        <NumberInput size="xs" w={150} leftSection={<Text size="10px">HP</Text>} value={hp} min={1} step={50} onChange={(v) => setHp(Number(v) || 300)} />
      </Group>
      <Section title="Party fight" padding="sm">
        <Text size="xs" c="dimmed">The whole party against the enemy with these hit points: chance it is down by each round. Median round {a.fight.median_round}.</Text>
        <Plot figure={fight} height={200} />
      </Section>
      <Section title="Synergies" padding="sm">
        {a.synergies.length ? a.synergies.map((s) => (
          <Checkbox key={s.key} size="xs" label={s.text} checked={a.active.includes(s.key)}
            onChange={() => setActive(a.active.includes(s.key) ? a.active.filter((k) => k !== s.key) : [...a.active, s.key])} />
        )) : <Text size="xs" c="dimmed">No synergies at this act.</Text>}
        <Table fz="xs" className="numeric">
          <Table.Thead><Table.Tr><Table.Th>Damage per round</Table.Th><Table.Th>Alone</Table.Th><Table.Th>With synergies</Table.Th></Table.Tr></Table.Thead>
          <Table.Tbody>{a.damage.map((d) => <Table.Tr key={d.name}><Table.Td>{d.name}</Table.Td><Table.Td>{d.alone.toFixed(1)}</Table.Td><Table.Td>{d.together.toFixed(1)}</Table.Td></Table.Tr>)}</Table.Tbody>
        </Table>
      </Section>
      <Section title="Roles" padding="sm">
        <Table.ScrollContainer minWidth={360}><Table fz="xs">
          <Table.Thead><Table.Tr><Table.Th>Role</Table.Th>{a.roles.map((m) => <Table.Th key={m.name}>{m.name.split(' (')[0]}</Table.Th>)}</Table.Tr></Table.Thead>
          <Table.Tbody>
            {roles.map((r) => (
              <Table.Tr key={r}>
                <Table.Td c={a.missing.includes(r) ? 'orange' : undefined}>{options.roleLabels[r]}</Table.Td>
                {a.roles.map((m) => <Table.Td key={m.name}><Tooltip label={m.roles[r] ?? ''} disabled={!m.roles[r]}><span>{m.roles[r] ? '✓' : ''}</span></Tooltip></Table.Td>)}
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table></Table.ScrollContainer>
        {a.missing.length > 0 && <Text size="xs" c="orange">Nobody covers: {a.missing.map((r) => options.roleLabels[r]).join(', ')}</Text>}
        {a.overlaps.map((o) => <Text key={o} size="xs" c="dimmed">{o}</Text>)}
      </Section>
    </Stack>
  )
}
