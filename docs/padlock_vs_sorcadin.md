# Padlock vs Sorcadin vs polearm fighters (Tactician)

Expected damage per round against the act reference enemies (AC 14 / 16 / 18), as **sustained / burst**. These are the planner example
builds of the same names, with no gear, so only the class and weapon choices differ. Generated with the engine (bg3/character.py,
computations/analytic.py).

- **Sustained:** the average round of a 3 round fight. Spell slots for smites are spread over the day (4 fights per long rest, 2 short
  rests, so pact slots come back twice), and a smite is used at most once per turn.
- **Burst:** round 1 with everything: a smite on every weapon hit using the highest slots first, Action Surge, and for the Sorcadin a
  Quickened Fireball (bonus action, single target, DEX save). No party buffs.
- Great Weapon Master is used or not, whichever is higher (it's a toggle in BG3).

| Build | Act 1 (lv 5) | Act 2 (lv 8) | Act 3 (lv 12) | One reaction attack, Act 3 |
|---|---|---|---|---|
| Padlock: Shadow Blade + shield | 25 / 44 | 50 / 62 | 91 / 120 (3 attacks) | 23 |
| Padlock: Greatsword (GWF, GWM) | 30 / 48 | 48 / 57 | 70 / 93 (3 attacks) | 15 |
| Padlock: Glaive (GWF, Polearm Master) | 26 / 44 | 44 / 52 | 73 / 109 (3 attacks) | 13 |
| Sorcadin: Shadow Blade + shield | 28 / 47 | 50 / 69 | 70 / 111 | 23 |
| Sorcadin: Greatsword (GWF, GWM) | 33 / 51 | 40 / 56 | 50 / 85 | 12 |
| Sorcadin: Glaive (GWF, Polearm Master) | 29 / 47 | 36 / 52 | 53 / 82 | 9 |
| Battle Master: Glaive (Polearm Master, GWM, Sentinel) | 24 / 30 | 27 / 34 | 32 / 41 | 11 |
| Fighter 9 / Swashbuckler 3: Glaive (Polearm Master, GWM) | 24 / 30 | 20 / 26 | 23 / 30 | 6 |
| Padlock: Shadow Blade + shield (Honour Mode) | 25 / 44 | 50 / 62 | 68 / 83 | 23 |

## Takeaways

- **Pact of the Blade's Extra Attack stacks with the Paladin's outside Honour Mode** (bg3.wiki, Deepened Pact). That third attack at
  Warlock 5 + Paladin 5 is the Padlock's whole edge. In Honour Mode the same build drops from 91 to 68 sustained in Act 3.
- **Act 3: the Padlock beats the Sorcadin on both sustained (91 vs 70) and burst (120 vs 111)** with Shadow Blade and a shield. The Sorcadin's
  bigger slots (5d8 smites, a 4d8 Shadow Blade, a Quickened Fireball) only close the burst gap. Without Vow of Enmity's advantage, the
  Padlock still leads sustained (68 vs 52) and the Sorcadin edges burst (85 vs 83). The Sorcadin also has more slots for long days and
  Fireball for groups, which a single target number doesn't show.
- **Shadow Blade + shield is the best weapon for both** (the d8s of Shadow Blade, Duelling's +2, and smites land more often without
  GWM's -5), plus +2 AC. Greatsword and Glaive come out close to each other. The Glaive's butt-end bonus attack adds a 4th smite to the burst.
- **Acts 1 and 2:** before Warlock 5 the Padlock is a Paladin with 2 attacks. In Act 1 both builds are still pure Paladin 5 and only
  differ by ability scores, and the two-handers lead there.
- **Polearm Master and Sentinel:** each reaction attack is worth about one plain attack (column on the right). Polearm Master's reach
  attack fires roughly once per fight when an enemy closes in. Sentinel fires when an enemy next to you attacks an *ally* (not you), at
  most once per round. That is worth a few points per round, not enough to close the gap to a Paladin. The no-gear fighters trail
  mostly because they have no Vow (advantage), no smites, and GWM's -5 against AC 18.
- The Fighter / Swashbuckler glaive build gets nothing from its Rogue levels in damage: Sneak Attack needs a finesse or ranged weapon.
  Its value is Dirty Tricks and utility.

## Assumptions and limits

- Shadow Blade bound as the pact weapon: the Hexblade's Bind Hexed Weapon works on summoned weapons according to the doc builds that use
  it, but bg3.wiki doesn't confirm it for Shadow Blade. Check in game that Bind works after casting it. If it doesn't, the Shadow Blade Padlock
  has 2 attacks with Strength.
- Vengeance Paladins have Vow of Enmity (advantage) all fight, and Padlocks have Hexblade's Curse on the target.
- Booming Blade is off for every build. Reactions aren't in the table totals. No gear, so items that add damage per hit (Act 2-3
  +weapons, Helldusk, rings) widen the gap for the builds with more attacks.
