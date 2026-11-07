import { Accordion, Alert, Group, Paper, Stack, Text } from '@mantine/core'
import type { SimulationResult } from '../../api'
import { DataTable } from '../../components/DataTable'
import { Plot } from '../../components/Plot'
import { useShallow } from 'zustand/react/shallow'
import { COLORS, useSimulator } from '../../store'

// The answer first (who comes out on top and by how much), then the plot, then tables folded underneath
export function Results({ result }: { result: SimulationResult | undefined }) {
  const names = useSimulator(useShallow((s) => s.characters.map((c) => c.name)))
  if (!result) return null
  if (result.problems?.length) {
    return <Alert color="orange" title="Please fix these before simulating">{result.problems.map((p) => <div key={p}>{p}</div>)}</Alert>
  }
  const headline = result.headline!
  const values = headline.values
  const top = values[0]
  const scale = Math.max(...values.map((v) => v.value), 1e-9)
  const color = (name: string) => COLORS[Math.max(names.indexOf(name), 0) % COLORS.length]
  const gap = values.length > 1 ? Math.abs(top.value - values[1].value) : 0

  return (
    <Stack gap="sm">
      <Paper p="sm" withBorder>
        <Text size="sm">
          <b>{top.name}</b> {headline.higherIsBetter ? 'leads' : 'is fastest'} with <b className="numeric">{top.value.toFixed(2)}</b> {headline.unit}
          {values.length > 1 ? `, ${gap.toFixed(2)} ${headline.higherIsBetter ? 'ahead of' : 'quicker than'} ${values[1].name}` : ''}
          {headline.context ? ` ${headline.context}` : ''}.
        </Text>
        <Stack gap={4} mt="xs">
          {values.map((v) => (
            <Group key={v.name} gap="xs" wrap="nowrap">
              <Text size="xs" w={190} truncate>{v.name}</Text>
              <div className="bar-track" style={{ flex: 1 }}>
                <div className="bar-fill" style={{ width: `${(100 * v.value) / scale}%`, background: color(v.name) }} />
              </div>
              <Text size="xs" w={56} ta="right" className="numeric">{v.value.toFixed(2)}</Text>
            </Group>
          ))}
        </Stack>
      </Paper>
      {result.figure && <Paper p={4} withBorder><Plot figure={result.figure} /></Paper>}
      <Accordion variant="contained" multiple>
        {result.tables?.map((t) => (
          <Accordion.Item key={t.title} value={t.title}>
            <Accordion.Control>{t.title} <Text span size="xs" c="dimmed">({t.rows.length} rows)</Text></Accordion.Control>
            <Accordion.Panel><DataTable table={t} /></Accordion.Panel>
          </Accordion.Item>
        ))}
      </Accordion>
    </Stack>
  )
}
