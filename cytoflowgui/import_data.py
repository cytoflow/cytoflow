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
from traitsui.api import View, Item
from traits.api import \
    Button, Str, Bool, Int, Instance, Property, Trait, cached_property
from import_dialog import ExperimentSetupDialog, Tube
from pyface.api import OK as PyfaceOK
from cytoflow import Experiment, LogFloat
import FlowCytometryTools as fc

class ImportWorkflowItem(WorkflowItem):
    """
    A WorkflowItem that handles importing data and making a new Experiment
    """
    name = Str("Import data")
    id = Str("")
    
    import_event = Button(label="Import data...")

    canonical_experiment = Instance(Experiment)

    samples = Property(depends_on = 'canonical_experiment')
    events = Property(depends_on = 'canonical_experiment')

    coarse_mode = Bool(False)
    coarse_mode_events = Int(1000)
    
    traits_view = View(Item(name='import_event',
                            show_label=False),
                       Item(name='samples',
                            label='Samples',
                            style='readonly',
                            visible_when='canonical_experiment is not None'),
                       Item(name='events',
                            label='Events',
                            style='readonly',
                            visible_when='canonical_experiment is not None'),
                       Item(name='coarse_mode',
                            label="Coarse mode?",
                            visible_when='canonical_experiment is not None'),
                       Item(name='coarse_mode_events',
                            label="Events per\nsample",
                            visible_when='(canonical_experiment is not None) and coarse_mode'),
)
    
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
        
        self.canonical_experiment = Experiment()

        trait_to_dtype = {"Str" : "category",
                          "Float" : "float",
                          "LogFloat" : "float",
                          "Bool" : "bool"}
        
        # get rid of the name and path traits
        trait_names = list(set(Tube.class_editable_traits()) - set(["Name", "File"]))
    
        for trait_name in trait_names:
            trait = Tube.class_traits()[trait_name]
            trait_type = trait.trait_type.__class__.__name__
        
            self.canonical_experiment.add_conditions(
                {trait_name : trait_to_dtype[trait_type]})
            if trait_type == "LogFloat":
                self.canonical_experiment.metadata[trait_name]["repr"] = "Log"
        
        # TODO - error checking.  yikes.
        for tube in setup.tubes:
            tube_fc = fc.FCMeasurement(ID=tube.Name,
                                       datafile=tube.File)
            self.canonical_experiment.add_tube(tube_fc,
                                               tube.trait_get(trait_names))
            
        self.experiment = self.canonical_experiment
        
    @cached_property
    def _get_samples(self):
        # TODO - this doesn't work
        if self.canonical_experiment is not None:
            return len(self.canonical_experiment.tubes)
        else:
            return 0
    
    @cached_property
    def _get_events(self):
        # TODO - this doesn't work.
        if self.canonical_experiment is not None:
            return self.canonical_experiment.data.size
        else:
            return 0
    
if __name__ == '__main__':
    wf = ImportWorkflowItem()
    wf.configure_traits()