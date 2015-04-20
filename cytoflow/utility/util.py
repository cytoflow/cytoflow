"""
Created on Mar 5, 2015

@author: brian
"""
from __future__ import division

import numpy as np
from scipy import stats

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