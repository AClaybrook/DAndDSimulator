// What each character, attack and enemy field is, grouped so editors show the common ones first and the rest on demand

export type Kind = 'int' | 'float' | 'bool' | 'text' | 'list' | 'stat' | 'select'

export interface Field {
  key: string
  label: string
  kind: Kind
  options?: string[]
  help?: string
  min?: number
  max?: number
}

export interface FieldGroup {
  title: string
  fields: Field[]
}

export const STATS = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
export const ATTACK_TYPES = ['weapon (melee)', 'weapon (ranged)', 'spell', 'unarmed', 'thrown']
export const DAMAGE_TYPES = ['slashing', 'piercing', 'bludgeoning', 'fire', 'cold', 'lightning', 'thunder', 'acid', 'poison', 'necrotic', 'radiant', 'psychic', 'force']

const f = (key: string, label: string, kind: Kind, extra: Partial<Field> = {}): Field => ({ key, label, kind, ...extra })
const DICE = 'Comma separated dice and numbers, i.e. 1d4, 2'

export const CHARACTER_GROUPS: FieldGroup[] = [
  {
    title: 'Feats and fighting styles',
    fields: [
      f('GWM', 'Great Weapon Master', 'bool', { help: '-5 to hit, +10 damage with heavy weapons' }),
      f('sharpshooter', 'Sharpshooter', 'bool', { help: '-5 to hit, +10 damage with ranged weapons' }),
      f('savage_attacker', 'Savage Attacker', 'bool', { help: 'Roll weapon damage twice, keep the higher total' }),
      f('savage_attacker_per_die', 'Savage Attacker per die (BG3)', 'bool'),
      f('tavern_brawler', 'Tavern Brawler', 'bool'),
      f('GWF', 'Great Weapon Fighting', 'bool'),
      f('archery', 'Archery', 'bool'),
      f('dueling', 'Dueling', 'bool'),
      f('TWF', 'Two Weapon Fighting', 'bool'),
      f('savage_attacks_half_orc', 'Half-Orc Savage Attacks', 'bool'),
    ],
  },
  {
    title: 'Class features',
    fields: [
      f('raging', 'Raging', 'bool'),
      f('barbarian_level', 'Barbarian level (0 = character level)', 'int', { min: 0, max: 20 }),
      f('brutal_critical', 'Brutal Critical', 'bool'),
      f('divine_smite', 'Divine Smite', 'bool'),
      f('divine_smite_level', 'Divine Smite level', 'int', { min: 1, max: 5 }),
      f('improved_divine_smite', 'Improved Divine Smite', 'bool'),
      f('agonizing_blast', 'Agonizing Blast', 'bool'),
      f('lifedrinker', 'Lifedrinker', 'bool'),
      f('empowered_evocation', 'Empowered Evocation', 'bool'),
      f('elemental_affinity', 'Elemental Affinity', 'bool'),
    ],
  },
  {
    title: 'Rolls',
    fields: [
      f('advantage', 'Advantage', 'bool'),
      f('disadvantage', 'Disadvantage', 'bool'),
      f('crit_on', 'Crit on', 'int', { min: 2, max: 20 }),
      f('attack_reroll_on', 'Reroll attack die at or below', 'int', { min: 0, max: 19 }),
      f('damage_reroll_on', 'Reroll damage dice at or below', 'int', { min: 0, max: 5 }),
      f('additional_spell_dc', 'Spell save DC bonus', 'int'),
      f('bonus_attack_die_mod_list', 'Bonus to hit', 'list', { help: DICE }),
      f('bonus_damage_die_mod_list', 'Bonus damage', 'list', { help: DICE }),
      f('bonus_crit_die_mod_list', 'Bonus crit damage', 'list', { help: DICE }),
      f('bonus_miss_die_mod_list', 'Damage on a miss', 'list', { help: DICE }),
    ],
  },
  {
    title: 'Once per turn and first round',
    fields: [
      f('once_per_turn_die_mod_list', 'Once per turn damage (Sneak Attack, smite)', 'list', { help: DICE }),
      f('once_per_turn_crit_only', 'Once per turn only on a crit', 'bool'),
      f('once_per_turn_uses_per_fight', 'Once per turn uses per fight (0 = unlimited)', 'float', { min: 0 }),
      f('first_round_advantage', 'First round advantage', 'bool'),
      f('first_round_auto_crit', 'First round hits are crits', 'bool'),
    ],
  },
]

export const ATTACK_MAIN: Field[] = [
  f('name', 'Name', 'text'),
  f('type', 'Type', 'select', { options: ATTACK_TYPES }),
  f('ability_stat', 'Ability', 'stat'),
  f('damage', 'Damage', 'text', { help: 'Dice and modifier, i.e. 2d6 or 1d8+2' }),
  f('damage_type', 'Damage type', 'select', { options: DAMAGE_TYPES }),
  f('weapon_enhancement', 'Enhancement (+1, +2...)', 'int', { min: 0, max: 3 }),
]

export const ATTACK_GROUPS: FieldGroup[] = [
  {
    title: 'Weapon',
    fields: [
      f('two_handed', 'Two-handed', 'bool'),
      f('heavy', 'Heavy', 'bool'),
      f('offhand', 'Offhand', 'bool'),
      f('proficient', 'Proficient', 'bool'),
      f('advantage', 'Advantage', 'bool'),
      f('disadvantage', 'Disadvantage', 'bool'),
      f('crit_on', 'Crit on', 'int', { min: 2, max: 20 }),
      f('extra_damage_list', 'Extra typed damage', 'list', { help: 'i.e. 1d4 fire, 2 acid' }),
    ],
  },
  {
    title: 'Limits and saving throws',
    fields: [
      f('uses_per_fight', 'Uses per fight (0 = every round)', 'float', { min: 0 }),
      f('fallback_for', 'Fallback for (attack name)', 'text', { help: 'Made once the named limited attack is used up' }),
      f('once_per_turn_eligible', 'Can carry once per turn damage', 'bool'),
      f('saving_throw', 'Saving throw instead of an attack roll', 'bool'),
      f('saving_throw_stat', 'Saving throw ability', 'stat'),
      f('saving_throw_success_multiplier', 'Damage on a successful save', 'float', { min: 0, max: 1 }),
      f('targets', 'Targets (area spells)', 'int', { min: 1, max: 10 }),
    ],
  },
  {
    title: 'Bonus dice',
    fields: [
      f('always_hit', 'Always hits', 'bool'),
      f('always_crit', 'Always crits', 'bool'),
      f('hits_crit', 'Hits are crits', 'bool'),
      f('damage_reroll_on', 'Reroll damage dice at or below', 'int', { min: 0, max: 5 }),
      f('bonus_attack_die_mod_list', 'Bonus to hit', 'list', { help: DICE }),
      f('bonus_damage_die_mod_list', 'Bonus damage', 'list', { help: DICE }),
      f('bonus_crit_die_mod_list', 'Bonus crit damage', 'list', { help: DICE }),
      f('bonus_miss_die_mod_list', 'Damage on a miss', 'list', { help: DICE }),
    ],
  },
]

export const ENEMY_MAIN: Field[] = [
  f('armor_class', 'Armor class', 'int', { min: 1, max: 40 }),
  f('hit_points', 'Hit points', 'int', { min: 1 }),
]

export const ENEMY_GROUPS: FieldGroup[] = [
  {
    title: 'Saving throws',
    fields: STATS.map((s) => f(`${s}_save`, `${s[0].toUpperCase()}${s.slice(1, 3)} save`, 'int', { help: 'Empty: from the ability score' })),
  },
  {
    title: 'Resistances',
    fields: [
      f('resistances', 'Resistances', 'list', { help: 'Damage types, i.e. fire, slashing (nonmagical)' }),
      f('vulnerabilities', 'Vulnerabilities', 'list'),
      f('immunities', 'Immunities', 'list'),
      f('resistance', 'Resistant to everything', 'bool'),
      f('vulnerability', 'Vulnerable to everything', 'bool'),
      f('damage_reduction', 'Damage reduction per hit', 'int', { min: 0 }),
    ],
  },
]

export const statLabel = (s: string) => s.slice(0, 3).toUpperCase()
