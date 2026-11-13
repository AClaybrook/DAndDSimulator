""" A BG3 build: a class preset with equipment, buffs and toggled conditions for each act.
    compile_build turns it into a plain Character at an act checkpoint, which the simulator uses as is """
from copy import deepcopy
from dataclasses import asdict, dataclass, field, fields, replace

from bg3.buffs import BUFFS
from bg3.character import POLEARM_REACTIONS, ROUNDS_PER_FIGHT, SENTINEL_REACTIONS, SHADOW_BLADE, Bg3Character, compile_character, is_proficient, weapon_proficiencies
from bg3.checkpoints import ACTS, act_level
from bg3.items import (BLOODLUST_KILLS_PER_FIGHT, REACTION_ADVANTAGE, SLOT_LABELS, SLOTS, active_effects, apply_effect, apply_lightning_charges, apply_reverberation, catalog,
                       condition_id, equip_weapon, extra_action)
from game_data import weapons
from game_data.classes import BUILDS, build_character

ACT_KEYS = [str(a) for a in ACTS]

@dataclass
class Bg3Build:
    name: str
    preset: str # A key of game_data.classes.BUILDS, which handles class features, feats and attacks per level
    # Act ("1", "2", "3"): slot: item key. Empty slots keep the item from the act before
    equipment: dict[str, dict[str, str]] = field(default_factory=dict)
    buffs: dict[str, list[str]] = field(default_factory=dict) # Act: buff keys
    conditions: list[str] = field(default_factory=list) # Conditional effects that are toggled on
    levels: dict[str, int] = field(default_factory=dict) # Act: level, overrides the default checkpoints
    # A custom character (bg3.character.Bg3Character as a dict) used instead of the class preset
    character: dict | None = None
    carried: list[str] = field(default_factory=list) # Items carried rather than worn, i.e. the Resonance Stone
    roles: list[str] = field(default_factory=list) # Party roles from the build's source, added to the ones worked out from its classes
    # Named "what ifs" compared next to the build (bg3.kits): {"name", "kit", "act", "buffs", "toggles", "conditions"}. They never change the gear
    variants: list[dict] = field(default_factory=list)
    advantage: bool = False # Attacks with advantage (for class presets; custom characters have the "advantage" toggle)
    # The player's own estimates, replacing the defaults (ASSUMPTIONS): kills a fight with Bloodlust, reaction attacks a fight
    assumptions: dict[str, float] = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        names = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in names})

# key: (label, default, what it means). How often things happen in a fight is a guess, so each build can set its own
ASSUMPTIONS = {
    "bloodlust_kills": ("Kills a fight", BLOODLUST_KILLS_PER_FIGHT, "A kill on your turn gives the Elixir of Bloodlust's extra action and Great Weapon "
                        "Master's bonus attack, once a turn each. 0 for a fight against one boss"),
    "polearm_reactions": ("Polearm Master reactions a fight", POLEARM_REACTIONS, "Attacks on enemies that walk into your reach"),
    "sentinel_reactions": ("Sentinel reactions a fight", SENTINEL_REACTIONS, "Attacks on enemies next to you that hit an ally"),
    "advantage_share": ("Share of attacks with advantage", 0.0, "Advantage some of the time: Shadow Blade in dim light or darkness, Faerie "
                        "Fire, hiding. 0.5 is half the attacks, 1 every attack (the advantage toggle)"),
}

def assumption(build, key):
    value = build.assumptions.get(key)
    return ASSUMPTIONS[key][1] if value is None else max(float(value), 0.0)

def main_weapon_finesse(bg3_character, gear):
    """ Whether the main weapon from gear ({slot: Item}) is finesse or ranged, None without one: it decides Sneak Attack and Flick o' the
        Wrist (i.e. The Dancing Breeze, a finesse glaive) """
    weapon = gear.get("ranged_main") if bg3_character.routine in ("ranged", "dual_hand_crossbows") else gear.get("melee_main")
    weapon = weapon.weapon if weapon is not None and weapon.weapon else None
    return None if weapon is None else weapon.get("kind") == "ranged" or "finesse" in (weapon.get("properties") or [])

def crit_chance(character, attack):
    """ The chance one attack roll is a crit, from its crit range and advantage (the enemy doesn't change it) """
    once = (21 - min(attack.crit_on, character.crit_on)) / 20
    twice = 1 - (1 - once) ** 2
    if attack.advantage or character.advantage:
        return twice
    return once + attack.advantage_chance * (twice - once)

def great_weapon_master_attack(character, kills):
    """ Great Weapon Master: a crit or a kill with a melee weapon attack gives another one with the bonus action that turn (any melee
        weapon, not only heavy ones). Added as a main hand attack made in the turns that happens: the chance any of the turn's melee
        attacks crits, plus the kills a fight (an estimate, ASSUMPTIONS). A bonus action attack the build makes every turn (off hand,
        Polearm Master's butt end, Flick o' the Wrist) is made in the other turns """
    melee = [a for a in character.attacks if a.type == "weapon (melee)" and not a.offhand and a.action in ("action", "extra")]
    if not character.GWM or not melee:
        return
    rounds = ROUNDS_PER_FIGHT
    uses = {a.name: a.uses_per_fight for a in reversed(character.attacks)}
    def share(a): # Of the turns the attack is made in
        if a.fallback_for and a.fallback_for != a.name and uses.get(a.fallback_for):
            return 1 - min(uses[a.fallback_for] / rounds, 1)
        return min(a.uses_per_fight / rounds, 1) if a.uses_per_fight else 1
    no_crit = 1.0
    for a in melee:
        no_crit *= (1 - crit_chance(character, a)) ** share(a)
    triggers = round(rounds * (1 - no_crit * (1 - min(kills / rounds, 1))), 2)
    every_turn = [a for a in melee if a.action == "action" and not a.uses_per_fight and not a.fallback_for]
    main = (every_turn or melee)[-1] # The last one: riders like Booming Blade sit on the first
    bonus = main.variant("Great Weapon Master", action="bonus", uses_per_fight=triggers, fallback_for="", tags=[t for t in main.tags if t != "after_cast"])
    usual = [a for a in character.attacks if (a.action == "bonus" or a.offhand) and a.is_weapon and not a.uses_per_fight and not a.fallback_for]
    if usual:
        usual[-1].fallback_for = bonus.name
    character.attacks.append(bonus)

def equipment_at(build, act):
    """ Slot: item key at an act, items carry over from earlier acts until replaced. An empty string clears a slot """
    gear = {}
    for a in ACT_KEYS[:ACT_KEYS.index(str(act)) + 1]:
        gear.update(build.equipment.get(a, {}))
    return {slot: key for slot, key in gear.items() if key}

def buffs_at(build, act):
    return [BUFFS[b] for b in build.buffs.get(str(act), []) if b in BUFFS]

def _weapon_slot(attack):
    """ The equipment slot an attack is made with, None for unarmed attacks, spells and conjured weapons (Shadow Blade) """
    if "conjured" in attack.tags:
        return None
    if attack.type == "weapon (melee)":
        return "melee_off" if attack.offhand else "melee_main"
    if attack.type in ("weapon (ranged)", "thrown"):
        if attack.type == "thrown":
            return "melee_main"
        return "ranged_off" if attack.offhand else "ranged_main"
    return None

def _finesse(attack):
    """ Whether the attack's weapon is finesse (Shadow Blade is) """
    return attack.base == SHADOW_BLADE or "finesse" in (weapons().get(attack.base, {}).get("properties") or [])

def compile_build(build, act, items=None):
    """ The build's Character at an act checkpoint, with gear, buffs and toggled conditions applied """
    items = items or catalog()
    level = act_level(act, build.levels)
    gear = {slot: items[key] for slot, key in equipment_at(build, act).items() if key in items and items[key].fits(slot)}
    if build.character:
        bg3_character = Bg3Character.from_dict(build.character)
        character, _ = compile_character(bg3_character, level, main_weapon_finesse(bg3_character, gear))
        for key, label in (("polearm_reactions", "Polearm Master reaction"), ("sentinel_reactions", "Sentinel reaction")):
            uses = assumption(build, key)
            for attack in character.attacks:
                if attack.action == "reaction" and attack.label == label:
                    attack.uses_per_fight = uses
            if not uses: # None at all: 0 uses would mean every turn
                character.attacks = [a for a in character.attacks if not (a.action == "reaction" and a.label == label)]
    else:
        character = build_character(build.preset, level, "bg3")

    # Weapons replace the preset's weapon for the attacks made with them. Custom characters lose the proficiency bonus with weapons they
    # aren't proficient with (presets are assumed proficient)
    profs = weapon_proficiencies(Bg3Character.from_dict(build.character), level) if build.character else None
    own_attacks = {slot: [] for slot in gear}
    names = {} # Old: new attack names, so fallbacks still point at their limited attack
    attacks = []
    for attack in character.attacks:
        slot = _weapon_slot(attack)
        item = gear.get(slot)
        if item is not None and item.weapon:
            renamed = equip_weapon(attack, item)
            names[attack.name] = renamed.name
            attack = renamed
            # A finesse weapon from gear hits with the higher of Strength and Dexterity (unless the build hits with Charisma, i.e. a pact weapon)
            if "finesse" in (item.weapon.get("properties") or []) and attack.ability_stat in ("strength", "dexterity"):
                attack.ability_stat = "dexterity" if character.dexterity > character.strength else "strength"
            if profs is not None:
                attack.proficient = is_proficient(item.weapon.get("base"), profs)
            own_attacks[slot].append(attack)
        else:
            attack = deepcopy(attack)
        attacks.append(attack)
    # Belm in the off hand: Perfectly Balanced Strike, the bonus action attack made with the main hand weapon (its ability modifier and
    # on-hit effects, bg3.wiki) instead of an off-hand swing
    off = gear.get("melee_off")
    if off is not None and any(e.kind == "main_hand_bonus_attack" for e in off.effects):
        mains = [a for a in attacks if a.type == "weapon (melee)" and not a.offhand and a.action == "action" and not a.uses_per_fight and not a.fallback_for]
        swings = own_attacks.get("melee_off", [])
        if mains and (swings or not any(a.action == "bonus" and a.is_weapon and not a.uses_per_fight for a in attacks)):
            strike = mains[-1].variant("Perfectly Balanced Strike", action="bonus", fallback_for=swings[0].fallback_for if swings else "")
            if swings:
                names[swings[0].name] = strike.name
                attacks[next(ii for ii, a in enumerate(attacks) if a is swings[0])] = strike
            else:
                attacks.append(strike)
            own_attacks["melee_off"] = swings[1:]
            if _weapon_slot(mains[-1]) in own_attacks:
                own_attacks[_weapon_slot(mains[-1])].append(strike)
    if any(item.key in REACTION_ADVANTAGE for item in gear.values()):
        for attack in attacks:
            if attack.action == "reaction":
                attack.advantage = True
    for attack in attacks:
        if attack.fallback_for in names:
            attack.fallback_for = names[attack.fallback_for]
    character.attacks = attacks

    # Ability scores first, so later effects see the final stats
    sources = [(item.key, item.effects, own_attacks.get(slot, [])) for slot, item in gear.items()]
    sources += [(f"buff:{b.key}", b.effects, []) for b in buffs_at(build, act)]
    conditions = list(build.conditions)
    keys = {item.key for item in gear.values()}
    if "bg3:broodmother_s_revenge" in keys and "bg3:ring_of_regeneration" in keys:
        # The ring heals at the start of every turn, even at full hit points, which keeps Broodmother's Revenge's poison coating up
        conditions.append(condition_id("bg3:broodmother_s_revenge", 0))
    effects = [(e, own) for key, effects_, own in sources for e in active_effects(key, effects_, conditions)]
    effects.sort(key=lambda pair: not pair[0].kind.startswith("ability"))
    honour_mode = bool(build.character) and Bg3Character.from_dict(build.character).toggle("honour_mode")
    extra_actions, limited_haste = 0, 0.0
    for effect, own in effects:
        if effect.kind == "extra_action":
            extra_actions += int(effect.value)
        elif effect.kind == "limited_haste":
            limited_haste = max(limited_haste, float(effect.value))
        elif effect.kind == "extra_action_on_kill":
            if assumption(build, "bloodlust_kills") > 0: # No kills: no extra actions (0 uses would mean every turn)
                apply_effect(character, replace(effect, value=assumption(build, "bloodlust_kills")), own, honour_mode)
        elif effect.kind != "lightning_charges":
            apply_effect(character, effect, own, honour_mode)
    # Gear and elixirs that set Strength or Dexterity (Gauntlets of Hill Giant Strength): finesse weapons hit with the higher one
    for attack in character.attacks:
        if attack.ability_stat in ("strength", "dexterity") and _finesse(attack):
            attack.ability_stat = "dexterity" if character.dexterity > character.strength else "strength"
    # Charges from several items don't stack their bonuses
    apply_lightning_charges(character, [(e, own) for e, own in effects if e.kind == "lightning_charges"])
    apply_reverberation(character, {item.key for item in gear.values()})

    # Haste: one more action each round (the Hastened condition doesn't stack, so one at most)
    if extra_actions:
        extra_action(character, "Haste", honour_mode)
    elif limited_haste:
        # A Haste the gear casts on some days (Gontr Mael's Celestial Haste): that many more actions in a typical fight
        extra_action(character, "Celestial Haste", honour_mode, uses=limited_haste)

    if build.advantage:
        character.advantage = True
    share = min(assumption(build, "advantage_share"), 1.0)
    if share:
        for attack in character.attacks:
            if not attack.saving_throw:
                attack.advantage_chance = max(attack.advantage_chance, share)
    great_weapon_master_attack(character, assumption(build, "bloodlust_kills"))
    label = ACTS[int(act)][0]
    character.name = f"{build.name} ({label})" if build.name else label
    worn = ", ".join(f"{SLOT_LABELS[slot]}: {item.name}" for slot, item in gear.items())
    base = character.description if build.character else f"{BUILDS[build.preset].label}, level {level}"
    character.description = f"{base}. {worn or 'No equipment'}" + \
        (f". Buffs: {', '.join(b.name for b in buffs_at(build, act))}" if buffs_at(build, act) else "")
    # Gear is part of the build, so level sweeps should not rebuild the preset without it
    character.preset = ""
    return character

def slot_order():
    return [key for key, _, _ in SLOTS]
