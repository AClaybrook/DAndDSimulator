""" Checks against damage values calculated independently of this project """
import json
from pathlib import Path
import pytest

from computations.analytic import expected_by_attack, expected_damage_per_round
from computations.models import Character, Enemy
from computations.numerical_simulation import simulate_rounds_from_characters, set_seed

PRESETS = Path(__file__).parent / "character_presets"

# Level 6 Oath of Vengeance Paladin (GWM, Bless, smites, Vow of Enmity advantage) damage per round by armor class, from
# https://docs.google.com/spreadsheets/d/14WlZE_UKwn3Vhv4i8ewVOc-f2-A7tMW_VRum_p3YNHQ/edit#gid=151780215
PALADIN_DPR_VS_AC = {
    10: 86.356875, 11: 83.701875, 12: 80.604375, 13: 77.064375, 14: 73.081875, 15: 68.656875, 16: 63.789375, 17: 58.479375,
    18: 52.72687, 19: 46.531875, 20: 39.894375, 21: 32.814375, 22: 25.291875, 23: 19.4840625, 24: 15.5015625, 25: 13.455,
}

@pytest.fixture(name="paladin")
def fixture_paladin():
    """ Saved by an older version of the app, so this also checks old json files still load """
    with open(PRESETS / "oath_of_vengeance_L1_L6.json", encoding="utf-8") as f:
        return Character.from_dict(json.load(f)[5])

@pytest.mark.parametrize("armor_class, dpr", PALADIN_DPR_VS_AC.items())
def test_paladin_matches_spreadsheet(paladin, armor_class, dpr):
    assert expected_damage_per_round(paladin, Enemy(armor_class=armor_class)) == pytest.approx(dpr, abs=1e-4)

def test_paladin_simulation_matches_spreadsheet(paladin):
    _, df_by_rounds, _ = simulate_rounds_from_characters([paladin], Enemy(armor_class=10), num_rounds=100_000, save_memory=True, rng=set_seed(1))
    assert df_by_rounds[0]["Damage"].mean() == pytest.approx(PALADIN_DPR_VS_AC[10], abs=0.3)

def test_paladin_attacks(paladin):
    halberd, _, blunt_end = expected_by_attack(paladin, Enemy(armor_class=10))
    assert halberd == pytest.approx(31.3325) and blunt_end == pytest.approx(23.691875)
