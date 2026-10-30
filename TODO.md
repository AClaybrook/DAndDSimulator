# BG3 Planner: To Do and Done Notes

Working notes for the Baldur's Gate 3 direction. The CHANGELOG has the user facing summary of each release.

## Active
- [ ] Open a PR with the BG3 planner work once you have looked at it

## Next
- [ ] Builder: more subclass features: Wildheart aspects (bleeding/poisoned targets), Beast Master and summons (need a companion model), Eldritch Knight War Magic and Shadow Strike (both trade Extra Attack for less damage, so low priority), Druid with a Scimitar or Shillelagh instead of a Longsword
- [ ] Builder: Smites as spells (Searing, Branding, Wrathful), Wild Shape, Enraged Throw's Strength based damage
- [ ] Elixir of Bloodlust (extra action on a kill) and kill based effects in general
- [ ] Arcane Acuity, Lightning Charges, Momentum and other stacking effects
- [ ] More story choices in bg3/data/story_choices.json (Act 3 companion endings, Grove raid), each checked against its bg3.wiki quest page
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
- 2026-10-30: Weapon proficiencies for custom characters from bg3.wiki: first class, multiclass, subclass (Hexblade, War/Tempest/Death clerics, Valour, Bladesinging) and race proficiencies; weapons without proficiency lose the bonus to hit and are flagged in the conflict report
- 2026-10-30: Builder: thrown weapon routine (Tavern Brawler twice, Giant's Rage doubled on throws, Berserker Enraged Throw), levelled damage spells cast with every slot high enough before the cantrip (pact slots too), Toll the Dead added; Throwzerker and Evocation Wizard examples (the wizard matches the Gale preset exactly)
- 2026-10-30: Builder: Battle Master manoeuvres, Arcane Shots, Blade Flourish and Death Domain Touch of Death are limited riders on one attack per round with their own uses (they stack with Smite and Sneak Attack), Potent Spellcasting (Light, Knowledge) and Aura of Hate (Oathbreaker); attack fallbacks survive weapon swaps from gear
- 2026-10-30: Session export/import includes the BG3 planner party, so builds can be saved and shared as one file
- 2026-10-29: Generic +1/+2/+3 trader gear gets an estimated act from its enchantment, items of unknown act are only suggested for Act 3
- 2026-10-30: Party damage chart: expected damage per round of each character across the act checkpoints, under the table
- 2026-10-30: Builder: Circle of Stars (Starry Form: Archer's Luminous Arrow each turn, Star Map Guiding Bolts before the cantrip), Circle of Spores (Symbiotic Entity 1d6 necrotic), Storm Sorcery (Heart of the Storm on lightning and thunder spells, hit or miss); Circle of Stars Druid example; the builder only lists the toggles for its classes
- 2026-10-30: Story choice conflicts: items from different outcomes of the same quest (sparing or killing the Nightsong, Glut or Spaw, Florrick's and Thrinn's one-of rewards) in the conflict report, highlighted, and named in gear suggestions. The Lae'zel example had one (Moonlight Glaive with the Rare Dark Justiciar Gauntlets) and now wears Flawed Helldusk Gloves in Act 2
