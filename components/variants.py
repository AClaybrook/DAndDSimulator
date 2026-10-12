""" Character variants: copies with one change, for quick what-if comparisons (i.e. is +2 strength better than a feat) """
from dataclasses import replace

from components.sweeps import primary_stat
from game_data.classes import character_at_level

MAX_LEVEL = 20
MAX_ABILITY_SCORE = 20

def _advantage(c):
    if c.advantage:
        return replace(c, advantage=False), "no Adv"
    return replace(c, advantage=True, disadvantage=False), "Adv"

def _level_up(c):
    if c.level >= MAX_LEVEL:
        raise ValueError(f"{c.name} is already level {MAX_LEVEL}")
    return character_at_level(c, c.level + 1), f"Lv {c.level + 1}"

def _ability_score(c):
    stat = primary_stat(c)
    score = getattr(c, stat)
    if score >= MAX_ABILITY_SCORE:
        raise ValueError(f"{c.name}'s {stat.title()} is already {score}, the most an ASI can give")
    gain = min(2, MAX_ABILITY_SCORE - score)
    return replace(c, **{stat: score + gain}), f"+{gain} {stat[:3].title()}"

def _power_attack(c):
    if c.GWM or c.sharpshooter:
        return replace(c, GWM=False, sharpshooter=False), "no GWM/SS"
    # Each feat only applies to its own attacks (heavy melee or ranged weapons), so turning both on is safe
    return replace(c, GWM=True, sharpshooter=True), "GWM/SS"

def _bless(c):
    if any(str(d).replace(" ", "").startswith("1d4") for d in c.bonus_attack_die_mod_list):
        raise ValueError(f"{c.name} already has a 1d4 attack bonus, Bless doesn't stack")
    return replace(c, bonus_attack_die_mod_list=[*c.bonus_attack_die_mod_list, "1d4"]), "Bless"

# Key: (menu label, function returning the changed character and a name suffix). "copy" copies the card as is
VARIANTS = {
    "copy": ("Exact copy", None),
    "advantage": ("Toggle advantage", _advantage),
    "level": ("One level higher", _level_up),
    "ability": ("+2 main ability score (ASI)", _ability_score),
    "power": ("Toggle GWM / Sharpshooter", _power_attack),
    "bless": ("Add Bless (+1d4 to hit)", _bless),
}

def make_variant(character, key):
    """ A copy of the character with one change, named i.e. 'Fighter (+2 Str)'. Raises ValueError if the change isn't possible """
    variant, suffix = VARIANTS[key][1](character)
    return replace(variant, name=f"{character.name} ({suffix})")
