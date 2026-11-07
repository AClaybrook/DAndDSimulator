// The BG3 party, kept in the browser: edited in the planner, ranked in the leaderboard, its gear marked on the map
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Build } from './api'
import { uid, uniqueName } from './store'

export const ACTS = ['1', '2', '3']

interface PartyState {
  party: Build[]
  selected: number
  enemies: number // Damage summed over this many enemies (area spells, auras)
  attackBonus: number | null // The enemy's attack bonus for hit chances, null: from its challenge rating
  collected: string[] // Map: party items already picked up
  setParty: (party: Build[]) => void
  select: (index: number) => void
  add: (build: Build) => void
  replace: (index: number, build: Build) => void
  remove: (index: number) => void
  update: (index: number, change: (build: Build) => Build) => void
  setEnemies: (n: number) => void
  setAttackBonus: (bonus: number | null) => void
  toggleCollected: (key: string) => void
}

const withId = (b: Build): Build => ({ ...b, uid: b.uid ?? uid() })

export const useParty = create<PartyState>()(
  persist(
    (set) => ({
      party: [],
      selected: 0,
      enemies: 1,
      attackBonus: null,
      collected: [],
      setParty: (party) => set({ party: party.map(withId), selected: 0 }),
      select: (index) => set({ selected: index }),
      add: (build) => set((s) => ({
        party: [...s.party, withId({ ...build, uid: undefined, name: uniqueName(build.name, s.party.map((b) => b.name)) })],
        selected: s.party.length,
      })),
      replace: (index, build) => set((s) => ({ party: s.party.map((b, i) => (i === index ? withId({ ...build, uid: b.uid }) : b)) })),
      remove: (index) => set((s) => ({ party: s.party.filter((_, i) => i !== index), selected: Math.max(0, Math.min(s.selected, s.party.length - 2)) })),
      update: (index, change) => set((s) => ({ party: s.party.map((b, i) => (i === index ? change(b) : b)) })),
      setEnemies: (enemies) => set({ enemies }),
      setAttackBonus: (attackBonus) => set({ attackBonus }),
      toggleCollected: (key) => set((s) => ({ collected: s.collected.includes(key) ? s.collected.filter((k) => k !== key) : [...s.collected, key] })),
    }),
    { name: 'bg3-party', version: 1 },
  ),
)

// Gear at an act: later acts keep earlier items until a slot is changed (mirrors bg3.build.equipment_at)
export function equipmentAt(build: Build, act: string): Record<string, string> {
  const gear: Record<string, string> = {}
  for (const a of ACTS.slice(0, ACTS.indexOf(act) + 1)) Object.assign(gear, build.equipment[a] ?? {})
  return Object.fromEntries(Object.entries(gear).filter(([, v]) => v))
}
