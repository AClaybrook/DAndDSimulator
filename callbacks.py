from dash import Input, Output, State, Patch, MATCH, ALL, ctx
from plots import COLORS, generate_plot_data
from components.character_card import generate_character_card, set_attack_from_values, extract_attack_ui_values, extract_character_ui_values
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import json
import numpy as np
from models import Attack, Character, Enemy
from numerical_simulation import simulate_character_rounds

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
            Input({'type': 'delete character',"index": ALL},"n_clicks"), # Unfortunately MATCH doesn't work since there is no corresponding MATCH in the outputs
            State("active_ids","data"),
            prevent_initial_call=True
    )
    def delete_character(clicked, active_ids_json):
        # Get clicked id and index
        delete_id = ctx.triggered_id["index"]
        active_ids, _ = get_active_ids_and_new_id(active_ids_json)
        index = active_ids.index(delete_id)

        # If no button was clicked, don't update
        if clicked[index] is None:
            raise PreventUpdate

        # Don't delete the last character
        if len(active_ids) == 1:
            raise PreventUpdate 
        
        # Delete the character and update
        patched_children = Patch()
        del patched_children[index]
        del active_ids[index]

        return patched_children, set_active_ids(active_ids)
    
    @app.callback(
        Output("character_row","children", allow_duplicate=True),
        Output("active_ids","data", allow_duplicate=True),
        Output('copy_counts', 'data', allow_duplicate=True),
        State("character_row","children"),
        Input({'type': 'copy character',"index": ALL},"n_clicks"),
        State("active_ids","data"),
        State('copy_counts', 'data'),
        prevent_initial_call=True
    )
    def copy_character(characters, clicked, active_ids_json, copy_counts_json):
        # Find which button was clicked
        copy_id = ctx.triggered_id["index"]
        active_ids, new_id = get_active_ids_and_new_id(active_ids_json)
        index = active_ids.index(copy_id)
        if copy_id is None:
            raise PreventUpdate
        
        # If button was not clicked don't update
        if clicked[index] == None:
            raise PreventUpdate
        
        # Check if click count incremented
        copy_counts_temp = json.loads(copy_counts_json)
        copy_counts = {int(k):v for k,v in copy_counts_temp.items()}
        if copy_id in copy_counts and copy_counts[copy_id] == clicked[index]:
            raise PreventUpdate

        # Don't add more than max characters
        if new_id >= MAX_CHARACTERS:
            raise PreventUpdate
        
        # Update copy count with all values
        for id,count in zip(active_ids, clicked):
            copy_counts[id] = count
        
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
        
        return patched_children, set_active_ids(active_ids), json.dumps(copy_counts)
    
    ## Attacks
    # @app.callback(
    #     Output({'type': 'attack',"index": MATCH},"children"),
    #     Input({'type': 'add-attack',"index": MATCH},"value"),
    #     Input({'type': 'attack',"index": MATCH, "num": ALL},"active"),
    #     prevent_initial_call=True
    # )
    # def update_attack(attack):
    #     return attack


    # @app.callback(
    #     Output({'type': 'attack',"index": MATCH},"children"),
    #     Output({'type': 'attack',"index": MATCH, "num": ALL},"active"),
    #     State({'type': 'add-attack',"index": MATCH},"value"),
    #     Input({'type': 'attack',"index": MATCH, "num": ALL},"active"),
    #     prevent_initial_call=True
    # )
    # def update_attack(attack, active_attacks):

    #     return attack


    # WORKS
    # @app.callback(
    #     Output({'type': 'attack',"index": MATCH, "num": ALL},"active"),
    #     Input({'type': 'attack',"index": MATCH, "num": ALL},"n_clicks_timestamp"),
    #     prevent_initial_call=True
    # )
    # def select_attack(selected_attacks):
    #     # Find last clicked attack
    #     max_ = 0 
    #     index = None
    #     for ii, time in enumerate(selected_attacks):
    #         if time is not None and time > max_:
    #             max_ = time
    #             index = ii

    #     # Prevent if all attacks are None
    #     if index is None:
    #         raise PreventUpdate

    #     # Update actively selected attacks
    #     attacks = [index == ii for ii in range(len(selected_attacks))]
    #     return attacks

    # TODO: Check that this works
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
        # Find last clicked attack
        max_ = 0 
        index = None
        for ii, time in enumerate(selected_attacks):
            if time is not None and time > max_:
                max_ = time
                index = ii

        # Prevent if all attacks are None
        if index is None:
            raise PreventUpdate
        
        # Prevent if add or delete attack was clicked recently
        max_add = 0
        if isinstance(add_attack_clicked, list):
            max_add = max([v if v is not None else 0 for v in add_attack_clicked])
        elif isinstance(add_attack_clicked, int):
            max_add = add_attack_clicked
        max_delete = 0
        if isinstance(delete_attack_clicked, list):
            max_delete = max([v if v is not None else 0 for v in delete_attack_clicked])
        elif isinstance(delete_attack_clicked, int):
            max_delete = delete_attack_clicked
        most_recent_button_click = max(max_add, max_delete)
        if max_ < most_recent_button_click:
            raise PreventUpdate

        # Update actively selected attacks
        attacks = [index == ii for ii in range(len(selected_attacks))]

        # Update attack ui to match the values of the selected attack
        attack_ui = set_attack_from_values(json.loads(avals), index)
        
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
        Output('dist-plot',"figure"),
        Input("simulate-button","n_clicks"),
        State("simulate-input","value"),
        State({'type': 'attack_store',"index": ALL},"data"),
        State("character_row","children"),
        prevent_initial_call=True
    )
    def simulate(clicked, num_rounds, attack_stores, characters_list):
        if clicked is None:
            raise PreventUpdate

        # TODO:
        # 1. Get all values from UI
        # 2. Simulate
        # 3. Update figure
        # 4. Update Tables

        
        characters = []
        for ii, c in enumerate(characters_list):
            attacksPython = [Attack(**attack) for attack in json.loads(attack_stores[ii])]
            characters.append(Character(attacks=attacksPython, **extract_character_ui_values(c)))
        
        # TODO: Currently bonus_attacks_mods is erroring, this needs to go to a list
        enemy = Enemy(armor_class=18)

        dfs, df_by_rounds = simulate_character_rounds(characters, enemy, num_rounds=num_rounds)

        data, fig = generate_plot_data(characters, df_by_rounds)
        print(f"test {clicked}")
        return fig