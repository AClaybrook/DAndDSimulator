""" Statistical Computations """
from scipy import stats

def get_distributions(dfs,column="damage"):
    """ Returns a list of distributions for a given column in a list of dataframes, used by some plots"""
    dists = []
    for df in dfs:
        val_counts = df[column].value_counts(normalize=True)
        values = (val_counts.index, val_counts.values)
        dist = stats.rv_discrete(values=values)
        dists.append(dist)
    return dists
