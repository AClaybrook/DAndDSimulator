// Typed calls to the FastAPI backend (api/main.py). The shapes come from the backend's own schema (api-types.ts is generated from
// api/schemas.py); only the simulator's characters, attacks and enemy are declared here, as open records the editor fills field by field
import type * as T from './api-types'

export type {
  ActResult, Advice, Conflict, DistributionChart, Evaluation, Expected, Headline, ItemOption, LeaderboardEntry, LeaderboardOptions, LinesChart, MapData,
  MapPoint, MemberResult, Deconflict, DeconflictStep, PartyAnalysis, PartyGear, PlannerOptions, Run, SimulationResult, SweepChart, Table, VariantRow,
} from './api-types'

export type Value = string | number | boolean | null | string[] | undefined
export type Attack = Record<string, Value> & { name: string; damage: string }
export type Character = Record<string, Value | Attack[]> & { name: string; level: number; attacks: Attack[]; uid?: string }
export type Enemy = Record<string, Value> & { name: string; armor_class: number; hit_points: number }

export type Options = Omit<T.SimulatorOptions, 'attackDefaults' | 'characterDefaults' | 'enemyDefaults'> & {
  attackDefaults: Attack; characterDefaults: Record<string, Value>; enemyDefaults: Enemy
}
export type Chart = T.DistributionChart | T.SweepChart | T.LinesChart
export type BuilderCharacter = T.BuilderCharacter
// A planner build; uid is the browser's own handle on it and never sent
export type Build = T.Build & { uid?: string }

export interface Settings {
  graph: string
  numRounds: number
  roundsPerFight: number
  sweepParameter: string
  ruleset: string
  randomSeed: boolean
}

async function request(path: string, body?: unknown): Promise<Response> {
  const response = await fetch(`/api${path}`, body === undefined ? undefined : {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!response.ok) throw new Error(`${path}: ${response.status} ${await response.text()}`)
  return response
}

const call = async <T,>(path: string, body?: unknown): Promise<T> => (await request(path, body)).json() as Promise<T>

const simulation = (characters: Character[], enemy: Enemy, s: Settings) => ({
  characters, enemy, graph: s.graph, num_rounds: s.numRounds, rounds_per_fight: s.roundsPerFight,
  sweep_parameter: s.sweepParameter, ruleset: s.ruleset, seed: s.randomSeed ? null : 1,
})

// The backend ignores fields it doesn't know, so the client's uid can go along
export const api = {
  options: () => call<Options>('/simulator/options'),
  defaults: () => call<{ characters: Character[]; enemy: Enemy }>('/simulator/default'),
  preset: (preset: string, level: number, ruleset: string) => call<Character>('/simulator/preset', { preset, level, ruleset }),
  enemy: (value: string) => call<Enemy>(`/simulator/enemy?value=${encodeURIComponent(value)}`),
  template: (value: string, ability_stat: string, level: number, ruleset: string) =>
    call<Attack[]>('/simulator/template', { value, ability_stat, level, ruleset }),
  expected: (characters: Character[], enemy: Enemy, rounds_per_fight: number) =>
    call<T.Expected>('/simulator/expected', { characters, enemy, rounds_per_fight }),
  simulate: (characters: Character[], enemy: Enemy, s: Settings) => call<T.SimulationResult>('/simulator/simulate', simulation(characters, enemy, s)),
  // A copy of a character with one change (level up, Bless...), or why it can't be made
  variant: (character: Character, key: string) => call<{ character?: Character; problems?: string[] }>('/simulator/variant', { character, key }),
  // Raw simulated data as CSV text
  exportCsv: async (characters: Character[], enemy: Enemy, s: Settings, kind: string) =>
    (await request('/simulator/export', { ...simulation(characters, enemy, s), kind })).text(),
}

// ---------- BG3: party planner, leaderboard, item maps

const strip = (party: Build[]) => party.map(({ uid: _uid, ...b }) => b)

export const bg3 = {
  plannerOptions: () => call<T.PlannerOptions>('/planner/options'),
  evaluate: (party: Build[], enemy: Enemy | null, rounds: number, attackBonus: number | null) =>
    call<T.Evaluation>('/planner/evaluate', { party: strip(party), enemy, rounds_per_fight: rounds, attack_bonus: attackBonus }),
  variants: (build: Build, enemy: Enemy | null, rounds: number, enemies: number, attackBonus: number) =>
    call<T.VariantRow[]>('/planner/variants', { build: strip([build])[0], enemy, rounds_per_fight: rounds, enemies, attack_bonus: attackBonus }),
  useVariant: (build: Build, index: number) => call<Build>('/planner/use-variant', { build: strip([build])[0], index }),
  kit: (party: Build[], selected: number, kit: string, act: string, skipTaken: boolean, onlyEmpty: boolean) =>
    call<T.KitResult>('/planner/kit', { party: strip(party), selected, kit, act, skip_taken: skipTaken, only_empty: onlyEmpty }),
  // The best gear a member can wear at the acts, from everything found by then (goal: damage, ac or score)
  bestGear: (party: Build[], selected: number, acts: string[], goal: string, enemy: Enemy | null, rounds: number, enemies: number, attackBonus: number | null,
    weapons: boolean, skipTaken: boolean) =>
    call<T.BestGear>('/planner/best-gear', { party: strip(party), selected, acts, goal, enemy, rounds_per_fight: rounds, enemies, attack_bonus: attackBonus, weapons, skip_taken: skipTaken }),
  // Settles the items several members wear: who keeps each one, and what the others wear instead
  deconflict: (party: Build[], enemy: Enemy | null, rounds: number) => call<T.Deconflict>('/planner/deconflict', { party: strip(party), enemy, rounds_per_fight: rounds }),
  example: (name: string) => call<Build>(`/planner/example?name=${encodeURIComponent(name)}`),
  party: (party: Build[], act: string, active: string[] | null, enemy: Enemy | null, rounds: number, hitPoints: number) =>
    call<T.PartyAnalysis>('/planner/party', { party: strip(party), act, active, enemy, rounds_per_fight: rounds, hit_points: hitPoints }),
  advice: (build: Build, party: Build[], act: string, slot: string, enemy: Enemy | null, rounds: number) =>
    call<T.Advice>('/planner/advice', { build: strip([build])[0], party: strip(party), act, slot, enemy, rounds_per_fight: rounds }),
  leaderboardOptions: () => call<T.LeaderboardOptions>('/leaderboard/options'),
  leaderboard: (party: Build[]) => call<T.LeaderboardEntry[]>('/leaderboard/entries', { party: strip(party) }),
  runs: () => call<T.Run[]>('/leaderboard/runs'),
  run: (id: number) => call<T.LeaderboardEntry[]>(`/leaderboard/runs/${id}`),
  saveRun: (party: Build[], label: string, withVariants: boolean) =>
    call<T.Saved>('/leaderboard/save', { party: strip(party), label, with_variants: withVariants }),
  importDoc: (source: string) => call<T.ImportResult>('/planner/import-doc', { source }),
  toSimulator: (party: Build[], act: string | null, selected: number | null) =>
    call<Character[]>('/planner/to-simulator', { party: strip(party), act, selected }),
  mapData: () => call<T.MapData>('/map/data'),
  partyGear: (party: Build[], act: string) => call<T.PartyGear[]>(`/map/party-gear?act=${act}`, { party: strip(party) }),
}
