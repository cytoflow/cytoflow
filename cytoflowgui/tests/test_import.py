#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2021
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
Created on Jan 4, 2018

@author: brian
'''
import unittest, tempfile, os
import pandas as pd

from cytoflowgui.tests.test_base import ImportedDataTest, TasbeTest
from cytoflowgui.workflow.serialization import save_yaml, load_yaml
from cytoflowgui.workflow.operations import ImportWorkflowOp, ImportChannel


class TestImport(ImportedDataTest):
    
    def setUp(self):
        super().setUp()
        
        self.wi = self.workflow.workflow[0]
        self.op = self.wi.operation

    def testCoarse(self):
        
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.events = 1000
        self.workflow.wi_waitfor(self.wi, 'status', 'invalid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[0].result is None"))

        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.do_estimate = True
        self.workflow.wi_waitfor(self.wi, 'status', 'valid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[0].result is not None"))
        self.assertTrue(self.workflow.remote_eval('len(self.workflow[0].result) == 6000'))
        self.assertEqual(self.op.ret_events, 6000)
         
    def testChannelRename(self):
         
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.channels_list = [ImportChannel(channel = 'SSC-A', name = 'SSC_A')]
        self.workflow.wi_waitfor(self.wi, 'status', 'invalid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[0].result is None"))

        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.do_estimate = True
        self.workflow.wi_waitfor(self.wi, 'status', 'valid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[0].result is not None"))
       
 
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
        new_op.ret_events = op.ret_events
        self.assertDictEqual(op.trait_get(op.copyable_trait_names()),
                             new_op.trait_get(op.copyable_trait_names()))
          
    def testSerializeV1(self):
        wi = self.workflow.workflow[0]
        op = wi.operation
        fh, filename = tempfile.mkstemp()
        try:
            os.close(fh)
             
            save_yaml(op, filename, lock_versions = {ImportWorkflowOp : 1})
            new_op = load_yaml(filename)
             
        finally:
            os.unlink(filename)
             
        self.maxDiff = None
        new_op.ret_events = op.ret_events
        self.assertDictEqual(op.trait_get(op.copyable_trait_names()),
                             new_op.trait_get(op.copyable_trait_names()))
 
    def testSerializeV2(self):
        wi = self.workflow.workflow[0]
        op = wi.operation
        fh, filename = tempfile.mkstemp()
        try:
            os.close(fh)
             
            save_yaml(op, filename, lock_versions = {ImportWorkflowOp : 2})
            new_op = load_yaml(filename)
             
        finally:
            os.unlink(filename)
             
        self.maxDiff = None
        new_op.ret_events = op.ret_events
        self.assertDictEqual(op.trait_get(op.copyable_trait_names()),
                             new_op.trait_get(op.copyable_trait_names()))
         
    def testNotebook(self):
        code = "from cytoflow import *\n"
        for i, wi in enumerate(self.workflow.workflow):
            code = code + wi.operation.get_notebook_code(i)
         
        exec(code)
        nb_data = locals()['ex_0'].data
        remote_data = self.workflow.remote_eval("self.workflow[0].result.data")
        self.assertTrue((nb_data == remote_data).all().all())
         
class TestImportTasbe(TasbeTest):
    def testNotebook(self):
        code = "from cytoflow import *\n"
        for i, wi in enumerate(self.workflow.workflow):
            code = code + wi.operation.get_notebook_code(i)
         
        exec(code)
        nb_data = locals()['ex_0'].data
        remote_data = self.workflow.remote_eval("self.workflow[0].result.data")
        
        pd.testing.assert_frame_equal(nb_data, remote_data)


if __name__ == "__main__":
#     import sys;sys.argv = ['', 'TestImportTasbe.testNotebook']
    unittest.main()