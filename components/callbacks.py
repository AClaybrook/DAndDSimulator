""" Callbacks for the app, which are registered in app.py. Clientside callbacks are located in assets/callbacks.js"""
import json
import base64
import pandas as pd
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from dash import dcc, html, Input, Output, State, Patch, MATCH, ALL, ctx, clientside_callback, ClientsideFunction
from computations.analytic import attack_breakdown
from computations.models import Character, Enemy
from computations.numerical_simulation import (simulate_rounds_from_characters, set_seed, simulate_rounds_from_characters_multi_acs,
                                               simulate_rounds_to_kill)
from game_data import attacks_from_template, enemy_from_preset
from game_data.classes import build_character

from utilities.helper_functions import timeit
from components.callback_helpers import (get_active_ids_and_new_id, get_new_id, set_active_ids, try_and_except_alert, reformat_df_ac, alert,
                                         button_was_clicked, new_card_click, reset_clicks, replace_card_index_and_color, per_attack_ac_tables,
                                         rename_card, unique_name)
from components.plots import (COLORS, generate_plot_data, add_tables, summary_stats, generate_line_plots, generate_damage_per_attack_histogram,
                              build_tables_row, build_leaderboard, build_breakdown_tables, generate_rounds_to_kill_plot, rounds_to_kill_summary)
from components.character_card import generate_character_card, set_attack_from_values, extract_attack_ui_values, extract_character_ui_values, characters_from_ui
from components.enemy_card import extract_enemy_ui_values, generate_enemy_card_body

MAX_CHARACTERS = min(8, len(COLORS)) # There are 10 colors and 4 characters fit per row, so 8 is a good max
ARMOR_CLASSES = range(10, 26)
MAX_ROUNDS_TO_KILL = 20

def parse_simulation_inputs(num_rounds, attack_stores, characters_list, enemy_card_body, numerical_options):
    """ Shared validation for simulate and export. Returns (characters, enemy, rng, alert) """
    # Randomize Seed
    rng = set_seed(None if 1 in (numerical_options or []) else 1)

    # Check number of rounds is valid
    if not num_rounds or num_rounds < 1:
        return None, None, rng, alert("Invalid Number of Rounds")

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
    enemy, error = try_and_except_alert(
        "Could not parse enemy, please check that all fields are filled out correctly",
        lambda: Enemy.from_dict(extract_enemy_ui_values(enemy_card_body)))
    return characters, enemy, rng, error

def dpa_vs_ac_tables(df_acs, order):
    """ One table per character with a column group per attack """
    data_summary = []
    for c_name in order:
        df_c = df_acs.loc[df_acs['Character'] == c_name, :]
        c_summary = []
        for n, g in df_c.groupby('Character-Attack', sort=False):
            g = g.copy()
            g["mean"] = g["mean"].astype(float).round(2)
            attack_name = n[len(c_name)+1:]
            reshaped = pd.concat({attack_name: g.set_index('Armor Class').drop(['Character-Attack', 'Character'], axis=1).T})
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
        Input({'type': 'copy character', "index": ALL}, "n_clicks_timestamp"),
        State("character_row", "children"),
        State("active_ids", "data"),
        State("last-card-click", "data"),
        prevent_initial_call=True
    )
    @timeit
    def copy_character(timestamps, characters, active_ids_json, last_handled):
        clicked_at = new_card_click(timestamps, last_handled)
        if clicked_at is None:
            raise PreventUpdate

        copy_id = ctx.triggered_id["index"]
        active_ids, new_id = get_active_ids_and_new_id(active_ids_json)
        # Don't add more than max characters
        if new_id >= MAX_CHARACTERS:
            return Patch(), active_ids_json, alert(f"Max of {MAX_CHARACTERS} characters reached", color="warning"), clicked_at

        # Copy the existing character and replace its id, color, name and button clicks
        character = characters[active_ids.index(copy_id)]
        character = replace_card_index_and_color(reset_clicks(character), copy_id, new_id, COLORS[new_id])
        existing_names = {extract_character_ui_values(c)["name"] for c in characters}
        character = rename_card(character, unique_name(extract_character_ui_values(character)["name"], existing_names))

        patched_children = Patch()
        patched_children.append(character)
        active_ids.append(new_id)

        return patched_children, set_active_ids(active_ids), None, clicked_at

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

    @app.callback(
            Output('download-characters', 'data'),
            Input('export-button', 'n_clicks'),
            State("character_row", "children"),
            State({"type": "attack_store", "index": ALL}, "data"),
            prevent_initial_call=True
    )
    @timeit
    def export_character(clicked, characters_ui, attack_stores):
        if not clicked:
            raise PreventUpdate

        c_dicts = []
        for ii, c in enumerate(characters_ui):
            c_dict = extract_character_ui_values(c)
            c_dict["attacks"] = json.loads(attack_stores[ii])
            c_dicts.append(c_dict)

        return dict(content=json.dumps(c_dicts, indent=4), filename="characters.json")

    @app.callback(
            Output('character_row', 'children', allow_duplicate=True),
            Output('active_ids', 'data', allow_duplicate=True),
            Output('character-alerts', 'children'),
            Input('upload-button', 'contents'),
            State("active_ids", "data"),
            prevent_initial_call=True
    )
    @timeit
    def import_characters(contents, active_ids_json):
        if contents is None:
            raise PreventUpdate

        content_type, content_string = contents.split(',')
        if 'json' not in content_type:
            return Patch(), active_ids_json, alert("Import Failed. Only json files are supported")
        try:
            characters_list = json.loads(base64.b64decode(content_string).decode('utf-8'))
        except Exception as e:
            print(e)
            return Patch(), active_ids_json, alert("Import Failed. Cannot parse json file")

        # Parse characters, stopping at the first that fails
        characters = []
        error = None
        for c in characters_list if isinstance(characters_list, list) else [characters_list]:
            try:
                characters.append(Character.from_dict(c))
            except Exception as e:
                print(e)
                name = c.get('name', 'Unknown') if isinstance(c, dict) else 'Unknown'
                error = alert(f"Import Failed. Cannot parse character '{name}'. Skipping any remaining characters")
                break

        patched_children, active_ids, warning = append_cards(characters, active_ids_json)
        return patched_children, active_ids, error or warning

    # NOTE: Using a data store caused memory issues in the deployed environment on heroku, often exceeding 1 GB and there is a 0.5 GB limit, resimulating is faster
    @app.callback(
        Output('dist-plot', "figure"),
        Output('damage-tables', "children"),
        Output('simulate-alerts', "children"),
        Output("simulate-spinner", "children"),
        Input("simulate-button", "n_clicks"),
        State("simulate-input", "value"),
        State({'type': 'attack_store', "index": ALL}, "data"),
        State("character_row", "children"),
        State("enemy-card-body", "children"),
        State("simulate-type", "value"),
        State("numerical-options", "value"),
        prevent_initial_call=True
    )
    @timeit
    def simulate(clicked, num_rounds, attack_stores, characters_list, enemy_card_body, simulate_type, numerical_options):
        if not clicked:
            raise PreventUpdate

        # Default Outputs
        fig = Patch()
        tables = Patch()
        spinner = "Simulate!"

        characters, enemy, rng, error = parse_simulation_inputs(num_rounds, attack_stores, characters_list, enemy_card_body, numerical_options)
        if error is not None:
            return fig, tables, error, spinner

        breakdown = build_breakdown_tables(characters, [attack_breakdown(c, enemy) for c in characters])
        error_message = "Could not simulate combat, please check that all fields are filled out correctly"

        # Simulate
        if simulate_type in ["DPR Distribution", "DPA Distribution"]:
            res, error = try_and_except_alert(error_message, simulate_rounds_from_characters, characters, enemy, num_rounds=num_rounds, save_memory=True, rng=rng)
            if error is not None:
                return fig, tables, error, spinner

            dfs, df_by_rounds, df_by_attacks = res
            leaderboard = build_leaderboard(characters, df_by_rounds)
            if simulate_type == "DPR Distribution":
                fig = generate_plot_data(characters, df_by_rounds, template=template, title="Damage Per Round Distribution")
                tables = leaderboard + add_tables(df_by_rounds, characters, by_round=True, width=3) + breakdown
            elif simulate_type == "DPA Distribution":
                fig = generate_damage_per_attack_histogram(characters, dfs, template=template, title="Damage Per Attack Distribution")
                tables = leaderboard + add_tables(df_by_attacks, characters, by_round=False, width=3) + breakdown
        elif simulate_type in ["DPR vs Armor Class", "DPA vs Armor Class"]:
            by_round = simulate_type == "DPR vs Armor Class"
            df_acs, error = try_and_except_alert(error_message, simulate_rounds_from_characters_multi_acs, characters, enemy,
                                                 armor_classes=ARMOR_CLASSES, num_rounds=num_rounds, by_round=by_round, rng=rng)
            if error is not None:
                return fig, tables, error, spinner

            groupby = "Character" if by_round else "Character-Attack"
            order = [c.name for c in characters]
            fig = generate_line_plots(df_acs, template=template, groupby=groupby, order=order)
            if by_round:
                df_acs = reformat_df_ac(df_acs, by_round=by_round)
                data_summary = [df_acs.loc[df_acs['Character'] == c_name, :].drop("Character", axis=1) for c_name in order]
            else:
                data_summary = dpa_vs_ac_tables(df_acs, order)
            tables = build_tables_row(characters, data_summary, width=3, by_round=by_round) + breakdown
        elif simulate_type == "Rounds to Kill":
            df_rtk, error = try_and_except_alert(error_message, simulate_rounds_to_kill, characters, enemy,
                                                 num_rounds=num_rounds, max_rounds=MAX_ROUNDS_TO_KILL, rng=rng)
            if error is not None:
                return fig, tables, error, spinner
            fig = generate_rounds_to_kill_plot(df_rtk, MAX_ROUNDS_TO_KILL, enemy.hit_points, template=template)
            tables = rounds_to_kill_summary(df_rtk, MAX_ROUNDS_TO_KILL) + breakdown
        return fig, tables, None, spinner


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
        prevent_initial_call=True
    )
    @timeit
    def export_results(clicked, export_type, num_rounds, attack_stores, characters_list, enemy_card_body, numerical_options):
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
        error_message = "Could not simulate combat, please check that all fields are filled out correctly"
        if export_type in ["DPR Summary", "DPA Summary", "DPR Distribution", "DPA Distribution"]:
            res, error = try_and_except_alert(error_message, simulate_rounds_from_characters, characters, enemy, num_rounds=num_rounds, rng=rng)
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

        elif export_type in ["DPR vs Armor Class", "DPA vs Armor Class"]:
            by_round = export_type == "DPR vs Armor Class"
            df_acs, error = try_and_except_alert(error_message, simulate_rounds_from_characters_multi_acs, characters, enemy,
                                                 armor_classes=ARMOR_CLASSES, num_rounds=num_rounds, by_round=by_round, rng=rng)
            if error is not None:
                return export, error, spinner
            dfs = [reformat_df_ac(df_acs, by_round=True)] if by_round else per_attack_ac_tables(df_acs, names)
        elif export_type == "Rounds to Kill":
            df_rtk, error = try_and_except_alert(error_message, simulate_rounds_to_kill, characters, enemy, num_rounds=num_rounds, max_rounds=MAX_ROUNDS_TO_KILL, rng=rng)
            if error is not None:
                return export, error, spinner
            df_rtk.index.name = "Fight"
            dfs = [df_rtk]
        else:
            raise PreventUpdate

        # Export to csv
        export = dcc.send_data_frame(pd.concat(dfs).to_csv, f"{export_type}.csv")
        return export, None, spinner
