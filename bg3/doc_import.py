""" Imports builds from a build reference document (i.e. a Google Doc shared by link) into planner builds.
    Reads the structured format in docs/bg3_build_format.md exactly, and the free text "Build N:" format best effort:
    class split, ability scores, feats, gear by act. Anything it can't place is listed with the build, never guessed silently.

    Usage: python -m bg3.doc_import <document url or text file>  (writes bg3/data/doc_builds.json) """
import html
import json
import re
import sys
import urllib.request
from difflib import get_close_matches
from itertools import permutations
from pathlib import Path

from bg3.abilities import point_buy_problems
from bg3.buffs import BUFFS
from bg3.build import Bg3Build
from bg3.character import CANTRIPS, CLASSES, FEATS, LEVELLED_SPELLS, RACES, ROUTINES, SHADOW_BLADE, SUBCLASSES, Bg3Character
from bg3.items import catalog
from computations.models import STATS

OUT = Path(__file__).parent / "data" / "doc_builds.json"
STAT_NAMES = {s[:3].upper(): s for s in STATS}
# Things the doc's gear lists name that aren't equipment: spells and carried items. Carried ones are kept for party synergies
CONJURED = {"shadow blade", "unarmed fists", "unarmed", "dual hand crossbows", "soul coins"}
CARRIED = {"resonance stone"}
ROLES = ["frontline", "striker", "ranged", "control", "healer", "support", "face", "skills", "summoner"]
SLOT_WORDS = {"main hand": "melee_main", "off hand": "melee_off", "off-hand": "melee_off", "ranged": "ranged_main", "ranged main": "ranged_main",
              "ranged off": "ranged_off", "helmet": "helmet", "head": "helmet", "cloak": "cloak", "armour": "armour", "armor": "armour", "chest": "armour",
              "gloves": "gloves", "boots": "boots", "amulet": "amulet", "ring 1": "ring_1", "ring 2": "ring_2", "shield": "melee_off"}
UNKNOWN = {"unknown", "none", "n/a", "-"}

def fetch_text(source):
    """ Plain text of a Google Doc link (read only, via its public mobile view) or a local file """
    if Path(source).exists():
        return normalise(Path(source).read_text(encoding="utf-8"))
    doc_id = re.search(r"/d/([\w-]+)", source)
    url = f"https://docs.google.com/document/d/{doc_id.group(1)}/mobilebasic" if doc_id else source
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as response:
        page = response.read().decode("utf-8", "ignore")
    page = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", page, flags=re.S)
    page = re.sub(r"<br\s*/?>|</p>|</h\d>|</li>|</tr>", "\n", page)
    page = html.unescape(re.sub(r"<[^>]+>", "", re.sub(r"</td>", " | ", page)))
    return normalise(page)

def normalise(text):
    return re.sub(r"\n\s*\n+", "\n", text.replace("\xa0", " ").replace("’", "'").replace("“", '"').replace("”", '"'))

# ---------- Items

def _key(name):
    return re.sub(r"[^a-z0-9]", "", name.lower().replace("’", "'").removeprefix("the "))

def item_index():
    index = {}
    for item in catalog().values():
        if item.key.startswith("bg3:"):
            index.setdefault(_key(item.name), item)
    for item in catalog().values(): # Plain base weapons ("Quarterstaff") when no named item has that name
        index.setdefault(_key(item.name), item)
    return index

def match_item(name, index):
    """ The item a name refers to, allowing small spelling differences ("Gloves of the Battlemage's Power") """
    key = _key(name)
    if key in index:
        return index[key]
    unique = [k for k, item in index.items() if item.unique] # Generic gear ("Hand Crossbow +2") only by its exact name
    close = get_close_matches(key, unique, n=1, cutoff=0.88)
    return index[close[0]] if close else None

def split_gear(text, upgrades=False):
    """ Item names from a gear list: commas separate items, '+' joins main and off hand, '->' is an upgrade (the last one counts),
        'A / B' and '(or B)' are alternatives (the first counts). Returns [(name, hint)] with hint 'off' for off-hand items.
        With upgrades, every item of an 'A -> B' chain is returned (for lists that cover all acts) """
    names = []
    for part in re.split(r",(?![^()]*\))", text):
        part = re.sub(r"\((?:or )?([^()]*?)\)", lambda m: " (off)" if re.search(r"off-?hand", m.group(1), re.I) else "", part)
        part = re.sub(r"^\s*Option [A-Z][^:]*:\s*", "", part)
        for chained in re.split(r"\s\+\s", part):
            hint = "off" if "(off)" in chained else ""
            for piece in chained.replace("(off)", "").split("->")[0 if upgrades else -1:]:
                piece = re.split(r"\s+or\s+|\s*/\s*", piece)[0]
                piece = re.sub(r"^\s*(?:and|add|plus|dual)\s+|\s*\.$|^\s*(?:upcast|via [^,]*)\s*", "", piece.strip(), flags=re.I).strip(" .:")
                if piece:
                    names.append((piece, hint))
    return names

def place_gear(names, index, carried, unmatched, equipment=None):
    """ Puts items in slots: weapons by kind and hint, shields in the off hand, rings in the first free ring slot """
    equipment = dict(equipment or {})
    for name, hint in names:
        if name.lower() in CONJURED or name.lower().startswith(SHADOW_BLADE.lower()):
            continue
        if name.lower() in CARRIED:
            carried.add(name.title())
            continue
        item = match_item(name, index)
        if item is None:
            unmatched.append(name)
            continue
        if item.slot == "ring":
            slot = "ring_2" if equipment.get("ring_1") not in (None, item.key) else "ring_1"
        elif item.slot == "shield":
            slot = "melee_off"
        elif item.weapon:
            ranged = item.weapon.get("kind") == "ranged"
            off = hint == "off" or (not ranged and "melee_main" in equipment and equipment["melee_main"] != item.key and "two-handed" not in
                                    item.weapon.get("properties", []))
            slot = ("ranged_off" if off else "ranged_main") if ranged else ("melee_off" if off else "melee_main")
        else:
            slot = item.slot
        equipment[slot] = item.key
    return equipment

# ---------- Characters

def parse_classes(text):
    """ '10 Bladesinging Wizard / 2 Oath of the Crown Paladin' -> [[class, subclass, levels], ...] in the order written """
    classes = []
    for levels, words in re.findall(r"(\d+)\s+([A-Z][\w'’ -]*?)(?=\s*(?:/|\(|\.|,|$|\bor\b))", text):
        lowered = words.lower()
        cls = next((c for c in CLASSES if re.search(rf"\b{c}\b", lowered)), None)
        if cls is None:
            cls = next((c for c, subs in SUBCLASSES.items() for s in subs if _sub_words(s) & set(lowered.split())), None)
        if cls is None:
            continue
        sub = max(SUBCLASSES[cls], key=lambda s: len(_sub_words(s) & set(lowered.split())))
        classes.append([cls, sub if _sub_words(sub) & set(lowered.split()) else SUBCLASSES[cls][0], int(levels)])
    return classes

def _sub_words(subclass):
    words = set(subclass.lower().replace("the ", "").split()) - {"of", "school", "domain", "circle", "way", "oath", "college", "path", "bloodline"}
    return words | ({"giant", "giants"} if subclass == "Giant" else set()) | ({"stars"} if "Stars" in subclass else set()) | \
        ({"spores"} if "Spores" in subclass else set()) | ({"necromancer", "necromancy"} if "Necromancy" in subclass else set()) | \
        ({"draconic"} if "Draconic" in subclass else set())

def parse_scores(text):
    """ 'STR 8, DEX 17 (+1 Hag's Hair to 18), ...' -> scores after the +2/+1 """
    scores = {STAT_NAMES[s]: int(v) for s, v in re.findall(r"\b(STR|DEX|CON|INT|WIS|CHA)\s+(\d+)", text)}
    return scores if len(scores) == 6 else None

def split_point_buy(final, primary=None):
    """ Point buy scores and the +2/+1 that give the final scores, preferring the +2 on the primary ability """
    options = []
    for plus2, plus1 in permutations(STATS, 2):
        base = {s: final[s] - (2 if s == plus2 else 1 if s == plus1 else 0) for s in STATS}
        bonus = {plus2: 2, plus1: 1}
        if not point_buy_problems(base, bonus):
            options.append((plus2 != primary, -final[plus2], base, bonus))
    if not options:
        return None, None
    options.sort(key=lambda o: o[:2])
    return options[0][2], options[0][3]

def parse_feats(text):
    """ Feats and ability improvements in the order they appear: 'ASI (+2 DEX ...)', 'Feat 2 (Level 8): Savage Attacker', 'Feats: War Caster ...' """
    found = []
    for m in re.finditer(r"\+2\s+(STR|DEX|CON|INT|WIS|CHA)\b|" + "|".join(re.escape(f) for f in sorted(FEATS, key=len, reverse=True)), text):
        if m.group(1):
            if re.search(r"(ASI|Feat)[^.]{0,40}$", text[max(0, m.start() - 45):m.start()]):
                found.append((m.start(), f"{STAT_NAMES[m.group(1)]}+2"))
        elif re.search(r"Feat|Feats", text[max(0, m.start() - 40):m.start()]):
            found.append((m.start(), m.group(0)))
    return [f for _, f in sorted(found)]

def guess_routine(text, equipment, items):
    """ The attack routine from what the build fights with """
    lowered = text.lower()
    main = items.get(equipment.get("melee_main", ""))
    if "shadow blade" in lowered and re.search(r"shadow blade[^.]{0,40}(main hand|primary)|shadow blade \+|main hand\)?: ?shadow blade|"
                                               r"shadow blade \(main", lowered):
        return "shadow_blade"
    if "unarmed" in lowered or "flurry of blows" in lowered:
        return "unarmed"
    if "throw" in lowered and ("tavern brawler" in lowered or "giant" in lowered):
        return "thrown"
    if re.search(r"eldritch blast beams|scorching ray|sorlock|nuker", lowered):
        return "cantrip"
    if equipment.get("ranged_main") and re.search(r"archer|arrows?\b", lowered):
        return "ranged"
    if main and main.weapon and "two-handed" in main.weapon.get("properties", []):
        return "two_handed"
    if equipment.get("melee_off") and items.get(equipment["melee_off"]) and items[equipment["melee_off"]].weapon:
        return "dual_wield"
    return "one_handed"

def parse_improvements(text):
    """ 'Feats: +2 DEX, Savage Attacker, +1 DEX +1 CON' -> builder feat choices """
    choices = []
    for part in re.split(r"[,;]", text):
        stats = re.findall(r"\+(\d)\s*(STR|DEX|CON|INT|WIS|CHA)\b", part)
        feat = next((f for f in FEATS if f.lower() in part.lower()), None)
        if feat:
            choices.append(feat)
        elif stats:
            choices.append(",".join(f"{STAT_NAMES[s]}+{n}" for n, s in stats))
    return choices

def parse_slots(text, index, carried, unmatched):
    """ 'Main Hand = X; Ring 1 = Y; Carried = Z' -> {slot: item key} """
    equipment = {}
    for pair in re.split(r";", text):
        if "=" not in pair:
            continue
        slot, name = (p.strip() for p in pair.split("=", 1))
        if name.lower() in UNKNOWN:
            continue
        if slot.lower() == "carried":
            carried.update(n.strip() for n in name.split(",") if n.strip())
            continue
        item = match_item(name, index)
        if SLOT_WORDS.get(slot.lower()) and item:
            equipment[SLOT_WORDS[slot.lower()]] = item.key
        elif name and not name.lower().startswith(SHADOW_BLADE.lower()):
            unmatched.append(f"{slot} = {name}")
    return equipment

def parse_level_order(text, classes):
    """ 'Paladin 1, Warlock 1, Paladin 2-11' -> the class key of each level, [] if it doesn't add up to the class split """
    order = []
    for name, start, end in re.findall(r"([A-Za-z][A-Za-z' ]*?)\s+(\d+)(?:\s*-\s*(\d+))?(?=\s*(?:,|;|$))", text):
        cls = next((c for c in CLASSES if c in name.lower()), None)
        if cls is None:
            return []
        order += [cls] * (int(end or start) - int(start) + 1)
    wanted = sorted(cls for cls, _, levels in classes for _ in range(int(levels)))
    return order if sorted(order) == wanted else []

def parse_buffs(text):
    names = {b.name.lower(): key for key, b in BUFFS.items()}
    return [names[n.strip().lower()] for n in re.split(r"[,;]", text) if n.strip().lower() in names]

# ---------- Builds

def build_sections(text):
    """ (number, title, body) for each 'Build N: Title' section """
    marks = list(re.finditer(r"^Build (\d+): (.+)$", text, re.M))
    ends = [m.start() for m in marks[1:]] + [len(text)]
    stop = re.search(r"^\d+\. (Master Item|Companion Assignment)", text, re.M)
    sections = []
    for m, end in zip(marks, ends):
        body = text[m.end():min(end, stop.start() if stop and stop.start() > m.end() else end)]
        sections.append((int(m.group(1)), m.group(2).strip(), body))
    return sections

def field(body, *names):
    for name in names:
        if m := re.search(rf"^{re.escape(name)}:\s*(.+)$", body, re.M | re.I):
            return m.group(1).strip()
    return ""

def parse_build(number, title, body, index, items):
    """ One build: a planner build dict plus what couldn't be read """
    notes, unmatched, carried = [], [], set()
    classes = parse_classes(field(body, "Class Split", "Classes", "Levels") or title)
    if not classes:
        notes.append("No class split found")
    primary = None
    ability_line = field(body, "Abilities", "Final abilities", "Starting Ability Scores", "Ability Scores")
    final = parse_scores(ability_line.split("|")[0])
    scores = bonus = None
    if final and "|" in ability_line:
        scores = final
        bonus = {STAT_NAMES[s]: int(n) for n, s in re.findall(r"\+(\d)\s*(STR|DEX|CON|INT|WIS|CHA)", ability_line.split("|")[1])}
        if point_buy_problems(scores, bonus):
            notes.append(f"Abilities: {'; '.join(point_buy_problems(scores, bonus))}")
    elif final:
        caster = {"wizard": "intelligence", "cleric": "wisdom", "druid": "wisdom", "warlock": "charisma", "sorcerer": "charisma", "bard": "charisma"}
        primary = max(final, key=lambda s: (final[s], s == caster.get(classes[0][0] if classes else "", "")))
        scores, bonus = split_point_buy(final, primary)
        if scores is None:
            notes.append("Ability scores aren't a 27 point buy with +2/+1, using the defaults")
    else:
        notes.append("No ability scores found")

    # Gear: per act lines, or one key gear list placed at the act each item is found
    equipment = {}
    for act, line in re.findall(r"^Act ([123]) Gear:\s*(.+)$", body, re.M):
        equipment[act] = {**equipment.get(str(int(act) - 1), {}), **parse_slots(line, index, carried, unmatched)}
    act_lines = [] if equipment else re.findall(r"^(Acts? [123](?: ?& ?[123])?)(?: BiS)?(?: \([^)]*\))?:\s*(.+)$", body, re.M)
    for label, line in act_lines:
        acts = re.findall(r"[123]", label)
        previous = equipment.get(str(int(acts[0]) - 1), {}) if acts[0] != "1" else {}
        placed = place_gear(split_gear(line), index, carried, unmatched, previous if line.lower().startswith("add") else {})
        for act in acts:
            equipment[act] = placed
    key_gear = field(body, "Key Gear", "Gear")
    if key_gear and not act_lines and not equipment:
        for name, hint in split_gear(key_gear, upgrades=True):
            item = match_item(name, index) if name.lower() not in CONJURED | CARRIED else None
            act = str(item.act or 3) if item else "1"
            equipment[act] = place_gear([(name, hint)], index, carried, unmatched, equipment.get(act, {}))
    # Each act lists only what changes, so drop what the act before already has
    trimmed = {}
    for act in ("1", "2", "3"):
        before = {}
        for a in ("1", "2", "3")[:int(act) - 1]:
            before.update(trimmed.get(a, {}))
        changed = {s: k for s, k in equipment.get(act, {}).items() if before.get(s) != k}
        if changed:
            trimmed[act] = changed
    flat = {}
    for act in ("1", "2", "3"):
        flat.update(trimmed.get(act, {}))
    routine = next((r for r, label in ROUTINES.items() if field(body, "Routine").lower() in (r, label.lower())), None) if field(body, "Routine") \
        else None
    routine = routine or guess_routine(body, flat, items)
    race = next((r for r in RACES if r.lower() in field(body, "Recommended Character/Race", "Race").lower()), "Human")
    character = Bg3Character(name=title.split(" (")[0].replace('"', "").strip(), race=race, scores=scores or Bg3Character().scores,
                             bonus=bonus or Bg3Character().bonus, classes=classes or [["fighter", "Champion", 12]],
                             feats=parse_improvements(field(body, "Feats")) if re.search(r"^Feats:.*,", body, re.M) and "Level" not in
                             field(body, "Feats") else parse_feats(body), routine=routine,
                             fighting_styles=[s.strip() for s in field(body, "Fighting styles").split(",") if s.strip()])
    if field(body, "Level order"):
        character.level_order = parse_level_order(field(body, "Level order"), character.classes)
        if not character.level_order:
            notes.append(f"Level order not read: {field(body, 'Level order')}")
    if field(body, "Respec"):
        notes.append(f"Respec not modelled (uses the final split): {field(body, 'Respec')}")
    if field(body, "Cantrip") or field(body, "Spell"):
        # Only damage spells the builder models; utility ones (Light, Aid, Hold Monster) and Divine Smite (a class feature here) are noted
        cantrip = next((c for c in CANTRIPS if c.lower() == field(body, "Cantrip").lower()), None)
        spell = next((c for c in LEVELLED_SPELLS if c.lower() == field(body, "Spell").lower()), "")
        # Support builds list a utility cantrip; they still get their class's damage cantrip so their damage isn't another class's
        natural = {"cleric": "Sacred Flame", "druid": "Produce Flame", "wizard": "Fire Bolt", "sorcerer": "Fire Bolt", "warlock": "Eldritch Blast"}
        character.cantrip = cantrip or natural.get(character.classes[0][0], character.cantrip)
        character.spell = spell
        skipped = [v for v, ok in ((field(body, "Cantrip"), cantrip), (field(body, "Spell"), spell)) if v and not ok and v.lower() not in UNKNOWN]
        if skipped and routine == "cantrip":
            notes.append(f"Not a modelled damage spell: {', '.join(skipped)}")
    elif routine == "cantrip":
        character.cantrip = "Eldritch Blast" if "eldritch blast" in body.lower() and any(c[0] == "warlock" for c in classes) else \
            "Fire Bolt" if "fire" in body.lower() else "Toll the Dead" if "toll the dead" in body.lower() else character.cantrip
        character.spell = "Scorching Ray" if "scorching ray" in body.lower() else ""
    roles = [r for r in ROLES if re.search(rf"\b{r}", field(body, "Roles", "Assigned Companion / Role", "Role").lower())]
    buffs = {act: parse_buffs(line) for act, line in re.findall(r"^Act ([123]) Buffs:\s*(.+)$", body, re.M)}
    build = Bg3Build(name=f"{number}. {character.name}", preset="fighter_gwm", equipment=trimmed, character=character.to_dict(),
                     buffs={a: b for a, b in buffs.items() if b}, carried=sorted(carried), roles=roles)
    return {"number": number, "title": title, "source": field(body, "Source", "Source / Creator"), "build": build.to_dict(),
            "carried": sorted(carried), "roles": roles, "unmatched": unmatched, "notes": notes,
            "companion": field(body, "Recommended Character/Race", "Assigned Companion / Role", "Companion"),
            "themes": [t.strip().lower() for t in field(body, "Themes").split(",") if t.strip()],
            "provides": [t.strip().lower() for t in field(body, "Provides").split(",") if t.strip()],
            "needs": [t.strip().lower() for t in field(body, "Needs").split(",") if t.strip()], "path": field(body, "Path"),
            "permanent_buffs": field(body, "Permanent buffs"), "gear_estimated": bool(re.search(r"^Gear acts:\s*estimated", body, re.M | re.I)),
            "caveats": field(body, "Caveats")}

def import_text(text):
    text = re.sub(r"^\*\s+", "", normalise(text), flags=re.M) # Required field markers from the format example
    index, items = item_index(), catalog()
    return [parse_build(n, title, body, index, items) for n, title, body in build_sections(text)]

def load():
    """ The imported builds, [] when nothing has been imported """
    return json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else []

if __name__ == "__main__":
    builds = import_text(fetch_text(sys.argv[1]))
    OUT.write_text(json.dumps(builds, indent=1, ensure_ascii=False), encoding="utf-8")
    for b in builds:
        print(f"{b['build']['name']}: {b['build']['character']['routine']}, {len(b['unmatched'])} unmatched {b['unmatched'][:4]} {b['notes']}")
