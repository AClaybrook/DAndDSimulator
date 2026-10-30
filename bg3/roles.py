""" Party roles: what each member covers (from its classes, attack routine and Charisma, plus roles its source lists), which core roles
    nobody covers, and where members overlap. Overlaps aren't problems, a themed party often doubles up; they are shown so it's a choice """
from bg3.build import compile_build
from bg3.character import Bg3Character, class_levels, subclass_of
from bg3.checkpoints import act_level

ROLE_LABELS = {"frontline": "Front line (melee)", "ranged": "Ranged damage", "healer": "Healer", "face": "Party face (Charisma)",
               "skills": "Locks, traps and sleight of hand", "control": "Control caster", "support": "Buffs (Bless, Haste, Aid)",
               "striker": "Damage dealer", "summoner": "Summoner"}
CORE_ROLES = ["frontline", "ranged", "healer", "face", "skills", "control"]
MELEE = {"two_handed", "one_handed", "dual_wield", "unarmed", "shadow_blade"}
CASTERS = {"bard", "cleric", "druid", "sorcerer", "warlock", "wizard"}

def member_roles(build, act):
    """ {role: reason} for one member at an act """
    act = str(act)
    level = act_level(act, build.levels)
    roles = {r: "from the build's source" for r in build.roles}
    character = compile_build(build, act)
    if build.character:
        bg3 = Bg3Character.from_dict(build.character)
        levels = class_levels(bg3, level)
        subs = {cls: subclass_of(bg3, cls, n) for cls, n in levels.items()}
        routine = bg3.routine
    else:
        levels = {build.preset.split("_")[0]: level}
        subs = {}
        routine = "cantrip" if any(a.type == "spell" for a in character.attacks) and not any(a.is_weapon for a in character.attacks) else \
            "ranged" if any(a.type == "weapon (ranged)" for a in character.attacks) else "two_handed"
    if routine in MELEE:
        roles.setdefault("frontline", f"{routine.replace('_', ' ')} attacks")
    if routine in ("ranged", "cantrip", "thrown"):
        roles.setdefault("ranged", f"{routine} attacks")
    healers = [c for c in ("cleric", "druid", "bard") if levels.get(c)] + (["paladin"] if levels.get("paladin", 0) >= 1 else [])
    if healers:
        roles.setdefault("healer", f"{', '.join(c.title() for c in healers)} healing" + (" (Lay on Hands only)" if healers == ["paladin"] else ""))
    if character.charisma >= 16:
        roles.setdefault("face", f"Charisma {character.charisma}")
    if levels.get("rogue") or (levels.get("bard", 0) >= 2):
        roles.setdefault("skills", "Rogue expertise and thieves' tools" if levels.get("rogue") else "Bard Jack of All Trades")
    caster_levels = sum(n for c, n in levels.items() if c in CASTERS)
    if caster_levels >= 5:
        roles.setdefault("control", f"{caster_levels} caster levels")
    if levels.get("cleric") or levels.get("bard") or levels.get("druid") or levels.get("paladin", 0) >= 2 or caster_levels >= 5:
        roles.setdefault("support", "Bless, Aid or Haste")
    if subs.get("wizard") == "Necromancy School" or levels.get("warlock", 0) >= 6 and subs.get("warlock") == "The Hexblade":
        roles.setdefault("summoner", "Undead (Necromancy) or Accursed Spectre")
    return roles

def party_roles(builds, act):
    """ (rows of [member, {role: reason}], missing core roles, overlap notes) """
    rows = [(b.name, member_roles(b, act)) for b in builds]
    missing = [r for r in CORE_ROLES if not any(r in roles for _, roles in rows)]
    overlaps = []
    for role in CORE_ROLES:
        members = [name for name, roles in rows if role in roles]
        if role == "face" and len(members) > 1:
            overlaps.append(f"{len(members)} party faces ({', '.join(members)}): only one talks, the others' Charisma mostly goes to spells")
        elif role in ("frontline", "ranged") and len(members) >= 3:
            overlaps.append(f"{len(members)} members are {ROLE_LABELS[role].lower()}: {', '.join(members)}")
        elif role == "skills" and len(members) > 1:
            overlaps.append(f"{len(members)} skill monkeys ({', '.join(members)})")
    return rows, missing, overlaps
