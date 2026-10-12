""" Characters must survive the trip to the UI cards and back unchanged """
import json
from pathlib import Path
import pytest

from components.character_card import generate_character_card, extract_character_ui_values, characters_from_ui
from components.enemy_card import generate_enemy_card, extract_enemy_ui_values
from computations.models import Character, Enemy
from game_data import enemy_from_monster
from game_data.classes import BUILDS, build_character

TEST_FILES = Path(__file__).parent.parent / "test_files"

def serialize(component):
    """ What dash sends back to callbacks """
    return json.loads(json.dumps(component.to_plotly_json(), default=lambda c: c.to_plotly_json()))

def find_store(component):
    """ The attack store data inside a serialized card """
    if isinstance(component, dict):
        if isinstance(component.get("props", {}).get("id"), dict) and component["props"]["id"].get("type") == "attack_store":
            return component["props"]["data"]
        return next((s for s in map(find_store, component.values()) if s), None)
    if isinstance(component, list):
        return next((s for s in map(find_store, component) if s), None)
    return None

def round_trip(character):
    card = serialize(generate_character_card(character.name, character=character, index=0))
    return characters_from_ui([card], [find_store(card)])[0]

@pytest.mark.parametrize("key", BUILDS)
def test_character_round_trip(key):
    character = build_character(key, 11)
    assert round_trip(character) == character

def test_extract_character_values_uses_model_field_names():
    card = serialize(generate_character_card("Test", character=Character(name="Test", GWM=True, once_per_turn_die_mod_list=["3d6"]), index=0))
    values = extract_character_ui_values(card)
    assert values["GWM"] is True and values["once_per_turn_die_mod_list"] == ["3d6"]
    assert set(values) <= {f for f in Character.__dataclass_fields__}

def test_enemy_round_trip():
    lich = enemy_from_monster("Lich")
    body = serialize(generate_enemy_card(lich))["props"]["children"]["props"]["children"][1]["props"]["children"]
    parsed = Enemy.from_dict(extract_enemy_ui_values(body))
    for field in ["name", "armor_class", "hit_points", "resistances", "immunities", "intelligence_save"]:
        assert getattr(parsed, field) == getattr(lich, field)
    assert parsed.saving_throw_modifier("strength") == lich.saving_throw_modifier("strength")

@pytest.mark.parametrize("filename", ["characters.json", "characters_skip.json"])
def test_import_older_exports(filename):
    with open(TEST_FILES / filename, encoding="utf-8") as f:
        data = json.load(f)
    characters = []
    for c in data:
        try:
            characters.append(Character.from_dict(c))
        except Exception: # characters_skip.json purposely has a broken character
            break
    assert characters and all(c.attacks for c in characters)
