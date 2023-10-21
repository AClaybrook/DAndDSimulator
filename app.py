# %%
# Imports
import pandas as pd
import numpy as np
from IPython.display import display
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash import html
import pandas as pd
from dataclasses import replace, asdict
from models import Character, Enemy, AttackContext, DamageContext
from numerical_simulation import simulate_character_rounds
from plots import generate_histogram, COLORS


# %%
# Example

# Character stats
character1 = Character(
    name='Fighter',
    proficiency_bonus=4, # Level 9-12
    ability_modifier=5, # 20-21
    num_attacks=3,
    weapon_die='2d6',
    )
character2 = replace(character1, name='Fighter GWF + Crit on 19', dis=False, GWF=True, crit_on=19)
character3 = replace(character1, name='Fighter Advantage', adv=True)
character4 = replace(character1, name='Fighter GWM', GWM=True)
enemy1 = Enemy(armor_class=18)

characters = [character1, character2, character3, character4]

dfs, df_by_rounds = simulate_character_rounds(characters, enemy1)

# %%
# Dashboard
style_sheet = dbc.themes.CYBORG
if style_sheet in [dbc.themes.CYBORG, dbc.themes.DARKLY]:
    template = 'plotly_dark'
else:
    template = 'plotly'

def generate_characted_cards(characters):
    cards = dbc.Row([
        dbc.Col(generate_character_card(c, COLORS[ii]), width={"size": 12/len(characters)})
        for ii, c in enumerate(characters)
        ])
    return cards

def generate_character_card(character, color):
    input_style = {'padding': '1px'}
    return dbc.Card([
        dbc.CardHeader(html.H4(character.name,style={'color': color})), 
        dbc.CardBody([
            dbc.Row([
                dbc.Col(dbc.Label("Num Attacks")),
                dbc.Col(dbc.Input(type="number", value=character.num_attacks, min=1, max=100, step=1, style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Ability Modifier")),
                dbc.Col(dbc.Input(type="number", value=character.ability_modifier, min=-10, max=10, step=1, style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Weapon Modifier")),
                dbc.Col(dbc.Input(type="number", value=character.weapon_modifier, min=0, max=10, step=1, style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Proficiency Bonus")),
                dbc.Col(dbc.Input(type="number", value=character.proficiency_bonus, min=0, max=10, step=1, style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Additional Attack Modifier")),
                dbc.Col(dbc.Input(type="number", value=character.additional_attack_modifier, min=0, max=50, step=1, style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Attack Reroll On")),
                dbc.Col(dbc.Input(type="number", value=character.attack_reroll_on if character.attack_reroll_on is not None else 0, min=0, max=19, step=1, style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Crit On")),
                dbc.Col(dbc.Input(type="number", value=character.crit_on, min=2, max=20, step=1, style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Weapon Die (format: '1d6')")),
                dbc.Col(dbc.Input(type="text", value=character.weapon_die, style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Additional Damage Modifier")),
                dbc.Col(dbc.Input(type="number", value=character.additional_damage_modifier, min=0, max=50, step=1, style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Advantage")),
                dbc.Col(dbc.Checkbox(value=character.adv))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Disadvantage")),
                dbc.Col(dbc.Checkbox(value=character.dis))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Great Weapon Master")),
                dbc.Col(dbc.Checkbox(value=character.GWM))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Great Weapon Fighting")),
                dbc.Col(dbc.Checkbox(value=character.GWF))
            ])
        ]),
    ])




def add_tables(by_round=True, width=12):
    if by_round:
        table_list = [dbc.Row(dbc.Col(html.H2("Per Round")))]
        data = df_by_rounds
    else:
        table_list = [dbc.Row(dbc.Col(html.H2("Per Attack")))]
        data = dfs
    row = []
    
    for ii, (c, datac) in enumerate(zip(characters, data)):
        if not by_round:
            datac = datac.drop("round", axis=1)
        df_table = datac.describe().drop("count",axis=0).reset_index().round(3)
        col = []  
        col.append(html.H4(c.name, style={'color': COLORS[ii]})) 
        col.append(dbc.Table.from_dataframe(df_table, striped=True, bordered=True, hover=True, responsive=True))
        col.append(html.Br())
        row.append(dbc.Col(col, width={"size": width}))
    table_list.append(dbc.Row(row))
    return table_list

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
            dbc.Label('Number Of Rounds'),
            dbc.Input(
                id='simulate-rounds-input',
                type='number',
                value=100000,
                min=1,
                max=10000000,
                step=50000,
                )
    ])

app = dash.Dash(__name__, external_stylesheets=[style_sheet])

# Plot data
data = pd.concat([pd.DataFrame({'damage': df_by_round["damage"], 'Type': c.name}) for c, df_by_round in zip(characters,df_by_rounds)])
fig = generate_histogram(data, x="damage", color="Type", marginal='box', template=template)

app.layout = dbc.Container([
    dbc.Row(dbc.Col(html.H1("D&D Damage Simulator"))),
    dbc.Row([dbc.Col([character_dropdown()],width={"size": 10}),dbc.Col([simulate_rounds_input()], width={"size": 2})]),
    dbc.Row(generate_characted_cards(characters)),
    dbc.Row([
        dbc.Col([
            dcc.Graph(
                id='dist-plot',
                figure=fig,
                style={'height': '60vh'}
            ),
        ],
        ),
    ]),
    *add_tables(width=12/len(characters)),
    *add_tables(by_round=False, width=12/len(characters)),

],
    fluid=True)

app.run_server(debug=False)


# %%
