from dash import Input, Output, State, Patch, MATCH, ALL, ctx
from plots import COLORS
from components.character_card import generate_character_card
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import json

MAX_CHARACTERS = min(8,len(COLORS)) # There are 10 colors and 4 characters fit per row, so 8 is a good max

# Manipulating ids
def get_active_ids_and_new_id(ids_json):
    ids = json.loads(ids_json)
    ids_set = set(ids)
    deleted_ids = [i for i in range(len(ids)) if i not in ids_set]
    new_id = deleted_ids[0] if len(deleted_ids) > 0 else len(ids)
    return ids, new_id

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
        # TODO: Find a cleaner way to replace colors... Perhaps find the 
        color = COLORS[new_id]
        character['props']['children']['props']['children'][0]['props']['children']['props']['children'][0]['props']['children']['props']['style']['color'] = color
        print(color)

        patched_children = Patch()
        patched_children.append(character)
        active_ids.append(new_id)
        
        return patched_children, set_active_ids(active_ids), json.dumps(copy_counts)
