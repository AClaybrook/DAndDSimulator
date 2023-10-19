# %%
# Imports
import plotly.express as px
import random
import pandas as pd
import plotly.figure_factory as ff
import numpy as np
from IPython.display import display
import dash
from dash import dash_table, Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
from dash import html
import pandas as pd
from dataclasses import dataclass, replace, asdict
import scipy.stats as stats

#%%
# Analytic Values
def expected_value(die_size):
    """ Returns the expected value of a die roll, which is a uniform distribution"""
    return (1 + die_size)/2

def avg_damage(num_die, die_size):
    """Average damage of multiple dice rolls"""
    ev = expected_value(die_size)
    return num_die * ev

def hit_chance(die, mod=0, ac=15, adv=False, dis=False, crit_on=20):
    roll_needed = ac - mod
    # Crit chance, always crit on 20, somtimes this can be lower, such as 19, 18, 17, etc.
    crit_chance = (die-crit_on+1)/die
    # Crit miss chance, always miss on 1
    crit_miss_chance = 1/die
    if dis:
        min_hit_chance = (1 - crit_miss_chance)**2
    elif adv:
        min_hit_chance = crit_miss_chance * crit_miss_chance
    return min(min_hit_chance, (die-roll_needed +1)/die)


# adv = [advantage(d1,d2) for d1 in rolls for d2 in rolls]
# dis = [disadvantage(d1,d2) for d1 in rolls for d2 in rolls]

# %%

# Numerical Simulation

# # Defaults
# rng = random.Random()
# rng.seed(1)

def roll(die_size=20, reroll_on=None):
    rerolled = False
    res = rng.randint(1,die_size)
    if reroll_on is not None and res <= reroll_on:
        res = rng.randint(1,die_size)
        rerolled = True
    return res

def advantage(d1, d2):
    return max(d1, d2)

def disadvantage(d1, d2):
    return min(d1, d2)

def roll_adv_dis(adv=False, dis=False,  **kwargs):
    if adv and not dis:
        res = advantage(roll(**kwargs), roll(**kwargs))
    elif dis and not adv:
        res = disadvantage(roll(**kwargs), roll(**kwargs))
    else:
        res = roll(**kwargs)
    return res

def attack_roll(attack_modifier=0, enemy_armor_class=15, crit_on=20, attack_reroll_on=None, **kwargs):
    """ Returns total attack roll, whether it hits, whether it crits and the roll value"""
    roll_val = roll_adv_dis(reroll_on=attack_reroll_on, **kwargs)
    attack_roll_val = roll_val + attack_modifier
    # Crit miss
    if roll_val == 1:
        hit, crit = False, False
    # Crit hit
    elif roll_val >= crit_on:
        hit, crit = True, True
    # Normal hit
    elif attack_roll_val >= enemy_armor_class:
        hit, crit = True, False
    # Normal miss
    else:
        hit, crit = False, False

    return attack_roll_val, roll_val, hit, crit

def damage_roll(num_die=1, damage_die=6, damage_modifier=0, damage_reroll_on=None, crit=False, **kwargs):
    
    hit_damage = sum([roll(die_size=damage_die, reroll_on=damage_reroll_on, **kwargs) for _ in range(num_die)]) + damage_modifier
    
    crit_damage = 0
    if crit:
        crit_damage = sum([roll(die_size=damage_die, reroll_on=damage_reroll_on, **kwargs) for _ in range(num_die)])

    total_damage = hit_damage + crit_damage

    return total_damage, hit_damage, crit_damage

def attack(attack_context, damage_context):
    total_damage, hit_damage, crit_damage = 0, 0, 0
    attack_roll_val, roll_val, hit, crit = attack_roll(**attack_context)
    if hit:
        total_damage, hit_damage, crit_damage = damage_roll(crit=crit, **damage_context)
    return attack_roll_val, roll_val, hit, crit, total_damage, hit_damage, crit_damage

def simulate_rounds(num_attacks, attack_context, damage_context, num_rounds=10000):
    results = np.zeros((num_rounds*num_attacks, 8), dtype=int)
    row = 0
    for round_ in range(num_rounds):
        # Damage per round
        for _ in range(num_attacks):
            attack_roll_val, roll_val, hit, crit, damage, hit_damage, crit_damage = attack(attack_context, damage_context)
            results[row] = np.array([round_+1, attack_roll_val, roll_val, hit, crit, damage, hit_damage, crit_damage])
            row += 1
    df = pd.DataFrame(results, columns=['round', 'attack_roll', 'attack_die_roll', 'hit', 'crit', 'damage', 'hit_damage', 'crit_damage'])
    return df

# Utility functions
def die_from_str(die_str):
    """Returns the number of dice and die size from a string of the form '2d6'"""
    die_str = die_str.lower()
    num_die, die_size = die_str.split('d')
    return int(num_die), int(die_size)

# Classes

# TOOD: Change this to a Creature class, and have Character and Enemy inherit from it
@dataclass
class Character:
    name: str = 'Character'
    num_attacks: int = 1
    # Attack and Damage Roll Modifiers
    ability_modifier: int = 0
    GWM: bool = False
    weapon_modifier: int = 0
    # Attack Roll Modifiers
    proficiency_bonus: int = 0
    adv: bool = False
    dis: bool = False
    additional_attack_modifier: int = 0
    attack_reroll_on: int = None
    crit_on: int = 20
    # Damage Roll Modifiers
    weapon_die: str = '1d6'
    additional_damage_modifier: int = 0
    GWF: bool = False
    # _damage_reroll_on: int = None # Internal variable managed by @property and setter

    @property
    def weapon_num_die(self):
        return die_from_str(self.weapon_die)[0]
    
    @property
    def weapon_damage_die(self):
        return die_from_str(self.weapon_die)[1]
    
    @property
    def attack_modifier(self):
        GWM_modifier = -5 if self.GWM else 0
        return self.ability_modifier + self.proficiency_bonus + self.weapon_modifier + GWM_modifier + self.additional_attack_modifier

    @property
    def damage_modifier(self):
        GWM_modifier = 10 if self.GWM else 0
        return self.ability_modifier + self.weapon_modifier + GWM_modifier + self.additional_damage_modifier
    
    @property
    def damage_reroll_on(self):
        return 2 if self.GWF else None
    
    # @property
    # def damage_reroll_on(self):
    #     if self._damage_reroll_on is not None:
    #         return self._damage_reroll_on
    #     return 2 if self.GWF else None
    
    # @damage_reroll_on.setter
    # def damage_reroll_on(self, value):
    #     self._damage_reroll_on = value

@dataclass
class Enemy:
    name: str = 'Mind Flayer'
    armor_class: int = 15
    hit_points: int = 71
    damage_reduction: int = 0

@dataclass
class AttackContext:
    attack_modifier: int = 0
    adv: bool = False
    dis: bool = False
    crit_on: int = 20
    attack_reroll_on: int = None
    enemy_armor_class: int = 15

    @staticmethod
    def from_character_and_enemy(character, enemy, **kwargs):
        return AttackContext(
            attack_modifier=character.attack_modifier,
            adv=character.adv,
            dis=character.dis,
            crit_on=character.crit_on,
            attack_reroll_on=character.attack_reroll_on,
            enemy_armor_class=enemy.armor_class,
            **kwargs
        )
    
@dataclass
class DamageContext:
    num_die: int = 1
    damage_die: int = 6
    damage_modifier: int = 0
    damage_reroll_on: int = None

    @staticmethod
    def from_character_and_enemy(character, enemy, **kwargs):
        # TODO: Add enemy damage reduction
        return DamageContext(
            num_die=character.weapon_num_die,
            damage_die=character.weapon_damage_die,
            damage_modifier=character.damage_modifier,
            damage_reroll_on=character.damage_reroll_on,
            **kwargs
        )

# %%
# Example 1

# Defaults
rng = random.Random()
rng.seed(1)

# Character stats
character1 = Character(
    name='Fighter',
    proficiency_bonus=4, # Level 9-12
    ability_modifier=5, # 20-21
    num_attacks=3,
    weapon_die='2d6',
    )

character2 = replace(character1, name='Fighter Disadvantage', dis=True)
character3 = replace(character1, name='Fighter Advantage', adv=True)
enemy1 = Enemy(armor_class=18)

characters = [character1, character2, character3]
dfs = []
df_by_rounds = []
for c in characters:
    # Attack roll modifiers
    attack_context = AttackContext.from_character_and_enemy(c, enemy1)

    # Damage roll modifiers
    damage_context = DamageContext.from_character_and_enemy(c, enemy1)

    # Num Rounds
    df = simulate_rounds(c.num_attacks, asdict(attack_context), asdict(damage_context), num_rounds=5000)


    display(df.describe())
    df_by_round = df.groupby('round').sum()
    display(df_by_round.describe())
    dfs.append(df)
    df_by_rounds.append(df_by_round)

#%%
# Plotting
# Themes here: https://plotly.com/python/templates/
import plotly.graph_objects as go

template = 'plotly_dark'
def generate_histogram(data, x, color, marginal='violin', histnorm='percent', barmode='overlay', opacity=0.75,template=template, **kwargs):
    """Apparently this is deprecated except for the kdensity plot"""
    fig = px.histogram(
        data, 
        x=x, 
        color=color, 
        marginal=marginal,
        histnorm=histnorm,
        barmode=barmode,
        opacity=opacity,
        template=template,
        **kwargs
    )
    return fig

def generate_distplot(groups, labels, template=template):
    fig = ff.create_distplot(groups, labels, show_rug=False, template=template)
    return fig

# Using distplot
# groups = [df_by_round["damage"] for df_by_round in df_by_rounds]
# labels = [c.name for c in characters]
# fig = generate_distplot(groups, labels)

# def add_damage_percent(data):
#     percent_dict = data.groupby("Type")["damage"].value_counts(normalize=True).to_dict()
#     data["Percent"] = data.apply(lambda x: percent_dict[(x["Type"], x["damage"])], axis=1)*100
#     return data

def add_damage_percent(data):
    percent_dict = data.groupby("Type")["damage"].value_counts(normalize=True).to_dict()
    data["Percent"] = data.apply(lambda x: percent_dict[(x["Type"], x["damage"])], axis=1)*100
    return data

def get_distributions(dfs,column="damage"):
    dists = []
    for df in dfs:
        val_counts = df[column].value_counts(normalize=True)
        values = (val_counts.index, val_counts.values)
        dist = stats.rv_discrete(values=values)
        dists.append(dist)
    return dists

# data = add_damage_percent(data)
# fig = px.bar(data, x="damage", y="Percent", color="Type",template=template, opacity=0.75,barmode='overlay')
# fig.show()


# fig.show()



data = pd.concat([pd.DataFrame({'damage': df_by_round["damage"], 'Type': c.name}) for c, df_by_round in zip(characters,df_by_rounds)])

fig = generate_histogram(data, x="damage", color="Type", marginal='violin')

# CDF

# fig = px.ecdf(data, x="damage", color="Type", marginal="histogram",orientation='h', template=template)

fig.show()






# %%


app = dash.Dash(__name__)

def add_tables():
    table_list = [html.H2("Summary Statistics Per Round")]
    for ii, (c, df_by_round) in enumerate(zip(characters, df_by_rounds)):
        df_table = df_by_round.describe().reset_index()
        table_list.append(html.H4(c.name)) 
        table_list.append(html.Div([
                dash_table.DataTable(
                    id=f'table{ii}',
                    columns=[{"name": i, "id": i} for i in df_table.columns],
                    data=df_table.to_dict('records')
                )
            ]))
    return table_list

app.layout = html.Div([
    html.H1("D&D Damage Per Round"),
    dcc.Graph(
        id='dist-plot',
        figure=fig
    ),
    *add_tables()
])

app.run_server(debug=False)

# %%
# Simple crit chance calculator
# https://bg3.wiki/wiki/Guide:Book%27s_Guide_to_Crits
crit_data = []
for crit_on in range(20,12, -1):
    crit_chance = (20-crit_on+1)/20
    crit_miss = 1-crit_chance
    crit_miss_w_adv = crit_miss * crit_miss
    crit_w_adv = 1-crit_miss_w_adv
    crit_data.append([crit_on, crit_chance, crit_w_adv])
pd.DataFrame(crit_data, columns=['crit_on', 'crit_chance', 'crit_w_adv'])

# %%
