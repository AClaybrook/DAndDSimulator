""" Helper functions for callbacks"""
import json
import pandas as pd
import dash_bootstrap_components as dbc
from dash import ctx

# Manipulating ids
def get_active_ids_and_new_id(ids_json):
    """ Returns a list of ids and a new id"""
    ids = json.loads(ids_json)
    new_id = get_new_id(ids)
    return ids, new_id

def get_new_id(ids):
    """ Returns a new id, which will be the first deleted id or the next id"""
    ids_set = set(ids)
    deleted_ids = [i for i in range(len(ids)) if i not in ids_set]
    new_id = deleted_ids[0] if len(deleted_ids) > 0 else len(ids)
    return new_id

def set_active_ids(ids):
    """ Returns a json string of the ids"""
    return json.dumps(ids)

def button_was_clicked():
    """ True if the callback was triggered by a real button click.
        Pattern matching callbacks also fire when buttons are added or removed, in which case n_clicks is None/0 """
    return bool(ctx.triggered_id) and any(t.get("value") for t in ctx.triggered)

def new_card_click(timestamps, last_handled):
    """ The timestamp of the card button that triggered the callback if it is a new click, else None.
        Callbacks with ALL inputs also fire when cards are added or removed, re-reporting old clicks """
    triggered = ctx.triggered_id
    if not triggered:
        return None
    index = [i["id"]["index"] for i in ctx.inputs_list[0]].index(triggered["index"])
    timestamp = timestamps[index]
    if not timestamp or timestamp <= (last_handled or 0):
        return None
    return timestamp

def reset_clicks(component):
    """ Recursively resets n_clicks of a serialized component, so a copied button doesn't look like it was just clicked """
    if isinstance(component, dict):
        return {k: (None if k in ("n_clicks", "n_clicks_timestamp") else reset_clicks(v)) for k, v in component.items()}
    if isinstance(component, list):
        return [reset_clicks(c) for c in component]
    return component

def replace_card_index_and_color(component, old_index, new_index, color):
    """ Recursively replaces the pattern matching index and the character name color of a serialized card """
    if isinstance(component, dict):
        new = {}
        for k, v in component.items():
            if k == "id" and isinstance(v, dict) and v.get("index") == old_index:
                new[k] = {**v, "index": new_index}
            else:
                new[k] = replace_card_index_and_color(v, old_index, new_index, color)
        props = new.get("props", {})
        if isinstance(props.get("id"), dict) and props["id"].get("type") == "character name":
            props["style"] = {**props.get("style", {}), "color": color}
        if props.get("style", {}).get("borderTop"):
            props["style"] = {**props["style"], "borderTop": f"3px solid {color}"}
        return new
    if isinstance(component, list):
        return [replace_card_index_and_color(c, old_index, new_index, color) for c in component]
    return component

def rename_card(component, new_name):
    """ Recursively sets the character name (header and name input) of a serialized card """
    if isinstance(component, dict):
        new = {k: rename_card(v, new_name) for k, v in component.items()}
        props = new.get("props", {})
        id_type = props.get("id", {}).get("type") if isinstance(props.get("id"), dict) else None
        if id_type == "character name":
            props["children"] = new_name
        elif id_type == "character name input":
            props["value"] = new_name
        return new
    if isinstance(component, list):
        return [rename_card(c, new_name) for c in component]
    return component

def unique_name(name, existing):
    """ 'Fighter' -> 'Fighter (Copy)', 'Fighter (Copy 2)', ... """
    candidate, ii = f"{name} (Copy)", 2
    while candidate in existing:
        candidate, ii = f"{name} (Copy {ii})", ii + 1
    return candidate

def alert(message, color="danger"):
    """ Dismissable alert """
    return dbc.Alert(message, dismissable=True, is_open=True, color=color)

def try_and_except_alert(alert_message, func, *args, **kwargs):
    """Wraps a function in a try except block and returns an alert if an exception is raised"""
    try:
        return func(*args, **kwargs), None
    except Exception as e:
        print(f"{func.__name__} failed: {e!r}")
        return None, alert(f"{alert_message} ({e})")

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
        for n, g in df.groupby('Character-Attack'):
            reshaped = pd.concat({n: g.set_index('Armor Class').drop(['Character-Attack', 'Character'], axis=1).T})
            new_dfs.append(reshaped)
        return pd.concat(new_dfs).T

def per_attack_ac_tables(df_acs, character_names):
    """ Splits the DPA vs Armor Class results into one table per character, used by tables and exports """
    data_summary = []
    for c_name in character_names:
        df_c = df_acs.loc[df_acs['Character'] == c_name, :]
        c_summary = []
        for n, g in df_c.groupby('Character-Attack', sort=False):
            g = g.copy()
            g["mean"] = g["mean"].astype(float).round(2)
            attack_name = n[len(c_name)+1:]
            g["Attack"] = attack_name
            c_summary.append(g.set_index('Armor Class').drop(['Character-Attack'], axis=1))
        data_summary.append(pd.concat(c_summary) if c_summary else pd.DataFrame())
    return data_summary
