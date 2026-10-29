""" Ability scores at character creation: point buy plus the +2/+1 bonus, then ability score improvements from feats """
from computations.models import STATS

POINT_BUY_POINTS = 27
POINT_BUY_COSTS = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9}
MAX_SCORE = 20 # Most an ability score improvement can raise a score to

def point_buy_cost(scores):
    """ Points spent on base scores (before the +2/+1 bonus), raises ValueError for a score outside 8-15 """
    total = 0
    for stat in STATS:
        score = int(scores.get(stat, 8))
        if score not in POINT_BUY_COSTS:
            raise ValueError(f"{stat.title()} {score} is outside point buy (8-15)")
        total += POINT_BUY_COSTS[score]
    return total

def point_buy_problems(scores, bonus):
    """ Readable problems with point buy scores and the +2/+1 bonus, empty if they are valid """
    problems = []
    try:
        cost = point_buy_cost(scores)
        if cost > POINT_BUY_POINTS:
            problems.append(f"point buy uses {cost} of {POINT_BUY_POINTS} points")
    except ValueError as e:
        problems.append(str(e))
    values = sorted((int(v) for v in bonus.values() if v), reverse=True)
    if values and values not in ([2, 1], [2], [1]):
        problems.append("the bonus is +2 to one ability and +1 to another")
    if any(stat not in STATS for stat in bonus):
        problems.append("the bonus names an unknown ability")
    return problems

def starting_scores(scores, bonus):
    """ Base scores plus the +2/+1 bonus """
    return {stat: int(scores.get(stat, 8)) + int(bonus.get(stat, 0)) for stat in STATS}

def apply_improvement(scores, choice):
    """ Applies an ability score improvement like 'strength+2' or 'strength+1,constitution+1', capped at 20 """
    scores = dict(scores)
    for part in choice.split(","):
        stat, _, amount = part.strip().partition("+")
        if stat in STATS:
            scores[stat] = min(MAX_SCORE, scores[stat] + int(amount or 2))
    return scores
