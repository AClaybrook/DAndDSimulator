""" Importing builds from a build reference document: the structured format exactly, free text best effort """
import re
from pathlib import Path

from bg3.build import Bg3Build, compile_build
from bg3.doc_import import import_text, parse_classes, split_gear, split_point_buy
from bg3.items import catalog

FREE_TEXT = """Build 1: The "Godblade" (Bladesinger Paladin)
Source: Someone
Class Split: 10 Bladesinging Wizard / 2 Oath of the Crown Paladin (Full Level 6 Spell Slot progression).
Recommended Character/Race: Custom (Wood Elf, Wood Half-Elf, Half-Orc, or Duergar) or Gale.
Starting Ability Scores: STR 8, DEX 17 (+1 Hag's Hair to 18), CON 14, INT 16, WIS 10, CHA 8.
Level 3 (Wizard 3): Spells: Shadow Blade (primary main-hand weapon), Cloud of Daggers.
Level 4 (Wizard 4): Feat 1: ASI (+2 DEX to reach 20 DEX with Hag's Hair).
Levels 7–8 (Wizard 7–8): Feat 2 (Level 8): Savage Attacker (rerolls damage dice).
Act 1: Shadow Blade (Main Hand) + Hunter's Dagger / Speedy Reply -> Knife of the Undermountain King (Off-Hand), Caustic Band, Crusher's Ring, Bow of Awareness.
Act 2: Add Cloak of Protection, Gloves of the Battlemage's Power, Strange Conduit Ring, and Resonance Stone.
Build 2: Arcane Deadeye
Class Split: 11 Arcane Archer Fighter / 1 War Domain Cleric.
Key Gear: Titanstring Bow (Acts 1–2) -> Gontr Mael or The Dead Shot (Act 3), Yuan-Ti Scale Mail -> Armour of Agility, Gloves of Archery.
"""

def test_free_text_builds():
    godblade, archer = import_text(FREE_TEXT)
    items = catalog()
    character = godblade["build"]["character"]
    assert character["classes"] == [["wizard", "Bladesinging", 10], ["paladin", "Oath of the Crown", 2]]
    # Final scores include the +2/+1, the point buy is worked back with the +2 on the main ability
    assert character["scores"]["dexterity"] == 15 and character["bonus"] == {"dexterity": 2, "intelligence": 1}
    assert character["feats"] == ["dexterity+2", "Savage Attacker"] and character["routine"] == "shadow_blade" and character["race"] == "Wood Elf"
    gear = godblade["build"]["equipment"]
    assert items[gear["1"]["melee_off"]].name == "Knife of the Undermountain King" and items[gear["1"]["ring_2"]].name == "Crusher's Ring"
    # Act 2 only lists what it adds, and the carried Resonance Stone isn't equipment
    assert {items[k].name for k in gear["2"].values()} == {"Cloak of Protection", "Gloves of Battlemage's Power", "Strange Conduit Ring"}
    assert godblade["carried"] == ["Resonance Stone"] and not godblade["unmatched"]
    # A key gear list puts each item in the act it is found, upgrades included
    assert archer["build"]["character"]["routine"] == "ranged"
    names = {act: {items[k].name for k in g.values()} for act, g in archer["build"]["equipment"].items()}
    assert "Titanstring Bow" in names["1"] and "Yuan-Ti Scale Mail" in names["2"] and {"Gontr Mael", "Armour of Agility"} <= names["3"]
    assert compile_build(Bg3Build.from_dict(godblade["build"]), 2).attacks[0].damage == "3d8"

def test_structured_format_from_the_docs():
    block = re.search(r"```\n(.*?)```", Path("docs/bg3_build_format.md").read_text(encoding="utf-8"), re.S).group(1)
    [build] = import_text(block)
    character = build["build"]["character"]
    assert character["bonus"] == {"dexterity": 2, "intelligence": 1} and character["feats"] == ["dexterity+2", "Savage Attacker", "intelligence+2"]
    assert character["fighting_styles"] == ["Defence"] and build["build"]["buffs"]["2"] == ["haste"]
    assert build["roles"] == ["frontline", "control", "support"] and "psychic" in build["themes"] and build["needs"] == ["darkness sight"]
    assert not build["unmatched"] and not build["notes"]

def test_helpers():
    assert parse_classes("4 Swashbuckler Rogue / 5 Hexblade Warlock / 3 Swarmkeeper Ranger") == \
        [["rogue", "Swashbuckler", 4], ["warlock", "The Hexblade", 5], ["ranger", "Swarmkeeper", 3]]
    assert parse_classes("8 Death Domain Cleric / 2 Necromancy Wizard / 2 Circle of the Spores Druid")[2] == ["druid", "Circle of Spores", 2]
    assert split_gear("Staff (or Other), A + B (Off-Hand), X -> Y") == [("Staff", ""), ("A", ""), ("B", "off"), ("Y", "")]
    base, bonus = split_point_buy({"strength": 8, "dexterity": 14, "constitution": 16, "intelligence": 8, "wisdom": 10, "charisma": 17}, "charisma")
    assert bonus == {"charisma": 2, "constitution": 1} and base["charisma"] == 15

def test_level_order_and_unknowns():
    from bg3.character import Bg3Character, class_levels
    from bg3.doc_import import import_text
    text = """Build 40: Dip First
Race: unknown
Classes: 11 Oath of the Crown Paladin / 1 The Hexblade Warlock
Level order: Paladin 1, Warlock 1, Paladin 2-11
Abilities: unknown
Routine: two_handed
Act 1 Gear: Main Hand = unknown; Shield = Wooden Shield
"""
    build = import_text(text)[0]
    character = Bg3Character.from_dict(build["build"]["character"])
    assert class_levels(character, 2) == {"paladin": 1, "warlock": 1} # The dip comes at level 2, not 12
    assert build["unmatched"] == [] # "unknown" is skipped, Shield is the off hand
    assert build["build"]["equipment"]["1"] == {"melee_off": "bg3:wooden_shield"}
