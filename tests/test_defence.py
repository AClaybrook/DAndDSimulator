""" Armour class per character and act """
from bg3.build import Bg3Build
from bg3.character import Bg3Character
from bg3.defence import armour_class, armour_data, hit_chance
from bg3.kits import variant_build
from bg3.presets import examples

def test_armour_data_from_the_wiki():
    data = armour_data()
    assert data["bg3:adamantine_splint_armour"] == {"type": "heavy", "ac": 18}
    assert data["bg3:wooden_shield"]["bonus"] == 2 and data["bg3:ring_of_protection"]["bonus"] == 1
    assert data["bg3:wondrous_gloves"]["bonus"] == 1

def test_godblade_high_ac_stack():
    godblade = examples()["1. The Godblade"] # DEX 19, Bracers of Defence, Bladesinger 5 in Act 1
    assert armour_class(godblade, "1")[0] == 10 + 4 + 2 + 3
    buffed = variant_build(godblade, {"kit": "tank_unarmoured", "buffs": ["mage_armour", "shield_of_faith", "haste"]})
    assert armour_class(buffed, "1")[0] == 13 + 4 + 2 + 3 + 1 + 2 + 2
    off = variant_build(godblade, {"toggles": {"bladesong": False}})
    assert armour_class(off, "1")[0] == 16

def test_armour_rules():
    heavy = Bg3Build("Tank", "fighter_gwm", character=Bg3Character(classes=[["fighter", "Champion", 5]], fighting_styles=["Defence"]).to_dict(),
                     equipment={"1": {"armour": "bg3:adamantine_splint_armour", "melee_off": "bg3:wooden_shield", "melee_main": "base:longsword",
                                      "gloves": "bg3:bracers_of_defence"}})
    ac, parts = armour_class(heavy, "1")
    assert ac == 18 + 2 + 1 and not any("Bracers" in p for p, _ in parts) # Bracers need no armour and no shield
    monk = Bg3Build("Monk", "monk_open_hand", character=Bg3Character(classes=[["monk", "Way of the Open Hand", 5]], routine="unarmed",
                    scores={"strength": 8, "dexterity": 15, "constitution": 14, "intelligence": 8, "wisdom": 15, "charisma": 10},
                    bonus={"dexterity": 2, "wisdom": 1}).to_dict())
    assert armour_class(monk, "1")[0] == 10 + 3 + 3
    assert hit_chance(30, 6) == 0.05 and hit_chance(5, 6) == 0.95 and hit_chance(16, 6) == 0.55
