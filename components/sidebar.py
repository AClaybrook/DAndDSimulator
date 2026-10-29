""" The sidebar component for the dashboard """
import dash_bootstrap_components as dbc
from dash import html

# we use the Row and Col components to construct the sidebar header
# it consists of a title, and a toggle, the latter is hidden on large screens
sidebar_header = dbc.Row(
    [
        dbc.Col(html.H2(["D&D Damage", html.Br(), "Simulator"], style={"textAlign": "left", "fontSize": "1.2rem", "marginBottom": 0}), width=9),
        dbc.Col(
            [
                html.Button(
                    html.Span(className="navbar-toggler-icon"),
                    className="navbar-toggler",
                    # TODO: Update color of navbar toggler to match theme, currently hardcoded in css. Need dynamically readjust the stroke color of the icon somehow
                    id="navbar-toggle",
                ),
                html.Button(
                    html.Span(className="navbar-toggler-icon"),
                    className="navbar-toggler",
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
                    "For the D&D and Baldur's Gate 3 theorycrafters of the world.",
                    className="small text-muted",
                ),
            ],
            id="blurb",
        ),
        # use the Collapse component to animate hiding / revealing links
        dbc.Collapse(
            dbc.Nav(
                [
                    dbc.NavLink("BG3 Party Planner", href="#bg3-planner",external_link=True,active="exact"),
                    dbc.NavLink("Character Builder", href="#character-builder",external_link=True,active="exact"),
                    dbc.NavLink("Enemy Builder", href="#enemy-builder",external_link=True,active="exact"),
                    dbc.NavLink("Simulator", href="#simulator",external_link=True,active="exact"),
                    dbc.NavLink("Damage Tables", href="#damage-tables",external_link=True,active="exact"),
                ],
                vertical=True,
                pills=True,
            ),
            id="collapse",
        ),
    ],
    id="sidebar",
)
