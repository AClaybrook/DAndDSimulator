""" Armour class per character and act, and the chance an enemy hits it.

    python -m bg3.defence    -> bg3/data/armour.json (armour types and base AC, shield bonuses and +AC items from the bg3.wiki pages in
                                bg3/data/raw/parsed.json)

    Rules (BG3): light armour adds DEX, medium up to +2 (+3 with Medium Armour Master), heavy none. Without armour: 10 + DEX, or the best of
    Mage Armour (13 + DEX), Draconic Resilience (13 + DEX), Monk (10 + DEX + WIS, no shield) and Barbarian (10 + DEX + CON) Unarmoured
    Defence. Then shields, the Defence fighting style (+1 in armour), +AC items, Bracers of Defence (+2 with no armour or shield), Bladesong
    (+2, +3 at Wizard 5, +4 at 9, not in medium or heavy armour or with a shield) and buffs (Shield of Faith +2, Haste +2, Warding Bond +1) """
import json
import re
from functools import lru_cache

from bg3.build import buffs_at, compile_build, equipment_at
from bg3.character import Bg3Character, class_levels, subclass_of
from bg3.checkpoints import act_level
from bg3.items import DATA, catalog

ARMOUR_TYPES = {"Clothing": "clothing", "Light Armour": "light", "Medium Armour": "medium", "Heavy Armour": "heavy", "Shields": "shield"}
AC_BUFFS = {"shield_of_faith": 2, "haste": 2, "warding_bond": 1}

def build_armour_data():
    """ {item key: {"type", "ac", "bonus"}} for armour, shields and items with a flat AC bonus """
    from bg3.scrape_wiki import RAW # pylint: disable=import-outside-toplevel
    parsed = {p["title"]: p["params"] for p in json.loads((RAW / "parsed.json").read_text(encoding="utf-8"))}
    out = {}
    for item in json.loads((DATA / "items.json").read_text(encoding="utf-8"))["items"]:
        params = parsed.get(item["name"], {})
        text = " ".join([params.get("special", ""), item.get("notes") or ""])
        bonus = re.search(r"Armour ?Class (?:\+|increases by )(\d)", text)
        entry = {}
        kind = ARMOUR_TYPES.get(params.get("type", ""))
        if item["slot"] in ("armour", "shield") and kind:
            entry["type"] = kind
            if kind == "shield":
                entry["bonus"] = int((params.get("armour class bonus") or "+2").strip("+") or 2)
            elif params.get("armour class", "").isdigit():
                entry["ac"] = int(params["armour class"])
        # Handwear, helmets and boots that need Medium or Heavy Armour proficiency count as wearing that armour: no Mage Armour,
        # Unarmoured Defence or Bladesong (seen in game with Legacy of the Masters)
        worn = {"Medium Armour": "medium", "Heavy Armour": "heavy"}.get(params.get("proficiency", ""))
        if item["slot"] not in ("armour", "shield") and worn:
            entry["proficiency"] = worn
        if bonus and not (params.get("armour class bonus") and kind == "shield"):
            entry["bonus"] = entry.get("bonus", 0) + int(bonus.group(1))
        if entry:
            out[item["key"]] = entry
    (DATA / "armour.json").write_text(json.dumps({"_source": "Armour types, base AC and AC bonuses from bg3.wiki (CC BY-NC-SA 4.0)",
                                                  "items": out}, indent=0, ensure_ascii=False), encoding="utf-8")
    return out

@lru_cache(maxsize=1)
def armour_data():
    path = DATA / "armour.json"
    return json.loads(path.read_text(encoding="utf-8"))["items"] if path.exists() else {}

def _mod(score):
    return (int(score) - 10) // 2

def armour_class(build, act, character=None):
    """ (AC, [(source, value)]) for a build at an act. character: the build already compiled at the act, to skip compiling it again """
    act = str(act)
    character = character or compile_build(build, act)
    gear = equipment_at(build, act)
    data = armour_data()
    items = catalog()
    dex, con, wis = _mod(character.dexterity), _mod(character.constitution), _mod(character.wisdom)
    level = act_level(act, build.levels)
    if build.character:
        bg3 = Bg3Character.from_dict(build.character)
        levels = class_levels(bg3, level)
        subs = {cls: subclass_of(bg3, cls, n) for cls, n in levels.items()}
        feats, styles = list(bg3.feats), list(bg3.fighting_styles)
        bladesong = bg3.toggle("bladesong")
    else:
        levels, subs, feats, styles, bladesong = {build.preset.split("_")[0]: level}, {}, [], [], True
    armour = data.get(gear.get("armour", ""), {})
    kind = armour.get("type", "clothing")
    shield = data.get(gear.get("melee_off", ""), {}) if data.get(gear.get("melee_off", ""), {}).get("type") == "shield" else {}
    # Shadow Blade and a shield: a plain shield when the gear has none
    shield_routine = bool(build.character) and build.character.get("routine") == "shadow_blade_shield"
    if shield_routine and not shield:
        shield = {"type": "shield", "bonus": 2}
    buffs = {b.key for b in buffs_at(build, act)}
    # A medium or heavy armour piece in another slot (Legacy of the Masters) ends unarmoured AC and Bladesong like body armour does
    armoured = next((items[k].name for k in gear.values() if data.get(k, {}).get("proficiency") and k in items), None)
    unarmoured = kind == "clothing" and not armoured
    parts = []
    if kind == "light":
        parts.append((f"{items[gear['armour']].name} (light)", armour.get("ac", 11) + dex))
    elif kind == "medium":
        # Some medium armour takes the whole Dexterity modifier (Armour of Agility, Yuan-Ti Scale Mail)
        full = "full dexterity modifier" in (items[gear["armour"]].notes or "").lower()
        parts.append((f"{items[gear['armour']].name} (medium)", armour.get("ac", 13) + (dex if full else min(dex, 3 if "Medium Armour Master" in feats else 2))))
    elif kind == "heavy":
        parts.append((f"{items[gear['armour']].name} (heavy)", armour.get("ac", 16)))
    elif armoured:
        parts.append((f"No armour (10 + DEX; {armoured} counts as medium armour)", 10 + dex))
    else:
        options = [("No armour (10 + DEX)", 10 + dex)]
        if "mage_armour" in buffs:
            options.append(("Mage Armour (13 + DEX)", 13 + dex))
        if subs.get("sorcerer") == "Draconic Bloodline":
            options.append(("Draconic Resilience (13 + DEX)", 13 + dex))
        if levels.get("monk") and not shield:
            options.append(("Unarmoured Defence (10 + DEX + WIS)", 10 + dex + wis))
        if levels.get("barbarian"):
            options.append(("Unarmoured Defence (10 + DEX + CON)", 10 + dex + con))
        parts.append(max(options, key=lambda o: o[1]))
    if shield:
        parts.append((items[gear["melee_off"]].name if gear.get("melee_off") in items else "Shield", shield.get("bonus", 2)))
    if kind in ("light", "medium", "heavy") and ("Defence" in styles or "Defense" in styles):
        parts.append(("Defence fighting style", 1))
    for key in gear.values():
        entry = data.get(key, {})
        if entry.get("bonus") and entry.get("type") != "shield" and key in items:
            parts.append((items[key].name, entry["bonus"]))
    if gear.get("gloves") == "bg3:bracers_of_defence" and unarmoured and not shield:
        parts.append(("Bracers of Defence (no armour or shield)", 2))
    if gear.get("cloak") == "bg3:wavemother_s_cloak":
        # Water Layer Protection: +2 AC (and saves) each turn until the wearer takes damage, so against the first attacks of a round
        parts.append(("Wavemother's Cloak (Water Layer Protection, until damaged)", 2))
    wizard = levels.get("wizard", 0)
    if bladesong and subs.get("wizard") == "Bladesinging" and wizard >= 2 and kind not in ("medium", "heavy") and not armoured and not shield:
        parts.append(("Bladesong", 2 + (wizard >= 5) + (wizard >= 9)))
    for key, value in AC_BUFFS.items():
        if key in buffs:
            parts.append((key.replace("_", " ").title(), value))
    return sum(v for _, v in parts), parts

# Dungeon Master's Guide "Monster Statistics by Challenge Rating": attack bonus
CR_ATTACK_BONUS = [(2, 3), (3, 4), (4, 5), (7, 6), (10, 7), (15, 8), (16, 9), (20, 10)]

def attack_bonus_for(enemy, default=6):
    """ The enemy's attack bonus from its challenge rating, or a typical mid game +6 when it has none (custom enemies) """
    cr = float(getattr(enemy, "challenge_rating", 0) or 0)
    if not cr:
        return default
    return next((bonus for top, bonus in CR_ATTACK_BONUS if cr <= top), 11)

def hit_chance(ac, attack_bonus):
    """ Chance an attack roll hits: a natural 20 always hits, a natural 1 always misses """
    return min(max((21 - (ac - attack_bonus)) / 20, 0.05), 0.95)

if __name__ == "__main__":
    print(len(build_armour_data()), "items with armour data")
