""" Example BG3 builds with gear for each act, from the Patch 8 item data.
    The default party shares a ring on purpose, so the conflict report has something to show """
from bg3.build import Bg3Build

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
]}

DEFAULT_PARTY = ["Lae'zel (Champion, GWM)", "Karlach (Berserker)", "Astarion (Assassin, dual wield)", "Gale (Evoker)"]
