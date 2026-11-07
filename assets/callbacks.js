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
        // BG3 planner: fill each gear dropdown from its slot group's item list, keeping items found by the dropdown's act
        // (items of unknown act are always offered)
        gear_options: function(groups){
            const outputs = dash_clientside.callback_context.outputs_list;
            return outputs.map(function(output){
                const act = parseInt(output.id.act);
                const options = [].concat(...output.id.group.split("+").map(function(g){ return groups[g] || []; }));
                return options.filter(function(o){ return o.act === null || o.act <= act; })
                    .map(function(o){ return {label: o.label, value: o.value, title: o.title}; });
            });
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
