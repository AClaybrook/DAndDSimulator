
from dataclasses import dataclass

### Utility functions ###
def die_from_str(die_str):
    """Returns the number of dice and die size from a string of the form '2d6'"""
    die_str = die_str.lower()
    num_die, die_size = die_str.split('d')
    return int(num_die), int(die_size)

### Classes ###

# TODO: Change this to a Creature class, and have Character and Enemy inherit from it
@dataclass
class Character:
    name: str = 'Character'
    num_attacks: int = 1
    # Attack and Damage Roll Modifiers
    ability_modifier: int = 0
    GWM: bool = False
    weapon_modifier: int = 0
    # Attack Roll Modifiers
    proficiency_bonus: int = 2
    adv: bool = False
    dis: bool = False
    additional_attack_modifier: int = 0
    attack_reroll_on: int = None
    crit_on: int = 20
    # Damage Roll Modifiers
    weapon_die: str = '1d6'
    additional_damage_modifier: int = 0
    GWF: bool = False
    # _damage_reroll_on: int = None # Internal variable managed by @property and setter

    @property
    def weapon_num_die(self):
        return die_from_str(self.weapon_die)[0]
    
    @property
    def weapon_damage_die(self):
        return die_from_str(self.weapon_die)[1]
    
    @property
    def attack_modifier(self):
        GWM_modifier = -5 if self.GWM else 0
        return self.ability_modifier + self.proficiency_bonus + self.weapon_modifier + GWM_modifier + self.additional_attack_modifier

    @property
    def damage_modifier(self):
        GWM_modifier = 10 if self.GWM else 0
        return self.ability_modifier + self.weapon_modifier + GWM_modifier + self.additional_damage_modifier
    
    @property
    def damage_reroll_on(self):
        return 2 if self.GWF else None
    
    # @property
    # def damage_reroll_on(self):
    #     if self._damage_reroll_on is not None:
    #         return self._damage_reroll_on
    #     return 2 if self.GWF else None
    
    # @damage_reroll_on.setter
    # def damage_reroll_on(self, value):
    #     self._damage_reroll_on = value

@dataclass
class Enemy:
    name: str = 'Mind Flayer'
    armor_class: int = 15
    hit_points: int = 71
    damage_reduction: int = 0
    resistance: bool = False
    vulnerability: bool = False

@dataclass
class AttackContext:
    attack_modifier: int = 0
    adv: bool = False
    dis: bool = False
    crit_on: int = 20
    reroll_on: int = None
    enemy_armor_class: int = 15

    @staticmethod
    def from_character_and_enemy(character, enemy, **kwargs):
        return AttackContext(
            attack_modifier=character.attack_modifier,
            adv=character.adv,
            dis=character.dis,
            crit_on=character.crit_on,
            reroll_on=character.attack_reroll_on,
            enemy_armor_class=enemy.armor_class,
            **kwargs
        )
    
@dataclass
class DamageContext:
    num_die: int = 1
    damage_die: int = 6
    damage_modifier: int = 0
    reroll_on: int = None

    @staticmethod
    def from_character_and_enemy(character, enemy, **kwargs):
        # TODO: Add enemy damage reduction, resistance, and vulnerability, etc.
        return DamageContext(
            num_die=character.weapon_num_die,
            damage_die=character.weapon_damage_die,
            damage_modifier=character.damage_modifier,
            reroll_on=character.damage_reroll_on,
            **kwargs
        )