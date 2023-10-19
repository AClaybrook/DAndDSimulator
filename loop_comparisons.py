# %%
import numpy as np
import pandas as pd

from functools import wraps
from time import time
from IPython.display import display

# Ref https://pythonspeed.com/articles/pandas-vectorization/
def timeit(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        # print('func:%r args: took: %2.4f sec' % \
        #   (f.__name__, te-ts))
        return f.__name__, te-ts
    return wrap

def display_results(results, size):
    print(f"Loop: size={size}, row={row}")
    df = pd.DataFrame(results, columns=['method','time (s)']).sort_values('time (s)')
    df['time per iter (micro sec)'] = df['time (s)'] / size * 1e6
    display(df)
    return df

def run_methods(methods, size=10000, row=[1,2,3,4,5]):
    results = []
    for method in methods:
        results.append(method(size,row))
    df = display_results(results,size)
    return results

def display_results_func(results,size):
    print(f"Loop: size={size}")
    df = pd.DataFrame(results, columns=['method','time (s)','func']).sort_values('time (s)')
    df['time per iter (micro sec)'] = df['time (s)'] / size * 1e6
    display(df)
    return df

def run_methods_w_funcs(methods, data, funcs, size):
    results = []
    for method in methods:
        for f in funcs:
            results.append(method(data.copy(),f) + (f.__name__,))
    df = display_results_func(results,size)
    return results

### Methods to avoid ###

# Numpy Append
@timeit
def numpy_append(size,row):
    test = np.empty((1,5))
    for i in range(size):
        test = np.append(test, row)
    return test

# Pandas Concat each row to initalized df
@timeit
def pandas_concat_to_existing(size, row):
    test = pd.DataFrame([dict(zip(row,row))])
    for i in range(1,size):
        df_row = pd.DataFrame([row], columns=row)
        test = pd.concat([test, df_row])
    return test

### Reasonably fast methods ###

# List Append
@timeit
def list_append(size,row):
    test = []
    for i in range(size):
        test.append(row)
    return test

# List Comprehension
@timeit
def list_comp(size,row):
    test = [row for i in range(size)]
    return test

# Numpy Pre-allocated
@timeit
def numpy_preallocated(size,row):
    test = np.empty((size,5))
    for i in range(size):
        test[i] = row
    return test

# Numpy Array 
@timeit
def numpy_repeat(size,row):
    test = np.repeat(row, size).reshape(size,5)
    return test

# Pandas from list comp
@timeit
def pandas_from_list_comp(size,row):
    data = [row for i in range(size)]
    test = pd.DataFrame(data, columns=row)
    return test

# Pandas from list comp to numpy to pandas
@timeit
def pandas_from_list_comp_to_array(size,row):
    data = [row for i in range(size)]
    test = pd.DataFrame(np.array(data), columns=row)
    return test

# %%

### Compare methods ###

size_avoid = 10000
methods_avoid = [numpy_append,pandas_concat_to_existing]
size = 1000000
methods_reasonable = [list_append, list_comp, numpy_preallocated, numpy_repeat, pandas_from_list_comp, pandas_from_list_comp_to_array]

row = [1.0,2,3,4,5]
print("### Numeric Datatypes ###")
run_methods(methods_avoid, size=size_avoid, row=row)
run_methods(methods_reasonable, size=size, row=row)

row = [1,2,'3',4.0,5]
print("### Mixed Datatypes ###")
run_methods(methods_avoid, size=size_avoid, row=row)
run_methods(methods_reasonable, size=size, row=row)

# Conclusions on data initialization
# - Avoid numpy append and pandas concat in a loop
# - List comprehension is faster than list append, but not significantly
# - Using numpy with loops is slower than built-in python lists
# - When working with numeric data, numpy is faster than lists if loops are avoided. Espcially if vectorization is used
# - Pandas is the slowest, but is easier to work with
# - For mixed data types, use lists, for numeric data, use numpy

# %%

# Functions to apply
def join_row_to_str(row):
    return ''.join(map(str, row))

def sum_row_as_numeric(row):
    res = 0
    for i in row:
        res += float(i)
    return res
def simple_assign(row):
    return 12345

@timeit
def list_loop(data, f):
    vals = [f(row_i) for row_i in data]
    new_data = list(zip(data, vals))
    # return new_data

@timeit
def df_apply(df,f):
    vals = df.apply(f, axis=1)
    df['vals'] = vals
    # print(df)
    # return df

@timeit
def df_iterrows(df,f): 
    vals = []
    for index, row in df.iterrows():
        vals.append(f(row))
    df['vals'] = vals
    # print(df)


# %%
### Comparing data manipulation ###
size_compare = 100000

df_methods = [df_apply, df_iterrows]
list_methods = [list_loop]
funcs = [join_row_to_str, sum_row_as_numeric, simple_assign]

print("### Numeric Datatypes ###")
row = [1,2,3,4.0,5]
data = [row for i in range(size_compare)]
df = pd.DataFrame(data, columns=row)
run_methods_w_funcs(df_methods, df, funcs, size_compare)
run_methods_w_funcs(list_methods, data, funcs, size_compare)

print("### Mixed Datatypes ###")
row = [1,2,'3',4.0,5]
data = [row for i in range(size_compare)]
df = pd.DataFrame(data, columns=row)
run_methods_w_funcs(df_methods, df, funcs, size_compare)
run_methods_w_funcs(list_methods, data, funcs, size_compare)


# Conclusions on data manipulation with loops
# - Avoid iterating over rows in a dataframe
# - df.apply() is slower than a list comprehension by approximately 5-20x
# %%

# Utilizing df vectorization
@timeit
def df_assign(df):
    df['vals'] = 12345

@timeit
def df_add_cols_as_str(df):
    df["vals"] = df.astype(str).sum(axis=1)

@timeit
def df_add_cols_as_float(df):
    df["vals"] = df.astype(float).sum(axis=1)

def run_methods_w_df(methods, df):
    results = []
    for method in methods:
        results.append(method(df.copy()))
    _ = display_results(results, size)
    return results

row = [1,2,'3',4.0,5]
data = [row for i in range(size_compare)]
df = pd.DataFrame(data, columns=row)

df_vec_methods = [df_assign, df_add_cols_as_str, df_add_cols_as_float]

run_methods_w_df(df_vec_methods, df)

# Conclusions
# - If vectorization is possible, it is much faster than looping, even faster than list comprehension by 10x-1000x


# %%
# Final Conclusions:
# Use numpy for numeric data, lists for mixed data
# Pandas is slower to initialize, but easier to work with, and has speed advantages if vectorization is possible

# %%
# from math import radians, cos, sin, asin, sqrt
from numpy import radians, cos, sin, arcsin, sqrt
from numba import jit

# @jit(nopython=True)
def haversine(lat1,lon1,lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """

    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * arcsin(sqrt(a)) 

    # 6367 km is the radius of the Earth
    km = 6367 * c
    return km

def haversine_vectorized(lat1,lon1,lat2, lon2):
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = radians(lon1), radians(lat1), radians(lon2), radians(lat2)
 
    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * arcsin(sqrt(a)) 

    # 6367 km is the radius of the Earth
    km = 6367 * c

    return km

@timeit
def apply_haversine(df):
    df['haversine'] = df.apply(lambda x: haversine(*x), axis=1)
    # print(df)
    return df


@timeit
def apply_haversine_vectorized(df):
    df['haversine'] = df.apply(lambda x: haversine_vectorized(*x), axis=1)
    # print(df)
    return df

@timeit
def list_haversine(data):
    vals = [haversine(*row) for row in data]
    new_data = list(zip(data, vals))
    return new_data

@timeit
def add_haversine_w_vec(df):
    df['haversine'] = haversine_vectorized(df['lat1'],df['lon1'],df['lat2'],df['lon2'])
    return df

@timeit
def add_haversine_w_vec_numba(lat1,lon1,lat2, lon2):
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = radians(lon1), radians(lat1), radians(lon2), radians(lat2)

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * arcsin(sqrt(a)) 

    # 6367 km is the radius of the Earth
    km = 6367 * c

    return km

# Generate df
d = {
    'lat1': {0: '31.215379379000467',
    1: '34.22133455500045',
    2: '34.795039606000444',
    3: '31.292159523000464',
    4: '31.69311635000048',
    5: '33.595265517000485',
    6: '34.44060759100046',
    7: '33.254429322000476',
    8: '33.50314015000049',
    9: '34.74643089500046'},
    'lon1': {0: ' -85.36146587999968',
    1: ' -86.15937514799964',
    2: ' -87.68507485299966',
    3: ' -86.25539902199966',
    4: ' -86.26549483099967',
    5: ' -86.66531866799966',
    6: ' -85.75726760699968',
    7: ' -86.81407933399964',
    8: ' -86.80242858299965',
    9: ' -87.69893502799965'}
    }
df = pd.DataFrame(d).astype(float)
df = pd.concat([df]*50000,ignore_index=True)
np.random.seed(123)
rand_dlat = np.random.randint(5, 35, size=len(df))
df['lat2'] = df['lat1']+rand_dlat
rand_dlon = np.random.randint(20, 50, size=len(df))
df['lon2'] = df['lon1']+rand_dlon
data = df.values

print("### Comparing apply, list and vectorization ###")
results = [apply_haversine(df.copy()), apply_haversine_vectorized(df.copy()),list_haversine(data.copy()),add_haversine_w_vec(df.copy())]
display_results(results, size=len(df))

from numba import jit

@jit(nopython=True)
def haversine(lat1,lon1,lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """

    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * arcsin(sqrt(a)) 

    # 6367 km is the radius of the Earth
    km = 6367 * c
    return km

print("### With Numba ###")
results = [apply_haversine(df.copy()), apply_haversine_vectorized(df.copy()),list_haversine(data.copy()),add_haversine_w_vec(df.copy())]
display_results(results, size=len(df));


# Conclusions
# - if functions can be vectorized with numpy it is much faster than apply by 100x-200x
# - Using a list comprehension is slightly faster than apply, but not significantly
# - Numba does make non-vecorized functions faster, in this case 2-5x
# - Numba makes vecorized functions much slower, in fact it is an order of magnitude slower (not shown here)
# - Try to write code that can easily be vectorized, if not try numba if speed is important.

# %%
