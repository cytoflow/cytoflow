'''
Created on Mar 20, 2015

@author: brian
'''
from traits.api import HasTraits, provides, Str, List, Bool, Instance, \
                       Property, property_depends_on
from cytoflow.operations.i_operation import IOperation
from cytoflow import Experiment

@provides(IOperation)
class ImportOp(HasTraits):
    '''
    classdocs
    '''
    
    class Tube(HasTraits):
        """
        The model for a tube in an experiment.
        """
        
        # these are the traits that every tube has.  every other trait is
        # dynamically created.
        
        File = Str
        Name = Str
        
        def traits_equal(self, other):
            """ Are the traits (except File, Name, Row, Col) equal? """
            
            for trait in self.trait_names():
                if trait in ["File", "Name", "Row", "Col"]:
                    continue
                if not self.trait_get(trait) == other.trait_get(trait): 
                    return False
                
            return True
    
    class ExperimentSetup(HasTraits):
        """
        The model for the TabularEditor in the dialog
        """
        
        # this is the actual model; the rest is a built-in view.
        tubes = List(Tube)
        tube_trait_names = List(Str)
    
#         # traits to communicate with the TabularEditor
#         update = Bool
#         refresh = Bool
#         selected = List
#         
#         handler = Instance('ExperimentHandler')
        
        #tube_metadata = {}
    
#         view = View(
#             Group(
#                 Item(name = 'tubes', 
#                      id = 'table', 
#                      editor = TableEditor(editable = True,
#                                           sortable = True,
#                                           auto_size = True,
#                                           configurable = False,
#                                           selection_mode = 'cells',
#                                           selected = 'selected',
#                                           columns = [ObjectColumn(name = 'Name')],
#                                           ),
#                      enabled_when = "object.tubes"),
#                 show_labels = False
#             ),
#             title     = 'Experiment Setup',
#             id        = 'edu.mit.synbio.experiment_table_editor',
#             width     = 0.60,
#             height    = 0.75,
#             resizable = True
#         )    

    id = "Import op"
    name = "Import data"
     
    experiment_setup = Instance(ExperimentSetup)
    
    samples = Property(depends_on = 'canonical_experiment')
    events = Property(depends_on = 'canonical_experiment')

    coarse_mode = Bool(False)
    coarse_mode_events = Int(1000)

#    _canonical_experiment = Instance(Experiment)
          
    def validate(self, experiment):
        raise NotImplementedError
      
    def apply(self, old_experiment):
        raise NotImplementedError
      
    def default_view(self, experiment):
        raise NotImplementedError

        """ """