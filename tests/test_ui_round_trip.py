""" Characters must survive the trip to the UI cards and back unchanged """
import json
from pathlib import Path
import pytest

from components.character_card import generate_character_card, extract_character_ui_values, characters_from_ui, character_dict_from_labels
from components.enemy_card import generate_enemy_card, extract_enemy_ui_values, enemy_dict_from_labels
from computations.models import Attack, Character, Enemy
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

def test_validation_errors_name_the_field():
    from components.character_card import validation_errors
    attack = {"name": "Greatsword", "damage": "2d", "crit_on": None, "bonus_damage_die_mod_list": ["1d6", "x"]}
    problems = validation_errors({"strength": None, "level": 5, "bonus_attack_die_mod_list": ["1d4"]}, [attack])
    assert "Strength is empty" in problems
    assert "attack 'Greatsword': Crit on is empty" in problems
    assert any("Weapon Damage '2d'" in p for p in problems) and any("Bonus Damage Mod" in p for p in problems)
    assert validation_errors({"level": 5}, []) == ["it has no attacks"]
    good = build_character("fighter_gwm", 5)
    card = serialize(generate_character_card(good.name, character=good, index=0))
    assert validation_errors(extract_character_ui_values(card), [a.to_dict() for a in good.attacks]) == []

def field_values(card, id_type):
    """ {label: value} from the inputs tagged with a pattern matching id, as the expected damage callbacks see them """
    values = {}
    def walk(node):
        if isinstance(node, dict):
            node_id = node.get("props", {}).get("id")
            if isinstance(node_id, dict) and node_id.get("type") == id_type:
                values[node_id["field"]] = node["props"].get("value")
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    walk(card)
    return values

@pytest.mark.parametrize("key", ["paladin_smite", "rogue_assassin", "wizard_fireball"])
def test_tagged_fields_match_card_values(key):
    """ The expected damage badge reads the tagged inputs, which must give the same character as the simulator """
    character = build_character(key, 9)
    card = serialize(generate_character_card(character.name, character=character, index=3))
    from_fields = {**character_dict_from_labels(field_values(card, "character field")), "level": character.level}
    expected = extract_character_ui_values(card)
    assert {k: v for k, v in from_fields.items() if k != "name"} == {k: v for k, v in expected.items() if k not in ("name", "description")} | {"description": ""}

def test_tagged_enemy_fields_match_card_values():
    enemy = enemy_from_monster("Mind Flayer")
    body = serialize(generate_enemy_card(enemy))
    from_fields = enemy_dict_from_labels(field_values(body, "enemy field").items())
    expected = extract_enemy_ui_values(body)
    assert {k: v for k, v in from_fields.items() if k != "name"} == {k: v for k, v in expected.items() if k != "name"}

def test_large_histograms_are_sampled():
    import pandas as pd
    from components.plots import MAX_PLOT_POINTS, generate_plot_data, plot_sample
    df = pd.DataFrame({"Damage": range(10 * MAX_PLOT_POINTS)})
    sample = plot_sample(df, 4)
    assert len(sample) == MAX_PLOT_POINTS // 4 and sample["Damage"].iloc[0] == 0 and sample["Damage"].iloc[-1] == len(df) - 1
    assert plot_sample(df.head(10), 4) is not None and len(plot_sample(df.head(10), 4)) == 10
    fig = generate_plot_data([Character(name="A")], [df], title="DPR")
    assert "sample" in fig.layout.title.text

def test_typed_extra_damage_round_trip_and_validation():
    from components.character_card import validation_errors
    character = Character(name="Flame", attacks=[Attack(name="Flaming Sword", extra_damage_list=["1d4 fire", "2 acid"])])
    assert round_trip(character) == character
    assert validation_errors({}, [{"name": "x", "extra_damage_list": ["1d4 fyre"]}])
    assert not validation_errors({}, [{"name": "x", "extra_damage_list": ["1d4 fire", "2"]}])

def test_planner_characters_survive_the_cards():
    """ Characters the BG3 planner sends to the simulator keep everything the cards can't lose, i.e. BG3 Savage Attacker and rage level """
    from bg3.build import compile_build
    from bg3.presets import PRESETS
    for build in PRESETS.values():
        for act in "123":
            character = compile_build(build, act)
            assert round_trip(character) == character, (build.name, act)
