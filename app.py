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

dfs, df_by_rounds = simulate_character_rounds(characters, enemy1)

# %%
# Dashboard
style_sheet = dbc.themes.DARKLY
if style_sheet in [dbc.themes.CYBORG, dbc.themes.DARKLY]:
    template = 'plotly_dark'
else:
    template = 'plotly'




def generate_character_cards(characters):
    cards = dbc.Row([
        dbc.Col(generate_character_card(c, COLORS[ii]), width={"size": 3})
        for ii, c in enumerate(characters)
        ])
    return cards

                                  
# Stat options
stat_options=[{"label": "Strength", "value": "strength"},
                {"label":"Dexterity", "value": "dexterity"},
                {"label":"Constitution", "value": "constitution"},
                {"label":"Intelligence", "value": "intelligence"},
                {"label":"Wisdom", "value": "wisdom"},
                {"label":"Charisma", "value": "charisma"}]


def generate_character_card(character, color):
    input_style = {'padding-top': '0.0rem', 'padding-bottom': '0.0rem'}
    label_style = {'margin-bottom': '0.2rem'}
    card_style = {'max-height': '60vh','min-height': '60vh','overflow-y': 'auto'}
    tab_style = {}

    # Stats tab
    stats = dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col(dbc.Label("Name", style=label_style)),
                dbc.Col(dbc.Input(type="text", value="Character1", style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Level", style=label_style)),
                dbc.Col(dbc.Input(type="number", value=1, min=1, max=20, step=1, style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Strength", style=label_style)),
                dbc.Col(dbc.Input(type="number", value=10, min=1, max=30, step=1, style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Dexterity", style=label_style)),
                dbc.Col(dbc.Input(type="number", value=10, min=1, max=30, step=1, style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Constitution", style=label_style)),
                dbc.Col(dbc.Input(type="number", value=10, min=1, max=30, step=1, style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Intelligence", style=label_style)),
                dbc.Col(dbc.Input(type="number", value=10, min=1, max=30, step=1, style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Wisdom", style=label_style)),
                dbc.Col(dbc.Input(type="number", value=10, min=1, max=30, step=1, style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Charisma", style=label_style)),
                dbc.Col(dbc.Input(type="number", value=10, min=1, max=30, step=1, style=input_style))
            ]),
            dbc.Row([
                dbc.Textarea(placeholder="Optional Description",  style={'width': '100%','min-height': '10vh'}),
            ]),
        ])
    ],style=tab_style)

    # Attacks tab
    attacks = dbc.Card([
        dbc.CardBody([
            dbc.Row([
                    dbc.Col(dbc.Button(html.I(className="fa-solid fa-plus"), color="primary", id={"type": "add-attack", "index": character.name})), # TODO: Don't use character name as index, switch to n_clicks for character builder
            ]),
            # dbc.Row(children=[], id={"type": "attacks", "index": character.name}),
            dbc.Row([dbc.Col(dbc.Label("Attack Name", style=label_style)),dbc.Col(dbc.Input(type="text", value="Attack Name", style=input_style))]),
            dbc.Row([
                dbc.Col(dbc.Label("Type", style=label_style)),
                dbc.Col(dbc.Select(options=[{"label": "Weapon (Melee)","value": "weapon (melee)"},
                                        {"label":"Weapon (Ranged)", "value": "weapon (ranged)"},
                                        {"label":"Spell", "value": "spell"},
                                        {"label": "Unarmed", "value": "unarmed"},
                                        {"label": "Thrown", "value": "thrown"}
                                        ],
                                        value='weapon (melee)', style=input_style))
                                        ]),
            dbc.Row([
            dbc.Col(dbc.Label("Attacking Stat", style=label_style)),
            dbc.Col(dbc.Select(options=stat_options,value='strength', style=input_style))
            ]),
            # Repeated Attacks
            dbc.Row([
                dbc.Col(dbc.Label("Num Attacks", style=label_style)),
                dbc.Col(dbc.Input(type="number", value=1, min=1, max=50, step=1, style=input_style))
            ]),
            # Weapon specific
            dbc.Row([
                dbc.Col(dbc.Label("Weapon Damage", style=label_style)),
                dbc.Col(dbc.Input(type="string", value='1d6', style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Weapon Enhancement", style=label_style)),
                dbc.Col(dbc.Input(type="number", value=0, min=0, max=10, step=1, style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Offhand", style=label_style)),
                dbc.Col(dbc.Checkbox(value=False))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Twohanded", style=label_style)),
                dbc.Col(dbc.Checkbox(value=False))
            ]),
            # Spell specific
            dbc.Row([
                dbc.Col(dbc.Label("Spell Damage", style=label_style)),
                dbc.Col(dbc.Input(type="string", value='1d6', style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Saving Throw", style=label_style)),
                dbc.Col(dbc.Checkbox(value=False))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Saving Throw Stat", style=label_style)),
                dbc.Col(dbc.Select(options=stat_options,value='dexterity', style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Failed Saving Throw Multiplier", style=label_style)),
                dbc.Col(dbc.Input(type="number", value=0.5, min=0, max=1, step=0.5, style=input_style))
            ]),
            # Additional
            dbc.Row([
                dbc.Col(dbc.Label("Bonus Attack Mod", style=label_style)),
                dbc.Col(dbc.Input(type="string", value="0d4,0", style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Bonus Damage Mod", style=label_style)),
                dbc.Col(dbc.Input(type="string", value="0d4,0", style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Bonus Crit Damage", style=label_style)),
                dbc.Col(dbc.Input(type="string", value="0d4,0", style=input_style))
            ]),
            dbc.Row(html.H6("Attacks")),
            dbc.Row(dbc.ListGroup(children=[], id={"type": "attacks", "index": character.name})),
            
        ])
    ])

    # Bonuses, Feats and abilities tab
    bonuses = dbc.Card([
        dbc.CardBody([
            dbc.Row([
                html.H6("Bonus Unaccounted for Modifiers"),
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Crit on", style=label_style)),
                dbc.Col(dbc.Input(type="number", value=20, min=2, max=20, step=1, style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Advantage", style=label_style)),
                dbc.Col(dbc.Checkbox(value=False))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Disadvantage", style=label_style)),
                dbc.Col(dbc.Checkbox(value=False))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Bonus attack modifiers", style=label_style)),
                dbc.Col(dbc.Input(type="string", value="0d4,0", style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Bonus damage modifiers", style=label_style)),
                dbc.Col(dbc.Input(type="string", value="0d4,0", style=input_style))
            ]),
            dbc.Row([
                html.H6("Feats"),
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Great Weapon Master", style=label_style)),
                dbc.Col(dbc.Checkbox(value=False))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Savage Attacker", style=label_style)),
                dbc.Col(dbc.Checkbox(value=False))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Sharpshooter", style=label_style)),
                dbc.Col(dbc.Checkbox(value=False))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Tavern Brawler", style=label_style)),
                dbc.Col(dbc.Checkbox(value=False))
            ]),
            dbc.Row([
                html.H6("Fighting Styles"),
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Great Weapon Fighting", style=label_style)),
                dbc.Col(dbc.Checkbox(value=False))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Archery", style=label_style)),
                dbc.Col(dbc.Checkbox(value=False))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Dueling", style=label_style)),
                dbc.Col(dbc.Checkbox(value=False))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Two Weapon Fighting", style=label_style)),
                dbc.Col(dbc.Checkbox(value=False))
            ]),
            dbc.Row([
                html.H6("Barbarian"),
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Raging", style=label_style)),
                dbc.Col(dbc.Checkbox(value=False))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Brutal Critical", style=label_style)),
                dbc.Col(dbc.Checkbox(value=False))
            ]),
            dbc.Row([
                html.H6("Paladin"),
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Divine Smite", style=label_style)),
                dbc.Col(dbc.Checkbox(value=False))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Divine Smite Level", style=label_style)),
                dbc.Col(dbc.Input(type="number", value=1, min=1, max=4, step=1, style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Improved Divine Smite", style=label_style)),
                dbc.Col(dbc.Checkbox(value=False))
            ]),
            dbc.Row([
                html.H6("Wizard"),
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Empowered Evocation", style=label_style)),
                dbc.Col(dbc.Checkbox(value=False))
            ]),
            dbc.Row([
                html.H6("Warlock"),
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Agonizing Blast", style=label_style)),
                dbc.Col(dbc.Checkbox(value=False))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Life Drinker", style=label_style)),
                dbc.Col(dbc.Checkbox(value=False))
            ]),
            dbc.Row([
                html.H6("Sorcerer"),
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Elemental Affinity", style=label_style)),
                dbc.Col(dbc.Checkbox(value=False))
            ]),
            dbc.Row([
                html.H6("Racial Bonuses"),
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Half Orc Savage Attacks", style=label_style)),
                dbc.Col(dbc.Checkbox(value=False))
            ]),
        ])
    ],style=tab_style)

    # Calcs tab
    # calcs = dbc.Card([
    #     dbc.CardBody([
    #         dbc.Row([
    #             dbc.Col(dbc.Label("Attack Modifier", style=label_style)),
    #             dbc.Col(dbc.Input(type="number", value=character.attack_modifier('strength'), readonly=True, style=input_style))
    #         ]),
    #         dbc.Row([
    #             dbc.Col(dbc.Label("Damage Modifier", style=label_style)),
    #             dbc.Col(dbc.Input(type="number", value=character.damage_modifier('strength'), readonly=True, style=input_style))
    #         ]),
    #     ])

    # ],style=tab_style)

    return dbc.Card([

        dbc.CardHeader(dbc.Row([
            dbc.Col(html.H4(character.name,style={'color': color, 'white-space':'nowrap'}),style={'overflow-x': 'auto'}, width={"size":9}),
            dbc.Col([dbc.Button(html.I(className="fa-solid fa-copy"), color="primary",class_name="me-1",style={"display":"flex"}),
                     dbc.Button(html.I(className="fa-solid fa-x"), color="danger",class_name="me-1",style={"display":"flex"}),
                     ], style={"text-align": "right","padding":"0rem"},width=3)
        ])), 
        dbc.CardBody([
            dbc.Tabs([
                dbc.Tab(stats, label="Stats", tab_id="stats"),
                dbc.Tab(attacks, label="Attacks", tab_id="attacks"),
                dbc.Tab(bonuses, label="Bonuses", tab_id="bonuses"),
                # dbc.Tab(calcs, label="Calcs", tab_id="calcs"),
            ])
        ]),
    ],style=card_style)
        # dbc.CardBody([
        #     dbc.Row([
        #         dbc.Col(dbc.Label("Num Attacks", style=label_style)),
        #         dbc.Col(dbc.Input(type="number", value=len(character.attacks), min=1, max=100, step=1, style=input_style))
        #     ]),

        #     dbc.Row([
        #         dbc.Col(dbc.Label("Level", style=label_style)),
        #         dbc.Col(dbc.Input(type="number", value=character.level, min=0, max=20, step=1, style=input_style))
        #     ]),
            # dbc.Row([
            #     dbc.Col(dbc.Label("Add. Attack Modifier", style=label_style)),
            #     dbc.Col(dbc.Input(type="number", value=character.additional_attack_modifier, min=0, max=50, step=1, style=input_style))
            # ]),
            # dbc.Row([
            #     dbc.Col(dbc.Label("Attack Reroll On", style=label_style)),
            #     dbc.Col(dbc.Input(type="number", value=character.attack_reroll_on if character.attack_reroll_on is not None else 0, min=0, max=19, step=1, style=input_style))
            # ]),
            # dbc.Row([
            #     dbc.Col(dbc.Label("Crit On", style=label_style)),
            #     dbc.Col(dbc.Input(type="number", value=character.crit_on, min=2, max=20, step=1, style=input_style))
            # ]),
            # dbc.Row([
            #     dbc.Col(dbc.Label("Add. Damage Modifier", style=label_style)),
            #     dbc.Col(dbc.Input(type="number", value=character.additional_damage_modifier, min=0, max=50, step=1, style=input_style))
            # ]),
            # dbc.Row([
            #     dbc.Col(dbc.Label("Advantage", style=label_style)),
            #     dbc.Col(dbc.Checkbox(value=character.adv))
            # ]),
            # dbc.Row([
            #     dbc.Col(dbc.Label("Disadvantage", style=label_style)),
            #     dbc.Col(dbc.Checkbox(value=character.dis))
            # ]),
            # dbc.Row([
            #     dbc.Col(dbc.Label("Great Weapon Master", style=label_style)),
            #     dbc.Col(dbc.Checkbox(value=character.GWM))
            # ]),
            # dbc.Row([
            #     dbc.Col(dbc.Label("Great Weapon Fighting", style=label_style)),
            #     dbc.Col(dbc.Checkbox(value=character.GWF))
            # ]),
            # html.H5("Calculated Values"),
            # dbc.Row([
            #     dbc.Col(dbc.Label("Attack Modifier", style=label_style)),
            #     dbc.Col(dbc.Input(type="number", value=character.attack_modifier, readonly=True, style=input_style))
            # ]),
            # dbc.Row([
            #     dbc.Col(dbc.Label("Damage Modifier", style=label_style)),
            #     dbc.Col(dbc.Input(type="number", value=character.damage_modifier, readonly=True, style=input_style))
            # ]),
        # ]),



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

app = Dash(__name__, external_stylesheets=[style_sheet, dbc.icons.FONT_AWESOME])

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
                dbc.Input(type="text", placeholder="Character Name", style={'display': 'inline-block'},),
                dbc.Button(html.I(className="fa-solid fa-plus"), color="primary",style={'display': 'inline-block'})
            ])
        ,width=2,class_name="mb-3"),

        # dbc.Col([
        #     dbc.Input(type="text", placeholder="Character Name", style={'display': 'inline-block'},),
        #     dbc.Button(html.I(className="fa-solid fa-plus"),class_name="mb-3", color="primary",style={'display': 'inline-block'})
        # ],width=2),
        generate_character_cards(characters)
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

register_callbacks(app)
app.run_server(debug=True)



# %%
