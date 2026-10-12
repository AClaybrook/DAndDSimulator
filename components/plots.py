""" Plotting and tables for the app """
# Themes here: https://plotly.com/python/templates/

import warnings
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from dash import html
import dash_bootstrap_components as dbc
from computations.analytic import attacks_per_round
from computations.numerical_simulation import describe

# Color Palette
COLORS = px.colors.qualitative.Plotly

def calc_opacity(num_categories, o_init=0.75, o_slope=0.2, o_min=0.25, per_category=5):
    """ Plotly slows down with too many overlapping histograms, so this function reduces the opacity as the number of categories increases"""
    reduction = (num_categories // per_category)*o_slope
    opacity = max([o_init - reduction, o_min])
    # print(f"Reduction: {reduction}")
    # print(f"Opacity: {opacity}")
    return opacity

def generate_plot_data(characters, df_by_rounds, template='plotly_dark',**kwargs):
    """ Generates the plot data for the DPR Distribution Histogram"""
    data = pd.concat([pd.DataFrame({'Damage': df_by_round["Damage"], 'Type': c.name}) for c, df_by_round in zip(characters,df_by_rounds)]).reset_index(drop=True)
    # Converting types saves about 10x the memory
    data["Damage"] = data["Damage"].astype('int32')
    data["Type"] = data["Type"].astype('category')
    # For memory debugging
    # print(f"Plot data (deep): {data.memory_usage(deep=True).sum()/1000000} MB")
    # print(f"Plot data : {data.memory_usage(deep=False).sum()/1000000} MB")
    # print(f"df_by_rounds (deep): {sum([d.memory_usage(deep=True).sum() for d in df_by_rounds])/1000000} MB")
    # print(f"df_by_rounds : {sum([d.memory_usage(deep=False).sum() for d in df_by_rounds])/1000000} MB")
    fig = generate_histogram(data, x="Damage", color="Type", marginal='box', opacity=calc_opacity(len(characters)),template=template,**kwargs)

    return fig

def generate_histogram(data, x, color, marginal='violin', histnorm='percent', barmode='overlay', opacity=0.75, **kwargs):
    """ Generic histogram helper function with marginal plot"""
    with warnings.catch_warnings():
        warnings.simplefilter(action='ignore', category=FutureWarning)
        fig = px.histogram(
            data,
            x=x,
            color=color,
            marginal=marginal,
            histnorm=histnorm,
            barmode=barmode,
            opacity=opacity,
            **kwargs
        )

    fig.update_layout(yaxis_title=histnorm.capitalize())
    return fig

def generate_distplot(groups, labels, **kwargs):
    """
    Alternative to generate_histogram, but has some performance issues for many data points
    Example Usage:
        groups = [df_by_round["damage"] for df_by_round in df_by_rounds]
        labels = [c.name for c in characters]
        fig = generate_distplot(groups, labels)
    """
    import plotly.figure_factory as ff # pylint: disable=import-outside-toplevel
    fig = ff.create_distplot(groups, labels, show_rug=True)
    fig.update_layout(**kwargs)
    return fig

def generate_bar_plot(data, x="damage",**kwargs):
    """ Basically a bar plot version of generate_distplot with out the side plots, but has some performance issues for many data points """
    def add_damage_percent(data):
        percent_dict = data.groupby("Type")[x].value_counts(normalize=True).to_dict()
        data["Percent"] = data.apply(lambda i: percent_dict[(i["Type"], i[x])], axis=1)*100
        return data
    data1 = add_damage_percent(data.copy())
    fig = px.bar(data1, x=x, y="Percent", color="Type", opacity=0.75,barmode='overlay',**kwargs)
    return fig

def generate_cdf_plot(data):
    """ Generates a Cumulative Distribution Function plot with a histogram"""
    return px.ecdf(data, x="damage", color="Type", marginal="histogram",orientation='h')



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



def build_tables_row(characters, data_summary, by_round=True, width=12):
    """ Builds the tables section from simulation data """
    if by_round:
        table_list = [dbc.Row(dbc.Col(html.H4("Per Round", className="mt-3")))]
    else:
        table_list = [dbc.Row(dbc.Col(html.H4("Per Attack", className="mt-3")))]
    row = []
    for ii, (c, df_table) in enumerate(zip(characters, data_summary)):
        col = []
        col.append(html.H5(c.name, style={'color': COLORS[ii]}))
        col.append(dbc.Table.from_dataframe(df_table, striped=True, bordered=True, hover=True, responsive=True, index=True, size="sm"))
        col.append(html.Br())
        row.append(dbc.Col(col, xs=12, md=6, xl=width))

    table_list.append(dbc.Row(row))
    return table_list

def add_tables(data, characters, by_round=True, width=12):
    """ Processes the data and then builds the tables section from simulation data"""
    data_summary = summary_stats(data, by_round=by_round)

    return build_tables_row(characters, data_summary, width=width, by_round=by_round)

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

def generate_damage_per_attack_histogram(characters, dfs ,template='plotly_dark', **kwargs):
    """ Generates a histogram of damage per attack, used by DPA Distribution"""
    attacks = []
    attack_color_map = {}
    for ii, (c, df_c_temp) in enumerate(zip(characters,dfs)):
        df_c = df_c_temp[["Damage","Attack"]].copy()
        df_c['Type'] = c.name + "-" + df_c['Attack'].astype(str)
        df_c = df_c.drop('Attack',axis=1)
        attacks.append(df_c)
        for a in df_c['Type'].unique():
            attack_color_map[a] = COLORS[ii].lower()

    df_attacks = pd.concat(attacks).reset_index(drop=True)
    df_attacks["Damage"] = df_attacks["Damage"].astype('int16') # This plot is very memory sensitive, need to reduce the size as much as possible
    df_attacks["Type"] = df_attacks["Type"].astype('category')
    fig = generate_histogram(df_attacks, x="Damage", color="Type", marginal='box',opacity=calc_opacity(len(df_attacks["Type"].unique()),o_slope=0.25), template=template,**kwargs)
    # Manually override colors
    for data in fig.data:
        data.marker.color = attack_color_map[data.legendgroup]

    return fig

def color_header(name, ii):
    return html.Span("\u25CF ", style={'color': COLORS[ii % len(COLORS)]}), name

def build_leaderboard(characters, df_by_rounds, rounds_per_fight=None):
    """ Ranks characters by mean damage per round """
    rows = []
    for ii, (c, df) in enumerate(zip(characters, df_by_rounds)):
        num_attacks = max(attacks_per_round(c, rounds_per_fight), 1e-9)
        rows.append({
            "ii": ii,
            "Character": c.name,
            "Mean DPR": df["Damage"].mean(),
            "Median": df["Damage"].median(),
            "25%-75%": f"{df['Damage'].quantile(0.25):g} - {df['Damage'].quantile(0.75):g}",
            "Attacks": f"{attacks_per_round(c, rounds_per_fight):.3g}",
            "Hit %": 100 * df["Hit"].mean() / num_attacks,
            "Crit %": 100 * df["Hit (Crit)"].mean() / num_attacks,
        })
    rows.sort(key=lambda r: r["Mean DPR"], reverse=True)
    best = rows[0]["Mean DPR"] if rows else 0
    header = html.Thead(html.Tr([html.Th(h) for h in ["#", "Character", "Mean DPR", "vs Best", "Median", "25%-75%", "Attacks/Round", "Hit %", "Crit %"]]))
    body = html.Tbody([
        html.Tr([
            html.Td(rank),
            html.Td(color_header(r["Character"], r["ii"])),
            html.Td(html.B(f"{r['Mean DPR']:.2f}")),
            html.Td(f"{100 * r['Mean DPR'] / best:.0f}%" if best else "-"),
            html.Td(f"{r['Median']:g}"),
            html.Td(r["25%-75%"]),
            html.Td(r["Attacks"]),
            html.Td(f"{r['Hit %']:.1f}"),
            html.Td(f"{r['Crit %']:.1f}"),
        ]) for rank, r in enumerate(rows, start=1)
    ])
    return [
        dbc.Row(dbc.Col(html.H4("Leaderboard", className="mt-3"))),
        dbc.Row(dbc.Col(dbc.Table([header, body], striped=True, bordered=True, hover=True, responsive=True, size="sm"))),
    ]

def build_breakdown_tables(characters, breakdowns, width=3):
    """ Per attack hit chance and expected damage (exact, from computations.analytic) """
    row = []
    for ii, (c, df) in enumerate(zip(characters, breakdowns)):
        total = df["Expected"].sum()
        row.append(dbc.Col([
            html.H5(c.name, style={'color': COLORS[ii]}),
            dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True, responsive=True, size="sm"),
            html.P(f"Expected damage per round: {total:.2f}", className="small text-muted"),
        ], xs=12, md=6, xl=width))
    return [
        dbc.Row(dbc.Col([
            html.H4("Attack Breakdown", className="mt-3 mb-0"),
            html.P("Exact hit chances and expected damage against the current enemy, useful to check the inputs are what you expect", className="small text-muted"),
        ])),
        dbc.Row(row),
    ]

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

def rounds_to_kill_summary(df_rtk, max_rounds):
    """ Summary table of the rounds to kill per character """
    summary = pd.DataFrame({
        "Mean Rounds": df_rtk.mean().round(2),
        "Median": df_rtk.median(),
        "25%": df_rtk.quantile(0.25),
        "75%": df_rtk.quantile(0.75),
        "Dead by Round 3 (%)": (100 * (df_rtk <= 3).mean()).round(1),
        f"Alive After {max_rounds} (%)": (100 * (df_rtk > max_rounds).mean()).round(1),
    })
    summary.index.name = "Character"
    return [
        dbc.Row(dbc.Col(html.H4("Rounds to Kill", className="mt-3"))),
        dbc.Row(dbc.Col(dbc.Table.from_dataframe(summary.reset_index(), striped=True, bordered=True, hover=True, responsive=True, size="sm"))),
    ]

def build_sweep_leaderboard(df_sweep, x_col, order):
    """ Ranks characters by their average damage per round over the swept range """
    rows = []
    for ii, name in enumerate(order):
        g = df_sweep.loc[df_sweep["Character"] == name]
        if g.empty:
            continue
        rows.append({"ii": ii, "Character": name, "avg": g["mean"].astype(float).mean(),
                     "low": g["mean"].astype(float).iloc[0], "high": g["mean"].astype(float).iloc[-1]})
    rows.sort(key=lambda r: r["avg"], reverse=True)
    first, last = df_sweep[x_col].iloc[0], df_sweep[x_col].iloc[-1]
    header = html.Thead(html.Tr([html.Th(h) for h in ["#", "Character", f"Average DPR ({x_col} {first} to {last})", f"DPR at {first}", f"DPR at {last}"]]))
    body = html.Tbody([
        html.Tr([
            html.Td(rank),
            html.Td(color_header(r["Character"], r["ii"])),
            html.Td(html.B(f"{r['avg']:.2f}")),
            html.Td(f"{r['low']:.2f}"),
            html.Td(f"{r['high']:.2f}"),
        ]) for rank, r in enumerate(rows, start=1)
    ])
    return [
        dbc.Row(dbc.Col(html.H4("Leaderboard", className="mt-3"))),
        dbc.Row(dbc.Col(dbc.Table([header, body], striped=True, bordered=True, hover=True, responsive=True, size="sm"))),
    ]

def build_insights(insights):
    """ Table of when to turn power attack feats (GWM, Sharpshooter) on or off """
    if not insights:
        return []
    return [
        dbc.Row(dbc.Col([
            html.H4("Insights", className="mt-3 mb-0"),
            html.P("Exact expected damage with each power attack feat on vs off against the current enemy's defenses at each armor class", className="small text-muted"),
        ])),
        dbc.Row(dbc.Col(dbc.Table.from_dataframe(pd.DataFrame(insights), striped=True, bordered=True, hover=True, responsive=True, size="sm"))),
    ]

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

def fight_summary(fights):
    """ Table of total damage per fight and how it is spread over the rounds """
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
    return [
        dbc.Row(dbc.Col([
            html.H4("Damage per Fight", className="mt-3 mb-0"),
            html.P("Limited attacks are used in the first rounds of each fight and limited once per turn damage is used on the first hits until it runs out",
                   className="small text-muted"),
        ])),
        dbc.Row(dbc.Col(dbc.Table.from_dataframe(pd.DataFrame(rows), striped=True, bordered=True, hover=True, responsive=True, size="sm"))),
    ]

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

def results_summary(values, unit, higher_is_better=True, context=""):
    """ One line summary of a simulation: who comes out on top and by how much """
    if not values:
        return None
    ranked = sorted(values.items(), key=lambda kv: kv[1], reverse=higher_is_better)
    best, best_value = ranked[0]
    text = [html.B(best), f" leads with {best_value:.2f} {unit}"]
    if len(ranked) > 1:
        second, second_value = ranked[1]
        if second_value:
            difference = (best_value / second_value - 1) if higher_is_better else (1 - best_value / second_value)
            text.append(f", {100 * difference:.0f}% {'ahead of' if higher_is_better else 'faster than'} {second} ({second_value:.2f})")
    if context:
        text.append(f" {context}")
    return dbc.Alert([html.I(className="fa-solid fa-trophy me-2"), *text], color="info", class_name="py-2 mb-2")
