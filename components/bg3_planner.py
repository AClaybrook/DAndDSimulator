""" BG3 Party Planner: up to four characters with gear and buffs for each act, equipment conflicts and expected damage per act """
import dash_bootstrap_components as dbc
from dash import dcc, html

from bg3.build import ACT_KEYS, Bg3Build, compile_build, equipment_at
from bg3.buffs import BUFFS
from bg3.checkpoints import ACTS, act_level
from bg3.items import SLOTS, catalog, condition_id
from bg3.party import MAX_PARTY_SIZE, build_conflicts, conflicting_items, party_conflicts
from computations.analytic import expected_damage_per_round
from game_data.classes import BUILDS

DEFAULT_PARTY = [
    Bg3Build("Lae'zel", "fighter_gwm").to_dict(),
    Bg3Build("Karlach", "barbarian_berserker").to_dict(),
    Bg3Build("Astarion", "rogue_assassin").to_dict(),
    Bg3Build("Gale", "wizard_fireball").to_dict(),
]

def item_label(item):
    if not item.unique:
        return f"{item.name} (base weapon)"
    details = " · ".join(x for x in [item.rarity, f"Act {item.act}" if item.act else ""] if x)
    return f"{item.name} · {details}" if details else item.name

def item_options(slot, act):
    """ Items that fit a slot and are found by an act, named items first """
    items = [i for i in catalog().values() if i.fits(slot) and (i.act is None or i.act <= int(act))]
    items.sort(key=lambda i: (not i.unique, i.act or 0, i.name))
    return [{"label": item_label(i), "value": i.key} for i in items]

def gear_table():
    """ Slots down, acts across. An empty cell keeps the item from the act before """
    header = dbc.Row([dbc.Col(html.B("Slot"), width=3)] + [dbc.Col(html.B(ACTS[int(a)][0]), width=3) for a in ACT_KEYS], class_name="g-1 mb-1")
    rows = [header]
    for slot, label, _ in SLOTS:
        rows.append(dbc.Row([dbc.Col(html.Small(label), width=3, class_name="d-flex align-items-center")] + [
            dbc.Col(dcc.Dropdown(options=item_options(slot, act), id={"type": "bg3-gear", "slot": slot, "act": act},
                                 className="bg3-gear", clearable=True, optionHeight=28), width=3)
            for act in ACT_KEYS], class_name="g-1 mb-1"))
    return html.Div(rows, className="bg3-gear-table")

def buff_options(act):
    return [{"label": b.name, "value": b.key} for b in BUFFS.values() if b.act <= int(act)]

def planner():
    """ The planner section """
    presets = [{"label": b.label, "value": key} for key, b in BUILDS.items()]
    member_editor = dbc.Row([
        dbc.Col([
            dbc.InputGroup([dbc.InputGroupText("Name"), dbc.Input(id="bg3-name", type="text")], size="sm", class_name="mb-2"),
            dbc.InputGroup([dbc.InputGroupText("Class"), dbc.Select(options=presets, id="bg3-preset")], size="sm", class_name="mb-2"),
            html.Small("Level at each checkpoint", className="text-muted"),
            dbc.Row([dbc.Col(dbc.InputGroup([dbc.InputGroupText(f"Act {a}"), dbc.Input(type="number", min=1, max=12, step=1,
                                                                                         id={"type": "bg3-level", "act": a})], size="sm"))
                     for a in ACT_KEYS], class_name="g-1 mb-2"),
            html.Small("Buffs during fights", className="text-muted"),
            dbc.Row([dbc.Col([html.Div(f"Act {a}", className="small"), dbc.Checklist(options=buff_options(a), id={"type": "bg3-buffs", "act": a},
                                                                                      class_name="small")]) for a in ACT_KEYS], class_name="g-1 mb-2"),
            html.Small("Conditional item effects (tick the ones your build sets up)", className="text-muted"),
            dbc.Checklist(id="bg3-conditions", class_name="small"),
        ], xs=12, lg=4),
        dbc.Col(gear_table(), xs=12, lg=8),
    ], class_name="mb-3")

    return html.Section([
        dbc.Row([
            dbc.Col(html.H3("BG3 Party Planner", id="bg3-planner", className="mb-0")),
            dbc.Col(dbc.InputGroup([
                dbc.Select(options=[*[{"label": f"Party at {ACTS[int(a)][0]}", "value": a} for a in ACT_KEYS],
                                    {"label": "Selected character, every act", "value": "member"}], value="1", id="bg3-send-act"),
                dbc.Button([html.I(className="fa-solid fa-arrow-down me-1"), "Add to simulator"], id="bg3-send", color="primary",
                           title="Add the compiled characters as cards below, to simulate and tweak them"),
            ], size="sm"), width="auto"),
        ], align="center", class_name="mb-1"),
        html.P(["Plan up to four characters with gear and buffs for each act. Checkpoints: ",
                ", ".join(f"{label} at level {level}" for label, level in ACTS.values()),
                ". An empty gear cell keeps the item from the act before. Unique items wanted by more than one character are highlighted."],
               className="small text-muted mb-2"),
        dbc.Row([
            dbc.Col(dbc.Tabs(id="bg3-member-tabs", active_tab="0"), class_name="mb-2"),
            dbc.Col(dbc.ButtonGroup([
                dbc.Button(html.I(className="fa-solid fa-user-plus"), id="bg3-add-member", color="primary", size="sm", title="Add a character"),
                dbc.Button(html.I(className="fa-solid fa-user-minus"), id="bg3-remove-member", color="danger", size="sm", title="Remove the selected character"),
            ]), width="auto"),
        ], align="center"),
        member_editor,
        dbc.Row([
            dbc.Col([html.H6("Expected damage per round", className="text-info"), html.Div(id="bg3-dpr")], xs=12, lg=6),
            dbc.Col([html.H6("Equipment conflicts", className="text-info"), html.Div(id="bg3-conflicts")], xs=12, lg=6),
        ]),
        dcc.Store(id="bg3-party", storage_type="local", data=DEFAULT_PARTY),
    ], className="panel mb-4")

def conditional_options(build):
    """ Toggles for the conditional effects of everything the build equips in any act """
    items, options, seen = catalog(), [], set()
    for act in ACT_KEYS:
        for key in equipment_at(build, act).values():
            item = items.get(key)
            if item is None or key in seen:
                continue
            seen.add(key)
            options += [{"label": f"{item.name}: {e.condition}", "value": condition_id(key, ii)} for ii, e in enumerate(item.effects) if e.condition]
    return options

def dpr_table(builds, enemy, rounds_per_fight):
    """ Exact expected damage per round for each character at each act """
    rows = []
    for b in builds:
        cells = [html.Td(b.name)]
        for act in ACT_KEYS:
            try:
                cells.append(html.Td(f"{expected_damage_per_round(compile_build(b, act), enemy, rounds_per_fight):.1f}"))
            except Exception as e: # pylint: disable=broad-exception-caught
                cells.append(html.Td("?", title=str(e)))
        rows.append(html.Tr(cells))
    # Levels can differ per character
    levels = {a: sorted({act_level(a, b.levels) for b in builds}) for a in ACT_KEYS}
    header = html.Thead(html.Tr([html.Th("Character")] + [html.Th(f"Act {a} (L{'/'.join(map(str, levels[a]))})") for a in ACT_KEYS]))
    return dbc.Table([header, html.Tbody(rows)], size="sm", bordered=False, hover=True, class_name="mb-0")

def conflicts_list(conflicts):
    if not conflicts:
        return html.Div([html.I(className="fa-solid fa-check me-1 text-success"), "No equipment conflicts"], className="small")
    by_act = {}
    for c in conflicts:
        by_act.setdefault(c.act, []).append(c)
    return html.Div([html.Div([html.B(f"Act {act}", className="small"),
                               html.Ul([html.Li(c.message, className="small text-warning" if c.kind == "shared" else "small") for c in items_],
                                       className="mb-1")])
                     for act, items_ in sorted(by_act.items())])

def inherited_placeholders(build, gear_ids):
    """ Empty cells show the item carried over from the act before """
    items, placeholders = catalog(), []
    for gid in gear_ids:
        act_index = ACT_KEYS.index(gid["act"])
        carried = equipment_at(build, ACT_KEYS[act_index - 1]).get(gid["slot"]) if act_index else None
        placeholders.append(f"↳ {items[carried].name}" if carried in items else "—")
    return placeholders

def gear_highlights(build, conflicts, gear_ids):
    """ CSS classes for each gear cell: shared items and the character's own gear problems are highlighted """
    own = {(c.act, c.item) for c in conflicts if build.name in c.members and c.kind != "shared"}
    classes = []
    for gid in gear_ids:
        key = build.equipment.get(gid["act"], {}).get(gid["slot"])
        flagged = key and (key in conflicting_items(conflicts, gid["act"]) and any(c.item == key and build.name in c.members for c in conflicts)
                           or (gid["act"], key) in own)
        classes.append("bg3-gear bg3-conflict" if flagged else "bg3-gear")
    return classes

__all__ = ["planner", "DEFAULT_PARTY", "MAX_PARTY_SIZE", "party_conflicts", "build_conflicts", "conditional_options", "dpr_table",
           "conflicts_list", "gear_highlights", "inherited_placeholders"]
