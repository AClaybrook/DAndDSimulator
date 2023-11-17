# %%
# Imports
import pandas as pd
import numpy as np
from IPython.display import display
from dash import dcc, html, Input, Output, State, MATCH, ALL, Patch, Dash
import dash_bootstrap_components as dbc
from dash import html
import pandas as pd
from dataclasses import replace, asdict
from models import Character, Enemy, AttackContext, DamageContext, Attack
from numerical_simulation import simulate_character_rounds
from plots import generate_histogram, COLORS
from callbacks import register_callbacks
from components.sidebar import sidebar
from components.character_card import generate_character_cards


# %%
# Example

# Build attacks
attacksPython = [Attack(name="Greatsword", two_handed=True, ability_stat="strength", damage='2d6', type='weapon (melee)')]*3

# Character stats
character1 = Character(name='Fighter',level=12, attacks=attacksPython, strength=20)

character2 = replace(character1, name='Fighter GWF + Crit On 19', dis=False, GWF=True, crit_on=19)
character3 = replace(character1, name='Fighter Advantage', adv=True)
character4 = replace(character1, name='Fighter GWM', GWM=True)
enemy1 = Enemy(armor_class=18)

characters = [character1, character2]

dfs, df_by_rounds = simulate_character_rounds(characters, enemy1,num_rounds=100_000)

# %%
# Dashboard
style_sheet = dbc.themes.DARKLY
if style_sheet in [dbc.themes.CYBORG, dbc.themes.DARKLY]:
    template = 'plotly_dark'
else:
    template = 'plotly'


def add_tables(by_round=True, width=12):
    if by_round:
        table_list = [dbc.Row(dbc.Col(html.H4("Per Round")))]
        data = df_by_rounds
    else:
        table_list = [dbc.Row(dbc.Col(html.H4("Per Attack")))]
        data = dfs
    
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

app = Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[style_sheet, dbc.icons.FONT_AWESOME])
app.config.suppress_callback_exceptions = True

# Plot data
data = pd.concat([pd.DataFrame({'damage': df_by_round["Damage"], 'Type': c.name}) for c, df_by_round in zip(characters,df_by_rounds)])
fig = generate_histogram(data, x="damage", color="Type", marginal='box', template=template)


row_style = style={'border': '1px solid #d3d3d3', 'border-radius': '15px', 'padding': '10px'}
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

        html.H3("Character Builder", id='character-builder'),
        dbc.Col(
            dbc.InputGroup([
                dbc.Input(type="text", placeholder="Character Name", style={'display': 'inline-block'},id="character_name"),
                dbc.Button(html.I(className="fa-solid fa-plus"), color="primary",style={'display': 'inline-block'},id="add_character_button")
            ])
        ,width=2,class_name="mb-3"),

        # dbc.Col([
        #     dbc.Input(type="text", placeholder="Character Name", style={'display': 'inline-block'},),
        #     dbc.Button(html.I(className="fa-solid fa-plus"),class_name="mb-3", color="primary",style={'display': 'inline-block'})
        # ],width=2),
        dbc.Row(generate_character_cards(characters),id="character_row"),
        

    ],style=row_style, class_name="mb-4"),
    # Simulator
    dbc.Row([
        html.H3("Simulator",id='simulator'),
        dbc.Row([
            dbc.Col([simulate_rounds_input()], width={"size": 2}),
        ]),
        dbc.Row([
            dcc.Graph(
                id='dist-plot',
                figure=fig,
                style={'height': '85vh'}
            ),
        ]),
        *add_tables(width=3),
        *add_tables(by_round=False, width=3),
        ],style=row_style),
    ],fluid=True),id="page-content")

app.layout = html.Div([dcc.Location(id="url"), sidebar, content])



# Callbacks
# @app.callback(
#     Output(),
#     Input()
# )
# def update_attack_card(type):

#     if type in ["weapon (melee)","weapon (ranged)"]:
        
#     pass

# @app.callback(
#     Output({"type": "attacks", "index": MATCH}, "children",allow_duplicate=True),
#     Input({"type": "add-attack", "index": MATCH}, "n_clicks"),
#     prevent_initial_call=True
# )
# def add_attack_card(n_clicks):

#     def new_attack_card(n_clicks):
#         label_style = {'margin-bottom': '0.2rem'}
#         input_style = {'padding-top': '0.0rem', 'padding-bottom': '0.0rem'}
#         return dbc.Card([
#         dbc.CardHeader(dbc.Row([
#             dbc.Col(html.H4("Attack Name")),
#             dbc.Col([
#                 dbc.Button(html.I(className="fa-solid fa-copy"), color="primary",class_name="me-1", id={"type": "copy-attack", "index": n_clicks}),
#                 dbc.Button(html.I(className="fa-solid fa-x"), color="danger", id={"type": "remove-attack", "index": n_clicks})
#                 ], style={"text-align": "right"})
#         ])), 
#         dbc.CardBody([
#             dbc.Row([dbc.Col(dbc.Label("Attack Name", style=label_style)),dbc.Col(dbc.Input(type="text", value="Attack Name", style=input_style))]),
#             dbc.Row([
#                 dbc.Col(dbc.Label("Type", style=label_style)),
#                 dbc.Col(dbc.Select(options=[{"label": "Weapon (Melee)","value": "weapon (melee)"},
#                                         {"label":"Weapon (Ranged)", "value": "weapon (ranged)"},
#                                         {"label":"Spell", "value": "spell"},
#                                         {"label": "Unarmed", "value": "unarmed"},
#                                         {"label": "Thrown", "value": "thrown"}
#                                         ],
#                                         value='weapon (melee)', style=input_style))
#                                         ]),
#             dbc.Row([
#             dbc.Col(dbc.Label("Attacking Stat", style=label_style)),
#             dbc.Col(dbc.Select(options=stat_options,value='strength', style=input_style))
#             ]),
#             # Repeated Attacks
#             dbc.Row([
#                 dbc.Col(dbc.Label("Num Attacks", style=label_style)),
#                 dbc.Col(dbc.Input(type="number", value=1, min=1, max=50, step=1, style=input_style))
#             ]),
#             # Weapon specific
#             dbc.Row([
#                 dbc.Col(dbc.Label("Weapon Damage", style=label_style)),
#                 dbc.Col(dbc.Input(type="string", value='1d6', style=input_style))
#             ]),
#             dbc.Row([
#                 dbc.Col(dbc.Label("Weapon Enhancement", style=label_style)),
#                 dbc.Col(dbc.Input(type="number", value=0, min=0, max=10, step=1, style=input_style))
#             ]),
#             dbc.Row([
#                 dbc.Col(dbc.Label("Offhand", style=label_style)),
#                 dbc.Col(dbc.Checkbox(value=False))
#             ]),
#             dbc.Row([
#                 dbc.Col(dbc.Label("Twohanded", style=label_style)),
#                 dbc.Col(dbc.Checkbox(value=False))
#             ]),
#             # Spell specific
#             dbc.Row([
#                 dbc.Col(dbc.Label("Spell Damage", style=label_style)),
#                 dbc.Col(dbc.Input(type="string", value='1d6', style=input_style))
#             ]),
#             dbc.Row([
#                 dbc.Col(dbc.Label("Saving Throw", style=label_style)),
#                 dbc.Col(dbc.Checkbox(value=False))
#             ]),
#             dbc.Row([
#                 dbc.Col(dbc.Label("Saving Throw Stat", style=label_style)),
#                 dbc.Col(dbc.Select(options=stat_options,value='dexterity', style=input_style))
#             ]),
#             dbc.Row([
#                 dbc.Col(dbc.Label("Failed Saving Throw Multiplier", style=label_style)),
#                 dbc.Col(dbc.Input(type="number", value=0.5, min=0, max=1, step=0.5, style=input_style))
#             ]),
#             # Additional
#             dbc.Row([
#                 dbc.Col(dbc.Label("Bonus Attack Mod", style=label_style)),
#                 dbc.Col(dbc.Input(type="string", value="0d4,0", style=input_style))
#             ]),
#             dbc.Row([
#                 dbc.Col(dbc.Label("Bonus Damage Mod", style=label_style)),
#                 dbc.Col(dbc.Input(type="string", value="0d4,0", style=input_style))
#             ]),
#             dbc.Row([
#                 dbc.Col(dbc.Label("Bonus Crit Damage", style=label_style)),
#                 dbc.Col(dbc.Input(type="string", value="0d4,0", style=input_style))
#             ]),
#         ])
#     ])

#     attacks_list = Patch()
#     attacks_list.append(new_attack_card(n_clicks))
#     return attacks_list


# @app.callback(
#     Output({"type": "attacks", "index": MATCH}, "children",allow_duplicate=True),
#     Input({"type": "remove-attack", "index": MATCH}, "n_clicks"),
#     prevent_initial_call=True
# )
# def delete_attack_card(n_clicks):
#     print(n_clicks)
#     attacks_list = Patch()
#     del attacks_list[n_clicks]
#     return attacks_list

#%%

register_callbacks(app)
app.run_server(debug=True)
print("Starting app")



# %%
