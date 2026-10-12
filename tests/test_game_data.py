""" Tests for the game database and level up presets """
import pytest

from computations.models import Attack, Character, Enemy
from computations.numerical_simulation import simulate_rounds_from_characters, simulate_rounds_from_characters_by_level
from game_data import (RULESETS, attack_templates, attacks_from_template, cantrip_tier, enemy_from_preset, enemy_presets,
                       spell_attacks, weapon_attack)
from game_data.classes import BUILDS, asi_levels, build_character, character_at_level

def test_weapon_attack():
    gs = weapon_attack("Greatsword")
    assert (gs.damage, gs.two_handed, gs.heavy, gs.damage_type) == ("2d6", True, True, "slashing")
    longsword = weapon_attack("Longsword", two_handed=True)
    assert longsword.damage == "1d10" and not longsword.heavy
    assert weapon_attack("Longbow").ability_stat == "dexterity"

@pytest.mark.parametrize("ruleset, level, tier", [("bg3", 4, 1), ("bg3", 5, 2), ("bg3", 10, 3), ("5e", 10, 2), ("5e", 17, 4)])
def test_cantrip_scaling(ruleset, level, tier):
    assert cantrip_tier(level, ruleset) == tier

def test_spell_scaling():
    assert spell_attacks("Fire Bolt", character_level=10)[0].damage == "3d10"
    assert len(spell_attacks("Eldritch Blast", character_level=10, ruleset="5e")) == 2
    assert len(spell_attacks("Magic Missile", slot_level=3)) == 5
    fireball = spell_attacks("Fireball", slot_level=5)[0]
    assert fireball.damage == "10d6" and fireball.saving_throw and fireball.saving_throw_success_multiplier == 0.5
    assert spell_attacks("Disintegrate", slot_level=7)[0].damage == "13d6+40"

def test_every_template_builds():
    for _, value in attack_templates():
        attacks = attacks_from_template(value, ability_stat="dexterity", character_level=5)
        assert attacks and all(isinstance(a, Attack) for a in attacks)

def test_every_enemy_preset_builds():
    for _, value in enemy_presets():
        enemy = enemy_from_preset(value)
        assert isinstance(enemy, Enemy) and enemy.armor_class > 0 and enemy.hit_points > 0
    lich = enemy_from_preset("monster:Lich")
    assert lich.saving_throw_modifier("intelligence") == 12
    assert lich.saving_throw_modifier("strength") == 0

def test_asi_levels():
    assert asi_levels("fighter", "bg3") == [4, 6, 8, 12]
    assert asi_levels("rogue", "5e") == [4, 8, 10, 12, 16, 19]

@pytest.mark.parametrize("key", BUILDS)
@pytest.mark.parametrize("ruleset", RULESETS)
def test_builds_level_up(key, ruleset):
    max_level = RULESETS[ruleset]["max_level"]
    enemy = Enemy(armor_class=15)
    previous = None
    for level in range(1, max_level + 1):
        c = build_character(key, level, ruleset)
        assert c.level == level and c.attacks
        _, df_by_rounds, _ = simulate_rounds_from_characters([c], enemy, num_rounds=200)
        assert df_by_rounds[0]["Damage"].mean() >= 0
        if previous:
            assert len(c.attacks) >= len(previous.attacks)
        previous = c

def every_round(character):
    """ Attacks made every round, not limited per fight """
    return [a for a in character.attacks if not a.uses_per_fight]

def test_fighter_progression():
    assert len(every_round(build_character("fighter_gwm", 4))) == 1
    assert len(every_round(build_character("fighter_gwm", 5))) == 2
    assert len(every_round(build_character("fighter_gwm", 11))) == 3
    assert len(every_round(build_character("fighter_gwm", 20, "5e"))) == 4
    # Action Surge repeats the attack action once per short rest (twice from 17 in 5e)
    surge = [a for a in build_character("fighter_gwm", 11).attacks if a.uses_per_fight]
    assert len(surge) == 3 and surge[0].uses_per_fight == 0.75
    assert build_character("fighter_gwm", 1).attacks == every_round(build_character("fighter_gwm", 1))
    assert build_character("fighter_gwm", 20).level == 12 # BG3 caps at level 12
    c = build_character("fighter_gwm", 8)
    assert c.GWM and c.strength == 20 and c.crit_on == 19

def test_character_at_level():
    preset = build_character("fighter_gwm", 3)
    preset.name = "Renamed"
    rebuilt = character_at_level(preset, 11)
    assert rebuilt.name == "Renamed" and len(every_round(rebuilt)) == 3 and rebuilt.preset == "fighter_gwm:bg3"
    plain = Character(name="Plain", attacks=[weapon_attack("Greatsword")])
    assert character_at_level(plain, 9).level == 9 and len(character_at_level(plain, 9).attacks) == 1

def test_dpr_by_level_sweep():
    characters = [build_character("barbarian_berserker", 1), Character(name="Plain", strength=16, attacks=[weapon_attack("Greatsword")])]
    df = simulate_rounds_from_characters_by_level(characters, Enemy(armor_class=15), range(1, 13), character_at_level, num_rounds=2000)
    assert set(df["Level"]) == set(range(1, 13))
    barbarian = df[df["Character"] == characters[0].name].set_index("Level")["mean"]
    assert barbarian[12] > 3 * barbarian[1]
    df_attacks = simulate_rounds_from_characters_by_level(characters, Enemy(), range(1, 4), character_at_level, num_rounds=500, by_round=False)
    assert {"Character-Attack", "Level"} <= set(df_attacks.columns)

def test_level_sweep_keeps_manual_edits():
    card = build_character("fighter_gwm", 5)
    card.strength += 1 # 20 at level 5 after the edit
    card.bonus_attack_die_mod_list = ["1d4"] # Bless
    card.attacks[0].weapon_enhancement = 1
    card.attacks[1].weapon_enhancement = 1
    card.attacks.append(weapon_attack("Handaxe"))
    rebuilt = character_at_level(card, 11)
    plain = build_character("fighter_gwm", 11)
    assert rebuilt.bonus_attack_die_mod_list == ["1d4"]
    assert rebuilt.strength == min(30, plain.strength + 1)
    assert [a.name for a in every_round(rebuilt)] == ["Greatsword"] * 3 + ["Handaxe"]
    # The new third greatsword gets the edits of the last edited copy
    assert all(a.weapon_enhancement == 1 for a in every_round(rebuilt)[:3])
    assert rebuilt.GWM and rebuilt.crit_on == plain.crit_on

def test_level_sweep_keeps_deleted_attacks_deleted():
    card = build_character("rogue_dual_wield", 5)
    card.attacks = card.attacks[:1]
    assert [a.name for a in character_at_level(card, 9).attacks] == ["Shortsword"]

def test_unedited_preset_rebuilds_exactly():
    card = build_character("paladin_smite", 7)
    rebuilt = character_at_level(card, 9)
    expected = build_character("paladin_smite", 9)
    expected.name = card.name
    assert rebuilt == expected

def test_resource_limits_per_fight():
    paladin = build_character("paladin_smite", 5)
    # Paladin 5 has 4 + 2 slots, over 4 fights per long rest
    assert paladin.once_per_turn_die_mod_list == ["3d8"] and paladin.once_per_turn_uses_per_fight == 1.5
    battle_master = build_character("fighter_battle_master", 7)
    assert battle_master.once_per_turn_uses_per_fight == 3.75 # 5 superiority dice per short rest
    monk = build_character("monk_open_hand", 6)
    assert [a.name for a in monk.attacks].count("Flurry of Blows") == 1 and monk.attacks[-1].uses_per_fight == 4.5

def test_multiclass_builds():
    sorlock = build_character("sorlock", 6)
    assert sorlock.agonizing_blast and sorlock.description.endswith("Warlock 2 / Sorcerer 4")
    quickened = [a for a in sorlock.attacks if a.uses_per_fight]
    assert len(quickened) == 2 and quickened[0].uses_per_fight == 0.25 # 4 sorcery points, 3 per quickened spell in BG3
    assert len([a for a in build_character("sorlock", 6, "5e").attacks if a.uses_per_fight]) == 2
    assert not any(a.uses_per_fight for a in build_character("sorlock", 3).attacks) # No metamagic yet
    hexadin = build_character("hexadin", 6)
    assert len(hexadin.attacks) == 2 and hexadin.dueling and hexadin.crit_on == 19
    # Paladin 5: multiclass caster level 2 (3 first level slots) plus the pact slot recovering on short rests
    assert hexadin.once_per_turn_die_mod_list == ["2d8"] and hexadin.once_per_turn_uses_per_fight == 1.5
    assert not build_character("hexadin", 2).once_per_turn_die_mod_list

def test_fireball_wizard_falls_back_to_fire_bolt():
    wizard = build_character("wizard_fireball", 7)
    assert [a.name for a in wizard.attacks] == ["Fireball", "Fire Bolt"]
    # Wizard 7: 3 + 1 slots of 3rd level or higher over 4 fights
    assert wizard.attacks[0].uses_per_fight == 1 and wizard.attacks[1].fallback_for == "Fireball"
    assert build_character("wizard_fireball", 3).attacks[0].name == "Burning Hands"

def test_first_round_presets():
    assassin = build_character("rogue_assassin", 3)
    assert assassin.first_round_advantage and assassin.first_round_auto_crit
    assert not build_character("rogue_assassin", 2).first_round_auto_crit
    gloom = build_character("ranger_gloom_stalker", 5)
    ambush = [a for a in gloom.attacks if a.uses_per_fight]
    assert len(ambush) == 1 and ambush[0].bonus_damage_die_mod_list == ["1d6", "1d8"]

def test_more_multiclass_builds():
    fighter_rogue = build_character("fighter_rogue", 7)
    assert fighter_rogue.TWF and fighter_rogue.once_per_turn_die_mod_list == ["3d6"] and fighter_rogue.description.endswith("Fighter 2 / Rogue 5")
    assert sum(1 for a in fighter_rogue.attacks if a.uses_per_fight) == 1 # Action Surge
    sorcadin = build_character("sorcadin", 10)
    # Paladin 6 / Sorcerer 4: caster level 7 (4, 3, 3, 1 slots), smiting with a 4th level slot
    assert sorcadin.once_per_turn_die_mod_list == ["5d8"] and sorcadin.once_per_turn_uses_per_fight == 2.75
    assert build_character("sorcadin", 6).once_per_turn_uses_per_fight == build_character("paladin_smite", 6).once_per_turn_uses_per_fight
