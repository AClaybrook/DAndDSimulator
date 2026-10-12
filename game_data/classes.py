""" Class progression and prebuilt characters.
    Each build levels up like the real class: attacks per round, fighting styles, feats/ability score improvements,
    subclass features, cantrip scaling and spell slots all depend on the character level and ruleset.
    The output is a plain Character, so everything can still be tweaked in the UI afterwards. """
from copy import deepcopy
from dataclasses import asdict, dataclass, fields, replace
from math import ceil
from collections.abc import Callable

from computations.models import Attack, Character, STATS
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

# Adventuring day used to turn resources per rest into average uses per fight
FIGHTS_PER_LONG_REST = 4
SHORT_RESTS_PER_LONG_REST = 2

def per_fight(per_long_rest=0, per_short_rest=0):
    """ Average uses per fight of resources that recover on a long and/or short rest """
    return round((per_long_rest + per_short_rest * (SHORT_RESTS_PER_LONG_REST + 1)) / FIGHTS_PER_LONG_REST, 2)

# Spell slots per slot level for a full caster (or the multiclass spellcaster table) by caster level
FULL_CASTER_SLOTS = {
    1: [2], 2: [3], 3: [4, 2], 4: [4, 3], 5: [4, 3, 2], 6: [4, 3, 3], 7: [4, 3, 3, 1], 8: [4, 3, 3, 2],
    9: [4, 3, 3, 3, 1], 10: [4, 3, 3, 3, 2], 11: [4, 3, 3, 3, 2, 1], 12: [4, 3, 3, 3, 2, 1], 13: [4, 3, 3, 3, 2, 1, 1],
    14: [4, 3, 3, 3, 2, 1, 1], 15: [4, 3, 3, 3, 2, 1, 1, 1], 16: [4, 3, 3, 3, 2, 1, 1, 1], 17: [4, 3, 3, 3, 2, 1, 1, 1, 1],
    18: [4, 3, 3, 3, 3, 1, 1, 1, 1], 19: [4, 3, 3, 3, 3, 2, 1, 1, 1], 20: [4, 3, 3, 3, 3, 2, 2, 1, 1],
}

def spell_slots(caster_level):
    """ Spell slots per slot level for a caster level, i.e. a single class paladin uses ceil(level / 2) """
    return FULL_CASTER_SLOTS.get(int(caster_level), [])

def smite(character, slots, pact_slots_per_short_rest=0, pact_slot_level=0):
    """ Divine Smite on the first hit each round with the highest slot, limited by the slots per day """
    highest = max(len(slots), pact_slot_level)
    if highest:
        character.once_per_turn_die_mod_list = [f"{min(1 + highest, 5)}d8"]
        character.once_per_turn_uses_per_fight = per_fight(per_long_rest=sum(slots), per_short_rest=pact_slots_per_short_rest)

def action_surge(level, ruleset, attack):
    """ Action Surge attacks (fighter level 2+), used at the start of fights """
    if level < 2:
        return []
    surges = 2 if level >= 17 and ruleset == "5e" else 1
    uses = per_fight(per_short_rest=surges)
    return [replace(attack, name=f"{attack.name} (Action Surge)", uses_per_fight=uses) for _ in range(extra_attacks(level, "fighter", ruleset))]

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
                # Feats the simulator models are flags on the character, others (i.e. Dual Wielder) only change the build's gear
                if hasattr(character, choice[5:]):
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
    c.attacks += action_surge(level, ruleset, weapon_attack("Greatsword"))
    return _named(c, "Champion Fighter (GWM)", level, taken)

def fighter_two_weapon(level, ruleset):
    c = Character(level=level, strength=STARTING_PRIMARY, constitution=STARTING_SECONDARY, TWF=True)
    taken = apply_asi_plan(c, "fighter", level, ruleset, ["feat:Dual Wielder", "strength", "strength", "feat:savage_attacker", "constitution"])
    c.crit_on = 20 - (level >= 3) - (level >= 15)
    # Dual Wielder allows non-light weapons
    weapon = "Longsword" if "Dual Wielder" in taken else "Shortsword"
    c.attacks = [weapon_attack(weapon) for _ in range(extra_attacks(level, "fighter", ruleset))] + [weapon_attack(weapon, offhand=True)]
    c.attacks += action_surge(level, ruleset, weapon_attack(weapon))
    return _named(c, "Champion Fighter (Two Weapon Fighting)", level, taken)

def fighter_archer(level, ruleset):
    c = Character(level=level, dexterity=STARTING_PRIMARY, constitution=STARTING_SECONDARY, archery=True)
    taken = apply_asi_plan(c, "fighter", level, ruleset, ["feat:sharpshooter", "dexterity", "dexterity", "constitution"])
    c.crit_on = 20 - (level >= 3) - (level >= 15)
    c.attacks = [weapon_attack("Longbow") for _ in range(extra_attacks(level, "fighter", ruleset))]
    c.attacks += action_surge(level, ruleset, weapon_attack("Longbow"))
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
    if level >= 2:
        smite(c, spell_slots(ceil(level / 2)))
    c.attacks = [weapon_attack("Greatsword") for _ in range(extra_attacks(level, "paladin", ruleset))]
    return _named(c, "Paladin (Smite First Hit)", level, taken)

def fighter_battle_master(level, ruleset):
    c = Character(level=level, strength=STARTING_PRIMARY, constitution=STARTING_SECONDARY, GWF=True)
    taken = apply_asi_plan(c, "fighter", level, ruleset, ["feat:GWM", "strength", "strength", "feat:savage_attacker", "constitution"])
    if level >= 3:
        # A damage maneuver (i.e. Trip Attack) on the first hit each round, superiority dice grow at 10 and 18 and recover on a short rest
        c.once_per_turn_die_mod_list = [f"1d{8 + 2 * ((level >= 10) + (level >= 18))}"]
        c.once_per_turn_uses_per_fight = per_fight(per_short_rest=4 + (level >= 7) + (level >= 15))
    c.attacks = [weapon_attack("Greatsword") for _ in range(extra_attacks(level, "fighter", ruleset))]
    c.attacks += action_surge(level, ruleset, weapon_attack("Greatsword"))
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
    strike = Attack(name="Unarmed Strike", type="unarmed", ability_stat="dexterity", damage=f"1d{martial_arts}", damage_type="bludgeoning")
    # Attack action plus the Martial Arts bonus action strike, Flurry of Blows (from level 2) adds a strike for 1 ki, ki is the monk level per short rest
    c.attacks = [replace(strike) for _ in range(extra_attacks(level, "monk", ruleset) + 1)]
    if level >= 2:
        c.attacks.append(replace(strike, name="Flurry of Blows", uses_per_fight=per_fight(per_short_rest=level)))
    return _named(c, "Open Hand Monk (Flurry)", level, taken)

def warlock_eldritch_blast(level, ruleset):
    c = Character(level=level, charisma=STARTING_PRIMARY, constitution=STARTING_SECONDARY, agonizing_blast=level >= 2)
    taken = apply_asi_plan(c, "warlock", level, ruleset, ["charisma", "charisma", "constitution"])
    c.attacks = spell_attacks("Eldritch Blast", ability_stat="charisma", character_level=level, ruleset=ruleset, bonus_damage=["1d6"]) # Hex
    for ii, a in enumerate(c.attacks):
        a.name = f"Eldritch Blast Beam {ii + 1}"
    return _named(c, "Warlock (Eldritch Blast + Hex)", level, taken)

def warlock_hexblade(level, ruleset):
    c = Character(level=level, charisma=STARTING_PRIMARY, constitution=STARTING_SECONDARY, lifedrinker=level >= 12)
    taken = apply_asi_plan(c, "warlock", level, ruleset, ["charisma", "charisma", "constitution"])
    # Hexblade's Curse: proficiency bonus to damage and crits on 19, Hex Warrior: charisma weapon attacks
    c.bonus_damage_die_mod_list = [str(c.proficiency_bonus)]
    c.crit_on = 19
    num_attacks = 2 if level >= 5 else 1 # Thirsting Blade / Pact of the Blade extra attack
    c.attacks = [weapon_attack("Longsword", ability_stat="charisma", bonus_damage=["1d6"]) for _ in range(num_attacks)] # Hex
    return _named(c, "Hexblade Warlock (Pact of the Blade)", level, taken)

def sorlock(level, ruleset):
    """ Warlock 2 (Agonizing Blast) then Sorcerer, Quickened Spell casts a second Eldritch Blast with sorcery points """
    warlock_level = min(level, 2)
    sorcerer_level = level - warlock_level
    c = Character(level=level, charisma=STARTING_PRIMARY, constitution=STARTING_SECONDARY, agonizing_blast=warlock_level >= 2)
    taken = apply_asi_plan(c, "sorcerer", sorcerer_level, ruleset, ["charisma", "charisma", "constitution"])
    blasts = spell_attacks("Eldritch Blast", ability_stat="charisma", character_level=level, ruleset=ruleset, bonus_damage=["1d6"]) # Hex
    c.attacks = [replace(a, name=f"Eldritch Blast Beam {ii + 1}") for ii, a in enumerate(blasts)]
    # Metamagic at sorcerer level 2 in BG3 (3 in 5e), Quickened Spell costs 3 sorcery points in BG3 (2 in 5e), sorcery points = sorcerer level per long rest
    metamagic_level, quicken_cost = (2, 3) if ruleset == "bg3" else (3, 2)
    if sorcerer_level >= metamagic_level:
        uses = per_fight(per_long_rest=sorcerer_level // quicken_cost)
        c.attacks += [replace(a, name=f"Quickened Eldritch Blast Beam {ii + 1}", uses_per_fight=uses) for ii, a in enumerate(blasts)]
    c = _named(c, "Sorlock (Warlock 2 / Sorcerer)", level, taken)
    c.description += f". Warlock {warlock_level} / Sorcerer {sorcerer_level}"
    return c

def hexadin(level, ruleset):
    """ Hexblade Warlock 1 then Paladin: charisma weapon attacks, Hexblade's Curse, and smites with both spell and pact slots """
    paladin_level = level - 1
    c = Character(level=level, charisma=STARTING_PRIMARY, constitution=STARTING_SECONDARY, dueling=paladin_level >= 2)
    taken = apply_asi_plan(c, "paladin", paladin_level, ruleset, ["charisma", "charisma", "constitution"])
    c.bonus_damage_die_mod_list = [str(c.proficiency_bonus)] # Hexblade's Curse
    c.crit_on = 19
    c.improved_divine_smite = paladin_level >= 11
    if paladin_level >= 2:
        # Multiclass spell slots use half the paladin level (rounded down), plus the warlock's first level pact slot each short rest
        smite(c, spell_slots(paladin_level // 2), pact_slots_per_short_rest=1, pact_slot_level=1)
    c.attacks = [weapon_attack("Longsword", ability_stat="charisma") for _ in range(extra_attacks(paladin_level, "paladin", ruleset))]
    c = _named(c, "Hexadin (Hexblade 1 / Paladin)", level, taken)
    c.description += f". Warlock 1 / Paladin {paladin_level}"
    return c

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
    Build("fighter_two_weapon", "Champion Fighter (Two Weapon Fighting)", "fighter", "Two weapon fighting style, Dual Wielder at 4 for longswords, crits on 19 from level 3", fighter_two_weapon),
    Build("fighter_archer", "Champion Fighter (Archer)", "fighter", "Longbow, Archery, Sharpshooter at 4", fighter_archer),
    Build("barbarian_berserker", "Berserker Barbarian (Reckless)", "barbarian", "Greataxe, always raging, Reckless Attack, Frenzy, GWM at 4", barbarian_berserker),
    Build("paladin_smite", "Paladin (Smite First Hit)", "paladin", "Greatsword, GWF, smites the first hit each round with the highest slot", paladin_smite),
    Build("paladin_crit_fish", "Paladin (Smite Crits Only)", "paladin", "Same as the smite paladin, but only smites critical hits (crit fishing)", paladin_crit_fish),
    Build("rogue_dual_wield", "Rogue (Dual Shortswords)", "rogue", "Two shortswords, Sneak Attack on the first hit each round", rogue_dual_wield),
    Build("rogue_thief", "Thief Rogue (BG3 Fast Hands)", "rogue", "Dual shortswords, in BG3 Fast Hands' extra bonus action gives a second offhand attack from level 3", rogue_thief),
    Build("ranger_archer", "Hunter Ranger (Archer + Hunter's Mark)", "ranger", "Longbow, Archery, Hunter's Mark, Colossus Slayer, Sharpshooter at 4", ranger_hunter_archer),
    Build("monk_open_hand", "Open Hand Monk (Flurry)", "monk", "Unarmed strikes plus Flurry of Blows every round", monk_open_hand),
    Build("warlock_eb", "Warlock (Eldritch Blast + Hex)", "warlock", "Eldritch Blast with Agonizing Blast and Hex on every beam", warlock_eldritch_blast),
    Build("warlock_hexblade", "Hexblade Warlock (Pact of the Blade)", "warlock", "Charisma longsword with Hex and Hexblade's Curse (not limited per rest), extra attack at 5, Lifedrinker at 12", warlock_hexblade),
    Build("sorlock", "Sorlock (Warlock 2 / Sorcerer)", "multiclass", "Eldritch Blast with Agonizing Blast and Hex, plus a Quickened Eldritch Blast while sorcery points last", sorlock),
    Build("hexadin", "Hexadin (Hexblade 1 / Paladin)", "multiclass", "Charisma longsword with Dueling and Hexblade's Curse, smites from spell slots and the pact slot", hexadin),
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

# Fields decided by leveling up, edits to these on a preset character are not carried to other levels
LEVEL_UP_FIELDS = {"name", "level", "preset", "description", "attacks"}

def _keyed_attacks(attacks):
    """ Pairs each attack with (name, occurrence), i.e. the second 'Greatsword' is ('Greatsword', 1) """
    counts = {}
    keyed = []
    for a in attacks:
        keyed.append(((a.name, counts.get(a.name, 0)), a))
        counts[a.name] = counts.get(a.name, 0) + 1
    return keyed

def _attack_edits(edited, original):
    return {k: v for k, v in asdict(edited).items() if v != getattr(original, k)}

def apply_edits(character, original, rebuilt):
    """ Carries the edits made to a preset character (compared to the preset at the character's level) over to a rebuilt character.
        Ability scores keep their difference (so ability score improvements still happen), other fields keep the edited value.
        Attacks are matched by name and order: edited attacks keep their edits (new copies of an attack get the edits of its last copy),
        deleted attacks stay deleted and added attacks are kept """
    changes = {}
    for f in fields(Character):
        mine, base = getattr(character, f.name), getattr(original, f.name)
        if f.name in LEVEL_UP_FIELDS or mine == base:
            continue
        changes[f.name] = max(1, min(30, getattr(rebuilt, f.name) + mine - base)) if f.name in STATS else mine
    rebuilt = replace(rebuilt, **changes)

    original_attacks = dict(_keyed_attacks(original.attacks))
    my_attacks = dict(_keyed_attacks(character.attacks))
    last_edits = {}
    for key, a in _keyed_attacks(original.attacks):
        if key in my_attacks:
            last_edits[key[0]] = _attack_edits(my_attacks[key], a)
    attacks = []
    for key, a in _keyed_attacks(rebuilt.attacks):
        if key in original_attacks:
            if key not in my_attacks:
                continue # Deleted by the user
            edits = _attack_edits(my_attacks[key], original_attacks[key])
        else:
            edits = last_edits.get(key[0], {})
        attacks.append(replace(a, **deepcopy(edits)))
    attacks += [deepcopy(a) for key, a in my_attacks.items() if key not in original_attacks]
    rebuilt.attacks = attacks
    return rebuilt

def character_at_level(character, level):
    """ The character at another level. Preset characters are rebuilt so they gain attacks, feats and features like the real class,
        keeping any edits made after creating the preset (see apply_edits), other characters only change their level """
    key, _, ruleset = (character.preset or "").partition(":")
    if key in BUILDS:
        ruleset = ruleset if ruleset in RULESETS else "bg3"
        original = build_character(key, character.level, ruleset)
        rebuilt = apply_edits(character, original, build_character(key, level, ruleset))
        rebuilt.name = character.name
        return rebuilt
    return replace(character, level=level)

__all__ = ["BUILDS", "build_character", "character_at_level", "asi_levels", "cantrip_tier"]
