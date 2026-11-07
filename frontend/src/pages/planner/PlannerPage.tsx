import { Center, Grid, Loader, NumberInput, Paper, SegmentedControl, Select, Tabs, Text } from '@mantine/core'
import { useQuery } from '@tanstack/react-query'
import { useEffect } from 'react'
import { api } from '../../api'
import { PageHeader } from '../../components/Layout'
import { useParty } from '../../party'
import { useSimulator } from '../../store'
import { AdviceTab } from './AdviceTab'
import { BuffsTab } from './BuffsTab'
import { BuildTab } from './BuildTab'
import { GearTab } from './GearTab'
import { PartyStrip } from './PartyStrip'
import { ResultsPanel } from './ResultsPanel'
import { useEvaluation, usePlannerOptions } from './usePlanner'
import { VariantsTab } from './VariantsTab'

export function PlannerPage() {
  const options = usePlannerOptions()
  const { party, selected, setParty, enemies, setEnemies, attackBonus, setAttackBonus } = useParty()
  const { enemy, setEnemy } = useSimulator()
  const simOptions = useQuery({ queryKey: ['options'], queryFn: api.options, staleTime: Infinity })
  const evaluation = useEvaluation()

  // First visit: the example party
  useEffect(() => {
    if (options.data && !party.length && !localStorage.getItem('bg3-party-started')) {
      setParty(options.data.defaultParty)
      localStorage.setItem('bg3-party-started', '1')
    }
  }, [options.data, party.length, setParty])

  if (!options.data) return <Center h={300}><Loader /></Center>
  const o = options.data
  const member = evaluation.data?.members[selected]

  return (
    <>
      <PageHeader title="Party planner" subtitle="Up to four characters, with gear and buffs for each act checkpoint"
        actions={<>
          <Select size="xs" w={260} searchable value={null} data={simOptions.data?.enemies ?? []}
            placeholder={enemy ? `${enemy.name} · AC ${enemy.armor_class}` : 'Enemy...'} title="The enemy for damage and hit chances, shared with the Simulator"
            onChange={async (v) => v && setEnemy(await api.enemy(v))} leftSection={<Text size="10px" c="dimmed">vs</Text>} />
          <SegmentedControl size="xs" value={String(enemies)} onChange={(v) => setEnemies(Number(v))}
            data={[1, 2, 3, 4].map((n) => ({ value: String(n), label: n === 1 ? '1 enemy' : `${n} (AoE)` }))} />
          <NumberInput size="xs" w={150} placeholder="auto" value={attackBonus ?? ''} min={0} max={20} leftSection={<Text size="10px" c="dimmed">Enemy to hit +</Text>}
            leftSectionWidth={84} onChange={(v) => setAttackBonus(v === '' ? null : Number(v))} title="The enemy's attack bonus, for the chance to be hit (empty: from its challenge rating)" />
        </>} />
      <PartyStrip options={o} evaluation={evaluation.data} enemies={enemies} />
      {party.length > 0 && (
        <Grid mt="md" gap="md">
          <Grid.Col span={{ base: 12, lg: 7 }}>
            <Paper p="md" withBorder>
              <Tabs defaultValue="gear" keepMounted={false}>
                <Tabs.List mb="md">
                  <Tabs.Tab value="gear">Gear</Tabs.Tab>
                  <Tabs.Tab value="build">Build</Tabs.Tab>
                  <Tabs.Tab value="buffs">Buffs</Tabs.Tab>
                  <Tabs.Tab value="variants">Variants</Tabs.Tab>
                  <Tabs.Tab value="advice">Gear advice</Tabs.Tab>
                </Tabs.List>
                <Tabs.Panel value="gear"><GearTab options={o} result={member} /></Tabs.Panel>
                <Tabs.Panel value="build"><BuildTab options={o} result={member} /></Tabs.Panel>
                <Tabs.Panel value="buffs"><BuffsTab options={o} result={member} /></Tabs.Panel>
                <Tabs.Panel value="variants"><VariantsTab options={o} attackBonus={evaluation.data?.attackBonus ?? 6} /></Tabs.Panel>
                <Tabs.Panel value="advice"><AdviceTab options={o} /></Tabs.Panel>
              </Tabs>
            </Paper>
          </Grid.Col>
          <Grid.Col span={{ base: 12, lg: 5 }}>
            <Paper p="md" withBorder style={{ position: 'sticky', top: 64 }}>
              <ResultsPanel options={o} evaluation={evaluation.data} />
            </Paper>
          </Grid.Col>
        </Grid>
      )}
    </>
  )
}
