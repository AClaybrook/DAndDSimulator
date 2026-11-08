# Padlock vs Sorcadin vs polearm builds (Tactician)

Expected damage per round against the act reference enemies (AC 14 / 16 / 18), as **sustained / burst**. These are the planner example
builds of the same names. Only the polearm builds get gear (their weapon), so the class and weapon choices are what differ. Generated with
the engine (bg3/character.py, computations/analytic.py).

![Sustained damage by act, and Act 3 sustained vs burst with reaction attacks](build_comparison.png)

## How the numbers are counted

- **Sustained:** the average round of a 3 round fight with the day's resources spread over 4 fights (2 short rests). A smite is used at
  most once per turn, and its size is the **average of the day's slots** (2d8 from a level 1 slot, +1d8 a level, at most 5d8): the
  Padlock's pact slots come back on short rests, the Sorcadin's sorcery points become one more slot (Flexible Casting), and the slot
  Shadow Blade was cast with is gone. In Act 3 that is 3.25 smites a fight averaging 3.2d8 for the Padlock, 3.5 averaging 3.4d8 for
  the Sorcadin.
- **Burst:** round 1 with everything: a smite on **every** weapon hit (reactions included) with the best slots first, Action Surge, and
  for the Sorcadin a Quickened Fireball as the bonus action (single target, DEX save, +CHA for a red Draconic Sorcerer). No party buffs.
- **Shadow Blade** is cast with the best slot: 3d8 for the Padlock (a level 3 pact slot), 4d8 for the Sorcadin (a level 5 slot). It lasts
  until a long rest and needs no concentration. Its own advantage (dim light or darkness) isn't counted separately, because every
  Vengeance Paladin here already attacks with advantage from Vow of Enmity.
- **Feats by Act 3:** Padlock and Sorcadin get 2 (Shadow Blade builds: +3 to their attack ability, Halberd builds: +2 and Polearm Master),
  the Battle Master 4 (Polearm Master, GWM, +2 Strength, Sentinel). Great Weapon Master is used or not, whichever is higher.
- **Why the Padlock hits harder than the Sorcadin:** per hit 3d8 + 11 (Charisma 5 from the pact weapon, Duelling 2, Hexblade's Curse 4)
  with crits on 19-20, three times a turn, against the Sorcadin's 4d8 + 7, twice a turn. The Sorcadin's bigger slots only show in burst.

| Build | Act 1 (lv 5) | Act 2 (lv 8) | Act 3 (lv 12) | One reaction attack, Act 3 |
|---|---|---|---|---|
| Padlock: Shadow Blade + shield | 31 / 31 | 57 / 80 | 87 / 120 | 23 |
| Padlock: Greatsword (GWF, GWM) | 21 / 21 | 45 / 66 | 65 / 93 | 15 |
| Padlock: Glaive (GWF, Polearm Master) | 19 / 19 | 41 / 62 | 72 / 135 | 13 |
| Sorcadin: Shadow Blade + shield | 26 / 43 | 44 / 65 | 62 / 114 | 23 |
| Sorcadin: Greatsword (GWF, GWM) | 31 / 51 | 34 / 56 | 41 / 87 | 12 |
| Sorcadin: Glaive (GWF, Polearm Master) | 27 / 47 | 31 / 52 | 47 / 113 | 9 |
| Battle Master: Glaive (Polearm Master, GWM, Sentinel) | 26 / 36 | 29 / 42 | 38 / 58 | 11 |
| Battle Master: Halberd of Vigilance (Polearm Master, GWM, Sentinel) | 26 / 36 | 48 / 71 | 64 / 100 | 17 |
| Battle Master: Halberd of Vigilance (GWM, Savage Attacker, no reaction feats) | 22 / 30 | 34 / 46 | 53 / 72 | 13 |
| Padlock: Halberd of Vigilance (GWF, Polearm Master) | 19 / 19 | 52 / 75 | 95 / 169 | 18 |
| Sorcadin: Halberd of Vigilance (GWF, Polearm Master) | 27 / 47 | 41 / 65 | 63 / 133 | 14 |
| Fighter 8 / Swashbuckler 4: The Dancing Breeze (Dexterity, Polearm Master) | 9 / 12 | 8 / 10 | 50 / 60 | 11 |
| Fighter 9 / Swashbuckler 3: Glaive (Polearm Master, GWM) | 26 / 36 | 22 / 31 | 25 / 36 | 6 |
| Padlock: Shadow Blade + shield (Honour Mode) | 31 / 31 | 57 / 80 | 63 / 83 | 23 |

## Takeaways

- **Pact of the Blade's Extra Attack stacks with the Paladin's outside Honour Mode** (bg3.wiki, Deepened Pact). That third attack at
  Warlock 5 + Paladin 5 is the Padlock's edge: in Honour Mode the same build drops from 87 to 63 sustained in Act 3.
- **Act 3: the Padlock beats the Sorcadin on sustained (87 vs 62) and burst (120 vs 114)** with Shadow Blade and a shield. Without Vow of
  Enmity's advantage the Padlock still leads sustained (64 vs 46), and the Sorcadin edges burst (87 vs 83). The Sorcadin also has
  Fireball for groups, which a single target number doesn't show.
- **Shadow Blade + shield is the best non-gear weapon for both** (Shadow Blade's d8s, Duelling's +2, and smites land more often without
  GWM's -5), plus +2 AC. With the Halberd of Vigilance the polearm builds pass it.

## Polearm builds and the Halberd of Vigilance

| Act 3 | Own turn | Reactions | Sustained / burst |
|---|---|---|---|
| Battle Master, Halberd, PAM + GWM + Sentinel, with advantage | 82 | +14 | 96 / 140 |
| Padlock, Halberd of Vigilance (PAM) | 89 | +6 | 95 / 169 |
| Padlock, Shadow Blade + shield | 87 | +0 | 87 / 120 |
| Battle Master, Halberd, PAM + GWM + Sentinel | 51 | +14 | 64 / 100 |
| Sorcadin, Halberd of Vigilance (PAM) | 59 | +5 | 63 / 133 |
| Sorcadin, Shadow Blade + shield | 62 | +0 | 62 / 114 |
| Battle Master, Halberd, GWM + Savage (no reaction feats) | 53 | +0 | 53 / 72 |
| Fighter 8 / Swashbuckler 4, Dancing Breeze (DEX) | 47 | +4 | 50 / 60 |
| Battle Master, plain Glaive, no gear | 31 | +7 | 38 / 58 |

- **The plain Glaive with no gear** hits AC 18 55% of the time for 1d10 + 4: no magic weapon, no smites, no advantage, and GWM's -5 isn't
  worth it there. It is a no gear baseline, not how the build is played.
- **The Halberd of Vigilance** (Act 2) roughly doubles it: +2 to hit and damage, 1d4 force on every hit, and every reaction attack with
  advantage. With Polearm Master (an enemy entering your reach, about once a fight) and Sentinel (an enemy next to you attacking an ally,
  about every other round) the reactions add about 14 a round in Act 3, so the reaction feats beat Savage Attacker and Strength (65 vs 53).
  With advantage (Trip Attack's prone, Faerie Fire) the Battle Master reaches 96, level with the Halberd Padlock.
- **On a Padlock** the Halberd is the strongest polearm: a bound pact weapon with 3 attacks and the butt end, smites on every hit in
  burst (169). **On a Sorcadin** it gives a big burst (133) but only 63 sustained: 2 attacks, and no Hexblade's Curse.
- **Dexterity glaive:** only works from Act 3 (The Dancing Breeze is the one finesse polearm), see below.
- Reaction attacks are an estimate (the `reactions` toggle on every build); real fights give more when enemies run past you.

## The Dancing Breeze and Hex

| Act 3, sustained / burst | |
|---|---|
| Padlock, Halberd of Vigilance (Polearm Master) + Hex | 112 / 188 |
| Padlock, Shadow Blade + shield + Hex | 98 / 131 |
| Pure Hexblade 12, Shadow Blade + dagger, darkness advantage + Hex | 93 / 93 |
| Fighter 6 / Swashbuckler 6, The Dancing Breeze (Dexterity, Polearm Master, Sentinel) | 59 / 76 (74 with advantage) |
| Fighter 8 / Swashbuckler 4, The Dancing Breeze (Dexterity, Polearm Master, GWM) | 52 / 64 (77 with advantage) |

- **The Dancing Breeze** is a +2 finesse glaive with Whirlwind Attack (hits every enemy around you). Its point is a Dexterity Rogue with
  reach: Sneak Attack is once per *turn*, so with Polearm Master and Sentinel each reaction attack on an enemy's turn adds another Sneak
  Attack (about 15 a round here), and Whirlwind is area damage this single target number doesn't show. As a single target damage
  dealer it is a mid build; it makes sense as the end of a Dexterity Rogue or Fighter you have played all game, not as a target to
  rebuild for in Act 3.
- **Hex** (+1d6 necrotic per hit, concentration, Warlock spell) stacks with Hexblade's Curse, smites and Shadow Blade, which needs no
  concentration in BG3. It adds about 10 to 16 a round to the Padlocks (more hits, more Hex dice) and puts the pure Hexblade with
  darkness advantage at 93, level with the Halberd Padlock without Hex. Builds with no Warlock level don't get it.

## Lockadin, Sorcadin and pure Hexblade variants

| Build (Shadow Blade + shield unless noted) | Act 1 | Act 2 | Act 3 | Act 3 without advantage |
|---|---|---|---|---|
| Lockadin Hexblade 5 first, then Paladin 7 | 31 / 31 | 57 / 80 | 87 / 120 | 64 |
| Lockadin Paladin first, Paladin 6 / Hexblade 6 (or 7 / 5) | 24 / 40 | 46 / 62 | 87 / 120 | 64 |
| Sorcadin 6 / 6 Draconic (red) | 26 / 43 | 44 / 65 | 62 / 114 | 46 |
| Sorcadin 6 / 6 Shadow Magic (Storm and Wild Magic are the same here) | 26 / 43 | 44 / 65 | 62 / 111 | 46 |
| Hex-Sorcadin Paladin 6 / Hexblade 1 / Sorcerer 5 | 19 / 23 | 44 / 62 | 61 / 114 | 44 |
| Vengeance Paladin 11 / Hexblade 1 (Longsword + shield) | 19 / 23 | 34 / 52 | 51 / 74 | 37 |
| Hex-Crown Paladin 11 / Hexblade 1 (Longsword + shield) | 17 / 21 | 30 / 44 | 46 / 66 | 37 |
| Pure Hexblade 12, Shadow Blade + dagger, advantage from darkness | 48 | 48 | 82 | 57 |
| Pure Hexblade 12, Shadow Blade + shield, advantage from darkness | 42 | 43 | 71 | 49 |

- **Lockadin order:** Hexblade 5 first is clearly better in Acts 1 and 2 (Shadow Blade, Extra Attack and Charisma attacks from level 5,
  then Vow and smites at Paladin 3) and the same in Act 3. The cost is armour: multiclassing *into* Paladin only gives light and medium
  armour and shields (bg3.wiki), so heavy armour needs Paladin as the first class (or a feat). Paladin 6 / Hexblade 6 deals the same
  damage as 7 / 5 (Paladin 6 is the one that matters: Aura of Protection).
- **Lockadin vs pure Hexblade:** the Lockadin wins in Act 2 and 3 (87 vs 71 to 82 sustained, and a 120 burst vs none). The pure Hexblade
  is ahead in Act 1, has a third feat, Lifedrinker (+CHA necrotic per hit at Warlock 12), 3 pact slots at level 5 and Warlock utility
  (Devil's Sight and Darkness for advantage, Eldritch Blast, a level 6 Mystic Arcanum). The Paladin side adds the third attack, smites,
  Vow of Enmity, Aura of Protection (+CHA to every save for you and allies nearby) and Lay on Hands.
- **Sorcerer subclass for a Sorcadin:** barely matters for damage. Draconic (red) adds CHA to fire spells (the Quickened Fireball) and
  +1 HP per Sorcerer level. Shadow Magic gives Darkness from sorcery points (Shadow Blade advantage, useful with an oath without Vow) and
  the Hound of Ill Omen, which costs the same 3 sorcery points and bonus action as a Quickened spell. Storm gives flight after spells.
- **Hex-Crown / Paladin 11 + Hexblade 1:** Improved Divine Smite (+1d8 radiant every hit) doesn't make up for 2 attacks and no Shadow Blade
  (Hexblade 1 can't learn it).
- **Swashbuckler with a glaive:** Rakish Sneak Attack and Flick o' the Wrist both need a finesse weapon. The only finesse polearm is
  The Dancing Breeze (Act 3); before that the Rogue levels add no damage, and Strength potions don't change that.

## Assumptions and limits

- Shadow Blade and halberds bound as the pact weapon (Bind Pact / Hexed Weapon). Vengeance Paladins have Vow of Enmity (advantage) all
  fight, and Hexblades have Hexblade's Curse on the target. Hex isn't counted (+1d6 per hit for anyone concentrating on it).
- Booming Blade is off. No gear except the polearms' weapons, so damage-per-hit items (Helldusk, rings, +weapons) widen the gap for
  builds with more attacks. Battle Master's Precision Attack and Trip Attack's prone advantage aren't modelled (the "with advantage" row
  shows what advantage is worth).
