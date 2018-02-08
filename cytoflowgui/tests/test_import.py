'''
Created on Jan 4, 2018

@author: brian
'''
import unittest, tempfile, os

import matplotlib
matplotlib.use('Agg')

from cytoflowgui.tests.test_base import ImportedDataTest, wait_for
from cytoflowgui.serialization import save_yaml, load_yaml
from cytoflowgui.tests.deep_eq import deep_eq

class Test(ImportedDataTest):

    def testCoarse(self):
        wi = self.workflow.workflow[0]
        op = wi.operation
        
        op.coarse = True
        op.coarse_events = 1000
        self.assertTrue(wait_for(wi, 'status', lambda v: v != 'valid', 5))
        self.assertTrue(wait_for(wi, 'status', lambda v: v == 'valid', 5))
        self.assertTrue(self.workflow.remote_eval('len(self.workflow[0].result) == 4000'))
        self.assertEqual(op.ret_events, 4000)
        

    def testSerialize(self):
        wi = self.workflow.workflow[0]
        op = wi.operation
        fh, filename = tempfile.mkstemp()
        try:
            os.close(fh)
            
            save_yaml(op, filename)
            new_op = load_yaml(filename)
            
        finally:
            os.unlink(filename)
            
        self.maxDiff = None
        self.assertDictEqual(op.trait_get(op.copyable_trait_names()),
                             new_op.trait_get(op.copyable_trait_names()))
         
        
    def testNotebook(self):
        code = "from cytoflow import *\n"
        for i, wi in enumerate(self.workflow.workflow):
            code = code + wi.operation.get_notebook_code(i)
        
        exec(code)
        nb_data = locals()['ex_0'].data
        remote_data = self.workflow.remote_eval("self.workflow[-1].result.data")
        self.assertTrue((nb_data == remote_data).all().all())


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()