""" Party synergies, roles and the party fight """
import pytest

from bg3.build import Bg3Build, compile_build
from bg3.presets import PRESETS, custom, CHARISMA, DEXTERITY
from bg3.roles import party_roles
from bg3 import synergy
from computations.analytic import expected_damage_per_round
from computations.models import Enemy

ENEMY = Enemy(armor_class=15, hit_points=200)
BLADE = Bg3Build("Hexblade", "warlock_hexblade", **custom("Hexblade", CHARISMA, {"charisma": 2, "constitution": 1}, [["warlock", "The Hexblade", 12]],
                                                          ["charisma+2"], "shadow_blade"), carried=["Resonance Stone"])
ARCHER = PRESETS["Arcane Archer Fighter (Patch 8)"]
ROGUE = Bg3Build("Rogue", "rogue_dual_wield", **custom("Rogue", DEXTERITY, {"dexterity": 2, "constitution": 1}, [["rogue", "Thief", 12]], [], "ranged"))

def test_resonance_stone_doubles_psychic_damage():
    assert synergy.default_active([BLADE, ARCHER], 2) == ["resonance_stone"]
    assert "resonance_stone" not in synergy.available([BLADE], 1)
    [(_, plain, boosted)] = synergy.party_damage([BLADE], 2, ENEMY, 4, ["resonance_stone"])
    characters, enemy = synergy.apply([BLADE], 2, ENEMY, ["resonance_stone"])
    assert "psychic" in enemy.vulnerabilities and "psychic" not in ENEMY.vulnerabilities
    assert boosted > 1.5 * plain and boosted == pytest.approx(expected_damage_per_round(characters[0], enemy, 4))

def test_darkness_and_paralysed():
    available = synergy.available([BLADE, ARCHER], 3)
    assert "darkness" in available and synergy.sees_in_darkness(BLADE, 3) and not synergy.sees_in_darkness(ARCHER, 3)
    characters, _ = synergy.apply([BLADE, ARCHER], 3, ENEMY, ["darkness"])
    assert all(a.advantage for a in characters[0].attacks) and not any(a.advantage for a in characters[1].attacks)
    characters, enemy = synergy.apply([BLADE], 3, ENEMY, ["paralysed"])
    assert all(a.hits_crit for a in characters[0].attacks if a.type == "weapon (melee)") and enemy.dexterity_save < -50

def test_party_fight():
    result = synergy.simulate_party_fight([BLADE, ARCHER], 2, ENEMY, 4, [])
    assert result["down_by_round"] == sorted(result["down_by_round"]) and result["rounds"] == 8
    assert sum(result["share"].values()) == pytest.approx(1)
    faster = synergy.simulate_party_fight([BLADE, ARCHER], 2, ENEMY, 4, ["resonance_stone"])
    assert sum(faster["down_by_round"]) > sum(result["down_by_round"])

def test_roles():
    rows, missing, _ = party_roles([BLADE, ARCHER], 2)
    roles = dict(rows)
    assert {"frontline", "face", "control"} <= set(roles["Hexblade"]) and "ranged" in roles["Arcane Archer Fighter (Patch 8)"]
    assert "skills" in missing and "healer" in missing
    _, missing, overlaps = party_roles([BLADE, ARCHER, ROGUE, PRESETS["Karlach (Berserker)"]], 2)
    assert "skills" not in missing and not overlaps
    assert compile_build(BLADE, 2).attacks[0].name.startswith("Shadow Blade")
