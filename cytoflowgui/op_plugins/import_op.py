"""
Created on Mar 15, 2015

@author: brian
"""

if __name__ == '__main__':
    from traits.etsconfig.api import ETSConfig
    ETSConfig.toolkit = 'qt4'

    import os
    os.environ['TRAITS_DEBUG'] = "1"

from traitsui.api import View, Item, Controller
from traits.api import Button, Property, cached_property, provides, Instance
from cytoflowgui.import_dialog import ExperimentDialog
from cytoflowgui.op_plugins.i_op_plugin import IOperationPlugin, OpHandlerMixin
from pyface.api import OK as PyfaceOK
from cytoflow import ImportOp
from envisage.api import Plugin
from cytoflowgui.workflow_item import WorkflowItem

class ImportHandler(Controller, OpHandlerMixin):
    """
    A WorkflowItem that handles importing data and making a new Experiment
    """
    
    import_event = Button(label="Edit samples...")
    samples = Property(depends_on = 'wi.result')
    events = Property(depends_on = 'wi.result')
    
    def default_traits_view(self):
        return View(Item('handler.import_event',
                         show_label=False),
                    Item('handler.samples',
                         label='Samples',
                         style='readonly',
                         visible_when='handler.wi.result is not None'),
                    Item('handler.events',
                         label='Events',
                         style='readonly',
                         visible_when='handler.wi.result is not None'),
                    Item('object.coarse',
                         label="Coarse\nimport?",
                         visible_when='handler.wi.result is not None'),
                    Item('object.coarse_events',
                         label="Events per\nsample",
                         visible_when='handler.wi.result is not None and object.coarse is True'))
        
    def _import_event_fired(self):
        """
        Import data; save as self.result
        """

        d = ExperimentDialog()

        if self.wi.operation.tubes is not None:
            d.model.tubes = self.wi.operation.tubes
            
        d.size = (550, 500)
        d.open()
        
        if d.return_code is not PyfaceOK:
            return
        
        self.wi.operation.tubes = d.model.tubes
        d = None
        
        #self.model.update = True
        
    @cached_property
    def _get_samples(self):
        if self.wi.result is not None:
            return len(self.wi.operation.tubes)
        else:
            return 0
     
    @cached_property
    def _get_events(self):
        if self.wi.result is not None:
            return self.wi.result.data.shape[0]
        else:
            return 0

            
@provides(IOperationPlugin)
class ImportPlugin(Plugin):
    """
    class docs
    """
    
    id = 'edu.mit.synbio.cytoflowgui.op.import'
    operation_id = 'edu.mit.synbio.cytoflow.op.import'

    short_name = "Import data"
    menu_group = "TOP"
    
    def get_operation(self):
        ret = ImportOp()
        ret.handler_factory = ImportHandler
        return ret
    