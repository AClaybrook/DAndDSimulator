""" Act 1 item map: notable items and key pickups on the game's minimap images, a separate page at /map """
import json
from pathlib import Path

import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import Input, Output, State, dcc, get_asset_url, html, no_update
from dash.exceptions import PreventUpdate

from bg3.build import ACT_KEYS, Bg3Build, equipment_at
from bg3.checkpoints import ACTS
from bg3.items import SLOT_LABELS, catalog

DATA = json.loads((Path(__file__).parent.parent / "bg3" / "data" / "map_act1.json").read_text(encoding="utf-8"))
MAPS = DATA["maps"]
POINTS = DATA["points"]
RARITIES = ["Key", "Legendary", "Story", "Very Rare", "Rare", "Uncommon", "Common"]
DEFAULT_RARITIES = ["Key", "Legendary", "Story", "Very Rare", "Rare"]
# The game's rarity colours, so markers read like the inventory. Key pickups (buffs, crafting) aren't items, white stars
COLORS = {"Common": "#9a9a9a", "Uncommon": "#3fbf5a", "Rare": "#3d8ff5", "Very Rare": "#b35cf2", "Legendary": "#e8b13a", "Story": "#f07a35",
          "Key": "#ffffff"}
WEAPON_SLOTS = {"weapon"}
LABELLED = {"Key", "Legendary", "Very Rare", "Story"}
PARTY_COLOR = "#ffd23f"

def asset(path):
    try:
        return get_asset_url(path)
    except Exception: # pylint: disable=broad-except
        return f"/assets/{path}" # No app yet, i.e. in tests

def party_gear(party, act):
    """ {item key: ["Member (slot)", ...]} for the planner party's gear at an act """
    gear = {}
    for data in party or []:
        try:
            build = Bg3Build.from_dict(data)
        except TypeError:
            continue
        for slot, key in equipment_at(build, act).items():
            if key and not key.startswith("base:"):
                gear.setdefault(key, []).append(f"{build.name} ({SLOT_LABELS.get(slot, slot)})")
    return gear

def rank(rarity):
    return RARITIES.index(rarity) if rarity in RARITIES else len(RARITIES)

def visible(point, rarities, options, search, party=None):
    if search and point["name"] in search:
        return True
    if party is not None and point["key"] in party:
        return True
    if "party_only" in options:
        return False
    if point["rarity"] not in rarities:
        return False
    if "builds" in options and point["rarity"] != "Key" and not point["builds"]:
        return False
    if "no_traders" in options and point["trader"]:
        return False
    if "no_inside" in options and point["inside"]:
        return False
    return True

def groups(map_key, rarities, options, search, party=None):
    """ Points on one map grouped by spot, best rarity first in each """
    by_spot = {}
    for p in POINTS:
        if p["map"] == map_key and visible(p, rarities, options, search, party):
            spot = (p["px"], p["py"]) if MAPS[map_key]["image"] else (p["x"], p["y"])
            by_spot.setdefault(spot, []).append(p)
    return [(spot, sorted(ps, key=lambda p: (rank(p["rarity"]), p["name"]))) for spot, ps in by_spot.items()]

def hover(points, party=None):
    party = party or {}
    first = points[0]
    where = f"{first['location']} (X {first['x']}, Y {first['y']})" + (" - inside, marked at the entrance" if first["inside"] else "")
    lines = [f"<b>{where}</b>"]
    for p in points[:12]:
        tags = [p["rarity"]] + (["trader"] if p["trader"] else []) + ([f"in {len(p['builds'])} example builds"] if p["builds"] else [])
        lines.append(f"{'★ ' if p['builds'] else ''}{p['name']} <span style='color:{COLORS.get(p['rarity'])}'>({', '.join(tags)})</span>" +
                     (f"<br>&nbsp;&nbsp;<span style='color:{PARTY_COLOR}'>Party: {', '.join(party[p['key']])}</span>" if p["key"] in party else ""))
    if len(points) > 12:
        lines.append(f"+{len(points) - 12} more, click for the list")
    return "<br>".join(lines)

def label(points, names, party):
    """ Marker text: every marker with names on, otherwise the rare finds and party gear """
    mine = [p for p in points if p["key"] in party]
    if mine:
        return mine[0]["name"] + (f" +{len(points) - 1}" if names and len(points) > 1 else "")
    if names or points[0]["rarity"] in LABELLED:
        return points[0]["name"] + (f" +{len(points) - 1}" if len(points) > 1 else "")
    return ""

def figure(map_key, rarities, options, search, template="plotly_dark", party=None, collected=()):
    m = MAPS[map_key]
    fig = go.Figure()
    party = {k: v for k, v in (party or {}).items() if k not in set(collected)}
    names = "names" in options
    spots = groups(map_key, rarities, options, search, party)
    # One trace per best rarity, so the legend works as a key
    for rarity in RARITIES:
        chosen = [(spot, ps) for spot, ps in spots if ps[0]["rarity"] == rarity]
        if not chosen:
            continue
        x = [spot[0] for spot, _ in chosen]
        y = [spot[1] for spot, _ in chosen]
        found = [any(p["name"] in (search or []) for p in ps) for _, ps in chosen]
        fig.add_trace(go.Scatter(
            x=x, y=y, mode="markers+text", name=rarity if rarity != "Key" else "Key pickup",
            text=[label(ps, names or hit, party) for (_, ps), hit in zip(chosen, found)],
            textposition="top center", textfont={"size": 11, "color": "#f2f2f2"},
            hovertext=[hover(ps, party) for _, ps in chosen], hoverinfo="text",
            customdata=[[map_key, f"{spot[0]},{spot[1]}"] for spot, _ in chosen],
            marker={"color": COLORS[rarity], "size": [min(10 + 2 * (len(ps) - 1), 20) + (8 if hit else 0) for (_, ps), hit in zip(chosen, found)],
                    "symbol": ["star" if rarity == "Key" else "diamond" if ps[0]["slot"] in WEAPON_SLOTS else "circle" for _, ps in chosen],
                    "line": {"color": ["#ff3355" if hit else "#111111" for hit in found], "width": [3 if hit else 1.5 for hit in found]},
                    "opacity": 0.95},
        ))
    # Party gear still to collect: a ring around its marker
    mine = [(spot, ps) for spot, ps in spots if any(p["key"] in party for p in ps)]
    if mine:
        fig.add_trace(go.Scatter(x=[s[0] for s, _ in mine], y=[s[1] for s, _ in mine], mode="markers", name="Party gear to collect",
                                 hovertext=[hover(ps, party) for _, ps in mine], hoverinfo="text",
                                 customdata=[[map_key, f"{s[0]},{s[1]}"] for s, _ in mine],
                                 marker={"symbol": "circle-open", "size": 28, "color": PARTY_COLOR, "line": {"width": 3}}))
    layout = {"template": template, "margin": {"l": 0, "r": 0, "t": 10, "b": 0}, "dragmode": "pan", "hoverlabel": {"align": "left", "bgcolor": "rgba(20,20,24,0.95)", "bordercolor": "#555", "font": {"color": "#eeeeee", "size": 12}},
              "legend": {"orientation": "h", "y": 1.0, "x": 0.01, "bgcolor": "rgba(0,0,0,0.55)"}, "uirevision": map_key}
    if m["image"]:
        fig.add_layout_image(source=asset(f"maps/{m['image']}"), xref="x", yref="y", x=0, y=0, sizex=m["width"], sizey=m["height"],
                             xanchor="left", yanchor="top", sizing="stretch", layer="below")
        layout.update(xaxis={"range": [0, m["width"]], "visible": False, "constrain": "domain"},
                      yaxis={"range": [m["height"], 0], "visible": False, "scaleanchor": "x"},
                      plot_bgcolor="#000000")
    else:
        layout.update(xaxis={"title": "Minimap X", "zeroline": False}, yaxis={"title": "Minimap Y", "scaleanchor": "x", "zeroline": False})
    if not spots:
        fig.add_annotation(text="Nothing on this map matches the filters", showarrow=False, xref="paper", yref="paper", x=0.5, y=0.5,
                           font={"size": 16})
    fig.update_layout(**layout)
    return fig

def details(points, party=None):
    """ The list shown when a marker is clicked """
    party = party or {}
    first = points[0]
    rows = []
    for p in points:
        rows.append(html.Li([
            html.A(p["name"], href=p["source"], target="_blank", style={"color": COLORS.get(p["rarity"])}),
            html.Span(f" {p['rarity']}" + (f", {p['slot'].replace('_', ' ')}" if p.get("slot") else ""), className="text-muted small"),
            html.Div(p["where"], className="small") if p.get("where") else None,
            html.Div(p["notes"], className="small text-muted") if p.get("notes") else None,
            html.Div(f"Your party: {', '.join(party[p['key']])}", className="small", style={"color": PARTY_COLOR}) if p["key"] in party else None,
            html.Div(f"★ Used by: {', '.join(p['builds'])}", className="small text-info") if p.get("builds") else None,
        ], className="mb-2"))
    return [html.H6(f"{first['location']} - X {first['x']}, Y {first['y']}" + (" (inside; marker at the entrance)" if first["inside"] else "")),
            html.Ul(rows, className="ps-3 mb-0")]

def map_list(map_key, spots, party):
    """ Every item on the current map, by location, best first """
    by_location = {}
    for _, ps in spots:
        loc = ps[0]["location"] + (" (inside)" if ps[0]["inside"] else "")
        by_location.setdefault(loc, []).extend(ps)
    ordered = sorted(by_location.items(), key=lambda kv: min(rank(p["rarity"]) for p in kv[1]))
    count = sum(len(ps) for ps in by_location.values())
    return [html.H6(f"On the {MAPS[map_key]['label']} map ({count})", className="mt-2"),
            html.Div([html.Div([html.Div(loc, className="fw-bold mt-1"),
                                *[html.Div([html.A(p["name"], href=p["source"], target="_blank", style={"color": COLORS.get(p["rarity"])}),
                                            html.Span(" ◎" if p["key"] in party else "", style={"color": PARTY_COLOR})], className="ms-2")
                                  for p in sorted(ps, key=lambda p: (rank(p["rarity"]), p["name"]))]]) for loc, ps in ordered],
                     style={"maxHeight": "60vh", "overflowY": "auto"})]

def party_checklist(party, act):
    """ Checklist options for the party's gear at an act: where each item is, on these maps or not """
    items = catalog()
    options = []
    for key, users in party_gear(party, act).items():
        spots = [p for p in POINTS if p["key"] == key]
        where = "; ".join(sorted({f"{p['location']} ({MAPS[p['map']]['label']})" for p in spots})) or \
            next((u["where"] or u["location"] for u in DATA["unplaced"] if u["key"] == key), "") or "not on the Act 1 maps"
        name = items[key].name if key in items else key
        options.append((not spots, name, {"label": html.Span([html.B(name), f" - {', '.join(users)}. ", html.Span(where, className="text-muted")]),
                                         "value": key}))
    return [o for *_, o in sorted(options, key=lambda o: (o[0], o[1]))]

def unplaced_table():
    rows = [html.Tr([html.Td(html.A(u["name"], href=u["source"], target="_blank", style={"color": COLORS.get(u["rarity"])})), html.Td(u["rarity"]),
                     html.Td(u["where"] or u["location"], className="small")]) for u in DATA["unplaced"] if u["rarity"] != "Uncommon"]
    return dbc.Table([html.Thead(html.Tr([html.Th("Item"), html.Th("Rarity"), html.Th("Where")])), html.Tbody(rows)],
                     size="sm", striped=True, class_name="small mb-0")

def map_page():
    names = sorted({p["name"] for p in POINTS})
    return dbc.Container([
        html.H3("BG3 Act 1 Map", className="mb-1"),
        html.P(["Where to find the notable gear and key pickups in Act 1. Hover a marker for what's there and its minimap coordinates (shown under the "
                "in-game minimap), click it for details and wiki links. ◆ weapons, ● armour and accessories, ★ key pickups; bigger markers hold "
                "more items. Items inside dungeons and buildings are marked at the entrance."], className="small text-muted mb-2"),
        dbc.Row([
            dbc.Col(dbc.RadioItems(options=[{"label": m["label"], "value": k} for k, m in MAPS.items()], value="wilderness", id="map-region",
                                   inline=True, input_class_name="btn-check", label_class_name="btn btn-outline-primary btn-sm",
                                   label_checked_class_name="active"), xs=12, class_name="mb-2"),
            dbc.Col(dbc.Checklist(options=[{"label": r if r != "Key" else "Key pickups", "value": r} for r in RARITIES], value=DEFAULT_RARITIES,
                                  id="map-rarities", inline=True, class_name="small"), xs=12, lg=6, class_name="mb-2"),
            dbc.Col(dbc.Checklist(options=[{"label": "Show item names", "value": "names"},
                                           {"label": "Only my party's gear", "value": "party_only"},
                                           {"label": "Only gear used by example builds", "value": "builds"},
                                           {"label": "Hide trader stock", "value": "no_traders"},
                                           {"label": "Hide items inside dungeons", "value": "no_inside"}],
                                  value=[], id="map-options", inline=True, class_name="small"), xs=12, lg=6, class_name="mb-2"),
            dbc.Col(dcc.Dropdown(options=names, multi=True, placeholder="Find items (highlights them on any map)...", id="map-search"),
                    xs=12, class_name="mb-2"),
        ]),
        dbc.Row([
            dbc.Col(dcc.Graph(id="map-graph", figure=figure("wilderness", DEFAULT_RARITIES, [], []), style={"height": "80vh"},
                              config={"scrollZoom": True, "displaylogo": False}), xs=12, xl=9),
            dbc.Col([html.Div(id="map-found", className="small mb-2"),
                     html.Div("Hover a marker for its items, click it for details.", id="map-details", className="small"),
                     html.Div(id="map-list", className="small")], xs=12, xl=3),
        ]),
        html.Section([
            dbc.Row([
                dbc.Col(html.H5("My party's gear", className="mb-0")),
                dbc.Col(dbc.Select(options=[{"label": f"Planned for {ACTS[int(a)][0]}", "value": a} for a in ACT_KEYS], value="1", id="map-party-act",
                                   size="sm"), width="auto"),
            ], align="center", class_name="mb-1"),
            html.P("The gear your BG3 Party Planner characters wear at that act, with gold rings on the map. Tick items as you collect them "
                   "(saved in this browser); collected items lose their ring.", className="small text-muted mb-1"),
            dbc.Checklist(id="map-party-list", class_name="small"),
            dcc.Store(id="map-collected", storage_type="local", data=[]),
        ], className="panel mt-3"),
        dbc.Accordion([dbc.AccordionItem(unplaced_table(), title=f"Notable Act 1 items with no map location ({sum(u['rarity'] != 'Uncommon' for u in DATA['unplaced'])}): "
                                         "camp chests, traders' levelled stock, carried by wandering characters")],
                      start_collapsed=True, class_name="mt-3"),
        html.P(["Item locations: ", html.A("bg3.wiki", href="https://bg3.wiki", target="_blank"), " (CC BY-NC-SA 4.0). Map images: Baldur's Gate 3 "
                "minimap textures © Larian Studios, via bg3.wiki. Unofficial fan tool."], className="small text-muted mt-2"),
    ], fluid=True)

def register_map_callbacks(app, template="plotly_dark"):
    @app.callback(
        Output("main-page", "style"),
        Output("map-page", "style"),
        Output("simulate-float", "style"),
        Input("url", "pathname"),
    )
    def route(pathname):
        on_map = (pathname or "").rstrip("/").endswith("/map")
        hidden = {"display": "none"}
        return (hidden, {}, hidden) if on_map else ({}, hidden, {})

    @app.callback(
        Output("map-party-list", "options"),
        Output("map-party-list", "value"),
        Input("bg3-party", "data"),
        Input("map-party-act", "value"),
        State("map-collected", "data"),
    )
    def party_list(party, act, collected):
        options = party_checklist(party, act)
        return options, [o["value"] for o in options if o["value"] in set(collected or [])]

    @app.callback(
        Output("map-collected", "data"),
        Input("map-party-list", "value"),
        State("map-party-list", "options"),
        State("map-collected", "data"),
        prevent_initial_call=True,
    )
    def remember_collected(ticked, options, collected):
        # Keep what was ticked for other acts' gear
        shown = {o["value"] for o in options or []}
        return sorted((set(collected or []) - shown) | set(ticked or []))

    @app.callback(
        Output("map-graph", "figure"),
        Output("map-found", "children"),
        Output("map-list", "children"),
        Input("map-region", "value"),
        Input("map-rarities", "value"),
        Input("map-options", "value"),
        Input("map-search", "value"),
        Input("bg3-party", "data"),
        Input("map-party-act", "value"),
        Input("map-party-list", "value"),
    )
    def update_map(map_key, rarities, options, search, party, act, collected):
        found = []
        for name in search or []:
            maps = sorted({MAPS[p["map"]]["label"] for p in POINTS if p["name"] == name})
            found.append(html.Div(f"{name}: {', '.join(maps)}"))
        gear = {k: v for k, v in party_gear(party, act).items() if k not in set(collected or [])}
        spots = groups(map_key, rarities or [], options or [], search or [], gear)
        return (figure(map_key, rarities or [], options or [], search or [], template, gear), found, map_list(map_key, spots, gear))

    @app.callback(
        Output("map-details", "children"),
        Input("map-graph", "clickData"),
        State("map-rarities", "value"),
        State("map-options", "value"),
        State("map-search", "value"),
        State("bg3-party", "data"),
        State("map-party-act", "value"),
        State("map-party-list", "value"),
        prevent_initial_call=True,
    )
    def show_details(click, rarities, options, search, party, act, collected):
        if not click or not click.get("points"):
            raise PreventUpdate
        map_key, spot = click["points"][0].get("customdata") or [None, None]
        if map_key is None:
            return no_update
        gear = {k: v for k, v in party_gear(party, act).items() if k not in set(collected or [])}
        for s, points in groups(map_key, rarities or [], options or [], search or [], gear):
            if f"{s[0]},{s[1]}" == spot:
                return details(points, gear)
        return no_update
