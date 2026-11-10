import { ActionIcon, Button, Group, Menu, Modal, NumberInput, Paper, Select, Stack, Text, Tooltip } from '@mantine/core'
import { IconCopy, IconPencil, IconPlus, IconTrash } from '@tabler/icons-react'
import { useState } from 'react'
import { api, type Expected, type Options } from '../../api'
import { MAX_CHARACTERS, useSimulator } from '../../store'
import { colorAt, useColors } from '../../theme'

interface Props {
  options: Options
  expected: Expected | undefined
  onEdit: (id: string) => void
}

// The characters at a glance: name, level and exact expected damage per round, details in the editor
export function PartyPanel({ options, expected, onEdit }: Props) {
  const { characters, removeCharacter, copyCharacter, addCharacter, settings } = useSimulator()
  const [problem, setProblem] = useState<string | null>(null)
  const [presetOpen, setPresetOpen] = useState(false)
  const [preset, setPreset] = useState<string | null>('fighter_gwm')
  const [level, setLevel] = useState<number>(5)
  const best = Math.max(1, ...(expected?.characters ?? []).map((c) => c.damagePerRound))
  const colors = useColors()

  const addPreset = async () => {
    if (!preset) return
    addCharacter(await api.preset(preset, level, settings.ruleset))
    setPresetOpen(false)
  }

  const addVariant = async (id: string, key: string) => {
    const original = characters.find((c) => c.uid === id)
    if (!original) return
    const result = await api.variant(original, key)
    setProblem(result.problems?.join('; ') ?? null)
    if (result.character) addCharacter(result.character)
  }

  return (
    <Paper p="md" withBorder>
      <Group justify="space-between" mb="sm">
        <Text fw={600}>Characters</Text>
        <Menu position="bottom-end">
          <Menu.Target>
            <Button size="xs" variant="light" leftSection={<IconPlus size={14} />} disabled={characters.length >= MAX_CHARACTERS}>Add</Button>
          </Menu.Target>
          <Menu.Dropdown>
            <Menu.Item onClick={() => setPresetOpen(true)}>From a class preset...</Menu.Item>
            <Menu.Item onClick={() => addCharacter({ ...(options.characterDefaults as object), name: 'Character', level: 5, attacks: [{ ...options.attackDefaults }] } as never)}>
              Blank character
            </Menu.Item>
          </Menu.Dropdown>
        </Menu>
      </Group>
      <Stack gap={6}>
        {characters.map((c, i) => {
          const dpr = expected?.characters?.[i]?.damagePerRound
          return (
            <Paper key={c.uid} p="xs" radius="md" withBorder style={{ borderLeft: `4px solid ${colorAt(colors, i)}`, cursor: 'pointer' }} onClick={() => onEdit(c.uid!)}>
              <Group justify="space-between" wrap="nowrap" gap="xs">
                <div style={{ minWidth: 0, flex: 1 }}>
                  <Text size="sm" fw={500} truncate>{c.name}</Text>
                  <Text size="xs" c="dimmed">Level {c.level} · {c.attacks.length} attack{c.attacks.length === 1 ? '' : 's'}</Text>
                </div>
                <Tooltip label="Exact expected damage per round against the enemy">
                  <Text fw={700} className="numeric">{dpr !== undefined ? dpr.toFixed(1) : '–'}</Text>
                </Tooltip>
                <Group gap={0} wrap="nowrap" onClick={(e) => e.stopPropagation()}>
                  <ActionIcon variant="subtle" size="sm" onClick={() => onEdit(c.uid!)} aria-label="Edit"><IconPencil size={14} /></ActionIcon>
                  <Menu position="bottom-end" withinPortal>
                    <Menu.Target>
                      <ActionIcon variant="subtle" size="sm" aria-label="Copy" disabled={characters.length >= MAX_CHARACTERS}><IconCopy size={14} /></ActionIcon>
                    </Menu.Target>
                    <Menu.Dropdown>
                      <Menu.Label>Add a copy</Menu.Label>
                      <Menu.Item onClick={() => copyCharacter(c.uid!)}>Exact copy</Menu.Item>
                      {options.variants.map((v) => <Menu.Item key={v.key} onClick={() => addVariant(c.uid!, v.key)}>{v.label}</Menu.Item>)}
                    </Menu.Dropdown>
                  </Menu>
                  <ActionIcon variant="subtle" size="sm" color="red" onClick={() => removeCharacter(c.uid!)} aria-label="Delete"><IconTrash size={14} /></ActionIcon>
                </Group>
              </Group>
              {dpr !== undefined && (
                <div className="bar-track" style={{ marginTop: 4 }}>
                  <div className="bar-fill" style={{ width: `${(100 * dpr) / best}%`, background: colorAt(colors, i) }} />
                </div>
              )}
            </Paper>
          )
        })}
        {problem && <Text size="xs" c="orange">{problem}</Text>}
        {expected?.problems?.map((p) => <Text key={p} size="xs" c="orange">{p}</Text>)}
      </Stack>
      <Modal opened={presetOpen} onClose={() => setPresetOpen(false)} title="Add a class preset" size="md">
        <Stack>
          <Select label="Preset" data={options.presets.map((p) => ({ value: p.key, label: p.label }))} value={preset} onChange={setPreset} searchable />
          {preset && <Text size="xs" c="dimmed">{options.presets.find((p) => p.key === preset)?.description}</Text>}
          <NumberInput label="Level" value={level} min={1} max={20} onChange={(v) => setLevel(Number(v) || 1)} />
          <Button onClick={addPreset}>Add</Button>
        </Stack>
      </Modal>
    </Paper>
  )
}
