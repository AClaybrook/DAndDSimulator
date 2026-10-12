""" Help text: graph descriptions and the quick start guide """
import dash_bootstrap_components as dbc
from dash import html

# What each graph type answers, shown under the graph type selector
GRAPH_DESCRIPTIONS = {
    "DPR Distribution": "How much damage does each character deal per round against this enemy, and how swingy is it?",
    "DPA Distribution": "Which attacks do the damage? The same as DPR, split by attack.",
    "DPR Sweep": "How does damage per round change with one parameter (pick it below)? i.e. is GWM worth it at high armor class, how does a build scale with level",
    "DPA Sweep": "The same as DPR Sweep, split by attack.",
    "Rounds to Kill": "How many rounds does each character need to kill this enemy on their own? Uses the enemy's hit points.",
    "Damage per Fight": "How is damage spread over a fight? Shows bursts from limited resources (Action Surge, smites, first round effects) using Rounds Per Fight.",
}

RECIPES = [
    ("Which build does the most damage?",
     "Add a few presets (Preset, Level, +), pick an enemy, then Simulate with DPR Distribution and read the Leaderboard."),
    ("Is Great Weapon Master or Sharpshooter worth it?",
     "Add a preset with the feat, then run DPR Sweep over Armor Class. The Insights table shows the armor class where you should turn it off."),
    ("Which feat or ASI should I take?",
     "Open the copy menu on a card and pick a change (+2 main ability score, one level higher, advantage, GWM/Sharpshooter, Bless), "
     "or make an exact copy and change it yourself. Compare the expected damage under each name, then Simulate for the full picture."),
    ("How does my build scale?",
     "Add preset characters and run DPR Sweep over Level. Presets level up like the real class and keep any edits you made."),
    ("How fast can we kill this boss?",
     "Load the monster in the Enemy Builder, then run Rounds to Kill."),
    ("Nova or sustained damage?",
     "Set Rounds Per Fight (i.e. 3 for short fights, 6 for long ones) and run Damage per Fight to see round 1 versus later rounds."),
    ("Do my numbers look right?",
     "The Attack Breakdown below every result shows each attack's to hit, damage dice, hit and crit chance and exact expected damage."),
]

def quick_start():
    """ Collapsible quick start guide with the main workflow and recipes for common questions """
    steps = [
        ("1. Characters", "Add presets (they level up like the real class) or blank characters, then tweak them. Each card shows its expected damage per round as you edit."),
        ("2. Enemy", "Load a monster or a CR baseline, or type in armor class, hit points, saves and resistances."),
        ("3. Simulate", "Pick what you want to know and press Simulate (also at the bottom right of the screen). Results start with a one line summary."),
    ]
    return html.Section([
        dbc.Row([
            dbc.Col(html.H5("Quick Start", className="mb-0"), width="auto"),
            dbc.Col(dbc.Button("Hide", id="quick-start-toggle", color="link", size="sm", class_name="p-0"), width="auto"),
        ], align="center", class_name="g-2"),
        dbc.Collapse([
            dbc.Row([dbc.Col([html.B(title), html.P(text, className="small mb-1")], xs=12, md=4) for title, text in steps], class_name="mt-2"),
            html.H6("Common questions", className="mt-2 mb-1 text-info"),
            html.Ul([html.Li([html.B(question + " "), answer], className="small") for question, answer in RECIPES], className="mb-0"),
        ], id="quick-start-collapse", is_open=True),
    ], className="panel mb-4", id="quick-start")
