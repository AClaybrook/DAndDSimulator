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

# When each elixir can first be had (bg3.wiki "where to find"), by the act checkpoints (End of Act 1 is level 5, Act 2 level 8, Act 3 level 12)
ELIXIR_ACT = {"elixir:elixir_of_viciousness": 2, "elixir:elixir_of_battlemage_s_power": 2}
OBTAIN = {
    "elixir:elixir_of_hill_giant_strength": "Act 1: Auntie Ethel sells 3 a long rest (Grove, then the Riverside Teahouse), Derryth in the Myconid Colony; craftable",
    "elixir:elixir_of_bloodlust": "Act 1: Cyrel (Risen Road), Derryth (Myconid Colony), Kith (Grymforge); craftable from Worg Fangs",
    "elixir:elixir_of_heroism": "Act 1: Mol (Tiefling Hideout), Talli; craftable from Pegasus Feathers",
    "elixir:elixir_of_the_colossus": "Act 1: craftable only, from Chasm Creepers (glowing purple plants along the Underdark paths), so a handful",
    "elixir:elixir_of_viciousness": "Trader stock from level 6 (Act 2), craftable from Shadowroot Sacs",
    "elixir:elixir_of_battlemage_s_power": "Trader stock from level 6 (Act 2), craftable from Gauth Eyestalks",
    "elixir:elixir_of_cloud_giant_strength": "Trader stock from level 9 (Act 3). Craftable earlier from Cloud Giant Fingers, which Blurg and Derryth "
                                             "(Myconid Colony) stock from level 6, so a few in Act 2",
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
            out.append(Buff(b["key"], b["name"], ELIXIR_ACT.get(b["key"], b["act"]), effects, notes, exclusive=True, source=b.get("source", "")))
    return out

# Standard spell effects (the same in BG3 as in 5e), then elixirs from the item data
BUFFS = {b.key: b for b in [
    Buff("bless", "Bless", 1, [Effect("attack_dice", "1d4")], "Also +1d4 to saving throws, up to 3 targets", concentration=True, targets=3),
    Buff("haste", "Haste", 1, [Effect("extra_action", 1)],
         "One more action per turn (a whole Attack action outside Honour Mode, one attack in it) and +2 AC. Needs a level 5 caster in Act 1, or a Potion of Speed", concentration=True),
    Buff("hex", "Hex", 1, [Effect("extra_damage", "1d6 necrotic")], "Cast by the character, bonus action", concentration=True, self_cast=True),
    Buff("divine_favour", "Divine Favour", 1, [Effect("extra_damage", "1d4 radiant", applies_to="weapon")], "Paladin, bonus action",
         concentration=True, self_cast=True),
    # Defensive spells: no damage effect, counted by the armour class (bg3.defence)
    Buff("shield_of_faith", "Shield of Faith", 1, [], "+2 AC (concentration). Counted in armour class, not damage", concentration=True),
    Buff("mage_armour", "Mage Armour", 1, [], "AC 13 + DEX without armour, until a long rest (camp cast)"),
    Buff("warding_bond", "Warding Bond", 1, [], "+1 AC and saves, resistance to all damage; the caster takes the same damage (camp cast)"),
    # Phalar Aluve's Melody (Act 1 Underdark longsword): the wielder spends an action, once per short rest, for 5 turns. Not concentration
    Buff("phalar_sing", "Phalar Aluve: Sing", 1, [Effect("attack_dice", "1d4")],
         "Allies within 6m but not the wielder: +1d4 to attack rolls and saves for 5 turns. Costs the wielder an action, once per short rest"),
    Buff("phalar_shriek", "Phalar Aluve: Shriek", 1, [Effect("extra_damage", "1d4 thunder")],
         "Enemies within 6m take +1d4 thunder whenever they are damaged (here: once per hit) and -1d4 on saves, for 5 turns. "
         "Costs the wielder an action, once per short rest"),
    *elixirs(),
]}
