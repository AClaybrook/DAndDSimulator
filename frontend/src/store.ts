// The simulator's state, kept in the browser (localStorage) so edits are instant and survive a reload
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Attack, Character, Enemy, Settings } from './api'

// Plotly's default colors, the same order as the backend's plots, so a character's color matches its trace
export const COLORS = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52']
export const MAX_CHARACTERS = 8

export const uid = () => Math.random().toString(36).slice(2, 10)

export function uniqueName(name: string, taken: string[]): string {
  if (!taken.includes(name)) return name
  let n = 2
  while (taken.includes(`${name} (${n})`)) n += 1
  return `${name} (${n})`
}

interface SimulatorState {
  characters: Character[]
  enemy: Enemy | null
  settings: Settings
  setAll: (characters: Character[], enemy: Enemy) => void
  addCharacter: (character: Character) => void
  updateCharacter: (id: string, changes: Partial<Character>) => void
  removeCharacter: (id: string) => void
  copyCharacter: (id: string) => void
  updateAttack: (id: string, index: number, changes: Partial<Attack>) => void
  addAttacks: (id: string, attacks: Attack[]) => void
  removeAttack: (id: string, index: number) => void
  setEnemy: (enemy: Enemy) => void
  updateEnemy: (changes: Partial<Enemy>) => void
  updateSettings: (changes: Partial<Settings>) => void
}

const mapCharacter = (characters: Character[], id: string, change: (c: Character) => Character) =>
  characters.map((c) => (c.uid === id ? change(c) : c))

export const useSimulator = create<SimulatorState>()(
  persist(
    (set) => ({
      characters: [],
      enemy: null,
      settings: { graph: 'DPR Distribution', numRounds: 10000, roundsPerFight: 3, sweepParameter: 'Armor Class', ruleset: 'bg3', randomSeed: false },
      setAll: (characters, enemy) => set({ characters: characters.map((c) => ({ ...c, uid: c.uid ?? uid() })), enemy }),
      addCharacter: (character) =>
        set((s) => ({
          characters: s.characters.length >= MAX_CHARACTERS ? s.characters
            : [...s.characters, { ...character, uid: uid(), name: uniqueName(character.name, s.characters.map((c) => c.name)) }],
        })),
      updateCharacter: (id, changes) => set((s) => ({ characters: mapCharacter(s.characters, id, (c) => ({ ...c, ...changes })) })),
      removeCharacter: (id) => set((s) => ({ characters: s.characters.filter((c) => c.uid !== id) })),
      copyCharacter: (id) =>
        set((s) => {
          const original = s.characters.find((c) => c.uid === id)
          if (!original || s.characters.length >= MAX_CHARACTERS) return s
          const copy = structuredClone(original)
          return { characters: [...s.characters, { ...copy, uid: uid(), name: uniqueName(`${original.name} copy`, s.characters.map((c) => c.name)) }] }
        }),
      updateAttack: (id, index, changes) =>
        set((s) => ({
          characters: mapCharacter(s.characters, id, (c) => ({ ...c, attacks: c.attacks.map((a, i) => (i === index ? { ...a, ...changes } : a)) })),
        })),
      addAttacks: (id, attacks) => set((s) => ({ characters: mapCharacter(s.characters, id, (c) => ({ ...c, attacks: [...c.attacks, ...attacks] })) })),
      removeAttack: (id, index) =>
        set((s) => ({ characters: mapCharacter(s.characters, id, (c) => ({ ...c, attacks: c.attacks.filter((_, i) => i !== index) })) })),
      setEnemy: (enemy) => set({ enemy }),
      updateEnemy: (changes) => set((s) => ({ enemy: s.enemy ? { ...s.enemy, ...changes } : s.enemy })),
      updateSettings: (changes) => set((s) => ({ settings: { ...s.settings, ...changes } })),
    }),
    { name: 'dnd-simulator', version: 1 },
  ),
)
