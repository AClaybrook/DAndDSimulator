import { Alert, Group, Paper, Stack, Tabs, Text } from '@mantine/core'
import { useMediaQuery } from '@mantine/hooks'
import { useMemo } from 'react'
import { useShallow } from 'zustand/react/shallow'
import type { SimulationResult } from '../../api'
import { DataTable } from '../../components/DataTable'
import { Plot } from '../../components/Plot'
import { useSimulator } from '../../store'
import { colorAt, useColors } from '../../theme'
import { drawChart } from './charts'

// The answer first (who comes out on top and by how much), then the chart and tables as tabs
export function Results({ result }: { result: SimulationResult | undefined }) {
  const names = useSimulator(useShallow((s) => s.characters.map((c) => c.name)))
  const colors = useColors()
  const chart = result?.chart
  const narrow = useMediaQuery('(max-width: 48em)') ?? false
  const drawn = useMemo(() => (chart ? drawChart(chart, colors, narrow) : null), [chart, colors, narrow])
  if (!result) return null
  if (result.problems?.length) {
    return <Alert color="orange" title="Please fix these before simulating">{result.problems.map((p) => <div key={p}>{p}</div>)}</Alert>
  }
  const headline = result.headline!
  const values = headline.values
  const top = values[0]
  const scale = Math.max(...values.map((v) => v.value), 1e-9)
  const gap = values.length > 1 ? Math.abs(top.value - values[1].value) : 0
  // Damage per round already has its home on the character cards (same exact numbers), so the ranked bars only show for other measures
  const ranked = headline.unit !== 'damage per round' && values.length > 1

  return (
    <Stack gap="md">
      <Paper p="md" withBorder>
        <Group justify="space-between" align="flex-start" wrap="nowrap">
          <div style={{ minWidth: 0 }}>
            <Text className="section-label">{headline.higherIsBetter ? 'Most damage' : 'Fastest'}</Text>
            <Text fz={22} fw={700} truncate>{top.name}</Text>
            <Text size="sm" c="dimmed">
              {values.length > 1 ? `${gap.toFixed(1)} ${headline.higherIsBetter ? 'ahead of' : 'quicker than'} ${values[1].name}` : ''}{headline.context ? ` · ${headline.context}` : ''}
            </Text>
          </div>
          <div style={{ textAlign: 'right', flexShrink: 0 }}>
            <Text fz={32} fw={800} className="numeric" lh={1}>{top.value.toFixed(1)}</Text>
            <Text size="xs" c="dimmed">{headline.unit}</Text>
          </div>
        </Group>
        {ranked && (
          <Stack gap={6} mt="sm">
            {values.map((v) => (
              <Group key={v.name} gap="xs" wrap="nowrap">
                <Text size="xs" w={{ base: 110, sm: 200 }} truncate>{v.name}</Text>
                <div className="bar-track" style={{ flex: 1 }}>
                  <div className="bar-fill" style={{ width: `${(100 * v.value) / scale}%`, background: colorAt(colors, Math.max(names.indexOf(v.name), 0)) }} />
                </div>
                <Text size="xs" w={48} ta="right" className="numeric">{v.value.toFixed(1)}</Text>
              </Group>
            ))}
          </Stack>
        )}
      </Paper>
      <Paper p="md" withBorder>
        <Tabs defaultValue="chart" keepMounted={false}>
          <Tabs.List mb="sm">
            <Tabs.Tab value="chart">Chart</Tabs.Tab>
            {result.tables?.map((t) => <Tabs.Tab key={t.title} value={t.title}>{t.title}</Tabs.Tab>)}
          </Tabs.List>
          <Tabs.Panel value="chart">
            {result.chart && drawn && (
              <>
                <Text fw={600} mb={4}>{result.chart.title}</Text>
                <Plot figure={drawn.figure} height={drawn.height} />
              </>
            )}
          </Tabs.Panel>
          {result.tables?.map((t) => <Tabs.Panel key={t.title} value={t.title}><DataTable table={t} maxHeight={520} /></Tabs.Panel>)}
        </Tabs>
      </Paper>
    </Stack>
  )
}
