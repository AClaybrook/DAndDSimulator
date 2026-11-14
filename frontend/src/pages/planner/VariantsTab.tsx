import { ActionIcon, Button, Checkbox, Group, MultiSelect, SegmentedControl, Select, Stack, Table, Text, TextInput, Tooltip } from '@mantine/core'
import { IconCheck, IconPlus, IconTrash } from '@tabler/icons-react'
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { bg3, type PlannerOptions } from '../../api'
import { Section } from '../../components/Layout'
import { Plot } from '../../components/Plot'
import { chartLayout } from '../../format'
import { ACTS, useParty } from '../../party'
import { colorAt, useColors } from '../../theme'
import { useSharedEnemy } from './usePlanner'

const MAX_LINES = 8 // One colour slot per line

// What ifs: another way to play the character (a different cantrip or spell), a kit, buffs or advantage on top of its own gear, compared
// side by side. They never change the character until "Use"
export function VariantsTab({ options, attackBonus }: { options: PlannerOptions; attackBonus: number }) {
  const { party, selected, update, replace, enemies, together } = useParty()
  const build = party[selected]
  const { enemy, rounds } = useSharedEnemy()
  const [name, setName] = useState('')
  const [kit, setKit] = useState<string | null>(null)
  const [buffs, setBuffs] = useState<string[]>([])
  const [advantage, setAdvantage] = useState(false)
  const [act, setAct] = useState('3')
  const [mode, setMode] = useState<{ routine: string | null; cantrip: string | null; spell: string | null; guardians: boolean }>({ routine: null, cantrip: null, spell: null, guardians: false })
  const colors = useColors()
  const rows = useQuery({
    queryKey: ['variants', build, enemy, rounds, enemies, attackBonus, together && party],
    queryFn: () => bg3.variants(build, enemy, rounds, enemies, attackBonus, party, together),
    enabled: Boolean(build && enemy), placeholderData: (p) => p,
  })
  if (!build) return null
  const addVariant = (variant: Record<string, unknown>) => update(selected, (b) => ({ ...b, variants: [...b.variants, variant] }))
  const remove = (i: number) => update(selected, (b) => ({ ...b, variants: b.variants.filter((_, j) => j !== i) }))
  const use = async (i: number) => replace(selected, await bg3.useVariant(build, i))
  const base = rows.data?.[0]
  const character = build.character
  const cleric = character?.classes.some((c) => c[0] === 'cleric')
  const addMode = () => {
    const changes = Object.fromEntries(Object.entries({ routine: mode.routine, cantrip: mode.cantrip, spell: mode.spell }).filter(([, v]) => v))
    addVariant({ name: name || [mode.spell, mode.cantrip, options.builder.routines.find((r) => r.value === mode.routine)?.label].filter(Boolean).join(' + ') || 'Spirit Guardians first',
      character: changes, toggles: mode.guardians ? { spirit_guardians: true } : {} })
    setName(''); setMode({ routine: null, cantrip: null, spell: null, guardians: false })
  }
  // The picture: each way to play against one to four enemies, as the gain over the build as planned (the ways sit within a few points
  // of each other, and a single target spell and an area spell trade places as enemies are added)
  const actIndex = ACTS.indexOf(act)
  const drawn = (rows.data ?? []).slice(0, MAX_LINES)
  const planned = drawn[0]?.byEnemies[actIndex] ?? []
  const figure = {
    data: drawn.map((r, i) => ({
      type: 'scatter', mode: 'lines+markers', name: r.name, x: [1, 2, 3, 4], y: r.byEnemies[actIndex].map((d, n) => d - planned[n]),
      customdata: r.byEnemies[actIndex], line: { color: colorAt(colors, i), width: i === 0 ? 3.5 : 2 }, marker: { size: i === 0 ? 6 : 8, color: colorAt(colors, i) },
      hovertemplate: i === 0 ? `${r.name}: %{customdata:.1f}<extra></extra>` : `${r.name}: %{y:+.1f} (%{customdata:.1f})<extra></extra>`,
    })),
    layout: chartLayout({ margin: { l: 50, r: 12, t: 8, b: 34 }, hovermode: 'x unified', showlegend: true,
      xaxis: { dtick: 1, title: { text: 'Enemies in reach' } }, yaxis: { title: { text: 'Gain per round' }, tickformat: '+' },
      legend: { orientation: 'h', y: -0.3, font: { size: 11 } } }),
  }

  return (
    <Stack gap="md">
      {drawn.length > 1 && (
        <Section padding="sm" title={<Text fw={600}>Ways to play <Text span size="xs" c="dimmed" fw={400}>· gain over the build as planned, by enemies in reach</Text></Text>}
          actions={<SegmentedControl size="xs" value={act} onChange={setAct} data={ACTS.map((a) => ({ value: a, label: `Act ${a}` }))} />}>
          <Plot figure={figure} height={260} />
        </Section>
      )}
      <Section title="Add a variant" padding="sm">
        <Group gap={6}>
          <Text size="xs" c="dimmed">Quick:</Text>
          {options.quickVariants.map((v) => (
            <Button key={v.key} size="compact-xs" variant="light" onClick={() => addVariant({ ...v })}>{v.name}</Button>
          ))}
        </Group>
        <Group gap="xs" align="flex-end" wrap="wrap">
          <TextInput size="xs" label="Name" placeholder="optional" w={140} value={name} onChange={(e) => setName(e.currentTarget.value)} />
          <Select size="xs" label="Kit" placeholder="No kit" clearable w={200} value={kit} onChange={setKit} data={options.kits.map((k) => ({ value: k.key, label: k.name }))} />
          <MultiSelect size="xs" label="Buffs" placeholder="None" w={220} value={buffs} onChange={setBuffs} searchable data={options.buffs.map((b) => ({ value: b.key, label: b.name }))} />
          <Checkbox size="xs" label="Advantage" checked={advantage} onChange={(e) => setAdvantage(e.currentTarget.checked)} mb={6} />
          <Button size="xs" leftSection={<IconPlus size={14} />} disabled={!kit && !buffs.length && !advantage} onClick={() => {
            addVariant({ name: name || options.kits.find((k) => k.key === kit)?.name || 'Variant', kit, buffs, toggles: advantage ? { advantage: true } : {} })
            setName(''); setKit(null); setBuffs([]); setAdvantage(false)
          }}>Add</Button>
        </Group>
        {character && (
          <Group gap="xs" align="flex-end" wrap="wrap">
            <Select size="xs" label="Play mode: routine" placeholder="Same" clearable w={150} data={options.builder.routines} value={mode.routine} onChange={(v) => setMode({ ...mode, routine: v })} />
            <Select size="xs" label="Cantrip" placeholder="Same" clearable searchable w={150} data={options.builder.cantrips} value={mode.cantrip} onChange={(v) => setMode({ ...mode, cantrip: v })} />
            <Select size="xs" label="Levelled spell" placeholder="Same" clearable searchable w={170} data={options.builder.spells} value={mode.spell} onChange={(v) => setMode({ ...mode, spell: v })} />
            {cleric && (
              <Tooltip label="Cast Spirit Guardians in round 1 and keep it up, then the mode's own spells">
                <Checkbox size="xs" label="After Spirit Guardians" checked={mode.guardians} onChange={(e) => setMode({ ...mode, guardians: e.currentTarget.checked })} mb={6} />
              </Tooltip>
            )}
            <Button size="xs" variant="light" leftSection={<IconPlus size={14} />} disabled={!mode.routine && !mode.cantrip && !mode.spell && !mode.guardians} onClick={addMode}>Add mode</Button>
          </Group>
        )}
      </Section>
      <Table.ScrollContainer minWidth={600}>
        <Table fz="xs" className="numeric" highlightOnHover striped>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Variant{enemies > 1 ? ` · vs ${enemies} enemies` : ''}</Table.Th>
              {ACTS.map((a) => <Table.Th key={a}>Act {a}</Table.Th>)}
              <Table.Th>Spell DC</Table.Th>
              <Table.Th>AC by act</Table.Th>
              <Table.Th>Score by act</Table.Th>
              <Table.Th />
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {(rows.data ?? []).map((r, i) => (
              <Table.Tr key={i}>
                <Table.Td><Text size="xs" fw={i === 0 ? 600 : 400}>{r.name}</Text><Text size="10px" c="dimmed">{r.description}</Text></Table.Td>
                {r.damage.map((d, a) => {
                  const delta = base && i > 0 ? d - base.damage[a] : 0
                  return <Table.Td key={a}>{d.toFixed(1)}{i > 0 && <Text span size="10px" c={delta > 0.05 ? 'teal' : delta < -0.05 ? 'red' : 'dimmed'}> {delta >= 0 ? '+' : ''}{delta.toFixed(1)}</Text>}</Table.Td>
                })}
                <Table.Td>{r.spellDc.some((d) => d != null) ? r.spellDc.map((d) => d ?? '–').join(' / ') : '–'}</Table.Td>
                <Table.Td>{r.ac.join(' / ')}</Table.Td>
                <Table.Td>{r.score.map((s) => s.toFixed(0)).join(' / ')}</Table.Td>
                <Table.Td>
                  {i > 0 && (
                    <Group gap={2} wrap="nowrap">
                      <Tooltip label="Play the character this way"><ActionIcon size="sm" variant="subtle" aria-label="Use variant" onClick={() => use(i - 1)}><IconCheck size={14} /></ActionIcon></Tooltip>
                      <Tooltip label="Delete"><ActionIcon size="sm" variant="subtle" color="red" aria-label="Delete variant" onClick={() => remove(i - 1)}><IconTrash size={14} /></ActionIcon></Tooltip>
                    </Group>
                  )}
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      </Table.ScrollContainer>
    </Stack>
  )
}
