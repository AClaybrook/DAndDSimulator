""" BG3 character builder: race, point buy, class levels in order (multiclassing), subclasses, feats and fighting styles,
    compiled into a plain Character for the simulator at any level.

    Rules follow Patch 8 (bg3/data/rules.json, researched from bg3.wiki). Features that change damage are modelled, the rest
    are listed in the build's notes. Resources per rest are turned into average uses per fight like the presets """
from dataclasses import asdict, dataclass, field, fields, replace
from math import ceil

from bg3.abilities import apply_improvement, starting_scores
from computations.models import STATS, Attack, Character
from game_data import spell_attacks, spells, weapon_attack, weapons
from game_data.classes import action_surge, per_fight, spell_slots

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
    "unarmed": "Unarmed strikes", "thrown": "Thrown weapon", "cantrip": "Attack cantrip",
}
DEFAULT_WEAPONS = {"two_handed": "Greatsword", "one_handed": "Longsword", "dual_wield": "Shortsword", "ranged": "Longbow", "thrown": "Handaxe"}
# Damage spells cast with spell slots before falling back to the attack cantrip
LEVELLED_SPELLS = ["Magic Missile", "Guiding Bolt", "Inflict Wounds", "Burning Hands", "Thunderwave", "Scorching Ray", "Shatter", "Fireball",
                   "Lightning Bolt", "Blight", "Cone of Cold", "Chain Lightning", "Disintegrate"]
POLEARMS = {"Glaive", "Halberd", "Pike", "Quarterstaff", "Spear"}
CANTRIPS = ["Eldritch Blast", "Fire Bolt", "Ray of Frost", "Sacred Flame", "Toll the Dead", "Chill Touch", "Shocking Grasp", "Produce Flame"]
# Options that need the build to set something up, all on by default
TOGGLES = {
    "rage": "Rage every fight", "reckless": "Reckless Attack (advantage)", "smite": "Smite with spell slots", "vow": "Oath: Vow of Enmity, "
    "Sacred Weapon or Righteous Clarity", "curse": "Hexblade's Curse on the target", "surprise": "Enemies are surprised (Assassin)",
    "manifestation": "Manifestation of Body (Open Hand)", "damaged_target": "Target is already damaged (Colossus Slayer)",
    "starry_form": "Starry Form: Archer (Circle of Stars)", "symbiotic": "Symbiotic Entity (Circle of Spores)",
    "storm_close": "Enemies within 6 m when casting (Heart of the Storm)",
}
# The class (and subclass) each toggle is for, so the builder only offers the ones that matter
TOGGLE_FOR = {"rage": ("barbarian", ""), "reckless": ("barbarian", ""), "smite": ("paladin", ""), "vow": ("paladin", ""),
              "curse": ("warlock", "The Hexblade"), "surprise": ("rogue", "Assassin"), "manifestation": ("monk", "Way of the Open Hand"),
              "damaged_target": ("ranger", "Hunter"), "starry_form": ("druid", "Circle of Stars"), "symbiotic": ("druid", "Circle of Spores"),
              "storm_close": ("sorcerer", "Storm Sorcery")}

def relevant_toggles(classes):
    """ Toggles for a [class, subclass, levels] list """
    return [k for k, (cls, sub) in TOGGLE_FOR.items() if any(c == cls and (not sub or s == sub) for c, s, *_ in classes)]

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

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        names = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in names})

    def toggle(self, key):
        return self.toggles.get(key, True)

def class_order(character, level=MAX_LEVEL):
    """ The class of each character level, i.e. ['fighter', 'fighter', 'rogue', ...] up to level """
    order = [cls for cls, _, levels in character.classes for _ in range(int(levels))]
    return order[:level]

def class_levels(character, level=MAX_LEVEL):
    counts = {}
    for cls in class_order(character, level):
        counts[cls] = counts.get(cls, 0) + 1
    return counts

def subclass_of(character, cls, class_level):
    for c, sub, _ in character.classes:
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
        A single class half caster rounds up """
    full = sum(n for cls, n in levels.items() if CASTER.get(cls) == "full")
    half = [n for cls, n in levels.items() if CASTER.get(cls) == "half"]
    third = sum(n for cls, n in levels.items() if subclasses.get(cls) in ("Eldritch Knight", "Arcane Trickster"))
    casting_classes = sum(1 for cls in levels if cls in CASTER) + (third > 0)
    if casting_classes == 1 and len(half) == 1:
        return ceil(half[0] / 2) if half[0] >= 2 else 0
    return full + sum(n // 2 for n in half) + third // 3

def warlock_pact_slots(warlock_level):
    """ (pact slots per short rest, pact slot level) """
    if not warlock_level:
        return 0, 0
    slots = 1 if warlock_level == 1 else 2 if warlock_level < 11 else 3
    return slots, min(5, (warlock_level + 1) // 2)

def compile_character(character, level=MAX_LEVEL):
    """ The Character at a level, and notes on what is and isn't modelled """
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
    c = Character(name=character.name, level=level, **scores)
    for feat in feats:
        if feat in FEAT_FLAGS:
            setattr(c, FEAT_FLAGS[feat], True)
        elif feat not in ("Dual Wielder", "Polearm Master", "Athlete"):
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

    attacks = _attacks(character, c, levels, subs, feats, notes)
    profs = weapon_proficiencies(character, level)
    if "Weapon Master" in feats:
        profs |= {weapon_base(a.name) for a in attacks} # Four weapons of your choice, assumed to be the ones used
    for a in attacks:
        if a.is_weapon and not is_proficient(weapon_base(a.name), profs):
            a.proficient = False
            notes.append(f"Not proficient with {weapon_base(a.name)}s")
    c.attacks = attacks
    _class_features(character, c, levels, subs, notes)
    split = " / ".join(f"{cls.title()} {n}" + (f" ({subs[cls]})" if subs.get(cls) else "") for cls, n in levels.items())
    c.description = f"{character.race}, {split}. Feats: {', '.join(feats) or 'none'}"
    return c, notes

def weapon_base(attack_name):
    """ 'Greatsword (Action Surge)' -> 'Greatsword' """
    return attack_name.split(" (")[0]

def _extra_attacks(levels, subs, character):
    """ Attacks with the Attack action """
    attacks = 1
    if levels.get("fighter", 0) >= 11:
        attacks = 3
    elif any(levels.get(cls, 0) >= 5 for cls in ("fighter", "barbarian", "paladin", "ranger", "monk")):
        attacks = 2
    elif levels.get("bard", 0) >= 6 and subs.get("bard") in ("College of Swords", "College of Valour"):
        attacks = 2
    elif levels.get("wizard", 0) >= 6 and subs.get("wizard") == "Bladesinging":
        attacks = 2
    elif levels.get("warlock", 0) >= 5 and character.routine != "cantrip": # Pact of the Blade, Deepened Pact
        attacks = 2
    return attacks

def _attacks(character, c, levels, subs, feats, notes):
    routine = character.routine
    if routine == "cantrip":
        stat = max((SPELL_ABILITY[cls] for cls in levels if cls in SPELL_ABILITY), key=lambda s: getattr(c, s), default="charisma")
        if character.cantrip == "Eldritch Blast" and not levels.get("warlock"):
            notes.append("Eldritch Blast needs a warlock level (or Spell Sniper)")
        beams = spell_attacks(character.cantrip, ability_stat=stat, character_level=c.level, ruleset="bg3")
        cantrip = [replace(a, name=f"{a.name} {ii + 1}" if len(beams) > 1 else a.name) for ii, a in enumerate(beams)]
        druid = levels.get("druid", 0)
        if not character.spell:
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
        casts = per_fight(per_long_rest=sum(slots[spell_level - 1:]), per_short_rest=pact if pact_level >= spell_level else 0)
        if not casts:
            notes.append(f"No spell slots of level {spell_level} or higher for {character.spell} yet")
            return cantrip
        levelled = spell_attacks(character.spell, ability_stat=stat, slot_level=spell_level, ruleset="bg3")
        for a in levelled:
            a.uses_per_fight = casts
        for a in cantrip:
            a.fallback_for = character.spell # Cast once the slots run out
        return levelled + cantrip

    hexblade = subs.get("warlock") == "The Hexblade" or levels.get("warlock", 0) >= 3 # Hex Warrior or Pact of the Blade use charisma
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
            attacks.append(replace(strike, name="Unarmed Strike (Martial Arts)")) # Bonus action strike
            ki = monk + 1
            attacks.append(replace(strike, name="Flurry of Blows", uses_per_fight=per_fight(per_short_rest=ki)))
        return attacks

    name = DEFAULT_WEAPONS[routine]
    weapon_stat = "dexterity" if routine in ("ranged", "dual_wield") else "strength"
    if routine == "one_handed" and c.dexterity > c.strength:
        name, weapon_stat = "Rapier", "dexterity" # Finesse
    main = weapon_attack(name, ability_stat=stat_for(weapon_stat))
    if routine == "thrown":
        main = replace(main, type="thrown", name=f"{name} (Thrown)")
    attacks = [replace(main) for _ in range(count)]
    bonus_actions = 2 if levels.get("rogue", 0) >= 3 and subs.get("rogue") == "Thief" else 1 # Fast Hands
    if routine == "dual_wield":
        offhand = weapon_attack("Longsword" if "Dual Wielder" in feats else name, ability_stat=stat_for(weapon_stat), offhand=True)
        attacks += [replace(offhand) for _ in range(bonus_actions)]
        bonus_actions = 0
    # Bonus action attacks: Frenzy, Polearm Master butt end, Swashbuckler Dirty Tricks, War Priest
    if bonus_actions and levels.get("barbarian", 0) >= 3 and subs.get("barbarian") == "Berserker" and character.toggle("rage"):
        # Frenzied Strike, or Enraged Throw for throwing builds
        attacks.append(replace(main, name=f"{weapon_base(main.name)} ({'Enraged Throw' if routine == 'thrown' else 'Frenzy'})"))
        bonus_actions -= 1
    if bonus_actions and "Polearm Master" in feats and name in POLEARMS:
        attacks.append(Attack(name="Polearm Butt End", ability_stat=stat_for("strength"), damage="1d4", damage_type="bludgeoning"))
        bonus_actions -= 1
    if bonus_actions and levels.get("rogue", 0) >= 4 and subs.get("rogue") == "Swashbuckler" and routine != "ranged":
        attacks.append(replace(main, name=f"{main.name} (Flick o' the Wrist)"))
        bonus_actions -= 1
    if bonus_actions and levels.get("cleric") and subs.get("cleric") == "War Domain":
        charges = 3 + (levels["cleric"] >= 5) + (levels["cleric"] >= 8) + (levels["cleric"] >= 11)
        attacks.append(replace(main, name=f"{main.name} (War Priest)", uses_per_fight=per_fight(per_long_rest=charges)))
    if levels.get("fighter", 0) >= 2:
        attacks += action_surge(levels["fighter"], "bg3", replace(main))
    if levels.get("ranger", 0) >= 3 and subs.get("ranger") == "Gloom Stalker":
        attacks.append(replace(main, name=f"{main.name} (Dread Ambusher)", uses_per_fight=1, bonus_damage_die_mod_list=["1d8"]))
    return attacks

def _limited_rider(c, label, uses, bonus=None, extra=None):
    """ A limited use rider on one attack each round (manoeuvres, Arcane Shots, Blade Flourish), until its uses per fight run out:
        the first plain weapon attack becomes a limited attack with the rider, with the plain attack as its fallback """
    main = next((a for a in c.attacks if a.is_weapon or a.type == "unarmed"), None)
    if main is None or not uses or main.uses_per_fight or main.fallback_for:
        return
    name = f"{main.name.split(' (')[0]} ({label})"
    rider = replace(main, name=name, uses_per_fight=uses,
                    bonus_damage_die_mod_list=[*main.bonus_damage_die_mod_list, *([bonus] if bonus else [])],
                    extra_damage_list=[*main.extra_damage_list, *([extra] if extra else [])])
    main.fallback_for = name
    c.attacks.insert(c.attacks.index(main), rider)

def _once_per_turn(c, dice, uses=0, crit_only=False):
    """ Adds once per turn damage. The engine has one pool, so a second source adds its dice to the first """
    c.once_per_turn_die_mod_list = [*c.once_per_turn_die_mod_list, dice]
    if uses and not c.once_per_turn_uses_per_fight:
        c.once_per_turn_uses_per_fight = uses
    c.once_per_turn_crit_only = c.once_per_turn_crit_only or crit_only

def _class_features(character, c, levels, subs, notes):
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
    if fighter >= 3 and subs.get("fighter") == "Arcane Archer" and character.routine == "ranged":
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
    if barbarian >= 2 and character.toggle("reckless") and character.routine != "ranged":
        c.advantage = True
    c.brutal_critical = barbarian >= 9
    # Paladin
    if paladin >= 2 and character.toggle("smite") and weapon:
        slots = spell_slots(caster_level(levels, subs))
        pact, pact_level = warlock_pact_slots(warlock)
        highest = max(len(slots), pact_level)
        if highest:
            _once_per_turn(c, f"{min(1 + highest, 5)}d8", per_fight(per_long_rest=sum(slots), per_short_rest=pact))
    c.improved_divine_smite = paladin >= 11 and weapon
    if paladin >= 3 and character.toggle("vow"):
        oath = subs.get("paladin")
        if oath == "Oath of Vengeance":
            c.advantage = True
        elif oath == "Oath of Devotion":
            c.bonus_attack_die_mod_list = [*c.bonus_attack_die_mod_list, str(max(c.charisma_ability_modifier, 0))]
        elif oath == "Oath of the Crown":
            c.bonus_attack_die_mod_list = [*c.bonus_attack_die_mod_list, str(c.proficiency_bonus)]
    # Ranger
    if ranger >= 3 and subs.get("ranger") == "Hunter" and character.toggle("damaged_target") and weapon:
        _once_per_turn(c, "1d8")
    if ranger >= 3 and subs.get("ranger") == "Swarmkeeper":
        _once_per_turn(c, "1d8" if ranger >= 11 else "1d6")
    # Rogue: Sneak Attack, never on off-hand attacks
    if rogue and character.routine != "unarmed":
        _once_per_turn(c, f"{ceil(rogue / 2)}d6")
        for a in c.attacks:
            if a.offhand:
                a.once_per_turn_eligible = False
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
        # Quickened Spell: a second cast for 3 sorcery points, sorcery points = sorcerer level per long rest
        uses = per_fight(per_long_rest=sorcerer // 3)
        c.attacks += [replace(a, name=f"Quickened {a.name}", uses_per_fight=uses) for a in list(c.attacks) if a.type == "spell"]
    c.empowered_evocation = wizard >= 10 and subs.get("wizard") == "Evocation School"
    if cleric >= 8 and subs.get("cleric") in ("War Domain", "Tempest Domain", "Death Domain", "Life Domain", "Nature Domain", "Trickery Domain") and weapon:
        _once_per_turn(c, "1d8") # Divine Strike
    if bard >= 3 and subs.get("bard") == "College of Swords" and weapon:
        inspirations = 3 + (bard >= 5) + (bard >= 10)
        _limited_rider(c, "Blade Flourish", per_fight(per_short_rest=inspirations), bonus="1d10" if bard >= 10 else "1d8" if bard >= 5 else "1d6")
    if cleric >= 2 and subs.get("cleric") == "Death Domain" and character.routine in ("two_handed", "one_handed", "dual_wield", "unarmed"):
        # Touch of Death: Channel Divinity (1 charge, 2 from level 6, short rest) on a melee hit
        _limited_rider(c, "Touch of Death", per_fight(per_short_rest=1 + (cleric >= 6)), extra=f"{5 + 2 * cleric} necrotic")
    if cleric >= 8 and subs.get("cleric") in ("Light Domain", "Knowledge Domain") and character.routine == "cantrip":
        # Potent Spellcasting: Wisdom to cleric cantrip damage
        for a in c.attacks:
            if a.type == "spell" and a.name.split(" (")[0].rstrip(" 0123456789") in ("Sacred Flame", "Toll the Dead", "Produce Flame"):
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
           "relevant_toggles", "STATS"]
