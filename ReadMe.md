# Dungeons and Dragons Damage Simulator

Live here: https://d-and-d-damage-simulator-745953dd5908.herokuapp.com/

##  For the D and D Theory Craftors of the World
![Alt Text](assets/CharacterBuilder.PNG)
![Alt Text](assets/Simulator.PNG)

* Simulates many thousand turns of combat to find distributions of damage for a given character
* Compare D&D characters at once for the theory crafters of the world, i.e.:
    * A Barbarian with Reckless Attacks with Advantage
    * A Fighter With the two Great Weapon Master Feat
* Not sure which Feat to take for optimal DPS? Well why not simulate them all and find out?

## References/Motivation ##
* https://www.youtube.com/@DnDDeepDive
* https://www.reddit.com/r/BG3Builds/comments/157p0cl/the_math_of_critical_hits_in_dd_5e_is_critfishing/?onetap_auto=true
* https://statmodeling.stat.columbia.edu/2014/07/12/dnd-5e-advantage-disadvantage-probability/
* https://forums.giantitp.com/showthread.php?582779-Comprehensive-DPR-Calculator-%28v2-0%29
* https://anydice.com/program/22f8c

## How to Install and Run Locally
* Download or git clone the repo from: https://github.com/AClaybrook/DAndDSimulator
* Install [uv](https://docs.astral.sh/uv/getting-started/installation/) (it installs the right Python version for you)
* `uv sync` to create the virtual environment and install the dependencies
* Launch the App on localhost 8050:
    * `uv run python app.py`
    * Or select the `.venv` interpreter and run app.py from VsCode
* Development:
    * `uv run pytest` to run the tests (the simulation is validated against exact analytic results)
    * `uv run ruff check .` to lint
    * `uv run python -m benchmarks.benchmark` to time the simulation, run it before and after changing `computations/`

See [CHANGELOG.md](CHANGELOG.md) for what changed in 2.0.

## Using the Dashboard
0. **BG3 Party Planner** (top of the page): up to four characters, each a class preset or a custom character (race, point buy, classes in order, subclasses, feats, fighting styles), with gear and buffs for each act checkpoint (End of Act 1 at level 5, Act 2 at 8, Act 3 at 12, editable per character). An empty gear cell keeps the item from the act before. The planner shows the exact expected damage per round of every character at every act, lists equipment conflicts (a unique item wanted by more than one character in the same act, a unique item in two slots, a two-handed weapon with an off hand, items found in a later act) and highlights the conflicting cells. "Add to simulator" adds the party at an act, or one character at every act, as cards for the full simulation.
1. **Characters**: add presets (Preset, Level, +), which level up like the real class, or blank characters, then tweak them. Each card shows its exact expected damage per round against the current enemy, updated as you edit. Card sections expand when the character uses them, attacks are edited by clicking one, changing it and pressing Save.
2. **Enemy**: load a monster or a CR baseline, or type in armor class, hit points, saves and resistances.
3. **Simulate**: pick what you want to know (each graph type says what it answers) and press Simulate, the floating button works from anywhere. Results start with a one line summary.

Common questions:
* **Which build does the most damage?** Add a few presets, Simulate with DPR Distribution and read the Leaderboard.
* **Is Great Weapon Master or Sharpshooter worth it?** DPR Sweep over Armor Class, the Insights table shows the armor class to turn it off.
* **Which feat or ASI should I take?** Use the copy menu on a card to make a copy with one change (+2 main ability score, a level up, advantage, GWM/Sharpshooter, Bless), or copy it exactly and change something yourself. The expected damage under each name compares them right away, Simulate for the full picture.
* **How does my build scale?** DPR Sweep over Level, presets level up and keep your edits.
* **How fast can we kill this boss?** Load the monster and run Rounds to Kill.
* **Nova or sustained damage?** Set Rounds per Fight and run Damage per Fight.

Sessions: every simulation saves the session in your browser, after a reload you are offered to restore it. Export saves the characters, enemy and settings to a json file that Import loads back (older character only files are still added to the current characters).

# Technical Notes/Features:

## Project Layout
* `computations/`: the generic simulator
    * `models.py`: Character, Enemy and Attack dataclasses, and the translation of class features into attack/damage contexts
    * `numerical_simulation.py`: vectorized numpy simulation
    * `analytic.py`: exact expected damage, used for tests and the Attack Breakdown tables
* `game_data/`: the optional game database, everything it produces is a plain Character/Enemy/Attack that can still be edited
    * `weapons.json`, `spells.json`, `monsters.json`: SRD weapons, spells, and monster defenses
    * `classes.py`: prebuilt characters that level up (attacks, feats/ASIs, subclass features, cantrip scaling, spell slots) for the BG3 and 5e rulesets
* `bg3/`: Baldur's Gate 3 planning, builds compile to plain Characters so the simulator is unchanged
    * `checkpoints.py`: act checkpoints and their levels
    * `items.py`, `data/items.json`: items, their modelled effects (with conditional toggles), and base weapons
    * `buffs.py`: buffs during fights (Bless, Haste, Hex, Divine Favour)
    * `build.py`: a build (class preset + gear, buffs and conditions per act) and compiling it at an act
    * `party.py`: equipment conflicts in a party
    * `scrape_wiki.py`, `scrape_sheet.py`, `build_items.py`: export the Patch 8 item pages from bg3.wiki and the community checklist sheet, and build `data/items.json` (hand checked fixes in `data/effect_overrides.json`)
    * `presets.py`: example builds with gear per act
    * `character.py`, `abilities.py`: the character builder (race, point buy, classes, subclasses, feats) compiled to a Character from the Patch 8 rules in `data/rules.json`
* `components/`: Dash layout and callbacks
* `tests/`, `benchmarks/`

## Completed Features:
* UI: Character, Enemy, Simulator, and Tables
* Collapsable nav/sidebar
* Import and Export of characters via json
* Simulate Combat from UI values
* 6 simulation types and corresponding plots:
    * Damage Per Round
    * Damage Per Attack
    * Damage Per Round/Attack sweeps over a parameter:
        * Armor Class, with insights on when to turn GWM/Sharpshooter off
        * Level, preset characters level up realistically and keep your edits
        * Enemy Save Bonus
        * Attack Ability Score
    * Rounds to Kill (uses enemy hit points)
    * Damage per Fight, damage by round of the fight with limited resources
* Export Damage Results to csv
* Implement easy callbacks in javascript
* Reduce memory of dataframes
* Random Seed toggle for random vs repeatable results
* Character presets that level up realistically, with a BG3 or 5e ruleset
* Weapon and spell templates for attacks
* Monster presets and CR baselines, damage type resistances/vulnerabilities/immunities, per ability saving throws
* Once per turn damage (sneak attack, smite), per attack eligibility and crit only (crit fishing)
* Leaderboard and exact per attack breakdown
* Validated numerical sims with tests

## Roadmap
Rough priority order, the first items have the most impact for the least work.

### Done in 2.1
* DPR vs Level sweep with realistic preset level ups, sweep leaderboards
* GWM/Sharpshooter breakeven insights
* Per attack once per turn eligibility, crit fishing smites
* Battle Master, BG3 Thief and crit fishing Paladin builds

### Done in 2.2
* Sweep parameter dropdown with Enemy Save Bonus and Attack Ability Score sweeps
* Level sweeps keep manual edits to preset characters
* Two Weapon Fighting Champion and Hexblade Warlock builds

### Done in 2.3
* Fights and limited resources: uses per fight for attacks and once per turn damage, Rounds per Fight, Damage per Fight view, fight based Rounds to Kill
* Resource limited presets (smite slots, superiority dice, Action Surge, ki) and multiclass presets (Sorlock, Hexadin)

### Done in 2.4
* Fallback attacks (Fireball while slots last, then Fire Bolt), first round advantage and auto crits
* Assassin Rogue, Gloom Stalker Ranger, Fighter 2 / Rogue and Sorcadin presets, slot limited Fireball Wizard

### Done in 2.5
* Dashboard usability: collapsible card sections, labelled attack editing, quick start with recipes, graph descriptions, floating Simulate button, results summary, saved and restorable sessions, readable validation errors

### Done in 2.6
* Copy with a change from the card (variants for quick what-if comparisons) and live expected damage per round on each card

### Done in 2.7 (in progress)
* BG3 Party Planner: act checkpoints, gear and buffs per act, equipment conflicts, expected damage per act, send to the simulator
* Typed extra damage on hits (i.e. 1d4 fire on a slashing weapon), resisted separately

* Patch 8 item database from bg3.wiki (911 items, 311 with modelled effects), cross-checked with the community unique item checklist sheet, example builds with gear per act

### Next (BG3)
* Arcane Acuity, Lightning Charges and other stacking item effects, per-weapon rerolls (Twist of Fortune)
* Data driven character builder: race, class levels and subclasses (including the Patch 8 subclasses), point buy, feats
* Elixirs and camp buffs, party buffs from one caster's concentration
* Story-exclusive items (one path or the other) in the conflict report
* Illithid powers

### Next
* Conditional damage: GWM bonus attack on a crit/kill, Colossus Slayer only on damaged targets, Toll the Dead d12 vs damaged targets
* Surprise as a fight setting (i.e. a chance the enemy is surprised) instead of assuming it for Assassinate
* Arcane Recovery, Font of Magic and other ways to regain slots
* BG3 specific mechanics: weapon actions, Elemental Adept, Savage Attacker per BG3 patch rules, BG3 item database (i.e. +1d4 rings, Gloves of the Belligerent Skald), verified against the game

### Later
* Multiple enemies and area of effect spells
* Party mode: buffs between characters (Bless, Haste, Faerie Fire) and turn order
* Saving/uploading enemies, editable monster database from the UI
* Extract "insights", i.e. when to turn on/off GWM/Sharpshooter (the AC where it stops paying off)
* Damage Source diffs, i.e. the damage gained from Bless
* Variable Color Theme
* Better app logging

### Backlog
* Ability checks
* Status effects: stunned, restrained, prone
* Enemies fighting back (hit points/AC of the character mattering)

## Current Assumptions/Limitations ##
* Calculations follow the BG3 ruleset by default. Presets and attack templates can use the 5e ruleset instead, which mostly changes the level cap and cantrip/extra attack progression
* Classes and Races are not fully implemented, just the main damaging perks
* Resources are tracked per fight, not per rest: limited attacks and once per turn damage have average uses per fight (fractional averages are randomized per fight). Presets convert per rest resources assuming 4 fights per long rest and 2 short rests. Characters without limits behave as if resources are unlimited
* Limited attacks are used in the first rounds of a fight, limited once per turn damage on the first hits. Fallback attacks are made once the limited attack they replace is used up
* First round conditions (advantage, hits are crits) apply to the first round of every fight, i.e. Assassinate assumes the enemy is surprised
* No multitarget, single target only
* Enemys do not fight back/ not considering back and forth combat. So a character with 10 hp and 10 ac is just as good at damage as a character with 100 hp and 20 ac. Only enemy defensive stats matter
* Do not consider turn order/initive
* 1 character at a time, no party mode
* 1 Enemy at a time
* Focused on damage, therefore actions that do not involve damage as not implemented
* Validation of build feasability is not done. Garbage in/ garbage out
    * Only some basic checks like GWM only with twohanded weapons 
* Adjusting rolls needed for critial hits (Crit on) needs to be applied manually, i.e. a Fighter taking the Champion subclass, spell sniper feat need to be accounted for by manually reducing the Character Crit on field (the Champion presets do this for you)
* Bonus damage dice use the attack's damage type for resistances, i.e. Hex on an Eldritch Blast is treated as force damage
* Once per turn damage applies to the first hit (or crit, if crit only) of any eligible attack roll (not saving throw spells)
* Rounds to kill resamples simulated rounds, since rounds are independent of each other
* no status effects, stunned, restrained etc

### Callback Implementation Quirks:
* Copy callback and others get called unintentionally when a character is deleted, because the Inputs techically change
    * Solution is to check the time of the clicked button (n_clicks_timestamp) against the last handled click, stored in `last-card-click`
    * dbc.Button no longer has n_clicks_timestamp, so the card buttons are html.Button with bootstrap classes
* Can not use MATCH for an Inuput when an Output doesn't have a MATCH, thus have to reach in ALL Inputs

### Build ideas
* Bladesinger
* Ice Sorcerer, prone
* Fire sorceror
* Gloomstalker, assasin
* Wardomain cleric, 
* Life domain cleric, healing extreme
* Barbarian cleave (bleed build)
* Bard crossbow arcane acuity
* Pure Fighter

