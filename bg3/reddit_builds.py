""" Rough planner versions of starred builds from the Reddit index (docs/reddit_build_index.md), for the leaderboard.

    The index only has each build's classes, subclasses and key items, so ability scores, feats and the rest of the gear here are
    reasonable guesses (point buy for the main stat, the build's signature feat, key items in the act they're found). Read their numbers
    as approximate; the source post is in each build's roles field. Builds whose core mechanic isn't modelled yet (Bowsinger's control,
    Cryogenicist's Encrusted with Frost) are left out """
from bg3.build import Bg3Build
from bg3.presets import BRAWLER, CHARISMA, DEXTERITY, STRENGTH, custom

# Two 15s for builds that attack with one stat and cast with another
DEX_CHA = {"strength": 8, "dexterity": 15, "constitution": 14, "intelligence": 8, "wisdom": 10, "charisma": 15}
STR_CHA = {"strength": 15, "dexterity": 8, "constitution": 14, "intelligence": 8, "wisdom": 10, "charisma": 15}
DEX_WIS = {"strength": 8, "dexterity": 15, "constitution": 14, "intelligence": 8, "wisdom": 15, "charisma": 10}

def reddit(name, post, equipment, *args, **kwargs):
    build = Bg3Build(name, "fighter_gwm", equipment=equipment, **custom(name.split(" (")[0], *args, **kwargs))
    build.roles = [f"Approximation of {post}"]
    return build

REDDIT = {b.name: b for b in [
    reddit("The Waterdeep Brat (EK 11 / Hexblade 1)", "https://www.reddit.com/r/BG3Builds/comments/1m0uk9b/", {},
           DEXTERITY, {"dexterity": 2, "constitution": 1}, [["warlock", "The Hexblade", 1], ["fighter", "Eldritch Knight", 11]],
           ["dexterity+2", "Savage Attacker", "dexterity+1,constitution+1", "constitution+2"], "shadow_blade", race="Half-Elf",
           toggles={"booming_blade": True}),
    reddit("Bhaalist Hexblade Battle Master (BM 11 / Hexblade 1)", "https://www.reddit.com/r/BG3Builds/comments/1kcrlpq/",
           {"2": {"melee_main": "bg3:shar_s_spear_of_evening"}, "3": {"armour": "bg3:bhaalist_armour"}},
           CHARISMA, {"charisma": 2, "constitution": 1}, [["warlock", "The Hexblade", 1], ["fighter", "Battle Master", 11]],
           ["charisma+2", "Savage Attacker", "charisma+1,constitution+1", "constitution+2"], "one_handed", ["Dueling"], race="Githyanki",
           toggles={"booming_blade": True}),
    reddit("Shadow Blade Fiend Warlock (Warlock 9 / BM 3)", "https://www.reddit.com/r/BG3Builds/comments/1p4fdo4/", {},
           DEX_CHA, {"dexterity": 2, "charisma": 1}, [["warlock", "The Fiend", 9], ["fighter", "Battle Master", 3]],
           ["dexterity+2", "charisma+2", "Savage Attacker"], "shadow_blade", race="Half-Elf", cantrip="Eldritch Blast",
           toggles={"booming_blade": True}),
    reddit("Booming Smite Assassin (Oathbreaker 5 / Assassin 3 / Sorcerer 4)", "https://www.reddit.com/r/BG3Builds/comments/1kpv4yl/",
           {"1": {"helmet": "bg3:diadem_of_arcane_synergy"}, "3": {"armour": "bg3:bhaalist_armour", "melee_main": "bg3:dolor_amarus"}},
           DEX_CHA, {"dexterity": 2, "charisma": 1}, [["paladin", "Oathbreaker", 5], ["rogue", "Assassin", 3], ["sorcerer", "Draconic Bloodline", 4]],
           ["dexterity+2", "charisma+2"], "one_handed", ["Dueling"], race="Half-Elf", toggles={"booming_blade": True}),
    reddit("Fire Marshal (Oathbreaker 7 / Fiend 5)", "https://www.reddit.com/r/BG3Builds/comments/1mxem4i/",
           {"1": {"melee_main": "bg3:everburn_blade"}, "2": {"gloves": "bg3:flawed_helldusk_gloves", "ring_1": "bg3:callous_glow_ring"}},
           STR_CHA, {"strength": 2, "charisma": 1}, [["paladin", "Oathbreaker", 7], ["warlock", "The Fiend", 5]],
           ["Great Weapon Master", "strength+2", "charisma+2"], "two_handed", ["Great Weapon Fighting"], race="Half-Orc"),
    reddit("Radiant Protector (Crown Paladin 12)", "https://www.reddit.com/r/BG3Builds/comments/1kilwey/",
           {"1": {"melee_main": "bg3:sword_of_justice"}, "3": {"ring_1": "bg3:band_of_the_mystic_scoundrel"}},
           STR_CHA, {"strength": 2, "charisma": 1}, [["paladin", "Oath of the Crown", 12]],
           ["strength+2", "charisma+2", "Great Weapon Master"], "two_handed", ["Great Weapon Fighting"], race="Human"),
    reddit("Filthy Harold Hunter (Hunter 11 / War Cleric 1)", "https://www.reddit.com/r/BG3Builds/comments/1u4pi9h/",
           {"1": {"gloves": "bg3:gloves_of_archery", "ranged_main": "bg3:titanstring_bow"}, "2": {"helmet": "bg3:marksmanship_hat"}},
           DEXTERITY, {"dexterity": 2, "constitution": 1}, [["ranger", "Hunter", 11], ["cleric", "War Domain", 1]],
           ["Sharpshooter", "dexterity+2", "dexterity+1,constitution+1"], "ranged", ["Archery"], race="Wood Elf"),
    reddit("Drunken Master Thief (Drunken Master 8 / Thief 4)", "https://www.reddit.com/r/BG3Builds/comments/1k69s59/",
           {"2": {"gloves": "bg3:gloves_of_crushing"}},
           BRAWLER, {"strength": 2, "dexterity": 1}, [["monk", "Way of the Drunken Master", 8], ["rogue", "Thief", 4]],
           ["Tavern Brawler", "strength+2", "dexterity+2"], "unarmed", race="Half-Orc"),
    reddit("Tempest Monk (Open Hand 6 / Tempest Cleric 6)", "https://www.reddit.com/r/BG3Builds/comments/1l87ee8/",
           {"1": {"boots": "bg3:the_watersparkers", "ring_1": "bg3:the_sparkswall"}},
           DEX_WIS, {"dexterity": 2, "wisdom": 1}, [["monk", "Way of the Open Hand", 6], ["cleric", "Tempest Domain", 6]],
           ["dexterity+2", "wisdom+2", "dexterity+1,wisdom+1"], "unarmed", race="Wood Elf"),
    reddit("Storm Bard (Storm Sorcerer 6 / Swords Bard 6)", "https://www.reddit.com/r/BG3Builds/comments/1qg7k9j/",
           {"2": {"helmet": "bg3:helmet_of_arcane_acuity"}},
           DEX_CHA, {"dexterity": 2, "charisma": 1}, [["bard", "College of Swords", 6], ["sorcerer", "Storm Sorcery", 6]],
           ["dexterity+2", "charisma+2"], "one_handed", ["Dueling"], race="Half-Elf", toggles={"booming_blade": True}),
    reddit("Thief Monoclass (Thief 12)", "https://www.reddit.com/r/BG3Builds/comments/1veef5a/",
           {"1": {"melee_main": "bg3:practice_sword", "melee_off": "bg3:knife_of_the_undermountain_king"}, "3": {"helmet": "bg3:helmet_of_grit"}},
           DEXTERITY, {"dexterity": 2, "constitution": 1}, [["rogue", "Thief", 12]],
           ["dexterity+2", "Dual Wielder", "dexterity+1,constitution+1", "Savage Attacker"], "dual_wield", race="Halfling"),
    reddit("Throwing Berserker GWM (Berserker 12)", "docs/reddit_build_index.md (throwing builds)",
           {"1": {"melee_main": "bg3:returning_pike", "ring_1": "bg3:ring_of_flinging"}, "3": {"gloves": "bg3:gauntlets_of_hill_giant_strength"}},
           STRENGTH, {"strength": 2, "constitution": 1}, [["barbarian", "Berserker", 12]],
           ["Tavern Brawler", "strength+2", "Savage Attacker"], "thrown", race="Half-Orc"),
]}
