import dash_bootstrap_components as dbc
from dash import html
from plots import COLORS

E_LABELS_TO_VALS = {
    "Name": "name",
    "Armor Class": "armor_class",
    "Hit Points": "hit_points",
    "Damage Reduction": "damage_reduction",
    "Resistant": "resistance",
    "Vulnerable": "vulnerability",
    "Saving Throw": "saving_throw",
}

E_LABELS =  {v:k for k,v in E_LABELS_TO_VALS.items()}

def generate_enemy_card(enemy=None, color=COLORS[0]):
    input_style = {'paddingTop': '0.0rem', 'paddingBottom': '0.0rem'}
    label_style = {'marginBottom': '0.2rem'}
    card_style = {'maxHeight': '30vh','minHeight': '30vh','overflowY': 'auto'}

    vals = {
        "name": enemy.name if enemy else "Mind Flayer",
        "armor_class": enemy.armor_class if enemy else 15,
        "hit_points": enemy.hit_points if enemy else 71,
        "damage_reduction": enemy.damage_reduction if enemy else 0,
        "resistance": enemy.resistance if enemy else False,
        "vulnerability": enemy.vulnerability if enemy else False,
        "saving_throw": enemy.saving_throw if enemy else False,
    }

    return dbc.Col(
        dbc.Card([
            dbc.CardHeader([
                html.H4(vals["name"],style={'color': color, 'whiteSpace':'nowrap'},id="enemy-name"),
            ]), 
            dbc.CardBody([
                dbc.Row([
                    dbc.Col(dbc.Label(E_LABELS["name"], style=label_style)),
                    dbc.Col(dbc.Input(type="string", value=vals["name"], style=input_style, id="enemy-name-input"))
                ]),
                dbc.Row([
                    dbc.Col(dbc.Label(E_LABELS["armor_class"], style=label_style)),
                    dbc.Col(dbc.Input(type="number", value=vals["armor_class"], min=1, max=35, step=1, style=input_style))
                ]),
                dbc.Row([
                    dbc.Col(dbc.Label(E_LABELS["hit_points"], style=label_style)),
                    dbc.Col(dbc.Input(type="number", value=vals["hit_points"], min=1, max=500, step=1, style=input_style))
                ]),
                dbc.Row([
                    dbc.Col(dbc.Label(E_LABELS["damage_reduction"], style=label_style)),
                    dbc.Col(dbc.Input(type="number", value=vals["damage_reduction"], min=0, max=20, step=1, style=input_style))
                ]),
                dbc.Row([
                    dbc.Col(dbc.Label(E_LABELS["resistance"], style=label_style)),
                    dbc.Col(dbc.Checkbox(value=vals["resistance"], style=input_style))
                ]),
                dbc.Row([
                    dbc.Col(dbc.Label(E_LABELS["vulnerability"], style=label_style)),
                    dbc.Col(dbc.Checkbox(value=vals["vulnerability"], style=input_style))
                ]),
                dbc.Row([
                    dbc.Col(dbc.Label(E_LABELS["saving_throw"], style=label_style)),
                    dbc.Col(dbc.Input(type="number", value=vals["saving_throw"], min=1, max=35, step=1, style=input_style))
                ]),
            ], id="enemy-card-body"),
        ],style=card_style),
    width=3, id="enemy-card")


def extract_enemy_ui_values(enemy_card_body):
    enemy_dict = {}
    for row in enemy_card_body:
        label_val_row = row['props']['children']
        if len(label_val_row) == 2:
            label_col = label_val_row[0]
            value_col = label_val_row[1]
            label = label_col['props']['children']['props']['children']
            value = value_col['props']['children']['props']['value']
            enemy_dict[label] = value
    enemy_dict = {E_LABELS_TO_VALS[k]:v for k,v in enemy_dict.items()}
    return enemy_dict