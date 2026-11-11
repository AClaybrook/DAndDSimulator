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
    pair = import_text("Build 60: Pair\nClass Split: 12 Thief Rogue.\nAct 2: Dual Hand Crossbows.\n")[0]
    assert pair["build"]["equipment"]["2"] == {"ranged_main": "bg3:hand_crossbow_1", "ranged_off": "bg3:hand_crossbow_1"} and not pair["unmatched"]
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

def test_free_text_fighting_style_and_phalar_buffs():
    from bg3.buffs import BUFFS
    from bg3.doc_import import import_text
    build = import_text("Build 41: Archer\nClass Split: 12 Arcane Archer Fighter.\nLevels 1-11: Archery Fighting Style, Arcane Shot\n")[0]
    assert build["build"]["character"]["fighting_styles"] == ["Archery"]
    assert not BUFFS["phalar_sing"].concentration and BUFFS["phalar_shriek"].effects[0].value == "1d4 thunder"

REAPER = """Build 50: Reaper
Class Split: 8 Death Domain Cleric / 2 Necromancy Wizard / 2 Circle of the Spores Druid.
Starting Ability Scores: STR 8, DEX 14, CON 14, INT 10, WIS 17, CHA 8.
Spells: Spirit Guardians and Spiritual Weapon every fight, Toll the Dead, then Circle of Death, Dethrone, Inflict Wounds or Thorn Whip.
Act 3: Staff of Cherished Necromancy (Main Hand), Amulet of the Devout, Armour of Agility, Ne'er Misser + Hellfire Hand Crossbow.
"""

def test_a_caster_with_a_staff_casts_and_gets_play_modes():
    from bg3.kits import variant_build
    entry = import_text(REAPER)[0]
    build = Bg3Build.from_dict(entry["build"])
    character = build.character
    # A full caster holding a staff casts its cantrip; Booming Blade only when the write-up asks for it
    assert character["routine"] == "cantrip" and character["cantrip"] == "Toll the Dead" and character["spell"] == "Spirit Guardians"
    assert character["toggles"] == {"spiritual_weapon": True, "booming_blade": False, "offhand_crossbow": True}
    # The second hand crossbow goes in the off hand, for the bonus action shot
    assert build.equipment["3"]["ranged_main"] == "bg3:ne_er_misser" and build.equipment["3"]["ranged_off"] == "bg3:hellfire_hand_crossbow"
    assert entry["unmatched"] == []
    # The other spells it names are play modes: levelled ones keep Spirit Guardians up, necromancy turns on the staff's free cast
    modes = {v["name"]: v for v in build.variants}
    assert list(modes) == ["Circle of Death", "Dethrone, once a day", "Inflict Wounds in melee", "Thorn Whip"]
    assert modes["Circle of Death"] == {"name": "Circle of Death", "character": {"spell": "Circle of Death"}, "toggles": {"spirit_guardians": True},
                                        "conditions": ["bg3:staff_of_cherished_necromancy#2"]}
    assert "conditions" not in modes["Dethrone, once a day"] and modes["Thorn Whip"] == {"name": "Thorn Whip", "character": {"cantrip": "Thorn Whip"}}
    main = {a.name: a for a in compile_build(build, "3").attacks}
    assert {"Spirit Guardians (aura)", "Spiritual Weapon", "Toll the Dead", "Hellfire Hand Crossbow (Offhand)", "Halo of Spores"} <= set(main)
    circle = {a.name: a for a in compile_build(variant_build(build, modes["Circle of Death"]), "3").attacks}
    assert circle["Circle of Death"].uses_per_fight == 1.25 and "Spirit Guardians (aura)" in circle # Its slot, and Life Essence's free cast
    assert "Thorn Whip (Touch of Death)" in {a.name for a in compile_build(variant_build(build, modes["Thorn Whip"]), "3").attacks}

def test_hags_hair_respec_note_and_conditions_always_met():
    text = FREE_TEXT.replace("Level 3 (Wizard 3)", "Level 12: Respec at 12 to take Paladin at Level 1 so scrolls/items scale with INT.\nLevel 1: Booming Blade.\nLevel 3 (Wizard 3)") \
        .replace("Caustic Band, Crusher's Ring", "Diadem of Arcane Synergy, Strange Conduit Ring")
    godblade, deadeye = import_text(text + "Starting Ability Scores: STR 8, DEX 17, CON 14, INT 16, WIS 10, CHA 8 (reaches 20 DEX / 16 INT).\n"
                                    "Feats: Sharpshooter, ASI (+2 DEX to 20), Alert.\n")
    character = godblade["build"]["character"]
    assert character["boons"] == {"dexterity": 1} and character["toggles"]["item_casting"] == "intelligence"
    # Shadow Blade is concentration and Booming Blade a cantrip with a condition: the ring's and the diadem's effects are on
    assert set(godblade["build"]["conditions"]) == {"bg3:diadem_of_arcane_synergy#0", "bg3:strange_conduit_ring#0"}
    blade = compile_build(Bg3Build.from_dict(godblade["build"]), "1").attacks[0]
    assert "1d4 psychic" in blade.extra_damage_list and blade.bonus_damage_die_mod_list[-1] == "3" # INT 16
    # 17 + 2 from the feat is 19: the write-up reaches 20, so the hair is assumed and noted
    assert deadeye["build"]["character"]["boons"] == {"dexterity": 1} and any("Auntie Ethel's Hair assumed" in n for n in deadeye["notes"])

def test_respec_permanent_buffs_and_metamagic_from_the_structured_format():
    """ A Respec line gives the class split at an act when levelling in order doesn't; Permanent buffs gives Auntie Ethel's Hair;
        'Twinned Haste' is Haste; a build written twice is read from its last section; a melee Sorcerer quickens Booming Blade """
    from bg3.build import Bg3Build, compile_build
    from bg3.character import Bg3Character, class_levels
    from bg3.doc_import import import_text
    text = """Build 1: Old write-up (12 Fighter)
Classes: 12 Champion Fighter
Build 1: Metamagic Blade
Classes: 4 Draconic Bloodline Sorcerer / 2 Oath of the Crown Paladin / 6 Bladesinging Wizard
Level order: Sorcerer 1, Paladin 1-2, Wizard 1-6, Sorcerer 2-4
Respec: Act 1 = 5 Bladesinging Wizard; Act 2 = 6 Bladesinging Wizard / 2 Oath of the Crown Paladin; Act 3 = 1 Draconic Bloodline Sorcerer / 2 Oath of the Crown Paladin / 6 Bladesinging Wizard / 3 Draconic Bloodline Sorcerer
Abilities: STR 8, DEX 15, CON 14, INT 15, WIS 10, CHA 8 | +2 DEX, +1 INT
Feats: +2 DEX, Savage Attacker
Routine: shadow_blade
Cantrip: Booming Blade
Permanent buffs: Act 1 Auntie Ethel's Hair DEX; Act 3 Mirror of Loss DEX
Act 3 Buffs: Twinned Haste, Elixir of Bloodlust
Caveats: Wizard is the last new class added, locking item, scroll, and Illithid Spell Save DC to Intelligence.
"""
    entries = import_text(text)
    assert len(entries) == 1 and entries[0]["build"]["name"].endswith("Metamagic Blade")
    build = Bg3Build.from_dict(entries[0]["build"])
    character = Bg3Character.from_dict(build.character)
    assert [class_levels(character, lv) for lv in (5, 8, 12)] == [{"wizard": 5}, {"wizard": 6, "paladin": 2}, {"sorcerer": 4, "paladin": 2, "wizard": 6}]
    assert character.boons == {"dexterity": 1} and character.toggles["item_casting"] == "intelligence"
    assert build.buffs["3"] == ["haste", "elixir:elixir_of_bloodlust"]
    attacks = compile_build(build, "3").attacks
    quick = next(a for a in attacks if a.label == "Quickened Booming Blade")
    assert quick.action == "bonus" and quick.uses_per_fight == 0.25 and next(a for a in attacks if a.offhand).fallback_for == quick.name
    assert not [a for a in compile_build(build, "1").attacks if a.label == "Quickened Booming Blade"]
