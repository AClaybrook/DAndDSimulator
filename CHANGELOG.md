# Changelog

## 2.7.0 (in progress)

Baldur's Gate 3 first. The original simulator and analytics are unchanged, BG3 builds compile to the same Characters.

- **BG3 Party Planner:** a new page section for up to four characters. Each has a class preset, a level for each act checkpoint (End of Act 1 at level 5, Act 2 at 8, Act 3 at 12 by default) and, for each act, gear in twelve slots, buffs and toggles for conditional item effects. An empty gear cell keeps the item from the act before and shows it as a hint.
  - Exact expected damage per round for every character at every act, against the current enemy, as a table and a line chart across the acts.
  - Equipment conflicts per act: unique items wanted by more than one character, a unique item in two slots, a two-handed weapon with an off hand, items found in a later act, and items in the wrong slot. Conflicting cells are highlighted.
  - "Add to simulator" adds the party at an act, or the selected character at every act, as cards.
  - The party is saved in the browser.
- **Typed extra damage:** attacks take extra damage like "1d4 fire" or "2 acid" on a hit. Each part uses its own resistance, vulnerability or immunity and is rounded down separately, so a fire resistant enemy only halves the fire. Dice double on a crit. Validated against the exact math, and the simulation speed is unchanged.
- **Item model:** items have a slot, act, rarity, uniqueness, weapon stats and modelled effects (ability scores, attack and damage bonuses, typed extra damage, crit range, advantage, spell DC, feature flags), each optionally conditional. Base weapons are included and are not unique.
- **Patch 8 item database:** 911 obtainable equippable items exported from bg3.wiki (CC BY-NC-SA 4.0), each linking to its page. Slot, rarity, uniqueness, weapon dice, enchantment and properties come straight from the wiki. The act comes from where the item is found (location, trader, or levelled trader tables): 355 in Act 1, 189 in Act 2, 278 in Act 3, 89 unknown (shown in every act). 311 items have modelled effects, parsed from their special text and passive features with conservative patterns (damage dealt back to attackers is skipped, conditional effects become toggles). Act 1 and Act 2 damage items were checked by hand, with corrections in `bg3/data/effect_overrides.json`. Effects that aren't modelled (i.e. Arcane Acuity, Lightning Charges) are shown when hovering an item.
- **More subclasses in the builder:** Circle of Stars (Luminous Arrow every turn, free Guiding Bolts from Star Maps), Circle of Spores (Symbiotic Entity) and Storm Sorcery (Heart of the Storm damages on a hit or a miss), with a Circle of Stars Druid example. The builder's toggles only list the ones for its classes.
- **Sharing builds:** Export/Import now includes the BG3 planner party (with custom characters, gear, buffs and toggles), so a whole plan is one file.
- **Throwing and spells in the builder:** a thrown weapon routine (Tavern Brawler adds Strength twice, Giant's Rage doubles the rage bonus on throws, Berserkers throw again with Enraged Throw), and casters can pick a levelled damage spell (Fireball, Scorching Ray, Magic Missile...) cast with every slot high enough before falling back to their cantrip. New examples: a Throwzerker and an Evocation Wizard.
- **Weapon proficiencies:** custom characters are proficient with their first class's weapons, the multiclass proficiencies of later classes, subclass grants (Hexblade, War, Tempest and Death clerics, Valour, Bladesinging) and their race's weapons (from bg3.wiki). Other weapons lose the proficiency bonus to hit and are flagged in the conflict report. Class presets are assumed proficient.
- **Example custom characters:** Swashbuckler Rogue, Path of Giants Barbarian, Arcane Archer Fighter, Bladesinger Wizard, Hexblade Warlock, Swarmkeeper Ranger and Tavern Brawler Drunken Master Monk (all Patch 8 subclasses) and a Sorlock, made with the character builder, with gear per act.
- **Example builds:** eight builds with gear for each act (Lae'zel GWM, Karlach Berserker, Astarion dual wield Assassin, Gale Evoker, Gloom Stalker archer, smite Paladin, Open Hand Monk, Eldritch Blast Warlock). The default party is the first four, and it shares Caustic Band, so the conflict report has something to show. Any character can be replaced with an example build.
- **Cross-checked with the community unique item checklist** (a Google Sheet with one tab per area, built from bg3.wiki): 535 of its 544 items match. Its area tabs set the act for 10 items where the wiki-derived act was wrong or unknown (i.e. Voss' Silver Sword and Staff of the Emperor are Act 3, not Act 1). The cross-check also found wiki pages that use other spellings of the item templates (i.e. Mourning Frost, The Blood of Lathander, Knife of the Undermountain King), which are now included, and items marked unobtainable, which are now left out.
- **Refreshing the data:** `python -m bg3.scrape_wiki` (pages, passive features, act categories), `python -m bg3.scrape_sheet` (checklist sheet), then `python -m bg3.build_items`.
- **Gear advice:** for the selected character at an act, what each equipped item adds to damage per round, and the best items for any slot (found by that act) with who else in the party uses them. Shared item conflicts show each character's gain and who it is best on. Instant, from the exact expected damage.
- **Elixirs:** damage elixirs from bg3.wiki are buffs per act (Hill Giant and Cloud Giant Strength, Viciousness, Heroism, Colossus, Battlemage's Power). Most elixirs replace each other, so picking two of those is reported as a conflict.
- **Concentration:** the conflict report flags a character concentrating on two of their own spells (Hex and Divine Favour), and party buffs that need more concentrating casters than the party has free (one Bless covers three characters, Haste one).
- **Per weapon damage rerolls:** attacks can reroll their own damage dice at or below a number (Twist of Fortune, Knife of the Undermountain King), the same as Great Weapon Fighting for that weapon. Editable on attack cards under Weapon.
- **More item effects:** crit-only damage (Craterflesh Gloves, Dolor Amarus), extra Sneak Attack damage (Stalker Gloves), and Tenacity, the Strength modifier as damage on a missed melee attack, which about 35 weapons have. Creature type conditions ("against Gnomes or Dwarves") are toggles. 319 items now have modelled effects.
- **BG3 rules checked against the wiki:** Patch 8 class, subclass, race and feat rules are in `bg3/data/rules.json` with sources. Fixes from them: Savage Attacker in BG3 keeps the higher of two rolls for each die (higher than the 5e version), rage also adds to unarmed attacks, the BG3 Martial Arts die (d4, d6 from 3, d8 from 9) and ki (level + 1) for the monk preset, and Sneak Attack never applies to off-hand attacks. The 5e ruleset keeps the 5e rules.
- **Character builder:** any planner character can be a custom character instead of a class preset: race, point buy with the +2/+1, up to three classes in the order levels are taken (feat levels per class, multiclass spell slots for smites), subclasses including the Patch 8 ones, feats, fighting styles, how the character attacks (two-handed, duelling, two weapons, ranged, unarmed, attack cantrip) and toggles for things the build sets up (rage, Reckless Attack, Vow of Enmity, Hexblade's Curse, surprise). The summary shows the point buy, the class split at each act checkpoint, feat levels and anything not modelled. Modelled features include Extra Attack from every source, Action Surge, Champion crits, superiority dice, Arcane Shots, rage by barbarian level, Frenzy, Elemental Cleaver, smites, Improved Divine Smite, oath channels, Colossus Slayer, Gathered Swarm, Dread Ambusher, Sneak Attack, Assassinate, Fast Hands, Swashbuckler Dirty Tricks, Martial Arts, Flurry of Blows, Manifestation of Body, Agonising Blast, Hexblade's Curse, Pact of the Blade, Lifedrinker, Quickened Spell, Elemental Affinity, Empowered Evocation, Bladesong Extra Attack, War Priest, Divine Strike and Blade Flourish.
- New effect kinds: damage from an ability modifier (Titanstring Bow), extra damage on a crit, and thrown attacks as their own target.

## 2.6.1 (2026-10-12)

Ported from unpushed local work (January 2024).

- **Faster large distributions:** DPR and DPA histograms plot an evenly spaced sample of at most 400,000 values. Tables and stats still use every round. At 1,000,000 rounds the DPA figure builds in 0.2s instead of 9.7s, and the browser receives 2MB instead of 64MB (DPR: 4MB instead of 43MB). The title says when a plot is sampled.
- **Independent validation:** a level 6 Oath of Vengeance Paladin (from an older app export) is checked against damage per round values from an external spreadsheet for armor class 10-25. The exact math matches to 4 decimal places, and the simulation matches within noise.
- Renamed `proficent` to `proficient` (attacks and enemy saving throws). Json files with the old name still load.
- `.gitignore`: fixed a missing line break that merged `__pycache__` and `.venv/`, and added `.vscode` and `.coverage`.

## 2.6.0 (2026-10-12)

Quicker comparisons from the character cards, no changes to the simulation itself.

- **Live expected damage:** every card shows its exact expected damage per round against the current enemy under the name. It updates as you edit the card, the enemy or Rounds Per Fight (attacks update when saved). It uses the same exact math as the Attack Breakdown, so it is instant, and Simulate still gives the full distribution.
- **Copy with a change:** the copy button on a card is now a menu. Besides an exact copy, it makes a copy with one change, named after it (i.e. "Fighter (+2 Str)"):
  - Toggle advantage
  - One level higher (presets are rebuilt like the real class, keeping edits)
  - +2 main ability score (up to 20)
  - Toggle GWM / Sharpshooter
  - Add Bless (+1d4 to hit)

  Changes that aren't possible (i.e. Strength is already 20) show a warning instead.
- Every card and enemy input now has a pattern matching id, so callbacks can react to any field changing.

## 2.5.0 (2026-10-12)

Usability and workflow, no changes to the simulation itself.

### Workflow
- **Quick Start** at the top of the page. It covers the three step workflow and recipes for common questions (best build, is GWM worth it, which feat, scaling, rounds to kill, nova vs sustained, checking the numbers). It can be hidden, and the browser remembers that.
- **"What do you want to know?"** Every graph type now has a one line description of the question it answers. The sweep parameter only shows for the sweep graphs, and the simulator settings are grouped together.
- **Floating Simulate button:** always reachable at the bottom right. After any simulation the page scrolls to the results.
- **Results summary:** a one line summary starts every result, i.e. "Fighter GWM + Advantage leads with 51.55 damage per round, 44% ahead of Fighter Advantage (35.92) against Mind Flayer". Each graph type has its own wording, i.e. rounds to kill or damage per fight.

### Character cards
- **Bonuses tab:** grouped into collapsible sections:
  - Roll Modifiers
  - Crit and Miss Damage
  - Once Per Turn
  - First Round
  - Feats
  - Fighting Styles
  - Class and Race Features

  Sections the character uses start expanded, so presets show what matters.
- **Attack editor:** a hint explains how editing works. The attack list comes first. Uncommon fields are in collapsible sections (Roll Modifiers, Weapon, Spell Saving Throw, Extra Dice, Limits Per Fight). The icon buttons are now labelled **Save**, **Add new** and **Delete**, and "Num Attacks" is now **Copies to Add**.
- **Reading values back:** the UI is now walked recursively. Rows can be nested in any layout, and the round trip tests still check that every preset survives the trip unchanged.

### Sessions
- **Autosave:** every simulation saves the session (characters, enemy and settings) in the browser. After a reload, a banner offers to **restore** it.
- **Export/Import:** now saves and loads the whole session (characters, enemy, rounds, rounds per fight, graph type, sweep parameter and ruleset) as `dnd_session.json`. Older character only files still import, and add their characters to the current ones.

### Errors
- **Specific validation:** problems are listed by character and field before simulating, i.e. "Fighter: Strength is empty", "attack 'Greatsword': Weapon Damage '2d' should be dice or numbers like 1d6, 2". Enemy fields left empty are named too.

### Fixes
- The floating button sits above Dash's dev tools badge, so it can be clicked in debug mode.

## 2.4.0 (2026-10-12)

### New features
- **Fallback attacks:** an attack's new **Fallback For** field names a limited attack. The fallback is only made once that attack is used up, i.e. Fireball while slots last and then Fire Bolt. Without fights (or if the named attack isn't limited), fallback attacks are never made.
- **First round conditions:** **First Round Advantage** and **First Round Hits Are Crits** on the character apply to attack rolls in the first round of every fight. This covers Assassinate.
- **Presets:**
  - **Evocation Wizard (Fireball, then Fire Bolt):** now limited by spell slots. It previously cast its highest slot Fireball every round. It now casts Fireball with every 3rd level or higher slot (Burning Hands with every slot before level 5), then Fire Bolt.
  - **Assassin Rogue (Dual Shortswords):** Assassinate from level 3 (assumes surprise).
  - **Gloom Stalker Ranger (Archer):** Dread Ambusher's extra first turn attack with +1d8 from level 3.
  - **Fighter 2 / Rogue (Dual Shortswords):** Two Weapon Fighting and Action Surge, then Sneak Attack.
  - **Sorcadin (Paladin 6 / Sorcerer):** sorcerer levels add multiclass spell slots for more smites.
- **Attack Breakdown and leaderboard:** the breakdown shows "after Fireball" for fallback attacks, and the leaderboard's attacks per round counts them.

### Changes
- **Speed:** `simulate_attacks` now makes shallow copies of the contexts instead of `dataclasses.asdict`, which deep copies. Repeated runs of the armor class sweep are slightly faster than 2.3. The level sweep benchmark runs 17 presets instead of 13, and is faster per preset.
- **Exact calculator:** first round profiles and fallback attacks are covered. Simulation vs analytic tests run for Fireball then Fire Bolt, Assassinate and Dread Ambusher.

## 2.3.0 (2026-10-12)

### New features
- **Fights and limited resources.**
  - **Uses Per Fight** on attacks: limited attacks such as Action Surge or a quickened spell are made in the first rounds of each fight.
  - **Once Per Turn Uses Per Fight** on characters: smites, superiority dice or sneak attacks run out.
  - **Fractional averages** (i.e. 1.5) are randomized per fight between 1 and 2 uses.
  - **Rounds Per Fight** (simulator input, default 3): every graph averages over fights of that many rounds. Characters without limits are unaffected.
- **Damage per Fight:** a graph of average damage in each round of a fight, which shows opening bursts. The table has total fight damage, round 1 vs the last round, and a csv export with every fight.
- **Rounds to Kill** simulates whole fights for characters with limited resources, so a first round burst counts. Other characters still use the faster resampling.
- **Resource limited presets** (assuming 4 fights per long rest and 2 short rests):
  - Paladin smites use the real paladin spell slot table, and the smite dice use the highest slot.
  - Battle Master superiority dice are limited per short rest.
  - Fighters get **Action Surge**.
  - The Monk's Flurry of Blows strike costs ki.
- **Multiclass presets:**
  - **Sorlock (Warlock 2 / Sorcerer):** Eldritch Blast with Agonizing Blast and Hex, plus a Quickened Eldritch Blast while sorcery points last. Metamagic comes at sorcerer 2 in BG3 (3 in 5e), and Quickened Spell costs 3 sorcery points in BG3 (2 in 5e).
  - **Hexadin (Hexblade 1 / Paladin):** Charisma longsword with Dueling and Hexblade's Curse. Smites use multiclass spell slots (half the paladin level) plus the warlock pact slot each short rest.
- **Leaderboard** shows attacks made per round, and Hit %/Crit % are per attack actually made.
- **Attack Breakdown** shows Uses/Fight when any attack is limited.

### Internals
- `simulate_fight_attacks` simulates fight by fight. `simulate_attacks` uses it only when a character has limits and `rounds_per_fight` is given, so the fast path is untouched.
- `simulate_fights` and `fight_damage` give damage per round of each fight.
- `expected_by_attack` extends the exact calculator to fights. It covers every combination of fractional uses, and a dynamic program over rounds tracks once per turn uses. Tests check the fight simulation against it for Action Surge, limited and crit only smites, quickened blasts and a limited Fireball.
- **Benchmarks:** new lines cover the fight path. With limits, 100k rounds takes about 170 ms; without limits, timings match 2.2. The level sweep benchmark is slower only because presets now have more attacks.

## 2.2.0 (2026-10-12)

### New features
- **Sweep parameter dropdown:** the graph types are now "DPR Sweep" and "DPA Sweep", plus a parameter to sweep. The same applies to csv exports. Parameters:
  - **Armor Class** (10-25), with the GWM/Sharpshooter insights.
  - **Level** (every level of the selected ruleset).
  - **Enemy Save Bonus** (-2 to +14 on every save): shows how saving throw spells fall off against high save monsters.
  - **Attack Ability Score** (8-20 for the ability most of a character's attacks use): shows what an ASI or a stat item is worth.
- **Level sweeps keep your edits to preset characters.** Changes made after adding a preset are carried to every level:
  - Ability scores keep their difference from the preset, so ASIs still happen.
  - Other fields keep your value (i.e. Bless in Bonus Attack Mod).
  - Edited attacks keep their edits, and new copies of an attack get the edits of its last copy.
  - Deleted attacks stay deleted, and added attacks are kept.
- **New builds:**
  - **Champion Fighter (Two Weapon Fighting):** Dual Wielder longswords from level 4, to compare against GWM.
  - **Hexblade Warlock (Pact of the Blade):** a Charisma longsword with Hex and Hexblade's Curse, Thirsting Blade at 5 and Lifedrinker at 12.

### Changes
- **Preset feats without a simulator flag** (i.e. Dual Wielder) can now be part of a build's ASI plan.
- **Speed:** the simulation itself is unchanged. Compared back to back with 2.1 on the same machine, every benchmark is equal or faster.

## 2.1.0 (2026-10-12)

### New features
- **DPR vs Level / DPA vs Level:** sweeps every level of the selected ruleset (1-12 for BG3, 1-20 for 5e), with graph, tables and csv export.
  - Preset characters are rebuilt at each level, so they gain attacks, feats and features like the real class. Their card shows the new **Level Up Preset** field. Edits made after adding the preset are not kept in the sweep.
  - Other characters only change their level (proficiency, rage damage and similar).
- **Sweep leaderboard:** the vs Armor Class and vs Level graphs rank characters by average DPR over the range.
- **Insights:** in DPR vs Armor Class, every character with Great Weapon Master or Sharpshooter turned on gets the exact AC where the -5/+10 stops paying off. It also shows the DPR gain against the current enemy (it can be negative).
- **Once per turn damage options:**
  - **Once Per Turn Eligible** on each attack, so Sneak Attack/Smite can be limited to the right attacks.
  - **Once Per Turn Only On Crit** on the character, for crit fishing with Divine Smite.
- **New builds:**
  - **Battle Master Fighter (GWM):** a damage maneuver on the first hit; superiority dice are d8/d10/d12.
  - **Paladin (Smite Crits Only).**
  - **Thief Rogue:** in BG3, Fast Hands' second bonus action is used for a second off-hand attack from level 3.

### Internals
- `simulate_sweep` generalizes the armor class sweep to any parameter. It only simulates damage, so sweeps stay fast: all 13 presets × 12 levels × 10k rounds takes about 0.2 s, and the benchmark includes it.
- `game_data.classes.character_at_level` rebuilds a preset character at another level.
- `Character.preset` records the build and ruleset a character came from.

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
