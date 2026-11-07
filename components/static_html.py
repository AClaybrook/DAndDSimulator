""" Read only output as one component: a Dash html/dbc tree turned into an HTML string inside a single dcc.Markdown.

    Why: the Dash 4 renderer dispatches a store update for every component a callback adds, and each update re-checks every component
    on the page. A results table of 50 cells replaced on each planner edit cost seconds; as one Markdown block it is one update.
    Only for display: no ids, callbacks or inputs inside (to_html raises on anything it can't render as plain HTML) """
from html import escape

from dash import dcc
from dash.development.base_component import Component

ATTRIBUTES = {"className": "class", "class_name": "class", "title": "title", "href": "href", "target": "target", "colSpan": "colspan",
              "rowSpan": "rowspan"}
TAGS = {"Table", "Thead", "Tbody", "Tr", "Td", "Th", "Div", "Span", "B", "I", "Small", "Ul", "Ol", "Li", "A", "H4", "H5", "H6", "P", "Br", "Strong",
        "Em"}
BREAKPOINTS = ("xs", "sm", "md", "lg", "xl", "xxl")

def _style(style):
    return ";".join(f"{''.join('-' + c.lower() if c.isupper() else c for c in key)}:{value}" for key, value in style.items())

def _attrs(component, classes=()):
    attrs = {}
    for prop, name in ATTRIBUTES.items():
        value = getattr(component, prop, None)
        if value not in (None, ""):
            attrs[name] = f"{attrs[name]} {value}" if name in attrs else str(value)
    if classes:
        attrs["class"] = " ".join([*classes, attrs.get("class", "")]).strip()
    if getattr(component, "style", None):
        attrs["style"] = _style(component.style)
    # Newlines in a title would end the Markdown HTML block at a blank line, encode them
    return "".join(f' {k}="{escape(v).replace(chr(10), "&#10;")}"' for k, v in attrs.items())

def to_html(node):
    """ HTML for a tree of html.* components (and dbc Table, Row and Col), strings and numbers """
    if node is None or node is False:
        return ""
    if isinstance(node, (list, tuple)):
        return "".join(to_html(n) for n in node)
    if isinstance(node, float) and node.is_integer():
        return str(int(node)) # As the browser shows a number: 21.0 is 21
    if not isinstance(node, Component):
        return escape(str(node)).replace("\n", " ")
    kind = node._type # pylint: disable=protected-access
    if node._namespace == "dash_bootstrap_components": # pylint: disable=protected-access
        return _bootstrap(node, kind)
    if node._namespace != "dash_html_components" or kind not in TAGS: # pylint: disable=protected-access
        raise ValueError(f"{node._namespace}.{kind} can't be shown as static HTML") # pylint: disable=protected-access
    tag = kind.lower()
    if tag == "br":
        return "<br/>" # A bare <br> blanks the whole Markdown block
    return f"<{tag}{_attrs(node)}>{to_html(getattr(node, 'children', None))}</{tag}>"

def _column_classes(node):
    classes = []
    for point in ("width", *BREAKPOINTS):
        value = getattr(node, point, None)
        if isinstance(value, dict):
            value = value.get("size")
        if value not in (None, ""):
            infix = "" if point in ("width", "xs") else f"-{point}"
            classes.append(f"col{infix}" if value is True else f"col{infix}-{value}")
    return classes or ["col"]

def _bootstrap(node, kind):
    """ The dbc layout and table components the result tables use, as their Bootstrap markup """
    if kind == "Table":
        classes = ["table"] + [f"table-{flag}" for flag in ("hover", "striped", "bordered") if getattr(node, flag, None)]
        classes += [f"table-{node.size}"] if getattr(node, "size", None) else []
        table = f"<table{_attrs(node, classes)}>{to_html(node.children)}</table>"
        return f'<div class="table-responsive">{table}</div>' if getattr(node, "responsive", None) else table
    if kind == "Row":
        return f"<div{_attrs(node, ['row'])}>{to_html(node.children)}</div>"
    if kind == "Col":
        return f"<div{_attrs(node, _column_classes(node))}>{to_html(node.children)}</div>"
    raise ValueError(f"dbc.{kind} can't be shown as static HTML")

def static(node, class_name=None):
    """ One dcc.Markdown showing the tree, see the module docstring """
    return dcc.Markdown(f"<div>{to_html(node)}</div>", dangerously_allow_html=True, className=class_name or "static-html")
