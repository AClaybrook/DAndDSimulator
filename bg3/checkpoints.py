""" Act checkpoints: standard points of comparison that roughly match the end of each act """

# Act: (label, default level). Acts 1 and 2 matter most, by Act 3 most builds are already strong
ACTS = {
    1: ("End of Act 1", 5),
    2: ("End of Act 2", 8),
    3: ("End of Act 3", 12),
}

def act_label(act):
    label, level = ACTS[int(act)]
    return f"{label} (level {level})"

def act_level(act, levels=None):
    """ The level used for an act, levels can override the defaults, i.e. {"1": 4} """
    levels = levels or {}
    return int(levels.get(str(act), levels.get(int(act), ACTS[int(act)][1])))
