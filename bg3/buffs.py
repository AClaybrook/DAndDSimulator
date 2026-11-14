""" Buffs: spells and consumables that are active during a fight, selected per act """
import json
from dataclasses import dataclass, field

from bg3.items import DATA, Effect

@dataclass
class Buff:
    key: str
    name: str
    act: int # First act it is usually available in
    effects: list[Effect] = field(default_factory=list)
    notes: str = ""
    concentration: bool = False # The caster can only keep one concentration spell up, so it takes a party member's concentration
    self_cast: bool = False # Cast by the character on themselves, i.e. Hex, rather than by another party member
    targets: int = 1 # Party members one cast can buff, i.e. 3 for Bless
    exclusive: bool = False # Elixirs that end the effect of the elixir drunk before, only one can be active
    source: str = ""
    # When it goes up: "fight" before each fight (lasts the fight; in round 1 instead it costs the action or bonus action in cost),
    # "long_rest" in camp, "combat" during the fight (its cost is in the numbers already)
    timing: str = "fight"
    cost: str = "" # The action type that casts or applies it, when the character does it themselves
    group: str = "" # Only one of a group at a time: "coating"

# When each elixir can first be had (bg3.wiki "where to find"), by the act checkpoints (End of Act 1 is level 5, Act 2 level 8, Act 3 level 12)
ELIXIR_ACT = {"elixir:elixir_of_viciousness": 2, "elixir:elixir_of_battlemage_s_power": 2, "elixir:elixir_of_cloud_giant_strength": 3}
OBTAIN = {
    "elixir:elixir_of_hill_giant_strength": "Act 1: Auntie Ethel sells 3 a long rest (Grove, then the Riverside Teahouse), Derryth in the Myconid Colony; craftable",
    "elixir:elixir_of_bloodlust": "Act 1: Cyrel (Risen Road), Derryth (Myconid Colony), Kith (Grymforge); craftable from Worg Fangs",
    "elixir:elixir_of_heroism": "Act 1: Mol (Tiefling Hideout), Talli; craftable from Pegasus Feathers",
    "elixir:elixir_of_the_colossus": "Act 1: craftable only, from Chasm Creepers (glowing purple plants along the Underdark paths), so a handful",
    "elixir:elixir_of_viciousness": "Trader stock from level 6 (Act 2), craftable from Shadowroot Sacs",
    "elixir:elixir_of_battlemage_s_power": "Trader stock from level 6 (Act 2), craftable from Gauth Eyestalks",
    "elixir:elixir_of_cloud_giant_strength": "Act 3: trader stock from level 9. Cloud Giant Fingers to craft it are rare before then, so Hill "
                                             "Giant Strength until Act 3",
}

def elixirs():
    """ Elixirs from data/buffs.json (built by build_items.py from bg3.wiki). Every elixir replaces the one drunk before (bg3.wiki),
        so they are all exclusive. Bloodlust's extra action on a kill is an estimate (bg3.items.BLOODLUST_KILLS_PER_FIGHT) """
    path = DATA / "buffs.json"
    if not path.exists():
        return []
    from bg3.items import BLOODLUST_KILLS_PER_FIGHT # pylint: disable=import-outside-toplevel
    out = []
    with open(path, encoding="utf-8") as f:
        for b in json.load(f)["buffs"]:
            effects = [Effect(**e) for e in b["effects"]]
            if b["key"] == "elixir:elixir_of_bloodlust":
                effects = [Effect("extra_action_on_kill", BLOODLUST_KILLS_PER_FIGHT)]
            notes = " ".join(x for x in (b.get("notes", ""), OBTAIN.get(b["key"], "")) if x)
            out.append(Buff(b["key"], b["name"], ELIXIR_ACT.get(b["key"], b["act"]), effects, notes, exclusive=True, source=b.get("source", ""),
                            timing="long_rest"))
    return out

# Weapon coatings (bg3.wiki Coatings): a bonus action, 10 turns (the whole fight), one at a time on a weapon set, both hands when dual
# wielding. Toxins hurt at the end of the target's next turn after a hit if it fails a Constitution save, so once a turn however many hits.
# Dipping a weapon in a fire surface is a free coating. Broodmother's Revenge's poison is a coating too, so a coating replaces it
COATING = "Bonus action, lasts 10 turns, one coating at a time (both hands when dual wielding). "
COATINGS = [
    Buff("coat:oil_of_accuracy", "Oil of Accuracy", 1, [Effect("attack_bonus", 2, applies_to="weapon")], COATING + "+2 to hit", cost="bonus", group="coating"),
    Buff("coat:diluted_oil_of_sharpness", "Diluted Oil of Sharpness", 1, [Effect("attack_bonus", 1, applies_to="weapon"), Effect("damage_bonus", 1, applies_to="weapon")],
         COATING + "+1 weapon enchantment", cost="bonus", group="coating"),
    Buff("coat:dipped_fire", "Dipped in fire (a fire surface)", 1, [Effect("extra_damage", "1d4 fire", applies_to="weapon")],
         COATING + "+1d4 fire on each hit. Free: dip in a torch, candle or burning surface", cost="bonus", group="coating"),
    Buff("coat:simple_toxin", "Simple Toxin", 1, [Effect("toxin", "1d4 poison", stat="constitution", max_value=11)],
         COATING + "1d4 poison at the end of the target's turn, Constitution save DC 11", cost="bonus", group="coating"),
    Buff("coat:serpent_fang_toxin", "Serpent Fang Toxin", 2, [Effect("toxin", "1d6 poison", stat="constitution", max_value=13)],
         COATING + "1d6 poison at the end of the target's turn, Constitution save DC 13", cost="bonus", group="coating"),
    Buff("coat:wyvern_toxin", "Wyvern Toxin", 2, [Effect("toxin", "1d8 poison", stat="constitution", max_value=15)],
         COATING + "1d8 poison at the end of the target's turn, Constitution save DC 15", cost="bonus", group="coating"),
    Buff("coat:purple_worm_toxin", "Purple Worm Toxin", 2, [Effect("toxin", "1d10 poison", stat="constitution", max_value=19)],
         COATING + "1d10 poison at the end of the target's turn, Constitution save DC 19", cost="bonus", group="coating"),
]

# Standard spell effects (the same in BG3 as in 5e), then elixirs from the item data
BUFFS = {b.key: b for b in [
    Buff("bless", "Bless", 1, [Effect("attack_dice", "1d4")], "Also +1d4 to saving throws, up to 3 targets", concentration=True, targets=3),
    Buff("rapture", "Rapture (Nymph's Grotto)", 3, [Effect("attack_dice", "1d6")],
         "+1d6 to attack rolls, ability checks and saving throws until a long rest: a dialogue choice with Naoise Nallinto in Sharess' Caress",
         timing="long_rest"),
    Buff("haste", "Haste", 1, [Effect("extra_action", 1)],
         "One more action per turn (a whole Attack action outside Honour Mode, one attack in it) and +2 AC. Needs a level 5 caster in Act 1, or a Potion of Speed. "
         "Cast in round 1 by the character (Wizard or Sorcerer 5+) it takes that turn's action", concentration=True, cost="action"),
    Buff("hex", "Hex", 1, [Effect("extra_damage", "1d6 necrotic")], "Cast by the character, bonus action", concentration=True, self_cast=True, cost="bonus"),
    Buff("divine_favour", "Divine Favour", 1, [Effect("extra_damage", "1d4 radiant", applies_to="weapon")], "Paladin, bonus action",
         concentration=True, self_cast=True, cost="bonus"),
    # Cast on one weapon, both last until a long rest. They stack with each other and with the weapon's own enchantment
    Buff("magic_weapon", "Magic Weapon", 1, [Effect("attack_bonus", 1, applies_to="main_weapon"), Effect("damage_bonus", 1, applies_to="main_weapon")],
         "+1 to hit and damage with one weapon (level 2 spell, +2 from a level 4 slot)", concentration=True),
    Buff("drakethroat", "Drakethroat Glaive: elemental weapon", 2,
         [Effect("attack_bonus", 1, applies_to="main_weapon"), Effect("extra_damage", "1d4 lightning", applies_to="main_weapon")],
         "Draconic Elemental Weapon: +1 to hit and 1d4 acid, cold, fire, lightning, poison or thunder (counted as lightning) on one weapon until "
         "a long rest, Shadow Blade included. Whoever holds the glaive casts it in camp, once a long rest, so one weapon in the party", timing="long_rest"),
    # Defensive spells: no damage effect, counted by the armour class (bg3.defence)
    Buff("shield_of_faith", "Shield of Faith", 1, [], "+2 AC (concentration). Counted in armour class, not damage", concentration=True),
    Buff("mage_armour", "Mage Armour", 1, [], "AC 13 + DEX without armour, until a long rest (camp cast)", timing="long_rest"),
    Buff("warding_bond", "Warding Bond", 1, [], "+1 AC and saves, resistance to all damage; the caster takes the same damage (camp cast)", timing="long_rest"),
    # Phalar Aluve's Melody (Act 1 Underdark longsword): the wielder spends an action, once per short rest, for 5 turns. Not concentration
    Buff("phalar_sing", "Phalar Aluve: Sing", 1, [Effect("attack_dice", "1d4")],
         "Allies within 6m but not the wielder: +1d4 to attack rolls and saves for 5 turns. Costs the wielder an action, once per short rest", timing="combat"),
    Buff("phalar_shriek", "Phalar Aluve: Shriek", 1, [Effect("extra_damage", "1d4 thunder")],
         "Enemies within 6m take +1d4 thunder whenever they are damaged (here: once per hit) and -1d4 on saves, for 5 turns. "
         "Costs the wielder an action, once per short rest", timing="combat"),
    *COATINGS,
    *elixirs(),
]}
