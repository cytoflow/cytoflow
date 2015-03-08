"""
Created on Mar 5, 2015

@author: brian
"""

from traits.api import BaseFloat

class LogFloat(BaseFloat):
    """A trait to represent a numeric condition on a log scale.
    
    We may not noeed this.
    """
    
    #pass  # don't need to actually override anything