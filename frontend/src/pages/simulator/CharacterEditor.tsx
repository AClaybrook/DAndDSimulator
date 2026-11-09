import { ActionIcon, Badge, Button, Divider, Drawer, Grid, Group, NavLink, NumberInput, ScrollArea, Select, SimpleGrid, Stack, Tabs, Text, Textarea, TextInput, Tooltip } from '@mantine/core'
import { IconCopy, IconPlus, IconTrash } from '@tabler/icons-react'
import { useState } from 'react'
import { api, type Attack, type Options, type Value } from '../../api'
import { FieldGroups, FieldInput } from '../../components/FieldInput'
import { ATTACK_GROUPS, ATTACK_MAIN, CHARACTER_GROUPS, STATS, statLabel } from '../../fields'
import { useSimulator } from '../../store'

interface Props {
  id: string | null
  options: Options
  attackDamage: number[] // Expected damage per round of each attack, in order
  onClose: () => void
}

// Everything about one character in tabs. Attacks: the list on the left, the selected attack's fields on the right
export function CharacterEditor({ id, options, attackDamage, onClose }: Props) {
  const character = useSimulator((s) => s.characters.find((c) => c.uid === id))
  const { updateCharacter, updateAttack, addAttacks, removeAttack } = useSimulator()
  const ruleset = useSimulator((s) => s.settings.ruleset)
  const [template, setTemplate] = useState<string | null>(null)
  const [attackIndex, setAttackIndex] = useState(0)
  if (!character || !id) return <Drawer opened={false} onClose={onClose} />
  const set = (key: string, value: Value) => updateCharacter(id, { [key]: value })
  const index = Math.min(attackIndex, character.attacks.length - 1)
  const attack: Attack | undefined = character.attacks[index]

  const addFromTemplate = async () => {
    if (!template) return
    const mainStat = STATS.reduce((best, s) => (Number(character[s]) > Number(character[best]) ? s : best), 'strength')
    addAttacks(id, await api.template(template, mainStat, character.level, ruleset))
    setAttackIndex(character.attacks.length)
    setTemplate(null)
  }

  return (
    <Drawer opened onClose={onClose} position="right" size="xl" title={<Text fw={600} size="lg">{character.name}</Text>}>
      <Tabs defaultValue="stats">
        <Tabs.List mb="md">
          <Tabs.Tab value="stats">Stats</Tabs.Tab>
          <Tabs.Tab value="attacks" rightSection={<Badge size="xs" variant="light" circle>{character.attacks.length}</Badge>}>Attacks</Tabs.Tab>
          <Tabs.Tab value="bonuses">Feats and bonuses</Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="stats">
          <Stack gap="sm">
            <Group grow>
              <TextInput size="xs" label="Name" value={character.name} onChange={(e) => set('name', e.currentTarget.value)} />
              <NumberInput size="xs" label="Level" value={character.level} min={1} max={20} onChange={(v) => set('level', Number(v) || 1)} />
            </Group>
            <SimpleGrid cols={6} spacing={6}>
              {STATS.map((s) => (
                <NumberInput key={s} size="xs" label={statLabel(s)} value={Number(character[s])} min={1} max={30} hideControls
                  onChange={(v) => set(s, Number(v) || 10)} />
              ))}
            </SimpleGrid>
            {character.preset ? <Text size="xs" c="dimmed">Built from the {String(character.preset)} preset; your edits are kept when it levels up in a sweep.</Text> : null}
            <Textarea size="xs" label="Notes" autosize minRows={2} value={String(character.description ?? '')} onChange={(e) => set('description', e.currentTarget.value)} />
          </Stack>
        </Tabs.Panel>

        <Tabs.Panel value="attacks">
          <Grid gap="md">
            <Grid.Col span={4}>
              <ScrollArea.Autosize mah="60vh">
                {character.attacks.map((a: Attack, i: number) => (
                  <NavLink key={i} active={i === index} onClick={() => setAttackIndex(i)} label={a.name}
                    description={`${a.damage} ${String(a.damage_type ?? '')}${attackDamage[i] !== undefined ? ` · ${attackDamage[i].toFixed(1)}/round` : ''}`} />
                ))}
              </ScrollArea.Autosize>
              <Divider my="sm" />
              <Stack gap={6}>
                <Select size="xs" placeholder="Add a weapon or spell..." data={options.attackTemplates} value={template} onChange={setTemplate} searchable />
                <Group gap={6} grow>
                  <Button size="xs" leftSection={<IconPlus size={14} />} disabled={!template} onClick={addFromTemplate}>Add</Button>
                  <Button size="xs" variant="default" onClick={() => { addAttacks(id, [{ ...options.attackDefaults, name: `Attack ${character.attacks.length + 1}` }]); setAttackIndex(character.attacks.length) }}>Blank</Button>
                </Group>
              </Stack>
            </Grid.Col>
            <Grid.Col span={8}>
              {attack ? (
                <Stack gap="sm">
                  <Group justify="space-between">
                    <Text fw={600}>{attack.name}</Text>
                    <Group gap={4}>
                      <Tooltip label="Duplicate"><ActionIcon variant="subtle" onClick={() => addAttacks(id, [{ ...attack }])}><IconCopy size={16} /></ActionIcon></Tooltip>
                      <Tooltip label="Delete"><ActionIcon variant="subtle" color="red" onClick={() => removeAttack(id, index)}><IconTrash size={16} /></ActionIcon></Tooltip>
                    </Group>
                  </Group>
                  <SimpleGrid cols={3} spacing="xs" verticalSpacing={4}>
                    {ATTACK_MAIN.map((field) => (
                      <FieldInput key={field.key} field={field} value={attack[field.key]} onChange={(v) => updateAttack(id, index, { [field.key]: v })} />
                    ))}
                  </SimpleGrid>
                  <FieldGroups groups={ATTACK_GROUPS} values={attack} onChange={(key, v) => updateAttack(id, index, { [key]: v })} columns={3} />
                </Stack>
              ) : <Text c="dimmed" size="sm">No attacks yet: add a weapon or spell.</Text>}
            </Grid.Col>
          </Grid>
        </Tabs.Panel>

        <Tabs.Panel value="bonuses">
          <FieldGroups groups={CHARACTER_GROUPS} values={character} onChange={set} columns={3} />
        </Tabs.Panel>
      </Tabs>
    </Drawer>
  )
}
