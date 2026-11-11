import { ActionIcon, Button, Collapse, Group, Menu, Modal, Paper, Select, SimpleGrid, Stack, Text, TextInput, Tooltip } from '@mantine/core'
import { IconFileImport, IconPlus, IconTrash, IconUserPlus } from '@tabler/icons-react'
import { useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { bg3, type Evaluation, type PlannerOptions } from '../../api'
import { ACTS, useParty } from '../../party'
import { classLine } from '../../format'
import { colorAt, useColors } from '../../theme'

// The party at a glance: each member's damage in every act; click one to edit it
export function PartyStrip({ options, evaluation, enemies }: { options: PlannerOptions; evaluation: Evaluation | undefined; enemies: number }) {
  const { party, selected, select, add, remove, together } = useParty()
  const [adding, setAdding] = useState<'example' | 'preset' | null>(null)
  const [choice, setChoice] = useState<string | null>(null)
  const full = party.length >= options.maxPartySize
  const colors = useColors()
  const queryClient = useQueryClient()
  const [importOpen, setImportOpen] = useState(false)
  const [docUrl, setDocUrl] = useState('')
  const [importing, setImporting] = useState(false)
  const [imported, setImported] = useState<string | null>(null)

  // Replaces the "Doc:" example builds with the document's current builds, then reloads the example list
  const importDoc = async () => {
    setImporting(true)
    try {
      const result = await bg3.importDoc(docUrl)
      if (result.problems) setImported(result.problems.join('; '))
      else {
        const notes = (result.builds ?? []).reduce((n, b) => n + b.notes.length, 0)
        setImported(`Imported ${result.builds?.length} builds${notes ? `, ${notes} notes on guessed or unmatched details (in each build's notes)` : ''}`)
        await queryClient.invalidateQueries({ queryKey: ['planner-options'] })
        await queryClient.invalidateQueries({ queryKey: ['leaderboard'] })
      }
    } catch (e) {
      setImported(String(e))
    } finally { setImporting(false) }
  }

  const addChosen = async () => {
    if (!choice) return
    if (adding === 'example') add(await bg3.example(choice))
    else add({ name: options.presets.find((p) => p.key === choice)?.label ?? 'Character', preset: choice, equipment: {}, buffs: {}, conditions: [], levels: {},
      character: null, carried: [], roles: [], variants: [], advantage: false, assumptions: {} })
    setAdding(null)
    setChoice(null)
  }
  const addCustom = () => add({ name: 'Custom character', preset: 'fighter_gwm', equipment: {}, buffs: {}, conditions: [], levels: {},
    character: { ...options.builder.defaultCharacter, name: 'Custom character' }, carried: [], roles: [], variants: [], advantage: false, assumptions: {} })

  return (
    <>
      <SimpleGrid cols={{ base: 1, sm: 2, lg: Math.min(party.length + (full ? 0 : 1), 5) }} spacing="sm">
        {party.map((b, i) => {
          const result = evaluation?.members[i]
          return (
            <Paper key={b.uid} p="sm" withBorder onClick={() => select(i)}
              style={{ cursor: 'pointer', borderTop: `3px solid ${colorAt(colors, i)}`, outline: i === selected ? `2px solid ${colorAt(colors, i)}` : undefined }}>
              <Group justify="space-between" wrap="nowrap" align="flex-start">
                <div style={{ minWidth: 0 }}>
                  <Text fw={600} truncate>{b.name}</Text>
                  <Text size="xs" c="dimmed" truncate>{classLine(b, options)}</Text>
                </div>
                <Tooltip label="Remove from the party">
                  <ActionIcon variant="subtle" color="gray" size="sm" onClick={(e) => { e.stopPropagation(); remove(i) }} aria-label="Remove"><IconTrash size={14} /></ActionIcon>
                </Tooltip>
              </Group>
              <Group gap="md" mt={6} wrap="nowrap">
                {ACTS.map((a) => (
                  <div key={a}>
                    <Text size="10px" c="dimmed" tt="uppercase">Act {a}</Text>
                    <Text fw={700} className="numeric">{result ? (together ? result.acts[a].together : result.acts[a].damage)[enemies - 1].toFixed(1) : '–'}</Text>
                  </div>
                ))}
                <Tooltip multiline w={320} disabled={!result} label={result && ACTS.map((a) => (
                  <div key={a}>Act {a}: {result.acts[a].acParts.map((p) => `${p.source} ${p.value}`).join(' + ')} (hit {Math.round(100 * result.acts[a].hitChance)}% of the time)</div>
                ))}>
                  <div>
                    <Text size="10px" c="dimmed" tt="uppercase">AC</Text>
                    <Text fw={700} className="numeric">{result ? ACTS.map((a) => result.acts[a].ac).join('/') : '–'}</Text>
                  </div>
                </Tooltip>
                {result && ACTS.some((a) => result.acts[a].spellDc != null) && (
                  <Tooltip multiline w={340} label={ACTS.filter((a) => result.acts[a].saves.length).map((a) => (
                    <div key={a}>Act {a}: {result.acts[a].saves.map((s) => `${s.name} ${s.stat.slice(0, 3).toUpperCase()} ${s.dc}, fails ${Math.round(100 * s.fail)}%${s.disadvantage ? ' (disadvantage)' : ''}`).join('; ')}</div>
                  ))}>
                    <div>
                      <Text size="10px" c="dimmed" tt="uppercase">Spell DC</Text>
                      <Text fw={700} className="numeric">{ACTS.map((a) => result.acts[a].spellDc ?? '–').join('/')}</Text>
                    </div>
                  </Tooltip>
                )}
              </Group>
            </Paper>
          )
        })}
        {!full && (
          <Paper p="sm" withBorder style={{ borderStyle: 'dashed', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Menu position="bottom">
              <Menu.Target><Button variant="subtle" leftSection={<IconUserPlus size={16} />}>Add a character</Button></Menu.Target>
              <Menu.Dropdown>
                <Menu.Item onClick={() => setAdding('example')}>From an example build...</Menu.Item>
                <Menu.Item onClick={() => setAdding('preset')}>From a class preset...</Menu.Item>
                <Menu.Item onClick={addCustom}>Custom character (race, classes, feats)</Menu.Item>
              </Menu.Dropdown>
            </Menu>
          </Paper>
        )}
      </SimpleGrid>
      <Modal opened={adding !== null} onClose={() => setAdding(null)} title={adding === 'example' ? 'Add an example build' : 'Add a class preset'}>
        <Stack>
          <Select searchable label={adding === 'example' ? 'Build' : 'Class preset'} value={choice} onChange={setChoice}
            data={adding === 'example' ? options.examples.map((e) => ({ value: e.name, label: e.name })) : options.presets.map((p) => ({ value: p.key, label: p.label }))} />
          <Button leftSection={<IconPlus size={14} />} onClick={addChosen} disabled={!choice}>Add</Button>
          {adding === 'example' && !options.readOnly && (
            <>
              <Button variant="subtle" size="xs" leftSection={<IconFileImport size={14} />} onClick={() => setImportOpen((o) => !o)}>
                Re-import builds from the build doc
              </Button>
              <Collapse expanded={importOpen}>
                <Stack gap="xs">
                  <TextInput size="xs" label="Document link" description="A Google Doc shared by link, with 'Build N: Title' sections (docs/bg3_build_format.md). Read only"
                    placeholder="https://docs.google.com/document/d/..." value={docUrl} onChange={(e) => setDocUrl(e.currentTarget.value)} />
                  <Button size="xs" variant="light" loading={importing} disabled={!docUrl} onClick={importDoc}>Import</Button>
                  {imported && <Text size="xs" c={imported.startsWith('Imported') ? 'teal' : 'red'}>{imported}</Text>}
                </Stack>
              </Collapse>
            </>
          )}
        </Stack>
      </Modal>
    </>
  )
}
