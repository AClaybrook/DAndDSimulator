import { Accordion, ActionIcon, Badge, Button, Drawer, Group, NumberInput, Select, SimpleGrid, Stack, Tabs, Text, Textarea, TextInput, Tooltip } from '@mantine/core'
import { IconCopy, IconPlus, IconTrash } from '@tabler/icons-react'
import { useState } from 'react'
import { api, type Attack, type Options, type Value } from '../../api'
import { FieldGroups, FieldInput } from '../../components/FieldInput'
import { ATTACK_GROUPS, ATTACK_MAIN, CHARACTER_GROUPS, STATS, statLabel } from '../../fields'
import { useSimulator } from '../../store'

interface Props {
  id: string | null
  options: Options
  attackDamage: Record<string, number> // Expected damage per round of each attack, by name
  onClose: () => void
}

// Everything about one character, in tabs: the stats first, attacks and bonuses one click away
export function CharacterEditor({ id, options, attackDamage, onClose }: Props) {
  const character = useSimulator((s) => s.characters.find((c) => c.uid === id))
  const { updateCharacter, updateAttack, addAttacks, removeAttack } = useSimulator()
  const ruleset = useSimulator((s) => s.settings.ruleset)
  const [template, setTemplate] = useState<string | null>(null)
  if (!character || !id) return <Drawer opened={false} onClose={onClose} />
  const set = (key: string, value: Value) => updateCharacter(id, { [key]: value })

  const addFromTemplate = async () => {
    if (!template) return
    const mainStat = STATS.reduce((best, s) => (Number(character[s]) > Number(character[best]) ? s : best), 'strength')
    addAttacks(id, await api.template(template, mainStat, character.level, ruleset))
    setTemplate(null)
  }

  return (
    <Drawer opened onClose={onClose} position="right" size="lg" title={<Text fw={600}>{character.name}</Text>}>
      <Tabs defaultValue="stats">
        <Tabs.List mb="sm">
          <Tabs.Tab value="stats">Stats</Tabs.Tab>
          <Tabs.Tab value="attacks">Attacks <Badge size="xs" variant="light" ml={4}>{character.attacks.length}</Badge></Tabs.Tab>
          <Tabs.Tab value="bonuses">Bonuses</Tabs.Tab>
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
            {character.preset ? <Text size="xs" c="dimmed">Built from the {String(character.preset)} preset. Editing it keeps your changes.</Text> : null}
            <Textarea size="xs" label="Notes" autosize minRows={2} value={String(character.description ?? '')} onChange={(e) => set('description', e.currentTarget.value)} />
          </Stack>
        </Tabs.Panel>

        <Tabs.Panel value="attacks">
          <Accordion variant="separated" multiple chevronPosition="left">
            {character.attacks.map((attack: Attack, index: number) => (
              <Accordion.Item key={index} value={String(index)}>
                <Group wrap="nowrap" gap={4} pr="xs">
                  <Accordion.Control>
                    <Group justify="space-between" wrap="nowrap">
                      <Text size="sm">{attack.name}</Text>
                      <Text size="xs" c="dimmed" className="numeric">
                        {attack.damage} {String(attack.damage_type ?? '')}
                        {attackDamage[attack.name] !== undefined ? ` · ${attackDamage[attack.name].toFixed(1)}/round` : ''}
                      </Text>
                    </Group>
                  </Accordion.Control>
                  <Tooltip label="Duplicate"><ActionIcon variant="subtle" onClick={() => addAttacks(id, [{ ...attack }])}><IconCopy size={14} /></ActionIcon></Tooltip>
                  <Tooltip label="Delete"><ActionIcon variant="subtle" color="red" onClick={() => removeAttack(id, index)}><IconTrash size={14} /></ActionIcon></Tooltip>
                </Group>
                <Accordion.Panel>
                  <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="xs" verticalSpacing={4} mb="sm">
                    {ATTACK_MAIN.map((field) => (
                      <FieldInput key={field.key} field={field} value={attack[field.key]} onChange={(v) => updateAttack(id, index, { [field.key]: v })} />
                    ))}
                  </SimpleGrid>
                  <FieldGroups groups={ATTACK_GROUPS} values={attack} onChange={(key, v) => updateAttack(id, index, { [key]: v })} />
                </Accordion.Panel>
              </Accordion.Item>
            ))}
          </Accordion>
          <Group mt="sm" gap="xs" align="end">
            <Select size="xs" style={{ flex: 1 }} label="Add an attack" placeholder="Weapon or spell..." data={options.attackTemplates} value={template}
              onChange={setTemplate} searchable />
            <Button size="xs" leftSection={<IconPlus size={14} />} disabled={!template} onClick={addFromTemplate}>Add</Button>
            <Button size="xs" variant="default" onClick={() => addAttacks(id, [{ ...options.attackDefaults, name: `Attack ${character.attacks.length + 1}` }])}>Blank</Button>
          </Group>
        </Tabs.Panel>

        <Tabs.Panel value="bonuses">
          <FieldGroups groups={CHARACTER_GROUPS} values={character} onChange={set} />
        </Tabs.Panel>
      </Tabs>
    </Drawer>
  )
}
