# BG3 Planner: To Do and Done Notes

Working notes for the Baldur's Gate 3 direction. The CHANGELOG has the user facing summary of each release.

## Active
- [ ] Open a PR with the BG3 planner work once you have looked at it

## Next
- [ ] Builder: more subclass features (Eldritch Knight, Wildheart aspects, Circle of Stars, Death Domain Touch of Death, College of Glamour, Shadow Magic...), Battle Master and Arcane Archer as separate dice pools
- [ ] Builder: leveled damage spells (Fireball, Scorching Ray, Smites as spells), thrown weapon builds (Throwzerker), Wild Shape
- [ ] Builder: weapon proficiencies by race and class (non-proficient weapons lose the proficiency bonus)
- [ ] Elixir of Bloodlust (extra action on a kill) and kill based effects in general
- [ ] Arcane Acuity, Lightning Charges, Momentum and other stacking effects
- [ ] Story exclusive items (one path or the other) in the conflict report
- [ ] Finish the hand review of parsed Act 3 item effects (first pass done: crit-only damage, Sneak Attack bonuses, Tenacity, creature type conditions)
- [ ] Smaller first load: the example DPR histogram is about 0.4MB of the 1MB page
- [ ] Illithid powers

## Done
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
- 2026-10-29: Generic +1/+2/+3 trader gear gets an estimated act from its enchantment, items of unknown act are only suggested for Act 3
