""" Builds bg3/data/items.json from the bg3.wiki export (see scrape_wiki.py).

    python -m bg3.build_items

    Structured fields (slot, rarity, act, weapon dice and properties) come straight from the wiki templates.
    Effects are read from the item's special text and passive features with conservative patterns, anything not matched is kept
    as a note. Hand checked corrections in data/effect_overrides.json replace the parsed effects of an item """
import json
import re
import unicodedata
from pathlib import Path

from bg3.scrape_wiki import RAW, plain_text, template_params
from computations.models import DAMAGE_TYPES, STATS

DATA = Path(__file__).parent / "data"

SLOT_BY_TYPE = {"Helmets": "helmet", "Cloaks": "cloak", "Gloves": "gloves", "Boots": "boots", "Amulets": "amulet", "Rings": "ring",
                "Shields": "shield", "Clothing": "armour", "Light Armour": "armour", "Medium Armour": "armour", "Heavy Armour": "armour"}
SKIP_TYPES = {"Camp Clothing", "Camp Shoes", "Underwear", "Musical Instruments", None, ""}
# Weapon type: base weapon in the weapon table
WEAPON_BASE = {"Daggers": "Dagger", "Quarterstaves": "Quarterstaff", "Longswords": "Longsword", "Shortswords": "Shortsword", "Greatswords": "Greatsword",
               "Scimitars": "Scimitar", "Clubs": "Club", "Maces": "Mace", "Spears": "Spear", "Warhammers": "Warhammer", "Flails": "Flail",
               "Rapiers": "Rapier", "Battleaxes": "Battleaxe", "Greataxes": "Greataxe", "Heavy Crossbows": "Heavy Crossbow", "Shortbows": "Shortbow",
               "Glaives": "Glaive", "Longbows": "Longbow", "Tridents": "Trident", "Pikes": "Pike", "Mauls": "Maul", "Halberds": "Halberd",
               "Greatclubs": "Greatclub", "Handaxes": "Handaxe", "Hand Crossbows": "Hand Crossbow", "War Picks": "War Pick",
               "Morningstars": "Morningstar", "Light Crossbows": "Light Crossbow", "Sickles": "Sickle", "Light Hammers": "Light Hammer",
               "Javelins": "Javelin", "Darts": "Dart", "Slings": "Sling"}
LOCATION_CATEGORIES = {"Category:Prologue Locations": 1, "Category:Act One Locations": 1, "Category:Act Two Locations": 2,
                       "Category:Act Three Locations": 3}
CHARACTER_CATEGORIES = {"Category:Characters in Act One": 1, "Category:Characters in Act Two": 2, "Category:Characters in Act Three": 3}
CONDITION_WORDS = re.compile(r"\b(if|when|whenever|while|against|after|once per|critical|burning|illuminated|obscured|raging|until|"
                             r"haven't|full health|frightened|on a hit|each turn|first)\b", re.I)
DAMAGE = r"(\d+d\d+(?:\s*\+\s*\d+)?|\d+)\s+(" + "|".join(t.title() for t in DAMAGE_TYPES) + r")"
DICE = r"(\d*d\d+|\d+)"
SCOPES = [("weapon and unarmed attacks", "all"), ("unarmed and melee attacks", "melee_weapon"), ("ranged weapon attacks", "ranged_weapon"),
          ("melee weapon attack", "melee_weapon"), ("ranged attack rolls", "ranged_weapon"), ("melee attack rolls", "melee_weapon"),
          ("unarmed attack", "unarmed"), ("throw attack", "thrown"), ("throw damage", "thrown"), ("thrown", "thrown"), ("weapon attacks", "weapon"),
          ("this weapon", "self"), ("this blade", "self"), ("with this dagger", "self"), ("cantrip", "spell"), ("spell", "spell")]
# Damage dealt back to attackers, and other effects that don't add to the wearer's damage
REACTIVE = re.compile(r"attackers that hit|that hit the wearer|hit (?:you|the wearer) with|who miss|when you are hit|you are hit|"
                      r"when you take|deals damage to the wearer|When a foe hits|foe that caused|incoming|Jumps?\b|items and world objects|"
                      r"succe(?:ed|ssful) (?:a |on a )?Saving ?Throw|take \d|takes \d", re.I)

# Companions and camp characters appear in every act, so linking them says nothing about where an item is found
COMPANIONS = {"Shadowheart", "Lae'zel", "Astarion", "Gale", "Wyll", "Karlach", "Halsin", "Jaheira", "Minsc", "Minthara", "Tav", "The Dark Urge",
              "Dark Urge", "Withers", "Scratch", "Owlbear Cub", "Alfira", "Volo", "The Emperor", "Orpheus"}
ACT_NAMES = {"Prologue": 1, "Act One": 1, "Act 1": 1, "Act Two": 2, "Act 2": 2, "Act Three": 3, "Act 3": 3}
# Regions whose sub locations aren't categorised by act
REGIONS = {"Nautiloid": 1, "Underdark": 1, "Grymforge": 1, "Risen Road": 1, "Wilderness": 1, "Emerald Grove": 1, "Goblin Camp": 1,
           "Mountain Pass": 1, "Shadow-Cursed Lands": 2, "Reithwin": 2, "Moonrise": 2, "Last Light": 2, "Gauntlet of Shar": 2,
           "Rivington": 3, "Wyrm's Crossing": 3, "Wyrm's Rock": 3, "Lower City": 3, "Upper City": 3, "Baldur's Gate": 3, "Outer City": 3}

def load_acts():
    with open(RAW / "act_categories.json", encoding="utf-8") as f:
        cats = json.load(f)
    locations, characters = {}, {}
    for cat, act in LOCATION_CATEGORIES.items():
        for t in cats.get(cat, []):
            locations.setdefault(t.replace(" (location)", ""), act)
            locations.setdefault(t, act)
    for cat, act in CHARACTER_CATEGORIES.items():
        for t in cats.get(cat, []):
            characters[t] = min(characters.get(t, 9), act)
    extra = RAW / "extra_location_categories.json"
    if extra.exists():
        for title, page_cats in json.loads(extra.read_text(encoding="utf-8")).items():
            acts = {act for cat, act in LOCATION_CATEGORIES.items() if cat in page_cats}
            if len(acts) == 1: # Places in several acts (i.e. the camp) don't tell
                locations.setdefault(title.replace("_", " "), acts.pop())
            char_acts = [act for cat, act in CHARACTER_CATEGORIES.items() if cat in page_cats]
            if char_acts:
                characters.setdefault(title.replace("_", " "), min(char_acts))
    for name in COMPANIONS:
        characters.pop(name, None)
    return locations, characters

def location_act(name, locations):
    name = name.split("#")[0].replace("_", " ").strip()
    if name in locations:
        return locations[name]
    return next((act for region, act in REGIONS.items() if region.lower() in name.lower()), None)

def raw_param(text, key):
    match = re.search(r"\|\s*" + re.escape(key) + r"\s*=(.*?)(?=\n\s*\|\s*[a-z0-9 ]+\s*=|\n\}\})", text, re.S)
    return match.group(1) if match else ""

def item_act(page, params, locations, characters):
    """ The earliest act an item is found in: from its location, linked locations and characters (traders), or the trader level """
    text = page["wikitext"]
    where = " ".join(raw_param(text, k) for k in ("where to find", "where to find2", "where to find3"))
    links = [link.strip() for link in re.findall(r"\[\[([^\]|#]+)", where)]
    # In order of reliability: the act named in the text, the location, linked places, linked traders/characters
    named = {act for name, act in ACT_NAMES.items() if name in links or re.search(rf"\bin (?:the )?{name}\b", plain_text(where))}
    named |= {ACT_NAMES[f"Act {a}"] for a in re.findall(r"#Act[_ ](One|Two|Three)", where)}
    if named:
        return min(named)
    located = {location_act(params.get(k, ""), locations) for k in ("where to find location", "where to find2 location") if params.get(k)}
    located |= {location_act(link, locations) for link in links}
    located.discard(None)
    if located:
        return min(located)
    people = {characters.get(name.strip()) for name in re.findall(r"\{\{CharLink\|([^}|]+)", where) + links}
    people.discard(None)
    if people:
        return min(people)
    # Levelled trader tables, i.e. "if the player is level 9 or above", "between levels 5 and 8"
    level = re.search(r"level (\d+) or above|between levels? (\d+)", plain_text(where))
    if level:
        lv = int(level.group(1) or level.group(2))
        return 1 if lv <= 5 else 2 if lv <= 8 else 3
    if re.search(r"Sold by any trader", plain_text(where)):
        return 1
    return None

def scope_of(sentence):
    lower = sentence.lower()
    for words, scope in SCOPES:
        if words in lower:
            return scope
    return "all"

def parse_effects(lines, own_weapon=False):
    """ Effects from effect sentences, returns (effects, unmatched sentences) """
    effects, notes = [], []
    for line in lines:
        for sentence in [s.strip(" *.") for s in re.split(r"(?<=\.)\s+|\n|\* ", line) if s.strip(" *.")]:
            found = _parse_sentence(sentence, own_weapon)
            if found:
                effects += found
            else:
                notes.append(sentence)
    return effects, notes

def _parse_sentence(sentence, own_weapon):
    # The wiki's damage templates render as i.e. "d4 Piercing 1d4", keep the dice
    sentence = re.sub(r"\bd\d+ (?:Physical|Piercing|Slashing|Bludgeoning|Weapon)\s*(\+?-?\d+d\d+)", r"\1", sentence)
    if REACTIVE.search(sentence):
        return []
    condition = sentence if CONDITION_WORDS.search(sentence) else ""
    scope = scope_of(sentence)
    if scope == "all" and own_weapon:
        scope = "self"
    conditional = {"condition": condition} if condition else {}
    effects = []
    if m := re.search(r"Set the wearer's (\w+)(?: score)? to (\d+)", sentence, re.I):
        stat = m.group(1).lower()
        if stat in STATS:
            return [{"kind": "ability_min", "stat": stat, "value": int(m.group(2))}]
    if m := re.search(r"increase your (\w+) by (\d+), to a maximum of (\d+)", sentence, re.I):
        stat = m.group(1).lower()
        if stat in STATS:
            return [{"kind": "ability_bonus", "stat": stat, "value": int(m.group(2)), "max_value": int(m.group(3))}]
    if m := re.search(r"Increases (\w+) to (\d+)", sentence):
        stat = m.group(1).lower()
        if stat in STATS:
            return [{"kind": "ability_min", "stat": stat, "value": int(m.group(2))}]
    if m := re.fullmatch(r"(\w+?)s? \+(\d+)(?: \(up to (\d+)\))?", sentence):
        stat = m.group(1).lower()
        if stat in STATS:
            return [{"kind": "ability_bonus", "stat": stat, "value": int(m.group(2)), **({"max_value": int(m.group(3))} if m.group(3) else {})}]
    if m := re.search(r"\+(\d+) bonus to (?:spell save DC|Spell Save DC)(?! and)", sentence):
        return [{"kind": "spell_dc", "value": int(m.group(1)), **conditional}]
    if m := re.search(r"\+(\d+) bonus to (?:Ranged )?Spell Attack Rolls", sentence, re.I):
        return [{"kind": "attack_bonus", "value": int(m.group(1)), "applies_to": "spell", **conditional}]
    if m := re.search(r"\+(\d+) bonus to (?:melee |ranged |unarmed )?(?:weapon )?Attack Rolls", sentence, re.I):
        return [{"kind": "attack_bonus", "value": int(m.group(1)), "applies_to": scope, **conditional}]
    if m := re.search(r"\+?" + DICE + r" bonus to (?:damage and Attack Rolls|attack and damage)", sentence, re.I):
        return [{"kind": "attack_dice" if "d" in m.group(1) else "attack_bonus", "value": m.group(1), "applies_to": scope, **conditional},
                {"kind": "damage_bonus", "value": m.group(1), "applies_to": scope, **conditional}]
    if m := re.search(r"\+?(\d*d\d+) bonus to Attack Rolls", sentence, re.I):
        return [{"kind": "attack_dice", "value": m.group(1), "applies_to": scope, **conditional}]
    if re.search(r"(?<![Dd]is)Advantage on (?:melee )?Attack Rolls|has Advantage on Attack Rolls|Attack Rolls against .+ have Advantage|"
                 r"have Advantage against", sentence):
        return [{"kind": "advantage", "applies_to": scope, **conditional}]
    if re.search(r"critical hit when rolling a 19", sentence, re.I):
        return [{"kind": "crit_range", "value": 1, "applies_to": scope}]
    if m := re.search(r"(?:additional|extra) damage equal to your (\w+) Modifier", sentence, re.I):
        stat = m.group(1).lower()
        return [{"kind": "damage_bonus_ability", "stat": stat if stat in STATS else "spellcasting", "applies_to": scope, **conditional}]
    if m := re.search(DICE + r" bonus to Throw damage|additional " + DICE + r" damage with Throw", sentence, re.I):
        return [{"kind": "damage_bonus", "value": m.group(1) or m.group(2), "applies_to": "thrown"}]
    if m := re.search(r"On a Critical Hit, the target takes an extra (\d+)", sentence, re.I):
        return [{"kind": "crit_damage", "value": int(m.group(1)), "applies_to": scope}]
    if m := re.search(r"\+(\d+) bonus to Spell Save DC and Spell Attack rolls", sentence, re.I):
        return [{"kind": "spell_dc", "value": int(m.group(1))}, {"kind": "attack_bonus", "value": int(m.group(1)), "applies_to": "spell"}]
    if m := re.fullmatch(r"(?:Ranged )?Spell (?:Save DC|Attack(?: Rolls?)?) \+(\d+)", sentence, re.I):
        kind = "spell_dc" if "dc" in sentence.lower() else "attack_bonus"
        return [{"kind": kind, "value": int(m.group(1)), **({"applies_to": "spell"} if kind == "attack_bonus" else {})}]
    if m := re.fullmatch(r"Attack rolls \+(\d+)", sentence, re.I):
        return [{"kind": "attack_bonus", "value": int(m.group(1)), "applies_to": "self" if own_weapon else "all"}]
    if m := re.search(r"\+(\d+) bonus to damage and Attack Rolls", sentence, re.I):
        return [{"kind": "attack_bonus", "value": int(m.group(1)), "applies_to": scope}, {"kind": "damage_bonus", "value": int(m.group(1)), "applies_to": scope}]
    if re.search(r"number you need to roll a Critical Hit (?:while attacking )?is reduced by (?:1|one)", sentence, re.I):
        condition = sentence if re.match(r"While|When|If", sentence) else ""
        return [{"kind": "crit_range", "value": 1, **({"condition": condition} if condition else {})}]
    for m in re.finditer(r"(?:also )?deal(?:s)? (?:an )?(?:additional|extra)?\s*" + DAMAGE + r"(?: points of \w+)?(?: damage)?", sentence):
        effects.append({"kind": "extra_damage", "value": f"{m.group(1).replace(' ', '')} {m.group(2).lower()}", "applies_to": scope})
    if m := re.search(r"additional (\d+) points of (\w+?)(?:see bugs)? damage", sentence):
        if m.group(2).lower() in DAMAGE_TYPES:
            effects.append({"kind": "extra_damage", "value": f"{m.group(1)} {m.group(2).lower()}", "applies_to": scope})
    if not effects and (m := re.search(r"deals? an additional " + DICE + r" damage", sentence)):
        effects.append({"kind": "damage_bonus", "value": m.group(1), "applies_to": scope})
    if effects and condition:
        for e in effects:
            e["condition"] = condition
    return effects

def weapon_stats(params):
    damage = params.get("damage", "")
    base_dice = re.match(r"\s*(\d+d\d+)", damage)
    versatile = re.match(r"\s*(\d+d\d+)", params.get("versatile damage") or "")
    props = [p for p in ("finesse", "light", "heavy", "thrown", "reach") if params.get(p) == "yes"]
    if params.get("handedness") == "two-handed":
        props.append("two-handed")
    if params.get("handedness") == "versatile" or versatile:
        props.append("versatile")
    enchantment = re.search(r"\+(\d+)", params.get("enchantment") or "")
    return {
        "base": WEAPON_BASE.get(params.get("type"), params.get("type")),
        "kind": "ranged" if (params.get("melee or ranged") or "").startswith("ranged") else "melee",
        "damage": base_dice.group(1) if base_dice else "1d6",
        "versatile_damage": versatile.group(1) if versatile else None,
        "damage_type": (params.get("damage type") or "slashing").lower(),
        "enhancement": int(enchantment.group(1)) if enchantment else 0,
        "properties": props,
    }

def key_for(title):
    """ 'Selûne's Spear of Night' -> 'bg3:selune_s_spear_of_night' """
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    return "bg3:" + re.sub(r"[^a-z0-9]+", "_", ascii_title.lower()).strip("_")

def build():
    locations, characters = load_acts()
    pages = {}
    with open(RAW / "pages.jsonl", encoding="utf-8") as f:
        for line in f:
            p = json.loads(line)
            pages[p["title"]] = p
    with open(RAW / "parsed.json", encoding="utf-8") as f:
        parsed = json.load(f)
    passives = {}
    with open(RAW / "passives.json", encoding="utf-8") as f:
        for name, text in json.load(f).items():
            params = template_params(text, "Passive feature page") or template_params(text, "Passive Feature Page")
            passives[name] = plain_text(params.get("description", "")).replace("\n", " ")
    overrides_path = DATA / "effect_overrides.json"
    overrides = json.loads(overrides_path.read_text(encoding="utf-8"))["items"] if overrides_path.exists() else {}
    base_names = {v for v in WEAPON_BASE.values()}

    items = []
    for entry in parsed:
        params, title = entry["params"], entry["title"]
        item_type = params.get("type")
        is_weapon = entry["template"].endswith("Weapon page")
        if item_type in SKIP_TYPES or (not is_weapon and item_type not in SLOT_BY_TYPE):
            continue
        if title in base_names:
            continue # Base weapons come from the weapon table
        where = plain_text(raw_param(pages[title]["wikitext"], "where to find"))
        generic = bool(re.fullmatch(r".+ \+\d", title)) or "Sold by any trader" in where or "levelled magic" in where
        lines = [params.get("special", "")]
        passive_names = [n.strip() for k in ("passives", "passives main hand") for n in (params.get(k) or "").split(",") if n.strip()]
        lines += [passives.get(n, "") for n in passive_names]
        effects, notes = parse_effects([x for x in lines if x], own_weapon=is_weapon)
        if is_weapon and params.get("extra damage"):
            m = re.fullmatch(DAMAGE, params["extra damage"].strip())
            if m:
                effects.append({"kind": "extra_damage", "value": f"{m.group(1).replace(' ', '')} {m.group(2).lower()}", "applies_to": "self"})
        item = {
            "key": key_for(title),
            "name": title,
            "slot": "weapon" if is_weapon else SLOT_BY_TYPE[item_type],
            "act": item_act(pages[title], params, locations, characters),
            "rarity": (params.get("rarity") or "").title(),
            "unique": not generic,
            "weapon": weapon_stats(params) if is_weapon else None,
            "effects": effects,
            "notes": "; ".join(n for n in notes if len(n) > 3)[:600],
            "location": params.get("where to find location") or where[:120],
            "source": entry["source"],
        }
        if title in overrides:
            item.update(overrides[title])
            item["reviewed"] = True
        items.append(item)

    items.sort(key=lambda i: (i["act"] or 9, i["slot"], i["name"]))
    out = {
        "_source": "Exported from bg3.wiki (CC BY-NC-SA 4.0) by bg3/scrape_wiki.py and bg3/build_items.py, every item links to its page. "
                   "Effects marked reviewed were checked by hand, others are parsed from the item text",
        "patch": "8",
        "exported": max(p["timestamp"] for p in pages.values())[:10],
        "items": items,
    }
    with open(DATA / "items.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    modelled = sum(1 for i in items if i["effects"] or (i["weapon"] and i["weapon"]["enhancement"]))
    print(f"{len(items)} items, {modelled} with modelled effects, acts: "
          f"{ {a: sum(1 for i in items if i['act'] == a) for a in (1, 2, 3, None)} }")

if __name__ == "__main__":
    build()
