import { Group, Select, SimpleGrid, Stack, Text } from '@mantine/core'
import { useQuery } from '@tanstack/react-query'
import type { ColumnDef } from '@tanstack/react-table'
import { useState } from 'react'
import { bg3, type Advice, type PlannerOptions } from '../../api'
import { SortTable } from '../../components/DataTable'
import { Section } from '../../components/Layout'
import { ACTS, useParty } from '../../party'
import { useSharedEnemy } from './usePlanner'

type Value = Advice['values'][number]
type Suggestion = Advice['suggestions'][number]
const gain = (g: number) => `${g >= 0 ? '+' : ''}${g.toFixed(2)}`

const valueColumns: ColumnDef<Value, unknown>[] = [
  { id: 'Slot', header: 'Slot', accessorFn: (r) => r.slot },
  { id: 'Item', header: 'Item', accessorFn: (r) => r.item, cell: ({ row }) => <span title={row.original.summary}>{row.original.item}</span> },
  { id: 'Adds', header: 'Adds', accessorFn: (r) => r.gain, cell: (c) => gain(c.getValue() as number) },
]
const suggestionColumns: ColumnDef<Suggestion, unknown>[] = [
  { id: 'Item', header: 'Item', accessorFn: (r) => r.item, cell: ({ row }) => <span title={row.original.summary}>{row.original.item}</span> },
  { id: 'Adds', header: 'Adds', accessorFn: (r) => r.gain, cell: (c) => gain(c.getValue() as number) },
  { id: 'Found', header: 'Found', accessorFn: (r) => r.act ?? 9, cell: ({ row }) => (row.original.act ? `Act ${row.original.act}` : 'Act ?') },
  { id: 'Clashes', header: 'Used by or clashes with', accessorFn: (r) => r.users.join(', '), cell: (c) => <Text span size="xs" c="yellow">{String(c.getValue())}</Text> },
]

// What each worn item adds, and the best items for a slot, at an act
export function AdviceTab({ options }: { options: PlannerOptions }) {
  const { party, selected } = useParty()
  const { enemy, rounds } = useSharedEnemy()
  const [act, setAct] = useState('1')
  const [slot, setSlot] = useState('melee_main')
  const build = party[selected]
  const advice = useQuery({
    queryKey: ['advice', build, party, act, slot, enemy, rounds],
    queryFn: () => bg3.advice(build, party, act, slot, enemy, rounds),
    enabled: Boolean(build && enemy), placeholderData: (p) => p,
  })
  if (!build) return null
  return (
    <Stack gap="md">
      <Group gap="xs">
        <Select size="xs" label="At" w={110} value={act} onChange={(v) => v && setAct(v)} allowDeselect={false} data={ACTS.map((a) => ({ value: a, label: `Act ${a}` }))} />
        <Select size="xs" label="Best items for" w={200} value={slot} onChange={(v) => v && setSlot(v)} allowDeselect={false}
          data={options.slots.filter((s) => s.key !== 'ring_2').map((s) => ({ value: s.key, label: s.label }))} />
      </Group>
      <SimpleGrid cols={{ base: 1, xl: 2 }}>
        <Section title="What each item adds" padding="sm">
          <Text size="xs" c="dimmed">Damage per round each worn item adds, compared to an empty slot.</Text>
          <SortTable data={advice.data?.values ?? []} columns={valueColumns} initialSorting={[{ id: 'Adds', desc: true }]} filterable={false} title="Item values" />
        </Section>
        <Section title="Best items for the slot" padding="sm">
          <SortTable data={advice.data?.suggestions ?? []} columns={suggestionColumns} initialSorting={[{ id: 'Adds', desc: true }]} filterable={false} title="Item suggestions" />
        </Section>
      </SimpleGrid>
    </Stack>
  )
}
