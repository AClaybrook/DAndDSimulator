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
        card_str = card_str.replace(f'"index": {copy_id}', f'"index": {new_id}') #TODO: this is not working, fix it
        character = json.loads(card_str)
        # # TODO: replace color
        color = COLORS[new_id]
        print(color)

        patched_children = Patch()
        patched_children.append(character)
        active_ids.append(new_id)
        
        return patched_children, set_active_ids(active_ids), json.dumps(copy_counts)
    
    # @app.callback(
    #         Output({'type': 'character card',"index": MATCH},"children", allow_duplicate=True),
    #         Input({'type': 'copy character',"index": MATCH},"n_clicks"),
    #         State({'type': 'character card',"index": MATCH},"children"),
    #         State({'type': 'character card',"index": MATCH},"id"),
    #         prevent_initial_call=True
    # )
    # def copy_character(clicked, card_children, id):
    #     if clicked is None:
    #         raise PreventUpdate
        
    #     # Simply add 1 to the index, this should 
    #     index = id["index"]
    #     card_str = json.dumps(card_children)
    #     card_str = card_str.replace(f'"index": {index}', f'"index": {index+1}')
    #     card_children = json.loads(card_str)
    
    #     return card_children
    
    
    # #TODO: Fix this callback, OLD
    # @app.callback(
    #     Output("character_row","children", allow_duplicate=True),
    #     State("character_row","children"),
    #     State({'type': 'character card',"index": ALL},"children"),
    #     State({'type': 'character card',"index": ALL},"id"),
    #     Input({'type': 'copy character',"index": ALL},"n_clicks"),
    #     prevent_initial_call=True
    # )
    # def copy_character(existing_characters, card_children, id, clicked):
    #     # Find which button was clicked
    #     # Have to pass in all values since MATCH only works if the output also has a MATCH
    #     copy_id = ctx.triggered_id['index']
    #     copy_index = [triggering_index for triggering_index,i in enumerate(id) if copy_id == i['index']]
    #     if len(copy_index) != 1:
    #         raise PreventUpdate
    #     copy_index = copy_index[0]
    #     id = id[copy_index]
    #     card_children = card_children[copy_index]
    #     clicked = clicked[copy_index]

    #     if clicked is None:
    #         raise PreventUpdate
        
    #     deleted_indices, num_children = get_deleted_characters(existing_characters)
        
    #     patched_children = Patch()
    #     # TODO: Simply add 1 to the index, this should deconflict with existing indices...
    #     index = id["index"]
    #     new_index = index+1
    #     card_str = json.dumps(card_children)
    #     card_str = card_str.replace(f'"index": {index}', f'"index": {new_index}')
    #     card_children = json.loads(card_str)

    #     # replace color
    #     color = COLORS[deleted_indices[0][0]] if len(deleted_indices) > 0 else COLORS[num_children]
    #     print(color)

    #     # Create new card in a column
    #     new_col = dbc.Col(card_children, width=3, id={"type": "character card", "index": new_index})
        
    #     if len(deleted_indices) > 0:
    #         patched_children[deleted_indices[0][0]] = new_col
    #     else:
    #         patched_children.append(new_col)
    #     return patched_children
    



    # @app.callback(
    #         Output("character_row","children", allow_duplicate=True),
    #         # State("character_row","children"),
    #         Input({'type': 'delete character',"index": MATCH},"n_clicks"),
    #         State({'type': 'character card',"index": MATCH},"id"),
    #         prevent_initial_call=True
    # )
    # def delete_character(clicked, id):
    #     if clicked is None:
    #         raise PreventUpdate
        
    #     print(clicked)
    #     print(id)
        
    #     patched_children = Patch()
    #     del patched_children[id]

    #     return patched_children


    # @app.callback(
    #         Output({'type': 'character name',"index": MATCH},"children", allow_duplicate=True),
    #         Input({'type': 'delete character',"index": MATCH},"n_clicks"),
    #         State({'type': 'character card',"index": MATCH},"id"),
    #         prevent_initial_call=True
    # )
    # def delete_character(clicked, id):
    #     if clicked is None:
    #         raise PreventUpdate

    #     return "testing"


