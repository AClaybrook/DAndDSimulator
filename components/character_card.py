import dash_bootstrap_components as dbc
from dash import html
from plots import COLORS

# Stat options
stat_options=[{"label": "Strength", "value": "strength"},
                {"label":"Dexterity", "value": "dexterity"},
                {"label":"Constitution", "value": "constitution"},
                {"label":"Intelligence", "value": "intelligence"},
                {"label":"Wisdom", "value": "wisdom"},
                {"label":"Charisma", "value": "charisma"}]


attack_options = [{"label": "Weapon (Melee)","value": "weapon (melee)"},
                    {"label":"Weapon (Ranged)", "value": "weapon (ranged)"},
                    {"label":"Spell", "value": "spell"},
                    {"label": "Unarmed", "value": "unarmed"},
                    {"label": "Thrown", "value": "thrown"}
                    ]

def generate_character_cards(characters):
    cards = [
        generate_character_card(c.name, character=c, color=COLORS[ii], index=ii+1)
        for ii, c in enumerate(characters)
        ]
    return cards


def generate_character_card(character_name, character=None, color="", index=-1):
    input_style = {'padding-top': '0.0rem', 'padding-bottom': '0.0rem'}
    label_style = {'margin-bottom': '0.2rem'}
    card_style = {'max-height': '60vh','min-height': '60vh','overflow-y': 'auto'}
    tab_style = {}

    vals = {
        # Stats
        "name": character.name if character else character_name,
        "level": character.level if character else 1,
        "strength": character.strength if character else 10,
        "dexterity": character.dexterity if character else 10,
        "constitution": character.constitution if character else 10,
        "intelligence": character.intelligence if character else 10,
        "wisdom": character.wisdom if character else 10,
        "charisma": character.charisma if character else 10,

        # TODO: Attacks, should be added below
        "attack1.name": "Attack Name",

        # Bonuses
        ## Generic bonuses
        "crit_on": character.crit_on if character else 20,
        "advantage": character.adv if character else False,
        "disadvantage": character.dis if character else False,
        "bonus_attack_mods": f"{character.additional_attack_die},{character.additional_attack_modifier}" if character else "0d4,0",
        "bonus_damage_mods": f"{character.additional_attack_die},{character.additional_attack_modifier}" if character else "0d4,0",

        ## Feats
        "GWM": character.GWM if character else False,
        "savage_attacker": character.savage_attacker if character else False,
        "sharpshooter": character.sharpshooter if character else False,
        "tavern_brawler": character.tavern_brawler if character else False,

        # Fighting Styles
        "GWF": character.GWF if character else False,
        "archery": character.archery if character else False,
        "dueling": character.dueling if character else False,
        "TWF": character.TWF if character else False,
        
        ## Barbarian
        "raging": character.rage if character else False,
        "brutal_critical": character.brutal_critical if character else False,
        ## Paladin
        "divine_smite": character.divine_smite if character else False,
        "divine_smite_level": character.divine_smite_level if character else 1,
        "improved_divine_smite": character.improved_divine_smite if character else False,
        ## Wizard
        "empowered_evocation": character.empowered_evocation if character else False,
        ## Warlock
        "agonizing_blast": character.agonizing_blast if character else False,
        "lifedrinker": character.lifedrinker if character else False,
        ## Sorcerer
        "elemental_affinity": character.elemental_affinity if character else False,
        "savage_attacks_half_orc": character.savage_attacks_half_orc if character else False,

    }

    # TODO: Implement attacks
    num_attacks = 1
    if character:
        num_attacks = len(character.attacks)
        c_attacks = {}
        # TODO: Loop through each character m nbattack
        for i,a in enumerate(character.attacks):
            pass

            

    # Stats tab
    stats = dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col(dbc.Label("Name", style=label_style)),
                dbc.Col(dbc.Input(type="text", value=vals["name"], style=input_style, id={"type":"character name input","index":index}))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Level", style=label_style)),
                dbc.Col(dbc.Input(type="number", value=vals["level"], min=1, max=20, step=1, style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Strength", style=label_style)),
                dbc.Col(dbc.Input(type="number", value=vals["strength"], min=1, max=30, step=1, style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Dexterity", style=label_style)),
                dbc.Col(dbc.Input(type="number", value=vals["dexterity"], min=1, max=30, step=1, style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Constitution", style=label_style)),
                dbc.Col(dbc.Input(type="number", value=vals["constitution"], min=1, max=30, step=1, style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Intelligence", style=label_style)),
                dbc.Col(dbc.Input(type="number", value=vals["intelligence"], min=1, max=30, step=1, style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Wisdom", style=label_style)),
                dbc.Col(dbc.Input(type="number", value=vals["wisdom"], min=1, max=30, step=1, style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Charisma", style=label_style)),
                dbc.Col(dbc.Input(type="number", value=vals["charisma"], min=1, max=30, step=1, style=input_style))
            ]),
            dbc.Row([
                dbc.Textarea(placeholder="Optional Description",  style={'width': '100%','min-height': '10vh'}),
            ]),
        ])
    ],style=tab_style)

    # Attacks tab
    i = 1
    attacks = dbc.Card([
        dbc.CardBody([
            dbc.Row([
                    dbc.Col(dbc.Button(html.I(className="fa-solid fa-plus"), color="primary", id={"type": "add-attack", "index": index})),
            ]),
            # dbc.Row(children=[], id={"type": "attacks", "index": character.name}),
            dbc.Row([dbc.Col(dbc.Label("Attack Name", style=label_style)),dbc.Col(dbc.Input(type="text", value=vals[f"attack{i}.name"], style=input_style))]),
            dbc.Row([
                dbc.Col(dbc.Label("Type", style=label_style)),
                dbc.Col(dbc.Select(options=attack_options,
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
            dbc.Row(dbc.ListGroup(children=[], id={"type": "attacks", "index": index})),
            
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
                dbc.Col(dbc.Input(type="number", value=vals["crit_on"], min=2, max=20, step=1, style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Advantage", style=label_style)),
                dbc.Col(dbc.Checkbox(value=vals["advantage"]))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Disadvantage", style=label_style)),
                dbc.Col(dbc.Checkbox(value=vals["disadvantage"]))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Bonus attack modifiers", style=label_style)),
                dbc.Col(dbc.Input(type="string", value=vals["bonus_attack_mods"], style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Bonus damage modifiers", style=label_style)),
                dbc.Col(dbc.Input(type="string", value=vals["bonus_damage_mods"], style=input_style))
            ]),
            dbc.Row([
                html.H6("Feats"),
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Great Weapon Master", style=label_style)),
                dbc.Col(dbc.Checkbox(value=vals["GWM"]))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Savage Attacker", style=label_style)),
                dbc.Col(dbc.Checkbox(value=vals["savage_attacker"]))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Sharpshooter", style=label_style)),
                dbc.Col(dbc.Checkbox(value=vals["sharpshooter"]))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Tavern Brawler", style=label_style)),
                dbc.Col(dbc.Checkbox(value=vals["tavern_brawler"]))
            ]),
            dbc.Row([
                html.H6("Fighting Styles"),
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Great Weapon Fighting", style=label_style)),
                dbc.Col(dbc.Checkbox(value=vals["GWF"]))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Archery", style=label_style)),
                dbc.Col(dbc.Checkbox(value=vals["archery"]))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Dueling", style=label_style)),
                dbc.Col(dbc.Checkbox(value=vals["dueling"]))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Two Weapon Fighting", style=label_style)),
                dbc.Col(dbc.Checkbox(value=vals["TWF"]))
            ]),
            dbc.Row([
                html.H6("Barbarian"),
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Raging", style=label_style)),
                dbc.Col(dbc.Checkbox(value=vals["raging"]))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Brutal Critical", style=label_style)),
                dbc.Col(dbc.Checkbox(value=vals["brutal_critical"]))
            ]),
            dbc.Row([
                html.H6("Paladin"),
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Divine Smite", style=label_style)),
                dbc.Col(dbc.Checkbox(value=vals["divine_smite"]))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Divine Smite Level", style=label_style)),
                dbc.Col(dbc.Input(type="number", value=vals["divine_smite_level"], min=1, max=4, step=1, style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Improved Divine Smite", style=label_style)),
                dbc.Col(dbc.Checkbox(value=vals["improved_divine_smite"]))
            ]),
            dbc.Row([
                html.H6("Wizard"),
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Empowered Evocation", style=label_style)),
                dbc.Col(dbc.Checkbox(value=vals["empowered_evocation"]))
            ]),
            dbc.Row([
                html.H6("Warlock"),
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Agonizing Blast", style=label_style)),
                dbc.Col(dbc.Checkbox(value=vals["agonizing_blast"]))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Life Drinker", style=label_style)),
                dbc.Col(dbc.Checkbox(value=vals["lifedrinker"]))
            ]),
            dbc.Row([
                html.H6("Sorcerer"),
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Elemental Affinity", style=label_style)),
                dbc.Col(dbc.Checkbox(value=vals["elemental_affinity"]))
            ]),
            dbc.Row([
                html.H6("Racial Bonuses"),
            ]),
            dbc.Row([
                dbc.Col(dbc.Label("Half Orc Savage Attacks", style=label_style)),
                dbc.Col(dbc.Checkbox(value=vals["savage_attacks_half_orc"]))
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

    return dbc.Col(
        dbc.Card([
            dbc.CardHeader(dbc.Row([
                dbc.Col(html.H4(vals["name"],style={'color': color, 'white-space':'nowrap'},id={"type":"character name","index":index}),style={'overflow-x': 'auto'}, width={"size":9},class_name="pe-0"),
                dbc.Col([dbc.Button(html.I(className="fa-solid fa-copy"), color="primary",class_name="me-1",style={"display":"flex"}),
                        dbc.Button(html.I(className="fa-solid fa-x"), color="danger",class_name="me-1",style={"display":"flex"},id={"type": "delete character", "index": index}),
                        ], style={"text-align": "right","padding":"0rem","display":"flex"},width=3)
            ])), 
            dbc.CardBody([
                dbc.Tabs([
                    dbc.Tab(stats, label="Stats", tab_id="stats"),
                    dbc.Tab(attacks, label="Attacks", tab_id="attacks"),
                    dbc.Tab(bonuses, label="Bonuses", tab_id="bonuses"),
                    # dbc.Tab(calcs, label="Calcs", tab_id="calcs"),
                ])
            ]),
        ],style=card_style),
    width=3, id={"type": "character card", "index": index})
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
