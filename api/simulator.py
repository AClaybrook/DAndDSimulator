""" The simulator's computations as JSON: options, presets, expected damage, and simulations with their figure, headline numbers and tables.
    Figures come from api.plots """
import json
from dataclasses import asdict

import numpy as np
import pandas as pd

from api.plots import (fight_export, fight_summary, generate_damage_per_attack_histogram, generate_fight_plot, generate_line_plots,
                       generate_plot_data, generate_rounds_to_kill_plot)
from api.sweeps import SWEEP_PARAMETERS, run_sweep
from api.validation import validation_errors
from api.variants import VARIANTS, make_variant
from computations.analytic import attack_breakdown, attacks_per_round, expected_by_attack, power_attack_insights
from computations.exact import damage_per_round
from computations.models import Attack, Character, Enemy
from computations.numerical_simulation import set_seed, simulate_fights, simulate_rounds_from_characters, simulate_rounds_to_kill
from game_data import RULESETS, attack_templates, attacks_from_template, enemy_from_monster, enemy_from_preset, enemy_presets
from game_data.classes import BUILDS, build_character

# What each graph type answers, shown under the graph picker
GRAPH_DESCRIPTIONS = {
    "DPR Distribution": "How much damage does each character deal per round against this enemy, and how swingy is it? The line over each "
                        "histogram is the exact distribution the simulation samples from; hover it for the mean, spread, skew and the chance "
                        "every attack misses.",
    "DPA Distribution": "Which attacks do the damage? The same as DPR, split by attack.",
    "DPR Sweep": "How does damage per round change with one parameter (pick it in Settings)? i.e. is GWM worth it at high armor class, how a "
                 "build scales with level.",
    "DPA Sweep": "The same as DPR Sweep, split by attack.",
    "Rounds to Kill": "How many rounds does each character need to kill this enemy on their own? Uses the enemy's hit points.",
    "Damage per Fight": "How is damage spread over a fight? Shows bursts from limited resources (Action Surge, smites, first round effects) "
                        "using Rounds per fight.",
}
EXPORTS = ["Damage per round", "Damage per attack", "Sweep", "Rounds to kill", "Damage per fight"]
TEMPLATE = "plotly_dark"
MAX_ROUNDS_TO_KILL = 20
ARMOR_CLASSES = range(10, 26)
SWEEPS = {"DPR Sweep": True, "DPA Sweep": False}

def options():
    """ Everything the simulator's pickers offer """
    return {
        "presets": [{"key": b.key, "label": b.label, "class": b.class_name, "description": b.description} for b in BUILDS.values()],
        "rulesets": [{"key": k, "label": v["label"], "maxLevel": v["max_level"]} for k, v in RULESETS.items()],
        "enemies": [{"label": label, "value": value} for label, value in enemy_presets()],
        "attackTemplates": [{"label": label, "value": value} for label, value in attack_templates()],
        "graphs": [{"key": k, "description": v} for k, v in GRAPH_DESCRIPTIONS.items()],
        "sweepParameters": [{"key": k, "description": v[2]} for k, v in SWEEP_PARAMETERS.items()],
        "variants": [{"key": k, "label": label} for k, (label, change) in VARIANTS.items() if change],
        "exports": EXPORTS,
        "attackDefaults": Attack().to_dict(),
        "characterDefaults": {k: v for k, v in Character().to_dict().items() if k != "attacks"},
        "enemyDefaults": Enemy().to_dict(),
    }

def default_session():
    """ The Dash app's example: four fighters against a Mind Flayer """
    from dataclasses import replace # pylint: disable=import-outside-toplevel
    sword = [Attack(name="Greatsword", two_handed=True, ability_stat="strength", damage="2d6", type="weapon (melee)") for _ in range(3)]
    fighter = Character(name="Fighter", level=12, attacks=sword, strength=20)
    characters = [fighter, replace(fighter, name="Fighter GWF + Crit On 19", GWF=True, crit_on=19),
                  replace(fighter, name="Fighter Advantage", advantage=True), replace(fighter, name="Fighter GWM + Advantage", GWM=True, advantage=True)]
    return {"characters": [c.to_dict() for c in characters], "enemy": enemy_from_monster("Mind Flayer").to_dict()}

def preset_character(preset, level, ruleset="bg3"):
    return build_character(preset, int(level), ruleset).to_dict()

def enemy(value):
    return enemy_from_preset(value).to_dict()

def template_attacks(value, ability_stat=None, level=1, ruleset="bg3"):
    return [a.to_dict() for a in attacks_from_template(value, ability_stat, int(level), ruleset)]

def parse(characters, enemy_dict):
    """ Characters and the enemy from JSON, or a list of readable problems """
    problems = []
    for ii, c in enumerate(characters):
        issues = validation_errors(c, c.get("attacks") or [])
        if issues:
            problems.append(f"{c.get('name') or f'Character {ii + 1}'}: {'; '.join(issues)}")
    names = [c.get("name") for c in characters]
    if len(set(names)) != len(names):
        problems.append("Character names must be unique")
    if problems:
        return None, None, problems
    try:
        return [Character.from_dict(c) for c in characters], Enemy.from_dict(enemy_dict), []
    except (TypeError, ValueError, KeyError) as e:
        return None, None, [f"Could not read the inputs: {e}"]

def expected(characters, enemy_dict, rounds_per_fight=None):
    """ Exact expected damage per round and per attack for each character, fast enough for every edit """
    parsed, foe, problems = parse(characters, enemy_dict)
    if problems:
        return {"problems": problems}
    out = []
    for c in parsed:
        per_attack = expected_by_attack(c, foe, rounds_per_fight)
        out.append({"name": c.name, "damagePerRound": float(per_attack.sum()),
                    "attacks": [{"name": a.name, "damage": float(v)} for a, v in zip(c.attacks, per_attack)]})
    return {"characters": out}

def _figure(fig):
    return json.loads(fig.to_json())

def _table(title, df, description=""):
    df = df.reset_index() if not isinstance(df.index, pd.RangeIndex) else df
    df = df.replace({np.nan: None})
    return {"title": title, "description": description, "columns": [str(c) for c in df.columns],
            "rows": [[v.item() if hasattr(v, "item") else v for v in row] for row in df.itertuples(index=False)]}

def _breakdown(characters, foe, rounds_per_fight):
    frames = [attack_breakdown(c, foe, rounds_per_fight).assign(Character=c.name) for c in characters]
    df = pd.concat(frames, ignore_index=True)
    return _table("Attack breakdown", df[["Character", *[col for col in df.columns if col != "Character"]]],
                  "Exact hit chances and expected damage of each attack against the enemy, to check the inputs are what you expect")

def _leaderboard(characters, df_by_rounds, rounds_per_fight):
    rows = []
    for c, df in zip(characters, df_by_rounds):
        attacks = max(attacks_per_round(c, rounds_per_fight), 1e-9)
        rows.append({"Character": c.name, "Mean DPR": round(df["Damage"].mean(), 2), "Median": float(df["Damage"].median()),
                     "25%": float(df["Damage"].quantile(0.25)), "75%": float(df["Damage"].quantile(0.75)),
                     "Attacks/Round": round(attacks_per_round(c, rounds_per_fight), 3),
                     "Hit %": round(100 * df["Hit"].mean() / attacks, 1), "Crit %": round(100 * df["Hit (Crit)"].mean() / attacks, 1)})
    rows.sort(key=lambda r: -r["Mean DPR"])
    return _table("Leaderboard", pd.DataFrame(rows))

def _headline(values, unit, higher_is_better=True, context=""):
    """ The headline: each character's number, best first, and the gap to the next """
    order = sorted(values.items(), key=lambda kv: -kv[1] if higher_is_better else kv[1])
    return {"unit": unit, "context": context, "higherIsBetter": higher_is_better,
            "values": [{"name": name, "value": round(float(v), 2)} for name, v in order]}

def simulate(characters, enemy_dict, graph="DPR Distribution", num_rounds=10000, rounds_per_fight=3, sweep_parameter="Armor Class",
             ruleset="bg3", seed=1):
    """ Runs one graph type; returns {figure, headline, tables} or {problems} """
    parsed, foe, problems = parse(characters, enemy_dict)
    if problems:
        return {"problems": problems}
    if not num_rounds or int(num_rounds) < 1:
        return {"problems": ["The number of rounds must be at least 1"]}
    num_rounds, rounds_per_fight = int(num_rounds), max(int(rounds_per_fight or 3), 1)
    rng = set_seed(seed)
    tables = []
    if graph in ("DPR Distribution", "DPA Distribution"):
        dfs, df_by_rounds, _ = simulate_rounds_from_characters(parsed, foe, num_rounds=num_rounds, save_memory=True, rng=rng,
                                                               rounds_per_fight=rounds_per_fight)
        if graph == "DPR Distribution":
            fig = generate_plot_data(parsed, df_by_rounds, template=TEMPLATE, title="Damage Per Round Distribution", enemy=foe,
                                     rounds_per_fight=rounds_per_fight)
        else:
            fig = generate_damage_per_attack_histogram(parsed, dfs, template=TEMPLATE, title="Damage Per Attack Distribution")
        headline = _headline({c.name: df["Damage"].mean() for c, df in zip(parsed, df_by_rounds)}, "damage per round", context=f"against {foe.name}")
        tables.append(_leaderboard(parsed, df_by_rounds, rounds_per_fight))
    elif graph in SWEEPS:
        by_round = SWEEPS[graph]
        df = run_sweep(parsed, foe, sweep_parameter, by_round=by_round, ruleset=ruleset, num_rounds=num_rounds, rng=rng, rounds_per_fight=rounds_per_fight)
        order = [c.name for c in parsed]
        fig = generate_line_plots(df, template=TEMPLATE, groupby="Character" if by_round else "Character-Attack", order=order, x_col=sweep_parameter)
        means = df.groupby(["Character", sweep_parameter])["mean"].sum().groupby("Character").mean()
        headline = _headline({n: means[n] for n in order if n in means}, f"average damage per round over {sweep_parameter} "
                             f"{df[sweep_parameter].min()} to {df[sweep_parameter].max()}")
        pivot = df.groupby(["Character", sweep_parameter])["mean"].sum().unstack(sweep_parameter).round(2).reindex(order)
        tables.append(_table(f"Mean damage per round by {sweep_parameter}", pivot))
        if sweep_parameter == "Armor Class":
            insights = [i for c in parsed for i in power_attack_insights(c, foe, ARMOR_CLASSES, rounds_per_fight)]
            if insights:
                tables.append(_table("Power attack insights", pd.DataFrame(insights)))
    elif graph == "Rounds to Kill":
        df_rtk = simulate_rounds_to_kill(parsed, foe, num_rounds=num_rounds, max_rounds=MAX_ROUNDS_TO_KILL, rng=rng)
        fig = generate_rounds_to_kill_plot(df_rtk, MAX_ROUNDS_TO_KILL, foe.hit_points, template=TEMPLATE)
        headline = _headline(df_rtk.mean().to_dict(), "rounds on average", higher_is_better=False, context=f"to kill {foe.name} ({foe.hit_points} HP)")
        summary = pd.DataFrame({"Mean": df_rtk.mean().round(2), "Median": df_rtk.median(), "25%": df_rtk.quantile(0.25), "75%": df_rtk.quantile(0.75)})
        tables.append(_table("Rounds to kill", summary.rename_axis("Character")))
    elif graph == "Damage per Fight":
        fights = simulate_fights(parsed, foe, num_fights=max(num_rounds // rounds_per_fight, 1), rounds_per_fight=rounds_per_fight, rng=rng)
        fig = generate_fight_plot(fights, template=TEMPLATE)
        headline = _headline({n: d.sum(axis=0).mean() for n, d in fights.items()}, f"damage per {rounds_per_fight} round fight", context=f"against {foe.name}")
        tables.append(_table("Damage per fight", fight_summary(fights), "Limited attacks are used in the first rounds of each fight, limited once "
                             "per turn damage on the first hits until it runs out"))
    else:
        return {"problems": [f"Unknown graph type {graph}"]}
    tables.append(_breakdown(parsed, foe, rounds_per_fight))
    return {"figure": _figure(fig), "headline": headline, "tables": tables}

def variant(character, key):
    """ A copy of the character with one change (copy menu), or {problems} when the change isn't possible """
    parsed, _, problems = parse([character], Enemy().to_dict())
    if problems:
        return {"problems": problems}
    try:
        return {"character": make_variant(parsed[0], key).to_dict()}
    except ValueError as e:
        return {"problems": [str(e)]}

def export(characters, enemy_dict, kind, num_rounds=10000, rounds_per_fight=3, sweep_parameter="Armor Class", ruleset="bg3", seed=1):
    """ Raw simulated data as CSV text: every round, every attack, a sweep, rounds to kill or every fight """
    parsed, foe, problems = parse(characters, enemy_dict)
    if problems:
        return None, problems
    rng = set_seed(seed)
    rounds_per_fight = max(int(rounds_per_fight or 3), 1)
    if kind in ("Damage per round", "Damage per attack"):
        dfs, df_by_rounds, _ = simulate_rounds_from_characters(parsed, foe, num_rounds=int(num_rounds), rng=rng, rounds_per_fight=rounds_per_fight)
        frames = df_by_rounds if kind == "Damage per round" else [d.sort_values(by=["Round"]) for d in dfs]
        df = pd.concat([f.assign(Name=c.name) for c, f in zip(parsed, frames)], ignore_index=True)
        df = df[["Name", *[col for col in df.columns if col != "Name"]]]
    elif kind == "Sweep":
        df = run_sweep(parsed, foe, sweep_parameter, by_round=True, ruleset=ruleset, num_rounds=int(num_rounds), rng=rng, rounds_per_fight=rounds_per_fight)
    elif kind == "Rounds to kill":
        df = simulate_rounds_to_kill(parsed, foe, num_rounds=int(num_rounds), max_rounds=MAX_ROUNDS_TO_KILL, rng=rng).rename_axis("Fight").reset_index()
    elif kind == "Damage per fight":
        df = fight_export(simulate_fights(parsed, foe, num_fights=max(int(num_rounds) // rounds_per_fight, 1), rounds_per_fight=rounds_per_fight, rng=rng))
    else:
        return None, [f"Unknown export {kind}"]
    return df.to_csv(index=False), []

def distribution(character, enemy_dict, rounds_per_fight=None):
    """ The exact damage per round distribution of one character, {damage: probability} """
    parsed, foe, problems = parse([character], enemy_dict)
    if problems:
        return {"problems": problems}
    probs = damage_per_round(parsed[0], foe, rounds_per_fight)
    return {"probabilities": [float(p) for p in probs]}

__all__ = ["options", "default_session", "preset_character", "enemy", "template_attacks", "expected", "simulate", "variant", "export", "distribution", "asdict"]
