""" Plotly figures for the simulator's results (the same figures the Dash app drew), from simulated data and the exact distributions """
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from computations.numerical_simulation import describe

COLORS = px.colors.qualitative.Plotly
# Histograms send bar heights, not every simulated value; at most this many bars per character
MAX_BINS = 200

def calc_opacity(num_categories, o_init=0.75, o_slope=0.2, o_min=0.25, per_category=5):
    """ Plotly slows down with too many overlapping histograms, so this function reduces the opacity as the number of categories increases"""
    reduction = (num_categories // per_category)*o_slope
    opacity = max([o_init - reduction, o_min])
    return opacity

def generate_plot_data(characters, df_by_rounds, template='plotly_dark', title=None, enemy=None, rounds_per_fight=None, **kwargs):
    """ Generates the plot data for the DPR Distribution Histogram. With the enemy, each histogram gets its exact distribution as a line """
    groups = {c.name: df["Damage"].to_numpy() for c, df in zip(characters, df_by_rounds)}
    exact = {}
    if enemy is not None:
        from computations.exact import damage_per_round # pylint: disable=import-outside-toplevel
        for c in characters:
            try:
                exact[c.name] = damage_per_round(c, enemy, rounds_per_fight)
            except Exception: # pylint: disable=broad-exception-caught
                pass # The smooth fit stands in
    return generate_histogram(groups, opacity=calc_opacity(len(characters)), template=template, title=title, exact=exact, **kwargs)

def box_stats(values):
    """ Tukey box plot statistics: quartiles, whiskers at the furthest values within 1.5 IQR, and the mean """
    q1, median, q3 = np.percentile(values, [25, 50, 75])
    iqr = q3 - q1
    inside = values[(values >= q1 - 1.5 * iqr) & (values <= q3 + 1.5 * iqr)]
    return {"q1": [q1], "median": [median], "q3": [q3], "lowerfence": [inside.min()], "upperfence": [inside.max()], "mean": [values.mean()]}

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

def generate_histogram(groups, colors=None, histnorm='percent', opacity=0.75, x_title="Damage", template='plotly_dark', title=None, fit=True, exact=None,
                       **kwargs):
    """ Overlaid histograms of integer values with a box plot of each group above, from {name: values}.
        Bins are one damage wide, or wider so there are at most MAX_BINS. fit adds a curve over each histogram: the exact distribution
        when exact has one for the group ({name: probabilities indexed by damage}, computations.exact), else a smooth kernel density fit.
        Hover it for the mean, standard deviation and skew """
    from plotly.subplots import make_subplots # pylint: disable=import-outside-toplevel
    groups = {name: np.asarray(v) for name, v in groups.items() if len(v)}
    colors = colors or {name: COLORS[ii % len(COLORS)] for ii, name in enumerate(groups)}
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.2, 0.8], vertical_spacing=0.03)
    if groups:
        low = int(min(v.min() for v in groups.values()))
        high = int(max(v.max() for v in groups.values()))
        width = max(1, -(-(high - low + 1) // MAX_BINS))
        for name, values in groups.items():
            counts = np.bincount(((values - low) // width).astype(np.int64))
            heights = counts / len(values) * (100 if histnorm == "percent" else 1)
            starts = low + width * np.arange(len(counts))
            keep = counts > 0
            label = "%{x}" if width == 1 else "%{customdata[0]} to %{customdata[1]}"
            fig.add_trace(go.Bar(x=starts[keep] + (width - 1) / 2, y=heights[keep], width=width, name=name, legendgroup=name, opacity=opacity,
                                 marker={"color": colors[name], "line": {"width": 0}}, customdata=np.stack([starts[keep], starts[keep] + width - 1], axis=1),
                                 hovertemplate=f"{name}<br>{x_title} {label}: %{{y:.2f}}{'%' if histnorm == 'percent' else ''}<extra></extra>"),
                          row=2, col=1)
            scale = 100 if histnorm == "percent" else 1
            if fit and (exact or {}).get(name) is not None:
                from computations.exact import binned # pylint: disable=import-outside-toplevel
                probs = np.asarray(exact[name])
                curve = binned(probs, low, width, len(counts))
                damage = np.arange(len(probs))
                mean = float(damage @ probs)
                sd = float(np.sqrt(((damage - mean) ** 2) @ probs))
                skew = float((((damage - mean) / sd) ** 3) @ probs) if sd else 0.0
                fig.add_trace(go.Scatter(x=starts + (width - 1) / 2, y=curve * scale, mode="lines", name=f"{name} (exact)", legendgroup=name,
                                         showlegend=False, line={"color": colors[name], "width": 2},
                                         hovertemplate=f"{name} exact: %{{y:.2f}}{'%' if histnorm == 'percent' else ''}<br>mean {mean:.1f}, "
                                                       f"sd {sd:.1f}, skew {skew:+.2f}, all miss {probs[0]:.1%}<extra></extra>"), row=2, col=1)
            elif fit and len(values) > 30 and values.std() > 0:
                offsets, curve = smooth_curve(counts, width, values)
                mean, sd, skew = distribution_summary(values)
                keep_curve = (low + width * offsets) > 0 if (values == 0).any() else np.ones(len(offsets), dtype=bool)
                fig.add_trace(go.Scatter(x=(low + width * offsets + (width - 1) / 2)[keep_curve], y=(curve * scale)[keep_curve], mode="lines",
                                         name=f"{name} (fit)", legendgroup=name, showlegend=False, line={"color": colors[name], "width": 2},
                                         hovertemplate=f"{name} fit<br>mean {mean:.1f}, sd {sd:.1f}, skew {skew:+.2f}<extra></extra>"), row=2, col=1)
            fig.add_trace(go.Box(y=[name], orientation="h", name=name, legendgroup=name, showlegend=False, marker={"color": colors[name]},
                                 boxmean=True, **box_stats(values)), row=1, col=1)
    fig.update_layout(barmode="overlay", bargap=0, template=template, title=title, legend={"tracegroupgap": 0}, **kwargs)
    fig.update_yaxes(title_text=histnorm.capitalize(), row=2, col=1)
    fig.update_yaxes(showticklabels=False, autorange="reversed", row=1, col=1) # Boxes in legend order, top down
    fig.update_xaxes(title_text=x_title, row=2, col=1)
    return fig

def summary_stats(data: list, by_round=True):
    """ Extracts summary stats to be used for tables and exports"""
    df_summary = []
    for datac in data:
        if by_round:
            datac = datac.drop(["Attack Roll", "Attack Roll (Die)", "Hit (Non-Crit)", "Hit (Crit)"], axis=1)
            datac.rename(columns={"Hit": "Num Hits","Hit (Non-Crit)": "Num Hits (Non-Crit)","Hit (Crit)": "Num Hits (Crit)"}, inplace=True)
            df_summaryc = describe(datac).round(2).T
            df_summaryc.index.set_names([""], inplace=True)
            df_summary.append(df_summaryc)
        else:
            # Assume this is already summary stats
            datac.rename(columns={"Hit": "Num Hits"}, inplace=True)
            datac = datac.T
            datac.index.set_names([""], inplace=True)
            df_summary.append(datac.round(2))
    return df_summary

def generate_line_plots(df_acs, groupby='Character', template='plotly_dark', order=None, x_col='Armor Class'):
    """ Generates a line plot of damage vs armor class (or another swept parameter), used by DPR/DPA vs Armor Class and Level"""
    fig = go.Figure()
    if not order:
        order = df_acs['Character'].unique()
    ii = 0
    alpha = calc_opacity(len(df_acs[groupby].unique()), o_init=0.5, o_slope=0.1)
    for jj, c in enumerate(order):
        df_c = df_acs.loc[df_acs['Character']==c, :]
        for name, g in df_c.groupby(groupby):
            ii = jj
            x = g[x_col]
            fig.add_trace(
                go.Scatter(
                    name=f"{name} (mean)",
                    x=x,
                    y=g['mean'],
                    mode='lines+markers',
                    line=dict(color=COLORS[ii]),
                ))
            fig.add_trace(
                go.Scatter(
                    name=f"{name} (50%)",
                    x=x,
                    y=g['50%'],
                    mode='lines+markers',
                    marker=dict(color=COLORS[ii]),
                    line=dict(dash='dash'),
                    # showlegend=False
                ))
            fig.add_trace(
                go.Scatter(
                    name=f"{name} (75%)",
                    x=x,
                    y=g['75%'],
                    mode='lines',
                    marker=dict(color=COLORS[ii]),
                    line=dict(width=0),
                    showlegend=False
                ))
            # Add alpha to fill color
            rgb_str = px.colors.convert_colors_to_same_type(COLORS[ii])[0][0]
            rgb_str_split = rgb_str.split(")")[0]
            rgba_str = f"rgba{rgb_str_split[3:]},{alpha})"
            fig.add_trace(
                go.Scatter(
                    name=f"{name} (25%-75%)",
                    x=x,
                    y=g['25%'],
                    marker=dict(color=COLORS[ii]),
                    line=dict(width=0),
                    mode='lines',
                    fillcolor=rgba_str,
                    fill='tonexty',
                    # showlegend=False
                ))
            # ii+=1 # If difference colors for each attack are desired
    fig.update_layout(
        xaxis_title=x_col,
        yaxis_title='Damage',
        title=f'Damage Per Round vs {x_col}' if groupby=='Character' else f'Damage Per Attack vs {x_col}',
        template=template,
        legend_traceorder="normal",
    )
    return fig

def generate_damage_per_attack_histogram(characters, dfs, template='plotly_dark', title=None, **kwargs):
    """ Generates a histogram of damage per attack, used by DPA Distribution. Attacks share their character's color """
    groups, colors = {}, {}
    for ii, (c, df) in enumerate(zip(characters, dfs)):
        for attack, values in df.groupby("Attack", observed=True, sort=False)["Damage"]:
            name = f"{c.name}-{attack}"
            groups[name], colors[name] = values.to_numpy(), COLORS[ii % len(COLORS)]
    return generate_histogram(groups, colors=colors, opacity=calc_opacity(len(groups), o_slope=0.25), template=template, title=title, **kwargs)

def generate_rounds_to_kill_plot(df_rtk, max_rounds, hit_points, template='plotly_dark'):
    """ Probability the enemy is dead by each round, one line per character """
    fig = go.Figure()
    rounds = list(range(1, max_rounds + 1))
    for ii, name in enumerate(df_rtk.columns):
        values = df_rtk[name].to_numpy()
        fig.add_trace(go.Scatter(
            name=name,
            x=rounds,
            y=[100 * (values <= r).mean() for r in rounds],
            mode='lines+markers',
            line=dict(color=COLORS[ii % len(COLORS)]),
        ))
    fig.update_layout(
        title=f"Rounds to Kill ({hit_points} HP)",
        xaxis_title='Round',
        yaxis_title='Enemy Dead By Round (%)',
        yaxis_range=[0, 102],
        template=template,
    )
    # Zoom in on the rounds before every character has (almost) always killed the enemy
    last_interesting = int(df_rtk.quantile(0.995).max()) if len(df_rtk) else max_rounds
    fig.update_xaxes(range=[0.5, min(max_rounds, last_interesting + 1) + 0.5], dtick=1)
    return fig

def generate_fight_plot(fights, template='plotly_dark'):
    """ Average damage in each round of a fight, shows bursts from limited resources at the start of fights """
    fig = go.Figure()
    for ii, (name, damage) in enumerate(fights.items()):
        rounds = list(range(1, damage.shape[0] + 1))
        fig.add_trace(go.Scatter(
            name=name,
            x=rounds,
            y=damage.mean(axis=1),
            mode='lines+markers',
            line=dict(color=COLORS[ii % len(COLORS)]),
        ))
    num_rounds = next(iter(fights.values())).shape[0] if fights else 0
    fig.update_layout(
        title=f"Damage by Round of a {num_rounds} Round Fight",
        xaxis_title='Round of the Fight',
        yaxis_title='Average Damage',
        xaxis=dict(dtick=1),
        template=template,
    )
    return fig

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
