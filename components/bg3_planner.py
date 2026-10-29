""" BG3 Party Planner: up to four characters with gear and buffs for each act, equipment conflicts and expected damage per act """
import dash_bootstrap_components as dbc
from dash import dcc, html

from bg3.build import ACT_KEYS, compile_build, equipment_at
from bg3.buffs import BUFFS
from bg3.checkpoints import ACTS, act_level
from bg3.items import SLOT_LABELS, SLOTS, catalog, condition_id
from bg3.party import MAX_PARTY_SIZE, build_conflicts, party_conflicts
from bg3.presets import DEFAULT_PARTY as PRESET_PARTY, PRESETS
from computations.analytic import expected_damage_per_round
from game_data.classes import BUILDS

DEFAULT_PARTY = [PRESETS[name].to_dict() for name in PRESET_PARTY]

def effect_text(effect):
    target = "" if effect.applies_to in ("all", "self") else f" ({effect.applies_to.replace('_', ' ')})"
    what = {"ability_min": f"{effect.stat.title()} {effect.value}", "ability_bonus": f"{effect.stat.title()} +{effect.value}",
            "attack_bonus": f"+{effect.value} to hit", "attack_dice": f"+{effect.value} to hit", "damage_bonus": f"+{effect.value} damage",
            "damage_bonus_ability": f"+{effect.stat.title()} modifier to damage", "extra_damage": f"+{effect.value} damage",
            "crit_damage": f"+{effect.value} on a crit", "crit_range": f"crit range +{effect.value}", "advantage": "advantage",
            "spell_dc": f"+{effect.value} spell DC", "damage_reroll": f"reroll damage dice of {effect.value} or less",
            "miss_damage_ability": f"{effect.stat.title()} modifier damage on a miss", "once_per_turn_bonus": f"+{effect.value} Sneak Attack damage", "extra_attack": "extra attack", "flag": str(effect.value)}.get(effect.kind, effect.kind)
    return what + target + (f" [toggle: {effect.condition}]" if effect.condition else "")

def item_summary(item):
    """ Hover text: modelled effects, other effects, where it's found """
    parts = []
    if item.weapon:
        w = item.weapon
        parts.append(f"{w['damage']} {w['damage_type']}" + (f" +{w['enhancement']}" if w.get("enhancement") else "") +
                     (f", {', '.join(w['properties'])}" if w.get("properties") else ""))
    parts += [effect_text(e) for e in item.effects]
    if item.notes:
        parts.append(f"Not modelled: {item.notes}")
    if item.location:
        parts.append(f"Found: {item.location}")
    return "\n".join(parts)

def item_label(item):
    if not item.unique:
        return f"{item.name} (common)"
    details = " · ".join(x for x in [item.rarity, f"Act {item.act}" if item.act else "Act ?"] if x)
    # Marks items whose effects change damage in the simulator
    marker = " ✦" if item.effects or (item.weapon and item.weapon.get("enhancement")) else ""
    return f"{item.name}{marker} · {details}"

def item_options(slot, act):
    """ Items that fit a slot and are found by an act, named items first """
    items = [i for i in catalog().values() if i.fits(slot) and (i.act is None or i.act <= int(act))]
    items.sort(key=lambda i: (not i.unique, i.act or 0, i.name))
    return [{"label": item_label(i), "value": i.key, "title": item_summary(i)} for i in items]

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
    """ Spells, then elixirs, available by an act. Hover for what isn't modelled """
    def label(b):
        name = b.name.replace("Elixir of ", "Elixir: ")
        return html.Span(name + (" ✦" if b.effects else ""), title=b.notes or "")
    return [{"label": label(b), "value": b.key} for b in BUFFS.values() if b.act <= int(act)]

def planner():
    """ The planner section """
    presets = [{"label": b.label, "value": key} for key, b in BUILDS.items()]
    member_editor = dbc.Row([
        dbc.Col([
            dbc.InputGroup([
                dbc.Select(options=[{"label": name, "value": name} for name in PRESETS], placeholder="Start from an example build...", id="bg3-load-preset"),
                dbc.Button("Load", id="bg3-load", color="secondary", title="Replace this character with the example build, gear included"),
            ], size="sm", class_name="mb-2"),
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
                ". An empty gear cell keeps the item from the act before. Unique items wanted by more than one character are highlighted. "
                "✦ marks items whose effects the simulator models, hover an item for its effects. Item data: Patch 8, from ",
                html.A("bg3.wiki", href="https://bg3.wiki", target="_blank"), "."],
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
        ], class_name="mb-3"),
        gear_advice(),
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

def gear_advice():
    """ What the selected character's gear is worth, and the best items for a slot """
    slot_options = [{"label": label, "value": key} for key, label, _ in SLOTS if key != "ring_2"]
    return dbc.Row([
        dbc.Col(dbc.InputGroup([
            dbc.InputGroupText("Gear advice for the selected character at"),
            dbc.Select(options=[{"label": ACTS[int(a)][0], "value": a} for a in ACT_KEYS], value="1", id="bg3-advice-act"),
        ], size="sm"), xs=12, class_name="mb-2"),
        dbc.Col([html.H6("What each item adds", className="text-info"), html.Div(id="bg3-item-values")], xs=12, lg=5),
        dbc.Col([
            dbc.InputGroup([dbc.InputGroupText("Best items for"), dbc.Select(options=slot_options, value="melee_main", id="bg3-advice-slot")],
                           size="sm", class_name="mb-1"),
            html.Div(id="bg3-suggestions"),
        ], xs=12, lg=7),
    ], class_name="bg3-advice")

def gain_text(gain):
    return f"{gain:+.1f}"

def item_values_table(values):
    if not values:
        return html.Div("Nothing equipped at this act. Empty weapon slots use the class preset's base weapon.", className="small text-muted")
    rows = [html.Tr([html.Td(SLOT_LABELS[slot], className="text-muted"), html.Td(item.name, title=item_summary(item)), html.Td(gain_text(gain))])
            for slot, item, gain in values]
    return dbc.Table([html.Thead(html.Tr([html.Th("Slot"), html.Th("Item"), html.Th("Damage per round")])), html.Tbody(rows)],
                     size="sm", hover=True, class_name="mb-0 small")

def suggestions_table(suggestions):
    if not suggestions:
        return html.Div("No item in this slot adds damage for this character yet.", className="small text-muted")
    rows = [html.Tr([html.Td(item.name, title=item_summary(item)), html.Td(gain_text(gain)), html.Td(f"Act {item.act}" if item.act else "Act ?"),
                     html.Td(", ".join(users), className="text-warning" if users else "")])
            for item, gain, users in suggestions]
    return html.Div([
        dbc.Table([html.Thead(html.Tr([html.Th("Item"), html.Th("Damage per round"), html.Th("Found"), html.Th("Also used by")])), html.Tbody(rows)],
                  size="sm", hover=True, class_name="mb-0 small"),
        html.Div("Compared to an empty slot (weapons: the class preset's base weapon). Conditional effects count when toggled on.",
                 className="small text-muted"),
    ])

def conflicts_list(conflicts, gains=None):
    """ Conflicts by act, shared items show what each character gains from the item """
    gains = gains or {}
    def message(c):
        if c.kind == "shared" and (c.act, c.item) in gains:
            g = gains[(c.act, c.item)]
            best = max(g, key=g.get)
            return f"{c.message.split(' is wanted')[0]}: " + ", ".join(f"{name} {gain_text(v)}" for name, v in g.items()) + f". Best on {best}"
        return c.message
    if not conflicts:
        return html.Div([html.I(className="fa-solid fa-check me-1 text-success"), "No equipment conflicts"], className="small")
    by_act = {}
    for c in conflicts:
        by_act.setdefault(c.act, []).append(c)
    return html.Div([html.Div([html.B(f"Act {act}", className="small"),
                               html.Ul([html.Li(message(c), className="small text-warning" if c.kind == "shared" else "small") for c in items_],
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
    """ CSS classes for each gear cell: items this character shares with others, and its own gear problems, including carried over items """
    flagged = {(c.act, c.item) for c in conflicts if build.name in c.members}
    gear_by_act = {act: equipment_at(build, act) for act in ACT_KEYS}
    return ["bg3-gear bg3-conflict" if (gid["act"], gear_by_act[gid["act"]].get(gid["slot"])) in flagged else "bg3-gear" for gid in gear_ids]

__all__ = ["planner", "DEFAULT_PARTY", "MAX_PARTY_SIZE", "party_conflicts", "build_conflicts", "conditional_options", "dpr_table",
           "conflicts_list", "gear_highlights", "inherited_placeholders", "item_values_table", "suggestions_table"]
