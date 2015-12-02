'''
Created on Nov 26, 2015

@author: brian
'''
import unittest
from numpy.testing import assert_almost_equal
import os

import cytoflow as flow
from cytoflow.operations.hlog import hlog, hlog_inv
import numpy as np
import fcsparser

class Test(unittest.TestCase):


    def setUp(self):
        self.cwd = os.path.dirname(os.path.abspath(__file__))
        self.ex = flow.Experiment(metadata = {"name_meta" : "$PnN"})
        tube = fcsparser.parse(self.cwd + '/data/tasbe/mkate.fcs', 
                               reformat_meta = True,
                               channel_naming = "$PnN")
        self.ex.add_tube(tube, {})
        
        self.op = flow.HlogTransformOp(channels = ["FSC-A", "Pacific Blue-A"])

    def test_run(self):
        self.op.apply(self.ex)

    # stolen shamelessly from Eugene Yurtsev's FlowCytometryTools
    # http://gorelab.bitbucket.org/flowcytometrytools/
    # thanks, Eugene!
    
    def test_hlog_function(self):
        n = 1000
        _xmax = 2 ** 18  # max machine value
        _ymax = 10 ** 4  # max display value
        _xpos = np.logspace(-3, np.log10(_xmax), n)
        _xneg = -_xpos[::-1]
        _xall = np.r_[_xneg, _xpos]
        _ypos = np.logspace(-3, np.log10(_ymax), n)
        _yneg = -_ypos[::-1]
        _yall = np.r_[_yneg, _ypos]
        
        hlpos = hlog(_xpos)
        hlneg = hlog(_xneg)
        assert_almost_equal((hlpos[-1] - _ymax) / _ymax, 0, decimal=2)
        assert_almost_equal(hlpos, -hlneg[::-1])  # check symmetry
        # test that values get larger as b decreases
        hlpos10 = hlog(_xpos, b=10)
        self.assertTrue(np.all(hlpos10 >= hlpos))
        # check that converges to tlog for large values
        tlpos = tlog(_xpos)
        i = np.where(_xpos > 1e4)[0]
        tlpos_large = tlpos[i]
        hlpos_large = hlpos10[i]
        d = (hlpos_large - tlpos_large) / hlpos_large
        assert_almost_equal(d, np.zeros(len(d)), decimal=2)
        
        

_machine_max = 2**18
_l_mmax = np.log10(_machine_max)
_display_max = 10**4

# stolen shamelessly from Eugene Yurtsev's FlowCytometryTools
# http://gorelab.bitbucket.org/flowcytometrytools/
# thanks, Eugene!
def tlog(x, th=1, r=_display_max, d=_l_mmax):
    ''' Trucated log10 transform)'''
    
    if th <= 0:
        raise ValueError, 'Threshold value must be positive. %s given.' % th
    return np.where(x <= th, np.log10(th) * 1. * r / d, np.log10(x) * 1. * r / d)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test_hlog_function']
    unittest.main()