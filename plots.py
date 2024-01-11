# Plotting
# Themes here: https://plotly.com/python/templates/
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from dash import html
import dash_bootstrap_components as dbc
from typing import List

# Color Palette
COLORS = px.colors.qualitative.Plotly

def generate_plot_data(characters, df_by_rounds, template='plotly_dark'):
    data = pd.concat([pd.DataFrame({'damage': df_by_round["Damage"], 'Type': c.name}) for c, df_by_round in zip(characters,df_by_rounds)])
    fig = generate_histogram(data, x="damage", color="Type", marginal='box', template=template)
    return fig

def generate_histogram(data, x, color, marginal='violin', histnorm='percent', barmode='overlay', opacity=0.75, **kwargs):
    """Histogram with marginal plot"""
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
    return fig

def generate_distplot(groups, labels, **kwargs):
    """
    Example Usage:
        groups = [df_by_round["damage"] for df_by_round in df_by_rounds]
        labels = [c.name for c in characters]
        fig = generate_distplot(groups, labels)
    """
    import plotly.figure_factory as ff
    fig = ff.create_distplot(groups, labels, show_rug=False, **kwargs)
    return fig

def generate_bar_plot(data):
    def add_damage_percent(data):
        percent_dict = data.groupby("Type")["damage"].value_counts(normalize=True).to_dict()
        data["Percent"] = data.apply(lambda x: percent_dict[(x["Type"], x["damage"])], axis=1)*100
        return data
    data1 = add_damage_percent(data.copy())
    fig = px.bar(data1, x="damage", y="Percent", color="Type", opacity=0.75,barmode='overlay')
    return fig

def generate_cdf_plot(data):
    return px.ecdf(data, x="damage", color="Type", marginal="histogram",orientation='h')



def summary_stats(data: List, by_round=True):
    df_summary = []
    for datac in data:
        if by_round:
            datac = datac.drop(["Attack Roll", "Attack Roll (Die)", "Hit (Non-Crit)", "Hit (Crit)"], axis=1)
            datac.rename(columns={"Hit": "Num Hits","Hit (Non-Crit)": "Num Hits (Non-Crit)","Hit (Crit)": "Num Hits (Crit)"}, inplace=True)
            df_summaryc = datac.describe().drop(["count","std"],axis=0).round(2)
            df_summaryc.index.set_names([""], inplace=True)
            df_summary.append(df_summaryc)
        else:
            # Assume this is already summary stats
            datac.rename(columns={"Hit": "Num Hits"}, inplace=True)
            datac.index.set_names(["Attack Name",""], inplace=True)
            df_summary.append(datac.round(2))
    return df_summary

def add_tables(data, characters, by_round=True, width=12):
    if by_round:
        table_list = [dbc.Row(dbc.Col(html.H4("Per Round")))]
    else:
        table_list = [dbc.Row(dbc.Col(html.H4("Per Attack")))]
    
    row = []
    
    data_summary = summary_stats(data, by_round=by_round)
    for ii, (c, df_table) in enumerate(zip(characters, data_summary)):
        col = []  
        col.append(html.H4(c.name, style={'color': COLORS[ii]})) 
        col.append(dbc.Table.from_dataframe(df_table, striped=True, bordered=True, hover=True, responsive=True, index=True))
        col.append(html.Br())
        row.append(dbc.Col(col, width={"size": width}))
    table_list.append(dbc.Row(row))
    return table_list


def data_to_store(characters, dfs):
    store = {}
    for ii, (c, df) in enumerate(zip(characters, dfs)):
        store[f"{ii},{c.name}"] = df.to_dict('records')
    return store

def data_from_store(store):
    dfs = []
    names = []
    for key, data in store.items():
        _, name = key.split(',')
        names.append(name)
        dfs.append(pd.DataFrame(data))
    return names, dfs



def line_plots(df_acs, template='plotly_dark'):
    """Plot damage vs armor class"""
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

def generate_line_plots(df_acs,template='plotly_dark'):
    fig = go.Figure()
    for ii, (name, g) in enumerate(df_acs.groupby('Character')):
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
        rgba_str = f"rgba{rgb_str_split[3:]},0.3)"
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
    fig.update_layout(
        xaxis_title='Armor Class',
        yaxis_title='Damage',
        title='Damage vs Armor Class',
        template=template
    )
    return fig