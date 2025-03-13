#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2022
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
cytoflowgui.workflow.workflow_item
----------------------------------

Represents one step in an analysis pipeline.  Wraps a single 
`IOperation` and any `IView` of its result.  
"""

import sys, logging, warnings, threading

import pandas as pd
import matplotlib.pyplot as plt

from traits.api import (HasStrictTraits, Instance, Str, Enum, Any, Dict, 
                        Tuple, List, DelegatesTo, ComparisonMode, Property,
                        observe, cached_property)

from cytoflow import Experiment
from cytoflow.utility import CytoflowError, CytoflowOpError, CytoflowViewError

from .serialization import camel_registry

# http://stackoverflow.com/questions/1977362/how-to-create-module-wide-variables-in-python
this = sys.modules[__name__]
this.last_view_plotted = None

logger = logging.getLogger(__name__)

class WorkflowItem(HasStrictTraits):
    """        
    The basic unit of a Workflow: wraps an operation and a list of views.  
    This class is serialized and synchronized between the `LocalWorkflow` and the
    `RemoteWorkflow`.
    
    Notes
    -----
    Because we serialize instances of this, we have to pay careful attention
    to which traits are ``transient`` (and aren't serialized). Additionally,
    traits marked as ``status`` are only serialized remote --> local.  For more
    details about the synchronization, see the module docstring for `cytoflowgui.workflow`
    """
    
    friendly_id = DelegatesTo('operation')
    """The operation's id"""
    
    name = DelegatesTo('operation')
    """The operation's name"""
    
    operation = Instance('cytoflowgui.workflow.operations.IWorkflowOperation', copy = "ref")
    """The operation that this `WorkflowItem` wraps"""
    
    # the IViews associated with this operation
    views = List(Instance('cytoflowgui.workflow.views.IWorkflowView'), 
                 copy = "ref", 
                 comparison_mode = ComparisonMode.identity)
    """The `IView`\'s associated with this operation"""
    
    current_view = Instance('cytoflowgui.workflow.views.IWorkflowView', copy = "ref")
    """The currently selected view"""
        
    result = Instance(Experiment, transient = True)
    """The `Experiment` that is the result of applying `operation` to the
       `previous_wi`'s `result`"""
    
    # the channels, conditions and statistics from result.  usually these would be
    # Properties (ie, determined dynamically), but that's hard with the
    # multiprocess model.
    
    channels = List(Str, status = True)
    """The channels from `result`"""
    
    conditions = Dict(Str, pd.Series, status = True)
    """The conditions from `result`"""
    
    metadata = Dict(Str, Any, status = True)
    """The metadata from `result`"""
    
    statistics = Dict(Tuple(Str, Str), pd.Series, status = True)
    """The statistics from `result`"""
    
    default_view = Property(Instance('cytoflowgui.workflow.views.IWorkflowView'), observe = 'operation')
    """The default view for this workflow item (if any)"""
    
    previous_wi = Instance('WorkflowItem', transient = True)
    """The previous `WorkflowItem` in the workflow"""
    
    next_wi = Instance('WorkflowItem', transient = True)
    """The next `WorkflowItem` in the workflow"""
    
    # the workflow that we're a part of.  need to make klass = HasStrictTraits because
    # we could be an instance of either LocalWorkflow or RemoteWorkflow
    workflow = Instance(HasStrictTraits, transient = True)
    """
    The `LocalWorkflow` or `RemoteWorkflow` that this `WorkflowItem` is a part of
    """
    
    # MAGIC: first value is the default
    status = Enum("invalid", "waiting", "estimating", "applying", "valid", "loading", status = True)
    """This `WorkflowItem`'s status"""
    
    # report the errors and warnings
    op_error = Str(status = True)
    """Errors from `operation`'s `IOperation.apply` method"""
    
    op_error_trait = Str(status = True)
    """The trait that caused the error in `op_error`"""

    op_warning = Str(status = True)
    """Warnings from `operation`'s `IOperation.apply` method"""
    
    op_warning_trait = Str(status = True)  
    """The trait that caused the warning in `op_warning`"""
      
    estimate_error = Str(status = True)
    """Errors from `operation`'s `IOperation.estimate` method"""
    
    estimate_warning = Str(status = True)
    """Warnings from `operation`'s `IOperation.estimate` method"""

    view_error = Str(status = True)
    """Errors from the most recently plotted view's `IView.plot` method"""
    
    view_error_trait = Str(status = True)
    """The trait that caused the error in `view_error`"""
    
    view_warning = Str(status = True)
    """Warnings from the most recently plotted view's `IView.plot` method"""
    
    view_warning_trait = Str(status = True)
    """The trait that caused the warning in `view_warning`"""
    
    plot_names = List(Any, status = True)
    """
    The possible values for the **plot_name** parameter of `current_view`'s
    `IView.plot` method. Retrieved from that view's **enum_plots()** method and
    updated automatically when `result` or `current_view` changes.
    """
    
    plot_names_label = Str(status = True)
    """
    The GUI label for the element that allows users to select a plot name from
    `plot_names`.  Updated automatically when `result` or `current_view` changes.
    """
    
    # synchronization primitives for plotting
    matplotlib_events = Any(transient = True)
    """`threading.Event` to synchronize matplotlib plotting across process boundaries"""
    
    plot_lock = Any(transient = True)
    """`threading.Lock` to synchronize matplotlib plotting across process boundaries"""
    
    lock = Instance(threading.RLock, (), transient = True)
    """`threading.Lock` for updating this `WorkflowItem`'s traits"""

    
    def edit_traits(self, view = None, parent = None, kind = None, 
                        context = None, handler = None, id = "",  # @ReservedAssignment
                        scrollable=None, **args):
        """
        Override the base `traits.has_traits.HasTraits.edit_traits` to make it go looking for views
        in the handler.
        """
         
        if context is None:
            context = self
 
        view = self.trait_view(view, handler = handler)
 
        return view.ui(context, parent, kind, self.trait_view_elements(),
                       handler, id, scrollable, args)
         
    def trait_view(self, name = None, view_element = None, handler = None):
        return self.__class__._trait_view(
            name,
            view_element,
            self.default_traits_view,
            self.trait_view_elements,
            self.visible_traits,
            handler if handler else self)
    
    def __str__(self):
        return "<{}: {}>".format(self.__class__.__name__, self.operation.__class__.__name__)
    

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self.operation.__class__.__name__)
    
    
    # property: default_view
    @cached_property
    def _get_default_view(self):
        try:
            return self.operation.default_view()
        except AttributeError:
            return None
        
        
    @observe('[result,current_view.+type]')
    def _update_plot_names(self, _):
        if self.current_view is None:
            return 
        
        if self.result:
            experiment = self.result
        elif self.previous_wi and self.previous_wi.result:
            experiment = self.previous_wi.result
        else:
            return None
        
        plot_iter = self.current_view.enum_plots(experiment)
        plot_names = [x for x in plot_iter]
        
        if plot_names == self.plot_names:
            return
        
        if plot_names == [None] or plot_names == []:
            self.plot_names = []
            self.plot_names_label = ""
        else:
            self.plot_names = plot_names
            try:
                self.plot_names_label = ", ".join(plot_iter.by)
            except AttributeError:
                self.plot_names_label = ""
        
        
    def estimate(self):
        """Call `operation`'s `IOperation.estimate`"""
        
        logger.debug("WorkflowItem.estimate :: {}".format((self)))

        prev_result = self.previous_wi.result if self.previous_wi else None
                 
        with warnings.catch_warnings(record = True) as w:
            try:    
                self.status = "estimating"
                
                try:
                    plt.gcf().canvas.set_working(True)
                except AttributeError:
                    pass

                self.operation.estimate(prev_result)

                self.estimate_error = ""
                if w:
                    self.estimate_warning = w[-1].message.__str__()
                else:
                    self.estimate_warning = ""
                
                return True

            except CytoflowOpError as e:                
                if e.args[0]:
                    self.op_error_trait = e.args[0]
                self.estimate_error = e.args[-1]    
                self.status = "invalid"
                return False
                
            except CytoflowError as e:
                self.estimate_error = e.__str__()    
                self.status = "invalid"
                return False 
            
            finally:
                try:
                    plt.gcf().canvas.set_working(False)
                except AttributeError:
                    pass
            
            
    def apply(self):
        """
        Calls `operation`'s `IOperation.apply`; applies this `WorkflowItem`'s 
        operation to `previous_wi`'s result
        """
        logger.debug("WorkflowItem.apply :: {}".format((self)))
        self.workflow.apply_calls += 1
         
        prev_result = self.previous_wi.result if self.previous_wi else None
         
        with warnings.catch_warnings(record = True) as w:
            try:    
                self.status = "applying"
                
                try:
                    plt.gcf().canvas.set_working(True)
                except AttributeError:
                    pass
                
                r = self.operation.apply(prev_result)
                self.result = r

                self.op_error = ""
                self.op_error_trait = ""
                if w:
                    self.op_warning = w[-1].message.__str__()
                else:
                    self.op_warning = ""
                    self.op_warning_trait = ""
                    
                self.status = "valid"
            
            except CytoflowOpError as e:                
                self.result = None
                if e.args[0]:
                    self.op_error_trait = e.args[0]
                self.op_error = e.args[-1]    
                self.status = "invalid"
                
            except CytoflowError as e:
                self.result = None
                self.op_error = e.args[-1]    
                self.status = "invalid"
            
            finally:
                try:
                    plt.gcf().canvas.set_working(False)
                except AttributeError:
                    pass

        
    def plot(self):   
        """
        Call `current_view`'s `IView.plot` on `result`, or on `previous_wi`'s `result`
        if there's no current `result`.
        """
                   
        logger.debug("WorkflowItem.plot :: {}".format((self)))
        self.workflow.plot_calls += 1
                     
        if not self.current_view:
            self.plot_lock.acquire()                
            self.matplotlib_events.clear()
            plt.clf()
            plt.show()
            self.matplotlib_events.set() 
            self.plot_lock.release()
            return
          
        with warnings.catch_warnings(record = True) as w:
            try:
                self.plot_lock.acquire()                
                self.matplotlib_events.clear()
                
                try:
                    plt.gcf().canvas.set_working(True)
                except AttributeError:
                    pass
                
                if this.last_view_plotted is not None and "interactive" in this.last_view_plotted.traits():
                    this.last_view_plotted.interactive = False
                
                plot_params = self.current_view.plot_params.trait_get()
                
                if self.result:
                    self.current_view.plot(self.result, **plot_params)
                elif self.previous_wi and self.previous_wi.result:
                    self.current_view.plot(self.previous_wi.result, **plot_params)
                    warnings.warn("Warning: plotting previous operation's result")
                else:
                    raise CytoflowViewError(None, "Nothing to plot!")
                    
                self.view_error = ""
                self.view_error_trait = ""
                 
                if "interactive" in self.current_view.traits():
                    self.current_view.interactive = True
                   
                this.last_view_plotted = self.current_view
                  
                # the remote canvas/pyplot interface of the multiprocess backend
                # is NOT interactive.  this call lets us batch together all 
                # the plot updates
                plt.show()
                
            except CytoflowViewError as e:                
                if e.args[0]:
                    self.view_error_trait = e.args[0]
                self.view_error = e.args[-1]    
                plt.clf()
                plt.show()
                                     
            except CytoflowError as e:
                self.view_error = e.__str__()   
                plt.clf()
                plt.show() 
            finally:
                self.matplotlib_events.set()
                try:
                    plt.gcf().canvas.set_working(False)
                except AttributeError:
                    pass
                 
                self.plot_lock.release()

                if w:
                    self.view_warning = w[-1].message.__str__()
                else:
                    self.view_warning = ""
                    
            return True
        
@camel_registry.dumper(WorkflowItem, 'workflow-item', version = 4)
def _dump_wi(wi):
                          
    # we really don't need to keep copying around the fcs metadata
    # it will still get saved out in the import op
    if 'fcs_metadata' in wi.metadata:
        del wi.metadata['fcs_metadata']
                            
    return dict(operation = wi.operation,
                views = wi.views,
                channels = wi.channels,
                conditions = wi.conditions,
                metadata = wi.metadata,
                statistics = wi.statistics,
                current_view = wi.current_view)
        
@camel_registry.dumper(WorkflowItem, 'workflow-item', version = 3)
def _dump_wi_v3(wi):
                          
    # we really don't need to keep copying around the fcs metadata
    # it will still get saved out in the import op
    if 'fcs_metadata' in wi.metadata:
        del wi.metadata['fcs_metadata']
                            
    return dict(operation = wi.operation,
                views = wi.views,
                channels = wi.channels,
                conditions = wi.conditions,
                metadata = wi.metadata,
                statistics = wi.statistics,
                current_view = wi.current_view,
                default_view = wi.default_view)
    
@camel_registry.dumper(WorkflowItem, 'workflow-item', version = 2)
def _dump_wi_v2(wi):
                          
    # we really don't need to keep copying around the fcs metadata
    # it will still get saved out in the import op
    if 'fcs_metadata' in wi.metadata:
        del wi.metadata['fcs_metadata']
                            
    return dict(deletable = wi.deletable,
                operation = wi.operation,
                views = wi.views,
                channels = wi.channels,
                conditions = wi.conditions,
                metadata = wi.metadata,
                statistics = wi.statistics,
                current_view = wi.current_view,
                default_view = wi.default_view)
    
@camel_registry.dumper(WorkflowItem, 'workflow-item', version = 1)
def _dump_wi_v1(wi):
                            
    return dict(deletable = False if wi.operation.id == "edu.mit.synbio.cytoflow.operations.import" else True,
                operation = wi.operation,
                views = wi.views,
                channels = wi.channels,
                conditions = wi.conditions,
                metadata = wi.metadata,
                statistics = list(wi.statistics.keys()),
                current_view = wi.current_view,
                default_view = wi.default_view)


@camel_registry.loader('workflow-item', version = 1)
def _load_wi_v1(data, version):
    
    data['statistics'] = {tuple(k) : pd.Series() for k in data['statistics']}
    del data['deletable']
    del data['default_view']
    ret = WorkflowItem(**data)
        
    return ret

@camel_registry.loader('workflow-item', version = 2)
def _load_wi_v2(data, version):
    del data['deletable']
    del data['default_view']
    return WorkflowItem(**data)

@camel_registry.loader('workflow-item', version = 3)
def _load_wi_v3(data, version):
    del data['default_view']
    return WorkflowItem(**data)

@camel_registry.loader('workflow-item', version = 4)
def _load_wi(data, version):
    return WorkflowItem(**data)

