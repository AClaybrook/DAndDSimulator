
from dataclasses import dataclass, field
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
        else:
            elem = elem.lower().replace(" ","")
            if 'd' in elem:
                n,s,m = die_from_str(elem)
                num_die.append(n)
                die_sizes.append(s)
            else:
                m = int(elem)
        total_mod += m
    return num_die, die_sizes, total_mod

### Classes ###

@dataclass
class Attack:
    name: str = 'Attack'
    attack_die_mod_list: list[str,int] = field(default_factory=list) # Format is ['1d6', 2]
    damage_die_mod_list: list[str,int] = field(default_factory=list) # Format is ['1d6', 2]
    proficent: bool = True
    type: Literal["weapon (melee)","weapon (ranged)","spell","unarmed","thrown"] = 'weapon (melee)'
    ability_stat: Literal["strength","dexterity","constitution","intelligence","wisdom","charisma"] = 'strength'
    # Weapon Specific
    weapon_enhancement: int = 0
    offhand: bool = False
    two_handed: bool = False
    # Spell Specific
    saving_throw: bool = False
    saving_throw_stat: Literal["strength","dexterity","constitution","intelligence","wisdom","charisma"] = 'dexterity'
    saving_throw_success_multiplier: float = 0.5
    # Unused
    damage_type = 'slashing'


@dataclass
class Creature:
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
    # Unused
    hit_points: int = 12
    initiative: int = 0
    type = 'humanoid'
    description: str  = 'A creature'

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


@dataclass(kw_only=True)
class Character(Creature):
    name: str = 'Character'
    # Attack Roll Modifiers
    adv: bool = False
    dis: bool = False
    additional_attack_modifier: int = 0
    attack_reroll_on: int = 0
    crit_on: int = 20
    additional_damage_modifier: int = 0
    damage_reroll_on: int = 0
    damage_on_miss: int = 0
    # Additional Crit Damage
    additional_crit_damage_die: str = '0d6'
    additional_crit_damage_modifier: int = 0
    # Additional Spell DC
    additional_spell_dc: int = 0

    # Feats/Abilities
    savage_attacker: bool = False # advantage on damage rerolls
    tavern_brawler: bool = False # strength modifier added to attack and damage rolls
    GWM: bool = False # -5 to hit, +10 to damage, TODO: bonus action attack on crit or kill
    sharpshooter: bool = False

    # Racial Traits (only half orc affects damage directly)
    savage_attacks_half_orc: bool = False
    # Class Traits
    # Fighter, Fighter Style
    archery: bool = False
    duelling: bool = False
    GWF: bool = False # reroll 1s and 2s on damage
    TWF: bool = False
    # Barbarian
    rage: bool = False
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

    def attack_modifier(self,stat):
        return self.ability_modifier(stat) + self.proficiency_bonus + self.additional_attack_modifier

    def damage_modifier(self,stat):
        return self.ability_modifier(stat) + self.additional_damage_modifier
    
    
    def spell_casting_modifier(self, stat):
        return self.ability_modifier(stat=stat)

    def spell_difficulty_class(self, stat):
        spell_casting_mod = self.spell_casting_modifier(stat)
        return 8 + self.proficiency_bonus + spell_casting_mod + self.additional_spell_dc

@dataclass(kw_only=True)
class Enemy(Creature):
    name: str = 'Mind Flayer'
    armor_class: int = 15
    hit_points: int = 71
    damage_reduction: int = 0
    resistance: bool = False
    vulnerability: bool = False
    saving_throw: int = 15

@dataclass
class AttackContext:
    num_die: List[int] = field(default_factory=list)
    die_size: List[int] = field(default_factory=list)
    modifier: int = 0
    adv: bool = False
    dis: bool = False
    crit_on: int = 20
    reroll_on: int = 0
    difficulty_class: int = 15
    always_hit: bool = False
    always_crit: bool = False

@dataclass
class DamageContext:
    # Standard Hit Damage
    num_die: List[int] = field(default_factory=list)
    die_size: List[int] = field(default_factory=list)
    modifier: int = 0
    damage_multiplier: float = 1
    adv: bool = False
    dis: bool = False
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
   
def calculate_attack_and_damage_context(character, enemy, **kwargs):
    attack_contexts = []
    damage_contexts = []
    for attack in character.attacks:
        # From character
        ability_modifier = character.ability_modifier(attack.ability_stat)
        # Attack Roll 
        attack_modifier = ability_modifier
        ## Proficiency, Spellcasting always uses proficency
        if attack.proficent or attack.type == 'spell':
            attack_modifier += character.proficiency_bonus
        # Damage
        damage_modifier = ability_modifier
        if attack.offhand:
            damage_modifier -= character.ability_modifier
        attack_adv = character.adv
        attack_dis = character.dis
        damage_adv = False
        damage_dis = False
        damage_reroll_on = character.damage_reroll_on
        damage_multiplier: float = 1

        damage_modifier: int = 0
        damage_multiplier: float = 1
        damage_failed_multiplier = 0
        crit_num_die = []
        crit_damage_die = []
        crit_damage_modifier = 0
        miss_num_die = []
        miss_damage_die = []
        miss_damage_modifier = 0

        # Attack Specific
        attack_num_die, attack_die_sizes, add_attack_mod = multiple_die_and_mod_from_list(attack.attack_die_mod_list)
        damage_num_die, damage_die_sizes, add_damage_mod = multiple_die_and_mod_from_list(attack.damage_die_mod_list)

        attack_modifier += add_attack_mod
        damage_modifier += add_damage_mod

        ## Weapon attacks
        if character.rage:
            rage_modifier = 2 
            if character.level >= 9:
                rage_modifier = 3

        if attack.type == 'weapon (melee)':
            if attack.weapon_enhancement:
                attack_modifier += attack.weapon_enhancement
                damage_modifier += attack.weapon_enhancement
            if character.GWM and attack.two_handed:
                attack_modifier -= 5
                damage_modifier += 10
            if character.savage_attacker:
                damage_adv=True
            if character.duelling and not attack.two_handed:
                damage_modifier += 2
            if character.GWF and attack.two_handed:
                damage_reroll_on = max(damage_reroll_on, 2)
            if character.TWF and attack.offhand and not attack.two_handed:
                damage_modifier += ability_modifier
            if character.rage:
                damage_modifier += rage_modifier
            if character.brutal_critical:
                crit_num_die.append(1)
                weapon_die = damage_die_sizes[0] # TODO: Specify weapon die or infer correctly
                crit_damage_die.append(weapon_die)
            if character.divine_smite:
                damage_num_die.append(min(2 + character.divine_smite_level-1,5))
                damage_die_sizes.append(8)
            if character.improved_divine_smite:
                damage_num_die.append(1)
                damage_die_sizes.append(8)
            if character.lifedrinker:
                damage_modifier += character.charisma_ability_modifier
            if character.savage_attacks_half_orc:
                crit_num_die.append(1)
                weapon_die = damage_die_sizes[0] # TODO: Specify weapon die or infer correctly
                crit_damage_die.append(weapon_die)
        elif attack.type == 'weapon (ranged)':
            if character.archery:
                attack_modifier += 2
            if character.sharpshooter:
                attack_modifier -= 5
        elif attack.type == 'unarmed':
            if character.tavern_brawler:
                attack_modifier += character.strength_ability_modifier
                damage_modifier += character.strength_ability_modifier
        elif attack.type == 'thrown':
            if character.tavern_brawler:
                attack_modifier += character.strength_ability_modifier
                damage_modifier += character.strength_ability_modifier
            if character.rage:
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
            modifier=attack_modifier,
            adv=attack_adv,
            dis=attack_dis,
            crit_on=character.crit_on,
            reroll_on=character.attack_reroll_on,
            difficulty_class=difficulty_class,
            **kwargs
        )
        # TODO: Add enemy damage reduction, resistance, and vulnerability, etc.
        damage_context = DamageContext(
            num_die=damage_num_die,
            die_size=damage_die_sizes,
            modifier=damage_modifier,
            adv=damage_adv,
            dis=damage_dis,
            reroll_on=damage_reroll_on,
            failed_multiplier=damage_failed_multiplier,
            **kwargs
        )

        attack_contexts.append(attack_context)
        damage_contexts.append(damage_context)
    return attack_contexts, damage_contexts

