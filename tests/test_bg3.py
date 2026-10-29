""" BG3 builds: gear per act compiles to the right character, and party conflicts are found.
    The items here are made up for testing, real item data comes from bg3/data/items.json """
from dataclasses import replace

import pytest

from bg3.build import Bg3Build, compile_build, equipment_at
from bg3.items import Effect, Item, catalog, condition_id
from bg3.party import build_conflicts, conflicting_items, party_conflicts
from computations.analytic import expected_damage_per_round
from computations.models import Enemy
from game_data.classes import build_character

GREATSWORD = catalog()["base:greatsword"].weapon
ITEMS = {
    **catalog(),
    "test:flame_sword": Item("test:flame_sword", "Test Flame Sword", "weapon", act=1,
                             weapon={**GREATSWORD, "enhancement": 1}, effects=[Effect("extra_damage", "1d4 fire", applies_to="self")]),
    "test:acid_ring": Item("test:acid_ring", "Test Acid Ring", "ring", act=1, effects=[Effect("extra_damage", "2 acid", applies_to="weapon")]),
    "test:giant_gloves": Item("test:giant_gloves", "Test Giant Gloves", "gloves", act=2, effects=[Effect("ability_min", 23, stat="strength")]),
    "test:rage_amulet": Item("test:rage_amulet", "Test Rage Amulet", "amulet", act=1,
                             effects=[Effect("damage_bonus", 2, applies_to="melee_weapon", condition="while raging")]),
    "test:keen_helm": Item("test:keen_helm", "Test Keen Helm", "helmet", act=3, effects=[Effect("crit_range", 1)]),
    "test:shield": Item("test:shield", "Test Shield", "shield", act=1),
}
ENEMY = Enemy(armor_class=15)

def fighter(**kwargs):
    return Bg3Build(name="Lae'zel", preset="fighter_gwm", **kwargs)

def test_no_gear_is_the_preset_at_the_checkpoint_level():
    character = compile_build(fighter(), 1, ITEMS)
    preset = build_character("fighter_gwm", 5, "bg3")
    assert character.level == 5 and [a.damage for a in character.attacks] == [a.damage for a in preset.attacks]
    assert expected_damage_per_round(character, ENEMY) == pytest.approx(expected_damage_per_round(preset, ENEMY))
    assert compile_build(fighter(levels={"2": 7}), 2, ITEMS).level == 7

def test_weapon_and_ring_effects():
    character = compile_build(fighter(equipment={"1": {"melee_main": "test:flame_sword", "ring_1": "test:acid_ring"}}), 1, ITEMS)
    swords = [a for a in character.attacks if a.name.startswith("Test Flame Sword")]
    assert swords and all(a.weapon_enhancement == 1 and a.extra_damage_list == ["1d4 fire", "2 acid"] for a in swords)
    # Fire resistance only halves the fire part
    plain = compile_build(fighter(), 1, ITEMS)
    assert expected_damage_per_round(character, ENEMY) > expected_damage_per_round(plain, ENEMY)
    assert expected_damage_per_round(character, replace(ENEMY, resistances=["fire"])) < expected_damage_per_round(character, ENEMY)

def test_gear_carries_over_and_can_be_cleared():
    build = fighter(equipment={"1": {"ring_1": "test:acid_ring"}, "2": {"gloves": "test:giant_gloves"}, "3": {"ring_1": ""}})
    assert equipment_at(build, 2) == {"ring_1": "test:acid_ring", "gloves": "test:giant_gloves"}
    assert equipment_at(build, 3) == {"gloves": "test:giant_gloves"}
    assert compile_build(build, 2, ITEMS).strength == 23
    assert compile_build(build, 1, ITEMS).strength < 23

def test_conditional_effects_need_their_toggle():
    gear = {"1": {"amulet": "test:rage_amulet"}}
    off = compile_build(fighter(equipment=gear), 1, ITEMS)
    on = compile_build(fighter(equipment=gear, conditions=[condition_id("test:rage_amulet", 0)]), 1, ITEMS)
    assert all("2" not in a.bonus_damage_die_mod_list for a in off.attacks)
    assert all("2" in a.bonus_damage_die_mod_list for a in on.attacks if a.type == "weapon (melee)")

def test_crit_range_stacks_with_champion():
    character = compile_build(fighter(equipment={"3": {"helmet": "test:keen_helm"}}), 3, ITEMS)
    assert all(a.crit_on == 18 for a in character.attacks) # Improved Critical 19, then one lower

def test_buffs():
    plain = compile_build(fighter(), 1, ITEMS)
    hasted = compile_build(fighter(buffs={"1": ["haste", "bless"]}), 1, ITEMS)
    assert len(hasted.attacks) == len(plain.attacks) + 1 and hasted.attacks[-1].name.endswith("(Haste)")
    assert all("1d4" in a.bonus_attack_die_mod_list for a in hasted.attacks)

def test_party_conflicts():
    a = fighter(equipment={"1": {"melee_main": "test:flame_sword", "ring_1": "test:acid_ring", "ring_2": "test:acid_ring"}})
    b = Bg3Build(name="Karlach", preset="barbarian_berserker", equipment={"1": {"melee_main": "test:flame_sword", "melee_off": "test:shield"},
                                                                       "2": {"melee_main": "base:greataxe"}})
    conflicts = party_conflicts([a, b], ITEMS)
    kinds = {(c.act, c.kind, c.item) for c in conflicts}
    assert ("1", "shared", "test:flame_sword") in kinds # Both want the sword in Act 1
    assert ("2", "shared", "test:flame_sword") not in kinds # Karlach switches to a Greataxe in Act 2
    assert ("2", "two_handed", "base:greataxe") in kinds # but still has the shield from Act 1
    assert ("1", "duplicate", "test:acid_ring") in kinds
    assert ("1", "two_handed", "test:flame_sword") in kinds
    assert conflicting_items(conflicts, act=1) == {"test:flame_sword"}
    # Base weapons are not unique, both can use one
    c = Bg3Build(name="Minthara", preset="fighter_gwm", equipment={"1": {"melee_main": "base:greataxe"}})
    assert not [x for x in party_conflicts([b, c], ITEMS, acts=["2"]) if x.kind == "shared"]

def test_build_conflicts_flag_items_from_later_acts():
    build = fighter(equipment={"1": {"helmet": "test:keen_helm", "gloves": "test:acid_ring"}})
    kinds = {c.kind for c in build_conflicts(build, 1, ITEMS)}
    assert {"too_early", "wrong_slot"} <= kinds

def test_build_round_trip():
    build = fighter(equipment={"1": {"ring_1": "test:acid_ring"}}, buffs={"1": ["bless"]}, conditions=["x#0"], levels={"1": 4})
    assert Bg3Build.from_dict(build.to_dict()) == build
