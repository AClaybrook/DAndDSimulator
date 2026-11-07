import { Checkbox, Chip, Group, Stack, Text, Tooltip } from '@mantine/core'
import type { MemberResult, PlannerOptions } from '../../api'
import { Section } from '../../components/Layout'
import { ACTS, useParty } from '../../party'

// Buffs active in fights at each act, and the conditional item effects the build sets up
export function BuffsTab({ options, result }: { options: PlannerOptions; result: MemberResult | undefined }) {
  const { party, selected, update } = useParty()
  const build = party[selected]
  if (!build) return null
  const toggleBuff = (act: string, key: string) => update(selected, (b) => {
    const current = b.buffs[act] ?? []
    return { ...b, buffs: { ...b.buffs, [act]: current.includes(key) ? current.filter((k) => k !== key) : [...current, key] } }
  })
  const toggleCondition = (value: string) => update(selected, (b) => ({
    ...b, conditions: b.conditions.includes(value) ? b.conditions.filter((c) => c !== value) : [...b.conditions, value],
  }))
  const spells = options.buffs.filter((b) => !b.key.startsWith('elixir:'))
  const elixirs = options.buffs.filter((b) => b.key.startsWith('elixir:'))
  const chips = (act: string, list: typeof options.buffs) => (
    <Group gap={4}>
      {list.filter((b) => b.act <= Number(act)).map((b) => (
        <Tooltip key={b.key} label={b.notes || b.name} multiline w={280} openDelay={300}>
          <Chip size="xs" checked={(build.buffs[act] ?? []).includes(b.key)} onChange={() => toggleBuff(act, b.key)} variant={b.modelled ? 'filled' : 'outline'}>
            {b.name.replace('Elixir of ', '')}
          </Chip>
        </Tooltip>
      ))}
    </Group>
  )

  return (
    <Stack gap="md">
      {ACTS.map((a) => (
        <Section key={a} title={options.acts.find((x) => x.key === a)?.label} padding="sm">
          <Text size="xs" c="dimmed">Spells</Text>
          {chips(a, spells)}
          <Text size="xs" c="dimmed">Elixirs</Text>
          {chips(a, elixirs)}
        </Section>
      ))}
      <Section title="Conditional item effects" padding="sm">
        <Text size="xs" c="dimmed">Effects that need the build to set something up. Tick the ones it does every fight.</Text>
        {result?.conditions.length ? result.conditions.map((c) => (
          <Checkbox key={c.value} size="xs" label={c.label} checked={build.conditions.includes(c.value)} onChange={() => toggleCondition(c.value)} />
        )) : <Text size="sm" c="dimmed">None of this character's gear has conditional effects.</Text>}
      </Section>
    </Stack>
  )
}
