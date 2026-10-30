""" Dataclasses and associated helper functions for containing character and enemy data """
from dataclasses import dataclass, field, asdict, fields
from typing import Literal

Stat = Literal["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
STATS = ("strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma")
DAMAGE_TYPES = ("acid", "bludgeoning", "cold", "fire", "force", "lightning", "necrotic",
                "piercing", "poison", "psychic", "radiant", "slashing", "thunder")
NONMAGICAL_SUFFIX = " (nonmagical)"

### Utility functions ###
def die_from_str(die_str):
    """Returns the number of dice, die size and flat modifier from a string of the form '2d6', '2d6+3' or 'd8-1'"""
    die_str = die_str.lower().replace(" ", "")
    num_die, rem = die_str.split('d')
    num_die = int(num_die) if num_die else 1
    if '+' in rem:
        die_size, die_mod = rem.split('+')
        die_mod = int(die_mod)
    elif '-' in rem:
        die_size, die_mod = rem.split('-')
        die_mod = -int(die_mod)
    else:
        die_size = rem
        die_mod = 0
    return num_die, int(die_size), die_mod

def multiple_die_and_mod_from_list(die_list):
    """Returns a list of the number of dice, die size, and total modifier from a list of strings of the form ['2d6',-3,'2d6+3']"""
    num_die = []
    die_sizes = []
    total_mod = 0
    if isinstance(die_list, str):
        die_list = die_list.split(",")
    for elem in die_list:
        if isinstance(elem, (int, float)):
            m = int(elem)
        else:
            elem = elem.lower().replace(" ", "")
            if len(elem) == 0:
                m = 0
            elif 'd' in elem:
                n, s, m = die_from_str(elem)
                # Skip empty dice such as the '0d4' placeholders used by the UI
                if n > 0 and s > 0:
                    num_die.append(n)
                    die_sizes.append(s)
            else:
                m = int(elem)
        total_mod += m
    return num_die, die_sizes, total_mod

# Old field name: new field name, so json files saved before a rename still load
RENAMED_FIELDS = {"proficent": "proficient", "saving_throw_proficent": "saving_throw_proficient"}

def from_dict(cls, data):
    """ Builds a dataclass from a dictionary, ignoring unknown keys so older/newer json files still load """
    names = {f.name for f in fields(cls) if f.init}
    data = {RENAMED_FIELDS.get(k, k): v for k, v in data.items()}
    return cls(**{k: v for k, v in data.items() if k in names})

def typed_damage_from_str(damage_str):
    """ '1d4 fire' -> ([1], [4], 0, 'fire'), '2d6+1 cold' -> ([2], [6], 1, 'cold'), '2 acid' -> ([], [], 2, 'acid').
        Without a damage type the type is '' (the attack's own type) """
    parts = str(damage_str).strip().lower().split()
    damage_type = parts[-1] if len(parts) > 1 and parts[-1] in DAMAGE_TYPES else ""
    dice = "".join(parts[:-1] if damage_type else parts)
    num_die, die_sizes, modifier = multiple_die_and_mod_from_list([dice])
    return num_die, die_sizes, modifier, damage_type

### Classes ###

@dataclass
class Attack:
    """ Dataclass for attacks """
    name: str = 'Attack'
    bonus_attack_die_mod_list: list[str | int] = field(default_factory=list) # Format is ['1d6', 2]
    bonus_damage_die_mod_list: list[str | int] = field(default_factory=list) # Format is ['1d6', 2]

    proficient: bool = True
    type: Literal["weapon (melee)", "weapon (ranged)", "spell", "unarmed", "thrown"] = 'weapon (melee)'
    ability_stat: Stat = 'strength'
    damage: str = '1d6' # Used by all attacks, can include a flat modifier i.e. '1d4+1'
    damage_type: str = 'slashing'
    # Attack specific
    advantage: bool = False
    disadvantage: bool = False
    always_hit: bool = False
    always_crit: bool = False
    hits_crit: bool = False # Every hit is a crit, i.e. melee attacks against paralysed targets
    crit_on: int = 20
    # Weapon Specific
    weapon_enhancement: int = 0
    offhand: bool = False
    two_handed: bool = False
    heavy: bool | None = None # Required for Great Weapon Master, defaults to two_handed for older json files
    # Spell Specific
    saving_throw: bool = False
    saving_throw_stat: Stat = 'dexterity'
    saving_throw_success_multiplier: float = 0.5
    # Whether the character's once per turn damage (sneak attack, smite) can be added to this attack
    once_per_turn_eligible: bool = True
    # Limited attacks (i.e. Action Surge, quickened spells): average uses per fight, used in the first rounds. 0 means every round
    uses_per_fight: float = 0
    # Only made once the limited attack with this name is used up, i.e. Fire Bolt as the fallback for Fireball
    fallback_for: str = ''
    # Extra damage dice on a crit (i.e. brutal critical) and damage on a miss/successful save (i.e. graze)
    bonus_crit_die_mod_list: list[str | int] = field(default_factory=list) # Format is ['1d6', 2]
    bonus_miss_die_mod_list: list[str | int] = field(default_factory=list) # Format is ['1d6', 2]
    # Extra damage on a hit with its own damage type, so resistances apply to it separately, i.e. ['1d4 fire', '2 acid'] (BG3 items)
    extra_damage_list: list[str] = field(default_factory=list)
    # Reroll damage dice at or below this, for this attack only (i.e. BG3 weapons like Twist of Fortune), like Great Weapon Fighting
    damage_reroll_on: int = 0

    def __post_init__(self):
        if self.heavy is None:
            self.heavy = self.two_handed

    def to_dict(self):
        return asdict(self)

    @property
    def is_weapon(self):
        return self.type in ("weapon (melee)", "weapon (ranged)", "thrown")

    @property
    def is_magical(self):
        return self.type == "spell" or self.weapon_enhancement > 0

@dataclass
class Creature:
    """ Dataclass for creatures, holds general stats """
    name: str = 'Creature'
    armor_class: int = 10
    damage_reduction: int = 0
    resistance: bool = False # Resistant to all damage
    vulnerability: bool = False # Vulnerable to all damage
    attacks: list[Attack] = field(default_factory=list)
    saving_throw_proficient: bool = False
    # Stats
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10
    level: int = 1
    # Attack Roll Modifiers
    advantage: bool = False
    disadvantage: bool = False
    bonus_attack_die_mod_list: list[str | int] = field(default_factory=list) # Format is ['1d6', 2]
    attack_reroll_on: int = 0
    crit_on: int = 20
    # Damage Roll Modifiers
    bonus_damage_die_mod_list: list[str | int] = field(default_factory=list) # Format is ['1d6', 2]
    damage_reroll_on: int = 0
    # Additional Crit Damage
    bonus_crit_die_mod_list: list[str | int] = field(default_factory=list) # Format is ['0d6', 0]
    # Additional Miss Damage
    bonus_miss_die_mod_list: list[str | int] = field(default_factory=list)
    # Bonus damage applied to the first hit each round, i.e. sneak attack or a divine smite
    once_per_turn_die_mod_list: list[str | int] = field(default_factory=list)
    once_per_turn_crit_only: bool = False # Only use it on a crit, i.e. crit fishing with divine smite
    once_per_turn_uses_per_fight: float = 0 # Average uses per fight (i.e. spell slots for smites), 0 means unlimited
    # First round of a fight, i.e. Assassinate: advantage against enemies that haven't acted, hits are crits against surprised enemies
    first_round_advantage: bool = False
    first_round_auto_crit: bool = False
    # Additional Spell DC
    additional_spell_dc: int = 0

    hit_points: int = 12
    # Unused
    initiative: int = 0
    description: str = ''

    # pylint: disable=missing-function-docstring
    @property
    def proficiency_bonus(self):
        return 2 + (self.level - 1) // 4

    @property
    def strength_ability_modifier(self):
        return (self.strength - 10) // 2

    @property
    def dexterity_ability_modifier(self):
        return (self.dexterity - 10) // 2

    @property
    def constitution_ability_modifier(self):
        return (self.constitution - 10) // 2

    @property
    def intelligence_ability_modifier(self):
        return (self.intelligence - 10) // 2

    @property
    def wisdom_ability_modifier(self):
        return (self.wisdom - 10) // 2

    @property
    def charisma_ability_modifier(self):
        return (self.charisma - 10) // 2

    def ability_modifier(self, stat):
        if stat not in STATS:
            raise ValueError(f"Unknown ability '{stat}'")
        return (getattr(self, stat) - 10) // 2

    def attack_modifier(self, stat):
        return self.ability_modifier(stat) + self.proficiency_bonus + multiple_die_and_mod_from_list(self.bonus_attack_die_mod_list)[2]

    def damage_modifier(self, stat):
        return self.ability_modifier(stat) + multiple_die_and_mod_from_list(self.bonus_damage_die_mod_list)[2]

    def spell_casting_modifier(self, stat):
        return self.ability_modifier(stat=stat)

    def spell_difficulty_class(self, stat):
        spell_casting_mod = self.spell_casting_modifier(stat)
        return 8 + self.proficiency_bonus + spell_casting_mod + self.additional_spell_dc

    def to_dict(self):
        return asdict(self)


@dataclass(kw_only=True)
class Character(Creature):
    """ Dataclass for characters, has additional properties associated with classes, races, feats, etc. """
    # pylint: disable=invalid-name
    name: str = 'Character'
    # Feats/Abilities
    savage_attacker: bool = False # roll weapon damage dice twice and take the higher total
    savage_attacker_per_die: bool = False # BG3 Savage Attacker: keep the higher of two rolls for each die separately
    tavern_brawler: bool = False # strength modifier added to attack and damage rolls
    GWM: bool = False # -5 to hit, +10 to damage, TODO: bonus action attack on crit or kill
    sharpshooter: bool = False # -5 to hit, +10 to damage with ranged weapons
    # TODO: Elemental Adept, cannot roll less than 1 on damage die, could cause many rerolls... Skipping for now
    # Racial Traits (only half orc affects damage directly)
    savage_attacks_half_orc: bool = False
    # Class Traits
    # Fighting Style
    archery: bool = False
    dueling: bool = False
    GWF: bool = False # reroll 1s and 2s on damage
    TWF: bool = False
    # Barbarian
    raging: bool = False
    barbarian_level: int = 0 # For multiclass characters, rage damage follows the barbarian level (0 uses the character level)
    brutal_critical: bool = False
    #Paladin
    divine_smite: bool = False # 2d8+1d8 per spell level above 1st, max 5d8, applied to every melee hit
    divine_smite_level: int = 1
    improved_divine_smite: bool = False # 1d8
    # Warlock
    agonizing_blast: bool = False # add charisma modifier to each blast
    lifedrinker: bool = False # add charisma modifier to pact weapon damage
    # Wizard
    empowered_evocation: bool = False # add intelligence modifier to evocation spell damage
    # Sorcerer
    elemental_affinity: bool = False # add charisma modifier to spell damage of matching element
    # Prebuilt character this was created from ("build:ruleset"), used to rebuild it at other levels
    preset: str = ''

    @property
    def rage_damage(self):
        barbarian_level = self.barbarian_level or self.level
        if barbarian_level >= 16:
            return 4
        if barbarian_level >= 9:
            return 3
        return 2

    @property
    def brutal_critical_dice(self):
        if self.level >= 17:
            return 3
        if self.level >= 13:
            return 2
        return 1

    @classmethod
    def from_dict(cls, data):
        data = dict(data)
        attacks = [a if isinstance(a, Attack) else from_dict(Attack, a) for a in data.pop("attacks", [])]
        return from_dict(cls, {**data, "attacks": attacks})

@dataclass(kw_only=True)
class Enemy(Creature):
    """ Dataclass for enemys/monsters """
    name: str = 'Mind Flayer'
    armor_class: int = 15
    hit_points: int = 71
    challenge_rating: float = 0
    # Saving throw modifiers, None means derived from the ability score (and proficiency if saving_throw_proficient)
    strength_save: int | None = None
    dexterity_save: int | None = None
    constitution_save: int | None = None
    intelligence_save: int | None = None
    wisdom_save: int | None = None
    charisma_save: int | None = None
    # Damage types, entries may end with ' (nonmagical)' to only apply to nonmagical weapon attacks
    resistances: list[str] = field(default_factory=list)
    vulnerabilities: list[str] = field(default_factory=list)
    immunities: list[str] = field(default_factory=list)

    @property
    def proficiency_bonus(self):
        # Monsters derive proficiency from challenge rating rather than level
        if self.challenge_rating:
            return max(2, 2 + (int(self.challenge_rating) - 1) // 4)
        return super().proficiency_bonus

    def saving_throw_modifier(self, stat):
        explicit = getattr(self, f"{stat}_save")
        if explicit is not None:
            return explicit
        return self.ability_modifier(stat) + (self.proficiency_bonus if self.saving_throw_proficient else 0)

    def damage_multiplier(self, attack: Attack, damage_type=None):
        """ Multiplier from resistances, vulnerabilities and immunities for a given attack, or for extra damage of another type """
        damage_type = damage_type or attack.damage_type
        def matches(entries):
            for entry in entries:
                entry = entry.strip().lower()
                if entry.endswith(NONMAGICAL_SUFFIX):
                    if attack.is_weapon and not attack.is_magical and entry[:-len(NONMAGICAL_SUFFIX)] == damage_type:
                        return True
                elif entry == damage_type:
                    return True
            return False

        if matches(self.immunities):
            return 0
        multiplier = 1
        if self.resistance or matches(self.resistances):
            multiplier *= 0.5
        if self.vulnerability or matches(self.vulnerabilities):
            multiplier *= 2
        return multiplier

    @classmethod
    def from_dict(cls, data):
        return from_dict(cls, data)

@dataclass
class AttackContext:
    """ Dataclass to hold just the critical information to compute an attack roll """
    num_die: list[int] = field(default_factory=list)
    die_size: list[int] = field(default_factory=list)
    modifier: int = 0
    advantage: bool = False
    disadvantage: bool = False
    crit_on: int = 20
    reroll_on: int = 0
    difficulty_class: int = 15
    # Saving throws are rolled by the enemy, a "hit" is a failed save
    saving_throw: bool = False
    # Special cases
    always_hit: bool = False
    always_crit: bool = False
    hits_crit: bool = False

@dataclass
class DamageContext:
    """ Dataclass to hold just the critical information to compute damage """
    # Standard Hit Damage
    num_die: list[int] = field(default_factory=list)
    die_size: list[int] = field(default_factory=list)
    modifier: int = 0
    damage_multiplier: float = 1
    damage_reduction: int = 0
    advantage: bool = False # roll the damage dice twice and keep the higher total
    disadvantage: bool = False
    per_die_advantage: bool = False # with advantage, keep the higher of two rolls for each die rather than the higher total
    reroll_on: int = 0
    # Bonus Crit Damage, beyond the standard 2x die rolls
    crit_num_die: list[int] = field(default_factory=list)
    crit_damage_die: list[int] = field(default_factory=list)
    crit_damage_modifier: int = 0
    # Damage on Miss
    miss_num_die: list[int] = field(default_factory=list)
    miss_damage_die: list[int] = field(default_factory=list)
    miss_damage_modifier: int = 0
    # Fraction of the hit damage dealt on a successful saving throw (i.e. 0.5 for fireball)
    save_success_multiplier: float = 0
    # Once per turn damage on the first hit (doubled dice on a crit)
    once_num_die: list[int] = field(default_factory=list)
    once_die_size: list[int] = field(default_factory=list)
    once_modifier: int = 0
    once_per_turn_eligible: bool = False
    once_crit_only: bool = False
    once_uses_per_fight: float = 0
    # Average uses per fight of a limited attack, 0 means every round
    uses_per_fight: float = 0
    # Index of the limited attack this attack replaces once it is used up, -1 for none
    fallback_index: int = -1
    # First round of a fight (attack rolls only)
    first_round_advantage: bool = False
    first_round_auto_crit: bool = False
    # Extra damage of other types on a hit (dice doubled on a crit), each with its own resistance multiplier
    rider_num_die: list[list[int]] = field(default_factory=list)
    rider_die_size: list[list[int]] = field(default_factory=list)
    rider_modifier: list[int] = field(default_factory=list)
    rider_multiplier: list[float] = field(default_factory=list)

def calculate_attack_and_damage_context(character, enemy):
    """ Extracts the attack and damage contexts for a given character and enemy """
    attack_contexts = []
    damage_contexts = []

    # Character Specific
    c_attack_num_die, c_attack_die_sizes, c_bonus_attack_mod = multiple_die_and_mod_from_list(character.bonus_attack_die_mod_list)
    c_damage_num_die, c_damage_die_sizes, c_bonus_damage_mod = multiple_die_and_mod_from_list(character.bonus_damage_die_mod_list)
    c_miss_num_die, c_miss_damage_die, c_miss_damage_modifier = multiple_die_and_mod_from_list(character.bonus_miss_die_mod_list)
    c_crit_num_die, c_crit_damage_die, c_crit_damage_modifier = multiple_die_and_mod_from_list(character.bonus_crit_die_mod_list)
    once_num_die, once_die_size, once_modifier = multiple_die_and_mod_from_list(character.once_per_turn_die_mod_list)
    attack_names = [a.name for a in character.attacks]

    for attack in character.attacks:
        # From character
        ability_modifier = character.ability_modifier(attack.ability_stat)
        # Attack Roll
        attack_modifier = ability_modifier
        ## Proficiency, Spellcasting and unarmed attacks always add proficiency bonus
        if attack.proficient or attack.type in ['spell', 'unarmed']:
            attack_modifier += character.proficiency_bonus
        # Damage
        damage_modifier = 0
        damage_adv = False
        per_die_advantage = False
        damage_dis = False
        damage_reroll_on = max(character.damage_reroll_on, attack.damage_reroll_on or 0)

        # Attack Specific
        attack_num_die, attack_die_sizes, bonus_attack_mod = multiple_die_and_mod_from_list(attack.bonus_attack_die_mod_list)
        damage_num_die, damage_die_sizes, bonus_damage_mod = multiple_die_and_mod_from_list([attack.damage] + list(attack.bonus_damage_die_mod_list))
        miss_num_die, miss_damage_die, miss_damage_modifier = multiple_die_and_mod_from_list(attack.bonus_miss_die_mod_list)
        crit_num_die, crit_damage_die, crit_damage_modifier = multiple_die_and_mod_from_list(attack.bonus_crit_die_mod_list)
        weapon_num_die, weapon_die, _ = die_from_str(attack.damage) if 'd' in attack.damage.lower() else (0, 0, 0)

        # Join character and attack specific modifiers
        bonus_attack_mod += c_bonus_attack_mod
        attack_num_die += c_attack_num_die
        attack_die_sizes += c_attack_die_sizes
        damage_num_die += c_damage_num_die
        damage_die_sizes += c_damage_die_sizes
        bonus_damage_mod += c_bonus_damage_mod
        miss_num_die += c_miss_num_die
        miss_damage_die += c_miss_damage_die
        miss_damage_modifier += c_miss_damage_modifier
        crit_num_die += c_crit_num_die
        crit_damage_die += c_crit_damage_die
        crit_damage_modifier += c_crit_damage_modifier

        # Add flat modifiers
        attack_modifier += bonus_attack_mod
        damage_modifier += bonus_damage_mod

        if attack.is_weapon and attack.weapon_enhancement:
            attack_modifier += attack.weapon_enhancement
            damage_modifier += attack.weapon_enhancement

        ## Weapon attacks
        if attack.type in ('weapon (melee)', 'weapon (ranged)', 'thrown'):
            damage_modifier += ability_modifier
            # Offhand attacks don't add a positive ability modifier to damage, unless two weapon fighting
            if attack.offhand and ability_modifier > 0 and not character.TWF:
                damage_modifier -= ability_modifier

        if attack.type == 'weapon (melee)':
            if character.GWM and attack.heavy:
                attack_modifier -= 5
                damage_modifier += 10
            if character.savage_attacker:
                damage_adv = True
                per_die_advantage = character.savage_attacker_per_die
            if character.dueling and not attack.two_handed and not attack.offhand:
                damage_modifier += 2
            if character.GWF and attack.two_handed:
                damage_reroll_on = max(damage_reroll_on, 2)
            # Barbarian
            if character.raging:
                damage_modifier += character.rage_damage
            if character.brutal_critical and weapon_die:
                crit_num_die.append(character.brutal_critical_dice)
                crit_damage_die.append(weapon_die)
            # Paladin
            if character.divine_smite:
                damage_num_die.append(min(2 + character.divine_smite_level - 1, 5))
                damage_die_sizes.append(8)
            if character.improved_divine_smite:
                damage_num_die.append(1)
                damage_die_sizes.append(8)
            # Warlock
            if character.lifedrinker:
                damage_modifier += max(character.charisma_ability_modifier, 1)
            # Half-Orc
            if character.savage_attacks_half_orc and weapon_die:
                crit_num_die.append(1)
                crit_damage_die.append(weapon_die)
        elif attack.type == 'weapon (ranged)':
            if character.archery:
                attack_modifier += 2
            if character.sharpshooter:
                attack_modifier -= 5
                damage_modifier += 10
        elif attack.type == 'unarmed':
            damage_modifier += ability_modifier
            if character.tavern_brawler:
                attack_modifier += character.strength_ability_modifier
                damage_modifier += character.strength_ability_modifier
            if character.raging:
                damage_modifier += character.rage_damage
        elif attack.type == 'thrown': # TODO: Implement improvised thrown weapons
            if character.tavern_brawler:
                attack_modifier += character.strength_ability_modifier
                damage_modifier += character.strength_ability_modifier
            if character.raging:
                damage_modifier += character.rage_damage
        elif attack.type == 'spell':
            if character.agonizing_blast:
                damage_modifier += character.charisma_ability_modifier
            if character.empowered_evocation:
                damage_modifier += character.intelligence_ability_modifier
            if character.elemental_affinity:
                damage_modifier += character.charisma_ability_modifier

        # Enemy Specific
        damage_multiplier = enemy.damage_multiplier(attack) if isinstance(enemy, Enemy) else 1
        riders = [typed_damage_from_str(r) for r in attack.extra_damage_list or []]
        riders = [(n, d, m, enemy.damage_multiplier(attack, t) if isinstance(enemy, Enemy) else 1) for n, d, m, t in riders if n or m]

        # Difficulty Class
        difficulty_class = enemy.armor_class
        saving_throw = attack.saving_throw
        advantage = character.advantage or attack.advantage
        disadvantage = character.disadvantage or attack.disadvantage
        save_success_multiplier = 0
        attack_reroll_on = character.attack_reroll_on
        crit_on = min(character.crit_on, attack.crit_on)
        if saving_throw:
            # The enemy rolls a saving throw against the character's spell save DC, so character attack roll bonuses don't apply
            difficulty_class = character.spell_difficulty_class(attack.ability_stat)
            attack_modifier = enemy.saving_throw_modifier(attack.saving_throw_stat) if isinstance(enemy, Enemy) else enemy.ability_modifier(attack.saving_throw_stat)
            attack_num_die, attack_die_sizes = [], []
            advantage = disadvantage = False
            attack_reroll_on = 0
            save_success_multiplier = attack.saving_throw_success_multiplier

        attack_context = AttackContext(
            num_die=attack_num_die,
            die_size=attack_die_sizes,
            modifier=attack_modifier,
            advantage=advantage,
            disadvantage=disadvantage,
            crit_on=crit_on,
            reroll_on=attack_reroll_on,
            difficulty_class=difficulty_class,
            saving_throw=saving_throw,
            always_hit=attack.always_hit,
            always_crit=attack.always_crit,
            hits_crit=attack.hits_crit and not saving_throw,
        )
        damage_context = DamageContext(
            num_die=damage_num_die,
            die_size=damage_die_sizes,
            modifier=damage_modifier,
            damage_multiplier=damage_multiplier,
            damage_reduction=enemy.damage_reduction,
            advantage=damage_adv,
            per_die_advantage=per_die_advantage,
            disadvantage=damage_dis,
            reroll_on=damage_reroll_on,
            save_success_multiplier=save_success_multiplier,
            crit_num_die=crit_num_die,
            crit_damage_die=crit_damage_die,
            crit_damage_modifier=crit_damage_modifier,
            miss_num_die=miss_num_die,
            miss_damage_die=miss_damage_die,
            miss_damage_modifier=miss_damage_modifier,
            once_num_die=list(once_num_die),
            once_die_size=list(once_die_size),
            once_modifier=once_modifier,
            once_per_turn_eligible=attack.once_per_turn_eligible and not saving_throw,
            once_crit_only=character.once_per_turn_crit_only,
            once_uses_per_fight=character.once_per_turn_uses_per_fight or 0,
            uses_per_fight=attack.uses_per_fight or 0,
            fallback_index=attack_names.index(attack.fallback_for) if attack.fallback_for in attack_names and attack.fallback_for != attack.name else -1,
            first_round_advantage=character.first_round_advantage and not saving_throw,
            first_round_auto_crit=character.first_round_auto_crit and not saving_throw and not attack.always_hit,
            rider_num_die=[r[0] for r in riders],
            rider_die_size=[r[1] for r in riders],
            rider_modifier=[r[2] for r in riders],
            rider_multiplier=[r[3] for r in riders],
        )

        attack_contexts.append(attack_context)
        damage_contexts.append(damage_context)
    return attack_contexts, damage_contexts
