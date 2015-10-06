from traits.api import HasStrictTraits, Str, CStr, List, Float, provides
import numpy as np
import matplotlib as mpl

from cytoflow.operations import IOperation
from cytoflow.utility import CytoflowOpError

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
        
    def apply(self, experiment):
        """Applies the threshold to an experiment.
        
        Parameters
        ----------
        experiment : Experiment
            the old experiment to which this op is applied
            
        Returns
        -------
            a new experiment, the same as old_experiment but with a new
            column the same as the operation name.  The bool is True if the
            event's measurement in self.channel is greater than self.low and
            less than self.high; it is False otherwise.
            
        Raises
        ------
        CytoflowOpError
            if for some reason the operation can't be applied to this
            experiment. The reason is in CytoflowOpError.value
        """
        
        if self.name in experiment.data.columns:
            raise CytoflowOpError("op.name is in the experiment already!")
        
        if not self.xchannel or not self.ychannel:
            raise CytoflowOpError("Must specify both an x channel and a y channel")
        
        if not self.xchannel in experiment.channels:
            raise CytoflowOpError("xchannel {0} is not in the experiment"
                                  .format(self.xchannel))
                                  
        if not self.ychannel in experiment.channels:
            raise CytoflowOpError("ychannel {0} is not in the experiment"
                                  .format(self.ychannel))
              
        if len(self.vertices) < 3:
            return False
       
        if any([len(x) != 2 for x in self.vertices]):
            return False 
        
        # make sure name got set!
        if not self.name:
            raise CytoflowOpError("You have to set the Polygon gate's name "
                               "before applying it!")
        
        # make sure old_experiment doesn't already have a column named self.name
        if(self.name in experiment.data.columns):
            raise CytoflowOpError("Experiment already contains a column {0}"
                               .format(self.name))
            
        # use a matplotlib Path because testing for membership is a fast C fn.
        path = mpl.path.Path(np.array(self.vertices))
        xy_data = experiment.data.as_matrix(columns = [self.xchannel,
                                                           self.ychannel])
        
        new_experiment = experiment.clone()
        
        new_experiment[self.name] = path.contains_points(xy_data)
            
        new_experiment.conditions[self.name] = "bool"
        new_experiment.metadata[self.name] = {}
            
        return new_experiment
