import { ActionIcon, Badge, Checkbox, Group, NumberInput, SegmentedControl, Select, SimpleGrid, Stack, Text, TextInput, Tooltip } from '@mantine/core'
import { IconPlus, IconX } from '@tabler/icons-react'
import type { Build, BuilderCharacter as Character, MemberResult, PlannerOptions } from '../../api'
import { Section } from '../../components/Layout'
import { STATS, statLabel } from '../../fields'
import { ACTS, useParty } from '../../party'

export function BuildTab({ options, result }: { options: PlannerOptions; result: MemberResult | undefined }) {
  const { party, selected, update } = useParty()
  const build = party[selected]
  if (!build) return null
  const set = (change: Partial<Build>) => update(selected, (b) => ({ ...b, ...change }))
  const character = build.character ?? null
  // A respec (the class split at an earlier act, from a build doc) belongs to the classes it was written for, so editing them drops it
  const setChar = (change: Partial<Character>) => update(selected, (b) => (b.character ? { ...b, character: { ...b.character, ...change, ...('classes' in change ? { respec: {} } : {}) } } : b))
  const b = options.builder
  const summary = result?.builder

  return (
    <Stack gap="md">
      <Group grow align="flex-end">
        <TextInput size="xs" label="Name" value={build.name} onChange={(e) => {
          const name = e.currentTarget.value
          update(selected, (x) => ({ ...x, name, character: x.character ? { ...x.character, name } : null }))
        }} />
        <div>
          <Text size="xs" fw={500} mb={2}>Character</Text>
          <SegmentedControl size="xs" fullWidth value={character ? 'custom' : 'preset'} data={[{ value: 'preset', label: 'Class preset' }, { value: 'custom', label: 'Custom' }]}
            onChange={(v) => set({ character: v === 'custom' ? { ...b.defaultCharacter, name: build.name } : null })} />
        </div>
      </Group>
      {!character && (
        <Select size="xs" label="Class preset" description="Levels up like the class: features, feats and attacks at each level" value={build.preset}
          onChange={(v) => v && set({ preset: v })} data={options.presets.map((p) => ({ value: p.key, label: p.label }))} searchable allowDeselect={false} />
      )}
      <div>
        <Text size="xs" fw={500} mb={4}>Level at each checkpoint</Text>
        <SimpleGrid cols={3} spacing="xs">
          {options.acts.map((a) => (
            <NumberInput key={a.key} size="xs" leftSection={<Text size="10px" c="dimmed">Act {a.key}</Text>} leftSectionWidth={44} min={1} max={12}
              value={build.levels[a.key] ?? a.level} onChange={(v) => {
                const level = Number(v) || a.level
                const levels = { ...build.levels }
                if (level === a.level) delete levels[a.key]
                else levels[a.key] = level
                set({ levels })
              }} />
          ))}
        </SimpleGrid>
      </div>

      {character && (
        <>
          <Section title="Race and abilities" padding="sm">
            <Group grow align="flex-end">
              <Select size="xs" label="Race" data={b.races} value={character.race} onChange={(v) => v && setChar({ race: v })} searchable allowDeselect={false} />
              <Select size="xs" label="+2" data={STATS.map((s) => ({ value: s, label: statLabel(s) }))} value={Object.keys(character.bonus).find((k) => character.bonus[k] === 2) ?? null}
                onChange={(v) => v && setChar({ bonus: { ...Object.fromEntries(Object.entries(character.bonus).filter(([k, n]) => n !== 2 && k !== v)), [v]: 2 } })} />
              <Select size="xs" label="+1" data={STATS.map((s) => ({ value: s, label: statLabel(s) }))} value={Object.keys(character.bonus).find((k) => character.bonus[k] === 1) ?? null}
                onChange={(v) => v && setChar({ bonus: { ...Object.fromEntries(Object.entries(character.bonus).filter(([k, n]) => n !== 1 && k !== v)), [v]: 1 } })} />
              <Tooltip label="Auntie Ethel's Hair (Act 1): a permanent +1 to one ability, up to 20">
                <Select size="xs" label="Hag's Hair +1" placeholder="None" clearable data={STATS.map((s) => ({ value: s, label: statLabel(s) }))}
                  value={Object.keys(character.boons ?? {})[0] ?? null} onChange={(v) => setChar({ boons: v ? { [v]: 1 } : {} })} />
              </Tooltip>
            </Group>
            <SimpleGrid cols={6} spacing={6}>
              {STATS.map((s) => (
                <NumberInput key={s} size="xs" label={statLabel(s)} min={8} max={15} hideControls value={character.scores[s] ?? 8}
                  onChange={(v) => setChar({ scores: { ...character.scores, [s]: Number(v) || 8 } })} />
              ))}
            </SimpleGrid>
            {summary && <Text size="xs" c={summary.pointBuy === 27 ? 'dimmed' : 'orange'}>Point buy: {summary.pointBuy ?? '?'} of 27 points (8 to 15 before the +2/+1)</Text>}
          </Section>

          <Section title="Classes, in the order levels are taken" padding="sm" actions={character.classes.length < 4 && (
            <ActionIcon size="sm" variant="light" onClick={() => setChar({ classes: [...character.classes, ['fighter', b.subclasses.fighter[0], 1]] })} aria-label="Add a class"><IconPlus size={14} /></ActionIcon>)}>
            {character.classes.map(([cls, sub, n], row) => (
              <Group key={row} gap="xs" wrap="nowrap">
                <Select size="xs" w={130} data={b.classes.map((c) => ({ value: c, label: c[0].toUpperCase() + c.slice(1) }))} value={cls} allowDeselect={false}
                  onChange={(v) => v && setChar({ classes: character.classes.map((r, i) => (i === row ? [v, b.subclasses[v]?.[0] ?? '', r[2]] : r)) })} />
                <Select size="xs" style={{ flex: 1 }} data={b.subclasses[cls] ?? []} value={sub || null} placeholder="Subclass"
                  onChange={(v) => setChar({ classes: character.classes.map((r, i) => (i === row ? [r[0], v ?? '', r[2]] : r)) })} />
                <NumberInput size="xs" w={80} min={1} max={12} value={n} suffix=" lvl"
                  onChange={(v) => setChar({ classes: character.classes.map((r, i) => (i === row ? [r[0], r[1], Number(v) || 1] : r)) })} />
                <ActionIcon size="sm" variant="subtle" color="gray" disabled={character.classes.length === 1}
                  onClick={() => setChar({ classes: character.classes.filter((_, i) => i !== row) })} aria-label="Remove class"><IconX size={14} /></ActionIcon>
              </Group>
            ))}
            {summary && (
              <Group gap={6}>
                {ACTS.map((a) => <Badge key={a} variant="light" size="sm">Act {a}: {Object.entries(summary.split[a] ?? {}).map(([c, n]) => `${c} ${n}`).join(' / ')}</Badge>)}
              </Group>
            )}
          </Section>

          <Section title="How it fights" padding="sm">
            <SimpleGrid cols={3} spacing="xs">
              <Select size="xs" label="Routine" data={b.routines} value={character.routine} onChange={(v) => v && setChar({ routine: v })} allowDeselect={false} />
              <Select size="xs" label="Cantrip" data={b.cantrips} value={character.cantrip} onChange={(v) => v && setChar({ cantrip: v })} allowDeselect={false} />
              <Select size="xs" label="Levelled spell" placeholder="None" clearable data={b.spells} value={character.spell || null} onChange={(v) => setChar({ spell: v ?? '' })} />
            </SimpleGrid>
            {summary && summary.toggles.length > 0 && (
              <Group gap="md">
                {summary.toggles.map((t) => {
                  // 'Honour Mode rules: Haste's ...' -> 'Honour Mode rules', the rest on hover
                  const short = t.label.split(/: | \(/)[0]
                  return (
                    <Tooltip key={t.value} label={t.label} disabled={short === t.label} multiline w={320} openDelay={300}>
                      <div>
                        <Checkbox size="xs" label={short} checked={Boolean(character.toggles?.[t.value] ?? t.on)}
                          onChange={(e) => setChar({ toggles: { ...character.toggles, [t.value]: e.currentTarget.checked } })} />
                      </div>
                    </Tooltip>
                  )
                })}
              </Group>
            )}
          </Section>

          <Section title={`Feats${summary ? ` (levels ${summary.featLevels.join(', ') || 'none'})` : ''}`} padding="sm">
            <SimpleGrid cols={2} spacing="xs">
              {(summary?.featLevels ?? character.feats.map(() => 0)).map((level, i) => (
                <Select key={i} size="xs" searchable clearable placeholder={`Level ${level}`} data={b.improvements} value={character.feats[i] ?? null}
                  label={`Level ${level}`} onChange={(v) => {
                    const feats = [...character.feats]
                    feats[i] = v ?? ''
                    setChar({ feats: feats.filter((f, j) => f || j < i) })
                  }} />
              ))}
            </SimpleGrid>
            <SimpleGrid cols={2} spacing="xs">
              {[0, 1].map((i) => (
                <Select key={i} size="xs" clearable placeholder={`Fighting style ${i + 1}`} data={b.fightingStyles} value={character.fighting_styles[i] ?? null}
                  onChange={(v) => setChar({ fighting_styles: [...character.fighting_styles.slice(0, i), ...(v ? [v] : []), ...character.fighting_styles.slice(i + 1)].filter(Boolean) })} />
              ))}
            </SimpleGrid>
          </Section>

          {summary && (summary.problems.length > 0 || summary.notes.length > 0) && (
            <Stack gap={2}>
              {summary.problems.map((p) => <Text key={p} size="xs" c="orange">{p}</Text>)}
              {summary.notes.map((n) => <Text key={n} size="xs" c="dimmed">{n}</Text>)}
            </Stack>
          )}
        </>
      )}
    </Stack>
  )
}
