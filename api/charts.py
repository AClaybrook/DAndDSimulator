""" Chart data for the simulator's results: what each chart shows as plain numbers, which the front end draws (frontend/src/pages/simulator/
    charts.ts). Histograms are sent as bar heights, never as every simulated value """
import numpy as np
import pandas as pd

# At most this many bars per histogram
MAX_BINS = 200

def box_stats(values):
    """ Quartiles, the furthest values within 1.5 IQR of them, and the mean """
    q1, median, q3 = np.percentile(values, [25, 50, 75])
    iqr = q3 - q1
    inside = values[(values >= q1 - 1.5 * iqr) & (values <= q3 + 1.5 * iqr)]
    return {"q1": float(q1), "median": float(median), "q3": float(q3), "low": float(inside.min()), "high": float(inside.max()), "mean": float(values.mean())}

def smooth_curve(counts, width, values):
    """ A smooth fit of a binned distribution when the exact one isn't known: a Gaussian kernel density estimate of the counts, in the same
        units as the bars. The bandwidth is chosen by leave-one-out cross-validation (the width whose curve, built without each value, gives
        the values the highest likelihood), so a hump per number of hits keeps its peak. Rounds where everything missed (exactly 0) are a
        spike no smooth curve can follow, they are left to their bar. Returns (bin offsets, heights as a share of all values per bin) """
    n = len(values)
    counts = counts.astype(float).copy()
    zeros = int((values == 0).sum())
    if values.min() == 0:
        counts[0] -= zeros
    m = counts.sum()
    rest = values[values != 0] if zeros else values
    if m < 2 or rest.std() == 0:
        return np.arange(len(counts)), counts / n
    spread = min(rest.std(), (np.percentile(rest, 75) - np.percentile(rest, 25)) / 1.34 or rest.std())
    silverman = 1.06 * spread * m ** -0.2 / width # In bins
    best = None
    for factor in (0.1, 0.15, 0.2, 0.3, 0.4, 0.5): # Wider never helped: it flattens the hit-count peaks
        bandwidth = max(factor * silverman, 0.6)
        reach = int(np.ceil(4 * bandwidth))
        kernel = np.exp(-0.5 * (np.arange(-reach, reach + 1) / bandwidth) ** 2)
        kernel /= kernel.sum()
        smoothed = np.convolve(counts, kernel, mode="full")[reach:reach + len(counts)]
        leave_out = (smoothed - kernel[reach] * counts) / (m - 1)
        seen = counts > 0
        likelihood = float(np.sum(counts[seen] * np.log(np.maximum(leave_out[seen], 1e-12))))
        if best is None or likelihood > best[0]:
            best = (likelihood, smoothed)
    return np.arange(len(counts)), best[1] / n

def distribution_summary(values):
    """ Mean, standard deviation and skew of a distribution, the shape of a fit in three numbers """
    mean, sd = float(np.mean(values)), float(np.std(values))
    skew = float(np.mean(((values - mean) / sd) ** 3)) if sd else 0.0
    return mean, sd, skew

def _rounded(values, digits=4):
    return [round(float(v), digits) for v in values]

def distribution(groups, owners=None, exact=None, title="", x_title="Damage"):
    """ Histograms of integer values, one series per group, from {name: values}. Bins are one damage wide, or wider so there are at most
        MAX_BINS, shared by every series. Each series has its bars (percent of rounds per bin), a curve over them (the exact distribution
        when exact has one for the group, {name: probabilities indexed by damage} from computations.exact, else a smooth fit), box
        statistics and the mean, standard deviation and skew. owners: {name: index of the character it belongs to}, for its colour """
    groups = {name: np.asarray(v) for name, v in groups.items() if len(v)}
    chart = {"kind": "distribution", "title": title, "xTitle": x_title, "binWidth": 1, "series": []}
    if not groups:
        return chart
    low = int(min(v.min() for v in groups.values()))
    high = int(max(v.max() for v in groups.values()))
    width = max(1, -(-(high - low + 1) // MAX_BINS))
    chart["binWidth"] = width
    for index, (name, values) in enumerate(groups.items()):
        counts = np.bincount(((values - low) // width).astype(np.int64))
        starts = low + width * np.arange(len(counts))
        keep = counts > 0
        series = {"name": name, "owner": (owners or {}).get(name, index), "start": [int(s) for s in starts[keep]],
                  "percent": _rounded(100 * counts[keep] / len(values)), "box": box_stats(values), "curve": None}
        probs = (exact or {}).get(name)
        if probs is not None:
            from computations.exact import binned # pylint: disable=import-outside-toplevel
            probs = np.asarray(probs)
            damage = np.arange(len(probs))
            mean = float(damage @ probs)
            sd = float(np.sqrt(((damage - mean) ** 2) @ probs))
            skew = float((((damage - mean) / sd) ** 3) @ probs) if sd else 0.0
            series["curve"] = {"kind": "exact", "start": [int(s) for s in starts], "percent": _rounded(100 * binned(probs, low, width, len(counts)))}
            series["stats"] = {"mean": round(mean, 2), "sd": round(sd, 2), "skew": round(skew, 2), "allMiss": round(float(probs[0]), 4)}
        else:
            mean, sd, skew = distribution_summary(values)
            series["stats"] = {"mean": round(mean, 2), "sd": round(sd, 2), "skew": round(skew, 2), "allMiss": None}
            if len(values) > 30 and values.std() > 0:
                offsets, curve = smooth_curve(counts, width, values)
                keep_curve = (low + width * offsets) > 0 if (values == 0).any() else np.ones(len(offsets), dtype=bool)
                series["curve"] = {"kind": "fit", "start": [int(s) for s in (low + width * offsets)[keep_curve]], "percent": _rounded(100 * curve[keep_curve])}
        chart["series"].append(series)
    return chart

def damage_per_round(characters, df_by_rounds, enemy=None, rounds_per_fight=None, title="Damage per round"):
    """ The DPR distribution of each character. With the enemy, each histogram gets its exact distribution as the curve """
    groups = {c.name: df["Damage"].to_numpy() for c, df in zip(characters, df_by_rounds)}
    exact = {}
    if enemy is not None:
        from computations.exact import damage_per_round as exact_distribution # pylint: disable=import-outside-toplevel
        for c in characters:
            try:
                exact[c.name] = exact_distribution(c, enemy, rounds_per_fight)
            except Exception: # pylint: disable=broad-exception-caught
                pass # The smooth fit stands in
    return distribution(groups, exact=exact, title=title)

def damage_per_attack(characters, dfs, title="Damage per attack"):
    """ The damage distribution of each attack, attacks share their character's colour """
    groups, owners = {}, {}
    for ii, (c, df) in enumerate(zip(characters, dfs)):
        for attack, values in df.groupby("Attack", observed=True, sort=False)["Damage"]:
            name = f"{c.name}: {attack}"
            groups[name], owners[name] = values.to_numpy(), ii
    return distribution(groups, owners=owners, title=title)

def sweep(df, groupby="Character", order=None, x_col="Armor Class"):
    """ Damage against one swept parameter: for each character (or attack) the mean, the median and the 25% to 75% band at every value """
    order = list(order) if order is not None else list(df["Character"].unique())
    series = []
    for owner, character in enumerate(order):
        for name, g in df.loc[df["Character"] == character].groupby(groupby, sort=False):
            g = g.sort_values(x_col)
            series.append({"name": str(name), "owner": owner, "x": [v.item() if hasattr(v, "item") else v for v in g[x_col]],
                           "mean": _rounded(g["mean"], 3), "median": _rounded(g["50%"], 3), "q1": _rounded(g["25%"], 3), "q3": _rounded(g["75%"], 3)})
    by_round = groupby == "Character"
    return {"kind": "sweep", "title": f"Damage per {'round' if by_round else 'attack'} by {x_col.lower()}", "xTitle": x_col,
            "yTitle": f"Damage per {'round' if by_round else 'attack'}", "series": series}

def rounds_to_kill(df_rtk, max_rounds, hit_points):
    """ Chance the enemy is dead by each round, one line per character. Shown up to the round (almost) every fight is over by """
    last_interesting = int(df_rtk.quantile(0.995).max()) if len(df_rtk) else max_rounds
    shown = min(max_rounds, last_interesting + 1)
    rounds = list(range(1, shown + 1))
    series = [{"name": str(name), "owner": ii, "y": _rounded([100 * (df_rtk[name].to_numpy() <= r).mean() for r in rounds], 2)}
              for ii, name in enumerate(df_rtk.columns)]
    return {"kind": "lines", "title": f"Enemy dead by round ({hit_points} HP)", "xTitle": "Round", "yTitle": "Fights won by this round (%)",
            "x": rounds, "yMax": 100, "unit": "%", "series": series}

def fight(fights):
    """ Average damage in each round of a fight, shows bursts from limited resources at the start of fights """
    num_rounds = next(iter(fights.values())).shape[0] if fights else 0
    series = [{"name": name, "owner": ii, "y": _rounded(damage.mean(axis=1), 2)} for ii, (name, damage) in enumerate(fights.items())]
    return {"kind": "lines", "title": f"Damage by round of a {num_rounds} round fight", "xTitle": "Round of the fight", "yTitle": "Average damage",
            "x": list(range(1, num_rounds + 1)), "yMax": None, "unit": "", "series": series}

def fight_export(fights):
    """ One row per character and fight, with the damage of each round """
    frames = []
    for name, damage in fights.items():
        df = pd.DataFrame(damage.T, columns=[f"Round {r}" for r in range(1, damage.shape[0] + 1)])
        df.insert(0, "Total", damage.sum(axis=0))
        df.insert(0, "Fight", range(1, damage.shape[1] + 1))
        df.insert(0, "Name", name)
        frames.append(df)
    return pd.concat(frames, ignore_index=True)

def fight_summary(fights):
    """ Total damage per fight and how it is spread over the rounds, one row per character, best first """
    rows = []
    for name, damage in fights.items():
        totals = damage.sum(axis=0)
        by_round = damage.mean(axis=1)
        rows.append({
            "Character": name,
            "Mean Fight Damage": round(float(totals.mean()), 2),
            "Median": float(np.median(totals)),
            "25%": float(np.percentile(totals, 25)),
            "75%": float(np.percentile(totals, 75)),
            "Average per Round": round(float(by_round.mean()), 2),
            "Round 1": round(float(by_round[0]), 2),
            "Last Round": round(float(by_round[-1]), 2),
        })
    rows.sort(key=lambda r: r["Mean Fight Damage"], reverse=True)
    return pd.DataFrame(rows)
