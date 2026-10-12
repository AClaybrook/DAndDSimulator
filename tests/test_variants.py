""" Copy with a change: each variant changes one thing """
import pytest

from components.variants import VARIANTS, make_variant
from computations.analytic import expected_damage_per_round
from computations.models import Character
from game_data import enemy_from_monster
from game_data.classes import build_character

ENEMY = enemy_from_monster("Mind Flayer")

def test_every_variant_has_a_label():
    assert all(label for label, _ in VARIANTS.values())

@pytest.mark.parametrize("key", [k for k in VARIANTS if k != "copy"])
def test_variants_are_new_named_characters(key):
    character = build_character("fighter_gwm", 4)
    variant = make_variant(character, key)
    assert variant.name.startswith(character.name + " (") and variant != character
    assert build_character("fighter_gwm", 4) == character # The original is unchanged

def test_advantage_toggles():
    character = Character(name="A")
    with_adv = make_variant(character, "advantage")
    assert with_adv.advantage and with_adv.name == "A (Adv)"
    assert not make_variant(with_adv, "advantage").advantage

def test_level_up_rebuilds_presets():
    character = build_character("fighter_gwm", 4)
    variant = make_variant(character, "level")
    assert variant.level == 5 and variant.name.endswith("(Lv 5)")
    assert len(variant.attacks) > len(character.attacks) # Extra Attack

def test_ability_score_raises_the_main_stat_up_to_20():
    character = build_character("fighter_gwm", 1) # Strength 17
    assert make_variant(character, "ability").strength == 19
    assert make_variant(make_variant(character, "ability"), "ability").strength == 20
    with pytest.raises(ValueError):
        make_variant(build_character("fighter_gwm", 12), "ability")

def test_power_attack_toggles_and_changes_damage():
    character = build_character("fighter_gwm", 8)
    without = make_variant(character, "power")
    assert not without.GWM and make_variant(without, "power").GWM
    assert expected_damage_per_round(without, ENEMY) != expected_damage_per_round(character, ENEMY)

def test_bless_adds_to_hit_once():
    character = build_character("fighter_gwm", 8)
    blessed = make_variant(character, "bless")
    assert expected_damage_per_round(blessed, ENEMY) > expected_damage_per_round(character, ENEMY)
    with pytest.raises(ValueError):
        make_variant(blessed, "bless")
