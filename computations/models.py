""" Dataclasses and associated helper functions for containing character and enemy data """
from dataclasses import dataclass, field, asdict
from typing import Literal, List

### Utility functions ###
def die_from_str(die_str):
    """Returns the number of dice and die size from a string of the form '2d6'"""
    die_str = die_str.lower()
    num_die, rem = die_str.split('d')
    if '+' in rem:
        die_size, die_mod = rem.split('+')
    elif '-' in rem:
        die_size, die_mod = rem.split('-')
        die_mod = -int(die_mod)
    else:
        die_size = rem
        die_mod = 0
    return int(num_die), int(die_size), die_mod

def multiple_die_and_mod_from_list(die_list):
    """Returns a list of the number of dice, die size, and total modifier from a list of strings of the form ['2d6',-3,'2d6+3']"""
    num_die = []
    die_sizes = []
    total_mod = 0
    for elem in die_list:
        if isinstance(elem, int):
            m = elem
        elif len(elem) == 0:
            # Empty string
            m = 0
        else:
            elem = elem.lower().replace(" ","")
            if 'd' in elem:
                n,s,m = die_from_str(elem)
                num_die.append(n)
                die_sizes.append(s)
            else:
                m = int(elem)
        total_mod += m
    # Remove zeros
    for ii, elem in enumerate(num_die):
        if elem == 0 or die_sizes[ii] == 0:
            num_die.pop(ii)
            die_sizes.pop(ii)
    return num_die, die_sizes, total_mod

### Classes ###

@dataclass
class Attack:
    """ Dataclass for attacks """
    name: str = 'Attack'
    bonus_attack_die_mod_list: list[str,int] = field(default_factory=list) # Format is ['1d6', 2]
    bonus_damage_die_mod_list: list[str,int] = field(default_factory=list) # Format is ['1d6', 2]

    proficent: bool = True
    type: Literal["weapon (melee)","weapon (ranged)","spell","unarmed","thrown"] = 'weapon (melee)'
    ability_stat: Literal["strength","dexterity","constitution","intelligence","wisdom","charisma"] = 'strength'
    damage: str = '1d6' # # Used by all attacks
    # Attack specific
    advantage: bool = False
    disadvantage: bool = False
    always_hit: bool = False
    always_crit: bool = False
    crit_on: int = 20
    # Weapon Specific
    weapon_enhancement: int = 0
    offhand: bool = False
    two_handed: bool = False
    # Spell Specific
    saving_throw: bool = False
    saving_throw_stat: Literal["strength","dexterity","constitution","intelligence","wisdom","charisma"] = 'dexterity'
    saving_throw_success_multiplier: float = 0.5
    # Unused
    damage_type: str = 'slashing'
    bonus_crit_die_mod_list: list[str,int] = field(default_factory=list) # Format is ['1d6', 2]
    bonus_miss_die_mod_list: list[str,int] = field(default_factory=list) # Format is ['1d6', 2]

@dataclass
class Creature:
    """ Dataclass for creatures, holds general stats """
    name: str = 'Creature'
    armor_class: int = 10
    damage_reduction: int = 0
    resistance: bool = False
    vulnerability: bool = False
    attacks: list[Attack] = field(default_factory=list)
    saving_throw_proficent: bool = False # TODO: Expand to per stat
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
    bonus_attack_die_mod_list: list[str,int] = field(default_factory=list) # Format is ['1d6', 2]
    attack_reroll_on: int = 0
    crit_on: int = 20
    # Damage Roll Modifiers
    bonus_damage_die_mod_list: list[str,int] = field(default_factory=list) # Format is ['1d6', 2]
    damage_reroll_on: int = 0
    damage_on_miss: int = 0
    # Additional Crit Damage
    bonus_crit_die_mod_list: list[str,int] = field(default_factory=list) # Format is ['0d6', 0]
    # Additional Miss Damage
    bonus_miss_die_mod_list: list[str,int] = field(default_factory=list)
    # Additional Spell DC
    additional_spell_dc: int = 0

    # Unused
    hit_points: int = 12
    initiative: int = 0
    type = 'humanoid'
    description: str  = 'A creature'

    # Internal properties
    additional_attack_modifier: int = 0
    additional_attack_num_die: list[int] = field(default_factory=list)
    additional_attack_die_sizes: list[int] = field(default_factory=list)
    additional_damage_modifier: int = 0
    additional_damage_num_die: list[int] = field(default_factory=list)
    additional_damage_die_sizes: list[int] = field(default_factory=list)
    additional_crit_damage_modifier: int = 0
    additional_crit_damage_num_die: list[int] = field(default_factory=list)
    additional_crit_damage_die_sizes: list[int] = field(default_factory=list)
    additional_miss_damage_modifier: int = 0
    additional_miss_damage_num_die: list[int] = field(default_factory=list)
    additional_miss_damage_die_sizes: list[int] = field(default_factory=list)

    def __post_init__(self):
        num_die, die_sizes, total_mod = multiple_die_and_mod_from_list(self.bonus_attack_die_mod_list)
        self.additional_attack_modifier += total_mod
        self.additional_attack_num_die += num_die
        self.additional_attack_die_sizes += die_sizes
        num_die, die_sizes, total_mod = multiple_die_and_mod_from_list(self.bonus_damage_die_mod_list)
        self.additional_damage_modifier += total_mod
        self.additional_damage_num_die += num_die
        self.additional_damage_die_sizes += die_sizes
        num_die, die_sizes, total_mod = multiple_die_and_mod_from_list(self.bonus_crit_die_mod_list)
        self.additional_crit_damage_modifier += total_mod
        self.additional_crit_damage_num_die += num_die
        self.additional_crit_damage_die_sizes += die_sizes
        num_die, die_sizes, total_mod = multiple_die_and_mod_from_list(self.bonus_miss_die_mod_list)
        self.additional_miss_damage_modifier += total_mod
        self.additional_miss_damage_num_die += num_die
        self.additional_miss_damage_die_sizes += die_sizes

    # pylint: disable=missing-function-docstring
    @property
    def proficiency_bonus(self):
        return 2 + (self.level-1)//4

    @property
    def strength_ability_modifier(self):
        return (self.strength-10)//2

    @property
    def dexterity_ability_modifier(self):
        return (self.dexterity-10)//2

    @property
    def constitution_ability_modifier(self):
        return (self.constitution-10)//2

    @property
    def intelligence_ability_modifier(self):
        return (self.intelligence-10)//2

    @property
    def wisdom_ability_modifier(self):
        return (self.wisdom-10)//2

    @property
    def charisma_ability_modifier(self):
        return (self.charisma-10)//2

    def ability_modifier(self, stat):
        if stat == 'strength':
            return self.strength_ability_modifier
        elif stat == 'dexterity':
            return self.dexterity_ability_modifier
        elif stat == 'constitution':
            return self.constitution_ability_modifier
        elif stat == 'intelligence':
            return self.intelligence_ability_modifier
        elif stat == 'wisdom':
            return self.wisdom_ability_modifier
        elif stat == 'charisma':
            return self.charisma_ability_modifier

    def attack_modifier(self,stat):
        return self.ability_modifier(stat) + self.proficiency_bonus + self.additional_attack_modifier

    def damage_modifier(self,stat):
        return self.ability_modifier(stat) + self.additional_damage_modifier

    def spell_casting_modifier(self, stat):
        return self.ability_modifier(stat=stat)

    def spell_difficulty_class(self, stat):
        spell_casting_mod = self.spell_casting_modifier(stat)
        return 8 + self.proficiency_bonus + spell_casting_mod + self.additional_spell_dc

    def to_dict(self):
        return {k: v for k, v in asdict(self).items()}


@dataclass(kw_only=True)
class Character(Creature):
    """ Dataclass for characters, has additional properties associated with classes, races, feats, etc. """
    # pylint: disable=invalid-name
    name: str = 'Character'
    # Feats/Abilities
    savage_attacker: bool = False # advantage on damage rerolls
    tavern_brawler: bool = False # strength modifier added to attack and damage rolls
    GWM: bool = False # -5 to hit, +10 to damage, TODO: bonus action attack on crit or kill
    sharpshooter: bool = False
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
    brutal_critical: bool = False
    #Paladin
    divine_smite: bool = False # 2d8+1d8 per spell level above 1st, max 5d8
    divine_smite_level: int = 1
    improved_divine_smite: bool = False # 1d8
    # Warlock
    agonizing_blast: bool = False # add charisma modifier to each blast
    lifedrinker: bool = False # add charisma modifier to pact weapon damage
    # Wizard
    empowered_evocation: bool = False # add intelligence modifier to evocation spell damage
    # Sorcerer
    elemental_affinity: bool = False # add charisma modifier to spell damage of matching element

@dataclass(kw_only=True)
class Enemy(Creature):
    """ Dataclass for enemys/monsters """
    name: str = 'Mind Flayer'
    armor_class: int = 15
    hit_points: int = 71
    damage_reduction: int = 0
    resistance: bool = False
    vulnerability: bool = False
    saving_throw: int = 15

@dataclass
class AttackContext:
    """ Dataclass to hold just the critical information to compute an attack roll """
    num_die: List[int] = field(default_factory=list)
    die_size: List[int] = field(default_factory=list)
    modifier: int = 0
    advantage: bool = False
    disadvantage: bool = False
    crit_on: int = 20
    reroll_on: int = 0
    difficulty_class: int = 15
    # Special cases
    always_hit: bool = False
    always_crit: bool = False

@dataclass
class DamageContext:
    """ Dataclass to hold just the critical information to compute damage """
    # Standard Hit Damage
    num_die: List[int] = field(default_factory=list)
    die_size: List[int] = field(default_factory=list)
    modifier: int = 0
    damage_multiplier: float = 1
    advantage: bool = False
    disadvantage: bool = False
    reroll_on: int = 0
    # Bonus Crit Damage, beyond the standard 2x die rolls
    crit_num_die: List[int] = field(default_factory=list)
    crit_damage_die: List[int] = field(default_factory=list)
    crit_damage_modifier: int = 0
    # Damage on Miss
    miss_num_die: List[int] = field(default_factory=list)
    miss_damage_die: List[int] = field(default_factory=list)
    miss_damage_modifier: int = 0
    failed_multiplier: float = 1
    # Special cases
    # TODO: Kill on hp remaining

def calculate_attack_and_damage_context(character, enemy, **kwargs):
    """ Extracts the attack and damage contexts for a given character and enemy """
    attack_contexts = []
    damage_contexts = []

    # Character Specific
    c_attack_num_die, c_attack_die_sizes, c_bonus_attack_mod = multiple_die_and_mod_from_list(character.bonus_attack_die_mod_list)
    c_damage_num_die, c_damage_die_sizes, c_bonus_damage_mod = multiple_die_and_mod_from_list(character.bonus_damage_die_mod_list)
    c_miss_num_die, c_miss_damage_die, c_miss_damage_modifier = multiple_die_and_mod_from_list(character.bonus_miss_die_mod_list)
    c_crit_num_die, c_crit_damage_die, c_crit_damage_modifier = multiple_die_and_mod_from_list(character.bonus_crit_die_mod_list)

    for attack in character.attacks:
        # From character
        ability_modifier = character.ability_modifier(attack.ability_stat)
        # Attack Roll
        attack_modifier = ability_modifier
        ## Proficiency, Spellcasting and unarmed attacks always add proficiency bonus
        if attack.proficent or attack.type in ['spell','unarmed']:
            attack_modifier += character.proficiency_bonus
        # Damage
        damage_modifier = 0
        damage_adv = False
        damage_dis = False
        damage_reroll_on = character.damage_reroll_on
        damage_multiplier = 1

        damage_failed_multiplier = 0

        # Attack Specific
        attack_num_die, attack_die_sizes, bonus_attack_mod = multiple_die_and_mod_from_list(attack.bonus_attack_die_mod_list)
        damage_num_die, damage_die_sizes, bonus_damage_mod = multiple_die_and_mod_from_list([attack.damage] + attack.bonus_damage_die_mod_list)
        miss_num_die, miss_damage_die, miss_damage_modifier = multiple_die_and_mod_from_list(attack.bonus_miss_die_mod_list)
        crit_num_die, crit_damage_die, crit_damage_modifier = multiple_die_and_mod_from_list(attack.bonus_crit_die_mod_list)

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

        ## Weapon attacks
        if character.raging:
            rage_modifier = 2
            if character.level >= 9:
                rage_modifier = 3

        if attack.type == 'weapon (melee)':
            damage_modifier += ability_modifier
            if attack.weapon_enhancement:
                attack_modifier += attack.weapon_enhancement
                damage_modifier += attack.weapon_enhancement
            if character.GWM and attack.two_handed:
                attack_modifier -= 5
                damage_modifier += 10
            if character.savage_attacker:
                damage_adv=True
            if character.dueling and not attack.two_handed:
                damage_modifier += 2
            if character.GWF and attack.two_handed:
                damage_reroll_on = max(damage_reroll_on, 2)
            if attack.offhand:
                damage_modifier -= ability_modifier
                if character.TWF and not attack.two_handed:
                    damage_modifier += ability_modifier
            # Barbarian
            if character.raging:
                damage_modifier += rage_modifier
            if character.brutal_critical:
                crit_num_die.append(1)
                _, weapon_die, _ = die_from_str(attack.damage)
                crit_damage_die.append(weapon_die)
            # Paladin
            if character.divine_smite:
                damage_num_die.append(min(2 + character.divine_smite_level-1,5))
                damage_die_sizes.append(8)
            if character.improved_divine_smite:
                damage_num_die.append(1)
                damage_die_sizes.append(8)
            # Warlock
            if character.lifedrinker:
                damage_modifier += character.charisma_ability_modifier
            # Half-Orc
            if character.savage_attacks_half_orc:
                crit_num_die.append(1)
                _, weapon_die, _ = die_from_str(attack.damage)
                crit_damage_die.append(weapon_die)
        elif attack.type == 'weapon (ranged)':
            damage_modifier += ability_modifier
            if character.archery:
                attack_modifier += 2
            if character.sharpshooter:
                attack_modifier -= 5
            if attack.offhand:
                damage_modifier -= character.ability_modifier
                if character.TWF and not attack.two_handed:
                    damage_modifier += ability_modifier
        elif attack.type == 'unarmed':
            damage_modifier += ability_modifier
            if character.tavern_brawler:
                attack_modifier += character.strength_ability_modifier
                damage_modifier += character.strength_ability_modifier
        elif attack.type == 'thrown': # TODO: Implement improvised thrown weapons
            damage_modifier += ability_modifier
            if character.tavern_brawler:
                attack_modifier += character.strength_ability_modifier
                damage_modifier += character.strength_ability_modifier
            if character.raging:
                damage_modifier += rage_modifier
        elif attack.type == 'spell':
            if character.agonizing_blast:
                damage_modifier += character.charisma_ability_modifier
            if character.empowered_evocation:
                damage_modifier += character.intelligence_ability_modifier
            if attack.saving_throw:
                #TODO: This is not right
                damage_failed_multiplier = attack.saving_throw_success_multiplier

        # Enemy Specific
        # TODO: Make this per attack
        if enemy.resistance:
            damage_multiplier *= 0.5
        if enemy.vulnerability:
            damage_multiplier *= 2

        # Difficulty Class
        difficulty_class = enemy.armor_class
        if attack.saving_throw and attack.type == 'spell':
            difficulty_class = character.spell_difficulty_class(attack.ability_stat)
            attack_roll_modifier = enemy.ability_modifier(attack.saving_throw_stat)
            if enemy.saving_throw_proficent:
                attack_roll_modifier += enemy.proficiency_bonus

        attack_context = AttackContext(
            num_die=attack_num_die,
            die_size=attack_die_sizes,
            modifier=attack_modifier,
            advantage=(character.advantage or attack.advantage),
            disadvantage=(character.disadvantage or attack.disadvantage),
            crit_on=min(character.crit_on, attack.crit_on),
            reroll_on=character.attack_reroll_on,
            difficulty_class=difficulty_class,
            **kwargs
        )
        # TODO: Add enemy damage reduction, resistance, and vulnerability, etc.
        damage_context = DamageContext(
            num_die=damage_num_die,
            die_size=damage_die_sizes,
            modifier=damage_modifier,
            damage_multiplier=damage_multiplier,
            advantage=damage_adv,
            disadvantage=damage_dis,
            reroll_on=damage_reroll_on,
            failed_multiplier=damage_failed_multiplier,
            crit_num_die=crit_num_die,
            crit_damage_die=crit_damage_die,
            crit_damage_modifier=crit_damage_modifier,
            miss_num_die=miss_num_die,
            miss_damage_die=miss_damage_die,
            miss_damage_modifier=miss_damage_modifier,
            **kwargs
        )

        attack_contexts.append(attack_context)
        damage_contexts.append(damage_context)
    return attack_contexts, damage_contexts
