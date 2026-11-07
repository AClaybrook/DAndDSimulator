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
