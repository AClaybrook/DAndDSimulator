""" Character Card Component"""
import json
import dash_bootstrap_components as dbc
from dash import html, dcc
from components.plots import COLORS
from computations.models import Attack, Character, DAMAGE_TYPES, multiple_die_and_mod_from_list
from game_data import attack_templates

INPUT_STYLE = {'paddingTop': '0.0rem', 'paddingBottom': '0.0rem'}
LABEL_STYLE = {'marginBottom': '0.2rem'}
DICE_PLACEHOLDER = "i.e. 1d4, 2"

# Stat options
stat_options = [{"label": "Strength", "value": "strength"},
                {"label": "Dexterity", "value": "dexterity"},
                {"label": "Constitution", "value": "constitution"},
                {"label": "Intelligence", "value": "intelligence"},
                {"label": "Wisdom", "value": "wisdom"},
                {"label": "Charisma", "value": "charisma"}]

attack_options = [{"label": "Weapon (Melee)", "value": "weapon (melee)"},
                  {"label": "Weapon (Ranged)", "value": "weapon (ranged)"},
                  {"label": "Spell", "value": "spell"},
                  {"label": "Unarmed", "value": "unarmed"},
                  {"label": "Thrown", "value": "thrown"}]

damage_type_options = [{"label": t.title(), "value": t} for t in DAMAGE_TYPES]

template_options = [{"label": label, "value": value} for label, value in attack_templates()]

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
    "Damage Type": "damage_type",
    "Weapon Enhancement": "weapon_enhancement",
    "Crit on": "crit_on",
    "Proficient": "proficent",
    "Advantage": "advantage",
    "Disadvantage": "disadvantage",
    "Always Hit": "always_hit",
    "Always Crit": "always_crit",
    "Offhand": "offhand",
    "Twohanded": "two_handed",
    "Heavy": "heavy",
    "Once Per Turn Eligible": "once_per_turn_eligible",
    "Uses Per Fight (0 = every round)": "uses_per_fight",
    "Fallback For (attack name)": "fallback_for",
    "Saving Throw": "saving_throw",
    "Saving Throw Stat": "saving_throw_stat",
    "Successful Saving Throw Multiplier": "saving_throw_success_multiplier",
    "Bonus Attack Mod": "bonus_attack_die_mod_list",
    "Bonus Damage Mod": "bonus_damage_die_mod_list",
    "Bonus Crit Damage": "bonus_crit_die_mod_list",
    "Bonus Miss Damage": "bonus_miss_die_mod_list"
}
A_LABELS = {v: k for k, v in A_LABEL_TO_VAL.items()}
DIE_MOD_LISTS = ["bonus_attack_die_mod_list", "bonus_damage_die_mod_list", "bonus_crit_die_mod_list", "bonus_miss_die_mod_list", "once_per_turn_die_mod_list"]

def to_list(value):
    """ '1d4, 2' -> ['1d4', '2'] """
    return [v.strip() for v in (value or "").split(",") if v.strip()]

def to_str(values):
    """ ['1d4', 2] -> '1d4, 2' """
    return ", ".join(str(v) for v in values or [])

def _children(component):
    children = component.get('props', {}).get('children') if isinstance(component, dict) else component
    if isinstance(children, (list, tuple)):
        return children
    return [children] if isinstance(children, dict) else []

def _is_label_row(component):
    """ A row made by label_row: a column with a Label and a column with an input """
    if not isinstance(component, dict) or component.get('type') != 'Row':
        return False
    columns = component['props'].get('children')
    return (isinstance(columns, list) and len(columns) == 2
            and isinstance(columns[0].get('props', {}).get('children'), dict) and columns[0]['props']['children'].get('type') == 'Label')

def label_value_rows(component):
    """ Yields (label, value) for every label/input row inside a (serialized) component tree, used to read values back from the UI.
        Rows can be nested anywhere, i.e. inside collapsible sections """
    stack = list(_children(component)) if isinstance(component, dict) else list(component)
    while stack:
        node = stack.pop(0)
        if _is_label_row(node):
            label_col, value_col = node['props']['children']
            yield label_col['props']['children']['props']['children'], value_col['props']['children']['props'].get('value')
        elif isinstance(node, (dict, list)):
            stack[:0] = _children(node)

def find_components(component, component_type):
    """ Every component of a type inside a (serialized) component tree """
    stack = [component]
    while stack:
        node = stack.pop()
        if isinstance(node, dict) and node.get('type') == component_type:
            yield node
        stack.extend(_children(node))

def extract_attack_ui_values(attack_ui_list):
    """Extracts the values from the attack_ui_list and returns a dictionary of the values
     and the number of attacks"""
    attack_ui_values = dict(label_value_rows(attack_ui_list))

    # Replace labels with internal dictionary keys and extract num attacks
    num_attacks = attack_ui_values.pop(COPIES_LABEL, 1) or 1
    attack_ui_values = {A_LABEL_TO_VAL[k]: v for k, v in attack_ui_values.items() if k in A_LABEL_TO_VAL}
    for key in DIE_MOD_LISTS:
        if key in attack_ui_values:
            attack_ui_values[key] = to_list(attack_ui_values[key])

    return attack_ui_values, int(num_attacks)

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
    "Level Up Preset": "preset",

    # Bonuses
    "Crit on": "crit_on",
    "Advantage": "advantage",
    "Disadvantage": "disadvantage",
    "Reroll Attack Die On": "attack_reroll_on",
    "Bonus Attack Mod": "bonus_attack_die_mod_list",
    "Bonus Damage Mod": "bonus_damage_die_mod_list",
    "Bonus Crit Mod": "bonus_crit_die_mod_list",
    "Bonus Miss Mod": "bonus_miss_die_mod_list",
    "Once Per Turn Damage": "once_per_turn_die_mod_list",
    "Once Per Turn Only On Crit": "once_per_turn_crit_only",
    "Once Per Turn Uses Per Fight (0 = unlimited)": "once_per_turn_uses_per_fight",
    "First Round Advantage": "first_round_advantage",
    "First Round Hits Are Crits": "first_round_auto_crit",
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
C_LABELS = {v: k for k, v in C_LABEL_TO_DICT_MAP.items()}

def extract_character_ui_values(character_from_ui):
    """ Parses the character ui values into a dictionary"""
    character_dict = {}
    # Extract values from the Stats and Bonuses tabs (the Attacks tab holds the attack editor, which reuses some labels)
    for tab in find_components(character_from_ui, 'Tab'):
        if tab['props']['label'] in ['Stats', 'Bonuses']:
            character_dict.update(label_value_rows(tab))
            for textarea in find_components(tab, 'Textarea'):
                character_dict["Description"] = textarea['props'].get('value') or ""

    # Convert labels to internal dictionary keys
    description = character_dict.pop("Description", "")
    character_dict = {C_LABEL_TO_DICT_MAP[k]: v for k, v in character_dict.items() if k in C_LABEL_TO_DICT_MAP}
    character_dict["description"] = description
    # Convert strs to lists
    for key in DIE_MOD_LISTS:
        character_dict[key] = to_list(character_dict.get(key))
    return character_dict


def characters_from_ui(characters_list, attack_stores):
    """ Parses the character ui values into a list of characters"""
    characters = []
    for ii, c in enumerate(characters_list):
        attacks = json.loads(attack_stores[ii])
        characters.append(Character.from_dict({**extract_character_ui_values(c), "attacks": attacks}))
    return characters

def label_row(label, component):
    """ A row with a label on the left and an input on the right, the structure is used to read values back """
    return dbc.Row([dbc.Col(dbc.Label(label, style=LABEL_STYLE)), dbc.Col(component)], class_name="label-row")

def number_row(label, value, min_, max_, step=1, **kwargs):
    return label_row(label, dbc.Input(type="number", value=value, min=min_, max=max_, step=step, style=INPUT_STYLE, size="sm", **kwargs))

def text_row(label, value, placeholder=None, **kwargs):
    return label_row(label, dbc.Input(type="text", value=value, placeholder=placeholder, style=INPUT_STYLE, size="sm", **kwargs))

def check_row(label, value):
    return label_row(label, dbc.Checkbox(value=bool(value)))

def select_row(label, value, options):
    return label_row(label, dbc.Select(options=options, value=value, style=INPUT_STYLE, size="sm"))

def section(title):
    return dbc.Row(html.H6(title, className="mt-2 mb-1 text-info"))

def collapsible_sections(sections, open_titles):
    """ Groups rows into collapsible sections, sections in open_titles start expanded """
    return dbc.Accordion(
        [dbc.AccordionItem(rows, title=title, item_id=title) for title, rows in sections],
        always_open=True, active_item=[t for t, _ in sections if t in open_titles], flush=True, class_name="card-sections mt-1")

def changed_sections(values, defaults, sections_fields):
    """ Titles of the sections where any field differs from its default, so edited sections are shown expanded """
    return {title for title, field_names in sections_fields.items() if any(values.get(f) != defaults.get(f) for f in field_names)}

COPIES_LABEL = "Copies to Add"

def set_attack_from_values(avals, i, index, num_attacks=1):
    """ Sets the attack ui from a dictionary of values"""
    defaults = Attack().to_dict()
    a = {**defaults, **avals[i]}
    sections = [
        ("Roll Modifiers", [
            number_row(A_LABELS["crit_on"], a["crit_on"], 2, 20),
            check_row(A_LABELS["proficent"], a["proficent"]),
            check_row(A_LABELS["advantage"], a["advantage"]),
            check_row(A_LABELS["disadvantage"], a["disadvantage"]),
            check_row(A_LABELS["always_hit"], a["always_hit"]),
            check_row(A_LABELS["always_crit"], a["always_crit"]),
        ]),
        ("Weapon", [
            number_row(A_LABELS["weapon_enhancement"], a["weapon_enhancement"], 0, 10),
            check_row(A_LABELS["offhand"], a["offhand"]),
            check_row(A_LABELS["two_handed"], a["two_handed"]),
            check_row(A_LABELS["heavy"], a["heavy"]),
        ]),
        ("Spell Saving Throw", [
            check_row(A_LABELS["saving_throw"], a["saving_throw"]),
            select_row(A_LABELS["saving_throw_stat"], a["saving_throw_stat"], stat_options),
            number_row(A_LABELS["saving_throw_success_multiplier"], a["saving_throw_success_multiplier"], 0, 1, step=0.5),
        ]),
        ("Extra Dice", [
            text_row(A_LABELS["bonus_attack_die_mod_list"], to_str(a["bonus_attack_die_mod_list"]), DICE_PLACEHOLDER),
            text_row(A_LABELS["bonus_damage_die_mod_list"], to_str(a["bonus_damage_die_mod_list"]), DICE_PLACEHOLDER),
            text_row(A_LABELS["bonus_crit_die_mod_list"], to_str(a["bonus_crit_die_mod_list"]), DICE_PLACEHOLDER),
            text_row(A_LABELS["bonus_miss_die_mod_list"], to_str(a["bonus_miss_die_mod_list"]), DICE_PLACEHOLDER),
        ]),
        ("Limits Per Fight", [
            check_row(A_LABELS["once_per_turn_eligible"], a["once_per_turn_eligible"]),
            number_row(A_LABELS["uses_per_fight"], a["uses_per_fight"], 0, 20, step=0.25),
            text_row(A_LABELS["fallback_for"], a["fallback_for"], placeholder="i.e. Fireball, made once it is used up"),
        ]),
    ]
    open_sections = changed_sections(a, defaults, {
        "Roll Modifiers": ["crit_on", "proficent", "advantage", "disadvantage", "always_hit", "always_crit"],
        "Weapon": ["weapon_enhancement", "offhand", "two_handed", "heavy"] if a["type"] != "spell" else [],
        "Spell Saving Throw": ["saving_throw"],
        "Extra Dice": DIE_MOD_LISTS[:4],
        "Limits Per Fight": ["once_per_turn_eligible", "uses_per_fight", "fallback_for"],
    })
    return [
        text_row(A_LABELS["name"], a["name"], id={"type": "attack_name", "index": index}),
        select_row(A_LABELS["type"], a["type"], attack_options),
        select_row(A_LABELS["ability_stat"], a["ability_stat"], stat_options),
        text_row(A_LABELS["damage"], a["damage"], placeholder="i.e. 2d6 or 1d4+1"),
        select_row(A_LABELS["damage_type"], a["damage_type"], damage_type_options),
        # Repeated Attacks, only used when adding
        number_row(COPIES_LABEL, num_attacks, 1, 20),
        collapsible_sections(sections, open_sections),
        ]

def generate_character_card(character_name, character=None, color="", index=1):
    """ Generates the character card, either from a character or with default values"""
    c = character or Character(name=character_name, attacks=[Attack(name="Attack Name")])
    card_style = {'height': '60vh', 'overflowY': 'auto'}

    # Stats tab
    stats = dbc.Card([
        dbc.CardBody([
            text_row(C_LABELS["name"], c.name, id={"type": "character name input", "index": index}),
            number_row(C_LABELS["level"], c.level, 1, 20, id={"type": "character level", "index": index}),
            *[number_row(C_LABELS[stat], getattr(c, stat), 1, 30) for stat in ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]],
            # DPR vs Level rebuilds preset characters at each level, clear it to only change the level
            text_row(C_LABELS["preset"], c.preset, placeholder="none (only level changes)"),
            dbc.Row([
                dbc.Textarea(value=c.description, placeholder="Optional Description", style={'width': '100%', 'minHeight': '10vh'}, class_name="mt-2"),
            ]),
        ])
    ], class_name="border-0")

    # Attacks tab
    avals = [a.to_dict() for a in c.attacks] or [Attack(name="Attack Name").to_dict()]

    attacks = dbc.Card([
        dbc.CardBody([
            html.Div("Click an attack to edit it, then Save. Add creates new copies of the values below.", className="small text-muted mb-1"),
            dbc.Row(dbc.ListGroup(
                [dbc.ListGroupItem(a["name"], active=ii == 0, action=True, id={"type": "attack", "index": index, "num": ii}) for ii, a in enumerate(avals)],
                id={"type": "attacks", "index": index}, numbered=True), class_name="mb-2"),
            dbc.Select(options=template_options, placeholder="Fill from weapon/spell...", size="sm", class_name="mb-2",
                       id={"type": "attack-template", "index": index}),
            html.Div(set_attack_from_values(avals, 0, index), id={"type": "attack_ui", "index": index}),
            dbc.ButtonGroup([
                dbc.Button([html.I(className="fa-solid fa-floppy-disk me-1"), "Save"], color="success", size="sm", title="Save changes to the selected attack", id={"type": "update-attack", "index": index}),
                dbc.Button([html.I(className="fa-solid fa-plus me-1"), "Add new"], color="primary", size="sm", title="Add the values above as new attack(s)", id={"type": "add-attack", "index": index}),
                dbc.Button([html.I(className="fa-solid fa-trash me-1"), "Delete"], color="danger", size="sm", title="Delete the selected attack", id={"type": "delete-attack", "index": index}),
            ], class_name="w-100 mt-2"),
            dcc.Store(id={"type": "attack_store", "index": index}, data=json.dumps(avals)), # Used to track attack data
        ]),
    ], class_name="border-0")

    # Bonuses, Feats and abilities tab, in collapsible sections (sections the character uses start expanded)
    bonus_sections = [
        ("Roll Modifiers", ["crit_on", "advantage", "disadvantage", "attack_reroll_on", "bonus_attack_die_mod_list", "bonus_damage_die_mod_list"], [
            number_row(C_LABELS["crit_on"], c.crit_on, 2, 20),
            check_row(C_LABELS["advantage"], c.advantage),
            check_row(C_LABELS["disadvantage"], c.disadvantage),
            number_row(C_LABELS["attack_reroll_on"], c.attack_reroll_on, 0, 19),
            text_row(C_LABELS["bonus_attack_die_mod_list"], to_str(c.bonus_attack_die_mod_list), "i.e. 1d4 (bless)"),
            text_row(C_LABELS["bonus_damage_die_mod_list"], to_str(c.bonus_damage_die_mod_list), "i.e. 1d6 (hex), 2"),
        ]),
        ("Crit and Miss Damage", ["bonus_crit_die_mod_list", "bonus_miss_die_mod_list"], [
            text_row(C_LABELS["bonus_crit_die_mod_list"], to_str(c.bonus_crit_die_mod_list), DICE_PLACEHOLDER),
            text_row(C_LABELS["bonus_miss_die_mod_list"], to_str(c.bonus_miss_die_mod_list), DICE_PLACEHOLDER),
        ]),
        ("Once Per Turn (Sneak Attack, Smite)", ["once_per_turn_die_mod_list", "once_per_turn_crit_only", "once_per_turn_uses_per_fight"], [
            text_row(C_LABELS["once_per_turn_die_mod_list"], to_str(c.once_per_turn_die_mod_list), "i.e. 3d6 (sneak attack)"),
            check_row(C_LABELS["once_per_turn_crit_only"], c.once_per_turn_crit_only),
            number_row(C_LABELS["once_per_turn_uses_per_fight"], c.once_per_turn_uses_per_fight, 0, 20, step=0.25),
        ]),
        ("First Round of a Fight", ["first_round_advantage", "first_round_auto_crit"], [
            check_row(C_LABELS["first_round_advantage"], c.first_round_advantage),
            check_row(C_LABELS["first_round_auto_crit"], c.first_round_auto_crit),
        ]),
        ("Feats", ["GWM", "savage_attacker", "sharpshooter", "tavern_brawler"], [
            check_row(C_LABELS["GWM"], c.GWM),
            check_row(C_LABELS["savage_attacker"], c.savage_attacker),
            check_row(C_LABELS["sharpshooter"], c.sharpshooter),
            check_row(C_LABELS["tavern_brawler"], c.tavern_brawler),
        ]),
        ("Fighting Styles", ["GWF", "archery", "dueling", "TWF"], [
            check_row(C_LABELS["GWF"], c.GWF),
            check_row(C_LABELS["archery"], c.archery),
            check_row(C_LABELS["dueling"], c.dueling),
            check_row(C_LABELS["TWF"], c.TWF),
        ]),
        ("Class and Race Features", ["raging", "brutal_critical", "divine_smite", "divine_smite_level", "improved_divine_smite", "empowered_evocation",
                                     "agonizing_blast", "lifedrinker", "elemental_affinity", "savage_attacks_half_orc"], [
            section("Barbarian"),
            check_row(C_LABELS["raging"], c.raging),
            check_row(C_LABELS["brutal_critical"], c.brutal_critical),
            section("Paladin"),
            check_row(C_LABELS["divine_smite"], c.divine_smite),
            number_row(C_LABELS["divine_smite_level"], c.divine_smite_level, 1, 5),
            check_row(C_LABELS["improved_divine_smite"], c.improved_divine_smite),
            section("Wizard"),
            check_row(C_LABELS["empowered_evocation"], c.empowered_evocation),
            section("Warlock"),
            check_row(C_LABELS["agonizing_blast"], c.agonizing_blast),
            check_row(C_LABELS["lifedrinker"], c.lifedrinker),
            section("Sorcerer"),
            check_row(C_LABELS["elemental_affinity"], c.elemental_affinity),
            section("Half-Orc"),
            check_row(C_LABELS["savage_attacks_half_orc"], c.savage_attacks_half_orc),
        ]),
    ]
    defaults = Character()
    open_sections = {"Roll Modifiers"} | changed_sections(vars(c), vars(defaults), {title: fields for title, fields, _ in bonus_sections})
    bonuses = dbc.Card([
        dbc.CardBody([
            html.Div("Effects the simulator models directly. Expanded sections are the ones this character uses.", className="small text-muted"),
            collapsible_sections([(title, rows) for title, _, rows in bonus_sections], open_sections),
        ], class_name="p-1")
    ], class_name="border-0")

    return dbc.Col(
        dbc.Card([
            dbc.CardHeader(dbc.Row([
                dbc.Col(html.H5(c.name, style={'color': color, 'whiteSpace': 'nowrap'}, className="mb-0", id={"type": "character name", "index": index}), style={'overflowX': 'auto'}, class_name="pe-0"),
                # html.Button rather than dbc.Button since n_clicks_timestamp is needed to tell real clicks from cards being added/removed
                dbc.Col([html.Button(html.I(className="fa-solid fa-copy"), className="btn btn-primary btn-sm me-1", title="Copy character", id={"type": "copy character", "index": index}),
                         html.Button(html.I(className="fa-solid fa-x"), className="btn btn-danger btn-sm", title="Delete character", id={"type": "delete character", "index": index}),
                         ], width="auto", class_name="d-flex align-items-center")
            ], align="center", class_name="g-1"), style={'borderTop': f'3px solid {color}'}),
            dbc.CardBody([
                dbc.Tabs([
                    dbc.Tab(stats, label="Stats", tab_id="stats"),
                    dbc.Tab(attacks, label="Attacks", tab_id="attacks"),
                    dbc.Tab(bonuses, label="Bonuses", tab_id="bonuses"),
                ], active_tab="stats"),
            ], class_name="p-1"),
        ], style=card_style),
    xs=12, md=6, xl=3, id={"type": "character card", "index": index}, class_name="mb-2")

# Fields that must be numbers, everything else can be blank
NUMERIC_CHARACTER_FIELDS = ["level", "strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma", "crit_on", "attack_reroll_on", "divine_smite_level"]
NUMERIC_ATTACK_FIELDS = ["crit_on", "weapon_enhancement", "saving_throw_success_multiplier"]

def _dice_problems(values, label):
    try:
        multiple_die_and_mod_from_list(values or [])
        return []
    except (ValueError, AttributeError):
        return [f"{label} '{to_str(values)}' should be dice or numbers like 1d6, 2"]

def validation_errors(character_dict, attacks):
    """ Readable problems with a character's values, i.e. "Strength is empty", empty if everything can be simulated """
    problems = [f"{C_LABELS[f]} is empty" for f in NUMERIC_CHARACTER_FIELDS if f in character_dict and character_dict[f] is None]
    for key in DIE_MOD_LISTS:
        problems += _dice_problems(character_dict.get(key), C_LABELS[key])
    if not attacks:
        problems.append("it has no attacks")
    for a in attacks:
        name = a.get("name") or "an attack"
        problems += [f"attack '{name}': {A_LABELS[f]} is empty" for f in NUMERIC_ATTACK_FIELDS if f in a and a[f] is None]
        problems += [f"attack '{name}': {p}" for key in DIE_MOD_LISTS[:4] for p in _dice_problems(a.get(key), A_LABELS[key])]
        problems += [f"attack '{name}': {p}" for p in _dice_problems([a.get("damage") or ""], A_LABELS["damage"])]
    return problems
