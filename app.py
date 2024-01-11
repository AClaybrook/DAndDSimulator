# %%
""" Main app file for D&D Damage Simulator """
# Imports
from dataclasses import replace
import json
import os
from dash import dcc, html, Dash
import dash_bootstrap_components as dbc
import gunicorn # Used by heroku to run the app
import numpy as np
from models import Character, Enemy, Attack
from numerical_simulation import simulate_character_rounds, simulate_character_rounds_for_multiple_armor_classes
from plots import generate_plot_data, add_tables, generate_line_plots
from callbacks import register_callbacks
from components.sidebar import sidebar
from components.character_card import generate_character_cards
from components.enemy_card import generate_enemy_card

# %%
# Example

# Build attacks
attacksPython = [Attack(name="Greatsword", two_handed=True, ability_stat="strength", damage='2d6', type='weapon (melee)')]*3

# Character stats
character1 = Character(name='Fighter',level=12, attacks=attacksPython, strength=20)

character2 = replace(character1, name='Fighter GWF + Crit On 19', disadvantage=False, GWF=True, crit_on=19)
character3 = replace(character1, name='Fighter Advantage', advantage=True)
character4 = replace(character1, name='Fighter GWM', GWM=True)
enemy1 = Enemy(armor_class=18)

characters = [character1, character2]

dfs, df_by_rounds, df_by_attacks = simulate_character_rounds(characters, enemy1,num_rounds=10_000)

# %%
# Dashboard
style_sheet = dbc.themes.DARKLY
if style_sheet in [dbc.themes.CYBORG, dbc.themes.DARKLY]:
    template = 'plotly_dark'
else:
    template = 'plotly'

def wrap_elements(element_list, width=12, same_row=False):
    if same_row:
        rows = [dbc.Row([dbc.Col([element], width={"size": width}) for element in element_list])]
    else:
        rows = [dbc.Row([dbc.Col([element], width={"size": width})]) for element in element_list]
    return rows

def character_dropdown():
    return dbc.DropdownMenu(
        id='character-dropdown',
        label="Character",
        children=[
            dbc.DropdownMenuItem(c.name) for ii, c in enumerate(characters)
        ]
    )

def simulate_rounds_input():
    return html.Div([
        dbc.Row(id="simulate-alerts"),
        dbc.Row(dbc.Label('Number Of Rounds')),
        dbc.Row([
            dbc.Col([
                dbc.InputGroup([
                    dbc.Input(type="number", value=10_000, min=1, max=50_000, step=1, style={'display': 'inline-block'},id="simulate-input"),
                    dbc.Button(dbc.Spinner("Simulate!",color="primary",id='simulate-spinner'), color="primary",style={'display': 'inline-block'},id="simulate-button"),
                ]),
            ],width=2),
            dbc.Col([
                dbc.RadioItems(
                    options=[
                        {"label": "Damage Per Round Distribution", "value": 1},
                        {"label": "Damage Per Round vs Armor Class", "value": 2},
                    ],
                    value=1,
                    id="simulate-type",
                    inline=True,
                    ),
            ]),
        ],class_name="mb-2"),
    ])

app = Dash(__name__, external_stylesheets=[style_sheet, dbc.icons.FONT_AWESOME])
server = app.server
# app.config.suppress_callback_exceptions = True

# Plot data
fig = generate_plot_data(characters, df_by_rounds, template=template)


row_style = style={'border': '1px solid #d3d3d3', 'border-radius': '15px', 'padding': '10px', 'padding-right': '0px'}
# CONTENT_STYLE = {
#     "top":0,
#     "margin-top":'2rem',
#     "margin-left": "18rem",
#     "margin-right": "2rem",
# }
content = html.Div(dbc.Container([
    # Navbar
    # dbc.NavbarSimple(children=[
    #     dbc.NavItem(dbc.NavLink("Character Builder", href="#character-builder",external_link=True)),
    #     dbc.NavItem(dbc.NavLink("Simulator", href="#simulator",external_link=True)),
    # ], brand="D&D Damage Simulator", brand_href="#", class_name="mb-4",sticky='top'),
    # Character Builder
    dbc.Row([
        # dbc.Col([html.H3("Character Builder",className="me-3",style={'display': 'inline-block'}, id='character-builder'),
        #         dbc.Button(html.I(className="fa-solid fa-plus"),class_name="mb-3", color="primary",style={'display': 'inline-block'}),
        #             ]),

        dbc.Row([
            dbc.Col(html.H3("Character Builder", id='character-builder'), width=10),
            dbc.Col([
                dbc.InputGroup([
                dbc.Button(html.I(className="fa-solid fa-download"),color="secondary", id="export-button"),
                dcc.Download(id="download-characters"),
                dcc.Upload(dbc.Button(html.I(className="fa-solid fa-upload"),color="info", id="import-button"), id='upload-button', multiple=False),
            ], class_name="justify-content-end"),
            ], class_name=" pr-0", width=2),
        ],class_name="justify-content-between  pr-0"),
        
        dbc.Col(
            dbc.InputGroup([
                dbc.Input(type="text", placeholder="Character Name", style={'display': 'inline-block'},id="character_name"),
                dbc.Button(html.I(className="fa-solid fa-plus"), color="primary",style={'display': 'inline-block'},id="add_character_button"),
                # dcc.Upload(html.Button(html.I(className="fa-solid fa-upload"),id="import-button"), id='upload-button', multiple=False),
                # dcc.Upload(children=html.Div("Click here"), id='upload-button', multiple=False)
            ])
        ,width=2,class_name="mb-2"),
        html.Div(id="character-alerts"),
        # dbc.Col([
        #     dbc.Input(type="text", placeholder="Character Name", style={'display': 'inline-block'},),
        #     dbc.Button(html.I(className="fa-solid fa-plus"),class_name="mb-3", color="primary",style={'display': 'inline-block'})
        # ],width=2),
        dbc.Row(generate_character_cards(characters),id="character_row"),
        dcc.Store(id='active_ids', data=json.dumps(list(range(len(characters))))), # Used to keep track of character ids, since character can be added, copied and deleted
        dcc.Store(id='delete-timestamp', data=None), # Used to keep track of last deleted character, since copying a character triggers a delete
        dcc.Store(id='all_attacks', data=json.dumps({})), # Used to keep track of copied character counts, since this gets triggered without button clicks

    ],style=row_style, class_name="mb-4"),
    dbc.Row([
        html.H3("Enemy Builder", id='enemy-builder'),
        dbc.Row(generate_enemy_card(enemy1),id="enemy_row"),
        ],style=row_style, class_name="mb-4"),
    # Simulator
    dbc.Row([
        dbc.Row([
            dbc.Col(html.H3("Simulator",id='simulator'), width=9),
            dbc.Col([
                dbc.InputGroup([
                    dbc.Select(
                        options=[
                            {'label': 'Round Summary', 'value': 'Round Summary'},
                            {'label': 'All Rounds', 'value': 'All Rounds'},
                            {'label': 'Attack Summary', 'value': 'Attack Summary'},
                            {'label': 'All Attacks', 'value': 'All Attacks'}
                            ],
                        value='Round Summary', id='export-type'),
                    dbc.Button(dbc.Spinner(html.I(className="fa-solid fa-download"),color="secondary", id="export-spinner", size="sm"),color="secondary", id="export-results-button"),
                    dcc.Download(id="export-results"),
                ]),
            ], class_name="pr-0", width=3, style={'text-align': 'right'}),
        ],class_name="justify-content-between  pr-0"),
        simulate_rounds_input(),
        # dcc.Store(id='results-store', data=data_to_store(characters, df_by_rounds)),
        dbc.Row([
                dcc.Graph(
                    id='dist-plot',
                    figure=fig,
                    style={'height': '85vh', 'margin-bottom': '2px'}
                ),
        ]),
        html.Div(id="per-round-tables",children=[
            *add_tables(df_by_rounds,characters,by_round=True, width=3)
        ]),
        html.Div(id="per-attack-tables",children=[
            *add_tables(df_by_attacks,characters,by_round=False, width=3),
        ]),
        ],style=row_style),
    ],fluid=True),id="page-content")

app.layout = html.Div([dcc.Location(id="url"), sidebar, content])

#%%

register_callbacks(app)
if __name__ == '__main__':
# Get the port number from the environment variable, or set to 8050 if not available
    port = int(os.environ.get("PORT", 8050))
    app.run_server(debug=False, host="0.0.0.0", port=port)

# app.run_server(debug=True)
print("Starting app")

# %%
