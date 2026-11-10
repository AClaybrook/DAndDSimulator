""" BG3 character builder: compiled characters follow the Patch 8 rules, and match the prebuilt characters where they should """
import pytest

from bg3.abilities import point_buy_problems
from bg3.character import Bg3Character, caster_level, class_levels, compile_character, feat_opportunities, relevant_toggles
from computations.analytic import expected_damage_per_round
from computations.models import Enemy
from game_data.classes import build_character

ENEMY = Enemy(armor_class=15)
STR = {"strength": 15, "dexterity": 13, "constitution": 13, "intelligence": 8, "wisdom": 10, "charisma": 8}

def champion():
    return Bg3Character("Champion", scores=STR, bonus={"strength": 2, "constitution": 1}, classes=[["fighter", "Champion", 12]],
                        feats=["Great Weapon Master", "strength+2", "strength+2", "Savage Attacker"], fighting_styles=["Great Weapon Fighting"])

@pytest.mark.parametrize("level", [1, 3, 5, 8, 11, 12])
def test_champion_matches_the_preset(level):
    character, notes = compile_character(champion(), level)
    preset = build_character("fighter_gwm", level)
    assert not notes and not point_buy_problems(STR, {"strength": 2, "constitution": 1})
    assert expected_damage_per_round(character, ENEMY, 3) == pytest.approx(expected_damage_per_round(preset, ENEMY, 3))

def test_multiclass_levels_feats_and_spell_slots():
    sorcadin = Bg3Character(classes=[["paladin", "Oath of Vengeance", 6], ["sorcerer", "Draconic Bloodline", 6]])
    assert class_levels(sorcadin, 9) == {"paladin": 6, "sorcerer": 3}
    # Feats at class levels 4 (paladin) and 4 (sorcerer, character level 10)
    assert [lv for lv, _ in feat_opportunities(sorcadin)] == [4, 10]
    assert caster_level({"paladin": 5}, {}) == 3 and caster_level({"paladin": 6, "sorcerer": 6}, {}) == 9
    # Eldritch Knight: level 2 slots at Fighter 7 (Shadow Blade), level 3 slots at 13; nothing before Fighter 3
    ek = {"fighter": "Eldritch Knight"}
    assert [caster_level({"fighter": n}, ek) for n in (2, 3, 6, 7, 12, 13)] == [0, 1, 2, 3, 4, 5]
    character, _ = compile_character(sorcadin, 12)
    # Smites average the day's slots (4/3/3/3/1 plus a level 4 slot from 6 sorcery points: 3.6d8 = 3d8 + 3), Vow of Enmity
    assert character.once_per_turn_die_mod_list == ["3d8", "3"] and character.once_per_turn_uses_per_fight == 3.75 and character.advantage

def test_class_features():
    rogue = Bg3Character(scores={**STR, "dexterity": 15, "strength": 8}, classes=[["rogue", "Thief", 12]], routine="dual_wield")
    character, _ = compile_character(rogue, 5)
    assert character.once_per_turn_die_mod_list == ["3d6"]
    assert [a.offhand for a in character.attacks].count(True) == 2 # Fast Hands: a second off-hand attack
    assert not any(a.once_per_turn_eligible for a in character.attacks if a.offhand) # No Sneak Attack off hand in BG3
    monk, _ = compile_character(Bg3Character(classes=[["monk", "Way of the Open Hand", 12]], routine="unarmed"), 9)
    assert monk.attacks[0].damage == "1d8" and monk.attacks[0].extra_damage_list # Martial Arts d8 at 9, Manifestation of Body
    barbarian, _ = compile_character(Bg3Character(classes=[["barbarian", "Berserker", 2], ["fighter", "Champion", 10]]), 12)
    assert barbarian.raging and barbarian.rage_damage == 2 # Rage damage follows the barbarian level
    assert "Greatsword (Frenzy)" not in [a.name for a in barbarian.attacks] # Frenzy needs barbarian level 3

def test_cantrip_casters():
    sorlock = Bg3Character(scores={**STR, "charisma": 15, "strength": 8}, bonus={"charisma": 2, "constitution": 1},
                           classes=[["warlock", "The Fiend", 2], ["sorcerer", "Draconic Bloodline", 10]], routine="cantrip", cantrip="Eldritch Blast")
    character, notes = compile_character(sorlock, 10)
    assert character.agonizing_blast and [a.name for a in character.attacks].count("Eldritch Blast 3") == 1
    assert any(a.name.startswith("Quickened") for a in character.attacks) # Quickened Spell from sorcerer level 3
    # Elemental Affinity only for the ancestry's damage type, Eldritch Blast is force
    assert not any("3" in a.bonus_damage_die_mod_list for a in character.attacks)
    fire = Bg3Character(scores={**STR, "charisma": 15}, classes=[["sorcerer", "Draconic Bloodline", 12]], routine="cantrip", cantrip="Fire Bolt")
    assert compile_character(fire, 6)[0].attacks[0].bonus_damage_die_mod_list
    assert any("no damage features" in n for n in notes) # The Fiend

def test_round_trip():
    character = champion()
    assert Bg3Character.from_dict(character.to_dict()) == character

def test_custom_character_in_a_planner_build():
    from bg3.build import Bg3Build, compile_build
    build = Bg3Build("Tav", "fighter_gwm", character=champion().to_dict(), equipment={"1": {"melee_main": "bg3:everburn_blade"}})
    act1 = compile_build(build, 1)
    assert act1.level == 5 and act1.attacks[0].name == "Everburn Blade" and "Human" in act1.description
    assert expected_damage_per_round(act1, ENEMY, 3) == pytest.approx(
        expected_damage_per_round(compile_build(Bg3Build("Tav", "fighter_gwm", equipment=build.equipment), 1), ENEMY, 3))

def test_example_custom_characters_are_valid():
    from bg3.build import compile_build
    from bg3.presets import PRESETS
    custom = [b for b in PRESETS.values() if b.character]
    assert len(custom) >= 8
    for build in custom:
        character = Bg3Character.from_dict(build.character)
        assert not point_buy_problems(character.scores, character.bonus), build.name
        assert len(character.feats) >= len(feat_opportunities(character)) - 1, build.name
        assert all(expected_damage_per_round(compile_build(build, act), ENEMY, 3) > 0 for act in "123"), build.name

def test_weapon_proficiencies():
    from bg3.build import Bg3Build, compile_build
    from bg3.character import is_proficient, weapon_proficiencies
    from bg3.party import build_conflicts
    wizard = Bg3Character(race="Human", classes=[["wizard", "Evocation School", 12]], routine="two_handed")
    profs = weapon_proficiencies(wizard)
    assert not is_proficient("Greatsword", profs) and is_proficient("Quarterstaff", profs) and is_proficient("Halberd", profs) # Human: polearms
    character, notes = compile_character(wizard, 5)
    assert not character.attacks[0].proficient and any("Not proficient" in n for n in notes)
    # Multiclassing into fighter gives martial weapons, multiclassing into rogue doesn't
    assert is_proficient("Greatsword", weapon_proficiencies(Bg3Character(classes=[["wizard", "", 2], ["fighter", "Champion", 1]])))
    assert not is_proficient("Greatsword", weapon_proficiencies(Bg3Character(race="Gold Dwarf", classes=[["wizard", "", 2], ["rogue", "Thief", 1]])))
    assert is_proficient("Greatsword", weapon_proficiencies(Bg3Character(race="Githyanki", classes=[["wizard", "", 2]])))
    # Gear: a sword on a wizard is flagged and loses the proficiency bonus
    build = Bg3Build("Gale", "wizard_fireball", character=wizard.to_dict(), equipment={"1": {"melee_main": "bg3:everburn_blade"}})
    assert not compile_build(build, 1).attacks[0].proficient
    assert [c.kind for c in build_conflicts(build, 1)] == ["proficiency"]

def test_thrown_and_levelled_spells():
    giant = Bg3Character(scores=STR, bonus={"strength": 2, "constitution": 1}, classes=[["barbarian", "Giant", 12]], feats=["Tavern Brawler"], routine="thrown")
    character, _ = compile_character(giant, 5)
    assert all(a.type == "thrown" and a.bonus_damage_die_mod_list == ["2"] for a in character.attacks) # Giant's Rage doubled on throws
    berserker, _ = compile_character(Bg3Character(classes=[["barbarian", "Berserker", 12]], routine="thrown"), 5)
    assert berserker.attacks[-1].name == "Handaxe (Enraged Throw)"
    wizard = Bg3Character(scores={**STR, "intelligence": 15, "strength": 8}, classes=[["wizard", "Evocation School", 12]], routine="cantrip",
                          cantrip="Fire Bolt", spell="Fireball")
    character, _ = compile_character(wizard, 5)
    assert character.attacks[0].name == "Fireball" and character.attacks[0].uses_per_fight == 0.5 and character.attacks[1].fallback_for == "Fireball"
    _, notes = compile_character(wizard, 4)
    assert any("No spell slots" in n for n in notes)

def test_limited_riders_keep_their_fallback_with_gear():
    from bg3.build import Bg3Build, compile_build
    bm = Bg3Character(scores=STR, classes=[["fighter", "Battle Master", 12]], fighting_styles=["Great Weapon Fighting"])
    character, _ = compile_character(bm, 5)
    assert character.attacks[0].name == "Greatsword (Trip Attack)" and character.attacks[1].fallback_for == "Greatsword (Trip Attack)"
    geared = compile_build(Bg3Build("BM", "fighter_gwm", character=bm.to_dict(), equipment={"1": {"melee_main": "bg3:everburn_blade"}}), 1)
    assert geared.attacks[0].name == "Everburn Blade (Trip Attack)" and geared.attacks[1].fallback_for == "Everburn Blade (Trip Attack)"
    # Superiority dice no longer use the once per turn pool, so they stack with Sneak Attack
    fighter_rogue = Bg3Character(scores=STR, classes=[["fighter", "Battle Master", 3], ["rogue", "Thief", 9]], routine="dual_wield")
    character, _ = compile_character(fighter_rogue, 12)
    assert character.once_per_turn_die_mod_list == ["5d6"] and any("Trip Attack" in a.name for a in character.attacks)

WIS = {"strength": 8, "dexterity": 14, "constitution": 15, "intelligence": 8, "wisdom": 15, "charisma": 10}

def test_circle_of_stars_and_spores():
    stars = Bg3Character("Stars", scores=WIS, bonus={"wisdom": 2, "constitution": 1}, classes=[["druid", "Circle of Stars", 12]],
                         feats=["wisdom+2"], routine="cantrip", cantrip="Produce Flame")
    character, notes = compile_character(stars, 5)
    names = {a.name: a for a in character.attacks}
    # Star Map Guiding Bolts (3 per long rest at level 5) before the cantrip, Luminous Arrow every round
    assert names["Guiding Bolt"].uses_per_fight == 0.75 and names["Produce Flame"].fallback_for == "Guiding Bolt"
    assert names["Luminous Arrow"].damage == "1d8+4" and not names["Luminous Arrow"].uses_per_fight and not notes
    assert compile_character(stars, 10)[0].attacks[-1].damage == "2d8+4"
    stars.toggles["starry_form"] = False
    assert "Luminous Arrow" not in {a.name for a in compile_character(stars, 5)[0].attacks}

    spores = Bg3Character("Spores", classes=[["druid", "Circle of Spores", 12]], routine="unarmed")
    assert compile_character(spores, 2)[0].attacks[0].extra_damage_list == ["1d6 necrotic"]

def test_heart_of_the_storm_hits_or_misses():
    storm = Bg3Character("Storm", classes=[["sorcerer", "Storm Sorcery", 12]], routine="cantrip", cantrip="Shocking Grasp")
    before, _ = compile_character(storm, 5)
    after, _ = compile_character(storm, 6)
    grasp = next(a for a in after.attacks if a.name == "Shocking Grasp")
    assert grasp.extra_damage_list == ["3 lightning"] and grasp.bonus_miss_die_mod_list == [3]
    assert not next(a for a in before.attacks if a.name == "Shocking Grasp").extra_damage_list
    # Three damage on every cast, hit or miss (Shocking Grasp's dice and Quickened casts aside)
    gain = expected_damage_per_round(after, ENEMY, 4) - expected_damage_per_round(replace_toggle(storm, "storm_close"), ENEMY, 4)
    casts = sum(1 if not a.uses_per_fight else a.uses_per_fight / 4 for a in after.attacks)
    assert gain == pytest.approx(3 * casts)

def replace_toggle(character, key):
    off = Bg3Character.from_dict({**character.to_dict(), "toggles": {key: False}})
    return compile_character(off, 6)[0]

def test_builder_only_offers_toggles_for_its_classes():
    assert relevant_toggles([["fighter", "Champion", 12]]) == ["reactions", "honour_mode", "advantage"]
    assert relevant_toggles([["paladin", "Oathbreaker", 6], ["warlock", "The Hexblade", 6]]) == ["smite", "vow", "curse", "booming_blade", "offhand_crossbow", "reactions", "honour_mode", "advantage"]
    assert relevant_toggles([["warlock", "The Fiend", 12]]) == ["booming_blade", "offhand_crossbow", "reactions", "honour_mode", "advantage"]


def test_shadow_blade_and_booming_blade():
    from bg3.character import shadow_blade_dice
    blade = Bg3Character("Godblade", scores={"strength": 8, "dexterity": 15, "constitution": 14, "intelligence": 15, "wisdom": 10, "charisma": 8},
                         bonus={"dexterity": 2, "intelligence": 1}, classes=[["wizard", "Bladesinging", 10], ["paladin", "Oath of the Crown", 2]],
                         routine="shadow_blade")
    # Upcasting only helps with odd slot levels: 2d8, 3d8 from level 3 slots, 4d8 from level 5 slots
    assert [shadow_blade_dice({"wizard": n}, {}) for n in (2, 3, 5, 8, 9)] == [0, 2, 3, 3, 4]
    assert shadow_blade_dice({"warlock": 9}, {}) == 4
    attacks = {a.name: a for a in compile_character(blade, 5)[0].attacks}
    assert attacks["Shadow Blade (Booming Blade)"].damage == "3d8" and attacks["Shadow Blade (Booming Blade)"].damage_type == "psychic"
    assert attacks["Shadow Blade (Booming Blade)"].extra_damage_list == ["1d8 thunder"] and attacks["Dagger (Offhand)"].offhand
    assert compile_character(blade, 12)[0].attacks[0].extra_damage_list == ["2d8 thunder"]
    # Before a level 2 slot: a Rapier, no Booming Blade damage before level 5
    early, notes = compile_character(blade, 2)
    assert early.attacks[0].name == "Rapier" and notes
    blade.toggles["booming_blade"] = False
    assert not compile_character(blade, 5)[0].attacks[0].extra_damage_list

def test_advantage_toggle_is_off_by_default():
    character = Bg3Character(classes=[["wizard", "Bladesinging", 5]], routine="shadow_blade")
    assert not character.toggle("advantage") and character.toggle("booming_blade")
    plain, _ = compile_character(character, 5)
    character.toggles["advantage"] = True
    assert not plain.advantage and compile_character(character, 5)[0].advantage

def test_dual_hand_crossbows():
    character = Bg3Character(classes=[["ranger", "Gloom Stalker", 5]], routine="dual_hand_crossbows", fighting_styles=["Archery"])
    c, _ = compile_character(character, 5)
    names = [a.name for a in c.attacks]
    assert names.count("Hand Crossbow") == 2 and "Hand Crossbow (Offhand)" in names
    assert all(a.type == "weapon (ranged)" for a in c.attacks)


def _attack_names(character, level):
    c, notes = compile_character(character, level)
    return [a.name for a in c.attacks], c, notes

def test_pact_of_the_blade_extra_attack_stacks_outside_honour_mode():
    """ bg3.wiki, Deepened Pact: Pact of the Blade's Extra Attack stacks with a Paladin's (3 attacks), but not in Honour Mode """
    padlock = Bg3Character("Padlock", classes=[["paladin", "Oath of Vengeance", 5], ["warlock", "The Hexblade", 5]], routine="two_handed",
                           toggles={"booming_blade": False})
    names, _, _ = _attack_names(padlock, 10)
    assert names.count("Greatsword") == 3
    honour = Bg3Character.from_dict({**padlock.to_dict(), "toggles": {"booming_blade": False, "honour_mode": True}})
    assert _attack_names(honour, 10)[0].count("Greatsword") == 2
    assert _attack_names(padlock, 9)[0].count("Greatsword") == 2 # Warlock 4: no Deepened Pact yet
    pure = Bg3Character("Blade", classes=[["warlock", "The Hexblade", 12]], routine="two_handed", toggles={"booming_blade": False})
    assert _attack_names(pure, 12)[0].count("Greatsword") == 2 # Deepened Pact alone is just Extra Attack
    ranged = Bg3Character.from_dict({**padlock.to_dict(), "routine": "ranged"})
    assert _attack_names(ranged, 10)[0].count("Longbow") == 2 # Not with a bow: the pact weapon is a melee weapon

def test_polearm_and_shadow_blade_with_a_shield():
    glaive = Bg3Character("Glaive", classes=[["fighter", "Battle Master", 12]], feats=["Polearm Master", "Great Weapon Master"],
                          fighting_styles=["Great Weapon Fighting"], routine="polearm")
    names, c, _ = _attack_names(glaive, 8)
    butt = next(a for a in c.attacks if a.name == "Polearm Butt End")
    assert "Glaive" in names and butt.damage == "1d4" and butt.two_handed and butt.heavy # GWF and GWM apply to the other end too
    shield = Bg3Character("Sword and board", classes=[["paladin", "Oath of Vengeance", 6], ["sorcerer", "Draconic Bloodline", 6]],
                          fighting_styles=["Duelling"], routine="shadow_blade_shield", toggles={"booming_blade": False})
    names, c, _ = _attack_names(shield, 12)
    assert names == ["Shadow Blade", "Shadow Blade"] and c.dueling and not any(a.offhand for a in c.attacks)
    # Paladin levels alone don't learn Shadow Blade: a Longsword (Strength, a shield) until a Sorcerer level
    names, _, notes = _attack_names(shield, 5)
    assert names == ["Longsword", "Longsword"] and any("Sorcerer, Warlock or Wizard" in n for n in notes)

def test_sneak_attack_needs_a_finesse_or_ranged_weapon():
    rapier = Bg3Character("Rapier", scores={"strength": 8, "dexterity": 15, "constitution": 15, "intelligence": 8, "wisdom": 14, "charisma": 10},
                          bonus={"dexterity": 2, "constitution": 1}, classes=[["rogue", "Thief", 5]], routine="one_handed")
    assert compile_character(rapier, 5)[0].once_per_turn_die_mod_list == ["3d6"]
    glaive = Bg3Character("Glaive rogue", classes=[["rogue", "Swashbuckler", 5]], routine="polearm")
    c, notes = compile_character(glaive, 5)
    assert not c.once_per_turn_die_mod_list and any("finesse" in n for n in notes)

def test_flick_and_sneak_attack_follow_a_finesse_weapon_from_gear():
    """ Flick o' the Wrist and Rakish Sneak Attack need a finesse weapon: none with a plain glaive, both with The Dancing Breeze (a finesse glaive) """
    from bg3.build import Bg3Build, compile_build
    swash = Bg3Character("Swash", classes=[["rogue", "Swashbuckler", 12]], routine="polearm")
    plain = compile_build(Bg3Build("Swash", "fighter_gwm", character=swash.to_dict()), "3")
    assert not plain.once_per_turn_die_mod_list and not any("Flick" in a.name for a in plain.attacks)
    breeze = compile_build(Bg3Build("Swash", "fighter_gwm", character=swash.to_dict(), equipment={"3": {"melee_main": "bg3:the_dancing_breeze"}}), "3")
    assert breeze.once_per_turn_die_mod_list == ["6d6"] and any("Flick" in a.name for a in breeze.attacks)

def test_reaction_attacks_and_the_halberd_of_vigilance():
    """ Polearm Master and Sentinel add expected reaction attacks; the Halberd of Vigilance gives them advantage """
    from bg3.build import compile_build
    from bg3.presets import PRESETS
    c = compile_build(PRESETS["Battle Master: Halberd of Vigilance (Polearm Master, GWM, Sentinel)"], "3")
    reactions = [a for a in c.attacks if "reaction)" in a.name]
    assert [a.uses_per_fight for a in reactions] == [1.0, 1.5] and all(a.advantage for a in reactions)
    plain = compile_build(PRESETS["Battle Master: Glaive (Polearm Master, GWM, Sentinel)"], "3")
    assert [a.advantage for a in plain.attacks if "reaction)" in a.name] == [True, False] # Sentinel: advantage on opportunity attacks only
    off = Bg3Character.from_dict({**PRESETS["Battle Master: Glaive (Polearm Master, GWM, Sentinel)"].character, "toggles": {"reactions": False}})
    assert not any("reaction)" in a.name for a in compile_character(off, 12)[0].attacks)

def test_reaction_attacks_get_their_own_sneak_attack():
    """ Sneak Attack is once per turn: a reaction attack on an enemy's turn adds its own, with a finesse weapon """
    from bg3.build import compile_build
    from bg3.presets import PRESETS
    c = compile_build(PRESETS["Fighter 6 / Swashbuckler 6: The Dancing Breeze (Dexterity, Polearm Master, Sentinel)"], "3")
    reactions = [a for a in c.attacks if "reaction)" in a.name]
    assert len(reactions) == 2 and all("3d6 slashing" in a.extra_damage_list and not a.once_per_turn_eligible for a in reactions)
    assert c.once_per_turn_die_mod_list == ["3d6"]

def test_quickened_spell_shares_slots_and_sorcery_points():
    """ A quickened levelled spell spends the same slots, and there is one quicken a fight at Sorcerer 12 (12 points, 3 each, 4 fights) """
    sorcerer = Bg3Character(classes=[["sorcerer", "Draconic Bloodline", 12]], routine="cantrip", cantrip="Fire Bolt", spell="Fireball")
    c, _ = compile_character(sorcerer, 12)
    uses = {a.name: a.uses_per_fight for a in c.attacks}
    assert uses == {"Fireball": 1.25, "Fire Bolt": 0, "Quickened Fireball": 1.0} # 2.25 slots a fight in all, no quickens left for the cantrip
    assert [a.action for a in c.attacks] == ["action", "action", "bonus"]
    # Few slots, more points: the quickens left over go on the cantrip, after the slots run out and only for that many rounds
    c, _ = compile_character(sorcerer, 6)
    quick = {a.name: (a.uses_per_fight, a.fallback_for) for a in c.attacks if "quickened" in a.tags}
    assert quick == {"Quickened Fireball": (0.38, ""), "Quickened Fire Bolt": (0.12, "Fireball")}
    assert sum(a.uses_per_fight for a in c.attacks if a.base == "Fireball") == pytest.approx(0.75, abs=0.02) # 3 level 3 slots over 4 fights
    # Without a levelled spell every quicken is a cantrip
    blaster, _ = compile_character(Bg3Character(classes=[["sorcerer", "Storm Sorcery", 12]], routine="cantrip", cantrip="Fire Bolt"), 12)
    assert [(a.name, a.uses_per_fight) for a in blaster.attacks] == [("Fire Bolt", 0), ("Quickened Fire Bolt", 1.0)]

def test_pact_weapon_charisma_is_main_hand_melee_only():
    cha = {"strength": 8, "dexterity": 14, "constitution": 14, "intelligence": 8, "wisdom": 10, "charisma": 17}
    def stats(routine):
        c, _ = compile_character(Bg3Character(scores=cha, bonus={"charisma": 2, "constitution": 1}, classes=[["warlock", "The Hexblade", 12]],
                                              routine=routine, toggles={"booming_blade": False}), 5)
        return {(a.offhand, a.ability_stat) for a in c.attacks}
    assert stats("one_handed") == {(False, "charisma")}
    assert stats("dual_wield") == {(False, "charisma"), (True, "dexterity")}
    assert stats("shadow_blade") == {(False, "charisma"), (True, "dexterity")}
    assert stats("ranged") == {(False, "dexterity")} and stats("thrown") == {(False, "strength")}

def test_multiclass_caster_level_sums_fractions():
    """ bg3.wiki: with several spellcasting classes the fractional levels are summed, then rounded down """
    assert caster_level({"paladin": 5, "ranger": 5}, {}) == 5 # 2.5 + 2.5, not 2 + 2
    assert caster_level({"paladin": 7, "sorcerer": 5}, {}) == 8
    assert caster_level({"fighter": 5, "rogue": 5}, {"fighter": "Eldritch Knight", "rogue": "Arcane Trickster"}) == 3 # 10 / 3
    assert caster_level({"paladin": 5}, {}) == 3 and caster_level({"fighter": 7}, {"fighter": "Eldritch Knight"}) == 3 # Single class: rounded up

def test_sneak_attack_and_smites_keep_separate_pools():
    scores = {"strength": 8, "dexterity": 16, "constitution": 14, "intelligence": 8, "wisdom": 10, "charisma": 16}
    build = Bg3Character(scores=scores, bonus={"dexterity": 1, "charisma": 2}, classes=[["paladin", "Oath of Vengeance", 6], ["rogue", "Thief", 6]],
                         routine="one_handed")
    c, _ = compile_character(build, 12)
    assert c.once_per_turn_die_mod_list == ["3d6"] and not c.once_per_turn_uses_per_fight and not c.once_per_turn_damage_type # Sneak Attack every round
    (smite,) = c.once_per_turn_extra
    assert smite["damage_type"] == "radiant" and smite["uses_per_fight"] > 0 and smite["dice"][0].endswith("d8")
    # A ranged or thrown paladin can't smite
    archer, _ = compile_character(Bg3Character(classes=[["paladin", "Oath of Vengeance", 12]], routine="ranged"), 5)
    assert not archer.once_per_turn_die_mod_list and not archer.once_per_turn_extra

def test_cleric_spirit_guardians_and_spiritual_weapon():
    """ bg3.wiki: Spirit Guardians 3d8 + 1d8 a slot level, an action; Spiritual Weapon 1d8 + 1 + WIS force, +1d8 per two slot levels,
        a bonus action, then its own attack every round """
    from bg3.character import cleric_slots
    wis = {"strength": 8, "dexterity": 14, "constitution": 14, "intelligence": 8, "wisdom": 17, "charisma": 10}
    def cleric(domain="Light Domain", **fields):
        return Bg3Character(**{"scores": wis, "bonus": {"wisdom": 2, "constitution": 1}, "classes": [["cleric", domain, 12]], "routine": "cantrip",
                               "cantrip": "Sacred Flame", "feats": ["wisdom+2"], **fields})
    both = cleric(spell="Spirit Guardians", toggles={"spiritual_weapon": True})
    c, notes = compile_character(both, 12)
    by_name = {a.name: a for a in c.attacks}
    # The day's best four slots (6, 5, 5, 4) go to Spirit Guardians: 5d8 on average; the next four (4, 4, 3, 3) to the weapon: 1.5d8
    assert cleric_slots(both, {"cleric": 12}, {"cleric": "Light Domain"}) == ([6, 5, 5, 4], [4, 4, 3, 3])
    assert by_name["Spirit Guardians (aura)"].damage == "5d8" and by_name["Spirit Guardians (aura)"].targets == 3
    weapon = by_name["Spiritual Weapon"]
    assert weapon.damage == "1d8+8" and weapon.damage_type == "force" and weapon.action == "bonus" and weapon.uses_per_fight == 10 # 1 + WIS 5 + half a d8
    assert by_name["Spirit Guardians (cast)"].uses_per_fight == 1 and by_name["Sacred Flame"].fallback_for == "Spirit Guardians (cast)" and not notes
    # The weapon alone, with every slot free: the two best are level 6 and 5 (3d8 and 2d8)
    alone, _ = compile_character(cleric(toggles={"spiritual_weapon": True}), 12)
    assert next(a for a in alone.attacks if a.name == "Spiritual Weapon").damage == "2d8+7" # (3 + 2 + 2 + 2) / 4 dice, the quarter die as +1, on top of 1 + WIS 5
    assert not any(a.name == "Spiritual Weapon" for a in compile_character(cleric(), 12)[0].attacks) # Off unless asked for
    # Level 3: the weapon in half the fights (two level 2 slots a day), no Spirit Guardians yet
    early, notes = compile_character(both, 3)
    assert next(a for a in early.attacks if a.name == "Spiritual Weapon").uses_per_fight == 1.5 and any("Spirit Guardians needs" in n for n in notes)
    # Death Domain: the aura is necrotic and Toll the Dead reaches a second creature (Reaper)
    death, _ = compile_character(cleric("Death Domain", spell="Spirit Guardians", cantrip="Toll the Dead"), 12)
    death = {a.name: a for a in death.attacks}
    assert death["Spirit Guardians (aura)"].damage_type == "necrotic" and death["Toll the Dead"].targets == 2
    # Haste's extra action attacks from round 1 while the action casts the spell
    from bg3.build import Bg3Build, compile_build
    hasted = compile_build(Bg3Build(name="Cleric", preset="", character=both.to_dict(), buffs={"3": ["haste"]}), "3")
    extra = next(a for a in hasted.attacks if a.label == "Haste")
    assert not extra.fallback_for and "after_cast" not in extra.tags

WIS17 = {"strength": 8, "dexterity": 14, "constitution": 14, "intelligence": 8, "wisdom": 17, "charisma": 10}

def reaper(**fields):
    """ Death Domain 8 / Necromancy 2 / Spores 2, WIS 20: Touch of Death deals 5 + 2 x 8 """
    return Bg3Character(**{"scores": WIS17, "bonus": {"wisdom": 2, "constitution": 1}, "routine": "cantrip", "cantrip": "Toll the Dead", "feats": ["wisdom+2"],
                           "classes": [["cleric", "Death Domain", 8], ["wizard", "Necromancy School", 2], ["druid", "Circle of Spores", 2]], **fields})

def attacks_of(character, level=12):
    return {a.name: a for a in compile_character(character, level)[0].attacks}

def test_death_domain_spells_and_touch_of_death():
    """ bg3.wiki: Touch of Death rides melee spell attacks; Reaper gives necromancy cantrips a second target; Dethrone has its own DC 18
        once a long rest; Circle of Death 8d6; Bursting Sinew 1d10 a tier in a 3 m burst; Thorn Whip 1d6 a tier """
    plain = attacks_of(reaper())
    assert plain["Toll the Dead"].damage == "3d12" and plain["Toll the Dead"].targets == 2 and "necromancy" in plain["Toll the Dead"].tags
    assert not any("Touch of Death" in name for name in plain) # A saving throw cantrip has nothing to carry it
    # Two charges a short rest: 1.5 casts a fight carry it, the cantrip goes on without
    whip = attacks_of(reaper(cantrip="Thorn Whip"))
    carrier = whip["Thorn Whip (Touch of Death)"]
    assert carrier.damage == "3d6" and carrier.extra_damage_list == ["21 necrotic"] and carrier.uses_per_fight == 1.5 and "channel_divinity" in carrier.tags
    assert whip["Thorn Whip"].fallback_for == carrier.name and not whip["Thorn Whip"].uses_per_fight
    # A limited spell splits its casts: 16 slots over four fights, 1.5 of the four casts a fight with a charge
    wounds = attacks_of(reaper(spell="Inflict Wounds"))
    assert wounds["Inflict Wounds (Touch of Death)"].uses_per_fight == 1.5 and wounds["Inflict Wounds"].uses_per_fight == 2.5
    assert wounds["Inflict Wounds"].fallback_for == "Inflict Wounds (Touch of Death)" and wounds["Toll the Dead"].fallback_for == "Inflict Wounds"
    dethrone = attacks_of(reaper(spell="Dethrone"))["Dethrone"]
    assert dethrone.damage == "10d6+20" and dethrone.save_dc == 18 and dethrone.uses_per_fight == 0.25 and dethrone.saving_throw_stat == "constitution"
    sinew = attacks_of(reaper(cantrip="Bursting Sinew"))["Bursting Sinew"]
    assert sinew.damage == "3d10" and sinew.targets == 3 and sinew.saving_throw_stat == "dexterity"
    # Halo of Spores: a reaction every round, 1d4 necrotic doubled by Symbiotic Entity, CON save
    halo = plain["Halo of Spores"]
    assert halo.action == "reaction" and halo.damage == "2d4" and halo.saving_throw_stat == "constitution" and not halo.uses_per_fight
    assert attacks_of(reaper(toggles={"symbiotic": False}))["Halo of Spores"].damage == "1d4"

def test_spirit_guardians_around_another_spell():
    """ Spirit Guardians cast first with another spell as the build's own: a spell of level 4 or more keeps its slots """
    from bg3.character import cleric_slots
    levels, subs = {"cleric": 8, "wizard": 2, "druid": 2}, {"cleric": "Death Domain"}
    both = {"spirit_guardians": True, "spiritual_weapon": True}
    circle = reaper(spell="Circle of Death", toggles=both)
    assert cleric_slots(circle, levels, subs) == ([5, 5, 4, 4], [4, 3, 3, 3]) # The level 6 slot is Circle of Death's
    assert cleric_slots(reaper(spell="Dethrone", toggles=both), levels, subs) == ([6, 5, 4, 4], [4, 3, 3, 3]) # Once a day: one level 5 slot kept
    assert cleric_slots(reaper(spell="Spirit Guardians", toggles={"spiritual_weapon": True}), levels, subs) == ([6, 5, 5, 4], [4, 4, 3, 3])
    assert cleric_slots(reaper(spell="Inflict Wounds", toggles=both), levels, subs) == ([6, 5, 5, 4], [2, 2, 2, 3]) # Cast with every slot left
    by_name = attacks_of(circle)
    assert by_name["Circle of Death"].uses_per_fight == 0.25 and by_name["Circle of Death"].targets == 4
    # Round 1 casts the aura, then Circle of Death, then the cantrip
    assert by_name["Circle of Death"].fallback_for == "Spirit Guardians (cast)" and by_name["Toll the Dead"].fallback_for == "Circle of Death"
    assert by_name["Spirit Guardians (aura)"].uses_per_fight == 10 and "spirit_guardians" in relevant_toggles(circle.classes)

def test_divine_strike_is_typed_and_weapon_only():
    from computations.models import once_per_turn_pools
    melee, _ = compile_character(Bg3Character(scores=WIS17, classes=[["cleric", "Death Domain", 8]], routine="one_handed"), 8)
    assert melee.once_per_turn_die_mod_list == ["1d8"] and melee.once_per_turn_damage_type == "necrotic"
    # A caster only gets it on the bonus action crossbow shot, never on a spell
    caster, _ = compile_character(reaper(toggles={"offhand_crossbow": True}), 12)
    assert once_per_turn_pools(caster) and all(not a.once_per_turn_eligible for a in caster.attacks if a.type == "spell")
    assert not once_per_turn_pools(compile_character(reaper(), 12)[0])
