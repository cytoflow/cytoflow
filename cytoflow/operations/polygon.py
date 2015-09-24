from traits.api import HasStrictTraits, Str, CStr, List, Float, provides
import numpy as np
import matplotlib as mpl
from cytoflow.operations.i_operation import IOperation

@provides(IOperation)
class PolygonOp(HasStrictTraits):
    """Apply a polygon gate to a cytometry experiment.
    
    Attributes
    ----------
    name : Str
        The operation name.  Used to name the new metadata field in the
        experiment that's created by apply()
        
    xchannel : Str
        The name of the first channel to apply the range gate.
        
    ychannel : Str
        The name of the second channel to apply the range gate.
        
    polygon : List((Float, Float))
        The polygon verticies.  An ordered list of 2-tuples, representing
        the x and y coordinates of the vertices.
        
    Notes
    -----
    This module uses `matplotlib.path.Path` to represent the polygon, because
    membership testing is very fast.
    
    You can set the verticies by hand, I suppose, but it's much easier to use
    the `PolygonSelection` view to do so.  Unfortunately, it's currently very
    slow in the GUI and impossible to use in an IPython notebook.
    """
    
    # traits
    id = "edu.mit.synbio.cytoflow.operations.polygon"
    friendly_id = "Polygon"
    
    name = CStr()
    xchannel = Str()
    ychannel = Str()
    vertices = List((Float, Float))
    
    def is_valid(self, experiment):
        """Validate this operation against an experiment."""

        if not self.name:
            return False
        
        if self.name in experiment.data.columns:
            return False
        
        if not self.xchannel or not self.ychannel:
            return False
        
        if (not self.xchannel in experiment.channels or
            not self.ychannel in experiment.channels):
            return False
              
        if len(self.vertices) < 3:
            return False
       
        if any([len(x) != 2 for x in self.vertices]):
            return False 
       
        return True
        
    def apply(self, old_experiment):
        """Applies the threshold to an experiment.
        
        Parameters
        ----------
        experiment : Experiment
            the old_experiment to which this op is applied
            
        Returns
        -------
            a new experiment, the same as old_experiment but with a new
            column the same as the operation name.  The bool is True if the
            event's measurement in self.channel is greater than self.low and
            less than self.high; it is False otherwise.
        """
        
        # make sure name got set!
        if not self.name:
            raise RuntimeError("You have to set the Polygon gate's name "
                               "before applying it!")
        
        # make sure old_experiment doesn't already have a column named self.name
        if(self.name in old_experiment.data.columns):
            raise RuntimeError("Experiment already contains a column {0}"
                               .format(self.name))
            
        # use a matplotlib Path because testing for membership is a fast C fn.
        path = mpl.path.Path(np.array(self.vertices))
        xy_data = old_experiment.data.as_matrix(columns = [self.xchannel,
                                                           self.ychannel])
        
        new_experiment = old_experiment.clone()
        
        new_experiment[self.name] = path.contains_points(xy_data)
            
        new_experiment.conditions[self.name] = "bool"
        new_experiment.metadata[self.name] = {}
            
        return new_experiment
