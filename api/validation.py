""" Readable problems with a character's values before simulating, i.e. "Strength is empty" or a bad dice string """
from computations.models import DAMAGE_TYPES, multiple_die_and_mod_from_list

# Labels as the front end shows them
LABELS = {
    "level": "Level", "strength": "Strength", "dexterity": "Dexterity", "constitution": "Constitution", "intelligence": "Intelligence",
    "wisdom": "Wisdom", "charisma": "Charisma", "barbarian_level": "Barbarian level", "additional_spell_dc": "Spell save DC bonus",
    "crit_on": "Crit on", "attack_reroll_on": "Reroll attack die", "divine_smite_level": "Divine Smite level", "weapon_enhancement": "Enhancement",
    "saving_throw_success_multiplier": "Damage on a successful save", "damage_reroll_on": "Reroll damage dice", "damage": "Damage",
    "bonus_attack_die_mod_list": "Bonus to hit", "bonus_damage_die_mod_list": "Bonus damage", "bonus_crit_die_mod_list": "Bonus crit damage",
    "bonus_miss_die_mod_list": "Damage on a miss", "once_per_turn_die_mod_list": "Once per turn damage", "extra_damage_list": "Extra typed damage",
}
NUMERIC_CHARACTER_FIELDS = ["barbarian_level", "additional_spell_dc", "level", "strength", "dexterity", "constitution", "intelligence", "wisdom",
                            "charisma", "crit_on", "attack_reroll_on", "divine_smite_level"]
NUMERIC_ATTACK_FIELDS = ["crit_on", "weapon_enhancement", "saving_throw_success_multiplier", "damage_reroll_on"]
DIE_MOD_LISTS = ["bonus_attack_die_mod_list", "bonus_damage_die_mod_list", "bonus_crit_die_mod_list", "bonus_miss_die_mod_list", "once_per_turn_die_mod_list"]

def _dice_problems(values, label):
    try:
        multiple_die_and_mod_from_list(values or [])
        return []
    except (ValueError, AttributeError):
        return [f"{label} '{', '.join(str(v) for v in values or [])}' should be dice or numbers like 1d6, 2"]

def _typed_damage_problems(values):
    """ Each entry needs dice and/or a number, optionally followed by a damage type, i.e. '1d4 fire' """
    problems = []
    for v in values or []:
        parts = str(v).strip().lower().split()
        dice = parts[:-1] if len(parts) > 1 else parts
        if len(parts) > 1 and parts[-1] not in DAMAGE_TYPES:
            problems.append(f"{LABELS['extra_damage_list']}: unknown damage type '{parts[-1]}'")
        else:
            problems += _dice_problems(["".join(dice)], LABELS["extra_damage_list"])
    return problems

def validation_errors(character, attacks):
    """ Problems with a character dictionary and its attacks, empty if everything can be simulated """
    problems = [f"{LABELS[f]} is empty" for f in NUMERIC_CHARACTER_FIELDS if f in character and character[f] is None]
    for key in DIE_MOD_LISTS:
        problems += _dice_problems(character.get(key), LABELS[key])
    if not attacks:
        problems.append("it has no attacks")
    for a in attacks:
        name = a.get("name") or "an attack"
        problems += [f"attack '{name}': {LABELS[f]} is empty" for f in NUMERIC_ATTACK_FIELDS if f in a and a[f] is None]
        problems += [f"attack '{name}': {p}" for key in DIE_MOD_LISTS[:4] for p in _dice_problems(a.get(key), LABELS[key])]
        problems += [f"attack '{name}': {p}" for p in _dice_problems([a.get("damage") or ""], LABELS["damage"])]
        problems += [f"attack '{name}': {p}" for p in _typed_damage_problems(a.get("extra_damage_list"))]
    return problems
