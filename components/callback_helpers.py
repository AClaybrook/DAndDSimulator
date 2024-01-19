""" Helper functions for callbacks"""
import json
import pandas as pd
import dash_bootstrap_components as dbc

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

def max_from_list(l):
    """ Returns the max value and index of a list of numbers. Handles edge cases of None and ints"""
    max_ = 0
    index = None
    if isinstance(l, int):
        max_ = l
        index = 0
    elif l is None:
        pass
    elif isinstance(l, list):
        for ii, time_ in enumerate(l):
            if time_ is not None and time_ > max_:
                max_ = time_
                index = ii
    return max_, index

def try_and_except_alert(alert_message, func, *args, **kwargs):
    """Wraps a function in a try except block and returns an alert if an exception is raised"""
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
