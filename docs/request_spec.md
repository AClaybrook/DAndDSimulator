BUILD DOC FORMAT SPEC (for the AI that maintains this doc)

Purpose: a planner tool reads this doc as plain text and imports each build. It reads each build's field lines exactly. It ignores other lines, so prose is safe anywhere outside a field line.

GENERAL RULES
1. Start each build with its own line: `Build N: Title`. N is a unique number that never changes once given. Don't renumber old builds; give new builds the next number.
2. Put each field on its own line, starting with the field name, a colon and a space. Spell field names exactly as below.
3. Put no bullets, numbering, emoji or extra text before a field name. Bold or headings on the line are fine.
4. Keep one field per line, and keep each value on that one line.
5. Spell item, spell, feat, race and subclass names exactly as bg3.wiki does (Patch 8).
6. If information isn't available, leave the field line out, or write `unknown`. Never guess or invent values. Put anything uncertain in `Caveats:`.
7. If the source gives information in a shape these fields can't hold, keep it as prose in `Notes:` lines. Several `Notes:` lines are allowed, and so is free text below the fields.
8. Levels and checkpoints: Act 1 ends at level 5, Act 2 at level 8, Act 3 at level 12.

FIELDS (in this order; the ones marked REQUIRED matter most)
`Build N: Title`
`Source:` creator, plus a video or page URL if known
`Updated:` YYYY-MM-DD
`Difficulty:` Honour, Tactician, Balanced, or unknown
`Companion:` suggested characters, comma separated
`Race:` exact race/subrace, e.g. Wood Half-Elf (REQUIRED)
`Classes:` final level 12 split as "levels subclass class", joined with " / ", in the order the classes are first taken. Example: `Classes: 10 Bladesinging Wizard / 2 Oath of the Crown Paladin` (REQUIRED)
`Level order:` only if the order differs from "first class first". Example: `Level order: Paladin 1, Warlock 1, Paladin 2-5, Sorcerer 6-12`
`Respec:` only if the build changes split between acts. Example: `Respec: Act 1 = 5 Paladin; Act 3 = 10 Wizard / 2 Paladin`
`Abilities:` the 27-point-buy scores BEFORE the racial +2/+1, then `|`, then the +2/+1. Example: `Abilities: STR 8, DEX 15, CON 14, INT 15, WIS 10, CHA 8 | +2 DEX, +1 INT`. Leave out Hag's Hair, elixirs and Mirror of Loss here; those go under Permanent buffs. If only final scores are known, write `Final abilities: STR 8, DEX 17, ...` instead (REQUIRED)
`Feats:` the choice at each feat level, in order, comma separated. Each is a feat name, `+2 DEX`, or `+1 DEX +1 CON` (REQUIRED)
`Fighting styles:` comma separated, in the order gained
`Routine:` exactly one of `two_handed`, `one_handed`, `dual_wield`, `ranged`, `unarmed`, `thrown`, `cantrip`, `shadow_blade`. This is how the build mainly attacks each turn (REQUIRED)
`Cantrip:` the main attack cantrip, if any (e.g. Eldritch Blast, Booming Blade)
`Spell:` the main levelled damage spell cast with slots, if any (e.g. Scorching Ray)
`Permanent buffs:` act and buff, separated by `;`. Example: `Permanent buffs: Act 1 Auntie Ethel's Hair DEX; Act 3 Mirror of Loss INT`
`Act 1 Gear:` `Slot = Item` pairs separated by `;` (REQUIRED for each act)
`Act 2 Gear:` list ONLY what is added or changed since the act before; earlier gear carries over
`Act 3 Gear:` same as Act 2
- Slot names: Main Hand, Off Hand, Ranged, Ranged Off, Helmet, Cloak, Armour, Gloves, Boots, Amulet, Ring 1, Ring 2, Carried
- Carried is for non-equipped items that matter, e.g. Resonance Stone.
- Spells like Shadow Blade are NOT gear: leave them out of gear lines and use Routine: shadow_blade instead.
- If the source gives only one item list, put each item in the act where it is first found. Write `Gear acts: estimated` on its own line.
- Example: `Act 2 Gear: Gloves = Gloves of the Battlemage's Power; Ring 2 = Strange Conduit Ring; Carried = Resonance Stone`
`Alternatives:` `Slot = Item` pairs for no-overlap substitutes, separated by `;`
`Act 1 Buffs:` buffs and elixirs used in fights that act, comma separated (Bless, Haste, Hex, Divine Favour, or exact elixir names). `Act 2 Buffs:` and `Act 3 Buffs:` work the same way
`Act 1 Loop:` the turn plan, as `Pre-combat ...; Action ...; Bonus action ...; Reaction ...; Concentration ...`. `Act 2 Loop:` and `Act 3 Loop:` work the same way
`Roles:` comma separated, from: frontline, striker, ranged, control, healer, support, face, skills, summoner
`Themes:` comma separated, from: psychic, darkness, radiant orb, reverberation, bleeding, thunder, lightning, fire, cold, necrotic, poison, arcane acuity, arcane synergy, summons, crit, throw. New words are allowed if none fit
`Provides:` conditions this build gives the party or enemy, comma separated, e.g. psychic vulnerability, darkness, bless, haste, reverberation, radiating orb, bleeding, paralysed, prone, frightened
`Needs:` what it depends on from others, comma separated, e.g. darkness sight, resonance stone carrier, haste, bless
`Path:` good, evil, either, or the specific choice, e.g. `Shadowheart kills the Nightsong`
`Caveats:` patch or difficulty limits, bugs relied on, unverified claims
`Notes:` free prose; repeatable

EXAMPLE
Build 29: Godblade
Source: Nizar GG - https://youtube.com/watch?v=...
Updated: 2026-10-30
Difficulty: Honour
Companion: Tav, Gale
Race: Wood Half-Elf
Classes: 10 Bladesinging Wizard / 2 Oath of the Crown Paladin
Abilities: STR 8, DEX 15, CON 14, INT 15, WIS 10, CHA 8 | +2 DEX, +1 INT
Feats: +2 DEX, Savage Attacker, +2 INT
Fighting styles: Defence
Routine: shadow_blade
Cantrip: Booming Blade
Permanent buffs: Act 1 Auntie Ethel's Hair DEX
Act 1 Gear: Off Hand = Knife of the Undermountain King; Helmet = Diadem of Arcane Synergy; Armour = Bloodguzzler Garb; Gloves = Bracers of Defence; Boots = Disintegrating Night Walkers; Amulet = Periapt of Wound Closure; Ring 1 = Caustic Band; Ring 2 = Crusher's Ring; Ranged = Bow of Awareness
Act 2 Gear: Cloak = Cloak of Protection; Gloves = Gloves of the Battlemage's Power; Ring 2 = Strange Conduit Ring; Carried = Resonance Stone
Act 3 Gear: Off Hand = Rhapsody; Armour = Robe of the Weave; Amulet = Amulet of Greater Health; Ring 1 = Band of the Mystic Scoundrel; Ranged = Hellrider Longbow
Alternatives: Gloves = Gloves of Dexterity
Act 2 Buffs: Haste
Act 2 Loop: Pre-combat Shadow Blade (level 3 slot); Action Booming Blade + attack; Bonus action off-hand attack; Concentration Shadow Blade
Roles: frontline, control, support
Themes: psychic, arcane acuity
Provides: psychic vulnerability
Needs: resonance stone carrier
Path: either
Caveats: Pact of the Blade + Extra Attack stacking differs on Honour Mode
Notes: Respec at 12 to put the Paladin level first.

PARTIES (optional, after all builds)
Start each party with a line: `Party N: Title`
`Members:` Build numbers with companions, separated by `;`. Example: `Members: Build 1 = Gale; Build 3 = Wyll; Build 5 = Astarion; Build 4 = Shadowheart`
`Act:` the act the party is planned for, or all
`Resolved overlaps:` `Item -> who gets it, what others use instead`, separated by `;`
`Notes:` free prose

EXISTING CONTENT
Leave existing prose sections as they are; they are ignored safely. When updating an older build, add the field lines above at the top of its section and keep the old prose below them.
