# Overall score

A 0 to 100 score per character and act (`bg3/score.py`), shown in the planner's "Overall score" table and in the variants table. It rewards well rounded builds: a high AC Godblade can outscore a pure damage version of itself.

## How it's worked out

Six parts, each 0 to 100, then a weighted average.

| Part | What it measures | 100 means | Weight |
|---|---|---|---|
| Damage | Expected single target damage per round (the same number as the damage table) | 1.5 x a strong build for that act (40 / 60 / 95 at levels 5 / 8 / 12) | 35 |
| AoE | Extra damage against 3 enemies (area spells, auras, Horde Breaker) | 1.5 x a strong area build (15 / 30 / 50) | 10 |
| Defence | Effective HP: hit points / chance the enemy hits (AC against its attack bonus, default +6) | 1.5 x a sturdy front liner (110 / 170 / 250 effective HP) | 25 |
| Control | Points for control tools: caster levels (Hold Person, Command, Web), Stunning Strike, manoeuvres, Dirty Tricks, Reverberation and Prone, items that frighten, silence or debuff | capped at 100 | 10 |
| Support | Points for healing and buffs: Cleric/Druid healing, Bardic Inspiration, Aura of Protection, Haste casters, Phalar Aluve's Sing, healing items | capped at 100 | 10 |
| Utility | Points for party face (CHA 16+), locks and traps (Rogue, Bard), rituals and scrolls, darkness sight, mobility and utility items | capped at 100 | 10 |

The references are fixed per act, so a score means the same in any party: a build scoring 50 is roughly "a strong build's damage and toughness for that act with some extras". Hover a cell for each part and where it came from.

Hit points follow BG3: the first class's full hit die at level 1, then half the die + 1 per level, plus the CON modifier each level, +2 per level with Tough.

## Limits of this first version

- **Weights are a choice.** 35 / 10 / 25 / 10 / 10 / 10 favours damage and toughness. A support player would weight support higher; `score(..., weights={...})` takes any weights.
- **Control, support and utility are points for having a tool, not its effect.** A Hold Person caster gets the same control points whether the enemy saves or not.
- **Defence ignores resistances, saves, healing taken and damage reduction** (Warding Bond's resistance, Adamantine armour, Heavy Armour Master).
- **The AoE part needs a group.** Against a single boss it overstates casters; against swarms it understates them.
- **References come from the planner's own example builds**, so they move if the models improve.

## Ways to improve it

1. **Effect-based control.** Value control as enemy damage prevented: enemy damage per round x chance it fails the save x turns lost (Hold Person, Command, Hypnotic Pattern, Prone, Stunning Strike).
2. **Effect-based support.** Count damage added to the party (Bless, Haste, Sing) and damage prevented (Aid and Heroes' Feast HP, Warding Bond, healing per round), using the planner's party model.
3. **A party score.** Score the four together: one healer and one control caster are worth more than four of either, so roles with diminishing returns per role.
4. **Role presets for the weights**, for example front liner, striker, controller or support, picked per character, so each build is judged on its job.
5. **Calibrate against real fights.** Use the party fight simulation (a two sided fight once enemy damage exists): rounds to win and damage taken against a set of Act 1–3 encounters, then fit the weights to that.
6. **Saves and resistances in defence:** proficient saves, Aura of Protection, resistances, and damage reduction per hit.
