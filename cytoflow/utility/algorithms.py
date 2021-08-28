#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2021
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
cytoflow.utility.algorithms
---------------------------

Useful algorithms.

`ci` -- determine a confidence interval by boostrapping.

`percentiles` -- find percentiles in an array.

`bootstrap` -- resample (with replacement) and store aggregate values.
"""

import numpy as np
from scipy import stats

def ci(data, func, which=95, boots=1000):
    """
    Determine the confidence interval of a function applied to a data set by
    bootstrapping.
    
    Parameters
    ----------
    data : pandas.DataFrame
        The data to resample.
        
    func : callable
        A function that is called on a resampled ``data``
        
    which : int
        The percentile to use for the confidence interval
        
    boots : int (default = 1000):
        How many times to bootstrap
        
    Returns
    -------
    (float, float)
        The confidence interval.
        
    """
    boots = bootstrap(data, func = func, n_boot = boots)
    p = 50 - which / 2, 50 + which / 2
    return tuple(percentiles(boots, p))
    
def percentiles(a, pcts, axis=None):
    """
    Like `scipy.stats.scoreatpercentile` but can take and return array of percentiles.

    from seaborn: https://github.com/mwaskom/seaborn/blob/master/seaborn/utils.py
    
    Parameters
    ----------
    a : array
        data
        
    pcts : sequence of percentile values
        percentile or percentiles to find score at
        
    axis : int or None
        if not None, computes scores over this axis
        
    Returns
    -------
    scores: array
        array of scores at requested percentiles
        first dimension is length of object passed to ``pcts``
        
    """
    scores = []
    try:
        n = len(pcts)
    except TypeError:
        pcts = [pcts]
        n = 0
    for p in pcts:
        if axis is None:
            score = stats.scoreatpercentile(a.ravel(), p)
        else:
            score = np.apply_along_axis(stats.scoreatpercentile, axis, a, p)
        scores.append(score)
    scores = np.asarray(scores)
    if not n:
        scores = scores.squeeze()
    return scores

def bootstrap(*args, **kwargs):
    """
    Resample one or more arrays with replacement and store aggregate values.
    Positional arguments are a sequence of arrays to bootstrap along the first
    axis and pass to a summary function.
    
    
    Parameters
    ----------
    n_boot : int, default 10000
        Number of iterations

    axis : int, default None
        Will pass axis to ``func`` as a keyword argument.

    units : array, default None
        Array of sampling unit IDs. When used the bootstrap resamples units
        and then observations within units instead of individual
        datapoints.

    smooth : bool, default False
        If True, performs a smoothed bootstrap (draws samples from a kernel
        destiny estimate); only works for one-dimensional inputs and cannot
        be used `units` is present.

    func : callable, default np.mean
        Function to call on the args that are passed in.

    random_seed : int | None, default None
        Seed for the random number generator; useful if you want
        reproducible resamples.
            
    Returns
    -------
    array
        array of bootstrapped statistic values
        
    from seaborn: https://github.com/mwaskom/seaborn/blob/master/seaborn/algorithms.py
    """
    # Ensure list of arrays are same length
    if len(np.unique(list(map(len, args)))) > 1:
        raise ValueError("All input arrays must have the same length")
    n = len(args[0])

    # Default keyword arguments
    n_boot = kwargs.get("n_boot", 10000)
    func = kwargs.get("func", np.mean)
    axis = kwargs.get("axis", None)
    units = kwargs.get("units", None)
    smooth = kwargs.get("smooth", False)
    random_seed = kwargs.get("random_seed", None)
    if axis is None:
        func_kwargs = dict()
    else:
        func_kwargs = dict(axis=axis)

    # Initialize the resampler
    rs = np.random.RandomState(random_seed)

    # Coerce to arrays
    args = list(map(np.asarray, args))
    if units is not None:
        units = np.asarray(units)

    # Do the bootstrap
    if smooth:
        return _smooth_bootstrap(args, n_boot, func, func_kwargs)

    if units is not None:
        return _structured_bootstrap(args, n_boot, units, func,
                                     func_kwargs, rs)

    boot_dist = []
    for i in range(int(n_boot)):
        resampler = rs.randint(0, n, n)
        sample = [a.take(resampler, axis=0) for a in args]
        boot_dist.append(func(*sample, **func_kwargs))
    return np.array(boot_dist)


def _structured_bootstrap(args, n_boot, units, func, func_kwargs, rs):
    """Resample units instead of datapoints."""
    unique_units = np.unique(units)
    n_units = len(unique_units)

    args = [[a[units == unit] for unit in unique_units] for a in args]

    boot_dist = []
    for i in range(int(n_boot)):
        resampler = rs.randint(0, n_units, n_units)
        sample = [np.take(a, resampler, axis=0) for a in args]
        lengths = list(map(len, sample[0]))
        resampler = [rs.randint(0, n, n) for n in lengths]
        sample = [[c.take(r, axis=0) for c, r in zip(a, resampler)]
                  for a in sample]
        sample = list(map(np.concatenate, sample))
        boot_dist.append(func(*sample, **func_kwargs))
    return np.array(boot_dist)


def _smooth_bootstrap(args, n_boot, func, func_kwargs):
    """Bootstrap by resampling from a kernel density estimate."""
    n = len(args[0])
    boot_dist = []
    kde = [stats.gaussian_kde(np.transpose(a)) for a in args]
    for i in range(int(n_boot)):
        sample = [a.resample(n).T for a in kde]
        boot_dist.append(func(*sample, **func_kwargs))
    return np.array(boot_dist)