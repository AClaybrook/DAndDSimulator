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

def test_fighter_progression():
    assert len(build_character("fighter_gwm", 4).attacks) == 1
    assert len(build_character("fighter_gwm", 5).attacks) == 2
    assert len(build_character("fighter_gwm", 11).attacks) == 3
    assert len(build_character("fighter_gwm", 20, "5e").attacks) == 4
    assert build_character("fighter_gwm", 20).level == 12 # BG3 caps at level 12
    c = build_character("fighter_gwm", 8)
    assert c.GWM and c.strength == 20 and c.crit_on == 19

def test_character_at_level():
    preset = build_character("fighter_gwm", 3)
    preset.name = "Renamed"
    rebuilt = character_at_level(preset, 11)
    assert rebuilt.name == "Renamed" and len(rebuilt.attacks) == 3 and rebuilt.preset == "fighter_gwm:bg3"
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
    assert [a.name for a in rebuilt.attacks] == ["Greatsword"] * 3 + ["Handaxe"]
    # The new third greatsword gets the edits of the last edited copy
    assert all(a.weapon_enhancement == 1 for a in rebuilt.attacks[:3])
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
