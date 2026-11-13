// Generated from the API's schema by `uv run python -m api.openapi`. Don't edit: change api/schemas.py and run it again

export interface AcPart {
  source: string
  value: number
}

export interface Act {
  key: string
  label: string
  level: number
}

export interface ActResult {
  level: number
  damage: number[]
  together: number[]
  spellDc?: number | null
  saves: SavingThrow[]
  ac: number
  acParts: AcPart[]
  hitChance: number
  score: number
  scoreParts: Record<string, number>
  scoreNotes: Record<string, string>
  inherited: Record<string, string>
  flagged: string[]
}

export interface Advice {
  values: ItemValue[]
  suggestions: Suggestion[]
}

export interface AdviceRequest {
  party: Build[]
  enemy?: Record<string, unknown> | null
  rounds_per_fight: number
  attack_bonus?: number | null
  synergies: boolean
  build: Build
  act: string
  slot: string
}

export interface Alternative {
  key: string
  item: string
  gain: number
}

export interface Assumption {
  key: string
  label: string
  default: number
  help: string
}

export interface AttackDamage {
  name: string
  damage: number
}

export interface BestGear {
  build: Build
  gear: Record<string, Record<string, string>>
  changes: GearChange[]
  kept: KeptItem[]
  goal: string
}

export interface BestGearRequest {
  party: Build[]
  enemy?: Record<string, unknown> | null
  rounds_per_fight: number
  attack_bonus?: number | null
  synergies: boolean
  selected: number
  acts: string[]
  goal: string
  enemies: number
  weapons: boolean
  skip_taken: boolean
  keep_uncounted: boolean
}

export interface Box {
  q1: number
  median: number
  q3: number
  low: number
  high: number
  mean: number
}

export interface Buff {
  key: string
  name: string
  act: number
  notes: string
  modelled: boolean
}

/** A planner build (bg3.build.Bg3Build) */
export interface Build {
  name: string
  preset: string
  equipment: Record<string, Record<string, string>>
  buffs: Record<string, string[]>
  conditions: string[]
  levels: Record<string, number>
  character?: BuilderCharacter | null
  carried: string[]
  roles: string[]
  variants: Record<string, unknown>[]
  advantage: boolean
  assumptions: Record<string, number>
}

/** A custom character (bg3.character.Bg3Character) */
export interface BuilderCharacter {
  name: string
  race: string
  scores: Record<string, number>
  bonus: Record<string, number>
  classes: [string, string, number][]
  feats: string[]
  fighting_styles: string[]
  routine: string
  cantrip: string
  spell: string
  toggles: Record<string, boolean | string>
  level_order: string[]
  boons: Record<string, number>
  respec: Record<string, [string, string, number][]>
}

export interface BuilderOptions {
  races: string[]
  classes: string[]
  subclasses: Record<string, string[]>
  improvements: Choice[]
  fightingStyles: string[]
  routines: Choice[]
  cantrips: string[]
  spells: string[]
  toggles: Toggle[]
  defaultCharacter: BuilderCharacter
}

export interface BuilderSummary {
  pointBuy?: number | null
  featLevels: number[]
  split: Record<string, Record<string, number>>
  problems: string[]
  notes: string[]
  toggles: Toggle[]
}

export interface Choice {
  value: string
  label: string
}

export interface Conflict {
  act: string
  kind: string
  message: string
  members: string[]
  item: string
  gains: Record<string, number>
}

export interface Curve {
  kind: 'exact' | 'fit'
  start: number[]
  percent: number[]
}

export interface Deconflict {
  party: Build[]
  steps: DeconflictStep[]
  remaining: number
}

export interface DeconflictStep {
  act: string
  item: string
  keeper: string
  member: string
  slot: string
  slotKey: string
  replacement: string
  replacementKey: string
  cost: number
  alternatives: Alternative[]
}

export interface Described {
  key: string
  description: string
}

export interface DistributionChart {
  kind: 'distribution'
  title: string
  xTitle: string
  binWidth: number
  series: DistributionSeries[]
}

export interface DistributionSeries {
  name: string
  owner: number
  start: number[]
  percent: number[]
  box: Box
  curve?: Curve | null
  stats: DistributionStats
}

export interface DistributionStats {
  mean: number
  sd: number
  skew: number
  allMiss?: number | null
}

export interface Evaluation {
  attackBonus: number
  members: MemberResult[]
  conflicts: Conflict[]
  synergies: Record<string, string[]>
}

export interface Example {
  name: string
  source: string
}

export interface Expected {
  characters?: ExpectedCharacter[] | null
  problems?: string[] | null
}

export interface ExpectedCharacter {
  name: string
  damagePerRound: number
  attacks: AttackDamage[]
}

export interface ExportRequest {
  characters: Record<string, unknown>[]
  enemy: Record<string, unknown>
  rounds_per_fight: number | null
  graph: string
  num_rounds: number
  sweep_parameter: string
  ruleset: string
  seed: number | null
  kind: string
}

export interface Fight {
  down_by_round: number[]
  median_round: number
  share: Record<string, number>
  rounds: number
  hit_points: number
}

export interface Frontier {
  current: FrontierPoint
  points: FrontierPoint[]
}

export interface FrontierChange {
  slot: string
  key: string
  name: string
}

export interface FrontierPoint {
  damage: number
  ac: number
  changes: FrontierChange[]
  drawbacks: string[]
  frontier: boolean
}

export interface FrontierRequest {
  build: Build
  party: Build[]
  synergies: boolean
  enemy?: Record<string, unknown> | null
  rounds_per_fight: number
  enemies: number
  attack_bonus: number
  selected: number
  act: string
  skip_taken: boolean
}

export interface GearChange {
  act: string
  slot: string
  before: string
  after: string
  gain: number
}

export interface Headline {
  unit: string
  context: string
  higherIsBetter: boolean
  values: HeadlineValue[]
}

export interface HeadlineValue {
  name: string
  value: number
}

export interface ImportRequest {
  source: string
}

export interface ImportResult {
  builds?: ImportedBuild[] | null
  problems?: string[] | null
}

export interface ImportedBuild {
  name: string
  notes: string[]
}

export interface Inputs {
  characters: Record<string, unknown>[]
  enemy: Record<string, unknown>
  rounds_per_fight: number | null
}

export interface ItemOption {
  label: string
  value: string
  title: string
  act?: number | null
}

export interface ItemValue {
  slot: string
  item: string
  summary: string
  gain: number
}

/** A worn item best in slot left alone: it has effects the damage doesn't count, so the numbers undersell it */
export interface KeptItem {
  act: string
  slot: string
  item: string
  preferred: string
  gain: number
}

export interface Keyed {
  key: string
  label: string
}

export interface Kit {
  key: string
  name: string
  act: number
  theme: string
  trigger: string
  fits: string
  synergy: string
  notes: string
  slots: Record<string, string[]>
}

export interface KitRequest {
  party: Build[]
  selected: number
  kit: string
  act: string
  skip_taken: boolean
  only_empty: boolean
}

export interface KitResult {
  build: Build
  placed: string[]
  blocked: string[]
}

export interface Labelled {
  label: string
  value: string
}

export interface LeaderboardEntry {
  key: string
  name: string
  source: string
  variant: string
  fingerprint: string
  spec: string
  gear_changes: string
  damage: Record<string, Record<string, number | null>>
  ac: Record<string, number | null>
  score: Record<string, number | null>
  advantage_source: Record<string, string>
  area?: Record<string, Record<string, string>> | null
  levels: Record<string, number>
  same_as?: string | null
}

export interface LeaderboardOptions {
  scenarios: Scenario[]
  enemyCounts: number[]
  variants: Keyed[]
  sources: string[]
  referenceEnemies: Record<string, string>
  roundsPerFight: number
  readOnly: boolean
}

export interface LineSeries {
  name: string
  owner: number
  y: number[]
}

export interface LinesChart {
  kind: 'lines'
  title: string
  xTitle: string
  yTitle: string
  x: number[]
  yMax?: number | null
  unit: string
  series: LineSeries[]
}

export interface MapData {
  maps: MapRegion[]
  acts: number[]
  points: MapPoint[]
  unplaced: MapPoint[]
  rarities: string[]
  defaultRarities: string[]
  colors: Record<string, string>
  partyColor: string
  missableColor: string
}

/** An item or key pickup at a spot. Key pickups have no item key or slot, sent as '' */
export interface MapPoint {
  name: string
  key: string
  rarity: string
  slot: string
  kind: string
  source: string
  notes: string
  builds: string[]
  tip: string
  location: string
  where: string
  trader: boolean
  map: string
  inside: boolean
  x: number
  y: number
  px?: number | null
  py?: number | null
  missable?: string | null
  act: number
}

export interface MapRegion {
  key: string
  label: string
  act: number
  image?: string | null
  width?: number | null
  height?: number | null
}

export interface MemberResult {
  name: string
  acts: Record<string, ActResult>
  conditions: Labelled[]
  builder?: BuilderSummary | null
}

export interface MemberRoles {
  name: string
  roles: Record<string, string>
}

export interface PartyAnalysis {
  roles: MemberRoles[]
  missing: string[]
  overlaps: string[]
  synergies: Synergy[]
  active: string[]
  damage: SynergyDamage[]
  fight: Fight
}

export interface PartyFightRequest {
  party: Build[]
  enemy?: Record<string, unknown> | null
  rounds_per_fight: number
  attack_bonus?: number | null
  synergies: boolean
  act: string
  active?: string[] | null
  hit_points: number
}

export interface PartyGear {
  key: string
  name: string
  users: string[]
  members: string[]
  where: string
  missable: string
  placed: boolean
  maps: string[]
}

export interface PartyRequest {
  party: Build[]
}

export interface PlannerOptions {
  maxPartySize: number
  acts: Act[]
  presets: Keyed[]
  examples: Example[]
  slots: Slot[]
  items: Record<string, ItemOption[]>
  buffs: Buff[]
  kits: Kit[]
  quickVariants: QuickVariant[]
  builder: BuilderOptions
  assumptions: Assumption[]
  scoreWeights: Record<string, number>
  partLabels: Record<string, string>
  roleLabels: Record<string, string>
  coreRoles: string[]
  defaultParty: Build[]
  savedParties: SavedParty[]
  readOnly: boolean
}

export interface PlannerRequest {
  party: Build[]
  enemy?: Record<string, unknown> | null
  rounds_per_fight: number
  attack_bonus?: number | null
  synergies: boolean
}

export interface PresetRequest {
  preset: string
  level: number
  ruleset: string
}

export interface QuickVariant {
  key: string
  name: string
  buffs: string[]
  toggles: Record<string, boolean>
  kit?: string | null
}

export interface Ruleset {
  key: string
  label: string
  maxLevel: number
}

export interface Run {
  id: number
  created: string
  label: string
  kind: string
  commit: string
  count: number
}

export interface SaveRequest {
  party: Build[]
  label: string
  with_variants: boolean
}

export interface Saved {
  id: number
  rows: number
}

export interface SavedParty {
  name: string
  notes: string[]
  builds: Build[]
}

export interface SavingThrow {
  name: string
  stat: string
  dc: number
  fixed: boolean
  fail: number
  disadvantage: boolean
}

export interface Scenario {
  key: string
  label: string
  note: string
}

export interface SendRequest {
  party: Build[]
  act?: string | null
  selected?: number | null
}

export interface Session {
  characters: Record<string, unknown>[]
  enemy: Record<string, unknown>
}

export interface Simulation {
  characters: Record<string, unknown>[]
  enemy: Record<string, unknown>
  rounds_per_fight: number | null
  graph: string
  num_rounds: number
  sweep_parameter: string
  ruleset: string
  seed: number | null
}

export interface SimulationResult {
  chart?: DistributionChart | SweepChart | LinesChart | null
  headline?: Headline | null
  tables?: Table[] | null
  problems?: string[] | null
}

export interface SimulatorOptions {
  presets: SimulatorPreset[]
  rulesets: Ruleset[]
  enemies: Labelled[]
  attackTemplates: Labelled[]
  graphs: Described[]
  sweepParameters: Described[]
  variants: Keyed[]
  exports: string[]
  attackDefaults: Record<string, unknown>
  characterDefaults: Record<string, unknown>
  enemyDefaults: Record<string, unknown>
}

export interface SimulatorPreset {
  key: string
  label: string
  class: string
  description: string
}

export interface Slot {
  key: string
  label: string
  group: string
}

export interface Suggestion {
  key: string
  item: string
  summary: string
  gain: number
  act?: number | null
  users: string[]
}

export interface SweepChart {
  kind: 'sweep'
  title: string
  xTitle: string
  yTitle: string
  series: SweepSeries[]
}

export interface SweepSeries {
  name: string
  owner: number
  x: number[]
  mean: number[]
  median: number[]
  q1: number[]
  q3: number[]
}

export interface Synergy {
  key: string
  text: string
}

export interface SynergyDamage {
  name: string
  alone: number
  together: number
}

export interface Table {
  title: string
  description: string
  columns: string[]
  rows: ((string | number | boolean | string[] | null)[])[]
}

export interface TemplateRequest {
  value: string
  ability_stat?: string | null
  level: number
  ruleset: string
}

export interface Toggle {
  value: string
  label: string
  on: boolean
}

export interface UseVariantRequest {
  build: Build
  index: number
}

export interface VariantRequest {
  character: Record<string, unknown>
  key: string
}

export interface VariantResult {
  character?: Record<string, unknown> | null
  problems?: string[] | null
}

export interface VariantRow {
  name: string
  description: string
  damage: number[]
  byEnemies: number[][]
  spellDc: (number | null)[]
  ac: number[]
  score: number[]
}

export interface VariantsRequest {
  build: Build
  party: Build[]
  synergies: boolean
  enemy?: Record<string, unknown> | null
  rounds_per_fight: number
  enemies: number
  attack_bonus: number
}
