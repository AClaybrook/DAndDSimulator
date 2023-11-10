# %%
import dash_bootstrap_components as dbc
from dash import html

# we use the Row and Col components to construct the sidebar header
# it consists of a title, and a toggle, the latter is hidden on large screens
sidebar_header = dbc.Row(
    [
        dbc.Col(html.H2("D & D Damage Simulator",style={"text-align":"left","font-size":"x-large","display":"inline"}),width=9,style={"display": "inline"}),
        dbc.Col(
            [
                html.Button(
                    # use the Bootstrap navbar-toggler classes to style
                    html.Span(className="navbar-toggler-icon"),
                    className="navbar-toggler",
                    # the navbar-toggler classes don't set color
                    # style={
                    #     "color": "rgba(0,0,0,.5)",
                    #     "border-color": "rgba(0,0,0,.1)",
                    # },
                    id="navbar-toggle",
                ),
                html.Button(
                    # use the Bootstrap navbar-toggler classes to style
                    html.Span(className="navbar-toggler-icon"),
                    className="navbar-toggler",
                    # the navbar-toggler classes don't set color
                    # style={
                    #     "color": "rgba(0,0,0,.5)",
                    #     "border-color": "rgba(0,0,0,.1)",
                    # },
                    id="sidebar-toggle",
                ),
            ],
            # the column containing the toggle will be only as wide as the
            # toggle, resulting in the toggle being right aligned
            width=3,
            # vertically align the toggle in the center
            align="center",
            style={"display": "inline"},
        ),
    ],style={"width":"100%"}
)

sidebar = html.Div(
    [
        sidebar_header,
        # we wrap the horizontal rule and short blurb in a div that can be
        # hidden on a small screen
        html.Div(
            [
                html.Hr(),
                html.P(
                    "For the D&D theorycrafters of the world.",
                    "links.",
                    className="lead",
                ),
            ],
            id="blurb",
        ),
        # use the Collapse component to animate hiding / revealing links
        dbc.Collapse(
            dbc.Nav(
                [
                    dbc.NavLink("Character Builder", href="#character-builder",external_link=True,active="exact"),
                    dbc.NavLink("Simulator", href="#simulator",external_link=True,active="exact"),
                ],
                vertical=True,
                pills=True,
            ),
            id="collapse",
        ),
    ],
    id="sidebar",
)
