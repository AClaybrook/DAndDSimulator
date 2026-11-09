import { ActionIcon, Button, Checkbox, Group, MultiSelect, Select, Stack, Table, Text, TextInput, Tooltip } from '@mantine/core'
import { IconCheck, IconPlus, IconTrash } from '@tabler/icons-react'
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { bg3, type PlannerOptions } from '../../api'
import { Section } from '../../components/Layout'
import { ACTS, useParty } from '../../party'
import { useSharedEnemy } from './usePlanner'

// What ifs: a kit, buffs or advantage on top of the character's own gear, compared side by side. They never change the gear until "Use"
export function VariantsTab({ options, attackBonus }: { options: PlannerOptions; attackBonus: number }) {
  const { party, selected, update, replace, enemies } = useParty()
  const build = party[selected]
  const { enemy, rounds } = useSharedEnemy()
  const [name, setName] = useState('')
  const [kit, setKit] = useState<string | null>(null)
  const [buffs, setBuffs] = useState<string[]>([])
  const [advantage, setAdvantage] = useState(false)
  const rows = useQuery({
    queryKey: ['variants', build, enemy, rounds, enemies, attackBonus],
    queryFn: () => bg3.variants(build, enemy, rounds, enemies, attackBonus),
    enabled: Boolean(build && enemy), placeholderData: (p) => p,
  })
  if (!build) return null
  const addVariant = (variant: Record<string, unknown>) => update(selected, (b) => ({ ...b, variants: [...b.variants, variant] }))
  const remove = (i: number) => update(selected, (b) => ({ ...b, variants: b.variants.filter((_, j) => j !== i) }))
  const use = async (i: number) => replace(selected, await bg3.useVariant(build, i))
  const base = rows.data?.[0]

  return (
    <Stack gap="md">
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
      </Section>
      <Table.ScrollContainer minWidth={600}>
        <Table fz="xs" className="numeric" highlightOnHover striped>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Variant</Table.Th>
              {ACTS.map((a) => <Table.Th key={a}>Act {a}</Table.Th>)}
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
                <Table.Td>{r.ac.join(' / ')}</Table.Td>
                <Table.Td>{r.score.map((s) => s.toFixed(0)).join(' / ')}</Table.Td>
                <Table.Td>
                  {i > 0 && (
                    <Group gap={2} wrap="nowrap">
                      <Tooltip label="Use as the character's gear"><ActionIcon size="sm" variant="subtle" onClick={() => use(i - 1)}><IconCheck size={14} /></ActionIcon></Tooltip>
                      <Tooltip label="Delete"><ActionIcon size="sm" variant="subtle" color="red" onClick={() => remove(i - 1)}><IconTrash size={14} /></ActionIcon></Tooltip>
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
