""" Characters must survive the trip to the browser (JSON) and back unchanged, and bad values must be named before simulating """
import json
from pathlib import Path
import pytest

from api.validation import validation_errors
from computations.models import Attack, Character, Enemy
from game_data import enemy_from_monster
from game_data.classes import BUILDS, build_character

TEST_FILES = Path(__file__).parent / "fixtures"

def round_trip(character):
    return Character.from_dict(json.loads(json.dumps(character.to_dict())))

@pytest.mark.parametrize("key", BUILDS)
def test_character_round_trip(key):
    character = build_character(key, 11)
    assert round_trip(character) == character

def test_enemy_round_trip():
    lich = enemy_from_monster("Lich")
    parsed = Enemy.from_dict(json.loads(json.dumps(lich.to_dict())))
    for field in ["name", "armor_class", "hit_points", "resistances", "immunities", "intelligence_save"]:
        assert getattr(parsed, field) == getattr(lich, field)
    assert parsed.saving_throw_modifier("strength") == lich.saving_throw_modifier("strength")

@pytest.mark.parametrize("filename", ["characters.json", "characters_skip.json"])
def test_import_older_exports(filename):
    with open(TEST_FILES / filename, encoding="utf-8") as f:
        data = json.load(f)
    characters = []
    for c in data:
        try:
            characters.append(Character.from_dict(c))
        except Exception: # characters_skip.json purposely has a broken character
            break
    assert characters and all(c.attacks for c in characters)

def test_validation_errors_name_the_field():
    attack = {"name": "Greatsword", "damage": "2d", "crit_on": None, "bonus_damage_die_mod_list": ["1d6", "x"]}
    problems = validation_errors({"strength": None, "level": 5, "bonus_attack_die_mod_list": ["1d4"]}, [attack])
    assert "Strength is empty" in problems
    assert "attack 'Greatsword': Crit on is empty" in problems
    assert any("Damage '2d'" in p for p in problems) and any("Bonus damage" in p for p in problems)
    assert validation_errors({"level": 5}, []) == ["it has no attacks"]
    good = build_character("fighter_gwm", 5).to_dict()
    assert validation_errors(good, good["attacks"]) == []

def test_typed_extra_damage_round_trip_and_validation():
    character = Character(name="Flame", attacks=[Attack(name="Flaming Sword", extra_damage_list=["1d4 fire", "2 acid"])])
    assert round_trip(character) == character
    assert validation_errors({}, [{"name": "x", "extra_damage_list": ["1d4 fyre"]}])
    assert not validation_errors({}, [{"name": "x", "extra_damage_list": ["1d4 fire", "2"]}])

def test_histograms_are_binned():
    """ Every round is plotted, but only bar heights and box statistics are sent to the browser """
    import numpy as np
    import pandas as pd
    from api.plots import MAX_BINS, generate_damage_per_attack_histogram, generate_histogram, generate_plot_data
    rng = np.random.default_rng(1)
    small, large = rng.integers(0, 30, 1_000_000), rng.integers(0, 1000, 1_000_000)
    fig = generate_plot_data([Character(name="A"), Character(name="B")], [pd.DataFrame({"Damage": small}), pd.DataFrame({"Damage": large})], title="DPR")
    bars = {t.name: t for t in fig.data if t.type == "bar"}
    boxes = {t.name: t for t in fig.data if t.type == "box"}
    assert sum(bars["A"].y) == pytest.approx(100) and sum(bars["B"].y) == pytest.approx(100)
    assert bars["A"].width == bars["B"].width == 5 and len(bars["B"].x) <= MAX_BINS # 1000 damage values in bins of 5
    assert boxes["A"].median[0] == np.median(small) and boxes["B"].mean[0] == pytest.approx(large.mean())
    assert len(fig.to_json()) < 60_000
    df = pd.DataFrame({"Damage": small, "Attack": np.where(small % 2, "Slash", "Stab")})
    fig = generate_damage_per_attack_histogram([Character(name="A")], [df])
    plain = [t for t in fig.data if t.type != "scatter"]
    assert {t.name for t in plain} == {"A-Slash", "A-Stab"} and len({t.marker.color for t in plain}) == 1
    # A smooth fit over each histogram, in the same units (its points add up to about the bars' 100%)
    fits = {t.name: t for t in fig.data if t.type == "scatter"}
    assert set(fits) == {"A-Slash (fit)", "A-Stab (fit)"} and all("mean" in t.hovertemplate for t in fits.values())
    assert sum(next(t for t in generate_histogram({"A": large}).data if t.type == "scatter").y) == pytest.approx(100, abs=3)

def test_planner_characters_survive_json():
    """ Characters the BG3 planner sends to the simulator keep everything, i.e. BG3 Savage Attacker and rage level """
    from bg3.build import compile_build
    from bg3.presets import PRESETS
    for build in PRESETS.values():
        for act in "123":
            character = compile_build(build, act)
            assert round_trip(character) == character, (build.name, act)
