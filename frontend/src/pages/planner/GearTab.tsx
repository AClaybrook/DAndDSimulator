import { Alert, Anchor, Button, Checkbox, Group, SegmentedControl, Select, Stack, Switch, Table, Text, Tooltip } from '@mantine/core'
import { useMediaQuery } from '@mantine/hooks'
import { IconWand } from '@tabler/icons-react'
import { useMemo, useState } from 'react'
import { bg3, type Build, type ItemOption, type MemberResult, type PlannerOptions } from '../../api'
import { ACTS, useParty } from '../../party'
import { useSharedEnemy } from './usePlanner'

const GOALS = [{ value: 'damage', label: 'Most damage' }, { value: 'ac', label: 'Highest armour class' }, { value: 'score', label: 'Best overall score' }]

// Slots down, acts across. An empty cell keeps the item from the act before (shown as its placeholder).
// Only the slots with an item show until more are asked for; on a narrow screen one act at a time
export function GearTab({ options, result }: { options: PlannerOptions; result: MemberResult | undefined }) {
  const { party, selected, update, replace, enemies, attackBonus } = useParty()
  const { enemy, rounds } = useSharedEnemy()
  const [mode, setMode] = useState('best') // Quick fill: the best gear found by search, or a curated kit
  const [goal, setGoal] = useState('damage')
  const [bestActs, setBestActs] = useState('3')
  const [weapons, setWeapons] = useState(true)
  const [busy, setBusy] = useState(false)
  const [undo, setUndo] = useState<Build | null>(null) // The build before the last fill
  const build = party[selected]
  const [kit, setKit] = useState<string | null>(null)
  const [kitAct, setKitAct] = useState('1')
  const [skipTaken, setSkipTaken] = useState(true)
  const [onlyEmpty, setOnlyEmpty] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [added, setAdded] = useState<string[]>([]) // Empty slots the user opened
  const [all, setAll] = useState(false)
  const [phoneAct, setPhoneAct] = useState('1')
  const narrow = useMediaQuery('(max-width: 48em)')

  const itemsFor = useMemo(() => {
    const cache: Record<string, ItemOption[]> = {}
    return (group: string) => (cache[group] ??= group.split('+').flatMap((g) => options.items[g] ?? []))
  }, [options.items])
  const dataFor = (group: string, act: string) =>
    itemsFor(group).filter((o) => o.act == null || o.act <= Number(act)).map((o) => ({ value: o.value, label: o.label }))
  const titles = useMemo(() => Object.fromEntries(Object.values(options.items).flat().map((o) => [o.value, o.title])), [options.items])

  if (!build) return null
  const setItem = (act: string, slot: string, value: string | null) =>
    update(selected, (b) => {
      const gear = { ...(b.equipment[act] ?? {}) }
      if (value) gear[slot] = value
      else delete gear[slot]
      return { ...b, equipment: { ...b.equipment, [act]: gear } }
    })
  // Best in slot: searched from every item found by the act, for this build against the current enemy. apply: wear it; otherwise it
  // is kept as a variant to compare next to the build first
  const fillBest = async (apply: boolean) => {
    setBusy(true)
    try {
      const acts = bestActs === 'all' ? ACTS : [bestActs]
      const result = await bg3.bestGear(party, selected, acts, goal, enemy, rounds, enemies, attackBonus, weapons, skipTaken)
      const where = bestActs === 'all' ? 'every act' : `Act ${bestActs}`
      if (!result.changes.length) { setMessage(`Nothing found by ${where} beats what ${build.name.split(' (')[0]} already wears for ${result.goal.toLowerCase()}.`); return }
      const listed = result.changes.map((c) => `${acts.length > 1 ? `Act ${c.act} ` : ''}${c.slot}: ${c.before || 'empty'} → ${c.after || 'empty'} (+${c.gain})`).join('; ')
      if (apply) {
        setUndo(build)
        replace(selected, result.build)
        setMessage(`${result.goal} gear at ${where}. ${listed}`)
      } else {
        update(selected, (b) => ({ ...b, variants: [...b.variants, { name: `${result.goal} gear (${where})`, gear: result.gear }] }))
        setMessage(`Added as a variant to compare (Variants tab), your gear is unchanged. ${listed}`)
      }
    } finally { setBusy(false) }
  }
  const applyKit = async () => {
    if (!kit) return
    const result = await bg3.kit(party, selected, kit, kitAct, skipTaken, onlyEmpty)
    setUndo(build)
    replace(selected, result.build)
    setMessage(`Placed ${result.placed.join(', ') || 'nothing (every kit slot already had an item)'}` + (result.blocked.length ? `. Taken by another character: ${result.blocked.join(', ')}` : ''))
  }
  const chosenKit = options.kits.find((k) => k.key === kit)
  const used = (slot: string) => ACTS.some((a) => build.equipment[a]?.[slot] || result?.acts[a]?.inherited[slot])
  const rows = options.slots.filter((s) => all || used(s.key) || added.includes(s.key))
  const hidden = options.slots.filter((s) => !rows.includes(s))
  const acts = narrow ? [phoneAct] : ACTS
  // The two ring slots share a label, so the picker numbers them
  const slotName = (s: (typeof options.slots)[number]) => {
    const twins = options.slots.filter((x) => x.label === s.label)
    return twins.length > 1 ? `${s.label} ${twins.indexOf(s) + 1}` : s.label
  }

  return (
    <Stack gap="sm">
      <Group gap="xs" align="flex-end" wrap="wrap">
        <div>
          <Text size="xs" fw={500} mb={2}>Quick gear</Text>
          <SegmentedControl size="xs" value={mode} onChange={setMode} data={[{ value: 'best', label: 'Best in slot' }, { value: 'kit', label: 'Kit' }]} />
        </div>
        {mode === 'best' ? (
          <>
            <Select size="xs" label="For" w={180} value={goal} onChange={(v) => v && setGoal(v)} allowDeselect={false} data={GOALS} />
            <Select size="xs" label="At" w={110} value={bestActs} onChange={(v) => v && setBestActs(v)} allowDeselect={false}
              data={[...ACTS.map((a) => ({ value: a, label: `Act ${a}` })), { value: 'all', label: 'Every act' }]} />
            <Checkbox size="xs" label="Weapon too" checked={weapons} onChange={(e) => setWeapons(e.currentTarget.checked)} mb={6} />
          </>
        ) : (
          <>
            <Select size="xs" label="Kit" placeholder="Pick a kit..." w={200} value={kit} onChange={setKit} clearable data={options.kits.map((k) => ({ value: k.key, label: k.name }))} />
            <Select size="xs" label="At" w={90} value={kitAct} onChange={(v) => v && setKitAct(v)} allowDeselect={false} data={ACTS.map((a) => ({ value: a, label: `Act ${a}` }))} />
            <Checkbox size="xs" label="Only empty slots" checked={onlyEmpty} onChange={(e) => setOnlyEmpty(e.currentTarget.checked)} mb={6} />
          </>
        )}
        <Tooltip label="Leaves the rest of the party's items alone, so filling this character adds no conflicts" multiline w={260}>
          <Checkbox size="xs" label="Skip items others wear" checked={skipTaken} onChange={(e) => setSkipTaken(e.currentTarget.checked)} mb={6} />
        </Tooltip>
        {mode === 'best' ? (
          <>
            <Button size="xs" leftSection={<IconWand size={14} />} loading={busy} onClick={() => fillBest(true)}>Fill</Button>
            <Tooltip label="Keeps your gear and adds this set as a variant, shown next to the build in the Variants tab">
              <Button size="xs" variant="default" disabled={busy} onClick={() => fillBest(false)}>Compare first</Button>
            </Tooltip>
          </>
        ) : <Button size="xs" leftSection={<IconWand size={14} />} disabled={!kit} onClick={applyKit}>Fill</Button>}
      </Group>
      {mode === 'kit' && chosenKit && <Text size="xs" c="dimmed">{chosenKit.trigger}. {chosenKit.fits ? `Fits ${chosenKit.fits}.` : ''}</Text>}
      {message && (
        <Alert py={6} color="blue" withCloseButton onClose={() => { setMessage(null); setUndo(null) }}>
          {message}{undo && <> <Anchor size="sm" component="button" onClick={() => { replace(selected, undo); setUndo(null); setMessage(null) }}>Undo</Anchor></>}
        </Alert>
      )}
      {narrow && <SegmentedControl size="xs" fullWidth value={phoneAct} onChange={setPhoneAct} data={ACTS.map((a) => ({ value: a, label: `Act ${a}` }))} />}
      <Table.ScrollContainer minWidth={narrow ? 280 : 620}>
        <Table verticalSpacing={4} horizontalSpacing={6}>
          <Table.Thead>
            <Table.Tr>
              <Table.Th w={narrow ? 92 : 120}>Slot</Table.Th>
              {acts.map((a) => <Table.Th key={a}>{options.acts.find((x) => x.key === a)?.label}</Table.Th>)}
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {rows.length === 0 && <Table.Tr><Table.Td colSpan={acts.length + 1}><Text size="sm" c="dimmed">No gear yet. Add a slot below, or fill from a kit.</Text></Table.Td></Table.Tr>}
            {rows.map((slot) => (
              <Table.Tr key={slot.key}>
                <Table.Td><Text size="xs" fw={500}>{slot.label}</Text></Table.Td>
                {acts.map((a) => {
                  const value = build.equipment[a]?.[slot.key] ?? null
                  const flagged = result?.acts[a]?.flagged.includes(slot.key)
                  const inherited = result?.acts[a]?.inherited[slot.key]
                  return (
                    <Table.Td key={a}>
                      <Tooltip label={value ? titles[value] : ''} disabled={!value || !titles[value]} multiline w={320} openDelay={400}>
                        <Select size="xs" searchable clearable limit={60} value={value} onChange={(v) => setItem(a, slot.key, v)}
                          placeholder={inherited ? `↳ ${inherited}` : '—'} data={dataFor(slot.group, a)}
                          error={flagged ? true : undefined} nothingFoundMessage="No item" />
                      </Tooltip>
                    </Table.Td>
                  )
                })}
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      </Table.ScrollContainer>
      <Group gap="sm" wrap="wrap">
        {hidden.length > 0 && (
          <Select size="xs" w={190} placeholder={`Add a slot (${hidden.length} empty)...`} value={null} data={hidden.map((s) => ({ value: s.key, label: slotName(s) }))}
            onChange={(v) => v && setAdded((list) => [...list, v])} aria-label="Add a slot" />
        )}
        <Switch size="xs" label="Every slot" checked={all} onChange={(e) => setAll(e.currentTarget.checked)} />
      </Group>
      <Text size="xs" c="dimmed">↳ kept from the act before · red: conflict · ✦ modelled effects · ⚠ can be missed</Text>
    </Stack>
  )
}
