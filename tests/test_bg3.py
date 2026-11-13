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
    # BG3 adds Great Weapon Master's bonus attack after a crit or a kill
    bonus = [a for a in character.attacks if a.label == "Great Weapon Master"]
    assert len(bonus) == 1 and bonus[0].action == "bonus" and 0 < bonus[0].uses_per_fight < 3
    with_bonus = expected_damage_per_round(character, ENEMY, 3)
    character.attacks = [a for a in character.attacks if a.label != "Great Weapon Master"]
    assert character.level == 5 and [a.damage for a in character.attacks] == [a.damage for a in preset.attacks]
    assert expected_damage_per_round(character, ENEMY) == pytest.approx(expected_damage_per_round(preset, ENEMY))
    assert with_bonus > 1.1 * expected_damage_per_round(preset, ENEMY, 3)
    # Without kills only crits give it; a bonus action attack made every turn (Polearm Master's butt end) is made in the other turns
    from bg3.character import Bg3Character
    no_kills = compile_build(fighter(assumptions={"bloodlust_kills": 0}), 1, ITEMS)
    assert next(a for a in no_kills.attacks if a.label == "Great Weapon Master").uses_per_fight < bonus[0].uses_per_fight
    polearm = compile_build(Bg3Build("P", "", character=Bg3Character(feats=["Great Weapon Master", "Polearm Master"], routine="polearm").to_dict()), 3)
    assert next(a for a in polearm.attacks if a.name == "Polearm Butt End").fallback_for == "Glaive (Great Weapon Master)"
    weapon = compile_build(Bg3Build("W", "fighter_gwm", buffs={"1": ["magic_weapon", "drakethroat"]}), 1)
    plain = build_character("fighter_gwm", 5, "bg3")
    assert weapon.attacks[0].bonus_attack_die_mod_list != plain.attacks[0].bonus_attack_die_mod_list and any("lightning" in str(x) for x in weapon.attacks[0].extra_damage_list)
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
    # Haste is another action: a whole Attack action outside Honour Mode (2 attacks at level 5), one attack in it
    extra = [a for a in hasted.attacks if a.label == "Haste"]
    assert len(hasted.attacks) == len(plain.attacks) + 2 and len(extra) == 2 and all(a.action == "extra" and not a.uses_per_fight for a in extra)
    assert all("1d4" in a.bonus_attack_die_mod_list for a in hasted.attacks)
    from bg3.character import Bg3Character
    custom = Bg3Character(classes=[["fighter", "Champion", 12]]).to_dict()
    def hastes(toggles):
        build = Bg3Build(name="Tav", preset="", character={**custom, "toggles": toggles}, buffs={"3": ["haste"]})
        return sum(a.label == "Haste" for a in compile_build(build, 3, ITEMS).attacks)
    assert hastes({}) == 3 and hastes({"honour_mode": True}) == 1 # Fighter 12: three attacks an action

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
    # Every elixir replaces the one before (Heroism's attack bonus too, bg3.wiki); Viciousness is in trader stock from level 6 (Act 2)
    assert giant.exclusive and vicious.exclusive and BUFFS["elixir:elixir_of_heroism"].exclusive
    assert (giant.act, vicious.act, BUFFS["elixir:elixir_of_cloud_giant_strength"].act) == (1, 2, 2)
    character = compile_build(fighter(buffs={"1": [giant.key]}), 1, ITEMS)
    assert character.strength == 21
    assert all(a.crit_on == 18 for a in compile_build(fighter(buffs={"1": [vicious.key]}), 1, ITEMS).attacks) # Champion 19, then one lower
    both = fighter(buffs={"1": [giant.key, vicious.key]})
    assert [c.kind for c in build_conflicts(both, 1, ITEMS)] == ["elixirs"]

def test_bloodlust_adds_an_attack_action_on_kills():
    """ Elixir of Bloodlust: an extra Attack action (Extra Attack included) on about half the turns against a group """
    from bg3.items import BLOODLUST_KILLS_PER_FIGHT
    character = compile_build(fighter(buffs={"1": ["elixir:elixir_of_bloodlust"]}), 1, ITEMS)
    extra = [a for a in character.attacks if "(Bloodlust)" in a.name]
    plain = [a for a in character.attacks if not a.uses_per_fight and not a.fallback_for and not a.offhand]
    assert extra and len(extra) <= len(plain) and all(a.uses_per_fight == BLOODLUST_KILLS_PER_FIGHT for a in extra)

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

def test_necromancy_staff_and_amulet_of_the_devout():
    """ bg3.wiki: Staff of Cherished Necromancy gives enemies disadvantage on saves against necromancy spells, and a free necromancy
        cast after a kill (Life Essence); Amulet of the Devout +2 spell save DC and one more Channel Divinity charge """
    from bg3.character import Bg3Character
    scores = {"strength": 8, "dexterity": 14, "constitution": 14, "intelligence": 8, "wisdom": 17, "charisma": 10}
    def build(gear, conditions=(), **fields):
        character = Bg3Character(scores=scores, bonus={"wisdom": 2, "constitution": 1}, classes=[["cleric", "Death Domain", 12]], routine="cantrip",
                                 cantrip="Toll the Dead", **fields)
        return Bg3Build(name="Reaper", preset="", character=character.to_dict(), equipment={"3": gear}, conditions=list(conditions))
    staff, amulet = "bg3:staff_of_cherished_necromancy", "bg3:amulet_of_the_devout"
    bare, held = compile_build(build({}), "3"), compile_build(build({"melee_main": staff}), "3")
    toll = next(a for a in held.attacks if a.name == "Toll the Dead")
    assert toll.save_disadvantage and not bare.attacks[0].save_disadvantage
    enemy = Enemy(armor_class=15, wisdom_save=4)
    assert expected_damage_per_round(held, enemy, 3) > expected_damage_per_round(bare, enemy, 3)
    # +2 DC from the amulet
    devout = compile_build(build({"amulet": amulet}), "3")
    assert devout.additional_spell_dc == bare.additional_spell_dc + 2
    assert expected_damage_per_round(devout, enemy, 3) > expected_damage_per_round(bare, enemy, 3)
    # Inflict Wounds: 16 slots a day are 4 casts a fight, 1.5 of them with Touch of Death. The amulet's charge moves a quarter cast over,
    # Life Essence (a condition) adds a cast, and never to the Channel Divinity ones
    def casts(gear, conditions=()):
        by_name = {a.name: a.uses_per_fight for a in compile_build(build(gear, conditions, spell="Inflict Wounds"), "3").attacks}
        return by_name["Inflict Wounds (Touch of Death)"], by_name["Inflict Wounds"]
    assert casts({}) == (1.5, 2.5) and casts({"amulet": amulet}) == (1.75, 2.25)
    assert casts({"melee_main": staff}) == (1.5, 2.5) and casts({"melee_main": staff}, [condition_id(staff, 2)]) == (1.5, 3.5)

def test_arcane_synergy_gwm_in_two_hands_and_saving_throw_bonuses():
    """ bg3.wiki: Arcane Synergy adds the spellcasting ability modifier to weapon attacks; Great Weapon Master: All In works with a
        versatile weapon held in both hands; the Helmet of Arcane Acuity gives +1 to Dexterity saving throws, not Dexterity """
    from bg3.character import Bg3Character
    scores = {"strength": 8, "dexterity": 15, "constitution": 14, "intelligence": 8, "wisdom": 12, "charisma": 15}
    hexblade = Bg3Character(scores=scores, bonus={"charisma": 2, "dexterity": 1}, classes=[["warlock", "The Hexblade", 12]], routine="two_handed",
                            feats=["Great Weapon Master"], toggles={"curse": False, "booming_blade": False})
    ring, phalar = "bg3:ring_of_arcane_synergy", "bg3:phalar_aluve"
    def main_attack(gear, conditions=()):
        build = Bg3Build(name="Hexblade", preset="", character=hexblade.to_dict(), equipment={"3": gear}, conditions=list(conditions))
        return compile_build(build, "3").attacks[0]
    bare = main_attack({"melee_main": phalar})
    assert bare.heavy and bare.damage == "1d10" # A longsword in two hands: All In's -5/+10 applies
    off, on = main_attack({"melee_main": phalar, "ring_1": ring}), main_attack({"melee_main": phalar, "ring_1": ring}, [condition_id(ring, 0)])
    assert off.bonus_damage_die_mod_list == bare.bonus_damage_die_mod_list and on.bonus_damage_die_mod_list == [*bare.bonus_damage_die_mod_list, "3"] # CHA 17
    helmet = catalog()["bg3:helmet_of_arcane_acuity"]
    assert helmet.effects == [] and helmet.notes.startswith("Dexterity saving throws +1")
    assert catalog()["bg3:khalid_s_gift"].effects[0].kind == "ability_bonus" # 'Wisdom +1 (up to 21)' is still an ability bonus

def test_dead_shot_gontr_mael_and_one_hags_hair():
    """ The Dead Shot adds the proficiency bonus twice to its own attack rolls; Gontr Mael's Guiding Bolt is advantage on a share of its
        shots (the same in every engine), with its radiant rider and a part-time Haste; Auntie Ethel's Hair on two members is a conflict """
    from bg3 import doc_import
    from bg3.party import party_conflicts
    doc = {e["build"]["name"]: e["build"] for e in doc_import.load()}
    deadeye = Bg3Build.from_dict(doc["5. Arcane Deadeye"])
    gontr = compile_build(deadeye, "3")
    shot = next(a for a in gontr.attacks if a.name == "Gontr Mael")
    assert shot.advantage_chance == 0.25 and not shot.advantage and "2 radiant" in shot.extra_damage_list
    assert any("Celestial Haste" in a.name and a.uses_per_fight == 0.5 for a in gontr.attacks)
    hasted = compile_build(replace(deadeye, buffs={"3": ["haste"]}), "3")
    assert not any("Celestial Haste" in a.name for a in hasted.attacks) and any("(Haste)" in a.name for a in hasted.attacks)

    dead_shot = compile_build(replace(deadeye, equipment={"3": {"ranged_main": "bg3:the_dead_shot"}}), "3")
    shot = next(a for a in dead_shot.attacks if a.name == "The Dead Shot")
    assert str(dead_shot.proficiency_bonus) in shot.bonus_attack_die_mod_list and shot.crit_on == 19

    # Advantage on a share of the rolls sits between none and always, and the engines agree on it
    from computations.models import Attack, Character
    from tests.test_exact import check
    enemy = Enemy(armor_class=18)
    plain, some, always = (Character(name="a", level=5, dexterity=18, attacks=[Attack(name="Bow", type="weapon (ranged)", ability_stat="dexterity",
                                                                                      damage="1d8", advantage_chance=q, advantage=q == 1)])
                           for q in (0, 0.25, 1))
    low, mid, high = (expected_damage_per_round(c, enemy) for c in (plain, some, always))
    assert low < mid < high and mid == pytest.approx(0.75 * low + 0.25 * high)
    check(some, enemy, 3)
    check(gontr, enemy, 3)

    party = (Bg3Build.from_dict(doc["1. The Godblade"]), deadeye)
    assert any("Auntie Ethel's Hair" in c.message for c in party_conflicts(party, acts=("3",)))
    assert not any("Auntie Ethel's Hair" in c.message for c in party_conflicts(party[:1], acts=("3",)))

def test_best_gear_keeps_armour_and_planned_items_unless_the_gain_is_real():
    """ Searching for damage never lowers armour class, only offers weapons the build is proficient with, and replaces an item the build
        already wears only for a gain of 3% or more; every change says what it adds """
    from bg3 import doc_import
    from bg3.character import Bg3Character, is_proficient, weapon_proficiencies
    from bg3.defence import armour_class
    from bg3.loadout import MIN_GAIN, best_gear
    from bg3.optimize import weapon_candidates
    doc = {e["build"]["name"]: e["build"] for e in doc_import.load()}
    party = [Bg3Build.from_dict(doc[n]) for n in ("1. The Godblade", "5. Arcane Deadeye")]
    for index, build in enumerate(party):
        gear, changes, _ = best_gear(party, index, ["2", "3"], "damage", Enemy(), 3, 1, 6, True, True)
        for act, slots in gear.items():
            after = replace(build, equipment={**build.equipment, act: {**build.equipment.get(act, {}), **slots}})
            assert armour_class(after, act)[0] >= armour_class(build, act)[0]
        assert all(c["gain"] > 0 for c in changes)
        before = expected_damage_per_round(compile_build(build, "3"), Enemy(), 3)
        assert all(c["gain"] >= MIN_GAIN * before * 0.9 for c in changes if c["before"] and c["act"] == "3")
    wizard = Bg3Build.from_dict(doc["14. Death Cleric Necromancer"])
    profs = weapon_proficiencies(Bg3Character.from_dict(wizard.character), 12)
    _, pool = weapon_candidates(wizard, "3")
    assert pool and all(is_proficient(i.weapon.get("base"), profs) for i in pool) and "bg3:infernal_rapier" not in {i.key for i in pool}

def test_estimates_party_synergies_and_items_the_damage_cannot_judge():
    """ A build's own estimates replace the defaults (kills with Bloodlust, reaction attacks); the planner gives damage with the party's
        every-fight synergies next to damage alone; best in slot leaves a worn item whose effects aren't all counted, and says so """
    from api import planner
    from bg3 import doc_import
    from bg3.character import Bg3Character
    from bg3.loadout import best_gear
    doc = {e["build"]["name"]: e["build"] for e in doc_import.load()}
    def damage(build):
        return expected_damage_per_round(compile_build(build, "3"), Enemy(), 3)
    godblade = Bg3Build.from_dict(doc["1. The Godblade"])
    thirsty = replace(godblade, buffs={"3": ["elixir:elixir_of_bloodlust"]})
    none, usual, many = (damage(replace(thirsty, assumptions=a)) for a in ({"bloodlust_kills": 0}, {}, {"bloodlust_kills": 3}))
    assert damage(replace(godblade, buffs={})) == pytest.approx(none) and none < usual < many
    polearm = Bg3Build("Polearm", "", character=Bg3Character(feats=["Polearm Master", "Sentinel"], routine="polearm").to_dict())
    quiet, normal, busy = (damage(replace(polearm, assumptions=a)) for a in ({"polearm_reactions": 0, "sentinel_reactions": 0}, {}, {"sentinel_reactions": 3}))
    assert quiet < normal < busy
    assert not [a for a in compile_build(replace(polearm, assumptions={"polearm_reactions": 0, "sentinel_reactions": 0}), "3").attacks if a.action == "reaction"]

    # The Godblade carries the Resonance Stone and deals psychic damage: more with the party's synergies from Act 2, the same in Act 1
    party = [Bg3Build.from_dict(doc[n]) for n in ("1. The Godblade", "5. Arcane Deadeye")]
    result = planner.evaluate([b.to_dict() for b in party])
    acts = result["members"][0]["acts"]
    assert "Resonance Stone" in result["synergies"]["3"] and "Resonance Stone" not in result["synergies"]["1"]
    assert acts["3"]["together"][0] > 1.3 * acts["3"]["damage"][0] and acts["1"]["together"] == acts["1"]["damage"]
    assert {o["key"] for o in planner.options()["assumptions"]} == {"bloodlust_kills", "polearm_reactions", "sentinel_reactions", "advantage_share"}

    items = catalog()
    names = {i.name: i for i in items.values()}
    for index in range(len(party)):
        _, changes, kept = best_gear(party, index, ["3"], "damage", Enemy(), 3, 1, 6, True, True)
        # Replaced items are fully counted, or partly counted and beaten by a wide margin
        base = expected_damage_per_round(compile_build(party[index], "3"), Enemy(), 3)
        assert all((names[c["before"]].effects or names[c["before"]].weapon) and c["gain"] >= 0.09 * base for c in changes if c["before"] and names[c["before"]].notes)
        assert all(names[k["item"]].notes and k["gain"] > 0 for k in kept)
    _, changes, kept = best_gear(party, 0, ["3"], "damage", Enemy(), 3, 1, 6, True, True, keep_uncounted=False)
    assert not kept and any(c["before"] and names[c["before"]].notes and not names[c["before"]].effects for c in changes)

def test_belm_in_the_off_hand_and_rhapsody_stacks():
    """ Belm in the off hand turns the bonus action attack into a main hand one (Perfectly Balanced Strike); Rhapsody's Scarlet
        Remittance is one toggle for its three effects (+3 to hit, damage and spell save DC) """
    from api.planner import conditional_options
    from bg3.character import Bg3Character
    blade = Bg3Character(classes=[["wizard", "Bladesinging", 12]], routine="shadow_blade", scores={**Bg3Character().scores, "dexterity": 16}).to_dict()
    def build(off, conditions=()):
        return Bg3Build("Blade", "", character=blade, equipment={"3": {"melee_off": off}}, conditions=list(conditions))
    belm = compile_build(build("bg3:belm"), "3")
    strike = next(a for a in belm.attacks if a.label == "Perfectly Balanced Strike")
    assert strike.action == "bonus" and not strike.offhand and strike.damage == "4d8" and not [a for a in belm.attacks if a.offhand]
    options = conditional_options(build("bg3:rhapsody"))
    assert len(options) == 1 and options[0]["label"].startswith("Rhapsody: Scarlet Remittance")
    cold, hot = (expected_damage_per_round(compile_build(build("bg3:rhapsody", c), "3"), Enemy(), 3) for c in ((), (options[0]["value"],)))
    assert cold < expected_damage_per_round(belm, Enemy(), 3) and hot > 1.15 * cold
    assert next(a for a in compile_build(build("bg3:rhapsody", (options[0]["value"],)), "3").attacks if not a.offhand).bonus_damage_die_mod_list[-1] == "3"

def test_a_hold_can_fail_and_the_resonance_stone_weakens_mental_saves():
    """ A held enemy counts for the share of turns it fails its Wisdom save against the caster's DC; the Resonance Stone gives enemies
        disadvantage on Intelligence, Wisdom and Charisma saves, for the hold and for save spells """
    from bg3 import synergy
    from bg3.character import Bg3Character
    wizard = Bg3Character(classes=[["wizard", "Bladesinging", 12]], routine="shadow_blade", scores={**Bg3Character().scores, "intelligence": 16}).to_dict()
    blade = Bg3Build("Blade", "", character=wizard, carried=["Resonance Stone"])
    tough = Enemy(wisdom_save=9)
    lands, dc, caster = synergy.hold_chance([blade], "3", tough)
    assert caster == "Blade" and lands == pytest.approx((dc - 1 - 9) / 20)
    stoned, active = synergy.party_enemy([blade], "3", tough, ["resonance_stone"])
    assert stoned.save_disadvantage == ["charisma", "intelligence", "wisdom"] and active == ["resonance_stone"]
    assert synergy.hold_chance([blade], "3", stoned)[0] == pytest.approx(1 - (1 - lands) ** 2)
    free = synergy.party_damage([blade], "3", tough, 3, ["resonance_stone"])[0][2]
    mixed = synergy.party_damage([blade], "3", tough, 3, ["resonance_stone", "paralysed"])[0][2]
    characters, foe = synergy.apply([blade], "3", tough, ["resonance_stone", "paralysed"])
    always = expected_damage_per_round(characters[0], foe, 3)
    share = synergy.hold_chance([blade], "3", stoned)[0]
    assert free < mixed < always and mixed == pytest.approx(share * always + (1 - share) * free)
    assert "lands" in synergy.describe([blade], "3", tough)["paralysed"]
    fight = synergy.simulate_party_fight([blade], "3", tough, 3, ["resonance_stone", "paralysed"], num_fights=500)
    assert 0 < fight["median_round"]
    # A Wisdom save cantrip against the same enemy: disadvantage makes it fail more often
    caster = compile_build(Bg3Build("Cleric", "", character=Bg3Character(classes=[["cleric", "Life Domain", 12]], routine="cantrip", cantrip="Toll the Dead").to_dict()), "3")
    assert expected_damage_per_round(caster, stoned) > expected_damage_per_round(caster, tough)

def test_eldritch_knight_shadow_blade_gets_war_magic_and_action_surge():
    from bg3.character import Bg3Character, compile_character
    knight = Bg3Character(name="Knight", race="Human", scores={"strength": 8, "dexterity": 17, "constitution": 14, "intelligence": 10, "wisdom": 12, "charisma": 10},
                          bonus={"dexterity": 2, "constitution": 1}, classes=[["fighter", "Eldritch Knight", 11], ["warlock", "The Hexblade", 1]],
                          feats=["dexterity+2", "constitution+2"], routine="shadow_blade")
    c, _ = compile_character(knight, 12)
    names = [a.name for a in c.attacks]
    assert "Shadow Blade (War Magic)" in names and not any(a.offhand for a in c.attacks) # War Magic takes the off-hand swing's bonus action
    assert names.count("Shadow Blade (Action Surge)") == 3

def test_strength_gear_sets_the_finesse_stat():
    from bg3.character import Bg3Character
    """ Gauntlets of Hill Giant Strength (23) beat Dexterity 20 for Shadow Blade and finesse daggers """
    character = Bg3Character(scores={"strength": 8, "dexterity": 17, "constitution": 14, "intelligence": 16, "wisdom": 10, "charisma": 8},
                             classes=[["paladin", "Oath of the Crown", 2], ["wizard", "Bladesinging", 10]], feats=["dexterity+2"],
                             fighting_styles=["Two-Weapon Fighting"], routine="shadow_blade").to_dict()
    bare = compile_build(Bg3Build("Godblade", "", character=character), "3")
    gloved = compile_build(Bg3Build("Godblade", "", character=character, equipment={"3": {"gloves": "bg3:gauntlets_of_hill_giant_strength"}}), "3")
    assert {a.ability_stat for a in bare.attacks if a.is_weapon} == {"dexterity"}
    assert {a.ability_stat for a in gloved.attacks if a.is_weapon} == {"strength"}
    assert expected_damage_per_round(gloved, Enemy(armor_class=18)) > expected_damage_per_round(bare, Enemy(armor_class=18))

def test_spellmight_gloves_add_to_booming_blade_without_the_penalty():
    from bg3.character import Bg3Character
    character = Bg3Character(classes=[["wizard", "Bladesinging", 12]], routine="shadow_blade").to_dict()
    gloved = compile_build(Bg3Build("Blade", "", character=character, equipment={"3": {"gloves": "bg3:spellmight_gloves"}}), "3")
    booming = [a for a in gloved.attacks if "booming_blade" in a.tags]
    assert booming and all("1d8 thunder" in a.extra_damage_list and "1d8" in a.bonus_damage_die_mod_list for a in booming)
    assert all("-5" not in a.bonus_attack_die_mod_list for a in booming)
    assert not any("1d8 thunder" in a.extra_damage_list for a in gloved.attacks if "booming_blade" not in a.tags)

def test_necklace_of_elemental_augmentation_skips_booming_blade():
    from bg3.character import Bg3Character
    character = Bg3Character(classes=[["wizard", "Bladesinging", 12]], routine="shadow_blade").to_dict()
    bare = compile_build(Bg3Build("Blade", "", character=character), "3")
    worn = Bg3Build("Blade", "", character=character, equipment={"3": {"amulet": "bg3:necklace_of_elemental_augmentation"}},
                    conditions=["bg3:necklace_of_elemental_augmentation#0"])
    assert expected_damage_per_round(compile_build(worn, "3"), Enemy(armor_class=18)) == expected_damage_per_round(bare, Enemy(armor_class=18))

def test_ring_of_regeneration_keeps_broodmothers_revenge_up():
    from bg3.character import Bg3Character
    character = Bg3Character(classes=[["fighter", "Battle Master", 12]], routine="dual_wield").to_dict()
    amulet = {"amulet": "bg3:broodmother_s_revenge"}
    alone = compile_build(Bg3Build("F", "", character=character, equipment={"3": amulet}), "3")
    healed = compile_build(Bg3Build("F", "", character=character, equipment={"3": {**amulet, "ring_1": "bg3:ring_of_regeneration"}}), "3")
    assert not any("1d6 poison" in a.extra_damage_list for a in alone.attacks)
    assert all("1d6 poison" in a.extra_damage_list for a in healed.attacks if a.is_weapon)

def test_wavemothers_cloak_adds_armour_class():
    from bg3.character import Bg3Character
    from bg3.defence import armour_class
    character = Bg3Character(classes=[["fighter", "Battle Master", 12]], routine="dual_wield").to_dict()
    bare = armour_class(Bg3Build("F", "", character=character), "3")[0]
    assert armour_class(Bg3Build("F", "", character=character, equipment={"3": {"cloak": "bg3:wavemother_s_cloak"}}), "3")[0] == bare + 2

def test_saved_party_variants_compile():
    from bg3.kits import variant_builds
    from bg3.parties import saved_parties
    party = saved_parties()[0]
    assert len(party["builds"]) == 4 and party["notes"]
    godblade = party["builds"][0]
    assert equipment_at(godblade, "3")["gloves"] == "bg3:spellmight_gloves"
    for name, _, build in variant_builds(godblade):
        compile_build(build, "3")
        if name.startswith("Elixir: Cloud Giant"):
            assert [b for b in build.buffs["3"] if b.startswith("elixir:")] == ["elixir:elixir_of_cloud_giant_strength"]

def test_medium_armour_gloves_end_mage_armour_and_bladesong():
    from bg3.defence import armour_class
    from bg3.parties import saved_parties
    godblade = saved_parties()[0]["builds"][0]
    ac, parts = armour_class(godblade, "3")
    gloved = replace(godblade, equipment={**godblade.equipment, "3": {**godblade.equipment["3"], "gloves": "bg3:legacy_of_the_masters"}})
    ac2, parts2 = armour_class(gloved, "3")
    assert any(s.startswith("Bladesong") for s, _ in parts) and not any(s.startswith(("Bladesong", "Mage Armour")) for s, _ in parts2)
    assert ac2 < ac

def test_frontier_is_non_dominated_and_starts_from_the_planned_gear():
    from bg3.frontier import solve
    from bg3.leaderboard import reference_enemy
    from bg3.parties import saved_parties
    godblade = saved_parties()[0]["builds"][0]
    result = solve(godblade, "3", reference_enemy(3), 3)
    current, frontier = result["current"], result["frontier"]
    assert current["changes"] == [] and current["ac"] == 28
    assert frontier and all(not (q["ac"] >= p["ac"] and q["damage"] > p["damage"]) for p in frontier for q in result["points"])
    assert max(p["damage"] for p in frontier) >= current["damage"]
    # Items that only pay off together are tried as a pair
    assert any({("amulet", "bg3:broodmother_s_revenge"), ("ring_1", "bg3:ring_of_regeneration")} <= set(p["changes"]) for p in result["points"])

def test_party_variants_are_leaderboard_rows():
    from api.leaderboard import _party_entries
    build = Bg3Build("Blade", "fighter_gwm", variants=[{"name": "Bless", "buffs": ["bless"]}])
    rows = _party_entries([build])
    saved = [r for r in rows if r["variant"] == "saved"]
    assert [r["name"] for r in saved] == ["Blade: Bless"] and saved[0]["base"] == rows[0]["fingerprint"]

def test_advantage_share_and_rapture():
    from bg3.parties import saved_parties
    godblade = saved_parties()[0]["builds"][0]
    character = compile_build(godblade, "3")
    weapons = [a for a in character.attacks if a.is_weapon]
    assert all(a.advantage_chance == 0.5 for a in weapons) and all("1d6" in a.bonus_attack_die_mod_list for a in weapons)
    plain = compile_build(replace(godblade, assumptions={}), "3")
    assert all(a.advantage_chance == 0 for a in plain.attacks if a.is_weapon)

def test_self_cast_haste_takes_a_smite_slot():
    from bg3.parties import saved_parties
    godblade = saved_parties()[0]["builds"][0]
    hasted = compile_build(godblade, "3")
    slow = compile_build(replace(godblade, buffs={**godblade.buffs, "3": [b for b in godblade.buffs["3"] if b != "haste"]}), "3")
    assert hasted.once_per_turn_damage_type == "radiant"
    assert round(slow.once_per_turn_uses_per_fight - hasted.once_per_turn_uses_per_fight, 2) == 1
