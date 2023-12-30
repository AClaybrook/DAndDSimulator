# Plotting
# Themes here: https://plotly.com/python/templates/
import plotly.express as px
import pandas as pd

from dash import html
import dash_bootstrap_components as dbc

# Color Palette
COLORS = px.colors.qualitative.Plotly

def generate_plot_data(characters, df_by_rounds, template='plotly_dark'):
    data = pd.concat([pd.DataFrame({'damage': df_by_round["Damage"], 'Type': c.name}) for c, df_by_round in zip(characters,df_by_rounds)])
    fig = generate_histogram(data, x="damage", color="Type", marginal='box', template=template)
    return data, fig

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

def add_tables(data, characters, by_round=True, width=12):
    if by_round:
        table_list = [dbc.Row(dbc.Col(html.H4("Per Round")))]
    else:
        table_list = [dbc.Row(dbc.Col(html.H4("Per Attack")))]
    
    row = []
    
    for ii, (c, datac) in enumerate(zip(characters, data)):
        if by_round:
            datac = datac.drop(["Attack Roll", "Attack Roll (Die)", "Hit (Non-Crit)", "Hit (Crit)"], axis=1)
            datac.rename(columns={"Hit": "Num Hits","Hit (Non-Crit)": "Num Hits (Non-Crit)","Hit (Crit)": "Num Hits (Crit)"}, inplace=True)
        else:
            datac = datac.drop("Round", axis=1)
        datac.rename(columns={"Hit": "Num Hits"}, inplace=True)
        df_table = datac.describe().drop(["count","std"],axis=0).reset_index().round(2)
        col = []  
        col.append(html.H4(c.name, style={'color': COLORS[ii]})) 
        col.append(dbc.Table.from_dataframe(df_table, striped=True, bordered=True, hover=True, responsive=True))
        col.append(html.Br())
        row.append(dbc.Col(col, width={"size": width}))
    table_list.append(dbc.Row(row))
    return table_list