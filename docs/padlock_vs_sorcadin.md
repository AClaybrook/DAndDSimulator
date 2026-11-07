# Padlock vs Sorcadin vs polearm fighters (Tactician)

Expected damage per round against the act reference enemies (AC 14 / 16 / 18), as **sustained / burst**. These are the planner example
builds of the same names, with no gear, so only the class and weapon choices differ. Generated with the engine (bg3/character.py,
computations/analytic.py).

- **Sustained:** the average round of a 3 round fight. Spell slots for smites are spread over the day (4 fights per long rest, 2 short
  rests, so pact slots come back twice), and a smite is used at most once per turn.
- **Burst:** round 1 with everything: a smite on every weapon hit using the highest slots first, Action Surge, and for the Sorcadin a
  Quickened Fireball (bonus action, single target, DEX save; +CHA for a red Draconic Sorcerer). No party buffs. Builds without
  limited resources (a pure Warlock) have the same number for both.
- Great Weapon Master is used or not, whichever is higher (it's a toggle in BG3).

| Build | Act 1 (lv 5) | Act 2 (lv 8) | Act 3 (lv 12) | One reaction attack, Act 3 |
|---|---|---|---|---|
| Padlock: Shadow Blade + shield | 31 / 31 | 59 / 80 | 91 / 120 | 23 |
| Padlock: Greatsword (GWF, GWM) | 21 / 21 | 48 / 66 | 70 / 93 | 15 |
| Padlock: Glaive (GWF, Polearm Master) | 19 / 19 | 44 / 62 | 73 / 109 | 13 |
| Sorcadin: Shadow Blade + shield | 28 / 47 | 50 / 69 | 70 / 114 | 23 |
| Sorcadin: Greatsword (GWF, GWM) | 33 / 51 | 40 / 56 | 50 / 87 | 12 |
| Sorcadin: Glaive (GWF, Polearm Master) | 29 / 47 | 36 / 52 | 53 / 84 | 9 |
| Battle Master: Glaive (Polearm Master, GWM, Sentinel) | 24 / 30 | 27 / 34 | 32 / 41 | 11 |
| Fighter 9 / Swashbuckler 3: Glaive (Polearm Master, GWM) | 24 / 30 | 20 / 26 | 23 / 30 | 6 |
| Padlock: Shadow Blade + shield (Honour Mode) | 31 / 31 | 59 / 80 | 68 / 83 | 23 |

## Takeaways

- **Pact of the Blade's Extra Attack stacks with the Paladin's outside Honour Mode** (bg3.wiki, Deepened Pact). That third attack at
  Warlock 5 + Paladin 5 is the Padlock's whole edge. In Honour Mode the same build drops from 91 to 68 sustained in Act 3.
- **Act 3: the Padlock beats the Sorcadin on both sustained (91 vs 70) and burst (120 vs 114)** with Shadow Blade and a shield. The Sorcadin's
  bigger slots (5d8 smites, a 4d8 Shadow Blade, a Quickened Fireball) only close the burst gap. Without Vow of Enmity's advantage, the
  Padlock still leads sustained (68 vs 52). The Sorcadin also has more slots for long days and Fireball for groups, which a single target
  number doesn't show.
- **Shadow Blade + shield is the best weapon for both** (the d8s of Shadow Blade, Duelling's +2, and smites land more often without
  GWM's -5), plus +2 AC. Greatsword and Glaive come out close to each other. The Glaive's butt-end bonus attack adds a 4th smite to the burst.
- **Polearm Master and Sentinel:** each reaction attack is worth about one plain attack (column on the right). Polearm Master's reach
  attack fires roughly once per fight when an enemy closes in. Sentinel fires when an enemy next to you attacks an *ally* (not you), at
  most once per round. That is worth a few points per round, not enough to close the gap to a Paladin. The no-gear fighters trail
  mostly because they have no Vow (advantage), no smites, and GWM's -5 against AC 18.

## Polearm builds: why the plain Glaive is low, and the Halberd of Vigilance

![Sustained damage by act, and Act 3 sustained vs burst with reaction attacks](build_comparison.png)

| Act 3, sustained / burst | Own turn | Reactions | Total |
|---|---|---|---|
| Padlock, Halberd of Vigilance (Polearm Master) | 95 | +6 | 101 / 169 |
| Battle Master, Halberd, Polearm Master + GWM + Sentinel, with advantage | 82 | +14 | 96 / 140 |
| Battle Master, Halberd, Polearm Master + GWM + Sentinel | 51 | +14 | 65 / 100 |
| Battle Master, Halberd, GWM + Savage Attacker (no reaction feats) | 53 | 0 | 53 / 72 |
| Fighter 8 / Swashbuckler 4, The Dancing Breeze (Dexterity) | 47 | +4 | 51 / 60 |
| Battle Master, plain Glaive, no gear | 31 | +7 | 38 / 59 |

- **The plain Glaive with no gear** hits AC 18 55% of the time for 1d10 + 4: no magic weapon, no smites, no advantage, and GWM's -5 isn't
  worth it there. It is a no gear baseline, not how the build is played.
- **The Halberd of Vigilance** (Act 2) roughly doubles it: +2 to hit and damage, 1d4 force on every hit, and every reaction attack with
  advantage. With Polearm Master (an enemy entering your reach, about once a fight) and Sentinel (an enemy next to you attacking an
  ally, about every other round) the reactions add about 14 a round in Act 3, so the reaction feats beat Savage Attacker and Strength
  (65 vs 53). With advantage (Trip Attack's prone, Faerie Fire, Reckless allies) it reaches 96, level with the Padlock.
- **On a Padlock** the Halberd is the strongest polearm: a bound pact weapon with 3 attacks, the butt end and smites on all four hits.
- **Dexterity glaive:** only works from Act 3 (The Dancing Breeze is the one finesse polearm), and the Swashbuckler's Sneak Attack and
  Flick o' the Wrist come back with it. Before Act 3 a Dexterity build would use another weapon.
- Reaction attacks are an estimate (the `reactions` toggle on every build); real fights give more when enemies run past you.

## Lockadin, Sorcadin and pure Hexblade variants

| Build (Shadow Blade + shield unless noted) | Act 1 | Act 2 | Act 3 | Act 3 without advantage |
|---|---|---|---|---|
| Lockadin Hexblade 5 first, then Paladin 7 | 31 / 31 | 59 / 80 | 91 / 120 | 68 |
| Lockadin Paladin 5 first, then Hexblade 5, Paladin 7 (or Paladin 6 / Hexblade 6) | 25 / 44 | 50 / 62 | 91 / 120 | 68 |
| Hex-Sorcadin Paladin 6 / Hexblade 1 / Sorcerer 5 | 19 / 23 | 47 / 62 | 73 / 118 | 54 |
| Sorcadin 6 / 6 Draconic (red) | 28 / 47 | 50 / 69 | 70 / 114 | 52 |
| Sorcadin 6 / 6 Shadow Magic (Storm and Wild Magic are the same here) | 28 / 47 | 50 / 69 | 70 / 111 | 52 |
| Vengeance Paladin 11 / Hexblade 1 (Longsword + shield) | 19 / 23 | 38 / 52 | 59 / 74 | 43 |
| Hex-Crown Paladin 11 / Hexblade 1 (Longsword + shield) | 17 / 21 | 33 / 44 | 53 / 66 | 43 |
| Pure Hexblade 12, Shadow Blade + dagger, advantage from darkness | 48 | 48 | 82 | 57 |
| Pure Hexblade 12, Shadow Blade + shield, advantage from darkness | 42 | 43 | 71 | 49 |

- **Lockadin order:** Hexblade 5 first is clearly better in Acts 1 and 2 (Shadow Blade, Extra Attack and Charisma attacks from level 5,
  then Vow and smites at Paladin 3). It's the same in Act 3. The cost is armour: multiclassing *into* Paladin only gives light and medium
  armour and shields (bg3.wiki), so heavy armour needs Paladin as the first class (or a feat). Paladin 6 / Hexblade 6 deals the same
  damage as 7 / 5 (Paladin 6 is the one that matters: Aura of Protection).
- **Lockadin vs pure Hexblade:** the Lockadin wins in Act 2 and 3 (91 vs about 71 to 82 sustained, and 120 burst vs no burst at all). The
  pure Hexblade is ahead in Act 1, has a third feat, Lifedrinker (+CHA necrotic per hit at Warlock 12), more pact slots (3 at level 5 by
  Act 3) and Warlock utility (Devil's Sight and Darkness for advantage, Eldritch Blast, a level 6 Mystic Arcanum). The Paladin side adds a
  third attack, smites, Vow of Enmity, Aura of Protection (+CHA to every save for you and allies nearby) and Lay on Hands, which makes it
  both stronger and tankier.
- **Sorcerer subclass for a Sorcadin:** barely matters for damage. Draconic (red) adds CHA to fire spells (the Quickened Fireball) and
  +1 HP per Sorcerer level. Shadow Magic gives Darkness from sorcery points (Shadow Blade advantage, useful with an oath that has no Vow)
  and the Hound of Ill Omen, which costs the same 3 sorcery points and bonus action as a Quickened spell. Storm gives flight after
  spells. A **Hexblade 1 dip** (Hex-Sorcadin) attacks with Charisma and adds Hexblade's Curse, closing most of the burst gap to the
  Lockadin (118 vs 120) at the cost of a weak Act 1.
- **Hex-Crown / Paladin 11 + Hexblade 1:** Improved Divine Smite (+1d8 radiant every hit) doesn't make up for having 2 attacks and no
  Shadow Blade (Hexblade 1 can't learn it).
- **Swashbuckler with a glaive:** Rakish Sneak Attack and Flick o' the Wrist both need a finesse weapon. The only finesse polearm is
  The Dancing Breeze (a glaive, Act 3). Before that the Rogue levels add no damage, and Strength potions don't change that.

## Assumptions and limits

- Shadow Blade bound as the pact weapon (it doesn't need concentration and lasts until a long rest, so Bind Pact / Hexed Weapon works on it).
- Vengeance Paladins have Vow of Enmity (advantage) all fight, and Hexblades have Hexblade's Curse on the target. Hex isn't counted
  (+1d6 per hit for any build with a Warlock level that concentrates on it).
- Booming Blade is off for every build. Reactions aren't in the table totals. No gear, so items that add damage per hit (Act 2-3
  +weapons, Helldusk, rings) widen the gap for the builds with more attacks.
