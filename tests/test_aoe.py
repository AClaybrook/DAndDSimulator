""" Damage against a group of enemies: single target attacks hit one, areas and auras up to their size """
from bg3.character import Bg3Character, compile_character
from bg3.presets import PRESETS
from bg3.build import compile_build
from computations.analytic import expected_damage_per_round, expected_damage_vs_enemies
from game_data import enemy_from_monster, spell_attacks

ENEMY = enemy_from_monster("Mind Flayer")

def test_single_target_damage_doesnt_spill_over():
    fighter = compile_build(PRESETS["Lae'zel (Champion, GWM)"], "1")
    one = expected_damage_vs_enemies(fighter, ENEMY, 3, 1)
    assert one == expected_damage_per_round(fighter, ENEMY, 3)
    assert all(expected_damage_vs_enemies(fighter, ENEMY, 3, n) == one for n in (2, 3, 4))

def test_area_spells_hit_up_to_their_size():
    assert spell_attacks("Fireball", slot_level=3)[0].targets == 4 and spell_attacks("Fire Bolt")[0].targets == 1
    wizard = compile_build(PRESETS["Evocation Wizard (Fireball, then Fire Bolt)"], "1")
    by_count = [expected_damage_vs_enemies(wizard, ENEMY, 3, n) for n in (1, 2, 3, 4, 5)]
    assert by_count[0] < by_count[1] < by_count[2] < by_count[3] == by_count[4] # Fireball catches up to 4

def test_spirit_guardians_aura_and_horde_breaker():
    cleric = Bg3Character(classes=[["cleric", "Light Domain", 5]], routine="cantrip", cantrip="Sacred Flame", spell="Spirit Guardians")
    c, notes = compile_character(cleric, 5)
    aura = next(a for a in c.attacks if a.name == "Spirit Guardians (aura)")
    assert aura.targets == 3 and aura.uses_per_fight > 0 and not notes
    assert any(a.name == "Sacred Flame" and not a.fallback_for for a in c.attacks) # The cantrip is still cast every round
    assert expected_damage_vs_enemies(c, ENEMY, 3, 3) > expected_damage_vs_enemies(c, ENEMY, 3, 1) + 10
    hunter = Bg3Character(classes=[["ranger", "Hunter", 5]], routine="ranged", toggles={"horde_breaker": True})
    h, _ = compile_character(hunter, 5)
    assert any(a.min_enemies == 2 for a in h.attacks)
    assert expected_damage_vs_enemies(h, ENEMY, 3, 2) > expected_damage_vs_enemies(h, ENEMY, 3, 1)

def test_planner_layout_builds():
    from components.bg3_planner import planner
    layout = str(planner())
    assert "bg3-enemies" in layout and "bg3-kit" in layout and "bg3-variants" in layout
