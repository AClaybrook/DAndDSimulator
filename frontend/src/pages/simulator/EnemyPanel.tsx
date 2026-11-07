import { Badge, Button, Drawer, Group, Paper, Select, SimpleGrid, Stack, Text, TextInput } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { IconPencil } from '@tabler/icons-react'
import { api, type Options } from '../../api'
import { FieldGroups, FieldInput } from '../../components/FieldInput'
import { ENEMY_GROUPS, ENEMY_MAIN, STATS, statLabel } from '../../fields'
import { useSimulator } from '../../store'

// The enemy at a glance: what it is, its armor class and hit points, what it resists. Everything else in the editor
export function EnemyPanel({ options }: { options: Options }) {
  const { enemy, setEnemy, updateEnemy } = useSimulator()
  const [editing, { open, close }] = useDisclosure(false)
  if (!enemy) return null
  const lists = ['resistances', 'vulnerabilities', 'immunities'] as const
  const saves = STATS.map((s) => [s, enemy[`${s}_save`]] as const).filter(([, v]) => v !== null && v !== undefined)

  return (
    <Paper p="md" withBorder>
      <Group justify="space-between" mb="xs">
        <Text fw={600}>Enemy</Text>
        <Button size="compact-xs" variant="subtle" leftSection={<IconPencil size={12} />} onClick={open}>Edit</Button>
      </Group>
      <Select size="xs" placeholder="Load a monster or CR baseline..." data={options.enemies} searchable value={null}
        onChange={async (v) => v && setEnemy(await api.enemy(v))} mb="sm" />
      <Group justify="space-between" align="flex-end">
        <div>
          <Text fw={600}>{enemy.name}</Text>
          <Group gap={4} mt={4}>
            {lists.flatMap((k) => ((enemy[k] as string[] | undefined) ?? []).map((t) => (
              <Badge key={k + t} size="xs" variant="light" color={k === 'resistances' ? 'yellow' : k === 'immunities' ? 'red' : 'teal'}>{k === 'vulnerabilities' ? 'weak: ' : k === 'immunities' ? 'immune: ' : ''}{t}</Badge>
            )))}
            {saves.map(([s, v]) => <Badge key={s} size="xs" variant="outline" color="gray">{statLabel(s)} {Number(v) >= 0 ? '+' : ''}{String(v)}</Badge>)}
          </Group>
        </div>
        <Group gap="lg">
          <div><Text size="10px" c="dimmed" tt="uppercase">AC</Text><Text fz={22} fw={700} className="numeric">{enemy.armor_class}</Text></div>
          <div><Text size="10px" c="dimmed" tt="uppercase">HP</Text><Text fz={22} fw={700} className="numeric">{enemy.hit_points}</Text></div>
        </Group>
      </Group>
      <Drawer opened={editing} onClose={close} position="right" size="md" title={<Text fw={600}>Enemy</Text>}>
        <Stack gap="sm">
          <TextInput size="xs" label="Name" value={enemy.name} onChange={(e) => updateEnemy({ name: e.currentTarget.value })} />
          <SimpleGrid cols={2} spacing="xs">
            {ENEMY_MAIN.map((field) => <FieldInput key={field.key} field={field} value={enemy[field.key]} onChange={(v) => updateEnemy({ [field.key]: v })} />)}
          </SimpleGrid>
          <FieldGroups groups={ENEMY_GROUPS} values={enemy} onChange={(key, v) => updateEnemy({ [key]: v })} columns={3} />
        </Stack>
      </Drawer>
    </Paper>
  )
}
