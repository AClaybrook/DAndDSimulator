import { Button, Center, Collapse, Grid, Group, Loader, NumberInput, Paper, SegmentedControl, Select, Stack, Switch, Text, Title, Tooltip } from '@mantine/core'
import { useDebouncedValue, useDisclosure } from '@mantine/hooks'
import { IconAdjustments, IconDice5 } from '@tabler/icons-react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api'
import { useSimulator } from '../../store'
import { CharacterEditor } from './CharacterEditor'
import { EnemyPanel } from './EnemyPanel'
import { PartyPanel } from './PartyPanel'
import { Results } from './Results'

// Simulator: setup on the left (characters, enemy, settings), the answer and its plot on the right
export function SimulatorPage() {
  const { characters, enemy, settings, setAll, updateSettings } = useSimulator()
  const [editing, setEditing] = useState<string | null>(null)
  const [settingsOpen, { toggle: toggleSettings }] = useDisclosure(false)
  const options = useQuery({ queryKey: ['options'], queryFn: api.options, staleTime: Infinity })

  // First visit: the example characters and enemy
  useEffect(() => {
    if (!enemy) api.defaults().then((d) => setAll(d.characters, d.enemy))
  }, [enemy, setAll])

  // Debounce on content (a JSON key), not on object identity, which changes every render
  const inputsKey = useMemo(() => JSON.stringify({ characters, enemy, rounds: settings.roundsPerFight }), [characters, enemy, settings.roundsPerFight])
  const [expectedKey] = useDebouncedValue(inputsKey, 250)
  // Exact expected damage, recomputed shortly after each edit
  const debounced = useMemo(() => JSON.parse(expectedKey), [expectedKey])
  const expected = useQuery({
    queryKey: ['expected', expectedKey],
    queryFn: () => api.expected(debounced.characters, debounced.enemy, debounced.rounds),
    enabled: Boolean(debounced.enemy && debounced.characters.length),
    placeholderData: (previous) => previous,
  })

  const simulation = useMutation({ mutationFn: () => api.simulate(characters, enemy!, settings) })
  const run = simulation.mutate
  // Simulations take a fraction of a second, so results follow every edit (shortly after the last one)
  const simulateKey = useMemo(() => JSON.stringify({ characters, enemy, settings }), [characters, enemy, settings])
  const [settledKey] = useDebouncedValue(simulateKey, 600)
  useEffect(() => {
    if (enemy && characters.length) run()
  }, [settledKey]) // eslint-disable-line react-hooks/exhaustive-deps

  if (!options.data || !enemy) return <Center h={300}><Loader /></Center>
  const graph = options.data.graphs.find((g) => g.key === settings.graph)
  const attackDamage = Object.fromEntries(
    (expected.data?.characters?.find((_, i) => characters[i]?.uid === editing)?.attacks ?? []).map((a) => [a.name, a.damage]),
  )

  return (
    <>
      <Grid gap="md">
        <Grid.Col span={{ base: 12, md: 4 }}>
          <Stack gap="sm">
            <PartyPanel options={options.data} expected={expected.data} onEdit={setEditing} />
            <EnemyPanel options={options.data} />
          </Stack>
        </Grid.Col>
        <Grid.Col span={{ base: 12, md: 8 }}>
          <Stack gap="sm">
            <Paper p="sm" withBorder>
              <Group justify="space-between" wrap="wrap" gap="xs">
                <SegmentedControl size="xs" data={options.data.graphs.map((g) => g.key)} value={settings.graph} onChange={(graph) => updateSettings({ graph })} />
                <Group gap="xs">
                  <Tooltip label="Rounds, fight length and sweep settings">
                    <Button size="xs" variant="subtle" leftSection={<IconAdjustments size={14} />} onClick={toggleSettings}>Settings</Button>
                  </Tooltip>
                  <Button size="xs" leftSection={<IconDice5 size={14} />} loading={simulation.isPending} onClick={() => run()}>Simulate</Button>
                </Group>
              </Group>
              {graph && <Text size="xs" c="dimmed" mt={6}>{graph.description}</Text>}
              <Collapse expanded={settingsOpen}>
                <Group mt="sm" gap="sm" align="end">
                  <NumberInput size="xs" label="Rounds" value={settings.numRounds} min={100} max={1000000} step={1000} w={110}
                    onChange={(v) => updateSettings({ numRounds: Number(v) || 10000 })} />
                  <NumberInput size="xs" label="Rounds per fight" value={settings.roundsPerFight} min={1} max={20} w={120}
                    onChange={(v) => updateSettings({ roundsPerFight: Number(v) || 3 })} />
                  {settings.graph.includes('Sweep') && (
                    <Select size="xs" label="Sweep over" data={options.data.sweepParameters.map((p) => p.key)} value={settings.sweepParameter}
                      onChange={(v) => v && updateSettings({ sweepParameter: v })} allowDeselect={false} w={180} />
                  )}
                  <Select size="xs" label="Rules" data={options.data.rulesets.map((r) => ({ value: r.key, label: r.label }))} value={settings.ruleset}
                    onChange={(v) => v && updateSettings({ ruleset: v })} allowDeselect={false} w={160} />
                  <Switch size="xs" label="New random seed each run" checked={settings.randomSeed} onChange={(e) => updateSettings({ randomSeed: e.currentTarget.checked })} />
                </Group>
              </Collapse>
            </Paper>
            {simulation.isError && <Text c="red" size="sm">{String(simulation.error)}</Text>}
            <Results result={simulation.data} />
          </Stack>
        </Grid.Col>
      </Grid>
      <CharacterEditor id={editing} options={options.data} attackDamage={attackDamage} onClose={() => setEditing(null)} />
    </>
  )
}

export const SimulatorTitle = () => <Title order={3}>Simulator</Title>
