# BG3 Planner: To Do and Done Notes

Working notes for the Baldur's Gate 3 direction. The CHANGELOG has the user facing summary of each release.

## Active
- [ ] Open a PR with the BG3 planner work once you have looked at it

## Priorities (most useful while playing first)
1. [ ] Map: missables, i.e. items lost to story choices (bg3/data/story_choices.json) or to leaving Act 1 (Grove raid, Nightsong, Crèche), flagged on the map and in the planner
2. [ ] Map: per member filter for the party gear layer, and where to get each Act 2/3 item once those maps exist
3. [ ] Map: more key pickups (permanent buffs, tomes, crafting) in bg3/data/map_pickups.json, and from the build doc's Permanent buffs lines
4. [ ] Map: Act 2 and 3 (Shadow-Cursed Lands and Lower City minimap images exist on bg3.wiki; calibrate them like Act 1), Grymforge and Rosymorn images if they turn up
5. [ ] Doc builds: re-import once the doc uses docs/request_spec.md; importer support for Level order, Respec and Party blocks
6. [ ] Engine and party items below (synergies, two sided fights, more subclass features)

## Next
- [ ] Doc builds: ask for the structured format (docs/bg3_build_format.md) in the build doc, then re-import; free text builds miss ability scores, routines and exact slots
- [ ] Synergies: Arcane Acuity stacks (Hat of Fire Acuity, Battlemage's gloves), Bless/Haste from another member's concentration, Bleeding, Radiating Orb (defensive), Steeped in Bliss mental save disadvantage
- [ ] Party fight: several enemies, summons (Accursed Spectre, undead), healing and enemy damage (a two sided fight)
- [ ] Roles: skills and backgrounds in the builder (face and lockpicking are guessed from Charisma and Rogue levels), armour class for front liners
- [ ] Builder: Eldritch Knight War Magic with Booming Blade, Bladesong, Accursed Spectre, Divine Smite variants (Wrathful, Staggering)
- [ ] Builder: more subclass features: Wildheart aspects (bleeding/poisoned targets), Beast Master and summons (need a companion model), Eldritch Knight War Magic and Shadow Strike (both trade Extra Attack for less damage, so low priority), Druid with a Scimitar or Shillelagh instead of a Longsword
- [ ] Builder: Smites as spells (Searing, Branding, Wrathful), Wild Shape, Enraged Throw's Strength based damage
- [ ] Elixir of Bloodlust (extra action on a kill) and kill based effects in general: needs a fight against several enemies (kill chance per round from Rounds to Kill), the single target model gives them nothing
- [ ] Arcane Acuity, Arcane Synergy, Radiating Orb, Reverberation and the 1d8 burst at 5 Lightning Charges (stacking effects that build up over a fight)
- [ ] More story choices in bg3/data/story_choices.json (Act 3 companion endings, Grove raid), each checked against its bg3.wiki quest page
- [ ] Finish the hand review of parsed Act 3 item effects (first pass done: crit-only damage, Sneak Attack bonuses, Tenacity, creature type conditions)
- [ ] Smaller first load: the BG3 item lists (0.22MB) could load when the planner is first opened
- [ ] Illithid powers

## Done
- 2026-10-31: Map: party gear layer (gold rings on the gear the planner party wears at a chosen act, with a collected checklist saved in the browser, "only my party's gear" filter), an "On this map" item list beside the map, an option to name every marker, readable hover boxes, cleaner where-to-find text
- 2026-10-31: Act 1 map page (/map): notable items and key pickups on the game's minimap images (Wilderness, Underdark, Crèche; Grymforge, Mountain Pass and Nautiloid on a coordinate grid), rarity filters (Rare and up by default), "used by example builds" filter, trader stock and dungeon interiors toggles, item search, click for details and wiki links, and a list of notable items with no map location. Images calibrated to the in-game minimap coordinates from waypoints (bg3/build_map.py)
- 2026-10-30: docs/request_spec.md, the structured format request for the build doc's maintainer
- 2026-10-29: Typed extra damage on hits (resisted separately), validated against the exact math
- 2026-10-29: BG3 build model: class preset + gear, buffs and conditional toggles per act, act checkpoints (levels 5/8/12)
- 2026-10-29: Party conflicts: shared unique items, duplicates, two-handed with an off hand, wrong slots, items from later acts
- 2026-10-29: BG3 Party Planner page: gear table per act, buffs, expected damage per act, conflicts, send to the simulator
- 2026-10-29: Patch 8 item database from bg3.wiki (911 obtainable items, 311 with modelled effects), Act 1 and 2 effects hand checked
- 2026-10-29: Cross-check with the community unique item checklist sheet: act fixes, skipped template spellings, unobtainable items
- 2026-10-29: Eight example builds with gear per act, loadable into any party slot
- 2026-10-29: Gear advice: what each equipped item adds, best items for a slot at an act (with who else uses them), and each character's gain from a shared item in the conflict report
- 2026-10-29: Elixirs from bg3.wiki as buffs (Hill Giant and Cloud Giant Strength, Viciousness, Heroism, Colossus, Battlemage's Power), with a warning when more than one elixir that replaces the others is selected
- 2026-10-29: Concentration checks: two of a character's own concentration spells (Hex and Divine Favour), and party buffs that need more concentrating casters than the party has free (Bless covers 3, Haste 1)
- 2026-10-29: Per weapon damage rerolls (Twist of Fortune, Knife of the Undermountain King), the same as Great Weapon Fighting on that weapon, also editable on attack cards
- 2026-10-29: Item parser fixes from an Act 3 review: crit-only damage (Craterflesh Gloves, Dolor Amarus), extra Sneak Attack damage (Stalker Gloves), Tenacity's Strength damage on a miss (about 35 weapons), creature type conditions become toggles, weapon-only bonuses, editor comments removed from text (319 items with modelled effects)
- 2026-10-29: Gear item lists are sent once per slot group and filtered by act in the browser (page 1.5MB -> 1.0MB); off hands no longer offer two-handed weapons; unknown act items sort last
- 2026-10-29: Patch 8 class, subclass, race and feat rules researched from bg3.wiki into bg3/data/rules.json (12 classes, 58 subclasses, 31 races, 41 feats, with sources; 9 values marked unverified)
- 2026-10-29: BG3 rule fixes from that research: per die Savage Attacker (keeps the higher of each die), rage adds to unarmed attacks, BG3 Martial Arts die (d4/d6 at 3/d8 at 9) and ki (level + 1), no Sneak Attack on off-hand attacks
- 2026-10-29: Character builder: race, point buy with +2/+1, up to three classes in order (multiclass feat levels and spell slots), subclasses, feats, fighting styles, attack routine (two-handed, duelling, dual wield, ranged, unarmed, cantrip) and toggles for build set ups. A Champion built with it matches the preset exactly. In the planner as "Custom character"
- 2026-10-29: Eight example custom characters (Swashbuckler, Path of Giants, Arcane Archer, Bladesinger, Hexblade, Swarmkeeper, Tavern Brawler Drunken Master, Sorlock) with gear per act; one-handed builds use a Rapier when Dexterity is higher
- 2026-10-29: Planner characters keep everything when sent to the simulator cards: new card fields for BG3 Savage Attacker per die, barbarian level for rage, and the spell save DC bonus from items (tested for every example at every act)
- 2026-10-30: Weapon proficiencies for custom characters from bg3.wiki: first class, multiclass, subclass (Hexblade, War/Tempest/Death clerics, Valour, Bladesinging) and race proficiencies; weapons without proficiency lose the bonus to hit and are flagged in the conflict report
- 2026-10-30: Builder: thrown weapon routine (Tavern Brawler twice, Giant's Rage doubled on throws, Berserker Enraged Throw), levelled damage spells cast with every slot high enough before the cantrip (pact slots too), Toll the Dead added; Throwzerker and Evocation Wizard examples (the wizard matches the Gale preset exactly)
- 2026-10-30: Builder: Battle Master manoeuvres, Arcane Shots, Blade Flourish and Death Domain Touch of Death are limited riders on one attack per round with their own uses (they stack with Smite and Sneak Attack), Potent Spellcasting (Light, Knowledge) and Aura of Hate (Oathbreaker); attack fallbacks survive weapon swaps from gear
- 2026-10-30: Session export/import includes the BG3 planner party, so builds can be saved and shared as one file
- 2026-10-29: Generic +1/+2/+3 trader gear gets an estimated act from its enchantment, items of unknown act are only suggested for Act 3
- 2026-10-30: Party damage chart: expected damage per round of each character across the act checkpoints, under the table
- 2026-10-30: Builder: Circle of Stars (Starry Form: Archer's Luminous Arrow each turn, Star Map Guiding Bolts before the cantrip), Circle of Spores (Symbiotic Entity 1d6 necrotic), Storm Sorcery (Heart of the Storm on lightning and thunder spells, hit or miss); Circle of Stars Druid example; the builder only lists the toggles for its classes
- 2026-10-30: Story choice conflicts: items from different outcomes of the same quest (sparing or killing the Nightsong, Glut or Spaw, Florrick's and Thrinn's one-of rewards) in the conflict report, highlighted, and named in gear suggestions. The Lae'zel example had one (Moonlight Glaive with the Rare Dark Justiciar Gauntlets) and now wears Flawed Helldusk Gloves in Act 2
- 2026-10-30: Distribution plots are binned on the server (bar heights and box statistics only), so every round is plotted instead of a 400,000 value sample; first page load 1.06MB -> 0.59MB, and simulation responses shrink the same way
- 2026-10-30: Lightning Charges (Florrick's Sparky Points, Joltshooter and Spellsparkler, Sparkle Hands): +1 to hit and 1 lightning damage on every attack once the build can gain charges, not stacked across items
- 2026-10-30: Build doc import (bg3.doc_import): all 28 builds of the reference doc as planner examples ("Doc: ..."), every gear name matched; a structured build format for the doc (docs/bg3_build_format.md) that imports exactly
- 2026-10-30: Builder: Shadow Blade routine (2d8/3d8/4d8 psychic from the highest odd slot, off-hand weapon) and Booming Blade (+1d8 thunder from level 5, 2d8 from 11)
- 2026-10-30: Party roles, synergies and fight: roles per member with missing roles and overlaps; Resonance Stone (psychic vulnerability), Darkness (advantage for members who see through it), Reverberation (-2 saves), Hold Person (advantage, melee hits crit); damage alone vs with synergies; a simulated party fight against the enemy's hit points (chance it's down by each round, damage share)
