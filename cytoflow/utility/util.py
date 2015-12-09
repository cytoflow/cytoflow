"""
Created on Mar 5, 2015

@author: brian
"""
from __future__ import division

import numpy as np
from scipy import stats

class CytoflowError(RuntimeError):
    pass

class CytoflowOpError(CytoflowError):
    pass

class CytoflowViewError(CytoflowError):
    pass

def iqr(a):
    """Calculate the IQR for an array of numbers."""
    a = np.asarray(a)
    q1 = stats.scoreatpercentile(a, 25)
    q3 = stats.scoreatpercentile(a, 75)
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
        return np.ceil((a.max() - a.min()) / h)
    
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

    m = n / arrays[0].size
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
