""" Example BG3 builds with gear for each act, from the Patch 8 item data.
    The default party shares a ring on purpose, so the conflict report has something to show """
from bg3.build import Bg3Build
from bg3.character import Bg3Character

# Point buy spreads (27 points) by main ability
STRENGTH = {"strength": 15, "dexterity": 13, "constitution": 15, "intelligence": 8, "wisdom": 12, "charisma": 8}
DEXTERITY = {"strength": 8, "dexterity": 15, "constitution": 15, "intelligence": 8, "wisdom": 14, "charisma": 10}
CHARISMA = {"strength": 8, "dexterity": 14, "constitution": 15, "intelligence": 8, "wisdom": 10, "charisma": 15}
WISDOM = {"strength": 8, "dexterity": 14, "constitution": 15, "intelligence": 8, "wisdom": 15, "charisma": 10}
INTELLIGENCE = {"strength": 8, "dexterity": 15, "constitution": 15, "intelligence": 15, "wisdom": 8, "charisma": 8}
# Tavern Brawler monks hit with Strength (added twice), unarmed strikes use the higher of Strength and Dexterity
BRAWLER = {"strength": 15, "dexterity": 15, "constitution": 14, "intelligence": 8, "wisdom": 10, "charisma": 8}

def custom(name, scores, bonus, classes, feats, routine, styles=(), race="Human", **kwargs):
    """ A custom character (bg3.character) as a planner build """
    character = Bg3Character(name=name, race=race, scores=scores, bonus=bonus, classes=classes, feats=feats, fighting_styles=list(styles),
                             routine=routine, **kwargs)
    return dict(character=character.to_dict())

PRESETS = {b.name: b for b in [
    Bg3Build("Lae'zel (Champion, GWM)", "fighter_gwm", equipment={
        "1": {"melee_main": "bg3:everburn_blade", "ring_1": "bg3:caustic_band"},
        "2": {"melee_main": "bg3:moonlight_glaive", "gloves": "bg3:dark_justiciar_gauntlets_rare", "ring_2": "bg3:callous_glow_ring"},
        "3": {"gloves": "bg3:gauntlets_of_hill_giant_strength", "helmet": "bg3:sarevok_s_horned_helmet"},
    }),
    Bg3Build("Karlach (Berserker)", "barbarian_berserker", equipment={
        "1": {"melee_main": "bg3:very_heavy_greataxe", "ring_1": "bg3:caustic_band"},
        "2": {"melee_main": "bg3:defender_greataxe", "gloves": "bg3:dark_justiciar_gauntlets_uncommon"},
        "3": {"helmet": "bg3:horns_of_the_berserker"},
    }),
    Bg3Build("Astarion (Assassin, dual wield)", "rogue_assassin", equipment={
        "1": {"melee_main": "bg3:the_baneful", "melee_off": "bg3:steelforged_sword"},
        "2": {"melee_main": "bg3:sword_of_life_stealing", "melee_off": "bg3:render_of_mind_and_body", "helmet": "bg3:covert_cowl"},
    }),
    Bg3Build("Gale (Evoker)", "wizard_fireball", equipment={
        "1": {"melee_main": "bg3:melf_s_first_staff", "amulet": "bg3:necklace_of_elemental_augmentation"},
        "2": {"armour": "bg3:robe_of_exquisite_focus"},
        "3": {"helmet": "bg3:hood_of_the_weave", "cloak": "bg3:cloak_of_the_weave", "armour": "bg3:robe_of_the_weave"},
    }),
    Bg3Build("Gloom Stalker (Archer)", "ranger_gloom_stalker", equipment={
        "1": {"gloves": "bg3:gloves_of_archery"},
        "2": {"ranged_main": "bg3:darkfire_shortbow", "helmet": "bg3:marksmanship_hat"},
    }),
    Bg3Build("Paladin (Smite)", "paladin_smite", equipment={
        "1": {"melee_main": "bg3:sword_of_justice"},
        "2": {"melee_main": "bg3:halberd_of_vigilance", "gloves": "bg3:dark_justiciar_gauntlets_uncommon"},
        "3": {"gloves": "bg3:gauntlets_of_hill_giant_strength"},
    }),
    Bg3Build("Monk (Open Hand)", "monk_open_hand", equipment={
        "1": {"gloves": "bg3:gloves_of_cinder_and_sizzle"},
        "2": {"gloves": "bg3:gloves_of_crushing"},
        "3": {"gloves": "bg3:gloves_of_soul_catching"},
    }),
    Bg3Build("Warlock (Eldritch Blast)", "warlock_eb", equipment={
        "3": {"helmet": "bg3:hood_of_the_weave", "armour": "bg3:robe_of_the_weave"},
    }),
    # Custom characters, including Patch 8 subclasses
    Bg3Build("Swashbuckler Rogue (Patch 8)", "rogue_dual_wield", equipment={
        "1": {"melee_main": "bg3:knife_of_the_undermountain_king"},
        "2": {"melee_main": "bg3:sword_of_life_stealing", "helmet": "bg3:covert_cowl"},
    }, **custom("Swashbuckler", DEXTERITY, {"dexterity": 2, "constitution": 1}, [["rogue", "Swashbuckler", 12]],
                ["dexterity+2", "dexterity+1,constitution+1", "Savage Attacker", "constitution+2"], "one_handed", race="Wood Elf")),
    Bg3Build("Path of Giants Barbarian (Patch 8)", "barbarian_berserker", equipment={
        "1": {"melee_main": "bg3:very_heavy_greataxe"},
        "2": {"gloves": "bg3:dark_justiciar_gauntlets_uncommon"},
    }, **custom("Giant Barbarian", STRENGTH, {"strength": 2, "constitution": 1}, [["barbarian", "Giant", 12]],
                ["Great Weapon Master", "strength+2", "Savage Attacker"], "two_handed", race="Half-Orc")),
    Bg3Build("Arcane Archer Fighter (Patch 8)", "fighter_archer", equipment={
        "1": {"gloves": "bg3:gloves_of_archery"},
        "2": {"ranged_main": "bg3:darkfire_shortbow", "helmet": "bg3:marksmanship_hat"},
    }, **custom("Arcane Archer", DEXTERITY, {"dexterity": 2, "constitution": 1}, [["fighter", "Arcane Archer", 12]],
                ["Sharpshooter", "dexterity+2", "dexterity+1,constitution+1", "constitution+2"], "ranged", ["Archery"], race="Wood Elf")),
    Bg3Build("Bladesinger Wizard (Patch 8)", "wizard_fireball", equipment={
        "1": {"melee_main": "bg3:sword_of_screams"},
    }, **custom("Bladesinger", INTELLIGENCE, {"intelligence": 2, "dexterity": 1}, [["wizard", "Bladesinging", 12]],
                ["dexterity+2", "dexterity+1,intelligence+1", "intelligence+2"], "one_handed", race="High Elf")),
    Bg3Build("Hexblade Warlock (Patch 8)", "warlock_hexblade", equipment={
        "1": {"melee_main": "bg3:the_baneful"},
    }, **custom("Hexblade", CHARISMA, {"charisma": 2, "constitution": 1}, [["warlock", "The Hexblade", 12]],
                ["charisma+2", "Great Weapon Master", "charisma+1,constitution+1"], "two_handed", race="Githyanki")),
    Bg3Build("Swarmkeeper Ranger (Patch 8)", "ranger_archer", equipment={
        "1": {"gloves": "bg3:gloves_of_archery"},
        "2": {"ranged_main": "bg3:darkfire_shortbow"},
    }, **custom("Swarmkeeper", DEXTERITY, {"dexterity": 2, "wisdom": 1}, [["ranger", "Swarmkeeper", 12]],
                ["Sharpshooter", "dexterity+2", "dexterity+1,constitution+1"], "ranged", ["Archery"], race="Wood Elf")),
    Bg3Build("Drunken Master Monk (Patch 8)", "monk_open_hand", equipment={
        "2": {"gloves": "bg3:gloves_of_crushing"},
    }, **custom("Drunken Master", BRAWLER, {"strength": 2, "dexterity": 1}, [["monk", "Way of the Drunken Master", 12]],
                ["Tavern Brawler", "strength+2", "dexterity+2"], "unarmed")),
    Bg3Build("Throwzerker (Giant, Tavern Brawler)", "barbarian_berserker", equipment={
        "1": {"melee_main": "bg3:returning_pike", "ring_1": "bg3:ring_of_flinging", "gloves": "bg3:gloves_of_uninhibited_kushigo"},
        "3": {"gloves": "bg3:gauntlets_of_hill_giant_strength"},
    }, **custom("Throwzerker", STRENGTH, {"strength": 2, "constitution": 1}, [["barbarian", "Giant", 12]],
                ["Tavern Brawler", "strength+2", "Savage Attacker"], "thrown", race="Half-Orc")),
    Bg3Build("Evocation Wizard (Fireball, then Fire Bolt)", "wizard_fireball", equipment={
        "1": {"melee_main": "bg3:melf_s_first_staff"},
        "2": {"armour": "bg3:robe_of_exquisite_focus"},
        "3": {"helmet": "bg3:hood_of_the_weave", "cloak": "bg3:cloak_of_the_weave", "armour": "bg3:robe_of_the_weave"},
    }, **custom("Evoker", INTELLIGENCE, {"intelligence": 2, "constitution": 1}, [["wizard", "Evocation School", 12]],
                ["intelligence+2", "intelligence+1,constitution+1", "constitution+2"], "cantrip", race="High Elf", cantrip="Fire Bolt", spell="Fireball")),
    Bg3Build("Circle of Stars Druid (Patch 8)", "wizard_fireball", equipment={
        "1": {"melee_main": "bg3:melf_s_first_staff", "gloves": "bg3:daredevil_gloves"},
        "2": {"ring_1": "bg3:callous_glow_ring"},
    }, **custom("Star Druid", WISDOM, {"wisdom": 2, "constitution": 1}, [["druid", "Circle of Stars", 12]],
                ["wisdom+2", "wisdom+1,constitution+1", "constitution+2"], "cantrip", race="Wood Elf", cantrip="Produce Flame")),
    Bg3Build("Sorlock (Warlock 2 / Sorcerer)", "sorlock", equipment={
        "3": {"helmet": "bg3:hood_of_the_weave"},
    }, **custom("Sorlock", CHARISMA, {"charisma": 2, "constitution": 1}, [["warlock", "The Fiend", 2], ["sorcerer", "Draconic Bloodline", 10]],
                ["charisma+2", "charisma+1,constitution+1"], "cantrip", cantrip="Eldritch Blast")),
]}

DEFAULT_PARTY = ["Lae'zel (Champion, GWM)", "Karlach (Berserker)", "Astarion (Assassin, dual wield)", "Gale (Evoker)"]
