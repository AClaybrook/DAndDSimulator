""" BG3 Party Planner: up to four characters with gear and buffs for each act, equipment conflicts and expected damage per act """
import dash_bootstrap_components as dbc
from dash import dcc, html

from bg3.build import ACT_KEYS, compile_build, equipment_at
from bg3.buffs import BUFFS
from bg3.checkpoints import ACTS, act_level
from bg3.items import SLOT_LABELS, SLOTS, catalog, condition_id
from bg3.party import MAX_PARTY_SIZE, build_conflicts, party_conflicts
from bg3.presets import DEFAULT_PARTY as PRESET_PARTY, PRESETS
from bg3.abilities import point_buy_cost, point_buy_problems
from bg3.character import (CANTRIPS, CLASSES, FEATS, FIGHTING_STYLES, LEVELLED_SPELLS, RACES, ROUTINES, SUBCLASSES, TOGGLES, Bg3Character, class_levels,
                           class_order,
                           compile_character, feat_opportunities)
from computations.models import STATS
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

def item_options(slot, act, include_unknown=True):
    """ Items that fit a slot and are found by an act, named items first """
    items = [i for i in catalog().values() if i.fits(slot) and ((i.act is None and include_unknown) or (i.act or 9) <= int(act))]
    items.sort(key=lambda i: (not i.unique, i.act or 9, i.name))
    return [{"label": item_label(i), "value": i.key, "title": item_summary(i)} for i in items]

# Slots that share an item list, the browser fills each dropdown from its group, filtered by act (see assets/callbacks.js)
# The off hand takes melee weapons and shields, so its list is both groups
OPTION_GROUPS = {"melee_main": "melee", "melee_off": "melee+shield", "ranged_main": "ranged", "ranged_off": "ranged", "ring_1": "ring", "ring_2": "ring"}

def option_group(slot):
    return OPTION_GROUPS.get(slot, slot)

def grouped_item_options():
    """ {group: options} with every item's act, sent to the browser once instead of in every dropdown """
    groups = {}
    for slot, _, _ in SLOTS:
        group = option_group(slot)
        if "+" not in group and group not in groups:
            groups[group] = [{**o, "act": catalog()[o["value"]].act} for o in item_options(slot, 3, include_unknown=True)]
    groups["shield"] = [{**o, "act": catalog()[o["value"]].act} for o in item_options("melee_off", 3) if catalog()[o["value"]].slot == "shield"]
    return groups

def gear_table():
    """ Slots down, acts across. An empty cell keeps the item from the act before """
    header = dbc.Row([dbc.Col(html.B("Slot"), width=3)] + [dbc.Col(html.B(ACTS[int(a)][0]), width=3) for a in ACT_KEYS], class_name="g-1 mb-1")
    rows = [header]
    for slot, label, _ in SLOTS:
        rows.append(dbc.Row([dbc.Col(html.Small(label), width=3, class_name="d-flex align-items-center")] + [
            dbc.Col(dcc.Dropdown(options=[], id={"type": "bg3-gear", "slot": slot, "act": act, "group": option_group(slot)},
                                 className="bg3-gear", clearable=True, optionHeight=28), width=3)
            for act in ACT_KEYS], class_name="g-1 mb-1"))
    return html.Div([*rows, dcc.Store(id="bg3-item-options", data=grouped_item_options())], className="bg3-gear-table")

def buff_options(act):
    """ Spells, then elixirs, available by an act. Hover for what isn't modelled """
    def label(b):
        name = b.name.replace("Elixir of ", "Elixir: ")
        return html.Span(name + (" ✦" if b.effects else ""), title=b.notes or "")
    return [{"label": label(b), "value": b.key} for b in BUFFS.values() if b.act <= int(act)]

def planner():
    """ The planner section """
    presets = [{"label": "Custom character (race, classes, feats)", "value": CUSTOM}] + [{"label": b.label, "value": key} for key, b in BUILDS.items()]
    member_editor = dbc.Row([
        dbc.Col([
            dbc.InputGroup([
                dbc.Select(options=[{"label": name, "value": name} for name in PRESETS], placeholder="Start from an example build...", id="bg3-load-preset"),
                dbc.Button("Load", id="bg3-load", color="secondary", title="Replace this character with the example build, gear included"),
            ], size="sm", class_name="mb-2"),
            dbc.InputGroup([dbc.InputGroupText("Name"), dbc.Input(id="bg3-name", type="text")], size="sm", class_name="mb-2"),
            dbc.InputGroup([dbc.InputGroupText("Class"), dbc.Select(options=presets, id="bg3-preset")], size="sm", class_name="mb-2"),
            dbc.Collapse(custom_builder(), id="bg3-custom", is_open=False),
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
            dbc.Col([html.H6("Expected damage per round", className="text-info"), html.Div(id="bg3-dpr"),
                     dcc.Graph(id="bg3-dpr-chart", config={"displayModeBar": False}, style={"height": "280px"})], xs=12, lg=6),
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

# Party line colors in fixed order, the app's series colors with the green stepped darker to pass the palette checks on the dark surface
PARTY_COLORS = ["#636EFA", "#EF553B", "#00A87C", "#AB63FA"]
SURFACE = "#303030"

def dpr_chart(builds, enemy, rounds_per_fight):
    """ Expected damage per round of each character across the act checkpoints """
    import plotly.graph_objects as go
    fig = go.Figure()
    ends = []
    for ii, b in enumerate(builds):
        acts = [f"Act {a} (L{act_level(a, b.levels)})" for a in ACT_KEYS]
        values = [expected_damage_per_round(compile_build(b, a), enemy, rounds_per_fight) for a in ACT_KEYS]
        color = PARTY_COLORS[ii % len(PARTY_COLORS)]
        fig.add_trace(go.Scatter(
            x=[f"Act {a}" for a in ACT_KEYS], y=values, name=b.name, mode="lines+markers", customdata=acts,
            line={"color": color, "width": 2}, marker={"size": 9, "color": color, "line": {"color": SURFACE, "width": 2}},
            hovertemplate="%{fullData.name}<br>%{customdata}: %{y:.1f} damage per round<extra></extra>"))
        ends.append([values[-1], b.name.split(" (")[0]])
    # End labels, nudged apart so close finishes don't overlap
    top = max([v for v, _ in ends] + [1])
    ends.sort()
    for jj in range(1, len(ends)):
        ends[jj][0] = max(ends[jj][0], ends[jj - 1][0] + 0.08 * top)
    for y, name in ends:
        fig.add_annotation(x="Act 3", y=y, text=name, showarrow=False, xanchor="left", xshift=10, font={"color": "#cfcfcf", "size": 11})
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=280,
        margin={"l": 40, "r": 100, "t": 10, "b": 30}, legend={"orientation": "h", "y": 1.12, "x": 0, "font": {"size": 11}},
        yaxis={"title": None, "gridcolor": "#444", "gridwidth": 1, "zeroline": False, "rangemode": "tozero"},
        xaxis={"title": None, "showgrid": False}, hoverlabel={"bgcolor": "#222"})
    return fig

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

CUSTOM = "custom"
STAT_SHORT = {s: s[:3].title() for s in STATS}

def cb(field):
    """ Id of a custom builder field """
    return {"type": "bg3-cb", "field": field}

def improvement_options():
    """ Feat level choices: an ability score improvement or a feat """
    asi = [{"label": f"+2 {STAT_SHORT[s]}", "value": f"{s}+2"} for s in STATS]
    pairs = [{"label": f"+1 {STAT_SHORT[a]} / +1 {STAT_SHORT[b]}", "value": f"{a}+1,{b}+1"} for i, a in enumerate(STATS) for b in STATS[i + 1:]]
    feats = [{"label": f, "value": f} for f in FEATS if f != "Ability Improvement"]
    return asi + feats + pairs

def custom_builder():
    """ Race, point buy, class levels in order, feats and fighting styles for a custom character """
    select = {"size": "sm"}
    stat_options = [{"label": s.title(), "value": s} for s in STATS]
    return html.Div([
        dbc.InputGroup([dbc.InputGroupText("Race"), dbc.Select(options=[{"label": r, "value": r} for r in RACES], id=cb("race"))], size="sm", class_name="mb-1"),
        html.Small("Point buy (27 points, 8-15) and the +2/+1", className="text-muted"),
        dbc.Row([dbc.Col(dbc.InputGroup([dbc.InputGroupText(STAT_SHORT[s]), dbc.Input(type="number", min=8, max=15, step=1, id=cb(f"score:{s}"))],
                                        size="sm"), width=4, class_name="mb-1") for s in STATS], class_name="g-1"),
        dbc.Row([
            dbc.Col(dbc.InputGroup([dbc.InputGroupText("+2"), dbc.Select(options=stat_options, id=cb("plus2"))], size="sm")),
            dbc.Col(dbc.InputGroup([dbc.InputGroupText("+1"), dbc.Select(options=stat_options, id=cb("plus1"))], size="sm")),
        ], class_name="g-1 mb-1"),
        html.Small("Classes in the order levels are taken (up to 12 levels)", className="text-muted"),
        *[dbc.Row([
            dbc.Col(dbc.Select(options=[{"label": "-", "value": ""}] + [{"label": c.title(), "value": c} for c in CLASSES], id=cb(f"class:{row}"), **select), width=4),
            dbc.Col(dbc.Select(options=[], id={"type": "bg3-cb-sub", "row": row}, placeholder="Subclass", **select), width=5),
            dbc.Col(dbc.Input(type="number", min=0, max=12, step=1, id=cb(f"levels:{row}"), size="sm", placeholder="Levels"), width=3),
        ], class_name="g-1 mb-1") for row in range(3)],
        dbc.Row([
            dbc.Col(dbc.Select(options=[{"label": label, "value": key} for key, label in ROUTINES.items()], id=cb("routine"), **select)),
            dbc.Col(dbc.Select(options=[{"label": c, "value": c} for c in CANTRIPS], id=cb("cantrip"), **select)),
            dbc.Col(dbc.Select(options=[{"label": "No levelled spell", "value": ""}] + [{"label": f"{sp}, then cantrip", "value": sp} for sp in LEVELLED_SPELLS],
                               id=cb("spell"), **select)),
        ], class_name="g-1 mb-1"),
        html.Small("Feat levels in order (an improvement or a feat)", className="text-muted"),
        dbc.Row([dbc.Col(dbc.Select(options=improvement_options(), id=cb(f"feat:{n}"), placeholder=f"Feat {n + 1}", **select), width=6, class_name="mb-1")
                 for n in range(6)], class_name="g-1"),
        dbc.Row([dbc.Col(dbc.Select(options=[{"label": "-", "value": ""}] + [{"label": f, "value": f} for f in FIGHTING_STYLES], id=cb(f"style:{n}"),
                                    placeholder=f"Fighting style {n + 1}", **select)) for n in range(2)], class_name="g-1 mb-1"),
        dbc.Checklist(options=[{"label": label, "value": key} for key, label in TOGGLES.items()], id=cb("toggles"), class_name="small"),
        html.Div(id="bg3-cb-summary", className="small mt-1"),
    ], className="bg3-custom mb-2 p-2")

def fields_from_character(character, field_ids):
    """ Builder field values (in the order of field_ids) from a Bg3Character """
    values = {"race": character.race, "routine": character.routine, "cantrip": character.cantrip, "spell": character.spell,
              "toggles": [k for k in TOGGLES if character.toggle(k)]}
    plus = sorted(character.bonus.items(), key=lambda kv: -kv[1])
    values["plus2"] = plus[0][0] if plus else None
    values["plus1"] = plus[1][0] if len(plus) > 1 else None
    for stat in STATS:
        values[f"score:{stat}"] = character.scores.get(stat, 8)
    for row in range(3):
        cls, _, levels = character.classes[row] if row < len(character.classes) else ("", "", None)
        values[f"class:{row}"], values[f"levels:{row}"] = cls, levels
    for n in range(6):
        values[f"feat:{n}"] = character.feats[n] if n < len(character.feats) else None
    for n in range(2):
        values[f"style:{n}"] = character.fighting_styles[n] if n < len(character.fighting_styles) else ""
    return [values.get(fid["field"]) for fid in field_ids]

def character_from_fields(field_ids, values, subclasses, name):
    """ A Bg3Character from the builder fields """
    v = {fid["field"]: value for fid, value in zip(field_ids, values)}
    bonus = {}
    if v.get("plus2"):
        bonus[v["plus2"]] = 2
    if v.get("plus1") and v.get("plus1") != v.get("plus2"):
        bonus[v["plus1"]] = 1
    classes = [[v[f"class:{row}"], subclasses[row] or "", int(v.get(f"levels:{row}") or 0)] for row in range(3)
               if v.get(f"class:{row}") and int(v.get(f"levels:{row}") or 0) > 0]
    toggles = {k: k in (v.get("toggles") or []) for k in TOGGLES}
    return Bg3Character(name=name, race=v.get("race") or "Human", scores={s: int(v.get(f"score:{s}") or 8) for s in STATS}, bonus=bonus,
                        classes=classes or [["fighter", "Champion", 12]], feats=[v[f"feat:{n}"] for n in range(6) if v.get(f"feat:{n}")],
                        fighting_styles=[v[f"style:{n}"] for n in range(2) if v.get(f"style:{n}")], routine=v.get("routine") or "two_handed",
                        cantrip=v.get("cantrip") or "Eldritch Blast", spell=v.get("spell") or "", toggles=toggles)

def subclass_options(cls):
    return [{"label": s, "value": s} for s in SUBCLASSES.get(cls, [])]

def builder_summary(character, levels):
    """ Point buy, the class split at each act, feat levels and anything not modelled """
    problems = point_buy_problems(character.scores, character.bonus)
    total = len(class_order(character))
    if total < max(levels):
        problems.append(f"{total} class levels, the last act checkpoint needs {max(levels)}")
    feat_levels = [lv for lv, _ in feat_opportunities(character)]
    parts = [html.Div(f"Point buy: {point_buy_cost_safe(character.scores)} of 27 points. Feats at levels {', '.join(map(str, feat_levels)) or 'none'}")]
    for act, level in zip(ACT_KEYS, levels):
        split = " / ".join(f"{cls.title()} {n}" for cls, n in class_levels(character, level).items())
        parts.append(html.Div(f"Act {act} (level {level}): {split}"))
    _, notes = compile_character(character, max(levels))
    parts += [html.Div(p, className="text-warning") for p in problems] + [html.Div(n, className="text-muted") for n in notes]
    return parts

def point_buy_cost_safe(scores):
    try:
        return point_buy_cost(scores)
    except ValueError:
        return "?"

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
           "conflicts_list", "dpr_chart", "gear_highlights", "inherited_placeholders", "item_values_table", "suggestions_table", "CUSTOM", "fields_from_character",
           "character_from_fields", "subclass_options", "builder_summary"]
