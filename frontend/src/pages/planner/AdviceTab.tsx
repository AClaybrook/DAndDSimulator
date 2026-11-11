import { Group, Select, Stack, Text } from '@mantine/core'
import { useQuery } from '@tanstack/react-query'
import type { ColumnDef } from '@tanstack/react-table'
import { useState } from 'react'
import { bg3, type Advice, type PlannerOptions } from '../../api'
import { SortTable } from '../../components/DataTable'
import { Section } from '../../components/Layout'
import { Plot } from '../../components/Plot'
import { chartLayout } from '../../format'
import { colorAt, useColors } from '../../theme'
import { ACTS, useParty } from '../../party'
import { useSharedEnemy } from './usePlanner'

type Suggestion = Advice['suggestions'][number]
const gain = (g: number) => `${g >= 0 ? '+' : ''}${g.toFixed(2)}`

const suggestionColumns: ColumnDef<Suggestion, unknown>[] = [
  { id: 'Item', header: 'Item', accessorFn: (r) => r.item, cell: ({ row }) => <span title={row.original.summary}>{row.original.item}</span> },
  { id: 'Adds', header: 'Adds', accessorFn: (r) => r.gain, cell: (c) => gain(c.getValue() as number) },
  { id: 'Found', header: 'Found', accessorFn: (r) => r.act ?? 9, cell: ({ row }) => (row.original.act ? `Act ${row.original.act}` : 'Act ?') },
  { id: 'Clashes', header: 'Used by or clashes with', accessorFn: (r) => r.users.join(', '), cell: (c) => <Text span size="xs" c="yellow">{String(c.getValue())}</Text> },
]

// What each worn item adds, and the best items for a slot, at an act
export function AdviceTab({ options }: { options: PlannerOptions }) {
  const { party, selected, together } = useParty()
  const { enemy, rounds } = useSharedEnemy()
  const [act, setAct] = useState('1')
  const [slot, setSlot] = useState('melee_main')
  const build = party[selected]
  const advice = useQuery({
    queryKey: ['advice', build, party, act, slot, enemy, rounds, together],
    queryFn: () => bg3.advice(build, party, act, slot, enemy, rounds, together),
    enabled: Boolean(build && enemy), placeholderData: (p) => p,
  })
  const colors = useColors()
  if (!build) return null
  // What each worn item adds, biggest at the top
  const worn = [...(advice.data?.values ?? [])].sort((x, y) => x.gain - y.gain)
  const figure = {
    data: [{ type: 'bar', orientation: 'h', y: worn.map((v) => v.item), x: worn.map((v) => v.gain), customdata: worn.map((v) => v.slot),
      text: worn.map((v) => gain(v.gain)), textposition: 'auto', marker: { color: colorAt(colors, selected) },
      hovertemplate: '%{y} (%{customdata}): %{x:+.2f}<extra></extra>' }],
    layout: chartLayout({ margin: { l: 190, r: 16, t: 4, b: 32 }, showlegend: false, xaxis: { title: { text: 'Damage per round added' }, rangemode: 'tozero' }, yaxis: { automargin: true } }),
  }
  return (
    <Stack gap="md">
      <Group gap="xs">
        <Select size="xs" label="At" w={110} value={act} onChange={(v) => v && setAct(v)} allowDeselect={false} data={ACTS.map((a) => ({ value: a, label: `Act ${a}` }))} />
        <Select size="xs" label="Best items for" w={200} value={slot} onChange={(v) => v && setSlot(v)} allowDeselect={false}
          data={options.slots.filter((s) => s.key !== 'ring_2').map((s) => ({ value: s.key, label: s.label }))} />
      </Group>
      <Section title="What each worn item adds" padding="sm">
        {worn.length ? <Plot figure={figure} height={worn.length * 30 + 60} /> : <Text size="sm" c="dimmed">No gear at this act.</Text>}
      </Section>
      <Section title="Best items for the slot" padding="sm">
        <SortTable data={advice.data?.suggestions ?? []} columns={suggestionColumns} initialSorting={[{ id: 'Adds', desc: true }]} filterable={false} title="Item suggestions" />
      </Section>
    </Stack>
  )
}
