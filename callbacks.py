from dash import Input, Output, State, Patch, MATCH, ALL, ctx
from plots import COLORS, generate_plot_data, add_tables, data_to_store, data_from_store, summary_stats
from components.character_card import generate_character_card, set_attack_from_values, extract_attack_ui_values, extract_character_ui_values
from components.enemy_card import extract_enemy_ui_values
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from dash import dcc
import json
import numpy as np
from models import Attack, Character, Enemy
from numerical_simulation import simulate_character_rounds
import base64
import pandas as pd

MAX_CHARACTERS = min(8,len(COLORS)) # There are 10 colors and 4 characters fit per row, so 8 is a good max

# Manipulating ids
def get_active_ids_and_new_id(ids_json):
    ids = json.loads(ids_json)
    new_id = get_new_id(ids)
    return ids, new_id

def get_new_id(ids):
    ids_set = set(ids)
    deleted_ids = [i for i in range(len(ids)) if i not in ids_set]
    new_id = deleted_ids[0] if len(deleted_ids) > 0 else len(ids)
    return new_id

def set_active_ids(ids):
    return json.dumps(ids)

def max_from_list(l):
    max_ = 0 
    index = None
    if isinstance(l, int):
        max_ = l
        index = 0
    elif l is None:
        pass
    elif isinstance(l, list):
        for ii, time in enumerate(l):
            if time is not None and time > max_:
                max_ = time
                index = ii
    return max_, index

def characters_from_ui(characters_list, attack_stores):
    characters = []
    for ii, c in enumerate(characters_list):
        attacksPython = [Attack(**attack) for attack in json.loads(attack_stores[ii])]
        characters.append(Character(attacks=attacksPython, **extract_character_ui_values(c)))
    return characters

# Note: Intellisense is not recognizing the callbacks as being accessed
def register_callbacks(app, sidebar=True):
    if sidebar:
        @app.callback(
            Output("sidebar", "className"),
            [Input("sidebar-toggle", "n_clicks")],
            [State("sidebar", "className")],
        )
        def toggle_classname(n, classname):
            if n and classname == "":
                return "collapsed"
            return ""
        
        @app.callback(
            Output("collapse", "is_open"),
            [Input("navbar-toggle", "n_clicks")],
            [State("collapse", "is_open")],
        )
        def toggle_collapse(n, is_open):
            if n:
                return not is_open
            return is_open
        
    @app.callback(
        Output("character_row","children"),
        Output("active_ids","data"),
        Input("add_character_button","n_clicks"),
        State("character_name","value"),
        State("active_ids","data"),
        prevent_initial_call=True
    )
    def add_character(n_clicks, name, active_ids_json):
        # Don't update without a name or without a button click
        if not name or n_clicks is None:
            raise PreventUpdate

        # Don't add more than max characters
        active_ids, new_id = get_active_ids_and_new_id(active_ids_json)
        if new_id >= MAX_CHARACTERS:
            raise PreventUpdate
        
        # Add new character using the first deleted id or the next id
        patched_children = Patch()
        patched_children.append(generate_character_card(name, color=COLORS[new_id], index=new_id))
        active_ids.append(new_id)
        
        return patched_children, set_active_ids(active_ids)

    
    @app.callback(
            Output({'type': 'character name',"index": MATCH},"children"),
            Input({'type': 'character name input',"index": MATCH},"value"),
            prevent_initial_call=True
    )
    def update_name(name):
        return name
    
    @app.callback(
            Output("character_row","children", allow_duplicate=True),
            Output("active_ids","data", allow_duplicate=True),
            Output("delete-timestamp","data"),
            Input({'type': 'delete character',"index": ALL},"n_clicks_timestamp"), # Unfortunately MATCH doesn't work since there is no corresponding MATCH in the outputs
            State("active_ids","data"),
            State("add_character_button","n_clicks_timestamp"),
            State({'type': 'copy character',"index": ALL},"n_clicks_timestamp"),
            prevent_initial_call=True
    )
    def delete_character(delete_timestamps, active_ids_json, add_timestamp, copy_timestamps):
        # Get clicked id and index
        delete_id = ctx.triggered_id["index"]
        active_ids, _ = get_active_ids_and_new_id(active_ids_json)
        index = active_ids.index(delete_id)
        
        # Prevent if attack was not the most recently clicked
        max_, index = max_from_list(delete_timestamps)
        if index is None:
            raise PreventUpdate
        max_add, _ = max_from_list(add_timestamp)
        max_copy, _ = max_from_list(copy_timestamps)
        most_recent_button_click = max(max_add, max_copy)
        if max_ < most_recent_button_click:
            raise PreventUpdate
        
        # Don't delete the last character
        if len(active_ids) == 1:
            raise PreventUpdate 
        
        # Delete the character and update
        patched_children = Patch()
        del patched_children[index]
        del active_ids[index]

        return patched_children, set_active_ids(active_ids), max_
    
    @app.callback(
        Output("character_row","children", allow_duplicate=True),
        Output("active_ids","data", allow_duplicate=True),
        State("character_row","children"),
        State("active_ids","data"),
        Input({'type': 'copy character',"index": ALL},"n_clicks_timestamp"),
        State("add_character_button","n_clicks_timestamp"),
        State("delete-timestamp","data"),
        prevent_initial_call=True
    )
    def copy_character(characters, active_ids_json, copy_timestamps, add_timestamp, delete_timestamps):
        # Find which button was clicked
        copy_id = ctx.triggered_id["index"]
        active_ids, new_id = get_active_ids_and_new_id(active_ids_json)
        index = active_ids.index(copy_id)
        if copy_id is None:
            raise PreventUpdate
        
        # Prevent if attack was not the most recently clicked
        max_, index = max_from_list(copy_timestamps)
        if index is None:
            raise PreventUpdate
        max_add, _ = max_from_list(add_timestamp)
        max_delete, _ = max_from_list(delete_timestamps)
        most_recent_button_click = max(max_add, max_delete)
        if max_ < most_recent_button_click:
            raise PreventUpdate
        
        # Don't add more than max characters
        if new_id >= MAX_CHARACTERS:
            raise PreventUpdate

        
        # Copy the existing character and replace its id and color 
        character = characters[index]    
        card_str = json.dumps(character)
        card_str = card_str.replace(f'"index": {copy_id}', f'"index": {new_id}')
        character = json.loads(card_str)
        # TODO: Find a cleaner way to replace colors... Perhaps find the h4 and id string and then replace the color with rgb values
        color = COLORS[new_id]
        character['props']['children']['props']['children'][0]['props']['children']['props']['children'][0]['props']['children']['props']['style']['color'] = color
        print(color)

        patched_children = Patch()
        patched_children.append(character)
        active_ids.append(new_id)
        
        return patched_children, set_active_ids(active_ids)
    
    ## Attacks

    # TODO: Check that this works, it appears to work
    @app.callback(
        Output({'type': 'attack',"index": MATCH, "num": ALL},"active"),
        Output({'type': 'attack_ui',"index": MATCH},"children"),
        Input({'type': 'attack',"index": MATCH, "num": ALL},"n_clicks_timestamp"),
        State({'type': 'attack_store',"index": MATCH},"data"),
        State({"type": "add-attack", "index": MATCH},"n_clicks_timestamp"),
        State({"type": "delete-attack", "index": MATCH},"n_clicks_timestamp"),
        prevent_initial_call=True
    )
    def select_attack(selected_attacks, avals, add_attack_clicked, delete_attack_clicked):
        # Prevent if attack was not the most recently clicked
        max_, index = max_from_list(selected_attacks)
        if index is None:
            raise PreventUpdate
        max_add, _ = max_from_list(add_attack_clicked)
        max_delete, _ = max_from_list(delete_attack_clicked)
        most_recent_button_click = max(max_add, max_delete)
        if max_ < most_recent_button_click:
            raise PreventUpdate

        # Update actively selected attacks
        attacks = [index == ii for ii in range(len(selected_attacks))]

        # Update attack ui to match the values of the selected attack
        card_index = ctx.triggered_id['index']

        attack_ui = set_attack_from_values(json.loads(avals), index, card_index)
        
        return attacks, attack_ui 

    @app.callback(
        Output({'type': 'attack_store',"index": MATCH},"data"),
        Output({'type': 'attacks',"index": MATCH},"children"),
        Input({"type": "add-attack", "index": MATCH},"n_clicks_timestamp"),
        State({"type": "attack_ui", "index": MATCH},"children"),
        State({'type': 'attack_store',"index": MATCH},"data"),
        State({'type': 'attacks',"index": MATCH},"children"),
        prevent_initial_call=True
    )
    def add_attack(add_attack_clicked, attack_ui_list, avals, existing_attacks):
        # Prevent if all attacks are None
        if add_attack_clicked is None:
            raise PreventUpdate

        # TODO: Determine if adding logic to make sure only adding within the last second is necessary

        # Get values from UI update attack store
        new_attack, num_attacks = extract_attack_ui_values(attack_ui_list)

        # Append to existing attack store
        avals_updated = json.loads(avals)
        for ii in range(num_attacks):
            avals_updated.append(new_attack)

        # Update UI attack list
        attacks_updated = existing_attacks
        nums = [int(a["props"]["id"]["num"]) for a in existing_attacks]
        index=ctx.triggered_id["index"]
        for ii in range(num_attacks):
            jj = get_new_id(nums)
            nums.append(jj)
            attacks_updated.append(dbc.ListGroupItem(new_attack["name"], active=False, id={"type": "attack", "index": index, "num": jj})) 
                         
        return json.dumps(avals_updated), attacks_updated
    

    @app.callback(
        Output({'type': 'attack_store',"index": MATCH},"data", allow_duplicate=True),
        Output({'type': 'attacks',"index": MATCH},"children", allow_duplicate=True),
        Input({"type": "delete-attack", "index": MATCH},"n_clicks_timestamp"),
        State({'type': 'attack_store',"index": MATCH},"data"),
        State({'type': 'attacks',"index": MATCH},"children"),
        State({'type': 'attack',"index": MATCH, "num": ALL},"active"),
        prevent_initial_call=True
    )
    def delete_attack(delete_attack_clicked, avals, existing_attacks, active_attacks):
        # Prevent if all attacks are None
        if delete_attack_clicked is None:
            raise PreventUpdate

        # Prevent if all attacks are None
        index = ctx.triggered_id["index"]
        if index is None:
            raise PreventUpdate

        # Update actively selected attacks
        attack_index = [ii for ii, a in enumerate(active_attacks) if a == True]
        if len(attack_index) != 1:
            raise PreventUpdate
        attack_index = attack_index[0]

        # Delete from store and UI
        avals_updated = json.loads(avals)
        for ii in range(len(avals_updated)):
            if ii == attack_index:
                del avals_updated[ii]
                del existing_attacks[ii]
                break

        return json.dumps(avals_updated), existing_attacks
    
    @app.callback(
            Output('download-characters','data'),
            Input('export-button','n_clicks'),
            State("character_row","children"),
            State({"type": "attack_store", "index": ALL},"data"),           
    )
    def export_character(clicked, characters_ui, attack_stores):
        if clicked is None:
            raise PreventUpdate
        
        c_dicts = []
        for ii,c in enumerate(characters_ui):
            attack_dicts= [attack for attack in json.loads(attack_stores[ii])]
            c_dict = extract_character_ui_values(c)
            c_dict["attacks"] = attack_dicts
            c_dicts.append(c_dict)

        return dict(content=json.dumps(c_dicts, indent=4), filename="characters.json")
    
    # TODO: Import characters
    @app.callback(
            Output('character_row','children', allow_duplicate=True),
            Output('active_ids','data', allow_duplicate=True),
            Output('character-alerts','children'),
            Input('upload-button','contents'), 
            State("active_ids","data"),
            prevent_initial_call=True           
    )
    def import_characters(contents, active_ids_json):
        if contents is None:
            raise PreventUpdate
        
        def parse_contents(contents):
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            alert = None
            characters_list = []
            if 'json' in content_type:
                try:
                    characters_list = json.loads(decoded.decode('utf-8'))
                except Exception as e:
                    print(e)
                    alert = dbc.Alert(
                        f"Import Failed. Cannot parse json file",
                        dismissable=True,
                        is_open=True,
                        color="danger")
            else:
                alert = dbc.Alert(
                    f"Import Failed. Only json files are supported",
                    dismissable=True,
                    is_open=True,
                    color="danger")
            return alert, characters_list
        
        alert, characters_list = parse_contents(contents)
    
        # Add characters
        characters = Patch()
        _active_ids_patch = Patch() # Needed so patch works for attack stores
        active_ids, new_id = get_active_ids_and_new_id(active_ids_json)

        if alert is None:

            for ii, c in enumerate(characters_list):
                # Don't add more than max characters
                if new_id >= MAX_CHARACTERS:
                    alert = dbc.Alert(
                        f"Max Characters Reached. Only imported {ii} characters from the file",
                        dismissable=True,
                        is_open=True,
                        color="warning")
                    break
                # TODO: For now ignore all characters that fail to parse, but this could be more granular in the future
                try:
                    attacks = c.pop("attacks")
                    attacksPython = [Attack(**attack) for attack in attacks]
                    characters.append(generate_character_card(c["name"], character=Character(**c, attacks=attacksPython), color=COLORS[new_id], index=new_id))
                except Exception as e:
                    alert = dbc.Alert(
                        f"Import Failed. Cannot parse character '{c['name']}'. Skipping any remaining characters",
                        dismissable=True,
                        is_open=True,
                        color="danger")
                    break
                active_ids.append(new_id)
                new_id = get_new_id(active_ids)
            
        return characters, set_active_ids(active_ids), alert

    @app.callback(
            Output("enemy-name","children"),
            Input("enemy-name-input","value"),
            prevent_initial_call=True
    )
    def update_enemy_name(name):
        return name
    
    @app.callback(
        Output('results-store',"data"),
        Output('dist-plot',"figure"),
        Output('per-round-tables',"children"),
        Output('per-attack-tables',"children"),
        Output('simulate-alerts',"children"),
        Input("simulate-button","n_clicks"),
        State("simulate-input","value"),
        State({'type': 'attack_store',"index": ALL},"data"),
        State("character_row","children"),
        State("enemy-card-body","children"),
        prevent_initial_call=True
    )
    def simulate(clicked, num_rounds, attack_stores, characters_list, enemy_card_body):
        if clicked is None:
            raise PreventUpdate
        
        if num_rounds is None:
            res = Patch()
            fig = Patch()
            rounds = Patch()
            attacks = Patch()
            alert = dbc.Alert(
                "Invalid Number of Rounds",
                dismissable=True,
                is_open=True,
                color="danger")
            return res, fig, rounds, attacks, alert

        characters = characters_from_ui(characters_list, attack_stores)
        
        enemy = Enemy(**extract_enemy_ui_values(enemy_card_body))

        dfs, df_by_rounds, df_by_attacks = simulate_character_rounds(characters, enemy, num_rounds=num_rounds)
        data, fig = generate_plot_data(characters, df_by_rounds)
        print(f"test {clicked}")
        rounds = add_tables(df_by_rounds,characters,by_round=True, width=3)
        attacks = add_tables(df_by_attacks,characters,by_round=False, width=3)
        # TODO: Looks like the data store is running out of memory, need to store only summary data and just resimulate if needed
        # TODO: Could add a random seed to ensure data is the same
        res = data_to_store(characters, df_by_rounds)
        return res, fig, rounds, attacks, None
    

    @app.callback(
        Output('export-results','data'),
        Input('export-results-button','n_clicks'),
        State("export-type","value"),         
        State("results-store","data"),         
    )
    def export_results(clicked, export_type, results_store):
        if clicked is None:
            raise PreventUpdate

        # TODO: Allow multiple download options, by round, by attack, etc.
        # TODO: Add characters to export

        dfs = []

        names, df_by_rounds = data_from_store(results_store)
        if export_type == "Summary Stats":
            df_summary = summary_stats(df_by_rounds, by_round=True)
            for name, data in zip(names,df_summary):
                data.insert(0, 'Name', name)
                dfs.append(data)
        elif export_type == "By Round":
            for name, data in zip(names,df_by_rounds):
                data.insert(0, 'Name', name)
                dfs.append(data)
        elif export_type == "By Attack":
            # TODO: NOT Implemented
            dfs = df_by_rounds
        elif export_type == "All Attacks":
             # TODO: NOT Implemented
            dfs = df_by_rounds

        # Export to csv
        export_kwargs = {"index": False}
        filename = f"Damage {export_type}.csv"
        export = dcc.send_data_frame(pd.concat(dfs).to_csv, filename, export_kwargs)
        return export
    

# TODO: Add multiple graph options. Add a simulate for multiple enemy armor classes