import { Button, Center, Grid, Loader, Menu, NumberInput, Popover, ScrollArea, SegmentedControl, Select, Stack, Switch, Text } from '@mantine/core'
import { useDebouncedValue } from '@mantine/hooks'
import { useShortcuts } from '../../hotkeys'
import { IconAdjustments, IconDice5, IconDownload } from '@tabler/icons-react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api'
import { PageHeader } from '../../components/Layout'
import { download, fileName } from '../../format'
import { useSimulator } from '../../store'
import { CharacterEditor } from './CharacterEditor'
import { EnemyPanel } from './EnemyPanel'
import { PartyPanel } from './PartyPanel'
import { Results } from './Results'

// Simulator: characters and the enemy on the left, the answer and its chart on the right. Results follow every edit
export function SimulatorPage() {
  const { characters, enemy, settings, setAll, updateSettings } = useSimulator()
  const [editing, setEditing] = useState<string | null>(null)
  const [exporting, setExporting] = useState(false)
  const options = useQuery({ queryKey: ['options'], queryFn: api.options, staleTime: Infinity })

  // First visit: the example characters and enemy
  useEffect(() => {
    if (!enemy) api.defaults().then((d) => setAll(d.characters, d.enemy))
  }, [enemy, setAll])

  // Debounce on content (a JSON key), not on object identity, which changes every render
  const inputsKey = useMemo(() => JSON.stringify({ characters, enemy, rounds: settings.roundsPerFight }), [characters, enemy, settings.roundsPerFight])
  const [expectedKey] = useDebouncedValue(inputsKey, 250)
  const debounced = useMemo(() => JSON.parse(expectedKey), [expectedKey])
  // Exact expected damage, recomputed shortly after each edit
  const expected = useQuery({
    queryKey: ['expected', expectedKey],
    queryFn: () => api.expected(debounced.characters, debounced.enemy, debounced.rounds),
    enabled: Boolean(debounced.enemy && debounced.characters.length),
    placeholderData: (previous) => previous,
  })

  const simulation = useMutation({ mutationFn: () => api.simulate(characters, enemy!, settings) })
  const run = simulation.mutate
  const simulateKey = useMemo(() => JSON.stringify({ characters, enemy, settings }), [characters, enemy, settings])
  const [settledKey] = useDebouncedValue(simulateKey, 600)
  useEffect(() => {
    if (enemy && characters.length) run()
  }, [settledKey]) // eslint-disable-line react-hooks/exhaustive-deps

  const exportRaw = async (kind: string) => {
    if (!enemy) return
    setExporting(true)
    try { download(fileName(kind), await api.exportCsv(characters, enemy, settings, kind)) } finally { setExporting(false) }
  }

  useShortcuts([['r', () => { if (enemy && characters.length) run() }]])

  if (!options.data || !enemy) return <Center h={300}><Loader /></Center>
  const graph = options.data.graphs.find((g) => g.key === settings.graph)
  const editingIndex = characters.findIndex((c) => c.uid === editing)
  const attackDamage = (expected.data?.characters?.[editingIndex]?.attacks ?? []).map((a) => a.damage)

  return (
    <>
      <PageHeader title="Simulator" subtitle="Monte Carlo damage of your characters against one enemy, with the exact math alongside"
        actions={<>
          <Popover width={300} position="bottom-end" withArrow>
            <Popover.Target><Button size="xs" variant="default" leftSection={<IconAdjustments size={14} />}>Settings</Button></Popover.Target>
            <Popover.Dropdown>
              <Stack gap="xs">
                <NumberInput size="xs" label="Simulated rounds" value={settings.numRounds} min={100} max={1000000} step={1000}
                  onChange={(v) => updateSettings({ numRounds: Number(v) || 10000 })} />
                <NumberInput size="xs" label="Rounds per fight" description="Limited resources (smites, Action Surge) are spread over a fight"
                  value={settings.roundsPerFight} min={1} max={20} onChange={(v) => updateSettings({ roundsPerFight: Number(v) || 3 })} />
                <Select size="xs" label="Sweep over" data={options.data.sweepParameters.map((p) => p.key)} value={settings.sweepParameter}
                  onChange={(v) => v && updateSettings({ sweepParameter: v })} allowDeselect={false} disabled={!settings.graph.includes('Sweep')} />
                <Select size="xs" label="Rules" data={options.data.rulesets.map((r) => ({ value: r.key, label: r.label }))} value={settings.ruleset}
                  onChange={(v) => v && updateSettings({ ruleset: v })} allowDeselect={false} />
                <Switch size="xs" label="New random seed each run" checked={settings.randomSeed} onChange={(e) => updateSettings({ randomSeed: e.currentTarget.checked })} />
              </Stack>
            </Popover.Dropdown>
          </Popover>
          <Menu position="bottom-end">
            <Menu.Target>
              <Button size="xs" variant="default" leftSection={<IconDownload size={14} />} loading={exporting}>Raw data</Button>
            </Menu.Target>
            <Menu.Dropdown>
              <Menu.Label>Every simulated value as CSV</Menu.Label>
              {options.data.exports.map((k) => <Menu.Item key={k} onClick={() => exportRaw(k)}>{k}</Menu.Item>)}
            </Menu.Dropdown>
          </Menu>
          <Button size="xs" leftSection={<IconDice5 size={14} />} loading={simulation.isPending} onClick={() => run()}>Simulate again</Button>
        </>} />
      <ScrollArea type="never">
        <SegmentedControl fullWidth data={options.data.graphs.map((g) => g.key)} value={settings.graph} onChange={(g) => updateSettings({ graph: g })} style={{ minWidth: 640 }} />
      </ScrollArea>
      <Text size="xs" c="dimmed" mt={6} mb="md">{graph?.description}</Text>
      <Grid gap="md">
        {/* Editing takes over the left column (and a little more room), the results stay in view and follow every change */}
        <Grid.Col span={{ base: 12, md: editingIndex >= 0 ? 6 : 4 }}>
          {editingIndex >= 0 ? (
            <CharacterEditor id={editing} options={options.data} attackDamage={attackDamage} damagePerRound={expected.data?.characters?.[editingIndex]?.damagePerRound}
              onSelect={setEditing} onClose={() => setEditing(null)} />
          ) : (
            <Stack gap="md">
              <PartyPanel options={options.data} expected={expected.data} onEdit={setEditing} />
              <EnemyPanel options={options.data} />
            </Stack>
          )}
        </Grid.Col>
        <Grid.Col span={{ base: 12, md: editingIndex >= 0 ? 6 : 8 }}>
          {simulation.isError && <Text c="red" size="sm">{String(simulation.error)}</Text>}
          <Results result={simulation.data} />
        </Grid.Col>
      </Grid>
    </>
  )
}
