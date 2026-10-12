# %%
""" Main app file for D&D Damage Simulator """
# Imports
from dataclasses import replace
import json
import os
from dash import dcc, html, Dash
import dash_bootstrap_components as dbc
from computations.models import Character, Attack
from computations.numerical_simulation import simulate_rounds_from_characters
from components.plots import generate_plot_data, add_tables, build_leaderboard, build_breakdown_tables, results_summary
from computations.analytic import attack_breakdown
from components.callbacks import register_callbacks
from components.sidebar import sidebar
from components.character_card import generate_character_cards
from components.enemy_card import generate_enemy_card
from game_data import RULESETS, enemy_from_monster
from game_data.classes import BUILDS
from components.sweeps import SWEEP_PARAMETERS
from components.help import GRAPH_DESCRIPTIONS, quick_start

# %%
# Example

# Build attacks
attacksPython = [Attack(name="Greatsword", two_handed=True, ability_stat="strength", damage='2d6', type='weapon (melee)') for ii in range(3)]

# Character stats
character1 = Character(name='Fighter',level=12, attacks=attacksPython, strength=20)
character2 = replace(character1, name='Fighter GWF + Crit On 19', disadvantage=False, GWF=True, crit_on=19)
character3 = replace(character1, name='Fighter Advantage', advantage=True)
character4 = replace(character1, name='Fighter GWM + Advantage', GWM=True, advantage=True)
enemy = enemy_from_monster("Mind Flayer")

characters = [character1, character2, character3, character4]

dfs, df_by_rounds, df_by_attacks = simulate_rounds_from_characters(characters, enemy,num_rounds=10_000, save_memory=True)

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

def preset_builder():
    """ Inputs to add a prebuilt character that levels up realistically """
    return dbc.InputGroup([
        dbc.InputGroupText("Preset"),
        dbc.Select(options=[{"label": b.label, "value": key} for key, b in BUILDS.items()], value="fighter_gwm", id="preset-build"),
        dbc.InputGroupText("Level"),
        dbc.Input(type="number", value=5, min=1, max=20, step=1, id="preset-level", style={'maxWidth': '5rem'}),
        dbc.Select(options=[{"label": r["label"], "value": key} for key, r in RULESETS.items()], value="bg3", id="ruleset", style={'maxWidth': '11rem'}),
        dbc.Button(html.I(className="fa-solid fa-plus"), color="primary", id="add-preset-button", title="Add preset character"),
    ], size="sm")

def simulate_rounds_input():
    """ Generates the simulator input section: what to simulate, settings and the simulate button """
    return dbc.Row([
        dbc.Row(dbc.Col(id="simulate-alerts")),
        dbc.Row([
            dbc.Col([
                dbc.Label("What do you want to know?", class_name="fw-bold"),
                dbc.RadioItems(
                    options=[{"label": graph, "value": graph} for graph in GRAPH_DESCRIPTIONS],
                    value="DPR Distribution",
                    id="simulate-type",
                    inline=True,
                    ),
                html.Div(GRAPH_DESCRIPTIONS["DPR Distribution"], id="graph-description", className="small text-info mt-1"),
                html.Div([
                    dbc.InputGroup([
                        dbc.InputGroupText("Sweep"),
                        dbc.Select(options=[{"label": p, "value": p} for p in SWEEP_PARAMETERS], value="Armor Class", id="sweep-parameter"),
                    ], size="sm", class_name="mt-2"),
                    dbc.FormText(id="sweep-description"),
                ], id="sweep-controls", style={"display": "none"}),
            ], xs=12, lg=7),
            dbc.Col([
                dbc.Label("Settings", class_name="fw-bold"),
                dbc.InputGroup([
                    dbc.InputGroupText("Rounds simulated"),
                    dbc.Input(type="number", value=10_000, min=1, max=1_000_000, step=1, id="simulate-input"),
                ], size="sm", class_name="mb-1"),
                dbc.InputGroup([
                    dbc.InputGroupText("Rounds per fight"),
                    dbc.Input(type="number", value=3, min=1, max=20, step=1, id="rounds-per-fight"),
                ], size="sm", class_name="mb-1"),
                dbc.FormText("Limited attacks, smites and first round effects are spread over fights of this many rounds"),
                dbc.Checklist(
                    options=[
                        {"label": "Randomize Seed", "value": 1},
                    ],
                    value=[1],
                    id="numerical-options",
                    switch=True,
                    class_name="mt-1",
                    ),
            ], xs=12, md=8, lg=3),
            dbc.Col(
                dbc.Button(dbc.Spinner("Simulate!", color="light", size="sm", id='simulate-spinner'), color="primary", size="lg", id="simulate-button", class_name="w-100"),
                xs=12, md=4, lg=2, class_name="d-flex align-items-center"),
        ], justify="start", class_name="g-3 mb-2"),
    ])

app = Dash(__name__, external_stylesheets=[style_sheet, dbc.icons.FONT_AWESOME], title="D&D Damage Simulator")
server = app.server

# Plot data
fig = generate_plot_data(characters, df_by_rounds, template=template, title="Damage Per Round Distribution")


content = html.Div(dbc.Container([
    quick_start(),
    # Character Builder
    html.Section([
        dbc.Row([
            dbc.Col(html.H3("Character Builder", id='character-builder', className="mb-0")),
            dbc.Col([
                dbc.InputGroup([
                    dbc.Button(html.I(className="fa-solid fa-download"), color="secondary", id="export-button", title="Export session (characters, enemy and settings) to json"),
                    dcc.Download(id="download-characters"),
                    dcc.Upload(dbc.Button(html.I(className="fa-solid fa-upload"), color="info", id="import-button", title="Import a session, or add characters from an older characters file"), id='upload-button', multiple=False),
                ], class_name="justify-content-end"),
            ], width="auto"),
        ], align="center", class_name="mb-2"),
        dbc.Row([
            dbc.Col(
                dbc.InputGroup([
                    dbc.Input(type="text", placeholder="New blank character name", id="character_name"),
                    dbc.Button(html.I(className="fa-solid fa-plus"), color="primary", id="add_character_button", title="Add blank character"),
                ], size="sm"),
            xs=12, md=4, xl=3, class_name="mb-2"),
            dbc.Col(preset_builder(), xs=12, md=8, xl=7, class_name="mb-2"),
        ]),
        # Offers to restore the session this browser saved on its last simulation, shown after a reload
        dbc.Alert([
            html.I(className="fa-solid fa-clock-rotate-left me-2"),
            html.Span(id="restore-text"),
            dbc.Button("Restore it", id="restore-session-button", color="success", size="sm", class_name="ms-2"),
        ], id="restore-banner", color="secondary", dismissable=True, is_open=False, class_name="py-2 mb-2 d-flex align-items-center"),
        dbc.Row(id="character-alerts"),
        dbc.Row(generate_character_cards(characters), id="character_row"),
        dcc.Store(id='active_ids', data=json.dumps(list(range(len(characters))))), # Used to keep track of character ids, since character can be added, copied and deleted
        dcc.Store(id='last-card-click', data=0), # Timestamp of the last handled copy/delete click, these callbacks also fire when cards are added or removed
    ], className="panel mb-4"),
    html.Section([
        html.H3("Enemy Builder", id='enemy-builder'),
        dbc.Row(generate_enemy_card(enemy), id="enemy_row"),
    ], className="panel mb-4"),
    # Simulator
    html.Section([
        dbc.Row([
            dbc.Col(html.H3("Simulator", id='simulator', className="mb-0")),
            dbc.Col([
                dbc.InputGroup([
                    dbc.Select(
                        options=[
                            {"label": "DPR Summary", "value": "DPR Summary"},
                            {"label": "DPR Distribution", "value": "DPR Distribution",},
                            {"label": "DPR Sweep", "value": "DPR Sweep"},
                            {"label": "DPA Summary", "value": "DPA Summary"},
                            {"label": "DPA Distribution", "value": "DPA Distribution",},
                            {"label": "DPA Sweep", "value": "DPA Sweep"},
                            {"label": "Rounds to Kill", "value": "Rounds to Kill"},
                            {"label": "Damage per Fight", "value": "Damage per Fight"},
                            ],
                        value='DPR Summary', id='export-type'),
                    dbc.Button(dbc.Spinner(html.I(className="fa-solid fa-download"), color="secondary", id="export-spinner", size="sm"), color="secondary", id="export-results-button", title="Export results to csv"),
                    dcc.Download(id="export-results"),
                ], size="sm"),
            ], width="auto"),
        ], align="center", class_name="mb-2"),
        simulate_rounds_input(),
        html.Div(results_summary({c.name: df["Damage"].mean() for c, df in zip(characters, df_by_rounds)}, "damage per round", context=f"against {enemy.name}."),
                 id="results-summary"),
        dbc.Row([
                dcc.Graph(
                    id='dist-plot',
                    figure=fig,
                    style={'height': '75vh', 'marginBottom': '2px'}
                ),
        ]),
        dbc.Row(
            html.Div(id="damage-tables", children=[
                *build_leaderboard(characters, df_by_rounds),
                *add_tables(df_by_rounds, characters, by_round=True, width=3),
                *build_breakdown_tables(characters, [attack_breakdown(c, enemy) for c in characters]),
            ]),
        ),
    ], className="panel"),
], fluid=True), id="page-content")

# Always reachable simulate button, results scroll into view when a simulation finishes
floating_simulate = dbc.Button([html.I(className="fa-solid fa-dice-d20 me-2"), "Simulate"], color="primary", id="simulate-float", class_name="shadow",
                               title="Simulate with the current settings")
stores = [
    dcc.Store(id="ui-prefs", storage_type="local"), # Per browser preferences, i.e. hiding the quick start
    dcc.Store(id="scroll-dummy"),
    dcc.Store(id="saved-session", storage_type="local"), # Last simulated session, offered for restore after a reload
]

app.layout = html.Div([dcc.Location(id="url"), sidebar, content, floating_simulate, *stores])

#%%

register_callbacks(app, template=template)

if __name__ == '__main__':
    # Get the port number from the environment variable, or set to 8050 if not available
    port = int(os.environ.get("PORT", 8050))
    print('STARTING App')
    app.run(debug=True, host="0.0.0.0", port=port)
    print("TERMINATING App")

# %%
