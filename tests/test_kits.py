""" Item kits and build variants """
from bg3.build import Bg3Build, compile_build, equipment_at
from bg3.items import catalog
from bg3.kits import QUICK_VARIANTS, apply_kit, kit_gear, kits, taken_by_others, variant_build, variant_damage
from bg3.presets import examples
from game_data import enemy_from_monster

def test_kit_items_exist_and_fit_their_slots():
    items = catalog()
    assert len(kits()) >= 12
    for key, kit in kits().items():
        assert kit["act"] in (1, 2, 3) and kit["trigger"], key
        for slot, options in kit["slots"].items():
            assert options, (key, slot)
            for item in options:
                assert item in items and items[item].fits(slot), (key, slot, item)

def test_apply_kit_only_changes_its_slots_and_stays_editable():
    godblade = examples()["1. The Godblade"]
    built, placed, blocked = apply_kit(godblade, "thunder", "1")
    assert placed["gloves"] == "bg3:gloves_of_belligerent_skies" and not blocked
    gear = equipment_at(built, "1")
    for slot in ("melee_off", "helmet", "armour", "ring_1"): # Not in the kit: kept
        assert gear[slot] == equipment_at(godblade, "1")[slot]
    assert equipment_at(godblade, "1")["gloves"] == "bg3:bracers_of_defence" # The original build isn't changed
    # Gear stays ordinary per act gear, so a manual edit afterwards is just another cell
    built.equipment["1"]["gloves"] = "bg3:gloves_of_dexterity"
    assert equipment_at(built, "1")["gloves"] == "bg3:gloves_of_dexterity"
    # Only empty slots: a full build keeps its gloves
    _, placed, _ = apply_kit(godblade, "thunder", "1", only_empty=True)
    assert "gloves" not in placed

def test_kit_skips_items_other_members_have():
    ex = examples()
    party = [ex["1. The Godblade"], ex["3. Hexwing Phantom"]] # The Hexwing wears the Boots of Stormy Clamour
    taken = taken_by_others(party, 0, "1")
    chosen, blocked = kit_gear("thunder", taken)
    assert "boots" in blocked and "boots" not in chosen
    chosen, _ = kit_gear("gwm", {"bg3:soulbreaker_greatsword"})
    assert chosen["melee_main"] == "bg3:svartlebee_s_woundseeker" # The next option

def test_variants_compare_without_changing_the_build():
    godblade = examples()["1. The Godblade"]
    godblade.variants = [{"name": "Thunder kit", "kit": "thunder"}, dict(QUICK_VARIANTS["all_in"])]
    enemy = enemy_from_monster("Mind Flayer")
    rows = variant_damage(godblade, enemy, 3)
    assert [r[0] for r in rows] == ["Build as planned", "Thunder kit", "Bless + Haste + advantage"]
    base, thunder, buffed = (r[2][0] for r in rows)
    assert thunder > base and buffed > thunder # The Necklace and the Ring of Elemental Infusion count, with their effects set up
    assert equipment_at(godblade, "1")["gloves"] == "bg3:bracers_of_defence"
    # Class presets get advantage from a build flag
    preset = Bg3Build("Fighter", "fighter_gwm", variants=[dict(QUICK_VARIANTS["advantage"])])
    assert compile_build(variant_build(preset, preset.variants[0]), "1").advantage
    assert Bg3Build.from_dict(godblade.to_dict()).variants == godblade.variants # Saved with the party
