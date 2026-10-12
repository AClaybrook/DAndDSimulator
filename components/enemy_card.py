""" Enemy Card Component """
import dash_bootstrap_components as dbc
from dash import html
from components.plots import COLORS
from components.character_card import check_row, number_row, text_row, to_list, to_str, label_value_rows
from computations.models import Enemy, STATS
from game_data import enemy_presets

E_LABELS_TO_VALS = {
    "Name": "name",
    "Armor Class": "armor_class",
    "Hit Points": "hit_points",
    "Damage Reduction": "damage_reduction",
    "Resistant (All)": "resistance",
    "Vulnerable (All)": "vulnerability",
    "Resistances": "resistances",
    "Vulnerabilities": "vulnerabilities",
    "Immunities": "immunities",
    **{f"{stat[:3].upper()} Save": f"{stat}_save" for stat in STATS},
}

E_LABELS = {v: k for k, v in E_LABELS_TO_VALS.items()}
DAMAGE_TYPE_LISTS = ["resistances", "vulnerabilities", "immunities"]
DAMAGE_TYPE_PLACEHOLDER = "i.e. fire, slashing (nonmagical)"

preset_options = [{"label": label, "value": value} for label, value in enemy_presets()]

def generate_enemy_card_body(enemy=None):
    """ The label/value rows of the enemy card """
    e = enemy or Enemy()
    return [
        text_row(E_LABELS["name"], e.name, id="enemy-name-input"),
        number_row(E_LABELS["armor_class"], e.armor_class, 1, 35),
        number_row(E_LABELS["hit_points"], e.hit_points, 1, 2000),
        number_row(E_LABELS["damage_reduction"], e.damage_reduction, 0, 20),
        check_row(E_LABELS["resistance"], e.resistance),
        check_row(E_LABELS["vulnerability"], e.vulnerability),
        text_row(E_LABELS["resistances"], to_str(e.resistances), DAMAGE_TYPE_PLACEHOLDER),
        text_row(E_LABELS["vulnerabilities"], to_str(e.vulnerabilities), DAMAGE_TYPE_PLACEHOLDER),
        text_row(E_LABELS["immunities"], to_str(e.immunities), DAMAGE_TYPE_PLACEHOLDER),
        *[number_row(E_LABELS[f"{stat}_save"], e.saving_throw_modifier(stat), -10, 30) for stat in STATS],
    ]

def generate_enemy_card(enemy=None, color=COLORS[0]):
    """ Generates the enemy card"""
    e = enemy or Enemy()
    return dbc.Col(
        dbc.Card([
            dbc.CardHeader(dbc.Row([
                dbc.Col(html.H5(e.name, style={'color': color, 'whiteSpace': 'nowrap'}, className="mb-0", id="enemy-name"), width="auto"),
                dbc.Col(dbc.Select(options=preset_options, placeholder="Load a monster or CR baseline...", size="sm", id="enemy-preset")),
            ], align="center", class_name="g-2")),
            dbc.CardBody(generate_enemy_card_body(e), id="enemy-card-body", class_name="enemy-grid"),
        ]),
    xs=12, lg=8, xl=6, id="enemy-card")


def extract_enemy_ui_values(enemy_card_body):
    """ Extracts the enemy ui values to a dictionary"""
    enemy_dict = {E_LABELS_TO_VALS[k]: v for k, v in label_value_rows(enemy_card_body) if k in E_LABELS_TO_VALS}
    for key in DAMAGE_TYPE_LISTS:
        enemy_dict[key] = [t.lower() for t in to_list(enemy_dict.get(key))]
    return enemy_dict
