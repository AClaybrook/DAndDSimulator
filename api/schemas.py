""" The shapes of the API's requests and responses. FastAPI checks every response against these and publishes them as an OpenAPI schema,
    from which the front end's types are generated (frontend/src/api-types.ts, `npm run types`), so the two sides can't drift apart.

    Simulator characters, attacks and enemies stay open dictionaries on purpose: the browser edits them field by field, half typed values
    included, and api.validation names what is wrong with them instead of the request being refused """
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Loose = dict[str, Any] # A simulator Character, Attack or Enemy (computations.models), see above

class Model(BaseModel):
    model_config = ConfigDict(extra="ignore")

# ---------- Simulator

class Labelled(Model):
    label: str
    value: str

class Keyed(Model):
    key: str
    label: str

class Described(Model):
    key: str
    description: str

class SimulatorPreset(Model):
    key: str
    label: str
    class_: str = Field(alias="class")
    description: str
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

class Ruleset(Model):
    key: str
    label: str
    maxLevel: int

class SimulatorOptions(Model):
    presets: list[SimulatorPreset]
    rulesets: list[Ruleset]
    enemies: list[Labelled]
    attackTemplates: list[Labelled]
    graphs: list[Described]
    sweepParameters: list[Described]
    variants: list[Keyed]
    exports: list[str]
    attackDefaults: Loose
    characterDefaults: Loose
    enemyDefaults: Loose

class Session(Model):
    characters: list[Loose]
    enemy: Loose

class AttackDamage(Model):
    name: str
    damage: float

class ExpectedCharacter(Model):
    name: str
    damagePerRound: float
    attacks: list[AttackDamage]

class Expected(Model):
    characters: list[ExpectedCharacter] | None = None
    problems: list[str] | None = None

class Box(Model):
    q1: float
    median: float
    q3: float
    low: float
    high: float
    mean: float

class Curve(Model):
    kind: Literal["exact", "fit"]
    start: list[int]
    percent: list[float]

class DistributionStats(Model):
    mean: float
    sd: float
    skew: float
    allMiss: float | None = None

class DistributionSeries(Model):
    name: str
    owner: int # The character it belongs to (its colour)
    start: list[int]
    percent: list[float]
    box: Box
    curve: Curve | None = None
    stats: DistributionStats

class DistributionChart(Model):
    kind: Literal["distribution"]
    title: str
    xTitle: str
    binWidth: int
    series: list[DistributionSeries]

class SweepSeries(Model):
    name: str
    owner: int
    x: list[float]
    mean: list[float]
    median: list[float]
    q1: list[float]
    q3: list[float]

class SweepChart(Model):
    kind: Literal["sweep"]
    title: str
    xTitle: str
    yTitle: str
    series: list[SweepSeries]

class LineSeries(Model):
    name: str
    owner: int
    y: list[float]

class LinesChart(Model):
    kind: Literal["lines"]
    title: str
    xTitle: str
    yTitle: str
    x: list[float]
    yMax: float | None = None
    unit: str
    series: list[LineSeries]

class HeadlineValue(Model):
    name: str
    value: float

class Headline(Model):
    unit: str
    context: str
    higherIsBetter: bool
    values: list[HeadlineValue]

class Table(Model):
    title: str
    description: str
    columns: list[str]
    rows: list[list[str | float | bool | None | list[str]]]

class SimulationResult(Model):
    chart: DistributionChart | SweepChart | LinesChart | None = Field(None, discriminator="kind")
    headline: Headline | None = None
    tables: list[Table] | None = None
    problems: list[str] | None = None

class VariantResult(Model):
    character: Loose | None = None
    problems: list[str] | None = None

# ---------- BG3 builds (requests and responses)

class BuilderCharacter(Model):
    """ A custom character (bg3.character.Bg3Character) """
    name: str = "Tav"
    race: str = "Human"
    scores: dict[str, int] = {}
    bonus: dict[str, int] = {}
    classes: list[tuple[str, str, int]] = [] # [class, subclass, levels] in the order they are taken
    feats: list[str] = []
    fighting_styles: list[str] = []
    routine: str = "two_handed"
    cantrip: str = "Eldritch Blast"
    spell: str = ""
    toggles: dict[str, bool | str] = {}
    level_order: list[str] = []
    boons: dict[str, int] = {} # Permanent ability bonuses: Auntie Ethel's Hair (+1), Mirror of Loss (+2)

class Build(Model):
    """ A planner build (bg3.build.Bg3Build) """
    name: str
    preset: str = ""
    equipment: dict[str, dict[str, str]] = {} # Act: slot: item key
    buffs: dict[str, list[str]] = {}
    conditions: list[str] = []
    levels: dict[str, int] = {}
    character: BuilderCharacter | None = None
    carried: list[str] = []
    roles: list[str] = []
    variants: list[dict[str, Any]] = []
    advantage: bool = False

# ---------- Planner

class ItemOption(Model):
    label: str
    value: str
    title: str
    act: int | None = None

class Act(Model):
    key: str
    label: str
    level: int

class Example(Model):
    name: str
    source: str

class Slot(Model):
    key: str
    label: str
    group: str

class Buff(Model):
    key: str
    name: str
    act: int
    notes: str
    modelled: bool

class Kit(Model):
    key: str
    name: str
    act: int
    theme: str
    trigger: str
    fits: str
    synergy: str
    notes: str
    slots: dict[str, list[str]]

class QuickVariant(Model):
    key: str
    name: str
    buffs: list[str] = []
    toggles: dict[str, bool] = {}
    kit: str | None = None

class Choice(Model):
    value: str
    label: str

class Toggle(Model):
    value: str
    label: str
    on: bool # Whether it counts while the build hasn't set it

class BuilderOptions(Model):
    races: list[str]
    classes: list[str]
    subclasses: dict[str, list[str]]
    improvements: list[Choice]
    fightingStyles: list[str]
    routines: list[Choice]
    cantrips: list[str]
    spells: list[str]
    toggles: list[Toggle]
    defaultCharacter: BuilderCharacter

class PlannerOptions(Model):
    maxPartySize: int
    acts: list[Act]
    presets: list[Keyed]
    examples: list[Example]
    slots: list[Slot]
    items: dict[str, list[ItemOption]]
    buffs: list[Buff]
    kits: list[Kit]
    quickVariants: list[QuickVariant]
    builder: BuilderOptions
    scoreWeights: dict[str, float]
    partLabels: dict[str, str]
    roleLabels: dict[str, str]
    coreRoles: list[str]
    defaultParty: list[Build]
    readOnly: bool # A shared copy: no doc import, no saved leaderboard runs

class AcPart(Model):
    source: str
    value: float

class SavingThrow(Model):
    name: str # The spell
    stat: str # The enemy's saving throw
    dc: int
    fixed: bool # A DC of the spell's own (Dethrone), not the build's
    fail: float # The enemy's chance to fail it
    disadvantage: bool

class ActResult(Model):
    level: int
    damage: list[float] # Against 1, 2, 3 and 4 enemies
    spellDc: int | None = None # None when the build forces no saving throws
    saves: list[SavingThrow]
    ac: int
    acParts: list[AcPart]
    hitChance: float
    score: float
    scoreParts: dict[str, float]
    scoreNotes: dict[str, str]
    inherited: dict[str, str]
    flagged: list[str]

class BuilderSummary(Model):
    pointBuy: int | None = None
    featLevels: list[int]
    split: dict[str, dict[str, int]]
    problems: list[str]
    notes: list[str]
    toggles: list[Toggle]

class MemberResult(Model):
    name: str
    acts: dict[str, ActResult]
    conditions: list[Labelled]
    builder: BuilderSummary | None = None

class Conflict(Model):
    act: str
    kind: str
    message: str
    members: list[str]
    item: str
    gains: dict[str, float]

class Evaluation(Model):
    attackBonus: int
    members: list[MemberResult]
    conflicts: list[Conflict]

class VariantRow(Model):
    name: str
    description: str
    damage: list[float] # By act, against the chosen number of enemies
    byEnemies: list[list[float]] # By act: against 1, 2, 3 and 4 enemies
    spellDc: list[int | None]
    ac: list[int]
    score: list[float]

class KitResult(Model):
    build: Build
    placed: list[str]
    blocked: list[str]

class GearChange(Model):
    act: str
    slot: str
    before: str # Item names, '' for an empty slot
    after: str

class BestGear(Model):
    build: Build
    gear: dict[str, dict[str, str]] # Act: slot: item key, only what changed
    changes: list[GearChange]
    goal: str

class Alternative(Model):
    key: str
    item: str
    gain: float

class DeconflictStep(Model):
    act: str
    item: str
    keeper: str
    member: str
    slot: str
    slotKey: str
    replacement: str # '' when the slot is left empty
    replacementKey: str
    cost: float # Damage per round the member gives up
    alternatives: list[Alternative]

class Deconflict(Model):
    party: list[Build]
    steps: list[DeconflictStep]
    remaining: int # Conflicts left that aren't shared items (story choices, wrong slots, concentration)

class MemberRoles(Model):
    name: str
    roles: dict[str, str]

class Synergy(Model):
    key: str
    text: str

class SynergyDamage(Model):
    name: str
    alone: float
    together: float

class Fight(Model):
    down_by_round: list[float]
    median_round: float
    share: dict[str, float]
    rounds: int
    hit_points: int

class PartyAnalysis(Model):
    roles: list[MemberRoles]
    missing: list[str]
    overlaps: list[str]
    synergies: list[Synergy]
    active: list[str]
    damage: list[SynergyDamage]
    fight: Fight

class ItemValue(Model):
    slot: str
    item: str
    summary: str
    gain: float

class Suggestion(Model):
    key: str
    item: str
    summary: str
    gain: float
    act: int | None = None
    users: list[str]

class Advice(Model):
    values: list[ItemValue]
    suggestions: list[Suggestion]

class ImportedBuild(Model):
    name: str
    notes: list[str]

class ImportResult(Model):
    builds: list[ImportedBuild] | None = None
    problems: list[str] | None = None

# ---------- Leaderboard

class Scenario(Model):
    key: str
    label: str
    note: str

class LeaderboardOptions(Model):
    scenarios: list[Scenario]
    enemyCounts: list[int]
    variants: list[Keyed]
    sources: list[str]
    referenceEnemies: dict[str, str]
    roundsPerFight: int
    readOnly: bool

class LeaderboardEntry(Model):
    key: str
    name: str
    source: str
    variant: str
    fingerprint: str
    spec: str
    gear_changes: str = ""
    damage: dict[str, dict[str, float | None]] # "scenario@enemies": act: damage
    ac: dict[str, float | None]
    score: dict[str, float | None]
    advantage_source: dict[str, str] = {}
    area: dict[str, dict[str, str]] | None = None
    levels: dict[str, int]
    same_as: str | None = None

class Run(Model):
    id: int
    created: str
    label: str
    kind: str
    commit: str
    count: int

class Saved(Model):
    id: int
    rows: int

# ---------- Map

class MapPoint(Model):
    """ An item or key pickup at a spot. Key pickups have no item key or slot, sent as '' """
    @model_validator(mode="before")
    @classmethod
    def _no_nulls(cls, data):
        keep_null = ("px", "py", "missable")
        return {k: v for k, v in data.items() if v is not None or k in keep_null} if isinstance(data, dict) else data

    name: str
    key: str = ""
    rarity: str = ""
    slot: str = ""
    kind: str = ""
    source: str = ""
    notes: str = ""
    builds: list[str] = []
    tip: str = ""
    location: str = ""
    where: str = ""
    trader: bool = False
    map: str = ""
    inside: bool = False
    x: float = 0
    y: float = 0
    px: float | None = None
    py: float | None = None
    missable: str | None = None
    act: int

class MapRegion(Model):
    key: str
    label: str
    act: int
    image: str | None = None
    width: float | None = None
    height: float | None = None

class MapData(Model):
    maps: list[MapRegion]
    acts: list[int]
    points: list[MapPoint]
    unplaced: list[MapPoint]
    rarities: list[str]
    defaultRarities: list[str]
    colors: dict[str, str]
    partyColor: str
    missableColor: str

class PartyGear(Model):
    key: str
    name: str
    users: list[str]
    members: list[str]
    where: str
    missable: str
    placed: bool
    maps: list[str]
