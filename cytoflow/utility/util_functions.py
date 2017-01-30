#!/usr/bin/env python2.7

# (c) Massachusetts Institute of Technology 2015-2016
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
Created on Mar 5, 2015

@author: brian
"""
from __future__ import division

import random, string

import numpy as np
import pandas as pd
from scipy import stats

def iqr(a):
    """Calculate the IQR for an array of numbers."""
    a = np.asarray(a)
    q1 = np.nanpercentile(a, 25)
    q3 = np.nanpercentile(a, 75)
    return q3 - q1

def num_hist_bins(a):
    """Calculate number of hist bins using Freedman-Diaconis rule."""
    # From http://stats.stackexchange.com/questions/798/
    a = np.asarray(a)
    h = 2 * iqr(a) / (len(a) ** (1 / 3))
      
    # fall back to 10 bins if iqr is 0
    if h == 0:
        return 10.
    else:
        return np.ceil((np.nanpercentile(a, 99) - 
                        np.nanpercentile(a, 1)) / h)
    
def geom_mean(a):
    """
    Compute the geometric mean for an "arbitrary" data set, ie one that
    contains zeros and negative numbers.
    
    Parameters
    ----------
    
    a : array-like
        A numpy.ndarray, or something that can be converted to an ndarray
        
    Returns
    -------
    The geometric mean of the input array
    
    Notes
    -----
    The traditional geometric mean can not be computed on a mixture of positive
    and negative numbers.  The approach here, validated rigorously in the
    cited paper[1], is to compute the geometric mean of the absolute value of
    the negative numbers separately, and then take a weighted arithmetic mean
    of that and the geometric mean of the positive numbers.  We're going to 
    discard 0 values, operating under the assumption that in this context
    there are going to be few or no observations with a value of exactly 0.
    
    References
    ----------
    [1] Geometric mean for negative and zero values
        Elsayed A. E. Habib
        International Journal of Research and Reviews in Applied Sciences
        11:419 (2012)
        http://www.arpapress.com/Volumes/Vol11Issue3/IJRRAS_11_3_08.pdf
        
        A new "Logicle" display method avoids deceptive effects of logarithmic 
        scaling for low signals and compensated data.
        Parks DR, Roederer M, Moore WA.
        Cytometry A. 2006 Jun;69(6):541-51.
        PMID: 16604519
        http://onlinelibrary.wiley.com/doi/10.1002/cyto.a.20258/full
    """
    
    a = np.array(a)
    pos = a[a > 0]
    pos_mean = stats.gmean(pos)
    pos_prop = pos.size / a.size
    
    neg = a[a < 0]
    neg = np.abs(neg)
    neg_mean = stats.gmean(neg) if neg.size > 0 else 0
    neg_prop = neg.size / a.size
    
    return (pos_mean * pos_prop) - (neg_mean * neg_prop)

def geom_sd(a):
    """
    Compute the geometric standard deviation for an "abitrary" data set, ie one
    that contains zeros and negative numbers.  Since we're in log space, this
    gives a *dimensionless scaling factor*, not a measure.  If you want 
    traditional "error bars", don't plot `[geom_mean - geom_sd, geom_mean + sd]`;
    rather, plot `[geom_mean / geom_sd, geom_mean * geom_sd]`.
    
    Parameters
    ----------
    
    a : array-like
        A numpy.ndarray, or something that can be converted to an ndarray
        
    Returns
    -------
    The geometric mean of the distribution.
    
    Notes
    -----
    As with `geom_mean`, non-positive numbers pose a problem.  The approach
    here, though less rigorously validated than the one above, is to replace
    negative numbers with their absolute value plus 2 * geometric mean, then
    go about our business as per the Wikipedia page for geometric sd[1].
    
    References
    ----------
    [1] https://en.wikipedia.org/wiki/Geometric_standard_deviation
    """
    
    a = np.array(a)
    u = geom_mean(a)
    a[a <= 0] = np.abs(a[a <= 0]) + 2 * u
    
    return np.exp(np.std(np.log(a)))
    
def geom_sd_range(a):
    """
    A convenience function to compute [geom_mean / geom_sd, geom_mean * geom_sd].
    
    Parameters
    ----------
    
    a : array-like
        A numpy.ndarray, or something that can be converted to an ndarray
        
    Returns
    -------
    A tuple, with `(geom_mean / geom_sd, geom_mean * geom_sd)`
    """
    
    u = geom_mean(a)
    sd = geom_sd(a)
    
    return (u / sd, u * sd)

def geom_sem(a):
    """
    Compute the geometric standard error of the mean for an "arbirary" data set,
    ie one that contains zeros and negative numbers.
    
    Parameters
    ----------
     Parameters
    ----------
    
    a : array-like
        A numpy.ndarray, or something that can be converted to an ndarray
        
    Returns
    -------
    The geometric mean of the distribution.
    
    Notes
    -----
    As with `geom_mean`, non-positive numbers pose a problem.  The approach
    here, though less rigorously validated than the one above, is to replace
    negative numbers with their absolute value plus 2 * geometric mean.  The
    geometric SEM is computed as in [1].
    
    References
    ----------
    [1] The Standard Errors of the Geometric and Harmonic Means and Their Application to Index Numbers
        Nilan Norris
        The Annals of Mathematical Statistics
        Vol. 11, No. 4 (Dec., 1940), pp. 445-448
    
        http://www.jstor.org/stable/2235723?seq=1#page_scan_tab_contents
    """
    
    a = np.array(a)
    u = geom_mean(a)
    a[a <= 0] = np.abs(a[a <= 0]) + 2 * u
    
    return u * np.std(np.log(a)) / np.sqrt(a.size)

    
def geom_sem_range(a):
    """
    A convenience function to compute [geom_mean / geom_sem, geom_mean * geom_sem].
    
    Parameters
    ----------
    
    a : array-like
        A numpy.ndarray, or something that can be converted to an ndarray
        
    Returns
    -------
    A tuple, with `(geom_mean / geom_sem, geom_mean * geom_sem)`
    """
    
    u = geom_mean(a)
    sem = geom_sem(a)
    
    return (u / sem, u * sem)

    
def cartesian(arrays, out=None):
    """
    Generate a cartesian product of input arrays.

    Parameters
    ----------
    arrays : list of array-like
        1-D arrays to form the cartesian product of.
    out : ndarray
        Array to place the cartesian product in.

    Returns
    -------
    out : ndarray
        2-D array of shape (M, len(arrays)) containing cartesian products
        formed of input arrays.

    Examples
    --------
    >>> cartesian(([1, 2, 3], [4, 5], [6, 7]))
    array([[1, 4, 6],
           [1, 4, 7],
           [1, 5, 6],
           [1, 5, 7],
           [2, 4, 6],
           [2, 4, 7],
           [2, 5, 6],
           [2, 5, 7],
           [3, 4, 6],
           [3, 4, 7],
           [3, 5, 6],
           [3, 5, 7]])
           
    References
    ----------
    Originally from http://stackoverflow.com/a/1235363/4755587
    """

    arrays = [np.asarray(x) for x in arrays]
    dtype = arrays[0].dtype

    n = np.prod([x.size for x in arrays])
    if out is None:
        out = np.zeros([n, len(arrays)], dtype=dtype)

    m = n // arrays[0].size
    out[:,0] = np.repeat(arrays[0], m)
    if arrays[1:]:
        cartesian(arrays[1:], out=out[0:m,1:])
        for j in xrange(1, arrays[0].size):
            out[j*m:(j+1)*m,1:] = out[0:m,1:]
    return out

def sanitize_identifier(name):
    """Makes name a Python identifier by replacing all nonsafe characters with '_'"""
    
    new_name = list(name)
    for i, c in enumerate(list(name)): # character by character
        if i == 0 and not (c.isalpha() or c == '_'):
            new_name[i] = '_'
        if i > 0 and not (c.isalnum() or c == '_'):
            new_name[i] = '_'

    return  "".join(new_name)

def categorical_order(values, order=None):
    """Return a list of unique data values.
    Determine an ordered list of levels in ``values``.
    
    Parameters
    ----------
    values : list, array, Categorical, or Series
        Vector of "categorical" values
    order : list-like, optional
        Desired order of category levels to override the order determined
        from the ``values`` object.
        
    Returns
    -------
    order : list
        Ordered list of category levels not including null values.
        
    From seaborn: https://github.com/mwaskom/seaborn/blob/master/seaborn/utils.py
    """
    if order is None:
        if hasattr(values, "categories"):
            order = values.categories
        else:
            try:
                order = values.cat.categories
            except (TypeError, AttributeError):
                try:
                    order = values.unique()
                except AttributeError:
                    order = pd.unique(values)
                try:
                    np.asarray(values).astype(np.float)
                    order = np.sort(order)
                except (ValueError, TypeError):
                    order = order
        order = filter(pd.notnull, order)
    return list(order)

def random_string(n):
    """from http://stackoverflow.com/questions/2257441/random-string-generation-with-upper-case-letters-and-digits-in-python"""
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))

def is_numeric(s):
    """
    s is a pandas.Series or a numpy.ndarray; try to determine if it's numeric
    from its dtype.
    """
    return s.dtype.kind in 'iufc'

#     return issubclass(s.dtype.type, np.number)