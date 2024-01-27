""" Tests analytic computations match the numerical simulations """
import json
from computations.analytic import approx_analytic_dpr
from computations.models import Character, Enemy, Attack
from computations.numerical_simulation import simulate_rounds_from_characters, simulate_rounds_from_characters_multi_acs
import pytest

def character_from_json(filepath):
    """ Loads a character from a json file """
    with open(filepath, 'r', encoding='utf-8') as f:
        characters_list = json.load(f)
    characters = []
    for _, c in enumerate(characters_list):
        attacks = c.pop("attacks")
        attacks_python = [Attack(**attack) for attack in attacks]
        characters.append(Character(attacks=attacks_python, **c))
    return characters

def test_oath_of_vengeance_L1_L6():
    """ Tests oath of vengeance L1-L6 gives expected results"""
    filepath = 'tests/character_presets/oath_of_vengeance_L1_L6.json'
    characters = character_from_json(filepath)
    i = 5 # only test last character for this file, which is a level 6 paladin
    characters = [characters[i]]
    enemy = Enemy(armor_class=10)
    _, df_by_rounds, dfs_by_attack = simulate_rounds_from_characters(characters, enemy, num_rounds=100000, save_memory=True)

    tol = 0.2 # There are can be some variation in the numerical simulations, +-0.2 over 100,000 rounds is reasonable

    df_round = df_by_rounds[0]
    assert df_round['Damage'].mean() == pytest.approx(86.358875, abs=tol)

    # Attack checks
    df_attack = dfs_by_attack[0]
    halberd = df_attack["Damage"]['Halberd (L2 Divine Smite)']['mean']
    halberd_blunt = df_attack["Damage"]['Halberd (Blunt End L1 Divine Smite)']['mean']
    assert halberd == pytest.approx(31.3335,abs=tol)
    assert halberd_blunt== pytest.approx(23.6918,abs=tol)

    c_dpr = approx_analytic_dpr(characters, enemy)
    assert c_dpr['Oath of Vengeance Paladin L6']['total'] == pytest.approx(86.358875, rel=0.01) # Within 1%

    # Check values are a reasonable match for all armor classes
    # Values confirmed from here: https://docs.google.com/spreadsheets/d/14WlZE_UKwn3Vhv4i8ewVOc-f2-A7tMW_VRum_p3YNHQ/edit#gid=151780215
    dpr_vs_ac = {
        10: 86.356875,
        11: 83.701875,
        12: 80.604375,
        13: 77.064375,
        14: 73.081875,
        15: 68.656875,
        16: 63.789375,
        17: 58.479375,
        18: 52.72687,
        19: 46.531875,
        20: 39.894375,
        21: 32.814375,
        22: 25.291875,
        23: 19.4840625,
        24: 15.5015625,
        25: 13.455
        }

    df = simulate_rounds_from_characters_multi_acs(characters, enemy, num_rounds=100_000, by_round=True)
    df = df.loc[df['Character'] == 'Oath of Vengeance Paladin L6',:].sort_values(by='Armor Class')
    dpr_vs_ac_res = dict(zip(df['Armor Class'].values, df['mean'].values))

    for ac, dpr in dpr_vs_ac.items():
        assert dpr_vs_ac_res[ac] == pytest.approx(dpr, abs=tol)

dpa_l9_ac10 = {
    "Halberd (Blunt End)" : 14.910625,
    "Halberd (L2 Divine Smite)": 32.1325,
    "Halberd (Unleashed Incarnation L1 Smite)": 27.435625,
    "Halberd (L1 Divine Smite Action Surge)": 27.435625,
    "Halberd (Unleashed Incarnation)": 18.041875,
}
