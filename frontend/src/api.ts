// Typed calls to the FastAPI backend (api/main.py)

export type Value = string | number | boolean | null | string[] | undefined
export type Attack = Record<string, Value> & { name: string; damage: string }
export type Character = Record<string, Value | Attack[]> & { name: string; level: number; attacks: Attack[]; uid?: string }
export type Enemy = Record<string, Value> & { name: string; armor_class: number; hit_points: number }

export interface Options {
  presets: { key: string; label: string; class: string; description: string }[]
  rulesets: { key: string; label: string; maxLevel: number }[]
  enemies: { label: string; value: string }[]
  attackTemplates: { label: string; value: string }[]
  graphs: { key: string; description: string }[]
  sweepParameters: { key: string; description: string }[]
  attackDefaults: Attack
  characterDefaults: Record<string, Value>
  enemyDefaults: Enemy
}

export interface Expected {
  characters?: { name: string; damagePerRound: number; attacks: { name: string; damage: number }[] }[]
  problems?: string[]
}

export interface Table {
  title: string
  description: string
  columns: string[]
  rows: Value[][]
}

export interface Headline {
  unit: string
  context: string
  higherIsBetter: boolean
  values: { name: string; value: number }[]
}

export interface SimulationResult {
  figure?: { data: object[]; layout: Record<string, unknown> }
  headline?: Headline
  tables?: Table[]
  problems?: string[]
}

export interface Settings {
  graph: string
  numRounds: number
  roundsPerFight: number
  sweepParameter: string
  ruleset: string
  randomSeed: boolean
}

async function call<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(`/api${path}`, body === undefined ? undefined : {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!response.ok) throw new Error(`${path}: ${response.status} ${await response.text()}`)
  return response.json() as Promise<T>
}

// The backend ignores fields it doesn't know, so the client's uid can go along
export const api = {
  options: () => call<Options>('/simulator/options'),
  defaults: () => call<{ characters: Character[]; enemy: Enemy }>('/simulator/default'),
  preset: (preset: string, level: number, ruleset: string) => call<Character>('/simulator/preset', { preset, level, ruleset }),
  enemy: (value: string) => call<Enemy>(`/simulator/enemy?value=${encodeURIComponent(value)}`),
  template: (value: string, ability_stat: string, level: number, ruleset: string) =>
    call<Attack[]>('/simulator/template', { value, ability_stat, level, ruleset }),
  expected: (characters: Character[], enemy: Enemy, rounds_per_fight: number) =>
    call<Expected>('/simulator/expected', { characters, enemy, rounds_per_fight }),
  simulate: (characters: Character[], enemy: Enemy, s: Settings) =>
    call<SimulationResult>('/simulator/simulate', {
      characters, enemy, graph: s.graph, num_rounds: s.numRounds, rounds_per_fight: s.roundsPerFight,
      sweep_parameter: s.sweepParameter, ruleset: s.ruleset, seed: s.randomSeed ? null : 1,
    }),
}

// ---------- BG3: party planner, leaderboard, Act 1 map

export type Build = {
  name: string
  preset: string
  equipment: Record<string, Record<string, string>>
  buffs: Record<string, string[]>
  conditions: string[]
  levels: Record<string, number>
  character: Record<string, unknown> | null
  carried: string[]
  roles: string[]
  variants: Record<string, unknown>[]
  advantage: boolean
  uid?: string
}

export interface ItemOption { label: string; value: string; title: string; act: number | null }

export interface PlannerOptions {
  maxPartySize: number
  acts: { key: string; label: string; level: number }[]
  presets: { key: string; label: string }[]
  examples: { name: string; source: string }[]
  slots: { key: string; label: string; group: string }[]
  items: Record<string, ItemOption[]>
  buffs: { key: string; name: string; act: number; notes: string; modelled: boolean }[]
  kits: { key: string; name: string; act: number; theme: string; trigger: string; fits: string; synergy: string; notes: string; slots: Record<string, string[]> }[]
  quickVariants: { key: string; name: string; buffs?: string[]; toggles?: Record<string, boolean>; kit?: string }[]
  builder: {
    races: string[]; classes: string[]; subclasses: Record<string, string[]>; improvements: { value: string; label: string }[]
    fightingStyles: string[]; routines: { value: string; label: string }[]; cantrips: string[]; spells: string[]
    toggles: { value: string; label: string }[]; defaultCharacter: Record<string, unknown>
  }
  scoreWeights: Record<string, number>
  partLabels: Record<string, string>
  roleLabels: Record<string, string>
  coreRoles: string[]
  defaultParty: Build[]
}

export interface ActResult {
  level: number
  damage: number[] // Against 1, 2, 3 and 4 enemies
  ac: number
  acParts: { source: string; value: number }[]
  hitChance: number
  score: number
  scoreParts: Record<string, number>
  scoreNotes: Record<string, string>
  inherited: Record<string, string>
  flagged: string[]
}

export interface MemberResult {
  name: string
  acts: Record<string, ActResult>
  conditions: { label: string; value: string }[]
  builder: null | {
    pointBuy: number | null; featLevels: number[]; split: Record<string, Record<string, number>>; problems: string[]; notes: string[]
    toggles: { value: string; label: string }[]
  }
}

export interface Conflict { act: string; kind: string; message: string; members: string[]; item: string; gains: Record<string, number> }
export interface Evaluation { attackBonus: number; members: MemberResult[]; conflicts: Conflict[] }
export interface VariantRow { name: string; description: string; damage: number[]; ac: number[]; score: number[] }
export interface PartyAnalysis {
  roles: { name: string; roles: Record<string, string> }[]; missing: string[]; overlaps: string[]
  synergies: { key: string; text: string }[]; active: string[]
  damage: { name: string; alone: number; together: number }[]
  fight: { down_by_round: number[]; median_round: number; share: Record<string, number>; rounds: number; hit_points: number }
}
export interface Advice {
  values: { slot: string; item: string; summary: string; gain: number }[]
  suggestions: { key: string; item: string; summary: string; gain: number; act: number | null; users: string[] }[]
}

export interface LeaderboardOptions {
  scenarios: { key: string; label: string; note: string }[]
  enemyCounts: number[]
  variants: { key: string; label: string }[]
  sources: string[]
  referenceEnemies: Record<string, string>
  roundsPerFight: number
}

export interface LeaderboardEntry {
  key: string
  name: string
  source: string
  variant: string
  fingerprint: string
  spec: string
  gear_changes: string
  damage: Record<string, Record<string, number | null>> // "scenario@enemies": act: damage
  ac: Record<string, number | null>
  score: Record<string, number | null>
  advantage_source: Record<string, string>
  area?: Record<string, Record<string, string>>
  levels: Record<string, number>
  same_as?: string
}

export interface Run { id: number; created: string; label: string; kind: string; commit: string; count: number }

export interface MapPoint {
  name: string; key: string; rarity: string; slot: string; kind: string; source: string; notes: string; builds: string[]; tip: string
  location: string; where: string; trader: boolean; map: string; inside: boolean; x: number; y: number; px?: number; py?: number; missable?: string
}
export interface MapData {
  maps: { key: string; label: string; image: string | null; width: number | null; height: number | null }[]
  points: MapPoint[]
  unplaced: MapPoint[]
  rarities: string[]
  defaultRarities: string[]
  colors: Record<string, string>
  partyColor: string
  missableColor: string
}
export interface PartyGear { key: string; name: string; users: string[]; where: string; missable: string; placed: boolean; maps: string[] }

const strip = (party: Build[]) => party.map(({ uid: _uid, ...b }) => b)

export const bg3 = {
  plannerOptions: () => call<PlannerOptions>('/planner/options'),
  evaluate: (party: Build[], enemy: Enemy | null, rounds: number, attackBonus: number | null) =>
    call<Evaluation>('/planner/evaluate', { party: strip(party), enemy, rounds_per_fight: rounds, attack_bonus: attackBonus }),
  variants: (build: Build, enemy: Enemy | null, rounds: number, enemies: number, attackBonus: number) =>
    call<VariantRow[]>('/planner/variants', { build: strip([build])[0], enemy, rounds_per_fight: rounds, enemies, attack_bonus: attackBonus }),
  useVariant: (build: Build, index: number) => call<Build>('/planner/use-variant', { build: strip([build])[0], index }),
  kit: (party: Build[], selected: number, kit: string, act: string, skipTaken: boolean, onlyEmpty: boolean) =>
    call<{ build: Build; placed: string[]; blocked: string[] }>('/planner/kit', { party: strip(party), selected, kit, act, skip_taken: skipTaken, only_empty: onlyEmpty }),
  example: (name: string) => call<Build>(`/planner/example?name=${encodeURIComponent(name)}`),
  party: (party: Build[], act: string, active: string[] | null, enemy: Enemy | null, rounds: number, hitPoints: number) =>
    call<PartyAnalysis>('/planner/party', { party: strip(party), act, active, enemy, rounds_per_fight: rounds, hit_points: hitPoints }),
  advice: (build: Build, party: Build[], act: string, slot: string, enemy: Enemy | null, rounds: number) =>
    call<Advice>('/planner/advice', { build: strip([build])[0], party: strip(party), act, slot, enemy, rounds_per_fight: rounds }),
  leaderboardOptions: () => call<LeaderboardOptions>('/leaderboard/options'),
  leaderboard: (party: Build[]) => call<LeaderboardEntry[]>('/leaderboard/entries', { party: strip(party) }),
  runs: () => call<Run[]>('/leaderboard/runs'),
  run: (id: number) => call<LeaderboardEntry[]>(`/leaderboard/runs/${id}`),
  saveRun: (party: Build[], label: string, withVariants: boolean) =>
    call<{ id: number; rows: number }>('/leaderboard/save', { party: strip(party), label, with_variants: withVariants }),
  mapData: () => call<MapData>('/map/data'),
  partyGear: (party: Build[], act: string) => call<PartyGear[]>(`/map/party-gear?act=${act}`, { party: strip(party) }),
}
