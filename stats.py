import scipy.stats as stats

def get_distributions(dfs,column="damage"):
    dists = []
    for df in dfs:
        val_counts = df[column].value_counts(normalize=True)
        values = (val_counts.index, val_counts.values)
        dist = stats.rv_discrete(values=values)
        dists.append(dist)
    return dists