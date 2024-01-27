// Client-side callbacks

window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: {
        // Update the character name
        update_name: function(character_name){
            return character_name
        },
        // Sidebase toggle
        toggle_classname: function(n,classname){
            if (classname === undefined) {
                return ""
            }
            if (n !== undefined && classname == "") {
                return "collapsed"
            }
            return ""
        },
        toggle_collapse: function(n, is_open){
            if (is_open === undefined) {
                return true
            }
            if (n !== undefined) {
                return !is_open
            }
            return is_open
        },
        // Proficiency Bonus
        proficiency_bonus: function(level){
            if (level === undefined) {
                return 2
            }
            return 2 + Math.floor((level-1)/4)
        },
                // Update attack type
        update_ability_modifier: function(ability_stat, strength, dexterity, constitution, intelligence, wisdom, charisma){
            let ability_modifier = 0
            if (ability_stat == "strength") {
                ability_modifier = Math.floor((strength-10)/2)
            } else if (ability_stat == "dexterity") {
                ability_modifier = Math.floor((dexterity-10)/2)
            } else if (ability_stat == "constitution") {
                ability_modifier = Math.floor((constitution-10)/2)
            } else if (ability_stat == "intelligence") {
                ability_modifier = Math.floor((intelligence-10)/2)
            } else if (ability_stat == "wisdom") {
                ability_modifier = Math.floor((wisdom-10)/2)
            } else if (ability_stat == "charisma") {
                ability_modifier = Math.floor((charisma-10)/2)
            }
            console.log(ability_modifier)
            return ability_modifier
        },
        recolor_characters: function(unused1, colors_json) {
            let colors = JSON.parse(colors_json)
            console.log(colors)
            let styles = []
            for (c of colors){
                styles.push({color: c, whiteSpace:'nowrap'})
            }
            console.log(styles)

            return styles
        }
        // // Update attack type
        // update_attack_type: function(attack_type, state){
        //     console.log(attack_type)
        //     // console.log(state)
        //     let weapon_style = attack_type.startsWith("weapon") ? {} : {display: "none"}
        //     let spell_style = attack_type.startsWith("spell") ? {} : {display: "none"}
        //     state[0]['props']['style'] = weapon_style
        //     state[1]['props']['style'] = weapon_style
        //     state[2]['props']['style'] = weapon_style
        //     state[3]['props']['style'] = spell_style
        //     state[4]['props']['style'] = spell_style
        //     state[5]['props']['style'] = spell_style
        //     console.log(state)
        //     return state
        // },
    }
});
