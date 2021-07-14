'''
Created on Jan 15, 2021

@author: brian
'''

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
    operation = Instance('cytoflowgui.workflow.operations.IWorkflowOperation', copy = "ref")
    
    # the IViews associated with this operation
    views = List(Instance('cytoflowgui.workflow.views.IWorkflowView'), 
                 copy = "ref", 
                 comparison_mode = ComparisonMode.identity)
    
    # the currently selected view
    current_view = Instance('cytoflowgui.workflow.views.IWorkflowView', copy = "ref")
        
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
    default_view = Property(Instance('cytoflowgui.workflow.views.IWorkflowView'), observe = 'operation')
    
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
    
    plot_names = List(Any, status = True)
    plot_names_label = Str(status = True)
    
    # synchronization primitives for plotting
    matplotlib_events = Any(transient = True)
    plot_lock = Any(transient = True)
    
    # synchronization primitive for updating wi traits
    lock = Instance(threading.RLock, (), transient = True)
    
    ### Overrides to make edit_traits go looking for views in the handler
    def edit_traits(self, view = None, parent = None, kind = None, 
                        context = None, handler = None, id = "",  # @ReservedAssignment
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
            self.plot_names_label = ", ".join(plot_iter.by)
        
        
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
        Apply this wi's operation to the previous_wi wi's result
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

