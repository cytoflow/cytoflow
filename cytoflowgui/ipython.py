'''
Created on May 17, 2015

@author: brian
'''

import os
from base64 import encodestring
import IPython.nbformat as nb

from traits.api import HasTraits, Str

class IPythonNotebookWriter(HasTraits):
    
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