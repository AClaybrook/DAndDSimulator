""" Buffs: spells and consumables that are active during a fight, selected per act """
from dataclasses import dataclass, field

from bg3.items import Effect

@dataclass
class Buff:
    key: str
    name: str
    act: int # First act it is usually available in
    effects: list[Effect] = field(default_factory=list)
    notes: str = ""
    concentration: bool = False # The caster can only keep one concentration spell up, so it takes a party member's concentration

# Standard spell effects (the same in BG3 as in 5e). Elixirs and camp buffs are added from the item data
BUFFS = {b.key: b for b in [
    Buff("bless", "Bless", 1, [Effect("attack_dice", "1d4")], "Also +1d4 to saving throws", concentration=True),
    Buff("haste", "Haste", 1, [Effect("extra_attack", 1, applies_to="weapon")],
         "One extra weapon attack per turn and +2 AC. Needs a level 5 caster in Act 1, or a Potion of Speed", concentration=True),
    Buff("hex", "Hex", 1, [Effect("extra_damage", "1d6 necrotic")], "Cast by the character, bonus action", concentration=True),
    Buff("divine_favour", "Divine Favour", 1, [Effect("extra_damage", "1d4 radiant", applies_to="weapon")], "Paladin, bonus action",
         concentration=True),
]}
