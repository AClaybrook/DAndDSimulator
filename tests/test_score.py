""" The all round score """
from bg3.kits import variant_build
from bg3.presets import PRESETS, examples
from bg3.score import WEIGHTS, hit_points, score
from game_data import enemy_from_monster

ENEMY = enemy_from_monster("Mind Flayer")

def test_score_parts_and_range():
    result = score(examples()["1. The Godblade"], "1", ENEMY)
    assert set(result.parts) == set(WEIGHTS) and 0 < result.total < 100
    assert all(0 <= v <= 100 for v in result.parts.values())
    assert sum(WEIGHTS.values()) == 100

def test_high_ac_godblade_scores_higher_than_damage_only():
    godblade = examples()["1. The Godblade"]
    high_ac = variant_build(godblade, {"kit": "tank_unarmoured", "buffs": ["mage_armour"]})
    base, tank = score(godblade, "1", ENEMY), score(high_ac, "1", ENEMY)
    assert tank.parts["damage"] < base.parts["damage"] and tank.parts["defence"] > base.parts["defence"]
    assert tank.total > base.total

def test_hit_points_and_support():
    godblade = examples()["1. The Godblade"] # Wizard 5, CON 14
    assert hit_points(godblade, "1") == 6 + 2 + 4 * (4 + 2)
    cleric, fighter = examples()["4. Deathreaper"], PRESETS["Lae'zel (Champion, GWM)"]
    assert score(cleric, "1", ENEMY).parts["support"] > score(fighter, "1", ENEMY).parts["support"]
    # Weights change the ranking, not the parts
    damage_only = score(fighter, "1", ENEMY, weights={"damage": 1})
    assert abs(damage_only.total - damage_only.parts["damage"]) < 1
