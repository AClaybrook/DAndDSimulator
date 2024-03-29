""" Plotting and tables for the app """
# Themes here: https://plotly.com/python/templates/

from typing import List
import warnings
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from dash import html
import dash_bootstrap_components as dbc

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
    print(f"Plot data in hist: {data.memory_usage(deep=True).sum()/1000000} MB")
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



def summary_stats(data: List, by_round=True):
    """ Extracts summary stats to be used for tables and exports"""
    df_summary = []
    for datac in data:
        if by_round:
            datac = datac.drop(["Attack Roll", "Attack Roll (Die)", "Hit (Non-Crit)", "Hit (Crit)"], axis=1)
            datac.rename(columns={"Hit": "Num Hits","Hit (Non-Crit)": "Num Hits (Non-Crit)","Hit (Crit)": "Num Hits (Crit)"}, inplace=True)
            df_summaryc = datac.describe().drop(["count","std"],axis=0).round(2).T
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
        table_list = [dbc.Row(dbc.Col(html.H4("Per Round")))]
    else:
        table_list = [dbc.Row(dbc.Col(html.H4("Per Attack")))]
    row = []
    for ii, (c, df_table) in enumerate(zip(characters, data_summary)):
        col = []
        col.append(html.H4(c.name, style={'color': COLORS[ii]}))
        col.append(dbc.Table.from_dataframe(df_table, striped=True, bordered=True, hover=True, responsive=True, index=True))
        col.append(html.Br())
        row.append(dbc.Col(col, width={"size": width}))

    table_list.append(dbc.Row(row))
    return table_list

def add_tables(data, characters, by_round=True, width=12):
    """ Processes the data and then builds the tables section from simulation data"""
    data_summary = summary_stats(data, by_round=by_round)

    return build_tables_row(characters, data_summary, width=width, by_round=by_round)

def data_to_store(characters, dfs):
    """ Stores character names and associated data in a dictionary, in perparation for use in a dcc.Store """
    store = {}
    for ii, (c, df) in enumerate(zip(characters, dfs)):
        store[f"{ii},{c.name}"] = df.to_dict('records')
    return store

def data_from_store(store):
    """ Extracts character names and associated data from a dcc.Store component """
    dfs = []
    names = []
    for key, data in store.items():
        _, name = key.split(',')
        names.append(name)
        dfs.append(pd.DataFrame(data))
    return names, dfs

def generate_line_plots(df_acs, groupby='Character', template='plotly_dark', order=None):
    """ Generates a line plot of damage vs armor class, used by DPR vs Armor Class and DPA vs Armor Class"""
    fig = go.Figure()
    if not order:
        order = df_acs['Character'].unique()
    ii = 0
    alpha = calc_opacity(len(df_acs[groupby].unique()), o_init=0.5, o_slope=0.1)
    for jj, c in enumerate(order):
        df_c = df_acs.loc[df_acs['Character']==c, :]
        for name, g in df_c.groupby(groupby):
            ii = jj
            x = g["Armor Class"]
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
        xaxis_title='Armor Class',
        yaxis_title='Damage',
        title='Damage Per Round vs Armor Class' if groupby=='Character' else 'Damage Per Attack vs Armor Class',
        template=template,
        legend_traceorder="normal",
    )
    return fig

def line_plots(df_acs, template='plotly_dark'):
    """ A simple plot of damage vs armor class"""
    for _, g in df_acs.groupby('Character'):

        fig = go.Figure()
        fig.add_trace(go.Line(
                name = g['Character'].iloc[0],
                x=g['Armor Class'],
                y=g['mean'],
                error_y=dict(
                    type='data',
                    symmetric=False,
                    array=g['75%'],
                    arrayminus=g['25%'])
                ))
    fig.update_layout(xaxis_title="Armor Class", yaxis_title="Damage", template=template)
    fig.show()
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
    for ii, data in enumerate(fig.data):
        data.marker.color = attack_color_map[data.legendgroup]

    return fig
