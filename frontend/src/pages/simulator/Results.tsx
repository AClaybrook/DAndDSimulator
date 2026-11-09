import { Alert, Group, Paper, Stack, Tabs, Text } from '@mantine/core'
import { useShallow } from 'zustand/react/shallow'
import type { SimulationResult } from '../../api'
import { DataTable } from '../../components/DataTable'
import { Plot } from '../../components/Plot'
import { COLORS, useSimulator } from '../../store'

// The answer first (who comes out on top and by how much), then the chart and tables as tabs
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
    <Stack gap="md">
      <Paper p="md" withBorder>
        <Group justify="space-between" align="flex-start" mb="sm" wrap="nowrap">
          <div>
            <Text className="section-label">{headline.higherIsBetter ? 'Most damage' : 'Fastest'}</Text>
            <Text fz={22} fw={700}>{top.name}</Text>
            <Text size="sm" c="dimmed">
              {values.length > 1 ? `${gap.toFixed(2)} ${headline.higherIsBetter ? 'ahead of' : 'quicker than'} ${values[1].name}` : ''}{headline.context ? ` · ${headline.context}` : ''}
            </Text>
          </div>
          <div style={{ textAlign: 'right' }}>
            <Text fz={32} fw={800} className="numeric" lh={1}>{top.value.toFixed(1)}</Text>
            <Text size="xs" c="dimmed">{headline.unit}</Text>
          </div>
        </Group>
        <Stack gap={6}>
          {values.map((v) => (
            <Group key={v.name} gap="xs" wrap="nowrap">
              <Text size="xs" w={200} truncate>{v.name}</Text>
              <div className="bar-track" style={{ flex: 1 }}>
                <div className="bar-fill" style={{ width: `${(100 * v.value) / scale}%`, background: color(v.name) }} />
              </div>
              <Text size="xs" w={56} ta="right" className="numeric">{v.value.toFixed(2)}</Text>
            </Group>
          ))}
        </Stack>
      </Paper>
      <Paper p="md" withBorder>
        <Tabs defaultValue="chart" keepMounted={false}>
          <Tabs.List mb="sm">
            <Tabs.Tab value="chart">Chart</Tabs.Tab>
            {result.tables?.map((t) => <Tabs.Tab key={t.title} value={t.title}>{t.title}</Tabs.Tab>)}
          </Tabs.List>
          <Tabs.Panel value="chart">{result.figure && <Plot figure={result.figure} />}</Tabs.Panel>
          {result.tables?.map((t) => <Tabs.Panel key={t.title} value={t.title}><DataTable table={t} maxHeight={520} /></Tabs.Panel>)}
        </Tabs>
      </Paper>
    </Stack>
  )
}
