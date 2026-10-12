# Changelog

## 2.0.0 (2026-10-12)

A modernization pass: bug fixes in the combat math, a much faster simulation, a game database with level-up presets, and a dashboard that works on current Dash.

### Speed

The simulation is 3.5 to 4 times faster than 1.x. Measured with `python -m benchmarks.benchmark` (4 characters with 3 attacks each, median of several runs):

| Benchmark               | 1.x     | 2.0     |
|-------------------------|---------|---------|
| DPR 10k rounds          | 78 ms   | 20 ms   |
| DPR 100k rounds         | 505 ms  | 132 ms  |
| DPR 1M rounds           | 6.9 s   | 1.7 s   |
| DPR vs AC 10k (16 ACs)  | 434 ms  | 106 ms  |
| DPA vs AC 10k (16 ACs)  | 375 ms  | 105 ms  |
| DPR vs AC 100k (16 ACs) | 1.75 s  | 0.74 s  |

What changed:
- Results are stored column-major, so each column is contiguous in memory.
- Per-round totals are summed in numpy instead of `DataFrame.add` (which also converted everything to float).
- Attack labels are built as categorical codes instead of factorizing strings.
- Percentiles come from bin counts (O(n), no sorting or copying). Tests check that they exactly match `np.percentile`.
- Damage-vs-AC sweeps only simulate the damage column.

### Bug fixes
- **Any character with exactly one attack crashed the simulation.** The per-round DataFrame aliased the per-attack frame.
- **Saving-throw spells were rolled like attack rolls**, using the caster's modifier against their own spell DC. Now the enemy rolls its saving throw against the spell DC, and on a successful save the attack deals its `saving_throw_success_multiplier` share of the damage (for example half for Fireball). Bless and advantage no longer help the enemy's save.
- **Bonus miss damage was always 0**, because it was multiplied by a failed-save multiplier of 0.
- **Ranged off-hand attacks crashed** (`damage_modifier -= character.ability_modifier` subtracted a method).
- **Dice strings with a modifier such as `2d6+3` crashed** (the modifier was a string), and `1d4-1` style modifiers were lost.
- **Several adjacent `0d4` placeholders weren't all removed**, because the list was modified while iterating over it.
- **Sharpshooter applied -5 to hit but never +10 damage.**
- **`always_hit`/`always_crit` on attacks were ignored.**
- **Elemental Affinity was ignored.**
- **Bonus attack dice (e.g. Bless) were rolled with advantage and with the halfling reroll.** They are now rolled normally.
- **`dataclasses.replace` doubled bonus dice:** `__post_init__` re-appended the parsed dice on every copy. The cached internal fields were removed and values are parsed on demand.
- **"DPR vs Armor Class" permanently changed the enemy's AC.** It now uses a copy.
- **Randomize Seed only produced 100 different seeds** (`randint(0, 100)`). It now uses fresh OS entropy.
- **Resistance and vulnerability were applied separately** to hit and crit damage, rounding each down. They now apply to the attack's total.
- **Damage reduction was in the UI but never used.** It is now subtracted from each attack's damage (minimum 0).
- **Weapon enhancement only applied to melee weapons.** It now also applies to ranged and thrown weapons.
- **Off-hand attacks no longer remove a negative ability modifier** (5e rule), and Dueling no longer applies to off-hand attacks.
- **`analytic.hit_chance` raised an error** when the roll had neither advantage nor disadvantage.
- **Rage damage had no +4 at level 16, and Brutal Critical had no extra dice at levels 13 and 17** (5e progression).
- **Dashboard (Dash 3+/dbc 2):** `dbc.Button` no longer has `n_clicks_timestamp`, which broke adding, copying and deleting characters and attacks. Card tabs also rendered empty without an `active_tab`. Copy/delete now use `html.Button` timestamps plus a "last handled click" store. This also fixes the documented quirk where deleting a card re-triggered copy.
- **Copying a character created a duplicate name**, which then blocked simulating. Copies are now named "Name (Copy)".
- **Lists with numbers (e.g. `[2]`) crashed the character card** (`",".join` on ints).

### New features
- **Game database (`game_data/`):**
  - All SRD weapons with damage type and properties.
  - Damaging spells that exist in both 5e and BG3, with cantrip/upcast/projectile scaling.
  - 28 monsters with AC, HP, saving throws, resistances, vulnerabilities and immunities.
  - DMG "CR baseline" enemies (typical AC/HP for CR 1/8 to 20).
- **Level-up presets:** 10 builds (Champion GWM/Archer, Berserker, Smite Paladin, Dual-Wield Rogue, Hunter Ranger, Open Hand Monk, Eldritch Blast Warlock, Fire Bolt Sorcerer, Fireball Wizard).
  - Each build levels from 1 to the ruleset's cap: Extra Attack, feats/ASIs at the class's real ASI levels, Improved Critical, rage damage, Brutal Critical, sneak attack dice, smite slot level, cantrip dice/beams, and so on.
  - Ruleset toggle: **Baldur's Gate 3** (level 12 cap, cantrips scale at 5/10) or **D&D 5e** (level 20, cantrips scale at 5/11/17).
  - Presets produce ordinary characters, so every value can still be edited.
- **Attack templates:** a "Fill from weapon/spell" dropdown on each card's attack editor, aware of the character level and ruleset.
- **Save button for attacks:** editing the selected attack and saving it in place (previously you had to add a new attack and delete the old one).
- **New per-attack fields in the UI:** damage type, heavy, crit on, proficient, advantage, disadvantage, always hit and always crit.
- **New character fields:**
  - **Once Per Turn Damage:** dice added to the first hit each round, doubled on a crit (Sneak Attack, Divine Smite, Colossus Slayer).
  - **Reroll Attack Die On:** Halfling Lucky.
  - **Description:** now saved.
- **Enemy builder:**
  - Monster/CR preset dropdown.
  - Damage-type resistances, vulnerabilities and immunities, including `slashing (nonmagical)` style entries that magic weapons bypass.
  - Per-ability saving throw modifiers.
  - Hit points are used by the new "Rounds to Kill" simulation.
- **Rounds to Kill:** a new graph type and export showing the chance the enemy is dead by each round.
- **Leaderboard:** characters ranked by mean DPR, with % of best, hit % and crit %.
- **Attack Breakdown:** exact to-hit, damage formula, hit/crit chance and expected damage per attack, computed analytically. It's a quick way to check the inputs (the "Preview character bonuses" backlog item).
- **Exact analytic calculator (`computations/analytic.py`):** convolves the d20, bonus dice, rerolls and advantage. It is used to validate the simulation.

### Modernization
- **Packaging:** `pyproject.toml` + `uv.lock` + `.python-version` replace `Pipfile`/`Pipfile.lock` (which pinned numpy 1.25 and Python 3.10). Works with Dash 4, dbc 2, pandas 3, numpy 2 and plotly 6. Removed unused dependencies: scipy, seaborn, numba, chart-studio, snakeviz, memory-profiler, nbformat and pylint.
- **Lint:** ruff replaces pylint (`ruff check .`).
- **Tests:** pytest suite (82 tests) in `tests/`. It covers dice parsing, every class feature in the context calculation, simulation vs exact math for 10 scenarios, the game database, every build at every level for both rulesets, and lossless character → UI card → character round trips (the README's "double check values are identical" item). It also covers importing older exported json files.
- **CI:** GitHub Actions runs lint, tests and the benchmark.
- **Removed:** `app.run_server` replaced by `app.run`, the unused `scipy`-based `computations/stats.py`, the broken `line_plots` (used the removed `go.Line`), the unused store helpers, and `test_files/app_timing_test.py` (replaced by `benchmarks/benchmark.py`).
- **Layout:**
  - Responsive card widths.
  - Readable sidebar.
  - Section panels.
  - Compact form rows.
  - Two-column enemy card.
  - Page title.
  - Button tooltips.
- **Consistent spacing/formatting**, with your original layout and naming kept.

### Notes for existing users
- **`Enemy.saving_throw` was removed.** It was in the UI but never used. Use the per-ability `<stat>_save` fields.
- **`Attack.heavy` is new and is what Great Weapon Master checks.** Older json files without it fall back to `two_handed`.
- **`Character.from_dict` / `Enemy.from_dict` ignore unknown keys,** so old exports still import.
- **Heroku:** the Python buildpack detects `uv.lock` and installs from it. The `Procfile` is unchanged.
