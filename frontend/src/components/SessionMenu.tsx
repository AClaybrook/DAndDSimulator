// Export or import everything kept in the browser (simulator characters, enemy, settings and the BG3 party) as one JSON file
import { ActionIcon, FileButton, Menu, Text, Tooltip } from '@mantine/core'
import { IconDeviceFloppy, IconDownload, IconUpload } from '@tabler/icons-react'
import { useRef, useState } from 'react'
import type { Build, Character, Enemy, Settings } from '../api'
import { download } from '../format'
import { useParty } from '../party'
import { MAX_CHARACTERS, uid, useSimulator } from '../store'

// The same file format as the old Dash app's exports (version 2), so older files still import
const SETTINGS: [keyof Settings, string][] = [
  ['numRounds', 'num_rounds'], ['roundsPerFight', 'rounds_per_fight'], ['graph', 'graph'], ['sweepParameter', 'sweep_parameter'], ['ruleset', 'ruleset'],
]
const withoutUid = <T extends { uid?: string }>(items: T[]) => items.map(({ uid: _uid, ...rest }) => rest)

function exportSession() {
  const { characters, enemy, settings } = useSimulator.getState()
  const { party, enemies, attackBonus, collected } = useParty.getState()
  const session = {
    version: 3,
    saved_at: new Date().toISOString().slice(0, 19),
    characters: withoutUid(characters),
    enemy,
    settings: Object.fromEntries(SETTINGS.map(([key, file]) => [file, settings[key]])),
    bg3_party: withoutUid(party),
    bg3_settings: { enemies, attack_bonus: attackBonus, collected },
  }
  download(`damage_lab_${session.saved_at.slice(0, 10)}.json`, JSON.stringify(session, null, 1), 'application/json')
}

// A session, or an older export that is a list of characters or a single character. Returns what was loaded
function importSession(data: unknown): string {
  const session = (Array.isArray(data) ? { characters: data } : data && typeof data === 'object' && !('characters' in data) && 'attacks' in data
    ? { characters: [data] } : data) as Record<string, unknown> | null
  if (!session || typeof session !== 'object' || !Array.isArray(session.characters)) throw new Error("The file doesn't contain characters")
  const characters = (session.characters as Character[]).filter((c) => c && typeof c.name === 'string' && Array.isArray(c.attacks)).slice(0, MAX_CHARACTERS)
  const simulator = useSimulator.getState()
  const enemy = (session.enemy as Enemy | null) ?? simulator.enemy
  if (enemy) simulator.setAll(characters, enemy)
  else useSimulator.setState({ characters: characters.map((c) => ({ ...c, uid: uid() })) })
  const settings = (session.settings ?? {}) as Record<string, unknown>
  simulator.updateSettings(Object.fromEntries(SETTINGS.filter(([, file]) => settings[file] != null).map(([key, file]) => [key, settings[file]])))
  const loaded = [`${characters.length} character${characters.length === 1 ? '' : 's'}`]
  if (session.enemy) loaded.push(`the enemy (${(session.enemy as Enemy).name})`)
  if (Array.isArray(session.bg3_party)) {
    const party = useParty.getState()
    party.setParty(session.bg3_party as Build[])
    const extra = (session.bg3_settings ?? {}) as { enemies?: number; attack_bonus?: number | null; collected?: string[] }
    if (extra.enemies) party.setEnemies(extra.enemies)
    if (extra.attack_bonus !== undefined) party.setAttackBonus(extra.attack_bonus)
    if (extra.collected) useParty.setState({ collected: extra.collected })
    loaded.push(`a BG3 party of ${(session.bg3_party as Build[]).length}`)
  }
  return `Loaded ${loaded.join(', ')}`
}

export function SessionMenu() {
  const [message, setMessage] = useState<string | null>(null)
  const reset = useRef<() => void>(null)
  const onFile = async (file: File | null) => {
    if (!file) return
    try {
      setMessage(importSession(JSON.parse(await file.text())))
    } catch (e) {
      setMessage(`Import failed: ${e instanceof Error ? e.message : String(e)}`)
    }
    reset.current?.()
  }

  return (
    <Menu position="bottom-end" width={260} onClose={() => setMessage(null)}>
      <Menu.Target>
        <Tooltip label="Save or load a session">
          <ActionIcon variant="default" size="lg" aria-label="Session"><IconDeviceFloppy size={18} /></ActionIcon>
        </Tooltip>
      </Menu.Target>
      <Menu.Dropdown>
        <Menu.Label>Session: simulator and BG3 party</Menu.Label>
        <Menu.Item leftSection={<IconDownload size={14} />} onClick={exportSession}>Export to a file</Menu.Item>
        <FileButton onChange={onFile} accept="application/json,.json" resetRef={reset}>
          {(props) => <Menu.Item {...props} closeMenuOnClick={false} leftSection={<IconUpload size={14} />}>Import a file...</Menu.Item>}
        </FileButton>
        {message && <Text size="xs" px="sm" py={6} c={message.startsWith('Import failed') ? 'red' : 'teal'}>{message}</Text>}
      </Menu.Dropdown>
    </Menu>
  )
}
