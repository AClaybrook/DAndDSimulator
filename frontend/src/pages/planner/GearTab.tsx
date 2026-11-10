import { Alert, Button, Checkbox, Group, SegmentedControl, Select, Stack, Switch, Table, Text, Tooltip } from '@mantine/core'
import { useMediaQuery } from '@mantine/hooks'
import { IconWand } from '@tabler/icons-react'
import { useMemo, useState } from 'react'
import { bg3, type ItemOption, type MemberResult, type PlannerOptions } from '../../api'
import { ACTS, useParty } from '../../party'

// Slots down, acts across. An empty cell keeps the item from the act before (shown as its placeholder).
// Only the slots with an item show until more are asked for; on a narrow screen one act at a time
export function GearTab({ options, result }: { options: PlannerOptions; result: MemberResult | undefined }) {
  const { party, selected, update, replace } = useParty()
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
  const applyKit = async () => {
    if (!kit) return
    const result = await bg3.kit(party, selected, kit, kitAct, skipTaken, onlyEmpty)
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
        <Select size="xs" label="Quick gear from a kit" placeholder="Pick a kit..." w={200} value={kit} onChange={setKit} clearable
          data={options.kits.map((k) => ({ value: k.key, label: k.name }))} />
        <Select size="xs" label="At" w={90} value={kitAct} onChange={(v) => v && setKitAct(v)} allowDeselect={false} data={ACTS.map((a) => ({ value: a, label: `Act ${a}` }))} />
        <Checkbox size="xs" label="Skip items others wear" checked={skipTaken} onChange={(e) => setSkipTaken(e.currentTarget.checked)} mb={6} />
        <Checkbox size="xs" label="Only empty slots" checked={onlyEmpty} onChange={(e) => setOnlyEmpty(e.currentTarget.checked)} mb={6} />
        <Button size="xs" leftSection={<IconWand size={14} />} disabled={!kit} onClick={applyKit}>Fill</Button>
      </Group>
      {chosenKit && <Text size="xs" c="dimmed">{chosenKit.trigger}. {chosenKit.fits ? `Fits ${chosenKit.fits}.` : ''}</Text>}
      {message && <Alert py={6} color="blue" withCloseButton onClose={() => setMessage(null)}>{message}</Alert>}
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
      <Text size="xs" c="dimmed">Empty cells keep the item from the act before (↳). Red cells are in a conflict, see Conflicts. ✦ items have modelled effects, ⚠ items can be missed (hover for why).</Text>
    </Stack>
  )
}
