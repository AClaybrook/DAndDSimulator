""" Sessions: characters, enemy and simulator settings saved together, for export/import and the browser's last session """
from dataclasses import asdict
from datetime import UTC, datetime

from computations.models import Character, Enemy

SESSION_VERSION = 2
# Simulator setting: component id
SETTINGS_IDS = {
    "num_rounds": "simulate-input",
    "rounds_per_fight": "rounds-per-fight",
    "graph": "simulate-type",
    "sweep_parameter": "sweep-parameter",
    "ruleset": "ruleset",
}

def make_session(characters, enemy, settings, bg3_party=None):
    """ A json serializable session from character and enemy dictionaries (or dataclasses), simulator settings and the BG3 planner party """
    def as_dict(x):
        return x if isinstance(x, dict) else asdict(x)
    session = {
        "version": SESSION_VERSION,
        "saved_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "characters": [as_dict(c) for c in characters],
        "enemy": as_dict(enemy) if enemy is not None else None,
        "settings": {k: v for k, v in settings.items() if k in SETTINGS_IDS and v is not None},
    }
    if bg3_party:
        session["bg3_party"] = bg3_party
    return session

def parse_session(data):
    """ Characters, enemy and settings from a session, or from an older export that only has a list of characters.
        Returns (characters, enemy or None, settings, error message or None). Stops at the first character that fails to load """
    if isinstance(data, list):
        raw_characters, raw_enemy, settings = data, None, {}
    elif isinstance(data, dict) and "characters" in data:
        raw_characters, raw_enemy, settings = data["characters"], data.get("enemy"), data.get("settings") or {}
    elif isinstance(data, dict):
        raw_characters, raw_enemy, settings = [data], None, {}
    else:
        return [], None, {}, "Import Failed. The file doesn't contain characters"

    characters, error = [], None
    for c in raw_characters:
        try:
            characters.append(Character.from_dict(c))
        except Exception as e: # pylint: disable=broad-exception-caught
            print(e)
            name = c.get("name", "Unknown") if isinstance(c, dict) else "Unknown"
            error = f"Import Failed. Cannot parse character '{name}'. Skipping any remaining characters"
            break
    enemy = None
    if raw_enemy:
        try:
            enemy = Enemy.from_dict(raw_enemy)
        except Exception as e: # pylint: disable=broad-exception-caught
            print(e)
            error = error or "Could not load the enemy from the file, the current enemy was kept"
    return characters, enemy, {k: v for k, v in settings.items() if k in SETTINGS_IDS}, error

def describe_session(session):
    """ i.e. '4 characters vs Mind Flayer, saved 2026-10-12 03:15 UTC' """
    characters = session.get("characters") or []
    enemy = (session.get("enemy") or {}).get("name")
    saved_at = (session.get("saved_at") or "").replace("T", " ")[:16]
    text = f"{len(characters)} character{'s' if len(characters) != 1 else ''}"
    if enemy:
        text += f" vs {enemy}"
    return text + (f", saved {saved_at} UTC" if saved_at else "")
