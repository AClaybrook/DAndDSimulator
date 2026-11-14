""" Item kits and build variants.

    A kit is a curated set of items that work together (bg3/data/kits.json, written up in docs/act1_item_kits.md): for each slot, item options
    best first. Applying a kit only fills ordinary gear cells, so every slot stays editable afterwards and slots the kit doesn't cover are kept.

    A variant is a named "what if" on a build: a kit, extra buffs and toggles layered over the build's own gear. Variants never change the
    build's gear; they are compiled side by side with it """
import json
from copy import deepcopy
from functools import lru_cache

from bg3.build import ACT_KEYS, Bg3Build, compile_build, equipment_at
from bg3.items import DATA, catalog

@lru_cache(maxsize=1)
def kits():
    """ {kit key: kit} """
    with open(DATA / "kits.json", encoding="utf-8") as f:
        return {k["key"]: k for k in json.load(f)["kits"]}

def taken_by_others(party, member_index, act):
    """ Unique items the other party members have at an act """
    items = catalog()
    taken = set()
    for ii, build in enumerate(party):
        if ii != member_index:
            taken |= {k for k in equipment_at(build, act).values() if k in items and items[k].unique}
    return taken

def kit_gear(kit_key, taken=(), current=None):
    """ The kit's choice per slot: the first option nobody else has, and the slots where every option is taken.
        A ring the kit puts in one ring slot isn't used again in the other """
    kit = kits()[kit_key]
    taken = set(taken)
    chosen, blocked = {}, []
    for slot, options in kit["slots"].items():
        pick = next((k for k in options if k not in taken and k not in chosen.values()), None)
        if pick is None:
            blocked.append(slot)
        else:
            chosen[slot] = pick
    if current is not None:
        # Don't put a ring in both ring slots when the build already wears it in the other one
        for slot, other in (("ring_1", "ring_2"), ("ring_2", "ring_1")):
            if slot in chosen and current.get(other) == chosen[slot] and other not in chosen:
                del chosen[slot]
    return chosen, blocked

def kit_conditions(kit_key):
    """ Condition ids of the kit's conditional item effects: a kit is used the way it's meant to, so they count as set up """
    from bg3.items import condition_id # pylint: disable=import-outside-toplevel
    items = catalog()
    keys = {k for options in kits()[kit_key]["slots"].values() for k in options}
    return [condition_id(k, ii) for k in keys if k in items for ii, e in enumerate(items[k].effects) if e.condition]

def apply_kit(build, kit_key, act, taken=(), only_empty=False):
    """ A copy of the build with the kit's items in its gear cells at an act. only_empty keeps every slot that already has an item there
        (set at that act or carried over from an earlier act). Returns (build, {slot: item key} placed, slots where every option was taken) """
    act = str(act)
    build = deepcopy(build)
    current = equipment_at(build, act)
    chosen, blocked = kit_gear(kit_key, taken, current)
    if only_empty:
        chosen = {slot: key for slot, key in chosen.items() if not current.get(slot)}
    build.equipment = {**build.equipment, act: {**build.equipment.get(act, {}), **chosen}}
    # The kit's buffs (Mage Armour for the unarmoured kit, Hill Giant Strength for throwing), ticked at that act and still editable
    if kits()[kit_key].get("buffs"):
        build.buffs = {**build.buffs, act: list(dict.fromkeys([*build.buffs.get(act, []), *kits()[kit_key]["buffs"]]))}
    placed = {f"{k}#" for k in chosen.values()}
    build.conditions = list(dict.fromkeys([*build.conditions, *(c for c in kit_conditions(kit_key) if c.split("#")[0] + "#" in placed)]))
    return build, chosen, blocked

# ---------- Variants

QUICK_VARIANTS = {
    "bless": {"name": "Bless", "buffs": ["bless"]},
    "haste": {"name": "Haste", "buffs": ["haste"]},
    "bless_haste": {"name": "Bless + Haste", "buffs": ["bless", "haste"]},
    "advantage": {"name": "With advantage", "toggles": {"advantage": True}},
    "all_in": {"name": "Bless + Haste + advantage", "buffs": ["bless", "haste"], "toggles": {"advantage": True}},
}

def variant_build(build, variant):
    """ The build with a variant layered on: its kit at the kit's act (before later acts' own gear), extra buffs in every act, toggles for
        custom characters. The build itself is unchanged """
    out = deepcopy(build)
    out.name = f"{build.name}: {variant.get('name') or 'variant'}"
    if variant.get("kit") in kits():
        kit_act = str(variant.get("act") or kits()[variant["kit"]]["act"])
        out, _, _ = apply_kit(out, variant["kit"], kit_act)
    # Gear of its own (i.e. a best in slot set to compare): act: slot: item key
    for act, gear in (variant.get("gear") or {}).items():
        out.equipment[str(act)] = {**out.equipment.get(str(act), {}), **gear}
    # Another way to play the same character (a different spell or cantrip, a routine): fields of the custom character
    if variant.get("character") and out.character:
        out.character = {**out.character, **variant["character"]}
    extra = list(variant.get("buffs") or [])
    if extra:
        from bg3.buffs import BUFFS # pylint: disable=import-outside-toplevel
        # A variant's elixir replaces the build's (only one elixir is active at a time)
        def available(b, act):
            return b not in BUFFS or int(BUFFS[b].act or 1) <= int(act)
        # Each act gets the buffs it can have by then (Cloud Giant Strength only in Act 3)
        added = {act: [b for b in extra if available(b, act)] for act in ACT_KEYS}
        def kind(b):
            """ Buffs of a kind replace each other: elixirs, coatings """
            return "elixir" if b in BUFFS and BUFFS[b].exclusive else (BUFFS[b].group if b in BUFFS else "") or None
        swap = {act: {kind(b) for b in added[act]} - {None} for act in ACT_KEYS}
        kept = {act: [b for b in out.buffs.get(act, []) if kind(b) not in swap[act]] for act in ACT_KEYS}
        out.buffs = {act: list(dict.fromkeys([*kept[act], *added[act]])) for act in ACT_KEYS}
    if variant.get("toggles"):
        if out.character:
            out.character = {**out.character, "toggles": {**out.character.get("toggles", {}), **variant["toggles"]}}
        elif variant["toggles"].get("advantage"):
            out.advantage = True
    out.conditions = list(dict.fromkeys([*out.conditions, *(variant.get("conditions") or [])]))
    return out

def describe_variant(variant):
    parts = []
    if variant.get("kit") in kits():
        parts.append(f"kit: {kits()[variant['kit']]['name']}")
    if variant.get("character"):
        parts.append("plays " + ", ".join(str(v) for v in variant["character"].values() if v))
    if (variant.get("toggles") or {}).get("spirit_guardians"):
        parts.append("after Spirit Guardians")
    if variant.get("gear"):
        parts.append("gear: " + ", ".join(f"Act {act} ({len(gear)} slots)" for act, gear in sorted(variant["gear"].items())))
    if variant.get("buffs"):
        from bg3.buffs import BUFFS # pylint: disable=import-outside-toplevel
        parts.append("buffs: " + ", ".join(BUFFS[b].name if b in BUFFS else b for b in variant["buffs"]))
    if (variant.get("toggles") or {}).get("advantage"):
        parts.append("advantage")
    return "; ".join(parts) or "same as the build"

def variant_builds(build):
    """ [(name, description, build)] for the build and each of its variants """
    return [("Build as planned", "its own gear and buffs", build),
            *((v.get("name") or "Variant", describe_variant(v), variant_build(build, v)) for v in build.variants)]

def variant_damage(build, enemy, rounds_per_fight, enemies=1):
    """ [(name, description, [damage per round per act], build)] for the build and each of its variants, against a group of enemies """
    from computations.analytic import expected_damage_vs_enemies # pylint: disable=import-outside-toplevel
    return [(name, description, [expected_damage_vs_enemies(compile_build(b, act), enemy, rounds_per_fight, enemies) for act in ACT_KEYS], b)
            for name, description, b in variant_builds(build)]

__all__ = ["kits", "kit_gear", "apply_kit", "taken_by_others", "variant_build", "variant_builds", "variant_damage", "describe_variant", "QUICK_VARIANTS", "Bg3Build"]
