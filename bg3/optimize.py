""" Gear variants found by search: for a build at an act, the armour, accessories and shield that maximise damage, armour class or the
    overall score. Weapons stay as planned (they decide the build's routine).

    Greedy, one slot at a time, starting from the planned gear, so each pick sees the ones before it. Only items with a modelled effect or an
    armour class value are tried, items of an unknown act only in Act 3, and armour the character can't wear (BG3 proficiencies, monks and
    Bladesong) is skipped """
from copy import deepcopy

from bg3.build import ACT_KEYS, equipment_at
from bg3.character import Bg3Character, class_levels, class_order, subclass_of
from bg3.checkpoints import act_level
from bg3.defence import armour_class, armour_data
from bg3.items import catalog

GEAR_SLOTS = ["armour", "gloves", "helmet", "amulet", "ring_1", "ring_2", "cloak", "boots"]
# BG3 armour proficiencies: from the first class, and from multiclassing into a class later
FIRST = {"barbarian": {"light", "medium", "shield"}, "bard": {"light"}, "cleric": {"light", "medium", "shield"}, "druid": {"light", "medium", "shield"},
         "fighter": {"light", "medium", "heavy", "shield"}, "monk": set(), "paladin": {"light", "medium", "heavy", "shield"},
         "ranger": {"light", "medium", "shield"}, "rogue": {"light"}, "sorcerer": set(), "warlock": {"light"}, "wizard": set()}
LATER = {**FIRST, "fighter": {"light", "medium", "shield"}, "paladin": {"light", "medium", "shield"}}
HEAVY_DOMAINS = {"Life Domain", "Nature Domain", "Tempest Domain", "War Domain", "Knowledge Domain"}
ARMOUR_FEATS = {"Lightly Armoured": {"light"}, "Moderately Armoured": {"light", "medium", "shield"}, "Heavily Armoured": {"heavy"}}
VARIANTS = {
    "planned": "Planned gear",
    "max_damage": "Max damage gear",
    "max_ac": "Max AC gear",
    "best_score": "Best overall score gear",
}

def _levels(build, act):
    level = act_level(act, build.levels)
    if build.character:
        character = Bg3Character.from_dict(build.character)
        levels = class_levels(character, level)
        return character, levels, {cls: subclass_of(character, cls, n) for cls, n in levels.items()}
    cls = build.preset.split("_")[0]
    return None, {cls: level}, {}

def proficiencies(build, act):
    """ The armour types (light, medium, heavy, shield) a build can wear at an act. Monks fighting unarmed and Bladesingers wear none,
        their own defence is better and armour switches it off """
    character, levels, subs = _levels(build, act)
    if character is None:
        return set(FIRST.get(next(iter(levels)), set()))
    order = class_order(character, act_level(act, build.levels))
    kinds = set(FIRST.get(order[0], set())) if order else set()
    for cls in levels:
        if cls != (order[0] if order else None):
            kinds |= LATER.get(cls, set())
    if subs.get("cleric") in HEAVY_DOMAINS:
        kinds |= {"heavy"}
    for feat, extra in ARMOUR_FEATS.items():
        if feat in character.feats:
            kinds |= extra
    if character.routine == "unarmed" or subs.get("wizard") == "Bladesinging":
        kinds -= {"medium", "heavy", "shield"}
        if character.routine == "unarmed":
            kinds = set()
    return kinds

def candidates(build, act, slot, items=None):
    """ Items worth trying in a slot: found by the act, with a modelled effect or an armour class value, and wearable """
    items = items or catalog()
    armour = armour_data()
    allowed = proficiencies(build, act)
    out = []
    for item in items.values():
        if not item.fits(slot) or (item.act or 3) > int(act):
            continue
        kind = armour.get(item.key, {}).get("type")
        if slot == "armour" and kind in ("light", "medium", "heavy") and kind not in allowed:
            continue
        if slot == "melee_off" and kind != "shield":
            continue
        if kind == "shield" and "shield" not in allowed:
            continue
        if item.effects or armour.get(item.key, {}).get("ac") or armour.get(item.key, {}).get("bonus"):
            out.append(item)
    return out

def with_gear(build, act, gear):
    """ A copy wearing exactly this gear at the act (later acts still change from it as planned) """
    out = deepcopy(build)
    out.equipment[str(act)] = {**out.equipment.get(str(act), {}), **{slot: key for slot, key in gear.items()}}
    return out

def shield_slot_free(build, act):
    """ A shield fits when the build fights one handed with nothing in the off hand """
    routine = (build.character or {}).get("routine") if build.character else ("one_handed" if "smite" in build.preset else "")
    return routine in ("one_handed", "shadow_blade", "cantrip") and not equipment_at(build, act).get("melee_off")

def optimise(build, act, objective, items=None):
    """ The gear (slot: item key, '' for empty) that maximises objective(build) at an act, one slot at a time """
    items = items or catalog()
    gear = {slot: equipment_at(build, act).get(slot, "") for slot in GEAR_SLOTS}
    slots = list(GEAR_SLOTS) + (["melee_off"] if shield_slot_free(build, act) else [])
    if "melee_off" in slots:
        gear["melee_off"] = ""
    best = objective(with_gear(build, act, gear))
    for slot in slots:
        taken = {gear.get(s) for s in ("ring_1", "ring_2") if s != slot} if slot.startswith("ring") else set()
        for item in candidates(build, act, slot, items):
            if item.key in taken or item.key == gear.get(slot):
                continue
            trial = {**gear, slot: item.key}
            value = objective(with_gear(build, act, trial))
            if value > best + 1e-6:
                best, gear = value, trial
    return {slot: key for slot, key in gear.items() if key or slot in equipment_at(build, act)}

def variant(build, kind, objective_for_act):
    """ The build with the variant's gear in every act. objective_for_act(act) gives the function to maximise """
    out = deepcopy(build)
    out.variants = []
    if kind == "planned":
        return out
    for act in ACT_KEYS:
        gear = optimise(out, act, objective_for_act(act))
        out.equipment[act] = {**out.equipment.get(act, {}), **gear}
    return out

def ac_objective(act, damage_of):
    """ Armour class first, damage to break ties """
    return lambda b: armour_class(b, act)[0] * 1000 + damage_of(b)
