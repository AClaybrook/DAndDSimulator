# Plotting
# Themes here: https://plotly.com/python/templates/
import plotly.express as px

# Color Palette
COLORS = px.colors.qualitative.Plotly

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
