from dash import Input, Output, State, Patch, MATCH, ALL, ctx
from plots import COLORS
from components.character_card import generate_character_card
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import json

def get_deleted_characters(existing_characters):
    #TODO: Potentially Simplify this logic
    # Check for deleted character card slots
    deleted_indices = [(ii,c['props']['id']['index']) for ii,c in enumerate(existing_characters) if c['props']['children'] == None]

    # TODO: Notify user of why update is prevented
    # Max number of characters is the number of colors
    max_children = len(COLORS)
    num_children = len(existing_characters)-len(deleted_indices)
    if num_children >= max_children:
        raise PreventUpdate # Not enough colors to add another character
    return deleted_indices, num_children

def get_existing_indices(existing_characters):
    #TODO: Potentially Simplify this logic
    # Check for deleted character card slots
    deleted_indices = [(ii,c['props']['id']['index']) for ii,c in enumerate(existing_characters) if c['props']['children'] == None]

    # TODO: Notify user of why update is prevented
    # Max number of characters is the number of colors
    max_children = len(COLORS)
    num_children = len(existing_characters)-len(deleted_indices)
    if num_children >= max_children:
        raise PreventUpdate # Not enough colors to add another character
    return deleted_indices, num_children


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
        State("character_row","children"),
        Input("add_character_button","n_clicks"),
        State("character_name","value"),
        prevent_initial_call=True
    )
    def add_character(existing_characters, n_clicks, name):
        # Don't update without a name or without a button click
        if not name or n_clicks is None:
            raise PreventUpdate
        
        deleted_indices, num_children = get_deleted_characters(existing_characters)

        init_num_char = 2 # Comes from the 2 default characters on start up
        patched_children = Patch()
        if len(deleted_indices) > 0:
            patched_children[deleted_indices[0][0]] = generate_character_card(name, color=COLORS[deleted_indices[0][0]], index=n_clicks+init_num_char)
        else:
            patched_children.append(generate_character_card(name, color=COLORS[num_children], index=n_clicks+init_num_char))
        return patched_children
    
    @app.callback(
            Output({'type': 'character name',"index": MATCH},"children"),
            Input({'type': 'character name input',"index": MATCH},"value"),
    )
    def update_name(name):
        return name
    
    @app.callback(
            Output({'type': 'character card',"index": MATCH},"children"),
            Input({'type': 'delete character',"index": MATCH},"n_clicks"),
            State({'type': 'character card',"index": MATCH},"id"),
            prevent_initial_call=True
    )
    def delete_character(clicked, id):
        if clicked is None:
            raise PreventUpdate
        return 
    
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
    
    
    #TODO: Fix this callback
    @app.callback(
        Output("character_row","children", allow_duplicate=True),
        State("character_row","children"),
        State({'type': 'character card',"index": ALL},"children"),
        State({'type': 'character card',"index": ALL},"id"),
        Input({'type': 'copy character',"index": ALL},"n_clicks"),
        prevent_initial_call=True
    )
    def copy_character(existing_characters, card_children, id, clicked):
        # Find which button was clicked
        # Have to pass in all values since MATCH only works if the output also has a MATCH
        copy_id = ctx.triggered_id['index']
        copy_index = [triggering_index for triggering_index,i in enumerate(id) if copy_id == i['index']]
        if len(copy_index) != 1:
            raise PreventUpdate
        copy_index = copy_index[0]
        id = id[copy_index]
        card_children = card_children[copy_index]
        clicked = clicked[copy_index]

        if clicked is None:
            raise PreventUpdate
        
        deleted_indices, num_children = get_deleted_characters(existing_characters)
        
        patched_children = Patch()
        # TODO: Simply add 1 to the index, this should deconflict with existing indices...
        index = id["index"]
        new_index = index+1
        card_str = json.dumps(card_children)
        card_str = card_str.replace(f'"index": {index}', f'"index": {new_index}')
        card_children = json.loads(card_str)

        # replace color
        color = COLORS[deleted_indices[0][0]] if len(deleted_indices) > 0 else COLORS[num_children]
        print(color)

        # Create new card in a column
        new_col = dbc.Col(card_children, width=3, id={"type": "character card", "index": new_index})
        
        if len(deleted_indices) > 0:
            patched_children[deleted_indices[0][0]] = new_col
        else:
            patched_children.append(new_col)
        return patched_children
    



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


