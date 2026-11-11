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
    return routine in ("one_handed", "shadow_blade", "shadow_blade_shield", "cantrip") and not equipment_at(build, act).get("melee_off")

def weapon_slot(build, act, items=None):
    """ (slot, test) for the weapon a build attacks with at an act: the slot its main attack uses and which weapons can stand in for
        the planned one (the same grip, so the build's routine and feats still apply), or (None, None) for unarmed, thrown and conjured
        weapons. Casters get the main hand for a staff """
    from bg3.build import compile_build # pylint: disable=import-outside-toplevel
    from bg3.character import POLEARMS # pylint: disable=import-outside-toplevel
    character = compile_build(build, act, items)
    main = next((a for a in character.attacks if a.is_weapon and not a.offhand), None)
    routine = (build.character or {}).get("routine", "") if build.character else ""
    if main is None:
        if any(a.type == "unarmed" for a in character.attacks):
            return None, None
        return "melee_main", lambda w: w.get("kind") != "ranged" # A caster's staff or blade, for its spell bonuses
    if "conjured" in main.tags or main.type == "thrown":
        return None, None
    def props(w):
        return w.get("properties") or []
    if main.type == "weapon (ranged)":
        hand = routine == "dual_hand_crossbows"
        return "ranged_main", lambda w: w.get("kind") == "ranged" and (w.get("base") == "Hand Crossbow") == hand
    if routine == "polearm":
        return "melee_main", lambda w: w.get("kind") != "ranged" and w.get("base") in POLEARMS and ("two-handed" in props(w) or "versatile" in props(w))
    if main.two_handed:
        return "melee_main", lambda w: w.get("kind") != "ranged" and ("two-handed" in props(w) or "versatile" in props(w))
    dual = any(a.is_weapon and a.offhand for a in character.attacks) and "Dual Wielder" not in ((build.character or {}).get("feats") or [])
    return "melee_main", lambda w: w.get("kind") != "ranged" and "two-handed" not in props(w) and (not dual or "light" in props(w))

# Weapons only one companion can get (Wyll's pact reward)
COMPANION_ONLY = {"bg3:infernal_rapier"}

def weapon_candidates(build, act, items=None):
    """ (slot, [weapons found by the act that fit the build's grip and that it is proficient with]) """
    from bg3.character import is_proficient, weapon_proficiencies # pylint: disable=import-outside-toplevel
    items = items or catalog()
    slot, fits = weapon_slot(build, act, items)
    if slot is None:
        return None, []
    profs = weapon_proficiencies(Bg3Character.from_dict(build.character), act_level(act, build.levels)) if build.character else None
    return slot, [i for i in items.values() if i.weapon and i.fits(slot) and (i.act or 3) <= int(act) and fits(i.weapon)
                  and i.key not in COMPANION_ONLY and (profs is None or is_proficient(i.weapon.get("base"), profs))]

PARTLY_COUNTED_GAIN = 0.10 # Share of the objective needed to replace a worn item only some of whose effects are counted

def optimise(build, act, objective, items=None, exclude=(), weapons=False, min_gain=0.0, guard=None, kept=None):
    """ The gear (slot: item key, '' for empty) that maximises objective(build) at an act, one slot at a time.
        exclude: unique items not to pick (worn by the rest of the party). weapons: also choose the main weapon, first, since the rest
        of the gear builds on it. min_gain: the share of the objective an item must add to replace one the build already wears (its
        unmodelled effects are worth something; empty slots take any gain). guard(build): a value a swap may not lower, i.e. armour
        class when searching for damage. kept: a dict to fill; when given, a worn item with effects the damage doesn't count (its notes)
        is harder to replace, since the numbers undersell it: never when none of its effects are counted, and only for PARTLY_COUNTED_GAIN
        when some are. kept[slot] = (its key, the item the numbers preferred, the gain they saw) for the ones that stayed """
    items = items or catalog()
    gear = {slot: equipment_at(build, act).get(slot, "") for slot in GEAR_SLOTS}
    slots = list(GEAR_SLOTS) + (["melee_off"] if shield_slot_free(build, act) else [])
    if "melee_off" in slots:
        gear["melee_off"] = ""
    pools = {}
    if weapons:
        slot, pool = weapon_candidates(build, act, items)
        if slot:
            gear = {slot: equipment_at(build, act).get(slot, ""), **gear}
            slots, pools[slot] = [slot, *slots], pool
    best = objective(with_gear(build, act, gear))
    planned = dict(gear)
    floor = guard(with_gear(build, act, gear)) if guard else None
    for slot in slots:
        taken = {gear.get(s) for s in ("ring_1", "ring_2") if s != slot} if slot.startswith("ring") else set()
        for item in pools.get(slot) or candidates(build, act, slot, items):
            if item.key in taken or item.key == gear.get(slot) or (item.unique and item.key in exclude):
                continue
            trial = {**gear, slot: item.key}
            worn = with_gear(build, act, trial)
            value = objective(worn)
            needed = abs(best) * min_gain if planned.get(slot) and gear.get(slot) == planned[slot] else 0
            if value > best + max(needed, 1e-6) and (guard is None or guard(worn) >= floor):
                worn_item = items.get(gear.get(slot))
                if kept is not None and worn_item is not None and worn_item.notes and gear.get(slot) == planned.get(slot):
                    counted = worn_item.effects or worn_item.weapon
                    if not counted or value - best < abs(best) * PARTLY_COUNTED_GAIN:
                        if slot not in kept or value - best > kept[slot][2]:
                            kept[slot] = (worn_item.key, item.key, value - best)
                        continue
                    kept.pop(slot, None)
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
