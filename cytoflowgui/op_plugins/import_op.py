"""
Created on Mar 15, 2015

@author: brian
"""


if __name__ == '__main__':
    from traits.etsconfig.api import ETSConfig
    ETSConfig.toolkit = 'qt4'

    import os
    os.environ['TRAITS_DEBUG'] = "1"

from cytoflowgui.workflow_item import WorkflowItem
from traitsui.api import View, Item, Controller, ModelView, Handler
from traits.api import \
    Button, Str, Bool, Int, Instance, Property, cached_property, provides, \
    HasTraits, Event
from cytoflowgui.import_dialog import ExperimentSetupDialog, Tube,\
    ExperimentSetup
from cytoflowgui.op_plugins.i_op_plugin import IOperationPlugin,\
    MOperationPlugin
from pyface.api import OK as PyfaceOK
from cytoflow import Experiment
from cytoflow.operations.i_operation import IOperation
from envisage.api import Plugin
import FlowCytometryTools as fc

@provides(IOperation)
class ImportOp(HasTraits):
    """
    class docs
    """

class ImportHandler(Handler):
    """
    A WorkflowItem that handles importing data and making a new Experiment
    """
    name = Str("Import data handler")
    id = Str("import data handler id")
    
    import_event = Button(label="Import data...")

    canonical_experiment = Instance(Experiment)


    
    def init(self, info):
        pass
        
    def _import_event_fired(self):
        """
        Import data; save as self.result
        """
        
        d = ExperimentSetupDialog()
        d.size = (550, 500)
        d.open()
        
        if d.return_code is not PyfaceOK:
            return
        
        setup = d.object
        
        experiment = Experiment()

        trait_to_dtype = {"Str" : "category",
                          "Float" : "float",
                          "LogFloat" : "float",
                          "Bool" : "bool"}
        
        # get rid of the name and path traits
        trait_names = \
            list(set(Tube.class_editable_traits()) - set(["Name", "File"]))
    
        for trait_name in trait_names:
            trait = Tube.class_traits()[trait_name]
            trait_type = trait.trait_type.__class__.__name__
        
            experiment.add_conditions({trait_name : trait_to_dtype[trait_type]})
            if trait_type == "LogFloat":
                experiment.metadata[trait_name]["repr"] = "Log"
        
        # TODO - error checking.  yikes.
        for tube in setup.tubes:
            tube_fc = fc.FCMeasurement(ID=tube.Name, datafile=tube.File)
            experiment.add_tube(tube_fc, tube.trait_get(trait_names))
            
        self.canonical_experiment = self.result = experiment
        
    @cached_property
    def _get_samples(self):
        if self.canonical_experiment is not None:
            return len(self.canonical_experiment.tubes)
        else:
            return 0
    
    @cached_property
    def _get_events(self):
        if self.canonical_experiment is not None:
            return self.canonical_experiment.data.shape[0]
        else:
            return 0
        
    def _coarse_mode_changed(self, coarse_mode):
        if coarse_mode:
            self.experiment.data = \
                self.canonical_experiment.data.copy(deep=True)
        else:
            self.result = self.canonical_experiment
            
            
@provides(IOperationPlugin)
class ImportPlugin(Plugin, MOperationPlugin):
    """
    class docs
    """
    
    id = 'edu.mit.synbio.cytoflow.op.import'
    name = "Import data"
    short_name = "Import"
    
    def get_operation(self):
        return ImportOp()
    
    def get_view(self):
        return View(Item(name='handler.import_event',
                         show_label=False),
                    Item(name='handler.samples',
                         label='Samples',
                         style='readonly',
                         visible_when='canonical_experiment is not None'),
                    Item(name='handler.events',
                         label='Events',
                         style='readonly',
                         visible_when='canonical_experiment is not None'),
                    Item(name='handler.coarse_mode',
                         label="Coarse mode?",
                         visible_when='canonical_experiment is not None'),
                    Item(name='handler.coarse_mode_events',
                         label="Events per\nsample",
                         visible_when='(canonical_experiment is not None) and coarse_mode'),
                    handler = ImportHandler()
    )
