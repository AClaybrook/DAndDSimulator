import { Button, Center, Grid, Loader, Menu, NumberInput, Paper, SegmentedControl, Select, Tabs, Text } from '@mantine/core'
import { useQuery } from '@tanstack/react-query'
import { IconSend } from '@tabler/icons-react'
import { useEffect, useState } from 'react'
import { api, bg3 } from '../../api'
import { PageHeader } from '../../components/Layout'
import { useParty } from '../../party'
import { MAX_CHARACTERS, useSimulator } from '../../store'
import { AdviceTab } from './AdviceTab'
import { BuffsTab } from './BuffsTab'
import { BuildTab } from './BuildTab'
import { FrontierTab } from './FrontierTab'
import { GearTab } from './GearTab'
import { PartyStrip } from './PartyStrip'
import { ResultsPanel } from './ResultsPanel'
import { SavedParties } from './SavedParties'
import { useEvaluation, usePlannerOptions } from './usePlanner'
import { VariantsTab } from './VariantsTab'

export function PlannerPage() {
  const options = usePlannerOptions()
  const { party, selected, setParty, enemies, setEnemies, attackBonus, setAttackBonus } = useParty()
  const { enemy, setEnemy, addCharacter } = useSimulator()
  const [sending, setSending] = useState(false)
  const simOptions = useQuery({ queryKey: ['options'], queryFn: api.options, staleTime: Infinity })
  const evaluation = useEvaluation()

  // First visit: the example party
  useEffect(() => {
    if (options.data && !party.length && !localStorage.getItem('bg3-party-started')) {
      setParty(options.data.defaultParty)
      localStorage.setItem('bg3-party-started', '1')
    }
  }, [options.data, party.length, setParty])

  // Compiled characters into the Simulator (as new characters, up to its limit), then open it
  const send = async (act: string | null, member: number | null) => {
    setSending(true)
    try {
      for (const c of await bg3.toSimulator(party, act, member)) addCharacter(c)
      window.location.hash = '#/simulator'
    } finally { setSending(false) }
  }

  if (!options.data) return <Center h={300}><Loader /></Center>
  const o = options.data
  const member = evaluation.data?.members[selected]

  return (
    <>
      <PageHeader title="Party planner" subtitle="Damage by act for up to four characters"
        actions={<>
          <SavedParties options={o} />
          <Select size="xs" w={260} searchable value={null} data={simOptions.data?.enemies ?? []}
            placeholder={enemy ? `${enemy.name} · AC ${enemy.armor_class}` : 'Enemy...'} title="The enemy for damage and hit chances, shared with the Simulator"
            onChange={async (v) => v && setEnemy(await api.enemy(v))} leftSection={<Text size="10px" c="dimmed">vs</Text>} />
          <SegmentedControl size="xs" value={String(enemies)} onChange={(v) => setEnemies(Number(v))}
            data={[1, 2, 3, 4].map((n) => ({ value: String(n), label: n === 1 ? '1 enemy' : `${n} (AoE)` }))} />
          <NumberInput size="xs" w={150} placeholder="auto" value={attackBonus ?? ''} min={0} max={20} leftSection={<Text size="10px" c="dimmed">Enemy to hit +</Text>}
            leftSectionWidth={84} onChange={(v) => setAttackBonus(v === '' ? null : Number(v))} title="The enemy's attack bonus, for the chance to be hit (empty: from its challenge rating)" />
          <Menu position="bottom-end">
            <Menu.Target>
              <Button size="xs" variant="default" leftSection={<IconSend size={14} />} loading={sending} disabled={!party.length}>To simulator</Button>
            </Menu.Target>
            <Menu.Dropdown>
              <Menu.Label>Add as Simulator characters (max {MAX_CHARACTERS})</Menu.Label>
              {o.acts.map((a) => <Menu.Item key={a.key} onClick={() => send(a.key, null)}>Whole party at {a.label}</Menu.Item>)}
              {party[selected] && <Menu.Item onClick={() => send(null, selected)}>{party[selected].name} at every act</Menu.Item>}
            </Menu.Dropdown>
          </Menu>
        </>} />
      <PartyStrip options={o} evaluation={evaluation.data} enemies={enemies} />
      {party.length > 0 && (
        <Grid mt="md" gap="md">
          <Grid.Col span={{ base: 12, lg: 6 }}>
            <Paper p="md" withBorder style={{ position: 'sticky', top: 64 }}>
              <ResultsPanel options={o} evaluation={evaluation.data} />
            </Paper>
          </Grid.Col>
          <Grid.Col span={{ base: 12, lg: 6 }}>
            <Paper p="md" withBorder>
              <Text className="section-label" mb={6}>{party[selected]?.name}</Text>
              <Tabs defaultValue="gear" keepMounted={false}>
                <Tabs.List mb="md">
                  <Tabs.Tab value="gear">Gear</Tabs.Tab>
                  <Tabs.Tab value="build">Build</Tabs.Tab>
                  <Tabs.Tab value="buffs">Buffs</Tabs.Tab>
                  <Tabs.Tab value="variants">Variants</Tabs.Tab>
                  <Tabs.Tab value="advice">Gear advice</Tabs.Tab>
                  <Tabs.Tab value="frontier">Frontier</Tabs.Tab>
                </Tabs.List>
                <Tabs.Panel value="gear"><GearTab options={o} result={member} /></Tabs.Panel>
                <Tabs.Panel value="build"><BuildTab options={o} result={member} /></Tabs.Panel>
                <Tabs.Panel value="buffs"><BuffsTab options={o} result={member} /></Tabs.Panel>
                <Tabs.Panel value="variants"><VariantsTab options={o} attackBonus={evaluation.data?.attackBonus ?? 6} /></Tabs.Panel>
                <Tabs.Panel value="advice"><AdviceTab options={o} /></Tabs.Panel>
                <Tabs.Panel value="frontier"><FrontierTab /></Tabs.Panel>
              </Tabs>
            </Paper>
          </Grid.Col>
        </Grid>
      )}
    </>
  )
}
