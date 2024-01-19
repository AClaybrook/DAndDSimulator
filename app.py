# %%
""" Main app file for D&D Damage Simulator """
# Imports
from dataclasses import replace
import json
import os
from dash import dcc, html, Dash
import dash_bootstrap_components as dbc
# Gunicorn is used by heroku to run the app
import gunicorn  # pylint: disable=unused-import
from computations.models import Character, Enemy, Attack
from computations.numerical_simulation import simulate_character_rounds
from components.plots import generate_plot_data, add_tables
from components.callbacks import register_callbacks
from components.sidebar import sidebar
from components.character_card import generate_character_cards
from components.enemy_card import generate_enemy_card

# %%
# Example

# Build attacks
attacksPython = [Attack(name=f"Greatsword{ii+1}", two_handed=True, ability_stat="strength", damage='2d6', type='weapon (melee)') for ii in range(3)]

# Character stats
character1 = Character(name='Fighter',level=12, attacks=attacksPython, strength=20)
character2 = replace(character1, name='Fighter GWF + Crit On 19', disadvantage=False, GWF=True, crit_on=19)
character3 = replace(character1, name='Fighter Advantage', advantage=True)
character4 = replace(character1, name='Fighter GWM + Advantage', GWM=True, advantage=True)
enemy = Enemy(armor_class=18)

characters = [character1, character2, character3, character4]

dfs, df_by_rounds, df_by_attacks = simulate_character_rounds(characters, enemy,num_rounds=10_000, save_memory=True)

# %%
# Dashboard
# pylint: disable=invalid-name
style_sheet = dbc.themes.DARKLY
if style_sheet in [dbc.themes.CYBORG, dbc.themes.DARKLY]:
    template = 'plotly_dark'
else:
    template = 'plotly'

def wrap_elements(element_list, width=12, same_row=False):
    """ Wraps a list of elements in a row and column"""
    if same_row:
        rows = [dbc.Row([dbc.Col([element], width={"size": width}) for element in element_list])]
    else:
        rows = [dbc.Row([dbc.Col([element], width={"size": width})]) for element in element_list]
    return rows

def character_dropdown():
    """ Generates a dropdown menu for characters"""
    return dbc.DropdownMenu(
        id='character-dropdown',
        label="Character",
        children=[
            dbc.DropdownMenuItem(c.name) for ii, c in enumerate(characters)
        ]
    )

def simulate_rounds_input():
    """ Generates the simulator input section"""
    return dbc.Row([
        dbc.Row(dbc.Col(id="simulate-alerts")),
        dbc.Row([
            dbc.Col([
                dbc.Label('Number Of Rounds'),
                dbc.Input(type="number", value=10_000, min=1, max=100_000, step=1, style={'display': 'inline-block'},id="simulate-input"),
            ],width=2),
            dbc.Col([
                dbc.Label("Graph Type"),
                dbc.RadioItems(
                    options=[
                        {"label": "DPR Distribution", "value": "DPR Distribution",},
                        {"label": "DPR vs Armor Class", "value": "DPR vs Armor Class"},
                        {"label": "DPA Distribution", "value": "DPA Distribution",},
                        {"label": "DPA vs Armor Class", "value": "DPA vs Armor Class"},
                    ],
                    value="DPR Distribution",
                    id="simulate-type",
                    inline=True,
                    ),
            ],width=3),
            dbc.Col([
                dbc.Label("Numerical Options"),
                dbc.Checklist(
                    options=[
                        {"label": "Randomize Seed", "value": 1},
                    ],
                    value=[1],
                    id="numerical-options",
                    # inline=True,
                    switch=True,
                    ),
            ],width=2),
        ],justify="start"),
        dbc.Row(
            dbc.Col(
                dbc.Button(dbc.Spinner("Simulate!",color="primary",id='simulate-spinner'), color="primary",id="simulate-button",style={'width': '100%'}),
                width=2
            ),
        class_name="mb-2"),
    ])

app = Dash(__name__, external_stylesheets=[style_sheet, dbc.icons.FONT_AWESOME])
server = app.server

# Plot data
fig = generate_plot_data(characters, df_by_rounds, template=template, title="Damage Per Round Distribution")

row_style = style={'border': '1px solid #d3d3d3', 'borderRadius': '15px', 'padding': '10px', 'paddingRight': '0px'}

content = html.Div(dbc.Container([
    # Character Builder
    dbc.Row([
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
            ])
        ,width=2,class_name="mb-2"),
        dbc.Row(id="character-alerts"),
        dbc.Row(generate_character_cards(characters),id="character_row"),
        dcc.Store(id='active_ids', data=json.dumps(list(range(len(characters))))), # Used to keep track of character ids, since character can be added, copied and deleted
        dcc.Store(id='delete-timestamp', data=None), # Used to keep track of last deleted character, since copying a character triggers a delete
        dcc.Store(id='all_attacks', data=json.dumps({})), # Used to keep track of copied character counts, since this gets triggered without button clicks

    ],style=row_style, class_name="mb-4"),
    dbc.Row([
        html.H3("Enemy Builder", id='enemy-builder'),
        dbc.Row(generate_enemy_card(enemy),id="enemy_row"),
        ],style=row_style, class_name="mb-4"),
    # Simulator
    dbc.Row([
        dbc.Row([
            dbc.Col(html.H3("Simulator",id='simulator'), width=9),
            dbc.Col([
                dbc.InputGroup([
                    dbc.Select(
                        options=[
                            {"label": "DPR Summary", "value": "DPR Summary"},
                            {"label": "DPR Distribution", "value": "DPR Distribution",},
                            {"label": "DPR vs Armor Class", "value": "DPR vs Armor Class"},
                            {"label": "DPA Summary", "value": "DPA Summary"},
                            {"label": "DPA Distribution", "value": "DPA Distribution",},
                            {"label": "DPA vs Armor Class", "value": "DPA vs Armor Class"},
                            ],
                        value='DPR Summary', id='export-type'),
                    dbc.Button(dbc.Spinner(html.I(className="fa-solid fa-download"),color="secondary", id="export-spinner", size="sm"),color="secondary", id="export-results-button"),
                    dcc.Download(id="export-results"),
                ]),
            ], class_name="pr-0", width=3, style={'textAlign': 'right'}),
        ],class_name="justify-content-between  pr-0"),
        simulate_rounds_input(),
        dbc.Row([
                dcc.Graph(
                    id='dist-plot',
                    figure=fig,
                    style={'height': '85vh', 'marginBottom': '2px'}
                ),
        ]),
        dbc.Row(
            html.Div(id="damage-tables",children=[
                *add_tables(df_by_rounds,characters,by_round=True, width=3)
            ]),
        ),

        ],style=row_style),
    ],fluid=True),id="page-content")

app.layout = html.Div([dcc.Location(id="url"), sidebar, content])

#%%

register_callbacks(app)

if __name__ == '__main__':
    # Get the port number from the environment variable, or set to 8050 if not available
    port = int(os.environ.get("PORT", 8050))
    print('STARTING App')
    app.run_server(debug=True, host="0.0.0.0", port=port)
    print("TERMINATING App")

# %%
