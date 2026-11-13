# Changelog

## 3.0.0 (in progress)

- **Gear solver and Pareto frontier:** the planner's Frontier tab searches gear and elixir combinations for a member at an act (each slot's
  options, then a beam search and a polish pass; item pairs like Broodmother's Revenge + Ring of Regeneration tried together) and plots
  damage against AC with the frontier marked. Use a point, or keep the frontier as variants. Costs the numbers miss are flagged (the Risky
  Ring's disadvantage on saves).
- **Leaderboard: saved variants.** Your party's what-ifs (Variants tab, kept frontier points) are ranked as rows of their own.
- **Medium armour accessories:** gloves, helmets and boots that need Medium or Heavy Armour proficiency (Legacy of the Masters) end Mage
  Armour, Unarmoured Defence, Bracers of Defence and Bladesong, as body armour does (seen in game).
- **Saved parties:** the planner's "Saved parties" loads a party of build doc builds with gear changes, the trade-offs worked out for
  them as variants (Variants tab) and the takeaways as notes (bg3/data/parties.json). A variant's elixir now replaces the build's.
- **Elixir of Bloodlust:** assumes its extra action on 2.5 of a fight's 3 turns (was 1.5), for a player who aims kills to trigger it.
- **Act 3 item map:** the map page has Act 3, its items placed by their bg3.wiki minimap coordinates on a plain grid per region (Rivington,
  Wyrm's Crossing & Wyrm's Rock, Lower City, Undercity, Upper City, elsewhere). 208 of the 216 items on the wiki's Act 3 list are placed.
- **Broodmother's Revenge:** its poison coats weapon attacks (not spells), and a Ring of Regeneration keeps it up every turn.
- **Wavemother's Cloak:** +2 armour class from Water Layer Protection.
- **Necklace of Elemental Augmentation:** no longer adds to Booming Blade, which doesn't trigger it in game.
- **Spellmight Gloves:** Booming Blade gets +1d8 on its weapon damage and +1d8 on its thunder, with no -5 penalty (seen in game).
- **Strength gear and finesse weapons:** Gauntlets of Hill Giant Strength and the giant strength elixirs now count for Shadow Blade
  and finesse weapons when they beat the character's Dexterity (they were ignored).
- **Eldritch Knight:** War Magic (Eldritch Knight 7) gives a main hand weapon attack with the bonus action on turns the action casts
  Booming Blade, in place of the off-hand swing. Shadow Blade builds now get Action Surge, which they were missing.
- **Best in slot gear:** the planner's Gear tab can fill a character's gear for an act (or every act) with the best of everything found
  by then, for the most damage, the highest armour class or the best overall score, the weapon included (one that fits the build's grip).
  It is searched for the build against the current enemy, not a fixed list, and can leave the rest of the party's items alone. "Compare
  first" keeps your gear and adds the set as a variant; Fill has an Undo.
- **Settle shared items:** the Conflicts tab proposes who keeps each item two characters wear (whoever gains the most damage from it) and
  the best item nobody wears for the others, with other options to pick instead. A slot left empty is filled in the first later act
  that has something for it.
- **Clerics:** Spiritual Weapon (a toggle: its own attack every round for 1d8 + 1 + Wisdom force, more from higher slots) and Spirit
  Guardians cast with the day's best slots (3d8 + 1d8 a slot level), costing the action of the first round. Before, the aura was always
  3d8 and counted in every fight even with two slots a day, which overstated level 5 clerics. Death Domain: a necrotic aura and Toll the
  Dead on two creatures (Reaper). Two example clerics, and builds from the build doc that use these spells now have them (Deathreaper,
  Tempest Bladesinger, Unstoppable Death Monk, Circle of the Stars / Light Cleric).
- **Play modes:** a variant can be another way to play the same character: a different routine, cantrip or levelled spell, with or
  without Spirit Guardians cast first ("Play mode" in the Variants tab). The tab leads with a chart of each way's gain over the build as
  planned against one to four enemies, since a single target spell and an area spell trade places as enemies are added. Builds imported
  from the build doc get a mode for each other damage spell their write-up names (the Deathreaper: Circle of Death, Dethrone, Inflict
  Wounds, Thorn Whip, Shocking Grasp, Bursting Sinew).
- **Spell save DC** on each party card, by act, for builds that force saving throws; hover for each spell's save, its DC and the
  enemy's chance to fail. The same lines are in the score details, and the DC is a column of the variants table.
- **Death Domain, Necromancy and Spores:** Circle of Death, Dethrone (its own DC 18, once a long rest), Thorn Whip and Bursting Sinew;
  Touch of Death on melee spell attacks (Inflict Wounds, Shocking Grasp, Thorn Whip) as well as weapon hits, with a limited spell's casts
  split between the ones that carry a charge and the rest; Reaper on every necromancy cantrip; Divine Strike in the domain's damage type
  and only on weapon hits; Halo of Spores as a reaction every round; a bonus action shot with an off hand hand crossbow for casters (a
  toggle). Spirit Guardians can be cast first around another spell, which keeps its own slots when it is level 4 or higher.
- **Items:** Staff of Cherished Necromancy (enemies save against necromancy spells with disadvantage; Life Essence's free cast as a
  toggle), Amulet of the Devout (+2 spell save DC and one more Channel Divinity charge), Armour of Agility's full Dexterity modifier.
- **Engine:** saving throws rolled with disadvantage, a spell's own fixed DC, and fallbacks that chain (cast A while its uses last, then
  B while its uses last, then C), in the analytic, exact and simulated engines.
- **Build doc import:** a full caster holding a staff casts its cantrip instead of swinging the staff, Toll the Dead is recognised, a
  second hand crossbow goes in the off hand, and Booming Blade is only assumed when the write-up names it.
- **Best in slot gear you can trust more:** searching for damage no longer trades armour for clothes with a small bonus (a swap may
  not lower armour class), only offers weapons the build is proficient with, skips Wyll's Infernal Rapier, and replaces an item the
  build already wears only when it adds 3% or more (planned items often have effects the model does not count). Each change shows
  what it adds.
- **Bigger charts, fewer panels:** the planner's damage chart and the leaderboard's scatter are taller and get half the page, the
  simulator's distributions are taller, the overall score moved into its own tab, and several helper texts are shorter.
- **A hold can fail:** "Enemy paralysed" in the Party tab now counts for the share of turns the hold lands (the target's Wisdom save
  against the caster's spell save DC, recast when it breaks) instead of always; its line shows the chance against the chosen enemy.
  The Resonance Stone gives enemies disadvantage on Intelligence, Wisdom and Charisma saves, for the hold and for every save spell
  (Toll the Dead, Spirit Guardians).
- **Belm and Rhapsody:** Belm in the off hand makes the bonus action attack with the main hand weapon (Perfectly Balanced Strike: its
  ability modifier and on-hit effects, once a turn), so a Shadow Blade build swings the blade a third time. Rhapsody's Scarlet
  Remittance (+1 to hit, damage and spell save DC a kill, up to +3) is a toggle, on for the doc builds that wear it; before, the
  dagger only counted +1 to spell attacks. Effects of one item that share a condition are one toggle.
- **Build doc re-import (32 builds):** the Metamagic Godblade (4 Draconic Sorcerer / 2 Crown Paladin / 6 Bladesinger) is new, and the
  importer reads more of the structured format: a Respec line gives the class split at an act when levelling in order doesn't (a pure
  Bladesinger until the multiclass comes together), Permanent buffs gives Auntie Ethel's Hair, "Twinned Haste" counts as Haste, the
  item casting ability comes from the caveat's wording, and a build written twice is read from its last section.
- **Quickened Booming Blade:** a melee Sorcerer (level 3) makes a second main hand Booming Blade attack with the bonus action, one
  a long rest per 3 sorcerer levels; the off-hand attack is made in the other turns.
- **Best in slot:** a swap that a later one makes pointless (a helmet for advantage, then a ring that gives it too) is put back.
- **Great Weapon Master's bonus attack:** a crit or a kill with a melee weapon attack gives another one with the bonus action, now
  counted for every build with the feat: the chance one of the turn's melee attacks crits (crit range, advantage and Haste count)
  plus the kills a fight from the Estimates box (1.5, the same number Bloodlust uses; 0 for a boss fight). A bonus action attack
  the build makes every turn (off hand, Polearm Master's butt end, Flick o' the Wrist) is made in the other turns, so a build
  whose bonus action already is a full weapon attack gains nothing.
- **Weapon buffs:** Magic Weapon (+1 to hit and damage) and the Drakethroat Glaive's elemental weapon (+1 to hit and 1d4, on any one
  weapon until a long rest, Shadow Blade included) are in the Buffs tab and stack with Haste, Bloodlust and the Resonance Stone.
- **Conflicts you can fix in one click:** an item worn before the act it is found in has "Move it there", Auntie Ethel's Hair on two
  characters has "Only <name>", and a problem that repeats in every act is listed once. A gear cell holding an item from a later act
  now shows it in red instead of looking empty.
- **Gear advice as a chart:** what each worn item adds is a bar chart, and the best items table gets the full width (its last columns
  were cut off). Build tab toggles are short labels with the detail on hover, and its Sneak Attack note follows the worn weapon.
- **Leaderboard gear variants** follow the planner's best in slot rules: a real gain to replace a worn item, items the damage can't
  judge stay, and Max damage doesn't give up armour class. Run 16.
- **Old page warning:** the built page isn't in git, so after pulling new code it can be stale; the app now says so (in the terminal
  and at the top of the page) with the command to rebuild.
- **Party synergies on the damage chart:** the planner's chart and the party cards now show damage with the synergies the party sets up
  every fight (a carried Resonance Stone doubling psychic damage, Reverberation lowering saves), with a "Party synergies" switch to see
  each character alone. Best in slot, gear advice and variants follow the switch, so psychic items are valued against the enemy the
  party really fights. Hovering a point shows the damage alone next to it.
- **Your own estimates:** the Buffs tab has an Estimates box for the guesses behind a build's numbers, only the ones it uses: kills a
  fight with the Elixir of Bloodlust (usually 1.5) and reaction attacks a fight from Polearm Master (1) and Sentinel (1.5). 0 turns one off.
- **Best in slot leaves what it can't judge:** a worn item with effects the damage doesn't count is undersold by the numbers, so it now
  stays when none of its effects are counted (Band of the Mystic Scoundrel, Helmet of Arcane Acuity) and needs a 10% gain when only
  some are (Staff of Cherished Necromancy). The result lists what stayed and what the numbers alone preferred, with "Compare replacing
  them" to see that set as a variant. Item names mark how much is counted: ✦ all, ◐ some, ○ none.
- **Act 3 bows:** The Dead Shot adds the proficiency bonus twice to its own attack rolls (Keen Attack, which was only a note, so the
  bow was undersold). Gontr Mael's Promised Victory is advantage on about a quarter of its shots (a hit marks the target with Guiding
  Bolt for the next attack roll that turn, after a DC 15 Dexterity save) instead of a toggle that gave every shot advantage; Bolt of
  Celestial Light's radiant rider and Celestial Haste (half an action a fight, nothing when Haste is already on) are counted. The
  engine has advantage on a share of an attack's rolls (`advantage_chance`), the same in the analytic, exact and simulated numbers.
- **Auntie Ethel's Hair** on more than one party member shows in the Conflicts tab (it is given once a playthrough).
- **Illithid powers:** a checkbox for every custom character (off by default). Psionic Overload adds 1d4 psychic to every attack
  roll, Favourable Beginnings the proficiency bonus to the first attack of a fight, and Luck of the Far Realms makes one hit a day a
  critical hit. Psionic Overload is taken as already up, like a buff. Mind Blast, Concentrated Blast, Cull the Weak and Black Hole
  aren't counted.
- **Build audit (Godblade, Hexwing Phantom, Deathreaper, Arcane Deadeye):** Auntie Ethel's Hair as a permanent +1 (a select next to
  the +2/+1, read from the build doc); Arcane Synergy on the ring and the diadem (the spellcasting ability modifier on weapon attacks,
  with the ability of the casting class taken last); Great Weapon Master with a versatile weapon held in both hands (Phalar Aluve);
  Gontr Mael's Guiding Bolt as a toggle; Gathered Swarm's damage is psychic. The Helmet of Arcane Acuity and Gloves of the Automaton
  gave +1 to an ability score where the game gives +1 to its saving throws. Imported builds switch on item conditions they always
  meet (Strange Conduit Ring while Shadow Blade is up, Arcane Synergy with Booming Blade).
- **Balduran's Giantslayer** doubles the Strength modifier's damage (and has advantage against Large creatures as a toggle).
- **Review fixes, rules:** Haste and Bloodlust give a whole Attack action outside Honour Mode (Extra Attack included) and one attack in
  it; the Honour Mode toggle is now offered to every class. BG3 Savage Attacker and Great Weapon Fighting reach rider and once per turn
  dice (smites, Sneak Attack, item damage), and Savage Attacker a thrown weapon's own dice. Lifedrinker is necrotic, so the Resonance
  Stone no longer doubles it. Quickened Spell shares the spell slots and the sorcery points (a Fireball sorcerer was overstated). The pact
  weapon's Charisma only applies to the main hand melee weapon. Multiclass caster levels sum their fractions before rounding down.
  Smites only on melee weapon hits. All checked against bg3.wiki.
- **Several once per turn pools:** a character can have Sneak Attack every round next to limited radiant smites, each with its own uses
  and damage type, in the analytic, exact and simulated engines (`once_per_turn_extra`). A fallback attack can have its own uses.
- **Charts drawn in the browser:** the simulator's backend sends chart data and the front end draws it, in one palette for both themes
  (checked for colour vision deficiencies and contrast). Damage distributions are one row per character on a shared axis instead of
  overlapping histograms. The headline is the exact number on the cards; the simulated mean is in the table. The Python plotly
  dependency is gone.
- **Layout:** the simulator's editor sits beside the results instead of over them. The planner leads with its chart, shows only the gear
  slots in use (one act at a time on a phone), has one buff by act grid and the overall score as a stacked bar per act. The leaderboard has
  denser rows, one armour class column for the chart's act, and its chart and table are linked. The map's key sits outside the plot and
  names avoid each other. Every page was checked at phone width.
- **Typed API:** `api/schemas.py` describes every request and response, responses are checked against it, and the front end's types are
  generated from it (`uv run python -m api.openapi`; a test fails when they are out of date). vitest unit tests for the front end's logic.
- **Attack roles as fields:** attacks carry `action` (action, bonus, reaction, extra), `tags`, `base` and `label`, replacing checks on
  their names.
- **For a hosted copy:** `DAMAGE_LAB_READ_ONLY=1` turns off the doc import and leaderboard saves; the doc import only follows Google Docs
  links; `python -m api` listens on this machine only unless `HOST` is set.
- **Cleanup:** `random/` and `utilities/` removed, test fixtures under `tests/fixtures/`, simulation timings in the log instead of printed.
  The example party wears armour.
- **New front end, page by page:** a React + TypeScript app (`frontend/`) over a FastAPI backend (`api/`), replacing the Dash app as pages
  are rebuilt. The Simulator is first: characters with their live expected damage on the left, the answer up front (who leads and by how
  much), the same plots as before, and sortable, filterable tables folded underneath. Characters open in a side panel with Stats, Attacks
  and Bonuses tabs, rarely used fields folded away. Results update shortly after each edit. Everything is kept in the browser.
  `uv run python -m api` serves it on http://localhost:8000.
- **Every page in the new app:** the Party planner (a strip of the party with damage per act; Gear, Build, Buffs, Variants and Gear advice
  tabs; results tabs for the damage chart and score, conflicts, and the party fight, synergies and roles), the Leaderboard (best builds up
  front, a damage vs armour class scatter, sortable rankings with a detail panel per build, saved runs to compare), and the Act 1 map
  (region switcher, markers drawn in the browser so every filter is instant, the party's gear as a checklist). One enemy is shared by the
  planner and the simulator.
- **Redesign:** navigation moved to the top bar, a refined dark theme, every page built from the same parts (a header with its controls,
  headline numbers, titled cards). Less to open by hand: results are tabs instead of folded sections, editors show every field group,
  attacks are a list with the selected one's fields beside it, and the enemy is a summary with a side panel editor.
- **Act 2 item map:** the Shadow-Cursed Lands minimap (Last Light Inn, Reithwin, Moonrise Towers, the Ruined Battlefield) with every Act 2
  item spot from bg3.wiki, plus the Gauntlet of Shar, the Shadowfell and the Mind Flayer Colony on coordinate grids. An Act switch on the
  map page picks the regions, the party gear checklist (now filterable by member) and the items with no spot. Missable items carry a ⚠ in
  the planner's gear lists.
- **Rules fixes (Tactician):** Pact of the Blade's Extra Attack now stacks with another class's outside Honour Mode (a Paladin 5 /
  Warlock 5 attacks 3 times with the pact weapon; an "Honour Mode rules" toggle turns it off). Sneak Attack only with finesse or ranged
  weapons. Shadow Blade needs a Sorcerer, Warlock or Wizard level. New attack routines: Polearm (Glaive; Polearm Master's butt end gets
  GWF and GWM) and Shadow Blade with a shield (Duelling, +2 AC).
- **Reaction attacks:** Polearm Master (an enemy entering your reach, about once a fight) and Sentinel (an enemy next to you attacking an
  ally, about every other round) as expected reaction attacks, with advantage from the Halberd of Vigilance; a "reactions" toggle.
  Finesse weapons from gear hit with the higher of Strength and Dexterity.
- **Smites keep their own damage type:** once per turn damage can have its own type (radiant for smites) with its own resistance or
  vulnerability, in the analytic, exact and simulated engines; Improved Divine Smite is a radiant rider. Before, a smite on a Shadow
  Blade hit took the blade's psychic vulnerability from the Resonance Stone. docs/padlock_vs_sorcadin.md has a Resonance Stone section.
- **Elixirs:** Bloodlust gives an extra Attack action on a kill (estimated every other turn against a group), every elixir replaces the one
  before (Heroism included), Viciousness and Battlemage's Power come from Act 2 trader stock, and each elixir says where to get it.
  docs/padlock_vs_sorcadin.md compares them per build and act (docs/elixirs.png).
- **Sneak Attack on reactions:** a reaction attack on an enemy's turn gets its own Sneak Attack (once per turn, not per round), with a
  finesse weapon. New example build: Fighter 6 / Swashbuckler 6 with The Dancing Breeze, Polearm Master and Sentinel.
- **Smites average the day's slots:** sustained damage counts each smite at the average size of the day's slots (pact slots back on
  short rests, Flexible Casting's extra slot, less the slot Shadow Blade used) instead of the best slot's size, which overstated every
  Paladin, the Sorcadin most.
- **Padlock vs Sorcadin vs polearm builds:** eight new example builds and docs/padlock_vs_sorcadin.md, sustained and burst damage by act.
- **Smaller additions:** re-import the build doc from the planner; overlay example builds on the planner's damage chart; leaderboard and
  map settings kept in the URL; keyboard shortcuts (1-4 pages, t theme, r simulate again, ? list); a light theme; a browser smoke test
  of every page in CI.
- **The Dash app is gone:** its last features moved over (session export/import with the BG3 party in one file, "To simulator" from the
  planner, the copy-with-a-change menu on simulator characters, CSV downloads of every table and of the raw simulated data), then
  `app.py`, `components/` and the Dash and gunicorn dependencies were removed. `Procfile` serves `uvicorn api.main:app`.

## 2.7.0 (in progress)

Baldur's Gate 3 first. The original simulator and analytics are unchanged, BG3 builds compile to the same Characters.

- **BG3 Party Planner:** a new page section for up to four characters. Each has a class preset, a level for each act checkpoint (End of Act 1 at level 5, Act 2 at 8, Act 3 at 12 by default) and, for each act, gear in twelve slots, buffs and toggles for conditional item effects. An empty gear cell keeps the item from the act before and shows it as a hint.
  - Exact expected damage per round for every character at every act, against the current enemy, as a table and a line chart across the acts.
  - Equipment conflicts per act: unique items wanted by more than one character, a unique item in two slots, a two-handed weapon with an off hand, items found in a later act, and items in the wrong slot. Conflicting cells are highlighted.
  - "Add to simulator" adds the party at an act, or the selected character at every act, as cards.
  - The party is saved in the browser.
- **Leaderboard, round 2:** a local database (local_data/bg3.sqlite, committed on purpose for this single user tool; gitignore it before making the repository public) keeps every run with each build's full spec, and "Compare with" shows what changed against any saved run. New scenarios: "Reliable buffs" (Bless, the build's own buffs, and advantage only with a dependable source: hiding, Shadow Blade in dim light, Reckless Attack, Trip Attack, Topple, Darkness with Devil's Sight) and "Max nova" (round 1 with Bless, Haste, Phalar Aluve's Sing, advantage and the target held, every resource spent). Rankings against 1 to 4 enemies: casters use their best area spell, clerics Spirit Guardians and Hunters Horde Breaker when that beats their planned routine. Gear variants for every build at every act, found by searching every armour, accessory and shield the build can wear (BG3 proficiencies; monks and Bladesingers stay unarmoured): max damage, max AC and best overall score, with AC and score columns to weigh damage against survivability. "Find gear variants for my party" does the same for the party.
- **Exact damage distributions:** the damage per round histograms have a line per character with the exact probability of every damage value (computations/exact.py), the distribution the simulation samples from. Same rules as the simulation (crits, rerolls, Savage Attacker, resistances rounded down, once per turn damage, limited resources over a fight); checked against 200,000 simulated rounds. Hover it for the mean, spread, skew and the chance every attack misses. Plots without an exact distribution (damage per attack) get a smooth kernel density fit with a cross-validated width.
- **Damage leaderboard:** every example build (19 presets, 31 build doc builds, 12 rough versions of starred Reddit builds) and your party ranked by damage at Acts 1, 2 and 3, each with its own planned gear, in the planner and in docs/leaderboard.md. Everyone gets the same conditions: one reference enemy per act (AC 14 / 16 / 18), single target, and a scenario (no buffs, advantage, Bless, Bless and advantage, or as planned). "Overall" averages each build's share of the best damage at each act. Each build has a fingerprint of its spec; save a ranking in the browser and the Change column shows which builds changed and by how much, and the download includes every build's full spec. `python -m bg3.leaderboard` regenerates the snapshot (bg3/data/leaderboard.json).
- **Build doc imports repaired:** free text builds without ability scores used one generic spread (Strength 15, Charisma 8 even for Sorlocks); they now get a point buy for their main stats, ability improvements when no feats are listed, repeated class rows dropped, a class named only in the title added, and monks and archers without a weapon fight unarmed or with a bow. Every guess is listed in the build's notes.
- **Faster planner:** edits, member switches and variants respond in about 2 seconds instead of 20, and the page loads in about 10 seconds instead of 26. The Dash renderer re-checks every component on the page for each component a callback adds, so result tables are now rendered as a single HTML block, unchanged outputs aren't sent, the map page only updates while it's open, the AC, score and damage chart share one callback, and the variant actions are one picker (pick a variant, then "Use as gear" or delete) instead of buttons on every row.
- **Overall score:** a 0-100 score per character and act that weighs damage, area damage, toughness (hit points and AC), control, support and utility, so all round builds rank fairly against pure damage. Hover for the parts; the method and its limits are in docs/scoring.md.
- **Armour class:** a Defence table shows each character's AC at each act and the chance an enemy hits it (attack bonus editable), with the sources on hover; variants show AC too, so the High AC kit's +AC is visible next to its damage cost. Shield of Faith, Mage Armour and Warding Bond are new buffs; Bladesong is a toggle.
- **Map missables:** red rings and a warning line on items you can lose to story choices or by missing a step, with an "Only missables" filter.
- **Reverberation:** the thunder kit's stacks, their 1d4 thunder burst and a "Prone from Reverberation" party synergy.
- **Damage against groups:** the planner's damage table, chart and variants can count 1 to 4 enemies. Weapon attacks still hit one, area spells hit up to their size (Fireball 4, Shatter 3...), Spirit Guardians is a cleric option whose aura hits 3 enemies every round, and Hunters can take Horde Breaker. Hover a damage cell for all four counts.
- **Item kits and variants:** 15 curated Act 1 kits (Thunder/Reverberation, Lightning Charges, Arcane Synergy, Fire, Cold, Psychic, Great Weapon Master, Throwing, Dual wield, Archer, Hand crossbows, Healer, Bard, High AC unarmoured, Heavy armour tank). "Quick gear" fills a kit's slots at an act in one click, skipping items another character already has, and every gear cell stays editable as before. Variants compare a character with a kit, buffs or advantage side by side by act without touching its gear, and "Use as gear" copies a variant in.
- **Act 1 map:** a separate page (sidebar "Act 1 Map", or `/map`) with the notable Act 1 gear and key pickups on the game's minimap images. Hover a marker for what's there and its minimap coordinates, click it for details and wiki links. It shows Rare and better by default; filters cover rarity, gear used by the example builds, trader stock and items inside dungeons (marked at the entrance), and a search highlights items on any map. Item locations come from bg3.wiki; the images are Larian's minimap textures via bg3.wiki, calibrated to the in-game coordinates (`python -m bg3.build_map`). The planner party's gear for a chosen act gets gold rings, with a checklist to tick off items as you collect them, and a list beside the map names every item shown.
- **Typed extra damage:** attacks take extra damage like "1d4 fire" or "2 acid" on a hit. Each part uses its own resistance, vulnerability or immunity and is rounded down separately, so a fire resistant enemy only halves the fire. Dice double on a crit. Validated against the exact math, and the simulation speed is unchanged.
- **Item model:** items have a slot, act, rarity, uniqueness, weapon stats and modelled effects (ability scores, attack and damage bonuses, typed extra damage, crit range, advantage, spell DC, feature flags), each optionally conditional. Base weapons are included and are not unique.
- **Patch 8 item database:** 911 obtainable equippable items exported from bg3.wiki (CC BY-NC-SA 4.0), each linking to its page. Slot, rarity, uniqueness, weapon dice, enchantment and properties come straight from the wiki. The act comes from where the item is found (location, trader, or levelled trader tables): 355 in Act 1, 189 in Act 2, 278 in Act 3, 89 unknown (shown in every act). 311 items have modelled effects, parsed from their special text and passive features with conservative patterns (damage dealt back to attackers is skipped, conditional effects become toggles). Act 1 and Act 2 damage items were checked by hand, with corrections in `bg3/data/effect_overrides.json`. Effects that aren't modelled (i.e. Arcane Acuity, Lightning Charges) are shown when hovering an item.
- **More subclasses in the builder:** Circle of Stars (Luminous Arrow every turn, free Guiding Bolts from Star Maps), Circle of Spores (Symbiotic Entity) and Storm Sorcery (Heart of the Storm damages on a hit or a miss), with a Circle of Stars Druid example. The builder's toggles only list the ones for its classes.
- **Party roles, synergies and fights:** a new planner section shows each member's roles (front line, ranged, healer, face, skills, control, support), roles nobody covers and overlaps, as notes rather than errors. Synergies one member sets up for the party are toggles: the Resonance Stone (double psychic damage), Darkness (advantage for members who see through it), Reverberation (enemy saves -2) and Hold Person (advantage, melee hits crit). It shows each member's damage alone and with synergies, and simulates the party fighting an enemy with the hit points you set.
- **Build doc import:** `python -m bg3.doc_import <doc link>` reads builds from a build reference document (read only) into planner examples. Free text builds are read best effort; `docs/bg3_build_format.md` describes a structured format that imports exactly.
- **Shadow Blade and Booming Blade** in the character builder.
- **Lightning Charges:** the Act 1 Sparky Points, Joltshooter, Spellsparkler and Sparkle Hands add +1 to hit and 1 lightning damage to every attack when the character makes attacks that gain charges (the 1d8 at 5 charges isn't modelled yet).
- **Story choices:** items from different outcomes of the same quest (sparing or killing the Nightsong, delivering Nere's head to Glut or Spaw, Florrick's and Thrinn's pick-one rewards) are flagged in the conflict report and gear suggestions, even within one character. The choices are listed in `bg3/data/story_choices.json` with their bg3.wiki quest pages.
- **Faster plots:** the damage distributions are binned before they are sent to the browser, so they plot every simulated round (no more sampling) and the page loads about 45% smaller.
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
