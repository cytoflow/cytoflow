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
from traits.api import Button, Property, cached_property, provides
from cytoflowgui.import_dialog import ExperimentDialog
from cytoflowgui.op_plugins.i_op_plugin import IOperationPlugin,\
    MOperationPlugin
from pyface.api import OK as PyfaceOK
from cytoflow import ImportOp
from envisage.api import Plugin

class ImportHandler(Controller):
    """
    A WorkflowItem that handles importing data and making a new Experiment
    """
    
    import_event = Button(label="Edit samples...")
    samples = Property(depends_on = 'model.result')
    events = Property(depends_on = 'model.result')
    
    def init(self, info):
        pass
        
    def _import_event_fired(self):
        """
        Import data; save as self.result
        """

        d = ExperimentDialog()

        if self.model.operation.tubes is not None:
            d.model.tubes = self.model.operation.tubes
            
        d.size = (550, 500)
        d.open()
        
        if d.return_code is not PyfaceOK:
            return
        
        self.model.operation.tubes = d.model.tubes
        d = None
        
        #self.model.update = True
        
    @cached_property
    def _get_samples(self):
        if self.model.result is not None:
            return len(self.model.operation.tubes)
        else:
            return 0
     
    @cached_property
    def _get_events(self):
        if self.model.result is not None:
            return self.model.result.data.shape[0]
        else:
            return 0

            
@provides(IOperationPlugin)
class ImportPlugin(Plugin, MOperationPlugin):
    """
    class docs
    """
    
    id = 'edu.mit.synbio.cytoflowgui.op.import'
    name = "Import data"
    short_name = "Import"
    menu_group = ""
    
    def get_operation(self):
        return ImportOp()
    
    def get_traitsui_view(self, model):
        return View(Item('handler.import_event',
                         show_label=False),
                    Item('handler.samples',
                         label='Samples',
                         style='readonly',
                         visible_when='object.result is not None'),
                    Item('handler.events',
                         label='Events',
                         style='readonly',
                         visible_when='object.result is not None'),
                    Item('object.operation.coarse',
                         label="Coarse\nimport?",
                         visible_when='object.result is not None'),
                    Item('object.operation.coarse_events',
                         label="Events per\nsample",
                         visible_when='object.result is not None and object.operation.coarse is True'),
                    handler = ImportHandler(model = model)
    )
