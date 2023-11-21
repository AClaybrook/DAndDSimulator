### D and D Damage Simulator

* Simulates many turns of combat to find distributions of damage, based on various assumptions
* Analytic methods are great for averages and can probably even be applied here, but numerical simulation is just easier for complicated values
* Comparison of up to 4 characters at once

## Design Intent ##

* Build Comparison
* Theory Crafting
    * Barbarin with Reckless Attacks and Advantage
    * Two weapon fighting
    * Fighter 
* Dungeon Master Combat Balancer
* Quantify trade offs between build paths/feats
* Test affects of Homebrew items

## Current Assumptions/Limitations ##
* Classes not implemented
* Assume resources are unlimited (i.e. not tracking spell slots)
* No multitarget, single target only
* Enemys do not fight back/ not considering back and forth combat. So a character with 10 hp and 10 ac is just as good at damage as 100 hp and 20 ac
* Do not consider turn order/initive
* 1 character at a time, no party mode
* 1 Enemy at a time
* Races
* Focused on damage, therefore actions that do not involve damage as not implemented
* Validation of build feasability Garbage in/ garbage out, for example don't use dueling and GWF, the bonuses will be stacked since there is no check. 
* No weapons
* Crit on reductions needs to be applied manually, thing such as champion, spell sniper etc
* no status effects, stunned, restrained etc

## TODO ##
* Manual overrides
* Implement in javascript? :(
* UI design
* Color Scheme
* Design of Experiments
    * Multiple enemy armor class
    * Per level
* Turns to kill a monster
* Expendable resources/damage over time
* Detailed vs simple view?
* Presets
* Spell save DC
* Concept of # of encounters per short/long rest for resources
* Extract "insights", i.e. when to turn on/off GWM/Sharpshooter
* 5e vs BG3 ruleset
* Damage Source, to see impact of various combinations


## Low priority ideas ##
* Ability checks\
* More monsters
* Saving/uploading presets

## Disclaimer ##
* D&D is a roll playing game, first and for most have fun! Damage is only one of the factors, min/maxing damage can be fun, but don't 
* 

## References/Motivation ##
* https://anydice.com/program/22f8c
* d4
* https://www.reddit.com/r/BG3Builds/comments/157p0cl/the_math_of_critical_hits_in_dd_5e_is_critfishing/?onetap_auto=true
* https://statmodeling.stat.columbia.edu/2014/07/12/dnd-5e-advantage-disadvantage-probability/

# Implementation Quirks:
* Copy call back and is getting called when a character is deleted, because the Inputs techically change, but no button was clicked. 
    * Solution was to track the copy counts in state and not update if the triggering id's value was known and did not increment.
* Can not use MATCH when output doesn't have a MATCH, thus settled on reading in ALL Inputs
