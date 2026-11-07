import { Group, Paper, Select, Text, TextInput, Title } from '@mantine/core'
import { api, type Options } from '../../api'
import { FieldGroups, FieldInput } from '../../components/FieldInput'
import { ENEMY_GROUPS, ENEMY_MAIN } from '../../fields'
import { useSimulator } from '../../store'

// The enemy: pick a monster or a challenge rating baseline, armor class and hit points up front, saves and resistances folded
export function EnemyPanel({ options }: { options: Options }) {
  const { enemy, setEnemy, updateEnemy } = useSimulator()
  if (!enemy) return null
  return (
    <Paper p="sm" withBorder>
      <Title order={5} mb="xs">Enemy</Title>
      <Select size="xs" placeholder="Load a monster or CR baseline..." data={options.enemies} searchable value={null}
        onChange={async (v) => v && setEnemy(await api.enemy(v))} mb="xs" />
      <Group grow gap="xs" mb="xs" align="start">
        <TextInput size="xs" label="Name" value={enemy.name} onChange={(e) => updateEnemy({ name: e.currentTarget.value })} />
        {ENEMY_MAIN.map((field) => (
          <FieldInput key={field.key} field={field} value={enemy[field.key]} onChange={(v) => updateEnemy({ [field.key]: v })} />
        ))}
      </Group>
      <FieldGroups groups={ENEMY_GROUPS} values={enemy} onChange={(key, v) => updateEnemy({ [key]: v })} />
      {(enemy.resistances as string[] | undefined)?.length ? <Text size="xs" c="dimmed" mt={4}>Resists {(enemy.resistances as string[]).join(', ')}</Text> : null}
    </Paper>
  )
}
