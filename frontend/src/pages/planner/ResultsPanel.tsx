import { Badge, Checkbox, Group, NumberInput, Select, SimpleGrid, Stack, Table, Tabs, Text, Tooltip } from '@mantine/core'
import { useDebouncedValue } from '@mantine/hooks'
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { bg3, type Evaluation, type PlannerOptions } from '../../api'
import { Section, Stat } from '../../components/Layout'
import { chartLayout } from '../../format'
import { Plot } from '../../components/Plot'
import { ACTS, useParty } from '../../party'
import { COLORS } from '../../store'
import { useSharedEnemy } from './usePlanner'

// Results: the party's damage across the acts first, then conflicts and how the party works together
export function ResultsPanel({ options, evaluation }: { options: PlannerOptions; evaluation: Evaluation | undefined }) {
  const { party, selected, enemies } = useParty()
  const conflicts = evaluation?.conflicts ?? []
  const member = evaluation?.members[selected]
  const figure = {
    data: (evaluation?.members ?? []).map((m, i) => ({
      type: 'scatter', mode: 'lines+markers', name: m.name, x: ACTS.map((a) => `Act ${a}`), y: ACTS.map((a) => m.acts[a].damage[enemies - 1]),
      customdata: ACTS.map((a) => m.acts[a].level), line: { color: COLORS[i % COLORS.length], width: i === selected ? 4 : 2 },
      marker: { size: 9 }, hovertemplate: `${m.name}<br>%{x} (level %{customdata}): %{y:.1f} damage per round<extra></extra>`,
    })),
    layout: chartLayout({ margin: { l: 45, r: 10, t: 10, b: 30 }, yaxis: { rangemode: 'tozero', title: { text: 'Damage per round' } }, showlegend: false }),
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
          <Plot figure={figure} height={260} />
          {member && (
            <>
              <Text size="sm" fw={600}>{member.name}</Text>
              <SimpleGrid cols={3} spacing="xs">
                {ACTS.map((a) => {
                  const r = member.acts[a]
                  return (
                    <Stat key={a} label={`Act ${a} · level ${r.level}`} value={r.damage[enemies - 1].toFixed(1)}
                      detail={<Tooltip multiline w={300} label={r.acParts.map((p) => `${p.source} ${p.value}`).join(' + ')}><span>AC {r.ac} · hit {Math.round(100 * r.hitChance)}%</span></Tooltip>} />
                  )
                })}
              </SimpleGrid>
              <Section title="Overall score" padding="sm">
                <Table fz="xs" className="numeric">
                  <Table.Thead><Table.Tr><Table.Th />{ACTS.map((a) => <Table.Th key={a}>Act {a}</Table.Th>)}</Table.Tr></Table.Thead>
                  <Table.Tbody>
                    <Table.Tr><Table.Td fw={700}>Total</Table.Td>{ACTS.map((a) => <Table.Td key={a} fw={700}>{member.acts[a].score.toFixed(0)}</Table.Td>)}</Table.Tr>
                    {Object.keys(options.partLabels).map((part) => (
                      <Table.Tr key={part}>
                        <Table.Td c="dimmed">{options.partLabels[part]} <Text span size="10px">×{options.scoreWeights[part]}</Text></Table.Td>
                        {ACTS.map((a) => <Table.Td key={a}><Tooltip label={member.acts[a].scoreNotes[part]} multiline w={260}><span>{member.acts[a].scoreParts[part]}</span></Tooltip></Table.Td>)}
                      </Table.Tr>
                    ))}
                  </Table.Tbody>
                </Table>
              </Section>
            </>
          )}
        </Stack>
      </Tabs.Panel>
      <Tabs.Panel value="conflicts">
        {!conflicts.length ? <Text size="sm" c="dimmed">No equipment conflicts.</Text> : (
          <Stack gap="xs">
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

function PartyAnalysisView({ options, count }: { options: PlannerOptions; count: number }) {
  const party = useParty((s) => s.party)
  const { enemy, rounds } = useSharedEnemy()
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
    data: [{ type: 'bar', x: a.fight.down_by_round.map((_, i) => i + 1), y: a.fight.down_by_round.map((p) => 100 * p), marker: { color: '#00CC96' },
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
        <Table fz="xs">
          <Table.Thead><Table.Tr><Table.Th>Role</Table.Th>{a.roles.map((m) => <Table.Th key={m.name}>{m.name.split(' (')[0]}</Table.Th>)}</Table.Tr></Table.Thead>
          <Table.Tbody>
            {roles.map((r) => (
              <Table.Tr key={r}>
                <Table.Td c={a.missing.includes(r) ? 'orange' : undefined}>{options.roleLabels[r]}</Table.Td>
                {a.roles.map((m) => <Table.Td key={m.name}><Tooltip label={m.roles[r] ?? ''} disabled={!m.roles[r]}><span>{m.roles[r] ? '✓' : ''}</span></Tooltip></Table.Td>)}
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
        {a.missing.length > 0 && <Text size="xs" c="orange">Nobody covers: {a.missing.map((r) => options.roleLabels[r]).join(', ')}</Text>}
        {a.overlaps.map((o) => <Text key={o} size="xs" c="dimmed">{o}</Text>)}
      </Section>
    </Stack>
  )
}
