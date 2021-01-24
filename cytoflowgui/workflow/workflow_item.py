'''
Created on Jan 15, 2021

@author: brian
'''

import sys, logging, warnings, threading

import pandas as pd
import matplotlib.pyplot as plt

from traits.api import (HasStrictTraits, Instance, Str, Enum, Any, Dict, 
                        Tuple, List, DelegatesTo)

from cytoflow import Experiment
from cytoflow.utility import CytoflowError, CytoflowOpError, CytoflowViewError

from cytoflowgui.workflow.serialization import camel_registry
from cytoflowgui.workflow.views import IWorkflowView
from cytoflowgui.workflow.operations import IWorkflowOperation

# http://stackoverflow.com/questions/1977362/how-to-create-module-wide-variables-in-python
this = sys.modules[__name__]
this.last_view_plotted = None

logger = logging.getLogger(__name__)

class WorkflowItem(HasStrictTraits):
    """        
    The basic unit of a Workflow: wraps an operation and a list of views.
    
    Notes
    -----
    Because we serialize instances of this, we have to pay careful attention
    to which traits are ``transient`` (and aren't serialized)
    """
    
    # the operation's id
    friendly_id = DelegatesTo('operation')
    
    # the operation's name
    name = DelegatesTo('operation')
    
    # the operation this Item wraps
    operation = Instance(IWorkflowOperation, copy = "ref")
    
    # the IViews associated with this operation
    views = List(IWorkflowView, copy = "ref")
    
    # the currently selected view
    current_view = Instance(IWorkflowView, copy = "ref")
        
    # the Experiment that is the result of applying *operation* to the
    # previous_wi WorkflowItem's ``result``
    result = Instance(Experiment, transient = True)
    
    # the channels, conditions and statistics from result.  usually these would be
    # Properties (ie, determined dynamically), but that's hard with the
    # multiprocess model.
    
    channels = List(Str, status = True)
    conditions = Dict(Str, pd.Series, status = True)
    metadata = Dict(Str, Any, status = True)
    statistics = Dict(Tuple(Str, Str), pd.Series, status = True)
    
    # the default view for this workflow item
    default_view = Instance(IWorkflowView, copy = "ref")
    
    # the previous_wi WorkflowItem in the workflow
    previous_wi = Instance('WorkflowItem', transient = True)
    
    # the next_wi WorkflowItem in the workflow
    next_wi = Instance('WorkflowItem', transient = True)
    
    # the workflow that we're a part of.  need to make klass = HasStrictTraits because
    # we could be an instance of either LocalWorkflow or RemoteWorkflow
    workflow = Instance(HasStrictTraits, transient = True)
    
    # is the wi valid?
    # MAGIC: first value is the default
    status = Enum("invalid", "waiting", "estimating", "applying", "valid", "loading", status = True)
    
    # report the errors and warnings
    op_error = Str(status = True)
    op_error_trait = Str(status = True)
    op_warning = Str(status = True)
    op_warning_trait = Str(status = True)    
    estimate_error = Str(status = True)
    estimate_warning = Str(status = True)
    view_error = Str(status = True)
    view_error_trait = Str(status = True)
    view_warning = Str(status = True)
    view_warning_trait = Str(status = True)
    
    # synchronization primitives for plotting
    matplotlib_events = Any(transient = True)
    plot_lock = Any(transient = True)
    
    # synchronization primitive for updating wi traits
    lock = Instance(threading.RLock, (), transient = True)
    
    def __str__(self):
        return "<{}: {}>".format(self.__class__.__name__, self.operation.__class__.__name__)
    

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self.operation.__class__.__name__)
    
   
    def estimate(self):
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
        Apply this wi's operation to the previous_wi wi's result
        """
        logger.debug("WorkflowItem.apply :: {}".format((self)))
#         self.apply_called = True
         
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
        logger.debug("WorkflowItem.plot :: {}".format((self)))
        self.plot_called = True
                     
        if not self.current_view:
            self.plot_lock.acquire()                
            self.matplotlib_events.clear()
            plt.clf()
            plt.show()
            self.matplotlib_events.set() 
            self.plot_lock.release()
            return

        try:
            if len(self.current_view.plot_names) > 0 and self.current_view.current_plot not in self.current_view.plot_names:
                self.view_error = "Plot {} not in current plot names {}".format(self.current_view.current_plot, self.current_view.plot_names)
                return
        except Exception as e:
            # occasionally if the types are really different the "in" statement 
            # above will throw an error
            self.view_error = "Plot {} not in current plot names {}".format(self.current_view.current_plot, self.current_view.plot_names)
            return
          
        with warnings.catch_warnings(record = True) as w:
            try:
                self.plot_lock.acquire()                
                self.matplotlib_events.clear()
                
                try:
                    plt.gcf().canvas.set_working(True)
                except AttributeError:
                    pass
                
                self.current_view.plot_wi(self)
                self.view_error = ""
                self.view_error_trait = ""
            
                if this.last_view_plotted and "interactive" in this.last_view_plotted.traits():
                    this.last_view_plotted.interactive = False
                 
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

#     ### Overrides to make edit_traits go looking for views in the handler
    def edit_traits(self, view = None, parent = None, kind = None, 
                        context = None, handler = None, id = "",
                        scrollable=None, **args):
         
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
                     

    
@camel_registry.dumper(WorkflowItem, 'workflow-item', version = 2)
def _dump_wi(wi):
                          
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
                            
    return dict(deletable = wi.deletable,
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
    
    ret = WorkflowItem(**data)
        
    return ret

@camel_registry.loader('workflow-item', version = 2)
def _load_wi(data, version):
    return WorkflowItem(**data)