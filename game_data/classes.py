""" Class progression and prebuilt characters.
    Each build levels up like the real class: attacks per round, fighting styles, feats/ability score improvements,
    subclass features, cantrip scaling and spell slots all depend on the character level and ruleset.
    The output is a plain Character, so everything can still be tweaked in the UI afterwards. """
from dataclasses import dataclass, replace
from math import ceil
from collections.abc import Callable

from computations.models import Attack, Character
from game_data import RULESETS, cantrip_tier, spell_attacks, weapon_attack

# Point buy (15) + racial/background bonus (+2), the usual optimized starting primary stat
STARTING_PRIMARY = 17
STARTING_SECONDARY = 14

FEAT_LABELS = {"GWM": "Great Weapon Master", "sharpshooter": "Sharpshooter", "savage_attacker": "Savage Attacker"}

def asi_levels(class_name, ruleset="bg3"):
    """ Levels where a feat or ability score improvement is gained """
    levels = [4, 8, 12, 16, 19]
    if class_name == "fighter":
        levels += [6, 14]
    if class_name == "rogue":
        levels += [10]
    return sorted(lv for lv in levels if lv <= RULESETS[ruleset]["max_level"])

def half_caster_slot(level):
    """ Highest spell slot for paladins and rangers """
    return 0 if level < 2 else 1 if level < 5 else 2 if level < 9 else 3 if level < 13 else 4 if level < 17 else 5

def full_caster_slot(level):
    """ Highest spell slot for full casters (wizard, sorcerer, cleric...) """
    return min(9, (level + 1) // 2)

def apply_asi_plan(character, class_name, level, ruleset, plan):
    """ Applies feats ("feat:GWM") and ability score improvements ("strength") in order for every ASI level reached.
        Ability score improvements are +2 (capped at 20), a capped stat falls through to the next plan item """
    remaining = list(plan)
    taken = []
    for _ in [lv for lv in asi_levels(class_name, ruleset) if lv <= level]:
        while remaining:
            choice = remaining.pop(0)
            if choice.startswith("feat:"):
                setattr(character, choice[5:], True)
                taken.append(FEAT_LABELS.get(choice[5:], choice[5:]))
                break
            if getattr(character, choice) < 20:
                setattr(character, choice, min(getattr(character, choice) + 2, 20))
                taken.append(f"+2 {choice[:3].title()}")
                break
    return taken

def extra_attacks(level, class_name, ruleset):
    """ Number of attacks with the attack action """
    if class_name == "fighter":
        return 1 + (level >= 5) + (level >= 11) + (level >= 20 and ruleset == "5e")
    if class_name in ("barbarian", "paladin", "ranger", "monk"):
        return 1 + (level >= 5)
    return 1

@dataclass
class Build:
    """ A prebuilt character that levels up """
    key: str
    label: str
    class_name: str
    description: str
    build: Callable[[int, str], Character]

def _named(character, label, level, taken):
    character.name = f"{label} L{level}"
    character.description = f"{label}, level {level}. Feats/ASIs: {', '.join(taken) or 'none'}"
    return character

def fighter_champion_gwm(level, ruleset):
    c = Character(level=level, strength=STARTING_PRIMARY, constitution=STARTING_SECONDARY, GWF=True)
    taken = apply_asi_plan(c, "fighter", level, ruleset, ["feat:GWM", "strength", "strength", "feat:savage_attacker", "constitution"])
    c.crit_on = 20 - (level >= 3) - (level >= 15) # Improved/Superior Critical
    c.attacks = [weapon_attack("Greatsword") for _ in range(extra_attacks(level, "fighter", ruleset))]
    return _named(c, "Champion Fighter (GWM)", level, taken)

def fighter_archer(level, ruleset):
    c = Character(level=level, dexterity=STARTING_PRIMARY, constitution=STARTING_SECONDARY, archery=True)
    taken = apply_asi_plan(c, "fighter", level, ruleset, ["feat:sharpshooter", "dexterity", "dexterity", "constitution"])
    c.crit_on = 20 - (level >= 3) - (level >= 15)
    c.attacks = [weapon_attack("Longbow") for _ in range(extra_attacks(level, "fighter", ruleset))]
    return _named(c, "Champion Fighter (Archer)", level, taken)

def barbarian_berserker(level, ruleset):
    c = Character(level=level, strength=STARTING_PRIMARY, constitution=STARTING_SECONDARY + 2, raging=True)
    taken = apply_asi_plan(c, "barbarian", level, ruleset, ["feat:GWM", "strength", "strength", "constitution"])
    c.advantage = level >= 2 # Reckless Attack
    c.brutal_critical = level >= 9
    num_attacks = extra_attacks(level, "barbarian", ruleset) + (level >= 3) # Frenzy bonus action attack
    c.attacks = [weapon_attack("Greataxe") for _ in range(num_attacks)]
    return _named(c, "Berserker Barbarian (Reckless)", level, taken)

def paladin_smite(level, ruleset):
    c = Character(level=level, strength=STARTING_PRIMARY, charisma=STARTING_SECONDARY + 2, GWF=level >= 2)
    taken = apply_asi_plan(c, "paladin", level, ruleset, ["feat:GWM", "strength", "strength", "charisma"])
    c.improved_divine_smite = level >= 11
    slot = half_caster_slot(level)
    if slot:
        # Smite the first hit each round with the highest slot
        c.once_per_turn_die_mod_list = [f"{min(1 + slot, 5)}d8"]
    c.attacks = [weapon_attack("Greatsword") for _ in range(extra_attacks(level, "paladin", ruleset))]
    return _named(c, "Paladin (Smite First Hit)", level, taken)

def fighter_battle_master(level, ruleset):
    c = Character(level=level, strength=STARTING_PRIMARY, constitution=STARTING_SECONDARY, GWF=True)
    taken = apply_asi_plan(c, "fighter", level, ruleset, ["feat:GWM", "strength", "strength", "feat:savage_attacker", "constitution"])
    if level >= 3:
        # A damage maneuver (i.e. Trip Attack) on the first hit each round, superiority dice grow at 10 and 18
        c.once_per_turn_die_mod_list = [f"1d{8 + 2 * ((level >= 10) + (level >= 18))}"]
    c.attacks = [weapon_attack("Greatsword") for _ in range(extra_attacks(level, "fighter", ruleset))]
    return _named(c, "Battle Master Fighter (GWM)", level, taken)

def paladin_crit_fish(level, ruleset):
    c = paladin_smite(level, ruleset)
    c.once_per_turn_crit_only = True
    return c

def rogue_thief(level, ruleset):
    c = rogue_dual_wield(level, ruleset)
    if level >= 3 and ruleset == "bg3":
        # Fast Hands gives a second bonus action in BG3, used for a second offhand attack
        c.attacks.append(weapon_attack("Shortsword", ability_stat="dexterity", offhand=True))
    return c

def rogue_dual_wield(level, ruleset):
    c = Character(level=level, dexterity=STARTING_PRIMARY, constitution=STARTING_SECONDARY)
    taken = apply_asi_plan(c, "rogue", level, ruleset, ["dexterity", "dexterity", "constitution"])
    c.once_per_turn_die_mod_list = [f"{ceil(level / 2)}d6"] # Sneak Attack
    c.attacks = [weapon_attack("Shortsword", ability_stat="dexterity"), weapon_attack("Shortsword", ability_stat="dexterity", offhand=True)]
    return _named(c, "Rogue (Dual Shortswords)", level, taken)

def ranger_hunter_archer(level, ruleset):
    c = Character(level=level, dexterity=STARTING_PRIMARY, wisdom=STARTING_SECONDARY, archery=level >= 2)
    taken = apply_asi_plan(c, "ranger", level, ruleset, ["feat:sharpshooter", "dexterity", "dexterity", "wisdom"])
    hunters_mark = ["1d6"] if level >= 2 else []
    if level >= 3:
        c.once_per_turn_die_mod_list = ["1d8"] # Colossus Slayer
    c.attacks = [weapon_attack("Longbow", bonus_damage=hunters_mark) for _ in range(extra_attacks(level, "ranger", ruleset))]
    return _named(c, "Hunter Ranger (Archer + Hunter's Mark)", level, taken)

def monk_open_hand(level, ruleset):
    c = Character(level=level, dexterity=STARTING_PRIMARY, wisdom=STARTING_SECONDARY + 2)
    taken = apply_asi_plan(c, "monk", level, ruleset, ["dexterity", "dexterity", "wisdom"])
    martial_arts = 4 + 2 * ((level >= 5) + (level >= 11) + (level >= 17))
    flurry = 2 if level >= 2 else 1 # Martial Arts bonus action strike, Flurry of Blows from level 2
    num_attacks = extra_attacks(level, "monk", ruleset) + flurry
    c.attacks = [Attack(name="Unarmed Strike", type="unarmed", ability_stat="dexterity", damage=f"1d{martial_arts}", damage_type="bludgeoning") for _ in range(num_attacks)]
    return _named(c, "Open Hand Monk (Flurry)", level, taken)

def warlock_eldritch_blast(level, ruleset):
    c = Character(level=level, charisma=STARTING_PRIMARY, constitution=STARTING_SECONDARY, agonizing_blast=level >= 2)
    taken = apply_asi_plan(c, "warlock", level, ruleset, ["charisma", "charisma", "constitution"])
    c.attacks = spell_attacks("Eldritch Blast", ability_stat="charisma", character_level=level, ruleset=ruleset, bonus_damage=["1d6"]) # Hex
    for ii, a in enumerate(c.attacks):
        a.name = f"Eldritch Blast Beam {ii + 1}"
    return _named(c, "Warlock (Eldritch Blast + Hex)", level, taken)

def sorcerer_draconic_fire_bolt(level, ruleset):
    c = Character(level=level, charisma=STARTING_PRIMARY, constitution=STARTING_SECONDARY, elemental_affinity=level >= 6)
    taken = apply_asi_plan(c, "sorcerer", level, ruleset, ["charisma", "charisma", "constitution"])
    c.attacks = spell_attacks("Fire Bolt", ability_stat="charisma", character_level=level, ruleset=ruleset)
    return _named(c, "Draconic Sorcerer (Fire Bolt)", level, taken)

def wizard_evoker_fireball(level, ruleset):
    c = Character(level=level, intelligence=STARTING_PRIMARY, constitution=STARTING_SECONDARY, empowered_evocation=level >= 10)
    taken = apply_asi_plan(c, "wizard", level, ruleset, ["intelligence", "intelligence", "constitution"])
    slot = full_caster_slot(level)
    if slot >= 3:
        c.attacks = spell_attacks("Fireball", ability_stat="intelligence", slot_level=slot, ruleset=ruleset)
    else:
        c.attacks = spell_attacks("Burning Hands", ability_stat="intelligence", slot_level=slot, ruleset=ruleset)
    return _named(c, "Evocation Wizard (Highest Slot Fireball)", level, taken)

BUILDS = {b.key: b for b in [
    Build("fighter_gwm", "Champion Fighter (GWM)", "fighter", "Greatsword, Great Weapon Fighting, GWM at 4, crits on 19 from level 3", fighter_champion_gwm),
    Build("fighter_battle_master", "Battle Master Fighter (GWM)", "fighter", "Greatsword, GWF, GWM, a damage maneuver on the first hit each round (superiority dice are not limited)", fighter_battle_master),
    Build("fighter_archer", "Champion Fighter (Archer)", "fighter", "Longbow, Archery, Sharpshooter at 4", fighter_archer),
    Build("barbarian_berserker", "Berserker Barbarian (Reckless)", "barbarian", "Greataxe, always raging, Reckless Attack, Frenzy, GWM at 4", barbarian_berserker),
    Build("paladin_smite", "Paladin (Smite First Hit)", "paladin", "Greatsword, GWF, smites the first hit each round with the highest slot", paladin_smite),
    Build("paladin_crit_fish", "Paladin (Smite Crits Only)", "paladin", "Same as the smite paladin, but only smites critical hits (crit fishing)", paladin_crit_fish),
    Build("rogue_dual_wield", "Rogue (Dual Shortswords)", "rogue", "Two shortswords, Sneak Attack on the first hit each round", rogue_dual_wield),
    Build("rogue_thief", "Thief Rogue (BG3 Fast Hands)", "rogue", "Dual shortswords, in BG3 Fast Hands' extra bonus action gives a second offhand attack from level 3", rogue_thief),
    Build("ranger_archer", "Hunter Ranger (Archer + Hunter's Mark)", "ranger", "Longbow, Archery, Hunter's Mark, Colossus Slayer, Sharpshooter at 4", ranger_hunter_archer),
    Build("monk_open_hand", "Open Hand Monk (Flurry)", "monk", "Unarmed strikes plus Flurry of Blows every round", monk_open_hand),
    Build("warlock_eb", "Warlock (Eldritch Blast + Hex)", "warlock", "Eldritch Blast with Agonizing Blast and Hex on every beam", warlock_eldritch_blast),
    Build("sorcerer_fire_bolt", "Draconic Sorcerer (Fire Bolt)", "sorcerer", "Fire Bolt with Elemental Affinity from level 6", sorcerer_draconic_fire_bolt),
    Build("wizard_fireball", "Evocation Wizard (Highest Slot Fireball)", "wizard", "Single target Fireball (Burning Hands before level 5) with the highest slot every round", wizard_evoker_fireball),
]}

def build_character(key, level, ruleset="bg3"):
    """ Builds a prebuilt character at a given level """
    level = max(1, min(int(level), RULESETS[ruleset]["max_level"]))
    character = BUILDS[key].build(level, ruleset)
    # Builds that extend another build keep its name, so name it after the build that was asked for
    base_label = character.name.rsplit(" L", 1)[0]
    character.name = f"{BUILDS[key].label} L{level}"
    character.description = character.description.replace(base_label, BUILDS[key].label, 1)
    character.preset = f"{key}:{ruleset}"
    return character

def character_at_level(character, level):
    """ The character at another level. Preset characters are rebuilt so they gain attacks, feats and features like the real class
        (edits made after creating the preset are not kept), other characters only change their level """
    key, _, ruleset = (character.preset or "").partition(":")
    if key in BUILDS:
        rebuilt = build_character(key, level, ruleset if ruleset in RULESETS else "bg3")
        rebuilt.name = character.name
        return rebuilt
    return replace(character, level=level)

__all__ = ["BUILDS", "build_character", "character_at_level", "asi_levels", "cantrip_tier"]
