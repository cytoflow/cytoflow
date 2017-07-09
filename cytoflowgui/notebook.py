#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2017
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
Created on May 17, 2015

@author: brian
'''

import os
from base64 import encodestring
import nbformat as nb

from traits.api import HasTraits, Str

class JupyterNotebookWriter(HasTraits):
    
    """
    see https://github.com/jupyter/nbformat/blob/master/nbformat/v4/tests/nbexamples.py
    for examples of writing notebook cells
    
    design: 
     - add a writer function generator to the op and view plugins
     - dynamically associate with the returned op and view instances
     - iterate over the workflow:
         - Include name and id in markdown cells
         - for each workflow item, make one cell with the operation's
           execution
         - for each view in the workflow item, make one cell with the
           view's parameterization, execution and output
    """
    
    file = Str
    
    def export(self, workflow):
        pass
