""" An all round score for a character at an act, 0 to 100, so a well rounded build can rank above pure damage.

    Six parts, each scored 0 to 100 against fixed per act references (so the score means the same thing in every party), then weighted:
      damage   single target damage per round            100 at 1.5 x a strong build for the act
      aoe      extra damage against a group of 3          100 at 1.5 x a strong area build
      defence  effective HP: hit points / chance to be hit 100 at 1.5 x a sturdy front liner
      control, support, utility                           points for the tools a build has (see each function), capped at 100
    The weights are a choice, not a fact: change WEIGHTS (or pass weights) to rank for a role. docs/scoring.md explains the method """
from dataclasses import dataclass, field

from bg3.build import buffs_at, compile_build, equipment_at
from bg3.character import Bg3Character, class_levels, class_order, feat_opportunities, subclass_of
from bg3.checkpoints import act_level
from bg3.defence import armour_class, hit_chance
from bg3.items import reverberation_per_round
from computations.analytic import expected_damage_vs_enemies

WEIGHTS = {"damage": 35, "aoe": 10, "defence": 25, "control": 10, "support": 10, "utility": 10}
# References per act: what a strong build does (from the planner's example rankings at levels 5, 8 and 12)
DAMAGE_REF = {"1": 40, "2": 60, "3": 95}
AOE_REF = {"1": 15, "2": 30, "3": 50}
EHP_REF = {"1": 110, "2": 170, "3": 250} # About 50, 75 and 110 hit points at a 45% chance to be hit
HIT_DIE = {"barbarian": 12, "fighter": 10, "paladin": 10, "ranger": 10, "bard": 8, "cleric": 8, "druid": 8, "monk": 8, "rogue": 8,
           "warlock": 8, "sorcerer": 6, "wizard": 6}
CONTROL_ITEMS = {"bg3:bow_of_the_banshee": 15, "bg3:sussur_greatsword": 10, "bg3:sussur_dagger": 10, "bg3:sussur_sickle": 10,
                 "bg3:gloves_of_power": 5, "bg3:ritual_axe": 5, "bg3:giantbreaker": 10}
SUPPORT_ITEMS = {"bg3:phalar_aluve": 15, "bg3:staff_of_arcane_blessing": 10, "bg3:amulet_of_restoration": 15, "bg3:the_whispering_promise": 10,
                 "bg3:hellrider_s_pride": 10, "bg3:cap_of_curing": 5, "bg3:wondrous_gloves": 5}
UTILITY_ITEMS = {"bg3:amulet_of_misty_step": 10, "bg3:shar_s_spear_of_evening": 10, "bg3:boots_of_speed": 10, "bg3:sunwalker_s_gift": 5,
                 "bg3:ring_of_jumping": 5, "bg3:mask_of_the_shapeshifter": 10}

@dataclass
class Score:
    total: float
    parts: dict = field(default_factory=dict) # part: 0-100
    notes: dict = field(default_factory=dict) # part: what it came from

def _scaled(value, reference):
    return max(0.0, min(100.0, 100 * value / (1.5 * reference)))

def _classes(build, act):
    level = act_level(act, build.levels)
    if build.character:
        character = Bg3Character.from_dict(build.character)
        levels = class_levels(character, level)
        taken = list(character.feats)[:len(feat_opportunities(character, level))] # Feats chosen by this level
        return levels, {cls: subclass_of(character, cls, n) for cls, n in levels.items()}, class_order(character, level), taken
    cls = build.preset.split("_")[0]
    return {cls: level}, {}, [cls] * level, []

def hit_points(build, act):
    """ BG3 hit points: the first class's full hit die at level 1, then half the die + 1 per level, plus CON each level; Tough +2 a level """
    levels, _, order, feats = _classes(build, act)
    con = (compile_build(build, act).constitution - 10) // 2
    if not order:
        return 1
    hp = HIT_DIE.get(order[0], 8) + con + sum(HIT_DIE.get(cls, 8) // 2 + 1 + con for cls in order[1:])
    if "Tough" in feats:
        hp += 2 * len(order)
    return max(hp, 1)

def control_points(build, act):
    levels, subs, _, _ = _classes(build, act)
    gear = set(equipment_at(build, act).values())
    caster = sum(n for cls, n in levels.items() if cls in ("bard", "cleric", "druid", "sorcerer", "warlock", "wizard"))
    caster += levels.get("paladin", 0) // 2 + levels.get("ranger", 0) // 2
    points, why = 0, []
    if caster >= 3:
        points += 25 + 5 * min(caster - 3, 7)
        why.append(f"{caster} caster levels (Hold Person, Command, Web...)")
    if levels.get("monk", 0) >= 5:
        points += 25
        why.append("Stunning Strike")
    if subs.get("fighter") == "Battle Master":
        points += 20
        why.append("manoeuvres (Trip, Menacing)")
    if levels.get("rogue", 0) >= 3 and subs.get("rogue") == "Swashbuckler":
        points += 15
        why.append("Dirty Tricks")
    if reverberation_per_round(compile_build(build, act), gear) > 1:
        points += 15
        why.append("Reverberation and Prone")
    for key, value in CONTROL_ITEMS.items():
        if key in gear:
            points += value
            why.append(key.split(":")[1].replace("_", " "))
    return min(points, 100), why

def support_points(build, act):
    levels, subs, _, _ = _classes(build, act)
    gear = set(equipment_at(build, act).values())
    points, why = 0, []
    if levels.get("cleric") or levels.get("druid"):
        points += 30 + 3 * min(levels.get("cleric", 0) + levels.get("druid", 0), 10)
        why.append("healing and Bless/Aid")
    if levels.get("bard"):
        points += 25
        why.append("Bardic Inspiration, healing")
    if levels.get("paladin", 0) >= 6:
        points += 25
        why.append("Aura of Protection")
    elif levels.get("paladin"):
        points += 10
        why.append("Lay on Hands")
    if levels.get("wizard", 0) >= 5 or levels.get("sorcerer", 0) >= 5:
        points += 15
        why.append("Haste")
    if any(b.key in ("bless", "phalar_sing", "haste") for b in buffs_at(build, act)):
        points += 5
    for key, value in SUPPORT_ITEMS.items():
        if key in gear:
            points += value
            why.append(key.split(":")[1].replace("_", " "))
    return min(points, 100), why

def utility_points(build, act):
    levels, subs, _, _ = _classes(build, act)
    gear = set(equipment_at(build, act).values())
    character = compile_build(build, act)
    points, why = 0, []
    if character.charisma >= 16:
        points += 30
        why.append(f"party face (CHA {character.charisma})")
    if levels.get("rogue"):
        points += 30
        why.append("locks, traps, Expertise")
    elif levels.get("bard", 0) >= 2:
        points += 20
        why.append("Jack of All Trades")
    if levels.get("wizard"):
        points += 15
        why.append("rituals and scrolls")
    if levels.get("warlock", 0) >= 2 or subs.get("sorcerer") == "Shadow Magic":
        points += 10
        why.append("sees in magical darkness")
    if levels.get("ranger") or levels.get("monk"):
        points += 10
        why.append("mobility and survival")
    for key, value in UTILITY_ITEMS.items():
        if key in gear:
            points += value
            why.append(key.split(":")[1].replace("_", " "))
    return min(points, 100), why

def score(build, act, enemy, rounds_per_fight=3, attack_bonus=6, weights=None):
    """ The all round score of a build at an act against an enemy """
    act = str(act)
    weights = weights or WEIGHTS
    character = compile_build(build, act)
    single = expected_damage_vs_enemies(character, enemy, rounds_per_fight, 1)
    group = expected_damage_vs_enemies(character, enemy, rounds_per_fight, 3)
    ac, _ = armour_class(build, act)
    hp = hit_points(build, act)
    ehp = hp / hit_chance(ac, attack_bonus)
    control, control_why = control_points(build, act)
    support, support_why = support_points(build, act)
    utility, utility_why = utility_points(build, act)
    parts = {"damage": _scaled(single, DAMAGE_REF[act]), "aoe": _scaled(group - single, AOE_REF[act]), "defence": _scaled(ehp, EHP_REF[act]),
             "control": control, "support": support, "utility": utility}
    notes = {"damage": f"{single:.1f} per round", "aoe": f"+{group - single:.1f} against 3 enemies",
             "defence": f"{hp} HP, AC {ac}: hit {hit_chance(ac, attack_bonus):.0%} -> {ehp:.0f} effective HP",
             "control": ", ".join(control_why) or "none", "support": ", ".join(support_why) or "none", "utility": ", ".join(utility_why) or "none"}
    total = sum(parts[k] * w for k, w in weights.items()) / sum(weights.values())
    return Score(round(total, 1), {k: round(v) for k, v in parts.items()}, notes)
