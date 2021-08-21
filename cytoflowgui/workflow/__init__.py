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

"""
cytoflowgui.workflow
--------------------

"""   
 
class Changed(object):
    # the operation's parameters needed to apply() changed.  
    # payload:
    # - the name of the changed trait
    # - the new trait value
    APPLY = "APPLY"
     
    # the operation's parameters to estimate() changed   
    # payload:
    # - the name of the changed trait
    # - the new trait value
    ESTIMATE = "ESTIMATE"    
     
    # the current view's parameters have changed
    # payload:
    # - the IView object that changed
    # - the name of the changed trait
    # - the new trait value 
    VIEW = "VIEW"         
     
    # the result of calling estimate() changed
    # payload: unused
    ESTIMATE_RESULT = "ESTIMATE_RESULT"  
     
    # some operation status info changed
    # payload:
    # - the name of the changed trait
    # - the new trait value
    OP_STATUS = "OP_STATUS"     
     
    # some view status changed
    # payload:
    # - the IView object that changed
    # - the name of the changed trait
    # - the new trait value
    # FIXME this is really only for exporting a table view -- 
    #       but we have the statistics locally too!  so just export from there.
    # VIEW_STATUS = "VIEW_STATUS" 
     
    # the result of calling apply() changed
    # payload: unused
    RESULT = "RESULT"        
     
    # the previous WorkflowItem's result changed
    # payload: unused
    PREV_RESULT = "PREV_RESULT"  


from .workflow import LocalWorkflow, RemoteWorkflow
from .workflow_item import WorkflowItem
