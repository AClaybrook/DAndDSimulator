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

def elixirs():
    """ Elixirs from data/buffs.json (built by build_items.py from bg3.wiki) """
    path = DATA / "buffs.json"
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [Buff(b["key"], b["name"], b["act"], [Effect(**e) for e in b["effects"]], b.get("notes", ""),
                     exclusive=b.get("exclusive", False), source=b.get("source", "")) for b in json.load(f)["buffs"]]

# Standard spell effects (the same in BG3 as in 5e), then elixirs from the item data
BUFFS = {b.key: b for b in [
    Buff("bless", "Bless", 1, [Effect("attack_dice", "1d4")], "Also +1d4 to saving throws, up to 3 targets", concentration=True, targets=3),
    Buff("haste", "Haste", 1, [Effect("extra_attack", 1, applies_to="weapon")],
         "One extra weapon attack per turn and +2 AC. Needs a level 5 caster in Act 1, or a Potion of Speed", concentration=True),
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
