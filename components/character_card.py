""" Character Card Component"""
import json
import dash_bootstrap_components as dbc
from dash import html, dcc
from components.plots import COLORS
from computations.models import Attack, Character

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
    """ Generates the character cards from a list of python characters"""
    cards = [
        generate_character_card(c.name, character=c, color=COLORS[ii], index=ii)
        for ii, c in enumerate(characters)
        ]
    return cards

# Map of attack labels to internal dictionary keys
A_LABEL_TO_VAL = {
    "Attack Name": "name",
    "Type": "type",
    "Attacking Stat": "ability_stat",
    "Weapon Damage": "damage",
    "Weapon Enhancement": "weapon_enhancement",
    "Crit on": "crit_on",
    "Offhand": "offhand",
    "Twohanded": "two_handed",
    "Saving Throw": "saving_throw",
    "Saving Throw Stat": "saving_throw_stat",
    "Successful Saving Throw Multiplier": "saving_throw_success_multiplier",
    "Bonus Attack Mod": "bonus_attack_die_mod_list",
    "Bonus Damage Mod": "bonus_damage_die_mod_list",
    "Bonus Crit Damage": "bonus_crit_die_mod_list",
    "Bonus Miss Damage": "bonus_miss_die_mod_list"
}
A_LABELS = {v:k for k,v in A_LABEL_TO_VAL.items()}

def extract_attack_ui_values(attack_ui_list):
    """Extracts the values from the attack_ui_list and returns a dictionary of the values
     and the number of attacks"""
    attack_ui_values = {}
    for a in attack_ui_list:
        if a['type'] == 'Row':
            row_vals = a['props']['children']
            if len(row_vals) == 2: # This is a row with a label and a value
                label_col = row_vals[0]
                value_col = row_vals[1]
                label = label_col['props']['children']['props']['children']
                value = value_col['props']['children']['props']['value']
                attack_ui_values[label] = value

    # Replace labels with internal dictionary keys and extract num attacks
    num_attacks = attack_ui_values.pop("Num Attacks")
    attack_ui_values = {A_LABEL_TO_VAL[k]:v for k,v in attack_ui_values.items()}

    # TODO: Handle missing values such as proficiency, damage type, etc.
    attack_ui_values["bonus_attack_die_mod_list"] = attack_ui_values["bonus_attack_die_mod_list"].split(",")
    attack_ui_values["bonus_damage_die_mod_list"] = attack_ui_values["bonus_damage_die_mod_list"].split(",")
    attack_ui_values["bonus_crit_die_mod_list"] = attack_ui_values["bonus_crit_die_mod_list"].split(",")
    attack_ui_values["bonus_miss_die_mod_list"] = attack_ui_values["bonus_miss_die_mod_list"].split(",")

    return attack_ui_values, num_attacks

C_LABEL_TO_DICT_MAP = {
    # Stats
    "Name": "name",
    "Level": "level",
    "Strength": "strength",
    "Dexterity": "dexterity",
    "Constitution": "constitution",
    "Intelligence": "intelligence",
    "Wisdom": "wisdom",
    "Charisma": "charisma",

    # Bonuses
    "Crit on": "crit_on",
    "Advantage": "advantage",
    "Disadvantage": "disadvantage",
    "Bonus Attack Mod": "bonus_attack_die_mod_list",
    "Bonus Damage Mod": "bonus_damage_die_mod_list",
    "Bonus Crit Mod": "bonus_crit_die_mod_list",
    "Bonus Miss Mod": "bonus_miss_die_mod_list",
    "Great Weapon Master": "GWM",
    "Savage Attacker": "savage_attacker",
    "Sharpshooter": "sharpshooter",
    "Tavern Brawler": "tavern_brawler",
    "Great Weapon Fighting": "GWF",
    "Archery": "archery",
    "Dueling": "dueling",
    "Two Weapon Fighting": "TWF",
    "Raging": "raging",
    "Brutal Critical": "brutal_critical",
    "Divine Smite": "divine_smite",
    "Divine Smite Level": "divine_smite_level",
    "Improved Divine Smite": "improved_divine_smite",
    "Empowered Evocation": "empowered_evocation",
    "Agonizing Blast": "agonizing_blast",
    "Life Drinker": "lifedrinker",
    "Elemental Affinity": "elemental_affinity",
    "Half Orc Savage Attacks": "savage_attacks_half_orc",
}
C_LABELS = {v:k for k,v in C_LABEL_TO_DICT_MAP.items()}

def extract_character_ui_values(character_from_ui):
    """ Parses the character ui values into a dictionary"""
    character_dict = {}
    card_body = character_from_ui['props']['children']['props']['children'][1]
    tabs = card_body['props']['children'][0]['props']['children']
    tab = tabs[0]
    # Loop through tabs, extract values from the Stats and Bonuses tabs
    for tab in tabs:
        tab_label = tab['props']['label']
        if tab_label in ['Stats','Bonuses']:
            rows = tab['props']['children']['props']['children'][0]['props']['children']
            for row in rows:
                label_val_row = row['props']['children']
                if len(label_val_row) == 2:
                    label_col = label_val_row[0]
                    value_col = label_val_row[1]
                    label = label_col['props']['children']['props']['children']
                    value = value_col['props']['children']['props']['value']
                    character_dict[label] = value

    # Convert labels to internal dictionary keys
    character_dict = {C_LABEL_TO_DICT_MAP[k]:v for k,v in character_dict.items()}
    # Convert strs to lists
    character_dict["bonus_attack_die_mod_list"] = character_dict["bonus_attack_die_mod_list"].split(",")
    character_dict["bonus_damage_die_mod_list"] = character_dict["bonus_damage_die_mod_list"].split(",")
    character_dict["bonus_crit_die_mod_list"] = character_dict["bonus_crit_die_mod_list"].split(",")
    character_dict["bonus_miss_die_mod_list"] = character_dict["bonus_miss_die_mod_list"].split(",")
    return character_dict


def characters_from_ui(characters_list, attack_stores):
    """ Parses the character ui values into a list of characters"""
    characters = []
    for ii, c in enumerate(characters_list):
        attacks_python = [Attack(**attack) for attack in json.loads(attack_stores[ii])]
        characters.append(Character(attacks=attacks_python, **extract_character_ui_values(c)))
    return characters

def set_attack_from_values(avals, i, index, label_style=None, input_style=None):
    """ Sets the attack ui from a dictionary of values"""
    if label_style is None:
        label_style = {'marginBottom': '0.2rem'}
    if input_style is None:
        input_style = {'paddingTop': '0.0rem', 'paddingBottom': '0.0rem'}

    attack_ui = [
        dbc.Row([dbc.Col(dbc.Label(A_LABELS["name"], style=label_style)),dbc.Col(dbc.Input(type="text", value=avals[i]["name"], style=input_style, id={"type":"attack_name","index":index}))]),
        dbc.Row([
            dbc.Col(dbc.Label(A_LABELS["type"], style=label_style)),
            dbc.Col(dbc.Select(options=attack_options,
                                    value=avals[i]["type"], style=input_style))
                                    ]),
        dbc.Row([
        dbc.Col(dbc.Label(A_LABELS["ability_stat"], style=label_style)),
        dbc.Col(dbc.Select(options=stat_options,value=avals[i]["ability_stat"], style=input_style))
        ]),
        # Repeated Attacks
        dbc.Row([
            dbc.Col(dbc.Label("Num Attacks", style=label_style)),
            dbc.Col(dbc.Input(type="number", value=1, min=1, max=20, step=1, style=input_style))
        ]),
        # Weapon specific
        dbc.Row([
            dbc.Col(dbc.Label(A_LABELS["damage"], style=label_style)),
            dbc.Col(dbc.Input(type="string", value=avals[i]["damage"], style=input_style))
        ]),
        dbc.Row([
            dbc.Col(dbc.Label(A_LABELS["weapon_enhancement"], style=label_style)),
            dbc.Col(dbc.Input(type="number", value=avals[i]["weapon_enhancement"], min=0, max=10, step=1, style=input_style))
        ]),
        dbc.Row([
            dbc.Col(dbc.Label(A_LABELS["offhand"], style=label_style)),
            dbc.Col(dbc.Checkbox(value=avals[i]["offhand"]))
        ]),
        dbc.Row([
            dbc.Col(dbc.Label(A_LABELS["two_handed"], style=label_style)),
            dbc.Col(dbc.Checkbox(value=avals[i]["two_handed"]))
        ]),
        # Spell specific
        dbc.Row([
            dbc.Col(dbc.Label(A_LABELS["saving_throw"], style=label_style)),
            dbc.Col(dbc.Checkbox(value=avals[i]["saving_throw"]))
        ]),
        dbc.Row([
            dbc.Col(dbc.Label(A_LABELS["saving_throw_stat"], style=label_style)),
            dbc.Col(dbc.Select(options=stat_options,value=avals[i]["saving_throw_stat"], style=input_style))
        ]),
        dbc.Row([
            dbc.Col(dbc.Label(A_LABELS["saving_throw_success_multiplier"], style=label_style)),
            dbc.Col(dbc.Input(type="number", value=avals[i]["saving_throw_success_multiplier"], min=0, max=1, step=0.5, style=input_style))
        ]),
        # Additional
        dbc.Row([
            dbc.Col(dbc.Label(A_LABELS["bonus_attack_die_mod_list"], style=label_style)),
            dbc.Col(dbc.Input(type="string", value=",".join(avals[i]["bonus_attack_die_mod_list"]), style=input_style))
        ]),
        dbc.Row([
            dbc.Col(dbc.Label(A_LABELS["bonus_damage_die_mod_list"], style=label_style)),
            dbc.Col(dbc.Input(type="string", value=",".join(avals[i]["bonus_damage_die_mod_list"]), style=input_style))
        ]),
        dbc.Row([
            dbc.Col(dbc.Label(A_LABELS["bonus_crit_die_mod_list"], style=label_style)),
            dbc.Col(dbc.Input(type="string", value=",".join(avals[i]["bonus_crit_die_mod_list"]), style=input_style))
        ]),
        dbc.Row([
            dbc.Col(dbc.Label(A_LABELS["bonus_miss_die_mod_list"], style=label_style)),
            dbc.Col(dbc.Input(type="string", value=",".join(avals[i]["bonus_miss_die_mod_list"]), style=input_style))
        ])
        ]
    return attack_ui

def generate_character_card(character_name, character=None, color="", index=1):
    """ Generates the character card, either from a character or with default values"""
    input_style = {'paddingTop': '0.0rem', 'paddingBottom': '0.0rem'}
    label_style = {'marginBottom': '0.2rem'}
    card_style = {'maxHeight': '60vh','minHeight': '60vh','overflowY': 'auto'}
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

        # Attacks are handled separately

        # Bonuses
        ## Generic bonuses
        "crit_on": character.crit_on if character else 20,
        "advantage": character.advantage if character else False,
        "disadvantage": character.disadvantage if character else False,
        "bonus_attack_die_mod_list": character.bonus_attack_die_mod_list if character else ["0d4","0"],
        "bonus_damage_die_mod_list": character.bonus_damage_die_mod_list if character else ["0d4","0"],
        "bonus_crit_die_mod_list": character.bonus_crit_die_mod_list if character else ["0d4","0"],
        "bonus_miss_die_mod_list": character.bonus_miss_die_mod_list if character else ["0d4","0"],

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
        "raging": character.raging if character else False,
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

    # Stats tab
    stats = dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col(dbc.Label(C_LABELS["name"], style=label_style)),
                dbc.Col(dbc.Input(type="text", value=vals["name"], style=input_style, id={"type":"character name input","index":index}))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label(C_LABELS["level"], style=label_style)),
                dbc.Col(dbc.Input(type="number", value=vals["level"], min=1, max=20, step=1, style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label(C_LABELS["strength"], style=label_style)),
                dbc.Col(dbc.Input(type="number", value=vals["strength"], min=1, max=30, step=1, style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label(C_LABELS["dexterity"], style=label_style)),
                dbc.Col(dbc.Input(type="number", value=vals["dexterity"], min=1, max=30, step=1, style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label(C_LABELS["constitution"], style=label_style)),
                dbc.Col(dbc.Input(type="number", value=vals["constitution"], min=1, max=30, step=1, style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label(C_LABELS["intelligence"], style=label_style)),
                dbc.Col(dbc.Input(type="number", value=vals["intelligence"], min=1, max=30, step=1, style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label(C_LABELS["wisdom"], style=label_style)),
                dbc.Col(dbc.Input(type="number", value=vals["wisdom"], min=1, max=30, step=1, style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label(C_LABELS["charisma"], style=label_style)),
                dbc.Col(dbc.Input(type="number", value=vals["charisma"], min=1, max=30, step=1, style=input_style))
            ]),
            dbc.Row([
                dbc.Textarea(placeholder="Optional Description",  style={'width': '100%','minHeight': '10vh'}),
            ]),
        ])
    ],style=tab_style)

    # Attacks tab, NOTE: Keep in sync with Attack class
    avals = []
    if character:
        for _,a in enumerate(character.attacks):
            attack = {
            "name": a.name,
            "bonus_attack_die_mod_list": a.bonus_attack_die_mod_list,
            "bonus_damage_die_mod_list": a.bonus_damage_die_mod_list,
            "proficent": a.proficent,
            "type": a.type,
            "ability_stat": a.ability_stat,
            "damage": a.damage,
            "advantage": a.advantage,
            "disadvantage": a.disadvantage,
            "always_hit": a.always_hit,
            "always_crit": a.always_crit,
            "crit_on": a.crit_on,
            "weapon_enhancement": a.weapon_enhancement,
            "offhand": a.offhand,
            "two_handed": a.two_handed,
            "saving_throw": a.saving_throw,
            "saving_throw_stat": a.saving_throw_stat,
            "saving_throw_success_multiplier" : a.saving_throw_success_multiplier,
            "damage_type": a.damage_type,
            "bonus_crit_die_mod_list": a.bonus_crit_die_mod_list,
            "bonus_miss_die_mod_list": a.bonus_miss_die_mod_list,
            }
            avals.append(attack)
    else:
        attack = {
            "name": "Attack Name",
            "bonus_attack_die_mod_list": ["0d4","0"],
            "bonus_damage_die_mod_list": ["0d4","0"],
            "proficent": True,
            "type": "weapon (melee)",
            "ability_stat": "strength",
            "damage": "1d6",
            "advantage": False,
            "disadvantage": False,
            "always_hit": False,
            "always_crit": False,
            "crit_on": 20,
            "weapon_enhancement": 0,
            "offhand": False,
            "two_handed": False,
            "saving_throw": False,
            "saving_throw_stat": "dexterity",
            "saving_throw_success_multiplier": 0.5,
            "damage_type": "slashing",
            "bonus_crit_die_mod_list": ["0d4","0"],
            "bonus_miss_die_mod_list": ["0d4","0"],
        }
        avals.append(attack)

    attacks = dbc.Card([
        dbc.CardBody([
            html.Div(set_attack_from_values(avals, 0, index), id={"type": "attack_ui", "index": index}),
            dbc.Row([
                dbc.Col([
                    dbc.Button(html.I(className="fa-solid fa-plus"), color="primary", class_name="me-1", id={"type": "add-attack", "index": index}),
                    dbc.Button(html.I(className="fa-solid fa-x"), color="danger", class_name="me-1", id={"type": "delete-attack", "index": index})
                        ],style={"textAlign": "end"}),
            ], class_name="mb-1 mt-1"),
            dbc.Row(dbc.ListGroup(
                [dbc.ListGroupItem(a["name"], active=ii==0, id={"type": "attack", "index": index, "num": ii}) for ii,a in enumerate(avals)],
                id={"type": "attacks", "index": index}, numbered=True)),
            dcc.Store(id={"type": "attack_store", "index": index}, data=json.dumps(avals)), # Used to track attack data

        ]),
    ], style=tab_style)

    # Bonuses, Feats and abilities tab
    bonuses = dbc.Card([
        dbc.CardBody([
            dbc.Row([
                html.H6("Bonus Unaccounted for Modifiers"),
            ]),
            dbc.Row([
                dbc.Col(dbc.Label(C_LABELS["crit_on"], style=label_style)),
                dbc.Col(dbc.Input(type="number", value=vals["crit_on"], min=2, max=20, step=1, style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label(C_LABELS["advantage"], style=label_style)),
                dbc.Col(dbc.Checkbox(value=vals["advantage"]))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label(C_LABELS["disadvantage"], style=label_style)),
                dbc.Col(dbc.Checkbox(value=vals["disadvantage"]))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label(C_LABELS["bonus_attack_die_mod_list"], style=label_style)),
                dbc.Col(dbc.Input(type="string", value=",".join(vals["bonus_attack_die_mod_list"]), style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label(C_LABELS["bonus_damage_die_mod_list"], style=label_style)),
                dbc.Col(dbc.Input(type="string", value=",".join(vals["bonus_damage_die_mod_list"]), style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label(C_LABELS["bonus_crit_die_mod_list"], style=label_style)),
                dbc.Col(dbc.Input(type="string", value=",".join(vals["bonus_crit_die_mod_list"]), style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label(C_LABELS["bonus_miss_die_mod_list"], style=label_style)),
                dbc.Col(dbc.Input(type="string", value=",".join(vals["bonus_miss_die_mod_list"]), style=input_style))
            ]),
            dbc.Row([
                html.H6("Feats"),
            ]),
            dbc.Row([
                dbc.Col(dbc.Label(C_LABELS["GWM"], style=label_style)),
                dbc.Col(dbc.Checkbox(value=vals["GWM"]))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label(C_LABELS["savage_attacker"], style=label_style)),
                dbc.Col(dbc.Checkbox(value=vals["savage_attacker"]))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label(C_LABELS["sharpshooter"], style=label_style)),
                dbc.Col(dbc.Checkbox(value=vals["sharpshooter"]))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label(C_LABELS["tavern_brawler"], style=label_style)),
                dbc.Col(dbc.Checkbox(value=vals["tavern_brawler"]))
            ]),
            dbc.Row([
                html.H6("Fighting Styles"),
            ]),
            dbc.Row([
                dbc.Col(dbc.Label(C_LABELS["GWF"], style=label_style)),
                dbc.Col(dbc.Checkbox(value=vals["GWF"]))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label(C_LABELS["archery"], style=label_style)),
                dbc.Col(dbc.Checkbox(value=vals["archery"]))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label(C_LABELS["dueling"], style=label_style)),
                dbc.Col(dbc.Checkbox(value=vals["dueling"]))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label(C_LABELS["TWF"], style=label_style)),
                dbc.Col(dbc.Checkbox(value=vals["TWF"]))
            ]),
            dbc.Row([
                html.H6("Barbarian"),
            ]),
            dbc.Row([
                dbc.Col(dbc.Label(C_LABELS["raging"], style=label_style)),
                dbc.Col(dbc.Checkbox(value=vals["raging"]))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label(C_LABELS["brutal_critical"], style=label_style)),
                dbc.Col(dbc.Checkbox(value=vals["brutal_critical"]))
            ]),
            dbc.Row([
                html.H6("Paladin"),
            ]),
            dbc.Row([
                dbc.Col(dbc.Label(C_LABELS["divine_smite"], style=label_style)),
                dbc.Col(dbc.Checkbox(value=vals["divine_smite"]))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label(C_LABELS["divine_smite_level"], style=label_style)),
                dbc.Col(dbc.Input(type="number", value=vals["divine_smite_level"], min=1, max=4, step=1, style=input_style))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label(C_LABELS["improved_divine_smite"], style=label_style)),
                dbc.Col(dbc.Checkbox(value=vals["improved_divine_smite"]))
            ]),
            dbc.Row([
                html.H6("Wizard"),
            ]),
            dbc.Row([
                dbc.Col(dbc.Label(C_LABELS["empowered_evocation"], style=label_style)),
                dbc.Col(dbc.Checkbox(value=vals["empowered_evocation"]))
            ]),
            dbc.Row([
                html.H6("Warlock"),
            ]),
            dbc.Row([
                dbc.Col(dbc.Label(C_LABELS["agonizing_blast"], style=label_style)),
                dbc.Col(dbc.Checkbox(value=vals["agonizing_blast"]))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label(C_LABELS["lifedrinker"], style=label_style)),
                dbc.Col(dbc.Checkbox(value=vals["lifedrinker"]))
            ]),
            dbc.Row([
                html.H6("Sorcerer"),
            ]),
            dbc.Row([
                dbc.Col(dbc.Label(C_LABELS["elemental_affinity"], style=label_style)),
                dbc.Col(dbc.Checkbox(value=vals["elemental_affinity"]))
            ]),
            dbc.Row([
                html.H6("Racial Bonuses"),
            ]),
            dbc.Row([
                dbc.Col(dbc.Label(C_LABELS["savage_attacks_half_orc"], style=label_style)),
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
                dbc.Col(html.H4(vals["name"],style={'color': color, 'whiteSpace':'nowrap'},id={"type":"character name","index":index}),style={'overflowX': 'auto'}, width={"size":9},class_name="pe-0"),
                dbc.Col([dbc.Button(html.I(className="fa-solid fa-copy"), color="primary",class_name="me-1",style={"display":"flex"},id={"type": "copy character", "index": index}),
                        dbc.Button(html.I(className="fa-solid fa-x"), color="danger",class_name="me-1",style={"display":"flex"},id={"type": "delete character", "index": index}),
                        ], style={"textAlign": "end","padding":"0rem","display":"flex"},width=3)
            ])),
            dbc.CardBody([
                dbc.Tabs([
                    dbc.Tab(stats, label="Stats", tab_id="stats"),
                    dbc.Tab(attacks, label="Attacks", tab_id="attacks"),
                    dbc.Tab(bonuses, label="Bonuses", tab_id="bonuses"),
                    # dbc.Tab(calcs, label="Calcs", tab_id="calcs"),
                ]),
            ]),
        ],style=card_style),
    width=3, id={"type": "character card", "index": index}, class_name="mb-2")
