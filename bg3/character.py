""" BG3 character builder: race, point buy, class levels in order (multiclassing), subclasses, feats and fighting styles,
    compiled into a plain Character for the simulator at any level.

    Rules follow Patch 8 (bg3/data/rules.json, researched from bg3.wiki). Features that change damage are modelled, the rest
    are listed in the build's notes. Resources per rest are turned into average uses per fight like the presets """
from dataclasses import asdict, dataclass, field, fields, replace
from math import ceil

from bg3.abilities import apply_improvement, starting_scores
from computations.models import STATS, Attack, Character
from game_data import spell_attacks, spells, weapon_attack, weapons
from game_data.classes import FIGHTS_PER_LONG_REST, SHORT_RESTS_PER_LONG_REST, action_surge, per_fight, spell_slots

MAX_LEVEL = 12
CLASSES = ("barbarian", "bard", "cleric", "druid", "fighter", "monk", "paladin", "ranger", "rogue", "sorcerer", "warlock", "wizard")
SUBCLASSES = {
    "barbarian": ["Berserker", "Giant", "Wild Magic", "Wildheart"],
    "bard": ["College of Glamour", "College of Lore", "College of Swords", "College of Valour"],
    "cleric": ["Death Domain", "Knowledge Domain", "Life Domain", "Light Domain", "Nature Domain", "Tempest Domain", "Trickery Domain", "War Domain"],
    "druid": ["Circle of the Land", "Circle of the Moon", "Circle of Spores", "Circle of Stars"],
    "fighter": ["Arcane Archer", "Battle Master", "Champion", "Eldritch Knight"],
    "monk": ["Way of the Drunken Master", "Way of the Four Elements", "Way of the Open Hand", "Way of Shadow"],
    "paladin": ["Oath of Devotion", "Oath of the Ancients", "Oath of the Crown", "Oath of Vengeance", "Oathbreaker"],
    "ranger": ["Beast Master", "Gloom Stalker", "Hunter", "Swarmkeeper"],
    "rogue": ["Arcane Trickster", "Assassin", "Swashbuckler", "Thief"],
    "sorcerer": ["Draconic Bloodline", "Shadow Magic", "Storm Sorcery", "Wild Magic"],
    "warlock": ["The Archfey", "The Fiend", "The Great Old One", "The Hexblade"],
    "wizard": ["Abjuration School", "Bladesinging", "Conjuration School", "Divination School", "Enchantment School", "Evocation School",
               "Illusion School", "Necromancy School", "Transmutation School"],
}
# Class level a subclass is chosen at
SUBCLASS_LEVEL = {"cleric": 1, "paladin": 1, "sorcerer": 1, "warlock": 1, "druid": 2, "wizard": 2}
FEAT_LEVELS = {"fighter": [4, 6, 8, 12], "rogue": [4, 8, 10, 12]}
CASTER = {"bard": "full", "cleric": "full", "druid": "full", "sorcerer": "full", "wizard": "full", "paladin": "half", "ranger": "half"}
SPELL_ABILITY = {"bard": "charisma", "cleric": "wisdom", "druid": "wisdom", "paladin": "charisma", "ranger": "wisdom", "sorcerer": "charisma",
                 "warlock": "charisma", "wizard": "intelligence", "fighter": "intelligence", "rogue": "intelligence"}
FIGHTING_STYLES = {"Archery": "archery", "Duelling": "dueling", "Great Weapon Fighting": "GWF", "Two-Weapon Fighting": "TWF", "Defence": None, "Protection": None}
FIGHTING_STYLE_LEVEL = {"fighter": 1, "paladin": 2, "ranger": 2}
# Feats the simulator models, the others only show in the notes
FEAT_FLAGS = {"Great Weapon Master": "GWM", "Sharpshooter": "sharpshooter", "Savage Attacker": "savage_attacker", "Tavern Brawler": "tavern_brawler"}
FEAT_ABILITY = {"Tavern Brawler": ("strength", "constitution"), "Athlete": ("strength", "dexterity")} # +1 to one of these (the higher)
FEATS = ["Ability Improvement", "Actor", "Alert", "Athlete", "Charger", "Crossbow Expert", "Defensive Duellist", "Dual Wielder", "Dungeon Delver",
         "Durable", "Elemental Adept", "Great Weapon Master", "Heavily Armoured", "Heavy Armour Master", "Lightly Armoured", "Lucky", "Mage Slayer",
         "Martial Adept", "Medium Armour Master", "Mobile", "Moderately Armoured", "Performer", "Polearm Master", "Resilient", "Ritual Caster",
         "Savage Attacker", "Sentinel", "Sharpshooter", "Shield Master", "Skilled", "Spell Sniper", "Tavern Brawler", "Tough", "War Caster",
         "Weapon Master"]
RACES = ["Human", "High Elf", "Wood Elf", "Lolth-Sworn Drow", "Seldarine Drow", "High Half-Elf", "Wood Half-Elf", "Drow Half-Elf", "Half-Orc",
         "Lightfoot Halfling", "Strongheart Halfling", "Gold Dwarf", "Shield Dwarf", "Duergar", "Forest Gnome", "Deep Gnome", "Rock Gnome",
         "Asmodeus Tiefling", "Mephistopheles Tiefling", "Zariel Tiefling", "Githyanki", "Black Dragonborn", "Copper Dragonborn", "Blue Dragonborn",
         "Bronze Dragonborn", "Brass Dragonborn", "Gold Dragonborn", "Red Dragonborn", "Green Dragonborn", "Silver Dragonborn", "White Dragonborn"]
# Weapon proficiencies: "simple", "martial" or a base weapon. The first class gives all of these, a multiclass only some (bg3.wiki)
CLASS_WEAPONS = {
    "barbarian": {"simple", "martial"}, "bard": {"simple", "Hand Crossbow", "Rapier", "Longsword", "Shortsword"}, "cleric": {"simple", "Flail", "Morningstar"},
    "druid": {"Club", "Dagger", "Javelin", "Mace", "Quarterstaff", "Scimitar", "Sickle", "Spear"}, "fighter": {"simple", "martial"},
    "monk": {"simple", "Shortsword"}, "paladin": {"simple", "martial"}, "ranger": {"simple", "martial"},
    "rogue": {"simple", "Hand Crossbow", "Longsword", "Rapier", "Shortsword"}, "sorcerer": {"Dagger", "Quarterstaff", "Light Crossbow"},
    "warlock": {"simple"}, "wizard": {"Dagger", "Quarterstaff", "Light Crossbow"},
}
MULTICLASS_WEAPONS = {"barbarian": {"simple", "martial"}, "cleric": {"Flail", "Morningstar"}, "fighter": {"simple", "martial"}, "monk": {"simple", "Shortsword"},
                      "paladin": {"simple", "martial"}, "ranger": {"simple", "martial"}, "warlock": {"simple"}}
SUBCLASS_WEAPONS = {"The Hexblade": {"martial"}, "War Domain": {"martial"}, "Tempest Domain": {"martial"}, "Death Domain": {"martial"},
                    "College of Valour": {"martial"}, "Bladesinging": {"Dagger", "Longsword", "Rapier", "Scimitar", "Shortsword", "Sickle"}}
RACE_WEAPONS = {
    **{r: {"Spear", "Pike", "Halberd", "Glaive"} for r in ("Human", "High Half-Elf", "Wood Half-Elf", "Drow Half-Elf")},
    **{r: {"Shortsword", "Longsword", "Shortbow", "Longbow"} for r in ("High Elf", "Wood Elf")},
    **{r: {"Rapier", "Shortsword", "Hand Crossbow"} for r in ("Lolth-Sworn Drow", "Seldarine Drow")},
    **{r: {"Battleaxe", "Handaxe", "Light Hammer", "Warhammer"} for r in ("Gold Dwarf", "Shield Dwarf", "Duergar")},
    "Githyanki": {"Shortsword", "Longsword", "Greatsword"},
}

def weapon_proficiencies(character, level=MAX_LEVEL):
    """ Weapon categories and base weapons the character is proficient with at a level """
    order = class_order(character, level)
    profs = set(CLASS_WEAPONS.get(order[0], set())) if order else set()
    for cls in set(order[1:]) - {order[0]}:
        profs |= MULTICLASS_WEAPONS.get(cls, set())
    levels = class_levels(character, level)
    for cls, n in levels.items():
        profs |= SUBCLASS_WEAPONS.get(subclass_of(character, cls, n), set())
    profs |= RACE_WEAPONS.get(character.race, set())
    return profs

def is_proficient(base, profs):
    """ Whether a base weapon (i.e. 'Greatsword') is covered by proficiencies, unknown weapons count as proficient """
    w = weapons().get(base)
    return w is None or base in profs or w.get("category") in profs

# How the character attacks each turn. Weapons are the default ones for the style until gear replaces them
ROUTINES = {
    "two_handed": "Two-handed weapon", "one_handed": "One-handed weapon (Duelling)", "dual_wield": "Two weapons", "ranged": "Ranged weapon",
    "unarmed": "Unarmed strikes", "thrown": "Thrown weapon", "cantrip": "Attack cantrip", "shadow_blade": "Shadow Blade (and an off-hand weapon)",
    "shadow_blade_shield": "Shadow Blade and a shield (Duelling applies)", "polearm": "Polearm (Glaive: reach, Polearm Master)",
    "dual_hand_crossbows": "Two hand crossbows",
}
SHADOW_BLADE = "Shadow Blade"
DEFAULT_WEAPONS = {"two_handed": "Greatsword", "polearm": "Glaive", "one_handed": "Longsword", "dual_wield": "Shortsword", "ranged": "Longbow", "thrown": "Handaxe",
                   "dual_hand_crossbows": "Hand Crossbow"}
RANGED_ROUTINES = ("ranged", "dual_hand_crossbows")
# Damage spells cast with spell slots before falling back to the attack cantrip
LEVELLED_SPELLS = ["Magic Missile", "Guiding Bolt", "Inflict Wounds", "Burning Hands", "Thunderwave", "Scorching Ray", "Shatter", "Fireball", "Spirit Guardians",
                   "Lightning Bolt", "Blight", "Cone of Cold", "Dethrone", "Chain Lightning", "Disintegrate", "Circle of Death"]
POLEARMS = {"Glaive", "Halberd", "Pike", "Quarterstaff", "Spear"}
CANTRIPS = ["Eldritch Blast", "Fire Bolt", "Ray of Frost", "Sacred Flame", "Toll the Dead", "Chill Touch", "Shocking Grasp", "Produce Flame", "Thorn Whip",
            "Bursting Sinew"]
# Options that need the build to set something up, all on by default
TOGGLES = {
    "rage": "Rage every fight", "reckless": "Reckless Attack (advantage)", "smite": "Smite with spell slots", "vow": "Oath buff (Vow of Enmity, "
    "Sacred Weapon or Righteous Clarity)", "curse": "Hexblade's Curse on the target", "surprise": "Enemies are surprised (Assassin)",
    "manifestation": "Manifestation of Body (Open Hand)", "damaged_target": "Target is already damaged (Colossus Slayer)",
    "starry_form": "Starry Form: Archer (Circle of Stars)", "symbiotic": "Symbiotic Entity (Circle of Spores)",
    "storm_close": "Enemies within 6 m when casting (Heart of the Storm)",
    "booming_blade": "Booming Blade on the first melee attack each turn",
    "offhand_crossbow": "Off-hand hand crossbow shot (the bonus action of casters with two hand crossbows in the ranged slots)",
    "spirit_guardians": "Spirit Guardians first, then the build's own spell (Cleric 5; pick it as the levelled spell to cast nothing else)",
    "spiritual_weapon": "Spiritual Weapon every fight (Cleric 3: a summoned weapon with its own attack each round, for a level 2+ slot)",
    "bladesong": "Bladesong in fights (+2/+3/+4 AC without medium or heavy armour or a shield)",
    "horde_breaker": "Horde Breaker instead of Colossus Slayer (an extra attack on a second enemy, needs 2+ enemies)",
    "reactions": "Reaction attacks: Polearm Master when an enemy enters your reach (about once a fight), Sentinel when an enemy next to you "
    "attacks an ally (about every other round)",
    "honour_mode": "Honour Mode rules: Haste's and Bloodlust's extra action is one attack (not a full Attack action), and Pact of the Blade's "
    "Extra Attack doesn't stack with another class's",
    "illithid": "Illithid powers: Psionic Overload (+1d4 psychic on every attack roll), Favourable Beginnings (+proficiency to hit on the "
    "first attack of a fight), Luck of the Far Realms (one hit a day becomes a critical hit)",
    "advantage": "Attack with advantage (Shadow Blade in darkness or dim light, hiding, Dirty Tricks, Faerie Fire, Darkness with Devil's Sight)",
}
# Toggles that are off unless ticked: advantage depends on the fight, so it isn't assumed
TOGGLE_DEFAULTS = {"advantage": False, "horde_breaker": False, "honour_mode": False, "spiritual_weapon": False, "offhand_crossbow": False, "spirit_guardians": False, "illithid": False}
# The class (and subclass) each toggle is for, so the builder only offers the ones that matter
TOGGLE_FOR = {"rage": ("barbarian", ""), "reckless": ("barbarian", ""), "smite": ("paladin", ""), "vow": ("paladin", ""),
              "curse": ("warlock", "The Hexblade"), "surprise": ("rogue", "Assassin"), "manifestation": ("monk", "Way of the Open Hand"),
              "damaged_target": ("ranger", "Hunter"), "starry_form": ("druid", "Circle of Stars"), "symbiotic": ("druid", "Circle of Spores"),
              "storm_close": ("sorcerer", "Storm Sorcery"),
              "booming_blade": [("wizard", ""), ("sorcerer", ""), ("warlock", ""), ("fighter", "Eldritch Knight"), ("rogue", "Arcane Trickster")],
              "horde_breaker": ("ranger", "Hunter"), "spirit_guardians": ("cleric", ""), "spiritual_weapon": ("cleric", ""), "offhand_crossbow": [(cls, "") for cls in ("bard", "cleric", "druid", "sorcerer", "warlock", "wizard")], "reactions": [(cls, "") for cls in CLASSES], "honour_mode": [(cls, "") for cls in CLASSES], "illithid": [(cls, "") for cls in CLASSES], "bladesong": ("wizard", "Bladesinging"), "advantage": [(cls, "") for cls in CLASSES]}

def relevant_toggles(classes):
    """ Toggles for a [class, subclass, levels] list """
    def matches(owners):
        owners = owners if isinstance(owners, list) else [owners]
        return any(c == cls and (not sub or s == sub) for cls, sub in owners for c, s, *_ in classes)
    return [k for k, owners in TOGGLE_FOR.items() if matches(owners)]

@dataclass
class Bg3Character:
    name: str = "Tav"
    race: str = "Human"
    scores: dict[str, int] = field(default_factory=lambda: {"strength": 15, "dexterity": 14, "constitution": 15, "intelligence": 8, "wisdom": 10, "charisma": 8})
    bonus: dict[str, int] = field(default_factory=lambda: {"strength": 2, "constitution": 1}) # +2/+1 at character creation
    classes: list[list] = field(default_factory=lambda: [["fighter", "Champion", 12]]) # [class, subclass, levels] in the order they are taken
    feats: list[str] = field(default_factory=list) # Per feat level in order: a feat name, or an improvement like 'strength+2'
    fighting_styles: list[str] = field(default_factory=list) # In the order they are gained
    routine: str = "two_handed"
    cantrip: str = "Eldritch Blast"
    spell: str = "" # A levelled damage spell cast with every slot high enough, before the cantrip (cantrip routine)
    toggles: dict = field(default_factory=dict) # TOGGLES (all on by default), and "ancestry" for Draconic Bloodline (default fire)
    level_order: list[str] = field(default_factory=list) # The class taken at each level when it isn't "first class first", i.e. a 1 level dip first
    boons: dict[str, int] = field(default_factory=dict) # Permanent ability bonuses from the story: Auntie Ethel's Hair (+1), Mirror of Loss (+2)
    # Character level: [[class, subclass, levels]] the character is respecced to at that level, when the levelling order doesn't give it
    # (i.e. a pure Wizard until the multiclass comes together at 12)
    respec: dict[str, list] = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        names = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in names})

    def toggle(self, key):
        return self.toggles.get(key, TOGGLE_DEFAULTS.get(key, True))

def class_order(character, level=MAX_LEVEL):
    """ The class of each character level, i.e. ['fighter', 'fighter', 'rogue', ...] up to level """
    split = (character.respec or {}).get(str(level))
    if split and sum(int(n) for _, _, n in split) == level:
        return [cls for cls, _, n in split for _ in range(int(n))]
    order = [cls for cls, _, levels in character.classes for _ in range(int(levels))]
    if character.level_order and sorted(character.level_order) == sorted(order):
        order = list(character.level_order)
    return order[:level]

def class_levels(character, level=MAX_LEVEL):
    counts = {}
    for cls in class_order(character, level):
        counts[cls] = counts.get(cls, 0) + 1
    return counts

def subclass_of(character, cls, class_level):
    for c, sub, _ in [*character.classes, *(row for split in (character.respec or {}).values() for row in split)]:
        if c == cls and class_level >= SUBCLASS_LEVEL.get(cls, 3):
            return sub
    return ""

def feat_opportunities(character, level=MAX_LEVEL):
    """ (character level, class) for every feat or improvement gained by a level """
    seen, out = {}, []
    for lv, cls in enumerate(class_order(character, level), start=1):
        seen[cls] = seen.get(cls, 0) + 1
        if seen[cls] in FEAT_LEVELS.get(cls, [4, 8, 12]):
            out.append((lv, cls))
    return out

def caster_level(levels, subclasses):
    """ Multiclass spellcaster level: full casters count fully, half casters half (rounded down), Eldritch Knights and Arcane Tricksters a third.
        A single class half or third caster rounds up """
    full = sum(n for cls, n in levels.items() if CASTER.get(cls) == "full")
    half = [n for cls, n in levels.items() if CASTER.get(cls) == "half"]
    third = sum(n for cls, n in levels.items() if subclasses.get(cls) in ("Eldritch Knight", "Arcane Trickster"))
    casting_classes = sum(1 for cls in levels if cls in CASTER) + sum(1 for cls in levels if subclasses.get(cls) in ("Eldritch Knight", "Arcane Trickster"))
    if casting_classes == 1 and len(half) == 1:
        return ceil(half[0] / 2) if half[0] >= 2 else 0
    if casting_classes == 1 and third and not full:
        return ceil(third / 3) if third >= 3 else 0 # Single class third casters round up too: level 2 slots at 7, level 3 at 13
    # Several casting classes: the fractions are summed first, then rounded down (bg3.wiki, Spells: effective spellcaster level)
    return (6 * full + 3 * sum(half) + 2 * third) // 6

def warlock_pact_slots(warlock_level):
    """ (pact slots per short rest, pact slot level) """
    if not warlock_level:
        return 0, 0
    slots = 1 if warlock_level == 1 else 2 if warlock_level < 11 else 3
    return slots, min(5, (warlock_level + 1) // 2)

def compile_character(character, level=MAX_LEVEL, main_finesse=None):
    """ The Character at a level, and notes on what is and isn't modelled. main_finesse: whether the main hand weapon from gear is finesse
        or ranged (Sneak Attack, Flick o' the Wrist), None to go by the routine's default weapon """
    level = max(1, min(int(level), MAX_LEVEL, len(class_order(character))))
    levels = class_levels(character, level)
    subs = {cls: subclass_of(character, cls, n) for cls, n in levels.items()}
    notes = []

    # Ability scores: point buy and the +2/+1, then feats and improvements in the order they are gained
    scores = starting_scores(character.scores, character.bonus)
    feats = []
    for _, choice in zip(feat_opportunities(character, level), character.feats):
        if "+" in choice:
            scores = apply_improvement(scores, choice)
        else:
            feats.append(choice)
            if choice in FEAT_ABILITY:
                stat = max(FEAT_ABILITY[choice], key=lambda s: scores[s])
                scores = apply_improvement(scores, f"{stat}+1")
    for stat, amount in (character.boons or {}).items():
        if stat in STATS: # The hair stops at 20 like an improvement, the Mirror of Loss at 24
            scores[stat] = max(scores[stat], min(scores[stat] + int(amount), 24 if int(amount) >= 2 else 20))
    c = Character(name=character.name, level=level, **scores)
    for feat in feats:
        if feat in FEAT_FLAGS:
            setattr(c, FEAT_FLAGS[feat], True)
        elif feat not in ("Dual Wielder", "Polearm Master", "Athlete", "Sentinel"):
            notes.append(f"{feat}: not modelled")
    c.savage_attacker_per_die = c.savage_attacker # BG3 Savage Attacker keeps the higher of each die
    styles = [s for s in character.fighting_styles if FIGHTING_STYLES.get(s)]
    allowed_styles = sum(levels.get(cls, 0) >= lv for cls, lv in FIGHTING_STYLE_LEVEL.items()) + (levels.get("fighter", 0) >= 10 and subs.get("fighter") == "Champion")
    allowed_styles += levels.get("bard", 0) >= 3 and subs.get("bard") == "College of Swords"
    for style in styles[:allowed_styles]:
        setattr(c, FIGHTING_STYLES[style], True)

    # Race
    if character.race == "Half-Orc":
        c.savage_attacks_half_orc = True
    if character.race.endswith("Halfling"):
        c.attack_reroll_on = 1 # Halfling Luck

    attacks = _attacks(character, c, levels, subs, feats, notes, main_finesse)
    if character.routine == "cantrip" and character.toggle("offhand_crossbow"):
        # A caster with two hand crossbows: the action goes to spells, the bonus action to an off-hand shot
        attacks.append(weapon_attack("Hand Crossbow", ability_stat="dexterity", offhand=True))
    profs = weapon_proficiencies(character, level)
    if "Weapon Master" in feats:
        profs |= {weapon_base(a) for a in attacks} # Four weapons of your choice, assumed to be the ones used
    for a in attacks:
        if a.is_weapon and not is_proficient(weapon_base(a), profs):
            a.proficient = False
            notes.append(f"Not proficient with {weapon_base(a)}s")
    c.attacks = attacks
    if character.toggle("booming_blade") and "booming_blade" in relevant_toggles(character.classes):
        _booming_blade(c, character)
        if levels.get("fighter", 0) >= 7 and subs.get("fighter") == "Eldritch Knight":
            _war_magic(c)
    _class_features(character, c, levels, subs, notes, main_finesse)
    _cleric_spells(character, c, levels, subs, notes)
    c.casting_stat = item_casting_stat(character, level)
    if character.toggle("illithid"):
        _illithid_powers(c)
    split = " / ".join(f"{cls.title()} {n}" + (f" ({subs[cls]})" if subs.get(cls) else "") for cls, n in levels.items())
    c.description = f"{character.race}, {split}. Feats: {', '.join(feats) or 'none'}"
    return c, notes

def weapon_base(attack):
    """ The base weapon of an attack: 'Greatsword' for 'Greatsword (Action Surge)' or a named greatsword """
    return attack.base or attack.stem

def _extra_attacks(levels, subs, character):
    """ Attacks with the Attack action. Pact of the Blade's Extra Attack (Warlock 5) stacks with another class's outside Honour Mode
        (bg3.wiki, Deepened Pact), with the pact weapon: a melee weapon or Shadow Blade bound with Bind Pact (or Hexed) Weapon """
    attacks = _class_extra_attacks(levels, subs, character)
    pact_weapon = character.routine in ("two_handed", "polearm", "one_handed", "shadow_blade", "shadow_blade_shield")
    if attacks >= 2 and levels.get("warlock", 0) >= 5 and pact_weapon and not character.toggle("honour_mode") and not _only_warlock(levels, subs):
        attacks += 1
    return attacks

def _only_warlock(levels, subs):
    """ Whether the Warlock's Deepened Pact is the build's only Extra Attack """
    return _class_extra_attacks({k: v for k, v in levels.items() if k != "warlock"}, subs, None) < 2

def _class_extra_attacks(levels, subs, character):
    attacks = 1
    if levels.get("fighter", 0) >= 11:
        attacks = 3
    elif any(levels.get(cls, 0) >= 5 for cls in ("fighter", "barbarian", "paladin", "ranger", "monk")):
        attacks = 2
    elif levels.get("bard", 0) >= 6 and subs.get("bard") in ("College of Swords", "College of Valour"):
        attacks = 2
    elif levels.get("wizard", 0) >= 6 and subs.get("wizard") == "Bladesinging":
        attacks = 2
    elif levels.get("warlock", 0) >= 5 and character is not None and character.routine != "cantrip": # Pact of the Blade, Deepened Pact
        attacks = 2
    return attacks

SPIRIT_GUARDIANS, SPIRITUAL_WEAPON = "Spirit Guardians", "Spiritual Weapon"
# Fights are taken as this long when a spell only covers some of the day's fights: its rounds are spread as that share of every fight
ROUNDS_PER_FIGHT = 3

def wants_guardians(character):
    """ Spirit Guardians as the build's spell, or cast first on top of another spell (the toggle) """
    return character.spell == SPIRIT_GUARDIANS or character.toggle("spirit_guardians")

def cleric_slots(character, levels, subs):
    """ The slot levels a Cleric spends on (Spirit Guardians, Spiritual Weapon) in a day, one cast of each per fight while slots last.
        Spirit Guardians takes the best slots and Spiritual Weapon the best of the rest. Another damage spell changes that: one of
        level 4 or more keeps its own slots, a lower one leaves Spiritual Weapon the lowest """
    cleric = levels.get("cleric", 0)
    slots = sorted((lv for lv, n in enumerate(spell_slots(caster_level(levels, subs)), start=1) for _ in range(n)), reverse=True)
    # A spell of level 4 or more keeps its own slots (one, when it is cast once a day), Spirit Guardians has the best of the rest
    other = spells().get(character.spell) if character.spell not in ("", SPIRIT_GUARDIANS) else None
    kept = sorted(lv for lv in slots if lv >= other["level"]) if other and other["level"] > 3 else []
    kept = kept[:1] if other and other.get("recharge") else kept
    guardians = []
    if wants_guardians(character) and cleric >= 5:
        free = list(slots)
        for lv in kept:
            free.remove(lv)
        guardians = [lv for lv in free if lv >= 3][:FIGHTS_PER_LONG_REST]
        for lv in guardians:
            slots.remove(lv)
    weapon = []
    if character.toggle("spiritual_weapon") and cleric >= 3:
        for lv in kept:
            slots.remove(lv)
        pool = slots if kept or not other else slots[::-1] # A low level spell is cast with every slot left, so it has the better ones
        weapon = [lv for lv in pool if lv >= 2][:FIGHTS_PER_LONG_REST]
    return guardians, weapon

def _fight_rounds(casts):
    """ Rounds per fight a spell that lasts the whole fight is up, from its casts a day: every round with a cast for each fight,
        else that share of the rounds """
    return 10.0 if casts >= FIGHTS_PER_LONG_REST else round(casts / FIGHTS_PER_LONG_REST * ROUNDS_PER_FIGHT, 2)

def _dice(mean, die=8):
    """ An average number of dice as whole dice plus the rest as a flat bonus: 4.5 -> ('4d8', 2) """
    whole = int(mean)
    return f"{whole}d{die}", round((mean - whole) * (die + 1) / 2)

def _cleric_spells(character, c, levels, subs, notes):
    """ Spirit Guardians and Spiritual Weapon (bg3.wiki), added to the character's attacks.
        Spirit Guardians: an action and a level 3+ slot, 3d8 (+1d8 a slot level) radiant to every enemy within 3 m each round, WIS save for
        half, for the fight. Casting it takes the action of round 1, so the attacks made with the action start in round 2.
        Spiritual Weapon: a bonus action and a level 2+ slot, a summoned weapon that attacks on its own turn every round for
        1d8 + 1 + the spellcasting modifier force (+1d8 per two slot levels), with the caster's spell attack bonus """
    guardians, weapon = cleric_slots(character, levels, subs)
    wisdom = max(c.wisdom_ability_modifier, 0)
    if wants_guardians(character) and not guardians:
        notes.append("Spirit Guardians needs a level 5 Cleric with a level 3 spell slot")
    if guardians:
        dice, rest = _dice(sum(lv for lv in guardians) / len(guardians)) # 3d8 from a level 3 slot, one more die a level
        necrotic = subs.get("cleric") == "Death Domain"
        cast = Attack(name=f"{SPIRIT_GUARDIANS} (cast)", base=SPIRIT_GUARDIANS, label="cast", tags=["setup"], type="spell", ability_stat="wisdom", damage="0",
                      always_hit=True, once_per_turn_eligible=False, uses_per_fight=round(min(len(guardians) / FIGHTS_PER_LONG_REST, 1.0), 2))
        # Whatever the action does first (a limited spell or rider included) waits for the cast; what follows it chains on
        for a in c.attacks:
            if a.action == "action" and not a.fallback_for:
                a.fallback_for, a.tags = cast.name, [*a.tags, *([] if a.uses_per_fight else ["after_cast"])]
        aura = spell_attacks(SPIRIT_GUARDIANS, ability_stat="wisdom", slot_level=3, ruleset="bg3")[0]
        aura = replace(aura, name=f"{SPIRIT_GUARDIANS} (aura)", label="aura", tags=["aura"], damage=dice + (f"+{rest}" if rest else ""),
                       damage_type="necrotic" if necrotic else "radiant", uses_per_fight=_fight_rounds(len(guardians)), once_per_turn_eligible=False)
        c.attacks = [cast, *c.attacks, aura]
    if weapon:
        dice, rest = _dice(sum(1 + (lv - 2) // 2 for lv in weapon) / len(weapon))
        c.attacks.append(Attack(name=SPIRITUAL_WEAPON, base=SPIRITUAL_WEAPON, tags=["summon"], action="bonus", type="spell", ability_stat="wisdom",
                                damage=f"{dice}+{1 + wisdom + rest}", damage_type="force", once_per_turn_eligible=False,
                                uses_per_fight=_fight_rounds(len(weapon))))
    elif character.toggle("spiritual_weapon") and levels.get("cleric"):
        notes.append("Spiritual Weapon needs a level 3 Cleric with a level 2 spell slot")

def _attacks(character, c, levels, subs, feats, notes, main_finesse=None):
    routine = character.routine
    if routine == "cantrip":
        stat = max((SPELL_ABILITY[cls] for cls in levels if cls in SPELL_ABILITY), key=lambda s: getattr(c, s), default="charisma")
        if character.cantrip == "Eldritch Blast" and not levels.get("warlock"):
            notes.append("Eldritch Blast needs a warlock level (or Spell Sniper)")
        beams = spell_attacks(character.cantrip, ability_stat=stat, character_level=c.level, ruleset="bg3")
        cantrip = [replace(a, name=f"{a.name} {ii + 1}" if len(beams) > 1 else a.name) for ii, a in enumerate(beams)]
        druid = levels.get("druid", 0)
        if not character.spell or character.spell == SPIRIT_GUARDIANS:
            if druid >= 2 and subs.get("druid") == "Circle of Stars":
                # Star Map: Guiding Bolt without a spell slot (2, 3 at 5, 4 at 9 per long rest)
                bolts = [replace(a, uses_per_fight=per_fight(per_long_rest=2 + (druid >= 5) + (druid >= 9)))
                         for a in spell_attacks("Guiding Bolt", ability_stat=stat, slot_level=1, ruleset="bg3")]
                for a in cantrip:
                    a.fallback_for = bolts[0].name
                return bolts + cantrip
            return cantrip
        spell_level = spells()[character.spell]["level"]
        slots = spell_slots(caster_level(levels, subs))
        pact, pact_level = warlock_pact_slots(levels.get("warlock", 0))
        # Less the slots Spirit Guardians and Spiritual Weapon take
        spent = sum(lv >= spell_level for taken in cleric_slots(character, levels, subs) for lv in taken)
        casts = per_fight(per_long_rest=sum(slots[spell_level - 1:]) - spent, per_short_rest=pact if pact_level >= spell_level else 0)
        if casts and spells()[character.spell].get("recharge") == "long_rest":
            casts = min(casts, round(1 / FIGHTS_PER_LONG_REST, 2)) # Once a day, i.e. Dethrone
        if not casts:
            notes.append(f"No spell slots of level {spell_level} or higher for {character.spell} yet")
            return cantrip
        levelled = spell_attacks(character.spell, ability_stat=stat, slot_level=spell_level, ruleset="bg3")
        for a in levelled:
            a.uses_per_fight = casts
        for a in cantrip:
            a.fallback_for = character.spell # Cast once the slots run out
        return levelled + cantrip

    # Bind Hexed Weapon (Hexblade) or Pact of the Blade (Warlock 3): the bound main hand melee weapon uses Charisma. One weapon only,
    # so not the off hand, and it can't be thrown (bg3.wiki, Bind Pact Weapon)
    hexblade = (subs.get("warlock") == "The Hexblade" or levels.get("warlock", 0) >= 3) and routine not in (*RANGED_ROUTINES, "thrown")
    def stat_for(weapon_stat):
        if hexblade and c.charisma > getattr(c, weapon_stat):
            return "charisma"
        return weapon_stat
    count = _extra_attacks(levels, subs, character)
    if routine == "unarmed":
        stat = "dexterity" if c.dexterity >= c.strength else "strength"
        monk = levels.get("monk", 0)
        die = 4 + 2 * ((monk >= 3) + (monk >= 9)) if monk else 0
        strike = Attack(name="Unarmed Strike", type="unarmed", ability_stat=stat, damage=f"1d{die}" if die else "1", damage_type="bludgeoning")
        attacks = [replace(strike) for _ in range(count)]
        if monk:
            attacks.append(strike.variant("Martial Arts", action="bonus")) # Bonus action strike
            ki = monk + 1
            attacks.append(replace(strike, name="Flurry of Blows", uses_per_fight=per_fight(per_short_rest=ki), action="bonus"))
        return attacks

    if routine in ("shadow_blade", "shadow_blade_shield"):
        blades = _shadow_blade_attacks(c, levels, subs, count, stat_for, notes, shield=routine == "shadow_blade_shield")
        surge = action_surge(levels.get("fighter", 0), "bg3", replace(blades[0])) if not blades[0].offhand else []
        return blades + _reaction_attacks(character, blades[0], weapon_base(blades[0]), feats, routine) + surge
    name = DEFAULT_WEAPONS[routine]
    weapon_stat = "dexterity" if routine in ("ranged", "dual_wield", "dual_hand_crossbows") else "strength"
    if routine == "one_handed" and c.dexterity > c.strength:
        name, weapon_stat = "Rapier", "dexterity" # Finesse
    main = weapon_attack(name, ability_stat=stat_for(weapon_stat))
    if routine == "thrown":
        main = replace(main, type="thrown", name=f"{name} (Thrown)", label="Thrown")
    attacks = [replace(main) for _ in range(count)]
    bonus_actions = 2 if levels.get("rogue", 0) >= 3 and subs.get("rogue") == "Thief" else 1 # Fast Hands
    if routine in ("dual_wield", "dual_hand_crossbows"):
        # The off-hand attack takes the bonus action; it adds the ability modifier only with Two-Weapon Fighting
        offhand = weapon_attack("Longsword" if "Dual Wielder" in feats and routine == "dual_wield" else name, ability_stat=weapon_stat, offhand=True)
        attacks += [replace(offhand) for _ in range(bonus_actions)]
        bonus_actions = 0
    # Bonus action attacks: Frenzy, Polearm Master butt end, Swashbuckler Dirty Tricks, War Priest
    if bonus_actions and levels.get("barbarian", 0) >= 3 and subs.get("barbarian") == "Berserker" and character.toggle("rage"):
        # Frenzied Strike, or Enraged Throw for throwing builds
        attacks.append(main.variant("Enraged Throw" if routine == "thrown" else "Frenzy", action="bonus"))
        bonus_actions -= 1
    if bonus_actions and "Polearm Master" in feats and name in POLEARMS:
        # The other end of the same weapon: Great Weapon Fighting and Great Weapon Master apply to it as to the blade
        attacks.append(replace(main, name="Polearm Butt End", label="", damage="1d4", damage_type="bludgeoning", action="bonus", tags=["butt_end"]))
        bonus_actions -= 1
    finesse = _finesse_or_ranged(main) if main_finesse is None else main_finesse
    if bonus_actions and levels.get("rogue", 0) >= 4 and subs.get("rogue") == "Swashbuckler" and routine not in RANGED_ROUTINES and finesse:
        # Dirty Trick: Flick o' the Wrist needs a finesse weapon in the main hand (bg3.wiki)
        attacks.append(main.variant("Flick o' the Wrist", action="bonus"))
        bonus_actions -= 1
    if bonus_actions and levels.get("cleric") and subs.get("cleric") == "War Domain":
        charges = 3 + (levels["cleric"] >= 5) + (levels["cleric"] >= 8) + (levels["cleric"] >= 11)
        attacks.append(main.variant("War Priest", action="bonus", uses_per_fight=per_fight(per_long_rest=charges)))
    attacks += _reaction_attacks(character, main, name, feats, routine)
    if levels.get("fighter", 0) >= 2:
        attacks += action_surge(levels["fighter"], "bg3", replace(main))
    if levels.get("ranger", 0) >= 3 and subs.get("ranger") == "Gloom Stalker":
        attacks.append(main.variant("Dread Ambusher", uses_per_fight=1, bonus_damage_die_mod_list=[*main.bonus_damage_die_mod_list, "1d8"]))
    return attacks

# Flexible Casting (Sorcerer 2): sorcery points into a spell slot, the cost by slot level (5e and BG3)
SLOT_COST = {1: 2, 2: 3, 3: 5, 4: 6, 5: 7}

def smite_slots(character, levels, subs):
    """ Slot levels a day for smites: long rest slots, pact slots (back on each short rest), slots made from sorcery points, less the
        slot Shadow Blade is cast with once a day (it lasts until a long rest; with a pact slot it comes back on the next short rest) """
    slots = [level for level, count in enumerate(spell_slots(caster_level(levels, subs)), start=1) for _ in range(count)]
    pact, pact_level = warlock_pact_slots(levels.get("warlock", 0))
    day = slots + [pact_level] * pact * (SHORT_RESTS_PER_LONG_REST + 1)
    points = levels.get("sorcerer", 0) if levels.get("sorcerer", 0) >= 2 else 0
    while points >= 2 and day:
        level = max(lv for lv, cost in SLOT_COST.items() if cost <= points and lv <= max(day))
        day.append(level)
        points -= SLOT_COST[level]
    if character.routine in ("shadow_blade", "shadow_blade_shield") and shadow_blade_dice(levels, subs):
        cast = max(slots, default=0)
        if cast >= pact_level and cast in day: # Cast with a long rest slot (a pact slot comes back after a short rest)
            day.remove(cast)
    return sorted(day, reverse=True)

def knows_shadow_blade(levels, subs):
    """ Shadow Blade is on the Sorcerer, Warlock and Wizard lists (and the Eldritch Knight's and Arcane Trickster's, which use the Wizard's) """
    return any(levels.get(cls) for cls in ("sorcerer", "warlock", "wizard")) or \
        subs.get("fighter") == "Eldritch Knight" or subs.get("rogue") == "Arcane Trickster"

# Reaction attacks per fight (an estimate): Polearm Master's attack when an enemy enters your reach, about once a fight as enemies close in;
# Sentinel's when an enemy next to you attacks an ally, about every other round of a 3 round fight
POLEARM_REACTIONS, SENTINEL_REACTIONS = 1.0, 1.5

def _reaction_attacks(character, main, name, feats, routine):
    """ Reaction attacks the build's feats make likely, with the main weapon (GWM and GWF apply). Polearm Master's is an opportunity
        attack, so Sentinel gives it advantage. Items like the Halberd of Vigilance give every reaction attack advantage (bg3.build) """
    if not character.toggle("reactions") or routine in (*RANGED_ROUTINES, "cantrip", "thrown"):
        return []
    out = []
    if "Polearm Master" in feats and name in POLEARMS:
        out.append(main.variant("Polearm Master reaction", action="reaction", uses_per_fight=POLEARM_REACTIONS,
                                advantage=main.advantage or "Sentinel" in feats))
    if "Sentinel" in feats:
        out.append(main.variant("Sentinel reaction", action="reaction", uses_per_fight=SENTINEL_REACTIONS))
    return out

def shadow_blade_dice(levels, subs):
    """ Shadow Blade's dice from the highest spell slot: 2d8, 3d8 from a level 3 slot, 4d8 from a level 5 slot (even levels add nothing).
        0 without a level 2 slot or a class that learns it """
    if not knows_shadow_blade(levels, subs):
        return 0
    slots = spell_slots(caster_level(levels, subs))
    highest = max(len(slots), warlock_pact_slots(levels.get("warlock", 0))[1])
    return 0 if highest < 2 else 4 if highest >= 5 else 3 if highest >= 3 else 2

def _shadow_blade_attacks(c, levels, subs, count, stat_for, notes, shield=False):
    """ Shadow Blade in the main hand (cast before the fight with a bonus action; in BG3 it lasts until a long rest, no concentration), and a
        dagger in the off hand with the bonus action, or a shield (no off-hand attack; Duelling's +2 applies) """
    dice = shadow_blade_dice(levels, subs)
    stat = stat_for("dexterity" if c.dexterity >= c.strength else "strength") # Finesse
    if not dice:
        # Until then a Rapier (or with a shield and more Strength, a Longsword)
        fallback = "Longsword" if shield and c.strength > c.dexterity else "Rapier"
        why = "a level 2 spell slot" if knows_shadow_blade(levels, subs) else "a Sorcerer, Warlock or Wizard level"
        notes.append(f"Shadow Blade needs {why}, using a {fallback} until then")
        main = weapon_attack(fallback, ability_stat=stat_for("strength" if fallback == "Longsword" else stat))
    else:
        main = Attack(name=SHADOW_BLADE, base=SHADOW_BLADE, tags=["conjured"], type="weapon (melee)", ability_stat=stat, damage=f"{dice}d8",
                      damage_type="psychic", weapon_enhancement=0)
    if shield:
        return [replace(main) for _ in range(count)]
    offhand = weapon_attack("Dagger", ability_stat="dexterity" if c.dexterity >= c.strength else "strength", offhand=True)
    return [replace(main) for _ in range(count)] + [offhand]

def _booming_blade(c, character):
    """ Booming Blade replaces the first melee weapon attack each turn: +1d8 thunder on a hit from level 5, 2d8 from level 11 (moving damage isn't modelled) """
    if c.level < 5 or character.routine not in ("two_handed", "polearm", "one_handed", "dual_wield", "shadow_blade", "shadow_blade_shield"):
        return
    first = next((a for a in c.attacks if a.type == "weapon (melee)" and not a.offhand and not a.uses_per_fight and not a.fallback_for), None)
    if first is not None:
        c.attacks[c.attacks.index(first)] = first.variant("Booming Blade", tags=[*first.tags, "booming_blade"],
                                                          extra_damage_list=[*first.extra_damage_list, f"{1 + (c.level >= 11)}d8 thunder"])

def _war_magic(c):
    """ War Magic (Eldritch Knight 7): after casting a cantrip with the action (Booming Blade every turn), a main hand weapon attack with
        the bonus action. It takes the bonus action from the off-hand swing (bg3.wiki) """
    mains = [a for a in c.attacks if a.type == "weapon (melee)" and not a.offhand and a.action == "action" and not a.uses_per_fight and not a.fallback_for]
    plain = [a for a in mains if "booming_blade" not in a.tags]
    if not mains or not any("booming_blade" in a.tags for a in mains):
        return
    strike = (plain or mains)[-1]
    off = next((a for a in c.attacks if a.offhand and a.action == "bonus" and not a.uses_per_fight), None)
    extra = strike.variant("War Magic", action="bonus", fallback_for=off.fallback_for if off else "",
                           extra_damage_list=[d for d in strike.extra_damage_list if "thunder" not in d or "booming_blade" not in strike.tags])
    if off is not None:
        c.attacks[c.attacks.index(off)] = extra
    else:
        c.attacks.append(extra)

def _limited_rider(c, label, uses, bonus=None, extra=None, main=None, tags=()):
    """ A limited use rider on one attack each round (manoeuvres, Arcane Shots, Blade Flourish, Touch of Death), until its uses per
        fight run out: the attack (the first plain weapon attack unless main is given) gets a limited copy with the rider, made first,
        and follows it. A carrier that is itself limited (a levelled spell) shares its uses with the copy; one that already follows
        another attack (the cantrip after the spell slots) keeps its place in the chain """
    spell_carrier = main is not None
    main = main or next((a for a in c.attacks if a.is_weapon or a.type == "unarmed"), None)
    if main is None or not uses or (not spell_carrier and (main.uses_per_fight or main.fallback_for)):
        return
    with_rider = min(uses, main.uses_per_fight) if main.uses_per_fight else uses
    rider = main.variant(label, uses_per_fight=round(with_rider, 2), tags=[*main.tags, *tags],
                         bonus_damage_die_mod_list=[*main.bonus_damage_die_mod_list, *([bonus] if bonus else [])],
                         extra_damage_list=[*main.extra_damage_list, *([extra] if extra else [])])
    index = c.attacks.index(main)
    if main.uses_per_fight and main.uses_per_fight - with_rider < 0.01:
        # Every cast carries the rider: the copy takes the attack's place, and whatever followed the attack follows the copy
        for a in c.attacks:
            if a.fallback_for == main.name:
                a.fallback_for = rider.name
        c.attacks[index] = rider
        return
    if main.uses_per_fight:
        main.uses_per_fight = round(main.uses_per_fight - with_rider, 2)
    main.fallback_for = rider.name
    c.attacks.insert(index, rider)

def item_casting_stat(character, level=MAX_LEVEL):
    """ The ability items and scrolls cast with (Arcane Synergy's damage): that of the spellcasting class whose first level was taken
        last (bg3.wiki, Spells: multiclassing). toggles['item_casting'] names it when a respec changes the order, '' without a caster """
    if character.toggles.get("item_casting") in STATS:
        return character.toggles["item_casting"]
    subs = {cls: sub for cls, sub, _ in character.classes}
    def casts(cls):
        return cls not in ("fighter", "rogue") or subs.get(cls) in ("Eldritch Knight", "Arcane Trickster")
    first_levels = list(dict.fromkeys(class_order(character, level)))
    return next((SPELL_ABILITY[cls] for cls in reversed(first_levels) if cls in SPELL_ABILITY and casts(cls)), "")

def _illithid_powers(c):
    """ Illithid powers that change damage (bg3.wiki). Psionic Overload: +1d4 psychic on each of the caster's attacks for 10 turns, an
        action once a short rest (a bonus action when Awakened), taken as already up like a buff. Favourable Beginnings: the proficiency
        bonus on the first attack roll against a target, here the first attack of the fight. Luck of the Far Realms: once a long rest a
        hit becomes a critical hit, on the same kind of attack """
    for a in c.attacks:
        if not a.saving_throw and not a.always_hit and "summon" not in a.tags:
            a.extra_damage_list = [*a.extra_damage_list, "1d4 psychic"]
    main = next((a for a in c.attacks if a.action == "action" and not a.saving_throw and not a.always_hit and not a.uses_per_fight
                 and not a.fallback_for and "setup" not in a.tags), None)
    if main is None:
        return
    index = c.attacks.index(main)
    lucky = main.variant("Luck of the Far Realms", uses_per_fight=round(1 / FIGHTS_PER_LONG_REST, 2), hits_crit=True)
    first = main.variant("Favourable Beginnings", uses_per_fight=1, fallback_for=lucky.name,
                         bonus_attack_die_mod_list=[*main.bonus_attack_die_mod_list, str(c.proficiency_bonus)])
    main.fallback_for = first.name
    c.attacks[index:index] = [lucky, first]

def _quickened(c, quickens):
    """ Quickened Spell: a second cast with the bonus action for 3 sorcery points (sorcery points = sorcerer level per long rest).
        A quickened levelled spell spends one of the same spell slots, so the slots are shared between the two casts; quickens left
        over go on the cantrip once the slots have run out """
    spells_cast = [a for a in c.attacks if a.type == "spell" and a.action == "action" and "aura" not in a.tags]
    levelled = [a for a in spells_cast if a.uses_per_fight]
    if not quickens or not spells_cast:
        return
    def quick(a, uses, **changes):
        return replace(a, name=f"Quickened {a.name}", uses_per_fight=round(uses, 2), action="bonus", tags=[*a.tags, "quickened"], **changes)
    if not levelled:
        c.attacks += [quick(a, quickens) for a in spells_cast]
        return
    slots = levelled[0].uses_per_fight
    on_spell = min(quickens, slots / 2)
    for a in levelled:
        a.uses_per_fight = round(slots - on_spell, 2)
    c.attacks += [quick(a, on_spell) for a in levelled]
    if quickens - on_spell > 0.01:
        c.attacks += [quick(a, quickens - on_spell) for a in spells_cast if a.fallback_for]

def _quickened_blade(c, quickens):
    """ Quickened Booming Blade: the cantrip again with the bonus action for 3 sorcery points, a second main hand attack with its thunder
        damage. The bonus action attack made every turn (the off hand) is made in the other turns """
    blade = next((a for a in c.attacks if "booming_blade" in a.tags), None)
    if blade is None or not quickens:
        return
    quick = blade.variant("Quickened Booming Blade", action="bonus", uses_per_fight=round(quickens, 2), tags=[*blade.tags, "quickened"])
    usual = [a for a in c.attacks if (a.action == "bonus" or a.offhand) and a.is_weapon and not a.uses_per_fight and not a.fallback_for]
    if usual:
        usual[-1].fallback_for = quick.name
    c.attacks.append(quick)

def _finesse_or_ranged(attack):
    """ Shadow Blade is finesse; other weapons by their base weapon's properties """
    base = weapon_base(attack)
    if base == SHADOW_BLADE or attack.type in ("weapon (ranged)",):
        return True
    data = weapons().get(base)
    return bool(data) and (data["kind"] == "ranged" or "finesse" in data.get("properties", []))

def _once_per_turn(c, name, dice, uses=0, damage_type=""):
    """ Adds once per turn damage. Sources with the same limit and damage type share a pool; others get their own (Sneak Attack every
        round next to radiant smites that run out), so each keeps its uses and its resistances. Unlimited damage of the weapon's type
        takes the main pool, which items that add Sneak Attack damage build on """
    dice = dice if isinstance(dice, list) else [dice]
    main = {"dice": c.once_per_turn_die_mod_list, "uses_per_fight": c.once_per_turn_uses_per_fight, "damage_type": c.once_per_turn_damage_type}
    def same(pool):
        return (pool.get("uses_per_fight") or 0) == uses and (pool.get("damage_type") or "") == damage_type
    if not main["dice"] or same(main):
        c.once_per_turn_die_mod_list = [*c.once_per_turn_die_mod_list, *dice]
        c.once_per_turn_uses_per_fight, c.once_per_turn_damage_type = uses, damage_type
        return
    if not uses and not damage_type:
        # Swap: the limited or typed pool moves out, this one becomes the main pool
        c.once_per_turn_extra = [*c.once_per_turn_extra, {"name": "Divine Smite" if main["damage_type"] == "radiant" else "Limited", **main}]
        c.once_per_turn_die_mod_list, c.once_per_turn_uses_per_fight, c.once_per_turn_damage_type = list(dice), 0, ""
        return
    for pool in c.once_per_turn_extra:
        if same(pool):
            pool["dice"] = [*pool["dice"], *dice]
            return
    c.once_per_turn_extra = [*c.once_per_turn_extra, {"name": name, "dice": list(dice), "uses_per_fight": uses, "damage_type": damage_type, "crit_only": False}]

def _class_features(character, c, levels, subs, notes, main_finesse=None):
    weapon = character.routine not in ("cantrip",)
    fighter, barbarian, paladin, ranger, rogue = (levels.get(k, 0) for k in ("fighter", "barbarian", "paladin", "ranger", "rogue"))
    monk, warlock, sorcerer, wizard, cleric, bard = (levels.get(k, 0) for k in ("monk", "warlock", "sorcerer", "wizard", "cleric", "bard"))
    druid = levels.get("druid", 0)

    # Fighter
    if fighter >= 3 and subs.get("fighter") == "Champion":
        c.crit_on = 19
    if fighter >= 3 and subs.get("fighter") == "Battle Master" and weapon:
        dice = 4 + (fighter >= 7)
        _limited_rider(c, "Trip Attack", per_fight(per_short_rest=dice), bonus="1d10" if fighter >= 10 else "1d8")
    if fighter >= 3 and subs.get("fighter") == "Arcane Archer" and character.routine in RANGED_ROUTINES:
        arrows = 4 + 3 * (fighter >= 7) + 3 * (fighter >= 10)
        _limited_rider(c, "Arcane Shot", per_fight(per_short_rest=arrows), extra="2d6 psychic") # Beguiling Arrow
    # Barbarian
    if barbarian and character.toggle("rage"):
        c.raging, c.barbarian_level = True, barbarian
        if subs.get("barbarian") == "Giant" and barbarian >= 3:
            # Giant's Rage: the rage damage bonus is doubled for throws
            for a in c.attacks:
                if a.type == "thrown":
                    a.bonus_damage_die_mod_list = [*a.bonus_damage_die_mod_list, str(c.rage_damage)]
        if barbarian >= 6 and subs.get("barbarian") == "Giant" and weapon:
            for a in c.attacks:
                if a.is_weapon:
                    a.extra_damage_list = [*a.extra_damage_list, "1d6 fire"] # Elemental Cleaver
    if barbarian >= 2 and character.toggle("reckless") and character.routine not in RANGED_ROUTINES:
        c.advantage = True
    if character.toggle("advantage"):
        c.advantage = True
    c.brutal_critical = barbarian >= 9
    # Paladin
    if paladin >= 2 and character.toggle("smite") and character.routine not in (*RANGED_ROUTINES, "cantrip", "thrown", "unarmed"):
        day = smite_slots(character, levels, subs)
        if day:
            # Each smite is the day's average: 2d8 from a level 1 slot, +1d8 a level, at most 5d8. Fractions of a die as a flat bonus
            # Radiant, with its own uses: a melee hit only (not thrown or ranged attacks)
            mean = sum(min(1 + level, 5) for level in day) / len(day)
            dice, rest = int(mean), round((mean - int(mean)) * 4.5)
            _once_per_turn(c, "Divine Smite", [f"{dice}d8", *([str(rest)] if rest else [])], round(len(day) / FIGHTS_PER_LONG_REST, 2), "radiant")
    if paladin >= 11 and weapon:
        # Improved Divine Smite: 1d8 radiant on every melee weapon hit, typed so it takes radiant resistance or vulnerability
        for a in c.attacks:
            if a.type == "weapon (melee)":
                a.extra_damage_list = [*a.extra_damage_list, "1d8 radiant"]
    if paladin >= 3 and character.toggle("vow"):
        oath = subs.get("paladin")
        if oath == "Oath of Vengeance":
            c.advantage = True
        elif oath == "Oath of Devotion":
            c.bonus_attack_die_mod_list = [*c.bonus_attack_die_mod_list, str(max(c.charisma_ability_modifier, 0))]
        elif oath == "Oath of the Crown":
            c.bonus_attack_die_mod_list = [*c.bonus_attack_die_mod_list, str(c.proficiency_bonus)]
    # Ranger
    if ranger >= 3 and subs.get("ranger") == "Hunter" and character.toggle("horde_breaker") and weapon:
        main = next((a for a in c.attacks if a.is_weapon and not a.offhand and not a.uses_per_fight), None)
        if main is not None:
            c.attacks.append(main.variant("Horde Breaker", min_enemies=2))
    elif ranger >= 3 and subs.get("ranger") == "Hunter" and character.toggle("damaged_target") and weapon:
        _once_per_turn(c, "Colossus Slayer", "1d8")
    if ranger >= 3 and subs.get("ranger") == "Swarmkeeper":
        _once_per_turn(c, "Gathered Swarm", "1d8" if ranger >= 11 else "1d6", damage_type="psychic") # Flurry of Moths
    # Rogue: Sneak Attack, never on off-hand attacks, and only with a finesse or ranged weapon (not a greatsword or a glaive)
    finesse = any(a.is_weapon and not a.offhand and _finesse_or_ranged(a) for a in c.attacks) if main_finesse is None else main_finesse
    if rogue and character.routine != "unarmed" and not finesse:
        notes.append("Sneak Attack needs a finesse or ranged weapon, so this weapon gets none")
    if rogue and character.routine != "unarmed" and finesse:
        _once_per_turn(c, "Sneak Attack", f"{ceil(rogue / 2)}d6")
        for a in c.attacks:
            if a.offhand:
                a.once_per_turn_eligible = False
            if a.action == "reaction":
                # Sneak Attack is once per turn, and a reaction attack is on an enemy's turn: it gets its own
                a.once_per_turn_eligible = False
                a.extra_damage_list = [*a.extra_damage_list, f"{ceil(rogue / 2)}d6 {a.damage_type}"]
    if rogue >= 3 and subs.get("rogue") == "Assassin" and character.toggle("surprise"):
        c.first_round_advantage = c.first_round_auto_crit = True
    # Monk
    if monk >= 6 and subs.get("monk") == "Way of the Open Hand" and character.toggle("manifestation"):
        for a in c.attacks:
            if a.type == "unarmed":
                a.extra_damage_list = [*a.extra_damage_list, f"1d4+{max(c.wisdom_ability_modifier, 0)} necrotic"]
    # Warlock
    if warlock >= 2 and character.routine == "cantrip" and character.cantrip == "Eldritch Blast":
        c.agonizing_blast = True
    if warlock and subs.get("warlock") == "The Hexblade" and character.toggle("curse"):
        c.bonus_damage_die_mod_list = [*c.bonus_damage_die_mod_list, str(c.proficiency_bonus)]
        c.crit_on = min(c.crit_on, 20) - 1
    c.lifedrinker = warlock >= 12 and weapon
    # Sorcerer, Wizard, Cleric, Bard
    if sorcerer >= 6 and subs.get("sorcerer") == "Draconic Bloodline":
        # Elemental Affinity: Charisma to spells of the ancestry's damage type (fire, from a red, gold or brass dragon by default)
        ancestry = character.toggles.get("ancestry") or "fire"
        for a in c.attacks:
            if a.type == "spell" and a.damage_type == ancestry:
                a.bonus_damage_die_mod_list = [*a.bonus_damage_die_mod_list, str(max(c.charisma_ability_modifier, 0))]
    if sorcerer >= 3 and character.routine == "cantrip":
        _quickened(c, per_fight(per_long_rest=sorcerer // 3))
    elif sorcerer >= 3:
        _quickened_blade(c, per_fight(per_long_rest=sorcerer // 3))
    c.empowered_evocation = wizard >= 10 and subs.get("wizard") == "Evocation School"
    if cleric >= 8 and subs.get("cleric") in ("War Domain", "Tempest Domain", "Death Domain", "Life Domain", "Nature Domain", "Trickery Domain") and \
            (weapon or character.toggle("offhand_crossbow")):
        # Divine Strike: once per turn on a weapon hit, in the domain's damage type
        strike = {"Death Domain": "necrotic", "Life Domain": "radiant", "Tempest Domain": "thunder", "Trickery Domain": "poison"}
        _once_per_turn(c, "Divine Strike", "1d8", damage_type=strike.get(subs.get("cleric"), ""))
        for a in c.attacks:
            if a.type == "spell":
                a.once_per_turn_eligible = False
    if bard >= 3 and subs.get("bard") == "College of Swords" and weapon:
        inspirations = 3 + (bard >= 5) + (bard >= 10)
        _limited_rider(c, "Blade Flourish", per_fight(per_short_rest=inspirations), bonus="1d10" if bard >= 10 else "1d8" if bard >= 5 else "1d6")
    if cleric >= 2 and subs.get("cleric") == "Death Domain":
        # Touch of Death: Channel Divinity (1 charge, 2 from level 6, short rest) on a melee hit, 5 + twice the Cleric level necrotic.
        # A melee weapon or unarmed hit, or a melee spell attack (Inflict Wounds, Shocking Grasp, Thorn Whip's 9 m reach)
        touch = {"uses": per_fight(per_short_rest=1 + (cleric >= 6)), "extra": f"{5 + 2 * cleric} necrotic", "tags": ["channel_divinity"]}
        if character.routine in ("two_handed", "one_handed", "dual_wield", "unarmed"):
            _limited_rider(c, "Touch of Death", **touch)
        else:
            carrier = next((a for a in c.attacks if a.type == "spell" and "melee" in a.tags and a.action == "action"), None)
            if carrier is not None:
                _limited_rider(c, "Touch of Death", main=carrier, **touch)
    if cleric and subs.get("cleric") == "Death Domain":
        # Reaper: Necromancy cantrips that target one creature can target a second one (bg3.wiki: Toll the Dead, Bone Chill)
        for a in c.attacks:
            if a.type == "spell" and a.base in ("Toll the Dead", "Chill Touch") and a.action == "action":
                a.targets = max(a.targets, 2)
    if cleric >= 8 and subs.get("cleric") in ("Light Domain", "Knowledge Domain") and character.routine == "cantrip":
        # Potent Spellcasting: Wisdom to cleric cantrip damage
        for a in c.attacks:
            if a.type == "spell" and a.base in ("Sacred Flame", "Toll the Dead", "Produce Flame"):
                a.bonus_damage_die_mod_list = [*a.bonus_damage_die_mod_list, str(max(c.wisdom_ability_modifier, 0))]
    if paladin >= 7 and subs.get("paladin") == "Oathbreaker":
        # Aura of Hate: Charisma to melee weapon damage
        for a in c.attacks:
            if a.type == "weapon (melee)":
                a.bonus_damage_die_mod_list = [*a.bonus_damage_die_mod_list, str(max(c.charisma_ability_modifier, 0))]
    # Druid
    if druid >= 2 and subs.get("druid") == "Circle of Stars" and character.toggle("starry_form") and character.routine != "dual_wield":
        # Starry Form: Archer lasts until a long rest, Luminous Arrow is a bonus action each turn
        c.attacks.append(Attack(name="Luminous Arrow", type="spell", ability_stat="wisdom", damage_type="radiant",
                                damage=f"{1 + (druid >= 10)}d8+{max(c.wisdom_ability_modifier, 0)}"))
    if druid >= 2 and subs.get("druid") == "Circle of Spores":
        # Halo of Spores: a reaction on your own turn, necrotic to one enemy within 6 m (CON save negates), doubled by Symbiotic Entity
        die = 4 + 2 * ((druid >= 6) + (druid >= 10))
        c.attacks.append(Attack(name="Halo of Spores", base="Halo of Spores", action="reaction", type="spell", ability_stat="wisdom", damage_type="necrotic",
                                damage=f"{2 if character.toggle('symbiotic') else 1}d{die}", saving_throw=True, saving_throw_stat="constitution",
                                saving_throw_success_multiplier=0, once_per_turn_eligible=False))
    if druid >= 2 and subs.get("druid") == "Circle of Spores" and character.toggle("symbiotic"):
        for a in c.attacks:
            if a.is_weapon or a.type == "unarmed":
                a.extra_damage_list = [*a.extra_damage_list, "1d6 necrotic"]
    if sorcerer >= 6 and subs.get("sorcerer") == "Storm Sorcery" and character.toggle("storm_close"):
        # Heart of the Storm: lightning or thunder spells (cantrips too, a bug) deal half the sorcerer level to enemies within 6 m, hit or miss
        for a in c.attacks:
            if a.type == "spell" and a.damage_type in ("lightning", "thunder"):
                a.extra_damage_list = [*a.extra_damage_list, f"{sorcerer // 2} {a.damage_type}"]
                a.bonus_miss_die_mod_list = [*a.bonus_miss_die_mod_list, sorcerer // 2]
    for sub in subs.values():
        if sub and sub not in MODELLED_SUBCLASSES:
            notes.append(f"{sub}: no damage features modelled yet")

MODELLED_SUBCLASSES = {"Champion", "Battle Master", "Arcane Archer", "Berserker", "Giant", "Wild Magic", "Wildheart", "Oath of Vengeance", "Oath of Devotion",
                       "Oathbreaker", "Light Domain", "Knowledge Domain",
                       "Oath of the Crown", "Hunter", "Swarmkeeper", "Gloom Stalker", "Assassin", "Thief", "Swashbuckler", "Way of the Open Hand",
                       "Way of the Drunken Master", "The Hexblade", "Draconic Bloodline", "Evocation School", "Bladesinging", "War Domain",
                       "Tempest Domain", "Death Domain", "Life Domain", "Nature Domain", "Trickery Domain", "College of Swords", "College of Valour",
                       "Circle of Stars", "Circle of Spores", "Storm Sorcery"}

__all__ = ["Bg3Character", "compile_character", "weapon_proficiencies", "is_proficient", "class_levels", "feat_opportunities", "caster_level", "CLASSES", "SUBCLASSES", "FEATS", "RACES",
           "ROUTINES", "CANTRIPS", "LEVELLED_SPELLS", "TOGGLES", "TOGGLE_FOR",
           "relevant_toggles", "shadow_blade_dice", "SHADOW_BLADE", "STATS"]
