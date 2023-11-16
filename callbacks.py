from dash import Input, Output, State, Patch, MATCH
from plots import COLORS
from components.character_card import generate_character_card
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

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
        
        #TODO: Potentially Simplify this logic
        # Check for deleted character card slots
        deleted_indices = [(ii,c['props']['id']['index']) for ii,c in enumerate(existing_characters) if c['props']['children'] == None]

        # TODO: Notify user of why update is prevented
        # Max number of characters is the number of colors
        max_children = len(COLORS)
        num_children = len(existing_characters)-len(deleted_indices)
        if num_children >= max_children:
            raise PreventUpdate # Not enough colors to add another character

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

    @app.callback(
            Output({'type': 'character card',"index": MATCH},"children"),
            # State("character_row","children"),
            Input({'type': 'delete character',"index": MATCH},"n_clicks"),
            State({'type': 'character card',"index": MATCH},"id"),
            prevent_initial_call=True
    )
    def delete_character(clicked, id):
        if clicked is None:
            raise PreventUpdate
        
        print(clicked)
        print(id)
        
        # patched_children = Patch()
        # del patched_children[id]

        return 


    
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
