import { ActionIcon, Button, Group, Menu, Modal, Paper, Select, SimpleGrid, Stack, Text, Tooltip } from '@mantine/core'
import { IconPlus, IconTrash, IconUserPlus } from '@tabler/icons-react'
import { useState } from 'react'
import { bg3, type Build, type Evaluation, type PlannerOptions } from '../../api'
import { ACTS, useParty } from '../../party'
import { COLORS } from '../../store'

export function classLine(build: Build, options: PlannerOptions) {
  const classes = (build.character as { classes?: [string, string, number][] } | null)?.classes
  if (classes?.length) return classes.map(([c, sub, n]) => `${c[0].toUpperCase()}${c.slice(1)} ${n}${sub ? ` (${sub})` : ''}`).join(' / ')
  return options.presets.find((p) => p.key === build.preset)?.label ?? build.preset
}

// The party at a glance: each member's damage in every act; click one to edit it
export function PartyStrip({ options, evaluation, enemies }: { options: PlannerOptions; evaluation: Evaluation | undefined; enemies: number }) {
  const { party, selected, select, add, remove } = useParty()
  const [adding, setAdding] = useState<'example' | 'preset' | null>(null)
  const [choice, setChoice] = useState<string | null>(null)
  const full = party.length >= options.maxPartySize

  const addChosen = async () => {
    if (!choice) return
    if (adding === 'example') add(await bg3.example(choice))
    else add({ name: options.presets.find((p) => p.key === choice)?.label ?? 'Character', preset: choice, equipment: {}, buffs: {}, conditions: [], levels: {},
      character: null, carried: [], roles: [], variants: [], advantage: false })
    setAdding(null)
    setChoice(null)
  }
  const addCustom = () => add({ name: 'Custom character', preset: 'fighter_gwm', equipment: {}, buffs: {}, conditions: [], levels: {},
    character: { ...options.builder.defaultCharacter, name: 'Custom character' }, carried: [], roles: [], variants: [], advantage: false })

  return (
    <>
      <SimpleGrid cols={{ base: 1, sm: 2, lg: Math.min(party.length + (full ? 0 : 1), 5) }} spacing="sm">
        {party.map((b, i) => {
          const result = evaluation?.members[i]
          return (
            <Paper key={b.uid} p="sm" withBorder onClick={() => select(i)}
              style={{ cursor: 'pointer', borderTop: `3px solid ${COLORS[i % COLORS.length]}`, outline: i === selected ? `2px solid ${COLORS[i % COLORS.length]}` : undefined }}>
              <Group justify="space-between" wrap="nowrap" align="flex-start">
                <div style={{ minWidth: 0 }}>
                  <Text fw={600} truncate>{b.name}</Text>
                  <Text size="xs" c="dimmed" truncate>{classLine(b, options)}</Text>
                </div>
                <Tooltip label="Remove from the party">
                  <ActionIcon variant="subtle" color="gray" size="sm" onClick={(e) => { e.stopPropagation(); remove(i) }} aria-label="Remove"><IconTrash size={14} /></ActionIcon>
                </Tooltip>
              </Group>
              <Group gap="md" mt={6} wrap="nowrap">
                {ACTS.map((a) => (
                  <div key={a}>
                    <Text size="10px" c="dimmed" tt="uppercase">Act {a}</Text>
                    <Text fw={700} className="numeric">{result ? result.acts[a].damage[enemies - 1].toFixed(1) : '–'}</Text>
                  </div>
                ))}
                <div>
                  <Text size="10px" c="dimmed" tt="uppercase">AC</Text>
                  <Text fw={700} className="numeric">{result ? ACTS.map((a) => result.acts[a].ac).join('/') : '–'}</Text>
                </div>
              </Group>
            </Paper>
          )
        })}
        {!full && (
          <Paper p="sm" withBorder style={{ borderStyle: 'dashed', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Menu position="bottom">
              <Menu.Target><Button variant="subtle" leftSection={<IconUserPlus size={16} />}>Add a character</Button></Menu.Target>
              <Menu.Dropdown>
                <Menu.Item onClick={() => setAdding('example')}>From an example build...</Menu.Item>
                <Menu.Item onClick={() => setAdding('preset')}>From a class preset...</Menu.Item>
                <Menu.Item onClick={addCustom}>Custom character (race, classes, feats)</Menu.Item>
              </Menu.Dropdown>
            </Menu>
          </Paper>
        )}
      </SimpleGrid>
      <Modal opened={adding !== null} onClose={() => setAdding(null)} title={adding === 'example' ? 'Add an example build' : 'Add a class preset'}>
        <Stack>
          <Select searchable label={adding === 'example' ? 'Build' : 'Class preset'} value={choice} onChange={setChoice}
            data={adding === 'example' ? options.examples.map((e) => ({ value: e.name, label: e.name })) : options.presets.map((p) => ({ value: p.key, label: p.label }))} />
          <Button leftSection={<IconPlus size={14} />} onClick={addChosen} disabled={!choice}>Add</Button>
        </Stack>
      </Modal>
    </>
  )
}
