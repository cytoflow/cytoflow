'''
Created on Jan 4, 2018

@author: brian
'''
import unittest

import matplotlib
matplotlib.use('Agg')

from cytoflowgui.tests.test_base import ImportedDataTest, wait_for

class Test(ImportedDataTest):

    def testCoarse(self):
        wi = self.workflow.workflow[0]
        op = wi.operation
        
        old_apply_calls = self.workflow.apply_calls

        op.coarse = True
        op.coarse_events = 1000
        self.assertTrue(wait_for(wi, 'status', lambda v: v == 'valid', 5))
        self.assertTrue(self.workflow.apply_calls > old_apply_calls)
        self.assertEqual(self.workflow.remote_eval('len(self.workflow[0].result)'), 4000)
        self.assertEqual(op.ret_events, 4000)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()