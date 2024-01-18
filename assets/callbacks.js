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
        }
    }
});
