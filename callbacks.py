from dash import Input, Output, State, Patch, MATCH, ALL, ctx, clientside_callback, ClientsideFunction
from plots import COLORS, generate_plot_data, add_tables, summary_stats, generate_line_plots, generate_damage_per_attack_histogram, build_tables_row
from components.character_card import generate_character_card, set_attack_from_values, extract_attack_ui_values, extract_character_ui_values
from components.enemy_card import extract_enemy_ui_values
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from dash import dcc, html
import json
from models import Attack, Character, Enemy
from numerical_simulation import simulate_character_rounds, set_seed, simulate_character_rounds_for_multiple_armor_classes
import base64
import pandas as pd
import numpy as np
from functools import wraps
from time import time
import sys

MAX_CHARACTERS = min(8,len(COLORS)) # There are 10 colors and 4 characters fit per row, so 8 is a good max



def timeit(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        print('func:%r took: %2.4f sec' % \
          (f.__name__, te-ts))
        return result
    return wrap

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

def try_and_except_alert(alert_message, func, *args, **kwargs):
    try:
        return func(*args, **kwargs), None
    except Exception as e:
        print(e)
        alert = dbc.Alert(
            alert_message,
            dismissable=True,
            is_open=True,
            color="danger")
        return None, alert
    
def reformat_df_ac(df, by_round=True):
    """Reformats the armor class dataframe"""
    if by_round:
        df_acs = df.reset_index(drop=True)
        ac_col = df_acs.pop("Armor Class")
        df_acs.insert(0, 'Armor Class', ac_col)
        name_col = df_acs.pop("Character")
        df_acs.insert(0, 'Character', name_col)
        df_acs.set_index(['Armor Class'], inplace=True)
        df_acs["mean"] = df_acs["mean"].astype(float).round(2)
        return df_acs
    else:
        new_dfs = []
        for n,g in df.groupby('Character-Attack'):
            reshaped = pd.concat({n:g.set_index('Armor Class').drop(['Character-Attack','Character'],axis=1).T})
            new_dfs.append(reshaped)
        return pd.concat(new_dfs).T



# Note: Intellisense is not recognizing the callbacks as being accessed
def register_callbacks(app, sidebar=True):
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

    @app.callback(
        Output("character_row","children"),
        Output("active_ids","data"),
        Input("add_character_button","n_clicks"),
        State("character_name","value"),
        State("active_ids","data"),
        prevent_initial_call=True
    )
    @timeit
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

    # Call client side callback in javascript, found in assets/callbacks.js
    clientside_callback(
        ClientsideFunction(
            namespace="clientside",
            function_name="update_name"
        ),
        Output({'type': 'character name',"index": MATCH},"children"),
        Input({'type': 'character name input',"index": MATCH},"value"),
        prevent_initial_call=True
    )

    clientside_callback(
        ClientsideFunction(
            namespace="clientside",
            function_name="update_name"
        ),
        Output("enemy-name","children"),
        Input("enemy-name-input","value"),
        prevent_initial_call=True
    )

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
    @timeit
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
    @timeit
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
    @timeit
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
    @timeit
    def add_attack(add_attack_clicked, attack_ui_list, avals, existing_attacks):
        # Prevent if all attacks are None
        if add_attack_clicked is None:
            raise PreventUpdate

        # TODO: Determine if adding logic to make sure only adding within the last second is necessary

        # Get values from UI update attack store
        new_attack, num_attacks = extract_attack_ui_values(attack_ui_list)

        # Append to existing attack store
        avals_updated = json.loads(avals)
        for _ in range(num_attacks):
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
    @timeit
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
        for ii, _ in enumerate(avals_updated):
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
            prevent_initial_call=True           
    )
    @timeit
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
    @timeit
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
                        "Import Failed. Cannot parse json file",
                        dismissable=True,
                        is_open=True,
                        color="danger")
            else:
                alert = dbc.Alert(
                    "Import Failed. Only json files are supported",
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
                    print(e)
                    alert = dbc.Alert(
                        f"Import Failed. Cannot parse character '{c['name']}'. Skipping any remaining characters",
                        dismissable=True,
                        is_open=True,
                        color="danger")
                    break
                active_ids.append(new_id)
                new_id = get_new_id(active_ids)
            
        return characters, set_active_ids(active_ids), alert

    # NOTE: Using a data store caused memory issues in the deployed environment on heroku, often exceeding 1 GB and there is a 0.5 GB limit, resimulating is faster
    @app.callback(
        # Output('results-store',"data"),
        Output('dist-plot',"figure"),
        Output('damage-tables',"children"),
        Output('simulate-alerts',"children"),
        Output("simulate-spinner","children"),
        Input("simulate-button","n_clicks"),
        State("simulate-input","value"),
        State({'type': 'attack_store',"index": ALL},"data"),
        State("character_row","children"),
        State("enemy-card-body","children"),
        State("simulate-type","value"),
        State("numerical-options","value"),
        prevent_initial_call=True
    )
    @timeit
    def simulate(clicked, num_rounds, attack_stores, characters_list, enemy_card_body, simulate_type, numerical_options):
        if clicked is None:
            raise PreventUpdate
        
        if 1 in numerical_options: # Randomize Seed
            set_seed(np.random.randint(0,100))
        else:
            set_seed()

        # Default Outputs
        fig = Patch()
        tables = Patch()
        alert = None
        spinner = "Simulate!"

        # Check number of rounds is valid
        if num_rounds is None:
            alert = dbc.Alert(
                "Invalid Number of Rounds",
                dismissable=True,
                is_open=True,
                color="danger")
            return fig, tables, alert, spinner

        # Parse characters
        characters, alert = try_and_except_alert(
            "Could not parse characters, please check that all fields are filled out correctly",
            characters_from_ui,
            *[characters_list, attack_stores]
            )
        if alert is not None:
            return fig, tables, alert, spinner

        # Character names should be unique, or else data analysis gets misleading
        unique_names = {c.name for c in characters}
        if len(unique_names) != len(characters):
            alert = dbc.Alert(
                "Characters names must be unique",
                dismissable=True,
                is_open=True,
                color="danger")
            return fig, tables, alert, spinner

        # Parse enemy
        enemy, alert = try_and_except_alert(
            "Could not parse enemy, please check that all fields are filled out correctly",
            Enemy,
            **extract_enemy_ui_values(enemy_card_body),
            )
        if alert is not None:
            return fig, tables, alert, spinner

        # Simulate
        if simulate_type in ["DPR Distribution","DPA Distribution"]:
            res, alert = try_and_except_alert(
                "Could not simulate combat, please check that all fields are filled out correctly",
                simulate_character_rounds,
                *[characters,enemy],
                num_rounds=num_rounds,
                save_memory=True
                )
            if alert is not None:
                return fig, tables, alert, spinner

            dfs, df_by_rounds, df_by_attacks = res
            del res
            if simulate_type == "DPR Distribution":
                fig = generate_plot_data(characters, df_by_rounds, title="Damage Per Round Distribution")
                tables = add_tables(df_by_rounds,characters,by_round=True, width=3)
            elif simulate_type == "DPA Distribution":
                fig = generate_damage_per_attack_histogram(characters, dfs, title="Damage Per Attack Distribution", opacity=0.5) # Many overlapping histograms cause large performance issues, a lower opacity helps
                tables = add_tables(df_by_attacks,characters,by_round=False, width=3)
            print(f"dfs : {sum([d.memory_usage(deep=True).sum() for d in dfs])/1000000} MB")
            print(f"df_by_rounds : {sum([d.memory_usage(deep=True).sum() for d in df_by_rounds])/1000000} MB")
            del dfs, df_by_rounds, df_by_attacks
        elif simulate_type in ["DPR vs Armor Class","DPA vs Armor Class"]:
            by_round = simulate_type == "DPR vs Armor Class"
            df_acs, alert = try_and_except_alert(
                "Could not simulate combat, please check that all fields are filled out correctly",
                simulate_character_rounds_for_multiple_armor_classes,
                *[characters,enemy],
                armor_classes = range(10,26),
                num_rounds=num_rounds,
                by_round=by_round
                )
            if alert is not None:
                return fig, tables, alert, spinner

            groupby = "Character" if by_round else "Character-Attack"
            order = [c.name for c in characters]
            fig = generate_line_plots(df_acs,template='plotly_dark', groupby=groupby, order=order)
            if by_round:
                df_acs = reformat_df_ac(df_acs, by_round=by_round)
                data_summary = [g.drop("Character",axis=1) for _, g in df_acs.groupby(groupby)]
            else:
                data_summary = []
                for c_name in order:
                    df_c = df_acs.loc[df_acs['Character']==c_name, :]
                    c_summary = []
                    for n,g in df_c.groupby('Character-Attack'):
                        g["mean"] = g["mean"].astype(float).round(2)
                        attack_name = n[len(c_name)+1:]
                        reshaped = pd.concat({attack_name:g.set_index('Armor Class').drop(['Character-Attack','Character'],axis=1).T})
                        c_summary.append(reshaped.T)
                    data_summary.append(pd.concat(c_summary,axis=1))
            
            tables = build_tables_row(characters, data_summary, width=3, by_round=by_round)
            print(f"df_acs : {df_acs.memory_usage(deep=True).sum()/1000000} MB")
            print(f"data_summary : {sum([d.memory_usage(deep=True).sum() for d in data_summary])/1000000} MB")
            del df_acs, data_summary
        print(f"Simulated {clicked} times")
        return fig, tables, alert, spinner


    # Resimulate since storing data is very memory intensive. Could implment client side callbacks, but this is sufficient for now
    @app.callback(
        Output('export-results','data'),
        Output('simulate-alerts',"children", allow_duplicate=True),
        Output('export-spinner',"children"),
        Input('export-results-button','n_clicks'),
        State("export-type","value"),
        State("simulate-input","value"),
        State({'type': 'attack_store',"index": ALL},"data"),
        State("character_row","children"),
        State("enemy-card-body","children"),
        State("numerical-options","value"),
        prevent_initial_call=True
    )
    @timeit
    def export_results(clicked, export_type, num_rounds, attack_stores, characters_list, enemy_card_body, numerical_options):
        if clicked is None:
            raise PreventUpdate

        if 1 in numerical_options: # Randomize Seed
            set_seed(np.random.randint(0,100))
        else:
            set_seed()

        # Default Outputs
        export = Patch()
        alert = None
        spinner = html.I(className="fa-solid fa-download")

        # Check number of rounds is valid
        if num_rounds is None:
            export = Patch()
            alert = dbc.Alert(
                "Invalid Number of Rounds",
                dismissable=True,
                is_open=True,
                color="danger")
            return export, alert, spinner

        # Parse characters
        characters, alert = try_and_except_alert(
            "Could not parse characters, please check that all fields are filled out correctly",
            characters_from_ui,
            *[characters_list, attack_stores]
            )
        if alert is not None:
            return export, alert, spinner

        # Character names should be unique, or else data analysis gets misleading
        unique_names = {c.name for c in characters}
        if len(unique_names) != len(characters):
            alert = dbc.Alert(
                "Characters names must be unique",
                dismissable=True,
                is_open=True,
                color="danger")
            return export, alert, spinner

        # Parse enemy
        enemy, alert = try_and_except_alert(
            "Could not parse enemy, please check that all fields are filled out correctly",
            Enemy,
            **extract_enemy_ui_values(enemy_card_body),
            )
        if alert is not None:
            return export, alert, spinner

        # Simulate
        dfs = []
        names = [c.name for c in characters]
        export_kwargs = {}
        if export_type in ["DPR Summary", "DPA Summary", "DPR Distribution","DPA Distribution"]:
            res, alert = try_and_except_alert(
                "Could not simulate combat, please check that all fields are filled out correctly",
                simulate_character_rounds,
                *[characters,enemy],
                num_rounds=num_rounds
                )
            if alert is not None:
                return export, alert, spinner

            df_all, df_by_rounds, df_by_attacks = res
            del res

            if export_type == "DPR Summary":
                df_summary = summary_stats(df_by_rounds, by_round=True)
                for name, data in zip(names,df_summary):
                    data.insert(0, 'Name', name)
                    dfs.append(data)
            elif export_type == "DPR Distribution":
                for name, data in zip(names,df_by_rounds):
                    data.insert(0, 'Name', name)
                    dfs.append(data)
            elif export_type == "DPA Summary":
                for name, data in zip(names,df_by_attacks):
                    data.insert(0, 'Name', name)
                    dfs.append(data)
            elif export_type == "DPA Distribution":
                for name, data in zip(names,df_all):
                    data.insert(0, 'Name', name)
                    dfs.append(data.sort_values(by=["Name","Round"]))
            
        elif export_type in ["DPR vs Armor Class","DPA vs Armor Class"]:
            export_kwargs = {} #{"index": False}
            by_round = export_type == "DPR vs Armor Class"
            df_acs, alert = try_and_except_alert(
                "Could not simulate combat, please check that all fields are filled out correctly",
                simulate_character_rounds_for_multiple_armor_classes,
                *[characters,enemy],
                armor_classes = range(10,26),
                num_rounds=num_rounds,
                by_round=by_round
                )
            if alert is not None:
                return export, alert, spinner
            if export_type == "DPR vs Armor Class":
                dfs = [reformat_df_ac(df_acs,by_round=by_round)]
            elif export_type == "DPA vs Armor Class":
                dfs = []
                for c_name in names:
                    df_c = df_acs.loc[df_acs['Character']==c_name, :]
                    c_summary = []
                    for n,g in df_c.groupby('Character-Attack'):
                        g["mean"] = g["mean"].astype(float).round(2)
                        attack_name = n[len(c_name)+1:]
                        g["Attack"] = attack_name
                        g.set_index('Armor Class', inplace=True)
                        c_summary.append(g.drop('Character-Attack',axis=1))
                    dfs.append(pd.concat(c_summary))
        else:
            raise PreventUpdate

        # Export to csv
        print(f"Exported {clicked} times")
        filename = f"{export_type}.csv"
        export = dcc.send_data_frame(pd.concat(dfs).to_csv, filename, **export_kwargs)
        return export, None, spinner

# TODO: Add multiple graph options. Add a simulate for multiple enemy armor classes
