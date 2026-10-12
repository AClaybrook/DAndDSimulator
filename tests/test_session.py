""" Tests for saving and loading sessions """
import json
from pathlib import Path

from components.session import describe_session, make_session, parse_session
from game_data import enemy_from_monster
from game_data.classes import build_character

TEST_FILES = Path(__file__).parent.parent / "test_files"

def test_session_round_trip():
    characters = [build_character("paladin_smite", 5), build_character("sorlock", 8)]
    enemy = enemy_from_monster("Lich")
    session = json.loads(json.dumps(make_session(characters, enemy, {"num_rounds": 5000, "graph": "DPR Sweep", "unknown": 1})))
    loaded, loaded_enemy, settings, error = parse_session(session)
    assert error is None
    assert loaded == characters and loaded_enemy == enemy
    assert settings == {"num_rounds": 5000, "graph": "DPR Sweep"}
    assert describe_session(session).startswith("2 characters vs Lich, saved ")

def test_older_character_lists_still_load():
    with open(TEST_FILES / "characters.json", encoding="utf-8") as f:
        characters, enemy, settings, error = parse_session(json.load(f))
    assert characters and enemy is None and settings == {} and error is None

def test_bad_sessions():
    characters, _, _, error = parse_session({"characters": [{"name": "Ok"}, {"name": "Broken", "attacks": "nope"}]})
    assert [c.name for c in characters] == ["Ok"] and "Broken" in error
    assert parse_session("not a session")[3]
    # A session without an enemy keeps the current enemy
    characters, enemy, _, error = parse_session({"characters": [{"name": "Ok"}], "enemy": None})
    assert [c.name for c in characters] == ["Ok"] and enemy is None and error is None
