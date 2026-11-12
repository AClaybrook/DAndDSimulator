""" Party synergies: conditions one party member sets up that change the enemy or the other members, and a party fight simulation.
    Each synergy is found from the party's classes, gear and carried items, and is a toggle, since most need the fight to go to plan """
from copy import deepcopy
from dataclasses import dataclass

import numpy as np

from bg3.build import compile_build, equipment_at
from bg3.character import SPELL_ABILITY, Bg3Character, class_levels, subclass_of
from bg3.checkpoints import act_level
from bg3.items import catalog, reverberation_per_round
from computations.analytic import expected_damage_per_round
from computations.models import Enemy
from computations.numerical_simulation import fight_damage, set_seed

@dataclass
class Synergy:
    key: str
    name: str
    effect: str
    default: bool # On when the party can set it up, or only when chosen (situational)
    min_act: int = 1

SYNERGIES = {s.key: s for s in [
    Synergy("resonance_stone", "Resonance Stone", "enemies near the carrier take double psychic damage (Shadow Blade, Shadow Arrow, Swarmkeeper moths, "
            "psychic riders) and roll Intelligence, Wisdom and Charisma saves with disadvantage", True, 2),
    Synergy("darkness", "Darkness on the enemy", "members who see through magical darkness (Devil's Sight, Eyes of the Dark, Shar's Spear) attack with "
            "advantage", False),
    Synergy("reverberation", "Reverberation", "stacks from thunder and condition items: -2 to the enemy's Strength, Dexterity and Constitution saves", True),
    Synergy("prone_reverb", "Prone from Reverberation", "at 5 stacks the enemy makes a CON save (effectively DC 15) or falls Prone: melee attacks "
            "against it have advantage. Tick to assume it's Prone for the melee members' attacks", False),
    Synergy("paralysed", "Enemy paralysed (Hold Person / Monster)", "advantage on attacks, melee hits are crits, Strength and Dexterity saves fail. "
            "Counted for the share of turns the hold lands: its Wisdom save against the caster's spell save DC", False),
]}
REVERBERATION_ITEMS = {"bg3:boots_of_stormy_clamour", "bg3:gloves_of_belligerent_skies", "bg3:spineshudder_amulet"}
DARKNESS_SIGHT_ITEMS = {"bg3:shar_s_spear_of_evening"}
HOLD_PERSON = {"bard", "cleric", "druid", "sorcerer", "warlock", "wizard"}
MENTAL = ("intelligence", "wisdom", "charisma")

def _levels(build, act):
    """ Class levels and subclasses at an act, None for class presets """
    if not build.character:
        return None, None
    character = Bg3Character.from_dict(build.character)
    levels = class_levels(character, act_level(act, build.levels))
    return levels, {cls: subclass_of(character, cls, n) for cls, n in levels.items()}

def sees_in_darkness(build, act):
    levels, subs = _levels(build, act)
    gear = set(equipment_at(build, act).values())
    if gear & DARKNESS_SIGHT_ITEMS:
        return True
    if levels is None:
        return build.preset.startswith("warlock")
    return levels.get("warlock", 0) >= 2 or (levels.get("sorcerer", 0) >= 3 and subs.get("sorcerer") == "Shadow Magic")

def casts_darkness(build, act):
    levels, subs = _levels(build, act)
    if levels is None:
        return any(build.preset.startswith(c) for c in ("warlock", "wizard", "sorcer"))
    return any(levels.get(c, 0) >= 3 for c in ("warlock", "sorcerer", "wizard")) or \
        (levels.get("monk", 0) >= 3 and subs.get("monk") == "Way of Shadow")

def casts_hold_person(build, act):
    levels, subs = _levels(build, act)
    if levels is None:
        return any(build.preset.startswith(c) for c in HOLD_PERSON)
    return any(levels.get(c, 0) >= 3 for c in HOLD_PERSON) or (levels.get("paladin", 0) >= 3 and subs.get("paladin") == "Oath of Vengeance")

def available(builds, act):
    """ {synergy key: [members who set it up]} for the synergies this party can use at an act. The Resonance Stone is one item for the party,
        so it is offered from Act 2 even if no build lists it """
    act = str(act)
    found = {}
    carriers = [b.name for b in builds if any("resonance stone" in c.lower() for c in b.carried)]
    if int(act) >= SYNERGIES["resonance_stone"].min_act:
        found["resonance_stone"] = carriers
    casters = [b.name for b in builds if casts_darkness(b, act)]
    if casters and any(sees_in_darkness(b, act) for b in builds):
        found["darkness"] = casters
    reverb = [b.name for b in builds if set(equipment_at(b, act).values()) & REVERBERATION_ITEMS]
    if reverb:
        found["reverberation"] = reverb
    stackers = [b.name for b in builds if reverberation_per_round(compile_build(b, act), set(equipment_at(b, act).values())) > 1]
    if stackers:
        found["prone_reverb"] = stackers
    holders = [b.name for b in builds if casts_hold_person(b, act)]
    if holders:
        found["paralysed"] = holders
    return found

def default_active(builds, act):
    """ Synergies on by default: the ones the party sets up every fight (a Resonance Stone only when a build carries it) """
    return [k for k, members in available(builds, act).items() if SYNERGIES[k].default and members]

def party_enemy(builds, act, enemy, active=None):
    """ The enemy as the party's synergies leave it (double psychic damage, lower saves). active: the default ones when None """
    act = str(act)
    usable = available(builds, act)
    active = [k for k in (default_active(builds, act) if active is None else active) if k in usable]
    enemy = deepcopy(enemy)
    if "resonance_stone" in active and "psychic" not in [v.lower() for v in enemy.vulnerabilities]:
        enemy.vulnerabilities = [*enemy.vulnerabilities, "psychic"]
        enemy.resistances = [r for r in enemy.resistances if r.lower() != "psychic"]
    if "resonance_stone" in active:
        enemy.save_disadvantage = sorted({*enemy.save_disadvantage, *MENTAL})
    if "reverberation" in active:
        for stat in ("strength", "dexterity", "constitution"):
            setattr(enemy, f"{stat}_save", enemy.saving_throw_modifier(stat) - 2)
    if "paralysed" in active:
        for stat in ("strength", "dexterity"):
            setattr(enemy, f"{stat}_save", -100) # Automatically fails
    return enemy, active

def apply(builds, act, enemy, active):
    """ The party's characters and the enemy with the active synergies applied """
    act = str(act)
    characters = [compile_build(b, act) for b in builds]
    enemy, active = party_enemy(builds, act, enemy, active)
    for build, character in zip(builds, characters):
        sighted = "darkness" in active and sees_in_darkness(build, act)
        for attack in character.attacks:
            if attack.saving_throw:
                continue
            if sighted or "paralysed" in active or ("prone_reverb" in active and attack.type in ("weapon (melee)", "unarmed")):
                attack.advantage = True
            if "paralysed" in active and attack.type in ("weapon (melee)", "unarmed"):
                attack.hits_crit = True
    return characters, enemy

def hold_chance(builds, act, enemy):
    """ (chance, spell save DC, caster) for the party's best Hold Person or Hold Monster against the enemy: it fails a Wisdom save, rolled
        twice when it has disadvantage on them (a Resonance Stone). (0, 0, '') without a caster """
    wisdom = enemy.saving_throw_modifier("wisdom")
    best = (0.0, 0, "")
    for build in builds:
        if not casts_hold_person(build, act):
            continue
        character = compile_build(build, act)
        levels, _ = _levels(build, act)
        stats = [SPELL_ABILITY[cls] for cls in levels if cls in HOLD_PERSON] if levels else list(MENTAL)
        dc = max(character.spell_difficulty_class(stat) for stat in stats)
        fails = min(max((dc - 1 - wisdom) / 20, 0.0), 1.0)
        if "wisdom" in enemy.save_disadvantage:
            fails = 1 - (1 - fails) ** 2
        best = max(best, (fails, dc, build.name))
    return best

def outcomes(builds, act, enemy, active):
    """ [(share of turns, characters, enemy)] with the active synergies. A held enemy is two cases, since it can save: held for the
        share of turns the hold lands (the caster casts it again when it breaks), and the rest without it """
    characters, boosted = apply(builds, act, enemy, active)
    if "paralysed" not in active or "paralysed" not in available(builds, act):
        return [(1.0, characters, boosted)]
    lands = hold_chance(builds, act, boosted)[0]
    free, unheld = apply(builds, act, enemy, [k for k in active if k != "paralysed"])
    return [(lands, characters, boosted), (1 - lands, free, unheld)]

def party_damage(builds, act, enemy, rounds_per_fight, active):
    """ [(name, damage per round without synergies, with the active ones)] """
    plain, _ = apply(builds, act, enemy, [])
    cases = outcomes(builds, act, enemy, active)
    return [(b.name, expected_damage_per_round(p, enemy, rounds_per_fight),
             sum(share * expected_damage_per_round(characters[ii], foe, rounds_per_fight) for share, characters, foe in cases))
            for ii, (b, p) in enumerate(zip(builds, plain))]

def simulate_party_fight(builds, act, enemy, rounds_per_fight, active, num_fights=4000, max_rounds=None, seed=7):
    """ Fights of the whole party against the enemy's hit points. Limited resources are spread over rounds_per_fight rounds, the fight can run
        to max_rounds. Returns the chance the enemy is down by each round, and each member's share of the damage """
    cases = outcomes(builds, act, enemy, active)
    rounds = max(max_rounds or 2 * rounds_per_fight, rounds_per_fight)
    rng = set_seed(seed)
    def simulate(characters, foe):
        out = []
        for c in characters:
            damage = fight_damage(c, foe, num_fights, rounds_per_fight, rng=rng)
            # Rounds past the planned fight length use the steady state (no limited resources left): repeat the last planned round
            extra = fight_damage(c, foe, num_fights * (rounds - rounds_per_fight) or 1, 1, rng=rng)[0][:num_fights * (rounds - rounds_per_fight)]
            out.append(np.vstack([damage, extra.reshape(rounds - rounds_per_fight, num_fights)]) if rounds > rounds_per_fight else damage)
        return out
    per_member = simulate(*cases[0][1:])
    if len(cases) > 1:
        # A hold that can fail: each fight goes one way or the other
        held = rng.random(num_fights) < cases[0][0]
        per_member = [np.where(held, a, b) for a, b in zip(per_member, simulate(*cases[1][1:]))]
    total = np.sum(per_member, axis=0).cumsum(axis=0)
    down = total >= enemy.hit_points
    killed_by = down.mean(axis=1)
    kill_round = np.where(down.any(axis=0), down.argmax(axis=0) + 1, rounds + 1)
    share = [float(m.sum()) for m in per_member]
    return {"down_by_round": [float(p) for p in killed_by], "median_round": float(np.median(kill_round)),
            "share": {b.name: s / max(sum(share), 1) for b, s in zip(builds, share)}, "rounds": rounds, "hit_points": enemy.hit_points}

def psychic_users(builds, act):
    """ Members dealing psychic damage, who gain from the Resonance Stone """
    users = []
    for build in builds:
        character = compile_build(build, act)
        if any(a.damage_type == "psychic" or any("psychic" in e for e in a.extra_damage_list) for a in character.attacks):
            users.append(build.name)
    return users

def prone_share(builds, act, enemy=None):
    """ Share of turns the enemy is knocked Prone by Reverberation: the party's stacks on one target reach 5 in some rounds, and it fails a
        CON save of effectively DC 15 (10 plus the Reverberation penalty) """
    added = sum(reverberation_per_round(compile_build(b, act), set(equipment_at(b, act).values())) for b in builds)
    if added <= 1:
        return 0.0
    con = enemy.saving_throw_modifier("constitution") if enemy is not None else 2
    fail = min(max((15 - con - 1) / 20, 0.05), 0.95)
    return min(1.0, (added - 1) / 5) * fail

def describe(builds, act, enemy=None):
    """ One line per available synergy: what it does, who sets it up and who gains """
    act = str(act)
    lines = {}
    for key, members in available(builds, act).items():
        s = SYNERGIES[key]
        who = f"set up by {', '.join(members)}" if members else "nobody carries it yet, tick to assume someone does"
        if key == "darkness":
            who += f"; sees through it: {', '.join(b.name for b in builds if sees_in_darkness(b, act)) or 'nobody'}"
        if key == "paralysed":
            lands, dc, caster = hold_chance(builds, act, party_enemy(builds, act, enemy or Enemy())[0])
            who += f"; lands {lands:.0%} of the time against this enemy ({caster}'s DC {dc} against its Wisdom save)"
        if key == "prone_reverb":
            share = prone_share(builds, act, enemy)
            who += f"; about {share:.0%} of turns against this enemy (5 stack bursts x its chance to fail the save)"
        if key == "resonance_stone":
            who += f"; psychic damage: {', '.join(psychic_users(builds, act)) or 'nobody'}"
        lines[key] = f"{s.name}: {s.effect} ({who})"
    return lines

__all__ = ["SYNERGIES", "available", "default_active", "apply", "party_damage", "simulate_party_fight", "describe", "sees_in_darkness", "catalog"]
