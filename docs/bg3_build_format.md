# Build format for the BG3 build reference doc

The planner imports builds from the doc with `python -m bg3.doc_import <doc link>` (read only, the doc is never changed).
Free text builds ("Build N: ...") are read best effort. Builds written like the block below are read exactly, so nothing is guessed.
Everything after the colon on each line is free to edit; the field names at the start of each line are what the importer looks for.
Fields can be left out; the ones marked * are the ones the planner needs most.

```
Build 29: Godblade
Source: Nizar GG - https://youtube.com/watch?v=...
Updated: 2026-10-30
Difficulty: Honour
Companion: Tav, Gale
Roles: frontline, control, support
Themes: psychic, shadow blade, arcane acuity
Path: either
* Race: Wood Half-Elf
* Classes: 10 Bladesinging Wizard / 2 Oath of the Crown Paladin
Level order: Wizard 1-10, Paladin 11-12
* Abilities: STR 8, DEX 15, CON 14, INT 15, WIS 10, CHA 8 | +2 DEX, +1 INT
* Feats: +2 DEX, Savage Attacker, +2 INT
Fighting styles: Defence
* Routine: shadow_blade
Cantrip: Booming Blade
Spell:
Permanent buffs: Act 1 Auntie Ethel's Hair DEX; Act 3 Mirror of Loss INT
* Act 1 Gear: Off Hand = Knife of the Undermountain King; Helmet = Diadem of Arcane Synergy; Armour = Bloodguzzler Garb; Gloves = Bracers of Defence; Boots = Disintegrating Night Walkers; Amulet = Periapt of Wound Closure; Ring 1 = Caustic Band; Ring 2 = Crusher's Ring; Ranged = Bow of Awareness
* Act 2 Gear: Cloak = Cloak of Protection; Gloves = Gloves of the Battlemage's Power; Ring 2 = Strange Conduit Ring; Carried = Resonance Stone
* Act 3 Gear: Off Hand = Rhapsody; Armour = Robe of the Weave; Amulet = Amulet of Greater Health; Ring 1 = Band of the Mystic Scoundrel; Ranged = Hellrider Longbow
Alternatives: Gloves = Gloves of Dexterity; Ring 1 = Ring of Protection
Act 1 Buffs: Bless, Elixir of Hill Giant Strength
Act 2 Buffs: Haste
Act 1 Loop: Pre-combat Shadow Blade; Action Booming Blade + attack; Bonus action off-hand Knife; Concentration Shadow Blade
Provides: psychic vulnerability (Resonance Stone), bless
Needs: darkness sight
Notes: anything else
```

## Field reference

| Field | What it's for | Values |
|---|---|---|
| Classes | class split at level 12, in the order taken | `10 Bladesinging Wizard / 2 Oath of the Crown Paladin` (subclass then class) |
| Level order | only when the order isn't "first class first" | `Paladin 1, Warlock 1, Paladin 2-5, Sorcerer 6-12` |
| Abilities | point buy scores **before** the +2/+1, then the +2/+1 after a `|` | 27 points, 8 to 15 |
| Feats | the choice at each feat level, in order | a feat name, `+2 DEX`, or `+1 DEX +1 CON` |
| Routine | how it attacks each turn | `two_handed`, `one_handed`, `dual_wield`, `ranged`, `unarmed`, `thrown`, `cantrip`, `shadow_blade` |
| Cantrip / Spell | for `cantrip` builds: the cantrip, and a levelled damage spell cast first | i.e. `Eldritch Blast`, `Scorching Ray` |
| Act N Gear | what is **added or changed** at that act; earlier gear carries over | `Slot = Item; ...` slots: Main Hand, Off Hand, Ranged, Ranged Off, Helmet, Cloak, Armour, Gloves, Boots, Amulet, Ring 1, Ring 2, Carried |
| Act N Buffs | buffs and elixirs that act | Bless, Haste, Hex, Divine Favour, any Elixir name |
| Roles | what it does for the party | frontline, striker, ranged, control, healer, support, face, skills, summoner |
| Themes | party synergies it creates or uses | psychic, darkness, radiant orb, reverberation, bleeding, thunder, fire, necrotic, arcane acuity |
| Provides / Needs | conditions it gives the party or depends on | psychic vulnerability, darkness, darkness sight, bless, haste, reverberation, radiating orb, bleeding, paralysed |
| Path | story choices it needs | good, evil, either, or the choice (`kills the Nightsong`) |

## Why these fields

- **Act checkpoints:** the planner compares builds at the end of Acts 1, 2 and 3 (levels 5, 8 and 12). Gear and buffs per act give the damage at each, and conflicts per act.
- **Exact slots:** free text lists can't tell which ring slot or hand an item goes in, or whether "A / B" means either or both.
- **Abilities before the +2/+1:** the guide's scores already include them (and sometimes Hag's Hair), so the importer has to guess the split.
- **Roles, Themes, Provides / Needs:** the party planner uses these to show overlapping roles and which members feed each other (a Resonance Stone carrier and psychic damage dealers).
