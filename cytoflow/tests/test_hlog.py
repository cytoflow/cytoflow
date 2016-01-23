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

'''
Created on Nov 26, 2015

@author: brian
'''
import unittest
import os

import numpy as np
from numpy.testing import assert_almost_equal

import cytoflow as flow
from cytoflow.operations.hlog import hlog

class Test(unittest.TestCase):


    def setUp(self):
        self.cwd = os.path.dirname(os.path.abspath(__file__))
        self.ex = flow.ImportOp(conditions = {},
                                tubes = [flow.Tube(file = self.cwd + '/data/tasbe/mkate.fcs',
                                                   conditions = {})]).apply()
        
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