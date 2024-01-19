# Dungeons and Dragons Damage Simulator

Live here: https://d-and-d-damage-simulator-745953dd5908.herokuapp.com/

##  For the D and D Theory Craftors of the World
![Alt Text](assets/CharacterBuilder.PNG)
![Alt Text](assets/Simulator.PNG)

* Simulates many thousand turns of combat to find distributions of damage for a given character
* Compare D&D characters at once for the theory crafters of the world, i.e.:
    * A Barbarian with Reckless Attacks with Advantage
    * A Fighter With the two Great Weapon Master Feat
* Not sure which Feat to take for optimal DPS? Well why not simulate them all and find out?

## References/Motivation ##
* https://www.youtube.com/@DnDDeepDive
* https://www.reddit.com/r/BG3Builds/comments/157p0cl/the_math_of_critical_hits_in_dd_5e_is_critfishing/?onetap_auto=true
* https://statmodeling.stat.columbia.edu/2014/07/12/dnd-5e-advantage-disadvantage-probability/
* https://forums.giantitp.com/showthread.php?582779-Comprehensive-DPR-Calculator-%28v2-0%29
* https://anydice.com/program/22f8c

## How to Install and Run Locally 
* Download or git clone the repo from: https://github.com/AClaybrook/DAndDSimulator
* Linux terminal install instructions:
    * Install the python and requirements
        * Install python3.11+ if needed from https://www.python.org/downloads/
        * Install pipenv if needed `pip install pipenv` 
        * `pipenv install --ignore-pipfile`
    * Activate the virtual environment
        * `pipenv shell`
    * Launch the App on localhost 8050:
        * `python app.py`
        * Or run app.py from VsCode

# Technical Notes/Features:

## Completed Features:
* UI: Character, Enemy, Simulator, and Tables
* Collapsable nav/sidebar
* Import and Export of characters via json
* Simulate Combat from UI values
* 4 different simulation types and corresponding plots:
    * Damage Per Round
    * Damage Per Attack
    * Damage Per Round vs Armor Class
    * Damage Per Attack vs Armor Class
* Export Damage Results to csv
* Implement easy callbacks in javascript 
* Reduce memory of dataframes
* Random Seed toggle for random vs repeatable results

## In Works
* UI design
    * Update attacks based on selected type
* Double check values are identical when reading elements
    * characters and attacks in UI get translated to python and back the same way
* Performance gains in callbacks

## TODO
* Import Character Presets
* Design of Experiments (vary a specified parameter)
* "Leaderboard"
* Tips for UI
* Validate numerical sims and implement tests

### Backlog
* 5e vs BG3 ruleset
    * Currently all calculations are implemented using the BG3 ruleset
* Expendable resources/damage over time
    * Can currently be simulated as a different character
* Simulate turns to kill a monster
* Ability checks
* Monsters presets
* Saving/uploading enemys
* Variable Color Theme
* Concept of # of encounters per short/long rest for resources
* Extract "insights", i.e. when to turn on/off GWM/Sharpshooter
    * Have to manually look at graphs/tables currently
* Damage Source, to see impact of various combinations, i.e. damage gain from bless
    * Alternatively could just implement diffing characters
* Multiple Enemys
* Summary Stats Section
* Better app logging
* Preview character bonuses to attack

## Current Assumptions/Limitations ##
* Classes and Races are not fully implemented, just the main damaging perks
* Assume resources are unlimited (i.e. not tracking spell slots)
* No multitarget, single target only
* Enemys do not fight back/ not considering back and forth combat. So a character with 10 hp and 10 ac is just as good at damage as a character with 100 hp and 20 ac. Only enemy defensive stats matter
* Do not consider turn order/initive
* 1 character at a time, no party mode
* 1 Enemy at a time
* Focused on damage, therefore actions that do not involve damage as not implemented
* Validation of build feasability is not done. Garbage in/ garbage out
    * Only some basic checks like GWM only with twohanded weapons 
* Adjusting rolls needed for critial hits (Crit on) needs to be applied manually, i.e. a Fighter taking the Champion subclass, spell sniper feat need to be accounted for by manually reducing the Character Crit on field
* no status effects, stunned, restrained etc

### Callback Implementation Quirks:
* Copy callback and others get called unintentionally when a character is deleted, because the Inputs techically change
    * Solution is to check time of the last clicked button and skip if copy wasn't clicked last
* Can not use MATCH for an Inuput when an Output doesn't have a MATCH, thus have to reach in ALL Inputs

### Build ideas
* Bladesinger
* Ice Sorcerer, prone
* Fire sorceror
* Gloomstalker, assasin
* Wardomain cleric, 
* Life domain cleric, healing extreme
* Barbarian cleave (bleed build)
* Bard crossbow arcane acuity
* Pure Fighter

