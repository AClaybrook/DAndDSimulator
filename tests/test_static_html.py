""" Read only output rendered as one Markdown component """
import dash_bootstrap_components as dbc
import pytest
from dash import dcc, html

from components.static_html import static, to_html

def test_html_and_bootstrap_markup():
    table = dbc.Table([html.Thead(html.Tr([html.Th("A")])), html.Tbody(html.Tr(html.Td([html.B("1 < 2"), " & more"], title="line 1\nline 2",
                                                                                        className="text-muted", style={"maxWidth": "5rem"})))],
                      size="sm", hover=True, responsive=True, class_name="mb-0")
    out = to_html(dbc.Row(dbc.Col(table, xs=12, md=6)))
    assert out.startswith('<div class="row"><div class="col-12 col-md-6"><div class="table-responsive"><table class="table table-hover table-sm mb-0">')
    assert '<td class="text-muted" title="line 1&#10;line 2" style="max-width:5rem"><b>1 &lt; 2</b> &amp; more</td>' in out
    assert "\n" not in out
    assert to_html([21.0, 27.92, 3]) == "2127.923" # A blank line would end the Markdown HTML block

def test_static_is_one_component():
    out = static([html.Div("a"), None, 3, html.Ul([html.Li("x")]), html.Br()])
    assert isinstance(out, dcc.Markdown) and out.dangerously_allow_html
    assert out.children == "<div><div>a</div>3<ul><li>x</li></ul><br/></div>"

def test_inputs_are_refused():
    with pytest.raises(ValueError):
        to_html(html.Div(dbc.Button("x", id="b")))
    with pytest.raises(ValueError):
        to_html(dcc.Input(id="i"))

def test_planner_tables_render():
    from bg3.build import Bg3Build
    from components.bg3_planner import DEFAULT_PARTY, ac_table, conflicts_list, dpr_table, score_table
    from computations.models import Enemy
    from bg3.party import party_conflicts
    builds = [Bg3Build.from_dict(b) for b in DEFAULT_PARTY]
    for node in [dpr_table(builds, Enemy(), 3), ac_table(builds, Enemy(), 6), score_table(builds, Enemy(), 3, 6),
                 conflicts_list(party_conflicts(builds))]:
        assert "<table" in to_html(node) or "<ul" in to_html(node) or "conflicts" in to_html(node)
