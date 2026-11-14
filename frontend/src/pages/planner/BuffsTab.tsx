import { Checkbox, Group, NumberInput, Stack, Switch, Table, Text, Tooltip } from '@mantine/core'
import { Fragment } from 'react'
import type { MemberResult, PlannerOptions } from '../../api'
import { Section } from '../../components/Layout'
import { ACTS, useParty } from '../../party'

// Buffs active in fights at each act, and the conditional item effects the build sets up
export function BuffsTab({ options, result }: { options: PlannerOptions; result: MemberResult | undefined }) {
  const { party, selected, update } = useParty()
  const build = party[selected]
  if (!build) return null
  // Elixirs and coatings are one at a time: ticking one clears the others of its kind at that act
  const kindOf = (key: string) => key.startsWith('elixir:') ? 'elixir' : options.buffs.find((b) => b.key === key)?.group || null
  const toggleBuff = (act: string, key: string) => update(selected, (b) => {
    const current = b.buffs[act] ?? []
    const kind = kindOf(key)
    const others = kind ? current.filter((k) => k === key || kindOf(k) !== kind) : current
    return { ...b, buffs: { ...b.buffs, [act]: current.includes(key) ? current.filter((k) => k !== key) : [...others, key] } }
  })
  const toggleCondition = (value: string) => update(selected, (b) => ({
    ...b, conditions: b.conditions.includes(value) ? b.conditions.filter((c) => c !== value) : [...b.conditions, value],
  }))
  // The guesses behind this build's numbers, only the ones it uses: kills with Bloodlust, reaction attacks from its feats
  const feats = build.character?.feats ?? []
  const uses: Record<string, boolean> = {
    bloodlust_kills: ACTS.some((a) => (build.buffs[a] ?? []).includes('elixir:elixir_of_bloodlust')) || feats.includes('Great Weapon Master') || /gwm/i.test(build.preset),
    polearm_reactions: feats.includes('Polearm Master'), sentinel_reactions: feats.includes('Sentinel'), advantage_share: true,
  }
  const precast = (build.assumptions?.precast_buffs ?? 1) >= 0.5
  const assumptions = options.assumptions.filter((a) => uses[a.key])
  const setAssumption = (key: string, value: number | string) => update(selected, (b) => {
    const next = { ...(b.assumptions ?? {}) }
    if (value === '' || Number(value) === options.assumptions.find((a) => a.key === key)?.default) delete next[key]
    else next[key] = Math.max(Number(value), 0)
    return { ...b, assumptions: next }
  })
  const elixir = (b: { key: string }) => b.key.startsWith('elixir:')
  const groups: [string, string, typeof options.buffs][] = [
    ['Pre-combat: before each fight', precast ? 'Up before the fight starts, for the whole fight' : 'Put up in round 1: each costs that turn\'s action or bonus action',
      options.buffs.filter((b) => b.timing === 'fight' && !b.group)],
    ['Pre-combat: weapon coatings', 'One at a time, a bonus action, 10 turns (both hands when dual wielding)', options.buffs.filter((b) => b.group === 'coating')],
    ['Until a long rest', 'Cast or drunk in camp', options.buffs.filter((b) => b.timing === 'long_rest' && !elixir(b))],
    ['Elixirs', 'One at a time, until a long rest', options.buffs.filter(elixir)],
    ['During the fight', 'Their cost is in the numbers', options.buffs.filter((b) => b.timing === 'combat')],
  ]

  return (
    <Stack gap="md">
      <Table.ScrollContainer minWidth={300}>
        <Table verticalSpacing={3} horizontalSpacing={8} fz="sm">
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Active in fights</Table.Th>
              {ACTS.map((a) => <Table.Th key={a} ta="center" w={64}>Act {a}</Table.Th>)}
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {groups.map(([label, help, list]) => (
              <Fragment key={label}>
                <Table.Tr><Table.Td colSpan={ACTS.length + 1} pt="sm">
                  <Group justify="space-between" gap="xs" wrap="nowrap">
                    <Tooltip label={help} multiline w={280} openDelay={300}><Text className="section-label">{label}</Text></Tooltip>
                    {label === 'Pre-combat: before each fight' && (
                      <Tooltip label="Haste, Hex, coatings and other fight-long buffs up before the fight (like Sneak Attack from stealth), or put up in round 1 at the cost of that turn's action or bonus action. Applies to every number for this build" multiline w={300}>
                        <Switch size="xs" label="Before the fight" checked={precast} onChange={(e) => setAssumption('precast_buffs', e.currentTarget.checked ? 1 : 0)} />
                      </Tooltip>
                    )}
                  </Group>
                </Table.Td></Table.Tr>
                {list.map((b) => (
                  <Table.Tr key={b.key}>
                    <Table.Td>
                      <Tooltip label={b.notes || b.name} multiline w={300} openDelay={300}>
                        <Text size="sm" span>{b.name.replace('Elixir of ', '')}{!b.modelled && <Text span size="xs" c="dimmed"> · not in the damage</Text>}{!precast && b.timing === 'fight' && b.cost && <Text span size="xs" c="dimmed"> · {b.cost} in round 1</Text>}</Text>
                      </Tooltip>
                    </Table.Td>
                    {ACTS.map((a) => (
                      <Table.Td key={a} ta="center">
                        {b.act <= Number(a)
                          ? <Checkbox size="xs" aria-label={`${b.name}, Act ${a}`} checked={(build.buffs[a] ?? []).includes(b.key)} onChange={() => toggleBuff(a, b.key)} styles={{ root: { display: 'inline-flex' } }} />
                          : <Tooltip label={`Found from Act ${b.act}`}><Text span size="xs" c="dimmed">–</Text></Tooltip>}
                      </Table.Td>
                    ))}
                  </Table.Tr>
                ))}
              </Fragment>
            ))}
          </Table.Tbody>
        </Table>
      </Table.ScrollContainer>
      {assumptions.length > 0 && (
        <Section title="Estimates" padding="sm">
          <Group gap="md" wrap="wrap">
            {assumptions.map((a) => (
              <Tooltip key={a.key} label={`${a.help}. Usually ${a.default}`} multiline w={260} openDelay={300}>
                <NumberInput size="xs" w={210} label={a.label} min={0} max={a.key === 'advantage_share' ? 1 : 6} step={a.key === 'advantage_share' ? 0.1 : 0.5} decimalScale={1} placeholder={String(a.default)}
                  value={build.assumptions?.[a.key] ?? a.default} onChange={(v) => setAssumption(a.key, v)} />
              </Tooltip>
            ))}
          </Group>
        </Section>
      )}
      <Section title="Conditional item effects" padding="sm">
        <Text size="xs" c="dimmed">Effects that need the build to set something up. Tick the ones it does every fight.</Text>
        {result?.conditions.length ? result.conditions.map((c) => (
          <Checkbox key={c.value} size="xs" label={c.label} checked={build.conditions.includes(c.value)} onChange={() => toggleCondition(c.value)} />
        )) : <Text size="sm" c="dimmed">None of this character's gear has conditional effects.</Text>}
      </Section>
    </Stack>
  )
}
