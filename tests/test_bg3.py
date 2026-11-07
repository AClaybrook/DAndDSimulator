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

def test_wiki_template_parsing():
    from bg3.scrape_wiki import plain_text, template_params
    text = "Intro {{WeaponPage\n| name = Test Blade\n| damage = 1d8\n| special = Deals {{DamageText|1d4|Fire}} on [[hit|hits]] |rarity=Rare}} outro"
    params = template_params(text, "WeaponPage")
    assert params["name"] == "Test Blade" and params["rarity"] == "Rare"
    assert plain_text(params["special"]) == "Deals 1d4 Fire on hits"

# Patch 8 item data exported from bg3.wiki
def test_item_data_has_key_items():
    items = catalog()
    everburn, caustic = items["bg3:everburn_blade"], items["bg3:caustic_band"]
    assert everburn.act == 1 and everburn.weapon["damage"] == "2d6" and "two-handed" in everburn.weapon["properties"]
    assert [e.value for e in everburn.effects if e.kind == "extra_damage"] == ["1d4 fire"]
    assert caustic.slot == "ring" and caustic.unique and [(e.kind, e.value, e.applies_to) for e in caustic.effects] == [("extra_damage", "2 acid", "weapon")]
    gauntlets = items["bg3:gauntlets_of_hill_giant_strength"]
    assert gauntlets.act == 3 and [(e.kind, e.stat, e.value) for e in gauntlets.effects] == [("ability_min", "strength", 23)]
    assert [(e.kind, e.stat) for e in items["bg3:titanstring_bow"].effects] == [("damage_bonus_ability", "strength")]
    assert items["bg3:selune_s_spear_of_night"].act == 2
    assert all(i.source.startswith("https://bg3.wiki/") for i in items.values() if i.key.startswith("bg3:"))

def test_effect_parsing():
    from bg3.build_items import parse_effects
    effects, _ = parse_effects(["Your weapon attacks also deal 2 Acid damage."])
    assert effects == [{"kind": "extra_damage", "value": "2 acid", "applies_to": "weapon"}]
    effects, _ = parse_effects(["When Concentrating on a spell, the wearer's weapon attacks deal an additional 1d4 Psychic damage."])
    assert effects[0]["kind"] == "extra_damage" and effects[0]["condition"]
    # Damage dealt back to attackers doesn't count
    effects, notes = parse_effects(["Undead creatures that hit the wearer receive 1d6 Radiant damage."])
    assert not effects and notes
    effects, _ = parse_effects(["This weapon deals additional damage equal to your Strength Modifier."], own_weapon=True)
    assert effects == [{"kind": "damage_bonus_ability", "stat": "strength", "applies_to": "self"}]
    effects, _ = parse_effects(["You gain Advantage on Attack Rolls and receive Disadvantage on SavingThrows."])
    assert effects == [{"kind": "advantage", "applies_to": "all"}]

def test_real_build_damage_goes_up_with_gear():
    plain = compile_build(fighter(), 1)
    geared = compile_build(fighter(equipment={"1": {"melee_main": "bg3:everburn_blade", "ring_1": "bg3:caustic_band"}}), 1)
    assert expected_damage_per_round(geared, ENEMY) > expected_damage_per_round(plain, ENEMY)
    giant = compile_build(fighter(equipment={"3": {"gloves": "bg3:gauntlets_of_hill_giant_strength"}}), 3)
    assert giant.strength == 23

def test_presets_use_real_items_in_the_right_slots():
    from bg3.presets import DEFAULT_PARTY, PRESETS
    items = catalog()
    for build in PRESETS.values():
        for act in ("1", "2", "3"):
            assert not [c for c in build_conflicts(build, act) if c.kind != "shared"], build.name
        assert all(key in items for gear in build.equipment.values() for key in gear.values())
    # The default party shares Caustic Band, to show the conflict report, and makes no conflicting story choices
    conflicts = party_conflicts([PRESETS[n] for n in DEFAULT_PARTY])
    assert any(c.kind == "shared" and c.item == "bg3:caustic_band" for c in conflicts)
    assert not [c for c in conflicts if c.kind == "story"]
    assert not [c for c in party_conflicts(list(PRESETS.values())) if c.kind == "story"]

def test_story_choices():
    from bg3.analysis import slot_suggestions
    from bg3.party import story_choices
    items = catalog()
    assert all(k in items for choice in story_choices() for keys in choice["paths"].values() for k in keys)
    spared = Bg3Build("Lae'zel", "fighter_gwm", equipment={"2": {"melee_main": "bg3:moonlight_glaive"}})
    killed = Bg3Build("Shadowheart", "fighter_gwm", equipment={"2": {"gloves": "bg3:dark_justiciar_gauntlets_rare"}})
    conflicts = [c for c in party_conflicts([spared, killed]) if c.kind == "story"]
    assert [c.act for c in conflicts] == ["2", "3"] and conflicts[0].members == ["Lae'zel", "Shadowheart"]
    assert set(conflicts[0].items) == {"bg3:moonlight_glaive", "bg3:dark_justiciar_gauntlets_rare"}
    assert "Moonlight Glaive on Lae'zel" in conflicts[0].message
    assert conflicting_items(conflicts, act=2) == {"bg3:moonlight_glaive", "bg3:dark_justiciar_gauntlets_rare"}
    # Items from the same outcome are fine, and one character can make the conflict alone
    assert not [c for c in party_conflicts([spared, replace(killed, equipment={"2": {"melee_main": "bg3:selune_s_spear_of_night"}})]) if c.kind == "story"]
    alone = replace(spared, equipment={"2": {**spared.equipment["2"], "gloves": "bg3:dark_justiciar_gauntlets_rare"}})
    assert [c.act for c in party_conflicts([alone]) if c.kind == "story"] == ["2", "3"]
    # Gear suggestions name the clash
    gloves = {i.key: users for i, _, users in slot_suggestions(spared, 2, "gloves", ENEMY, 3, party=[spared])}
    assert gloves["bg3:dark_justiciar_gauntlets_rare"] == ["Moonlight Glaive on Lae'zel (other story outcome)"]
    assert gloves["bg3:dark_justiciar_gauntlets_uncommon"] == []

def test_gear_advice():
    from bg3.analysis import item_values, shared_item_gains, slot_suggestions
    build = fighter(equipment={"1": {"melee_main": "test:flame_sword", "ring_1": "test:acid_ring"}})
    values = {item.key: gain for _, item, gain in item_values(build, 1, ENEMY, 3, ITEMS)}
    # Each item's value is the damage lost without it
    full = expected_damage_per_round(compile_build(build, 1, ITEMS), ENEMY, 3)
    without_ring = expected_damage_per_round(compile_build(fighter(equipment={"1": {"melee_main": "test:flame_sword"}}), 1, ITEMS), ENEMY, 3)
    assert values["test:acid_ring"] == pytest.approx(full - without_ring) and values["test:acid_ring"] > 0
    # Suggestions only use items found by the act, best first, and say who else uses them
    other = Bg3Build(name="Karlach", preset="barbarian_berserker", equipment={"1": {"ring_1": "test:acid_ring"}})
    rings = slot_suggestions(fighter(), 1, "ring_1", ENEMY, 3, ITEMS, party=[fighter(), other])
    acid = next(r for r in rings if r[0].key == "test:acid_ring")
    assert acid[2] == ["Karlach"] and acid[1] == pytest.approx(rings[0][1]) # Ties with Caustic Band, the real ring it copies
    gains = [g for _, g, _ in rings]
    assert gains == sorted(gains, reverse=True)
    assert not [i for i, _, _ in slot_suggestions(fighter(), 1, "helmet", ENEMY, 3, ITEMS) if i.key == "test:keen_helm"] # Act 3 item
    conflict = next(c for c in party_conflicts([build, other], ITEMS) if c.kind == "shared" and c.act == "1")
    assert set(shared_item_gains([build, other], conflict, ENEMY, 3, ITEMS)) == {"Lae'zel", "Karlach"}

def test_elixirs():
    from bg3.buffs import BUFFS
    giant, vicious = BUFFS["elixir:elixir_of_hill_giant_strength"], BUFFS["elixir:elixir_of_viciousness"]
    assert giant.exclusive and vicious.exclusive and not BUFFS["elixir:elixir_of_heroism"].exclusive
    character = compile_build(fighter(buffs={"1": [giant.key]}), 1, ITEMS)
    assert character.strength == 21
    assert all(a.crit_on == 18 for a in compile_build(fighter(buffs={"1": [vicious.key]}), 1, ITEMS).attacks) # Champion 19, then one lower
    both = fighter(buffs={"1": [giant.key, vicious.key]})
    assert [c.kind for c in build_conflicts(both, 1, ITEMS)] == ["elixirs"]

def test_concentration():
    from bg3.party import concentration_conflicts
    def member(name, *buffs):
        return Bg3Build(name=name, preset="fighter_gwm", buffs={"1": list(buffs)})
    # One Bless covers three characters, Haste needs a caster each
    assert not concentration_conflicts([member("A", "bless"), member("B", "bless"), member("C", "bless"), member("D")], 1)
    assert not concentration_conflicts([member("A", "haste"), member("B", "haste"), member("C"), member("D")], 1)
    # Four Hastes and a Bless need five casters
    assert concentration_conflicts([member(n, "haste", "bless") for n in "ABCD"], 1)
    # A warlock keeping Hex up can't also cast Haste, B is free to cast Haste on themselves but not also Bless
    assert not concentration_conflicts([member("A", "hex"), member("B", "haste")], 1)
    assert concentration_conflicts([member("A", "hex"), member("B", "haste", "bless")], 1)
    assert [c.kind for c in build_conflicts(member("A", "hex", "divine_favour"), 1, ITEMS)] == ["concentration"]

def test_tenacity_crit_and_sneak_attack_item_effects():
    items = catalog()
    assert [(e.kind, e.stat) for e in items["bg3:defender_flail"].effects] == [("miss_damage_ability", "strength")]
    assert [(e.kind, e.value) for e in items["bg3:craterflesh_gloves"].effects] == [("crit_damage", "1d6")]
    tenacity = compile_build(fighter(equipment={"1": {"melee_main": "bg3:doom_hammer"}}), 1)
    assert all(a.bonus_miss_die_mod_list == ["3"] for a in tenacity.attacks) # Strength 17 at level 5 -> +3 on a miss
    # Stalker Gloves only add to Sneak Attack, so a fighter gains nothing and a rogue gains on the first hit
    gloves = {"1": {"gloves": "bg3:stalker_gloves"}}
    assert not compile_build(fighter(equipment=gloves), 1).once_per_turn_die_mod_list
    rogue = compile_build(Bg3Build("Astarion", "rogue_assassin", equipment=gloves), 1)
    assert rogue.once_per_turn_die_mod_list[-1] == "1d4"

def test_point_buy():
    from bg3.abilities import apply_improvement, point_buy_cost, point_buy_problems, starting_scores
    scores = {"strength": 15, "dexterity": 14, "constitution": 15, "intelligence": 8, "wisdom": 10, "charisma": 8}
    assert point_buy_cost(scores) == 27 and not point_buy_problems(scores, {"strength": 2, "constitution": 1})
    assert point_buy_problems({**scores, "wisdom": 12}, {}) # 29 points
    assert point_buy_problems({**scores, "strength": 16}, {})
    assert point_buy_problems(scores, {"strength": 2, "dexterity": 2})
    start = starting_scores(scores, {"strength": 2, "constitution": 1})
    assert start["strength"] == 17 and start["constitution"] == 16
    assert apply_improvement(start, "strength+2")["strength"] == 19
    assert apply_improvement({**start, "strength": 19}, "strength+2")["strength"] == 20
    assert apply_improvement(start, "strength+1,constitution+1")["constitution"] == 17

def test_lightning_charges():
    rogue = Bg3Build("Astarion", "rogue_dual_wield", equipment={"1": {"melee_main": "bg3:the_sparky_points"}})
    character = compile_build(rogue, 1)
    assert all(a.extra_damage_list.count("1 lightning") == 1 and "1" in a.bonus_attack_die_mod_list for a in character.attacks)
    # A second source doesn't stack, and the Spellsparkler needs spells to gain charges
    both = replace(rogue, equipment={"1": {**rogue.equipment["1"], "melee_off": "bg3:the_sparky_points", "gloves": "bg3:the_sparkle_hands"}})
    assert all(a.extra_damage_list.count("1 lightning") == 1 for a in compile_build(both, 1).attacks)
    fighter_ = Bg3Build("Lae'zel", "fighter_gwm", equipment={"1": {"melee_main": "bg3:the_spellsparkler"}})
    assert not any("1 lightning" in a.extra_damage_list for a in compile_build(fighter_, 1).attacks)
    wizard = Bg3Build("Gale", "wizard_fireball", equipment={"1": {"melee_main": "bg3:the_spellsparkler"}})
    assert all("1 lightning" in a.extra_damage_list for a in compile_build(wizard, 1).attacks if a.type == "spell")
    assert expected_damage_per_round(character, ENEMY, 3) > expected_damage_per_round(compile_build(replace(rogue, equipment={}), 1), ENEMY, 3)
