""" Callbacks for the app, which are registered in app.py. Clientside callbacks are located in assets/callbacks.js"""
import json
import base64
from copy import deepcopy
import pandas as pd
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from dash import dcc, html, Input, Output, State, Patch, MATCH, ALL, ctx, clientside_callback, ClientsideFunction, no_update
from computations.analytic import attack_breakdown, expected_damage_per_round, power_attack_insights
from computations.models import Character, Enemy
from computations.numerical_simulation import simulate_rounds_from_characters, set_seed, simulate_rounds_to_kill, simulate_fights
from game_data import attacks_from_template, enemy_from_preset
from game_data.classes import build_character

from utilities.helper_functions import timeit
from components.callback_helpers import (get_active_ids_and_new_id, get_new_id, set_active_ids, try_and_except_alert, reformat_df_ac, alert,
                                         button_was_clicked, new_card_click, reset_clicks, replace_card_index_and_color, per_attack_ac_tables,
                                         rename_card, unique_name)
from components.plots import (COLORS, generate_plot_data, add_tables, summary_stats, generate_line_plots, generate_damage_per_attack_histogram,
                              build_tables_row, build_leaderboard, build_breakdown_tables, generate_rounds_to_kill_plot, rounds_to_kill_summary,
                              build_sweep_leaderboard, build_insights, generate_fight_plot, fight_summary, fight_export,
                              results_summary)
from components.help import GRAPH_DESCRIPTIONS
from components.character_card import (generate_character_card, set_attack_from_values, extract_attack_ui_values, extract_character_ui_values, characters_from_ui,
                                       label_value_rows, validation_errors, character_dict_from_labels)
from components.enemy_card import extract_enemy_ui_values, generate_enemy_card_body, enemy_dict_from_labels
from components.variants import make_variant
from components.sweeps import SWEEP_PARAMETERS, run_sweep
from components.session import SETTINGS_IDS, describe_session, make_session, parse_session
from components.bg3_planner import (DEFAULT_PARTY, MAX_PARTY_SIZE, conditional_options, conflicts_list, dpr_table, gear_highlights,
                                    inherited_placeholders)
from bg3.build import ACT_KEYS, Bg3Build, compile_build
from bg3.checkpoints import ACTS, act_level
from bg3.party import party_conflicts
from bg3.presets import PRESETS
from game_data.classes import BUILDS

MAX_CHARACTERS = min(8, len(COLORS)) # There are 10 colors and 4 characters fit per row, so 8 is a good max
ARMOR_CLASSES = range(10, 26)
MAX_ROUNDS_TO_KILL = 20
DEFAULT_ROUNDS_PER_FIGHT = 3

def parse_simulation_inputs(num_rounds, attack_stores, characters_list, enemy_card_body, numerical_options):
    """ Shared validation for simulate and export. Returns (characters, enemy, rng, alert) """
    # Randomize Seed
    rng = set_seed(None if 1 in (numerical_options or []) else 1)

    # Check number of rounds is valid
    if not num_rounds or num_rounds < 1:
        return None, None, rng, alert("Invalid Number of Rounds")

    # Check each character's values first, so problems can be reported by name and field
    problems = []
    for ii, c in enumerate(characters_list):
        values = extract_character_ui_values(c)
        issues = validation_errors(values, json.loads(attack_stores[ii]))
        if issues:
            problems.append(html.Li([html.B(values.get("name") or f"Character {ii + 1}"), ": " + "; ".join(issues)]))
    if problems:
        return None, None, rng, alert(["Please fix these before simulating:", html.Ul(problems, className="mb-0")], color="warning")

    # Parse characters
    characters, error = try_and_except_alert(
        "Could not parse characters, please check that all fields are filled out correctly",
        characters_from_ui, characters_list, attack_stores)
    if error is not None:
        return None, None, rng, error

    # Character names should be unique, or else data analysis gets misleading
    if len({c.name for c in characters}) != len(characters):
        return None, None, rng, alert("Characters names must be unique")

    # Parse enemy
    enemy_values = extract_enemy_ui_values(enemy_card_body)
    empty = [label for label, value in label_value_rows(enemy_card_body) if value is None and label not in ("Resistances", "Vulnerabilities", "Immunities")]
    if empty:
        return None, None, rng, alert(f"Please fill in the enemy's {', '.join(empty)}", color="warning")
    enemy, error = try_and_except_alert(
        "Could not parse enemy, please check that all fields are filled out correctly",
        lambda: Enemy.from_dict(enemy_values))
    return characters, enemy, rng, error

# Sweep graph/export types: by round (DPR) or by attack (DPA), the swept parameter is chosen separately
SWEEPS = {"DPR Sweep": True, "DPA Sweep": False}

def dpa_vs_ac_tables(df_acs, order, x_col='Armor Class'):
    """ One table per character with a column group per attack """
    data_summary = []
    for c_name in order:
        df_c = df_acs.loc[df_acs['Character'] == c_name, :]
        c_summary = []
        for n, g in df_c.groupby('Character-Attack', sort=False):
            g = g.copy()
            g["mean"] = g["mean"].astype(float).round(2)
            attack_name = n[len(c_name)+1:]
            reshaped = pd.concat({attack_name: g.set_index(x_col).drop(['Character-Attack', 'Character'], axis=1).T})
            c_summary.append(reshaped.T)
        data_summary.append(pd.concat(c_summary, axis=1))
    return data_summary

# Note: Intellisense is not recognizing the callbacks as being accessed
def register_callbacks(app, sidebar=True, template='plotly_dark'): # pylint: disable=too-many-statements
    """ Registers all callbacks for the app"""
    if sidebar:
        clientside_callback(
            ClientsideFunction(
                namespace="clientside",
                function_name="toggle_classname"
            ),
            Output("sidebar", "className"),
            Input("sidebar-toggle", "n_clicks"),
            State("sidebar", "className"),
        )

        clientside_callback(
            ClientsideFunction(
                namespace="clientside",
                function_name="toggle_collapse"
            ),
            Output("collapse", "is_open"),
            Input("navbar-toggle", "n_clicks"),
            State("collapse", "is_open"),
        )

    def append_cards(characters, active_ids_json):
        """ Appends character cards using the first deleted ids, returns the patch, new active ids and an alert if full """
        patched_children = Patch()
        active_ids, new_id = get_active_ids_and_new_id(active_ids_json)
        warning = None
        for ii, character in enumerate(characters):
            # Don't add more than max characters
            if new_id >= MAX_CHARACTERS:
                warning = alert(f"Max of {MAX_CHARACTERS} characters reached" + (f", only added {ii}" if ii else ""), color="warning")
                break
            patched_children.append(generate_character_card(character.name, character=character, color=COLORS[new_id], index=new_id))
            active_ids.append(new_id)
            new_id = get_new_id(active_ids)
        return patched_children, set_active_ids(active_ids), warning

    @app.callback(
        Output("character_row", "children"),
        Output("active_ids", "data"),
        Output("character-alerts", "children", allow_duplicate=True),
        Input("add_character_button", "n_clicks"),
        State("character_name", "value"),
        State("active_ids", "data"),
        prevent_initial_call=True
    )
    @timeit
    def add_character(n_clicks, name, active_ids_json):
        # Don't update without a name or without a button click
        if not name or not n_clicks:
            raise PreventUpdate
        return append_cards([Character(name=name, attacks=[])], active_ids_json)

    @app.callback(
        Output("character_row", "children", allow_duplicate=True),
        Output("active_ids", "data", allow_duplicate=True),
        Output("character-alerts", "children", allow_duplicate=True),
        Input("add-preset-button", "n_clicks"),
        State("preset-build", "value"),
        State("preset-level", "value"),
        State("ruleset", "value"),
        State("active_ids", "data"),
        prevent_initial_call=True
    )
    @timeit
    def add_preset_character(n_clicks, build_key, level, ruleset, active_ids_json):
        if not n_clicks or not build_key:
            raise PreventUpdate
        return append_cards([build_character(build_key, level or 1, ruleset or "bg3")], active_ids_json)

    # Call client side callback in javascript, found in assets/callbacks.js
    clientside_callback(
        ClientsideFunction(
            namespace="clientside",
            function_name="update_name"
        ),
        Output({'type': 'character name', "index": MATCH}, "children"),
        Input({'type': 'character name input', "index": MATCH}, "value"),
        prevent_initial_call=True
    )

    clientside_callback(
        ClientsideFunction(
            namespace="clientside",
            function_name="update_name"
        ),
        Output("enemy-name", "children"),
        Input("enemy-name-input", "value"),
        prevent_initial_call=True
    )

    @app.callback(
            Output("character_row", "children", allow_duplicate=True),
            Output("active_ids", "data", allow_duplicate=True),
            Output("last-card-click", "data", allow_duplicate=True),
            Input({'type': 'delete character', "index": ALL}, "n_clicks_timestamp"), # Unfortunately MATCH doesn't work since there is no corresponding MATCH in the outputs
            State("active_ids", "data"),
            State("last-card-click", "data"),
            prevent_initial_call=True
    )
    @timeit
    def delete_character(timestamps, active_ids_json, last_handled):
        # Callbacks with ALL also fire when cards are added or removed, so check this is a new click
        clicked_at = new_card_click(timestamps, last_handled)
        if clicked_at is None:
            raise PreventUpdate
        active_ids, _ = get_active_ids_and_new_id(active_ids_json)
        # Don't delete the last character
        if len(active_ids) == 1:
            raise PreventUpdate

        # Delete the character and update, active ids are in the same order as the cards
        index = active_ids.index(ctx.triggered_id["index"])
        patched_children = Patch()
        del patched_children[index]
        del active_ids[index]

        return patched_children, set_active_ids(active_ids), clicked_at

    @app.callback(
        Output("character_row", "children", allow_duplicate=True),
        Output("active_ids", "data", allow_duplicate=True),
        Output("character-alerts", "children", allow_duplicate=True),
        Output("last-card-click", "data", allow_duplicate=True),
        Input({'type': 'copy character', "index": ALL, "variant": ALL}, "n_clicks_timestamp"),
        State("character_row", "children"),
        State({'type': 'attack_store', "index": ALL}, "data"),
        State("active_ids", "data"),
        State("last-card-click", "data"),
        prevent_initial_call=True
    )
    @timeit
    def copy_character(timestamps, characters, attack_stores, active_ids_json, last_handled):
        """ Copies a card as is, or as a variant with one change (see components/variants.py) """
        clicked_at = new_card_click(timestamps, last_handled)
        if clicked_at is None:
            raise PreventUpdate

        copy_id, variant = ctx.triggered_id["index"], ctx.triggered_id["variant"]
        active_ids, new_id = get_active_ids_and_new_id(active_ids_json)
        # Don't add more than max characters
        if new_id >= MAX_CHARACTERS:
            return Patch(), active_ids_json, alert(f"Max of {MAX_CHARACTERS} characters reached", color="warning"), clicked_at

        position = active_ids.index(copy_id)
        existing_names = {extract_character_ui_values(c)["name"] for c in characters}
        if variant == "copy":
            # Copy the existing card, including unsaved edits, and replace its id, color, name and button clicks
            character = replace_card_index_and_color(reset_clicks(characters[position]), copy_id, new_id, COLORS[new_id])
            character = rename_card(character, unique_name(extract_character_ui_values(character)["name"], existing_names))
        else:
            values = extract_character_ui_values(characters[position])
            issues = validation_errors(values, json.loads(attack_stores[position]))
            if issues:
                return Patch(), active_ids_json, alert(f"Please fix {values.get('name')} before copying: " + "; ".join(issues), color="warning"), clicked_at
            original, error = try_and_except_alert("Could not copy the character", characters_from_ui, [characters[position]], [attack_stores[position]])
            if error is not None:
                return Patch(), active_ids_json, error, clicked_at
            try:
                variant_character = make_variant(original[0], variant)
            except ValueError as e:
                return Patch(), active_ids_json, alert(str(e), color="warning"), clicked_at
            if variant_character.name in existing_names:
                variant_character.name = unique_name(variant_character.name, existing_names)
            character = generate_character_card(variant_character.name, character=variant_character, color=COLORS[new_id], index=new_id)

        patched_children = Patch()
        patched_children.append(character)
        active_ids.append(new_id)

        return patched_children, set_active_ids(active_ids), None, clicked_at

    @app.callback(
        Output("enemy-values", "data"),
        Input({'type': 'enemy field', "field": ALL}, "value"),
    )
    def enemy_values(values):
        """ The enemy as a dictionary, or None if a field is empty. Callbacks with a MATCH output aren't triggered by
            pattern matching inputs without the MATCH key, so the expected damage badges use this instead """
        enemy_dict = enemy_dict_from_labels((i["id"]["field"], v) for i, v in zip(ctx.inputs_list[0], values))
        if any(v is None for k, v in enemy_dict.items() if k not in ("resistances", "vulnerabilities", "immunities")):
            return None
        return enemy_dict

    @app.callback(
        Output({'type': 'dpr badge', "index": MATCH}, "children"),
        Input({'type': 'character field', "index": MATCH, "field": ALL}, "value"),
        Input({'type': 'character level', "index": MATCH}, "value"),
        Input({'type': 'attack_store', "index": MATCH}, "data"),
        Input("enemy-values", "data"),
        Input("rounds-per-fight", "value"),
    )
    def expected_damage_badge(field_values, level, avals, enemy_dict, rounds_per_fight):
        """ Exact expected damage per round against the current enemy, updated as the card is edited """
        labels = [i["id"]["field"] for i in ctx.inputs_list[0]]
        character_dict = {**character_dict_from_labels(dict(zip(labels, field_values))), "level": level}
        attacks = json.loads(avals)
        problems = validation_errors(character_dict, attacks)
        if problems or not enemy_dict:
            return html.Span("Expected damage: check the inputs (hover for details)", title="; ".join(problems) or "The enemy has empty fields")
        try:
            character = Character.from_dict({**character_dict, "attacks": attacks})
            dpr = expected_damage_per_round(character, Enemy.from_dict(enemy_dict), rounds_per_fight or DEFAULT_ROUNDS_PER_FIGHT)
        except Exception as e: # pylint: disable=broad-exception-caught
            return html.Span("Expected damage: check the inputs (hover for details)", title=str(e))
        return [html.B(f"{dpr:.1f}", className="text-light"), " expected damage per round"]

    ## Attacks

    @app.callback(
        Output({'type': 'attack', "index": MATCH, "num": ALL}, "active"),
        Output({'type': 'attack_ui', "index": MATCH}, "children"),
        Input({'type': 'attack', "index": MATCH, "num": ALL}, "n_clicks"),
        State({'type': 'attack_store', "index": MATCH}, "data"),
        prevent_initial_call=True
    )
    @timeit
    def select_attack(_, avals):
        if not button_was_clicked():
            raise PreventUpdate

        # Update actively selected attacks, the store is in the same order as the list
        nums = [i["id"]["num"] for i in ctx.inputs_list[0]]
        selected = nums.index(ctx.triggered_id["num"])
        attacks = [selected == ii for ii in range(len(nums))]

        # Update attack ui to match the values of the selected attack
        attack_ui = set_attack_from_values(json.loads(avals), selected, ctx.triggered_id['index'])

        return attacks, attack_ui

    @app.callback(
        Output({'type': 'attack_store', "index": MATCH}, "data"),
        Output({'type': 'attacks', "index": MATCH}, "children"),
        Input({"type": "add-attack", "index": MATCH}, "n_clicks"),
        State({"type": "attack_ui", "index": MATCH}, "children"),
        State({'type': 'attack_store', "index": MATCH}, "data"),
        State({'type': 'attacks', "index": MATCH}, "children"),
        prevent_initial_call=True
    )
    @timeit
    def add_attack(n_clicks, attack_ui_list, avals, existing_attacks):
        if not n_clicks:
            raise PreventUpdate

        # Get values from UI update attack store
        new_attack, num_attacks = extract_attack_ui_values(attack_ui_list)

        # Append to existing attack store
        avals_updated = json.loads(avals)
        avals_updated.extend(dict(new_attack) for _ in range(num_attacks))

        # Update UI attack list
        attacks_updated = existing_attacks or []
        nums = [int(a["props"]["id"]["num"]) for a in attacks_updated]
        index = ctx.triggered_id["index"]
        for _ in range(num_attacks):
            jj = get_new_id(nums)
            nums.append(jj)
            attacks_updated.append(dbc.ListGroupItem(new_attack["name"], active=False, action=True, id={"type": "attack", "index": index, "num": jj}))

        return json.dumps(avals_updated), attacks_updated

    @app.callback(
        Output({'type': 'attack_store', "index": MATCH}, "data", allow_duplicate=True),
        Output({'type': 'attacks', "index": MATCH}, "children", allow_duplicate=True),
        Input({"type": "update-attack", "index": MATCH}, "n_clicks"),
        State({"type": "attack_ui", "index": MATCH}, "children"),
        State({'type': 'attack_store', "index": MATCH}, "data"),
        State({'type': 'attacks', "index": MATCH}, "children"),
        State({'type': 'attack', "index": MATCH, "num": ALL}, "active"),
        prevent_initial_call=True
    )
    @timeit
    def update_attack(n_clicks, attack_ui_list, avals, existing_attacks, active_attacks):
        """ Saves the edited values to the selected attack """
        selected = [ii for ii, a in enumerate(active_attacks) if a]
        if not n_clicks or len(selected) != 1:
            raise PreventUpdate
        selected = selected[0]
        new_values, _ = extract_attack_ui_values(attack_ui_list)
        avals_updated = json.loads(avals)
        avals_updated[selected] = {**avals_updated[selected], **new_values}
        existing_attacks[selected]["props"]["children"] = new_values["name"]
        return json.dumps(avals_updated), existing_attacks

    @app.callback(
        Output({'type': 'attack_store', "index": MATCH}, "data", allow_duplicate=True),
        Output({'type': 'attacks', "index": MATCH}, "children", allow_duplicate=True),
        Input({"type": "delete-attack", "index": MATCH}, "n_clicks"),
        State({'type': 'attack_store', "index": MATCH}, "data"),
        State({'type': 'attacks', "index": MATCH}, "children"),
        State({'type': 'attack', "index": MATCH, "num": ALL}, "active"),
        prevent_initial_call=True
    )
    @timeit
    def delete_attack(n_clicks, avals, existing_attacks, active_attacks):
        if not n_clicks:
            raise PreventUpdate

        # Delete the actively selected attack
        attack_index = [ii for ii, a in enumerate(active_attacks) if a is True]
        if len(attack_index) != 1:
            raise PreventUpdate
        attack_index = attack_index[0]

        # Delete from store and UI
        avals_updated = json.loads(avals)
        del avals_updated[attack_index]
        del existing_attacks[attack_index]

        return json.dumps(avals_updated), existing_attacks

    @app.callback(
        Output({'type': 'attack_ui', "index": MATCH}, "children", allow_duplicate=True),
        Input({'type': 'attack-template', "index": MATCH}, "value"),
        State({'type': 'attack_ui', "index": MATCH}, "children"),
        State({'type': 'character level', "index": MATCH}, "value"),
        State("ruleset", "value"),
        prevent_initial_call=True
    )
    @timeit
    def apply_attack_template(template, attack_ui_list, level, ruleset):
        """ Fills the attack editor from the weapon/spell database, add or save it afterwards """
        if not template:
            raise PreventUpdate
        current, _ = extract_attack_ui_values(attack_ui_list)
        attacks = attacks_from_template(template, ability_stat=current.get("ability_stat"), character_level=level or 1, ruleset=ruleset or "bg3")
        # Keep the bonus dice the user already entered
        values = {**attacks[0].to_dict(), **{k: v for k, v in current.items() if k.startswith("bonus_") and v}}
        return set_attack_from_values([values], 0, ctx.triggered_id["index"], num_attacks=len(attacks))

    @app.callback(
        Output("sweep-description", "children"),
        Input("sweep-parameter", "value"),
    )
    def describe_sweep(parameter):
        return SWEEP_PARAMETERS[parameter][2] if parameter in SWEEP_PARAMETERS else ""

    @app.callback(
        Output("enemy-card-body", "children"),
        Output("enemy-name", "children", allow_duplicate=True),
        Input("enemy-preset", "value"),
        prevent_initial_call=True
    )
    def load_enemy_preset(preset):
        if not preset:
            raise PreventUpdate
        enemy = enemy_from_preset(preset)
        return generate_enemy_card_body(enemy), enemy.name

    SETTINGS_STATES = [State(component_id, "value") for component_id in SETTINGS_IDS.values()]

    def session_outputs(characters, enemy, settings):
        """ Replaces every character, the enemy (if any) and settings (if given) with a loaded session """
        characters = characters[:MAX_CHARACTERS]
        cards = [generate_character_card(c.name, character=c, color=COLORS[ii], index=ii) for ii, c in enumerate(characters)]
        enemy_outputs = (generate_enemy_card_body(enemy), enemy.name) if enemy is not None else (no_update, no_update)
        setting_values = tuple(settings.get(key, no_update) for key in SETTINGS_IDS)
        return (cards, set_active_ids(list(range(len(characters)))), *enemy_outputs, *setting_values)

    SESSION_OUTPUTS = [
        Output('character_row', 'children', allow_duplicate=True),
        Output('active_ids', 'data', allow_duplicate=True),
        Output("enemy-card-body", "children", allow_duplicate=True),
        Output("enemy-name", "children", allow_duplicate=True),
        *[Output(component_id, "value", allow_duplicate=True) for component_id in SETTINGS_IDS.values()],
    ]
    NO_SESSION_CHANGE = (no_update,) * len(SESSION_OUTPUTS)

    @app.callback(
            Output('download-characters', 'data'),
            Input('export-button', 'n_clicks'),
            State("character_row", "children"),
            State({"type": "attack_store", "index": ALL}, "data"),
            State("enemy-card-body", "children"),
            *SETTINGS_STATES,
            prevent_initial_call=True
    )
    @timeit
    def export_session(clicked, characters_ui, attack_stores, enemy_card_body, *settings):
        """ Exports the characters, enemy and simulator settings to a json file that Import loads back """
        if not clicked:
            raise PreventUpdate

        c_dicts = []
        for ii, c in enumerate(characters_ui):
            c_dict = extract_character_ui_values(c)
            c_dict["attacks"] = json.loads(attack_stores[ii])
            c_dicts.append(c_dict)
        session = make_session(c_dicts, extract_enemy_ui_values(enemy_card_body), dict(zip(SETTINGS_IDS, settings)))
        return dict(content=json.dumps(session, indent=4), filename="dnd_session.json")

    @app.callback(
            *SESSION_OUTPUTS,
            Output('character-alerts', 'children'),
            Input('upload-button', 'contents'),
            State("active_ids", "data"),
            prevent_initial_call=True
    )
    @timeit
    def import_session(contents, active_ids_json):
        """ Loads a session file (replacing everything) or adds the characters of an older characters only file """
        if contents is None:
            raise PreventUpdate

        content_type, content_string = contents.split(',')
        if 'json' not in content_type:
            return *NO_SESSION_CHANGE, alert("Import Failed. Only json files are supported")
        try:
            data = json.loads(base64.b64decode(content_string).decode('utf-8'))
        except Exception as e:
            print(e)
            return *NO_SESSION_CHANGE, alert("Import Failed. Cannot parse json file")

        characters, enemy, settings, error = parse_session(data)
        if isinstance(data, dict) and "characters" in data:
            if not characters:
                return *NO_SESSION_CHANGE, alert(error or "Import Failed. The session has no characters")
            message = alert(error, color="warning") if error else alert(f"Loaded session: {describe_session(data)}", color="success")
            return *session_outputs(characters, enemy, settings), message

        # Older exports are a list of characters, which are added to the current ones
        patched_children, active_ids, warning = append_cards(characters, active_ids_json)
        return patched_children, active_ids, *NO_SESSION_CHANGE[2:], (alert(error) if error else warning)

    @app.callback(
        Output("restore-banner", "is_open"),
        Output("restore-text", "children"),
        Input("url", "pathname"),
        State("saved-session", "data"),
    )
    def offer_restore(_, saved_session):
        """ Offers to restore the session saved in this browser by the last simulation """
        if not saved_session or not saved_session.get("characters"):
            return False, ""
        return True, f"Your last session is saved in this browser ({describe_session(saved_session)})."

    @app.callback(
        *SESSION_OUTPUTS,
        Output("restore-banner", "is_open", allow_duplicate=True),
        Output("character-alerts", "children", allow_duplicate=True),
        Input("restore-session-button", "n_clicks"),
        State("saved-session", "data"),
        prevent_initial_call=True
    )
    def restore_session(n_clicks, saved_session):
        if not n_clicks or not saved_session:
            raise PreventUpdate
        characters, enemy, settings, error = parse_session(saved_session)
        if not characters:
            return *NO_SESSION_CHANGE, False, alert(error or "Could not restore the last session")
        return *session_outputs(characters, enemy, settings), False, (alert(error, color="warning") if error else None)

    # NOTE: Using a data store caused memory issues in the deployed environment on heroku, often exceeding 1 GB and there is a 0.5 GB limit, resimulating is faster
    @app.callback(
        Output("graph-description", "children"),
        Output("sweep-controls", "style"),
        Input("simulate-type", "value"),
    )
    def describe_graph(simulate_type):
        return GRAPH_DESCRIPTIONS.get(simulate_type, ""), {"display": "block" if simulate_type in SWEEPS else "none"}

    @app.callback(
        Output("ui-prefs", "data"),
        Input("quick-start-toggle", "n_clicks"),
        State("ui-prefs", "data"),
        prevent_initial_call=True
    )
    def toggle_quick_start(n_clicks, prefs):
        prefs = prefs or {}
        return {**prefs, "quick_start_open": not prefs.get("quick_start_open", True)}

    @app.callback(
        Output("quick-start-collapse", "is_open"),
        Output("quick-start-toggle", "children"),
        Input("ui-prefs", "data"),
    )
    def show_quick_start(prefs):
        is_open = (prefs or {}).get("quick_start_open", True)
        return is_open, "Hide" if is_open else "Show"

    # Bring the results into view when a simulation finishes, i.e. after using the floating simulate button
    clientside_callback(
        """function(figure) {
            const results = document.getElementById("results-summary");
            if (results) { results.scrollIntoView({behavior: "smooth", block: "start"}); }
            return window.dash_clientside.no_update;
        }""",
        Output("scroll-dummy", "data"),
        Input("dist-plot", "figure"),
        prevent_initial_call=True
    )

    @app.callback(
        Output('dist-plot', "figure"),
        Output('damage-tables', "children"),
        Output('simulate-alerts', "children"),
        Output("simulate-spinner", "children"),
        Output("results-summary", "children"),
        Output("saved-session", "data"),
        Input("simulate-button", "n_clicks"),
        Input("simulate-float", "n_clicks"),
        State("simulate-input", "value"),
        State({'type': 'attack_store', "index": ALL}, "data"),
        State("character_row", "children"),
        State("enemy-card-body", "children"),
        State("simulate-type", "value"),
        State("numerical-options", "value"),
        State("ruleset", "value"),
        State("sweep-parameter", "value"),
        State("rounds-per-fight", "value"),
        prevent_initial_call=True
    )
    @timeit
    def simulate(clicked, float_clicked, num_rounds, attack_stores, characters_list, enemy_card_body, simulate_type, numerical_options, ruleset, sweep_parameter, rounds_per_fight):
        if not clicked and not float_clicked:
            raise PreventUpdate

        # Default Outputs
        fig = Patch()
        tables = Patch()
        spinner = "Simulate!"
        summary = None

        characters, enemy, rng, error = parse_simulation_inputs(num_rounds, attack_stores, characters_list, enemy_card_body, numerical_options)
        if error is not None:
            return fig, tables, error, spinner, summary, no_update
        # Remember the session in this browser, so it can be restored after a reload
        session = make_session(characters, enemy, {"num_rounds": num_rounds, "rounds_per_fight": rounds_per_fight, "graph": simulate_type,
                                                   "sweep_parameter": sweep_parameter, "ruleset": ruleset})

        rounds_per_fight = max(int(rounds_per_fight or DEFAULT_ROUNDS_PER_FIGHT), 1)
        breakdown = build_breakdown_tables(characters, [attack_breakdown(c, enemy, rounds_per_fight) for c in characters])
        error_message = "Could not simulate combat, please check that all fields are filled out correctly"

        # Simulate
        if simulate_type in ["DPR Distribution", "DPA Distribution"]:
            res, error = try_and_except_alert(error_message, simulate_rounds_from_characters, characters, enemy, num_rounds=num_rounds, save_memory=True, rng=rng,
                                              rounds_per_fight=rounds_per_fight)
            if error is not None:
                return fig, tables, error, spinner, summary, session

            dfs, df_by_rounds, df_by_attacks = res
            leaderboard = build_leaderboard(characters, df_by_rounds, rounds_per_fight)
            summary = results_summary({c.name: df["Damage"].mean() for c, df in zip(characters, df_by_rounds)}, "damage per round", context=f"against {enemy.name}.")
            if simulate_type == "DPR Distribution":
                fig = generate_plot_data(characters, df_by_rounds, template=template, title="Damage Per Round Distribution")
                tables = leaderboard + add_tables(df_by_rounds, characters, by_round=True, width=3) + breakdown
            elif simulate_type == "DPA Distribution":
                fig = generate_damage_per_attack_histogram(characters, dfs, template=template, title="Damage Per Attack Distribution")
                tables = leaderboard + add_tables(df_by_attacks, characters, by_round=False, width=3) + breakdown
        elif simulate_type in SWEEPS:
            x_col, by_round = sweep_parameter, SWEEPS[simulate_type]
            df_acs, error = try_and_except_alert(error_message, run_sweep, characters, enemy, x_col, by_round=by_round, ruleset=ruleset, num_rounds=num_rounds, rng=rng,
                                                 rounds_per_fight=rounds_per_fight)
            if error is not None:
                return fig, tables, error, spinner, summary, session

            groupby = "Character" if by_round else "Character-Attack"
            order = [c.name for c in characters]
            fig = generate_line_plots(df_acs, template=template, groupby=groupby, order=order, x_col=x_col)
            leaderboard = build_sweep_leaderboard(df_acs, x_col, order) if by_round else []
            averages = df_acs.groupby(["Character", x_col])["mean"].sum().groupby("Character").mean()
            summary = results_summary({name: averages[name] for name in order if name in averages}, f"average damage per round over {x_col} {df_acs[x_col].min()} to {df_acs[x_col].max()}")
            insights = []
            if x_col == "Armor Class":
                insights = build_insights([i for c in characters for i in power_attack_insights(c, enemy, ARMOR_CLASSES, rounds_per_fight)])
            if by_round:
                df_acs = reformat_df_ac(df_acs, by_round=by_round, x=x_col)
                data_summary = [df_acs.loc[df_acs['Character'] == c_name, :].drop("Character", axis=1) for c_name in order]
            else:
                data_summary = dpa_vs_ac_tables(df_acs, order, x_col=x_col)
            tables = leaderboard + insights + build_tables_row(characters, data_summary, width=3, by_round=by_round) + breakdown
        elif simulate_type == "Rounds to Kill":
            df_rtk, error = try_and_except_alert(error_message, simulate_rounds_to_kill, characters, enemy,
                                                 num_rounds=num_rounds, max_rounds=MAX_ROUNDS_TO_KILL, rng=rng)
            if error is not None:
                return fig, tables, error, spinner, summary, session
            fig = generate_rounds_to_kill_plot(df_rtk, MAX_ROUNDS_TO_KILL, enemy.hit_points, template=template)
            tables = rounds_to_kill_summary(df_rtk, MAX_ROUNDS_TO_KILL) + breakdown
            summary = results_summary(df_rtk.mean().to_dict(), "rounds on average", higher_is_better=False, context=f"to kill {enemy.name} ({enemy.hit_points} HP).")
        elif simulate_type == "Damage per Fight":
            fights, error = try_and_except_alert(error_message, simulate_fights, characters, enemy, num_fights=max(num_rounds // rounds_per_fight, 1),
                                                 rounds_per_fight=rounds_per_fight, rng=rng)
            if error is not None:
                return fig, tables, error, spinner, summary, session
            fig = generate_fight_plot(fights, template=template)
            tables = fight_summary(fights) + breakdown
            summary = results_summary({name: damage.sum(axis=0).mean() for name, damage in fights.items()}, f"damage per {rounds_per_fight} round fight", context=f"against {enemy.name}.")
        return fig, tables, None, spinner, summary, session


    # Resimulate since storing data is very memory intensive. Could implment client side callbacks, but this is sufficient for now
    @app.callback(
        Output('export-results', 'data'),
        Output('simulate-alerts', "children", allow_duplicate=True),
        Output('export-spinner', "children"),
        Input('export-results-button', 'n_clicks'),
        State("export-type", "value"),
        State("simulate-input", "value"),
        State({'type': 'attack_store', "index": ALL}, "data"),
        State("character_row", "children"),
        State("enemy-card-body", "children"),
        State("numerical-options", "value"),
        State("ruleset", "value"),
        State("sweep-parameter", "value"),
        State("rounds-per-fight", "value"),
        prevent_initial_call=True
    )
    @timeit
    def export_results(clicked, export_type, num_rounds, attack_stores, characters_list, enemy_card_body, numerical_options, ruleset, sweep_parameter, rounds_per_fight):
        if not clicked:
            raise PreventUpdate

        # Default Outputs
        export = Patch()
        spinner = html.I(className="fa-solid fa-download")

        characters, enemy, rng, error = parse_simulation_inputs(num_rounds, attack_stores, characters_list, enemy_card_body, numerical_options)
        if error is not None:
            return export, error, spinner

        # Simulate
        dfs = []
        names = [c.name for c in characters]
        rounds_per_fight = max(int(rounds_per_fight or DEFAULT_ROUNDS_PER_FIGHT), 1)
        error_message = "Could not simulate combat, please check that all fields are filled out correctly"
        if export_type in ["DPR Summary", "DPA Summary", "DPR Distribution", "DPA Distribution"]:
            res, error = try_and_except_alert(error_message, simulate_rounds_from_characters, characters, enemy, num_rounds=num_rounds, rng=rng,
                                              rounds_per_fight=rounds_per_fight)
            if error is not None:
                return export, error, spinner

            df_all, df_by_rounds, df_by_attacks = res
            if export_type == "DPR Summary":
                data_list = summary_stats(df_by_rounds, by_round=True)
            elif export_type == "DPR Distribution":
                data_list = df_by_rounds
            elif export_type == "DPA Summary":
                data_list = df_by_attacks
            else:
                data_list = [d.sort_values(by=["Round"]) for d in df_all]
            for name, data in zip(names, data_list):
                data.insert(0, 'Name', name)
                dfs.append(data)

        elif export_type in SWEEPS:
            x_col, by_round = sweep_parameter, SWEEPS[export_type]
            df_acs, error = try_and_except_alert(error_message, run_sweep, characters, enemy, x_col, by_round=by_round, ruleset=ruleset, num_rounds=num_rounds, rng=rng,
                                                 rounds_per_fight=rounds_per_fight)
            if error is not None:
                return export, error, spinner
            dfs = [reformat_df_ac(df_acs, by_round=True, x=x_col)] if by_round else per_attack_ac_tables(df_acs, names, x=x_col)
        elif export_type == "Rounds to Kill":
            df_rtk, error = try_and_except_alert(error_message, simulate_rounds_to_kill, characters, enemy, num_rounds=num_rounds, max_rounds=MAX_ROUNDS_TO_KILL, rng=rng)
            if error is not None:
                return export, error, spinner
            df_rtk.index.name = "Fight"
            dfs = [df_rtk]
        elif export_type == "Damage per Fight":
            fights, error = try_and_except_alert(error_message, simulate_fights, characters, enemy, num_fights=max(num_rounds // rounds_per_fight, 1),
                                                 rounds_per_fight=rounds_per_fight, rng=rng)
            if error is not None:
                return export, error, spinner
            dfs = [fight_export(fights)]
        else:
            raise PreventUpdate

        # Export to csv
        export = dcc.send_data_frame(pd.concat(dfs).to_csv, f"{export_type}.csv")
        return export, None, spinner

    ## BG3 Party Planner

    @app.callback(
        Output("bg3-party", "data"),
        Output("bg3-member-tabs", "children"),
        Output("bg3-member-tabs", "active_tab"),
        Output("bg3-name", "value"),
        Output("bg3-preset", "value"),
        Output({"type": "bg3-level", "act": ALL}, "value"),
        Output({"type": "bg3-gear", "slot": ALL, "act": ALL}, "value"),
        Output({"type": "bg3-gear", "slot": ALL, "act": ALL}, "className"),
        Output({"type": "bg3-gear", "slot": ALL, "act": ALL}, "placeholder"),
        Output({"type": "bg3-buffs", "act": ALL}, "value"),
        Output("bg3-conditions", "options"),
        Output("bg3-conditions", "value"),
        Output("bg3-conflicts", "children"),
        Output("bg3-dpr", "children"),
        Input("bg3-member-tabs", "active_tab"),
        Input("bg3-add-member", "n_clicks"),
        Input("bg3-remove-member", "n_clicks"),
        Input("bg3-load", "n_clicks"),
        Input("bg3-name", "value"),
        Input("bg3-preset", "value"),
        Input({"type": "bg3-level", "act": ALL}, "value"),
        Input({"type": "bg3-gear", "slot": ALL, "act": ALL}, "value"),
        Input({"type": "bg3-buffs", "act": ALL}, "value"),
        Input("bg3-conditions", "value"),
        Input("enemy-values", "data"),
        Input("rounds-per-fight", "value"),
        State("bg3-party", "data"),
        State("bg3-load-preset", "value"),
    )
    def sync_planner(active_tab, _add, _remove, _load, name, preset, levels, gear, buffs, conditions, enemy_dict, rounds_per_fight, party, example):
        """ Keeps the party store and the member editor in sync. Editing updates the selected member, switching members loads them """
        party = [Bg3Build.from_dict(b) for b in (party or DEFAULT_PARTY)] or [Bg3Build.from_dict(DEFAULT_PARTY[0])]
        selected = min(int(active_tab or 0), len(party) - 1)
        triggered = ctx.triggered_id
        level_ids = [i["id"] for i in ctx.inputs_list[6]]
        gear_ids = [i["id"] for i in ctx.inputs_list[7]]
        buff_ids = [i["id"] for i in ctx.inputs_list[8]]
        editor_changed = triggered in ("bg3-name", "bg3-preset", "bg3-conditions") or (isinstance(triggered, dict) and triggered.get("type") in ("bg3-level", "bg3-gear", "bg3-buffs"))

        if triggered == "bg3-add-member" and len(party) < MAX_PARTY_SIZE:
            party.append(Bg3Build(f"Character {len(party) + 1}", "fighter_gwm"))
            selected = len(party) - 1
        elif triggered == "bg3-load" and example in PRESETS:
            party[selected] = deepcopy(PRESETS[example])
        elif triggered == "bg3-remove-member" and len(party) > 1:
            del party[selected]
            selected = min(selected, len(party) - 1)
        elif editor_changed:
            # Save the editor into the selected member
            member = party[selected]
            member.name = name or f"Character {selected + 1}"
            member.preset = preset if preset in BUILDS else member.preset
            member.levels = {gid["act"]: int(v) for gid, v in zip(level_ids, levels) if v and int(v) != ACTS[int(gid["act"])][1]}
            member.equipment = {}
            for gid, value in zip(gear_ids, gear):
                if value:
                    member.equipment.setdefault(gid["act"], {})[gid["slot"]] = value
            member.buffs = {bid["act"]: list(v or []) for bid, v in zip(buff_ids, buffs) if v}
            member.conditions = list(conditions or [])

        member = party[selected]
        conflicts = party_conflicts(party)
        enemy = Enemy.from_dict(enemy_dict) if enemy_dict else Enemy()
        tabs = [dbc.Tab(label=b.name, tab_id=str(ii)) for ii, b in enumerate(party)]
        outputs_from_member = not editor_changed
        return (
            [b.to_dict() for b in party],
            tabs,
            str(selected),
            member.name if outputs_from_member else no_update,
            member.preset if outputs_from_member else no_update,
            [act_level(gid["act"], member.levels) for gid in level_ids] if outputs_from_member else [no_update] * len(level_ids),
            [member.equipment.get(gid["act"], {}).get(gid["slot"]) for gid in gear_ids] if outputs_from_member else [no_update] * len(gear_ids),
            gear_highlights(member, conflicts, gear_ids),
            inherited_placeholders(member, gear_ids),
            [member.buffs.get(bid["act"], []) for bid in buff_ids] if outputs_from_member else [no_update] * len(buff_ids),
            conditional_options(member),
            [c for c in member.conditions if c in {o["value"] for o in conditional_options(member)}] if outputs_from_member else no_update,
            conflicts_list(conflicts),
            dpr_table(party, enemy, max(int(rounds_per_fight or DEFAULT_ROUNDS_PER_FIGHT), 1)),
        )

    @app.callback(
        Output("character_row", "children", allow_duplicate=True),
        Output("active_ids", "data", allow_duplicate=True),
        Output("character-alerts", "children", allow_duplicate=True),
        Input("bg3-send", "n_clicks"),
        State("bg3-send-act", "value"),
        State("bg3-party", "data"),
        State("bg3-member-tabs", "active_tab"),
        State("character_row", "children"),
        State("active_ids", "data"),
        prevent_initial_call=True
    )
    def send_party_to_simulator(n_clicks, which, party, active_tab, cards, active_ids_json):
        """ Adds the planner's characters, compiled at a checkpoint, as cards for the simulator """
        if not n_clicks or not party:
            raise PreventUpdate
        builds = [Bg3Build.from_dict(b) for b in party]
        if which == "member":
            member = builds[min(int(active_tab or 0), len(builds) - 1)]
            characters = [compile_build(member, act) for act in ACT_KEYS]
        else:
            characters = [compile_build(b, which) for b in builds]
        existing = {extract_character_ui_values(c)["name"] for c in cards}
        for c in characters:
            if c.name in existing:
                c.name = unique_name(c.name, existing)
            existing.add(c.name)
        return append_cards(characters, active_ids_json)
