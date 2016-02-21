'''
Created on Feb 21, 2016

@author: brian
'''

#!/usr/bin/env python2.7

# (c) Massachusetts Institute of Technology 2015-2016
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

from __future__ import division

from traits.api import HasTraits, Float, Instance, Property, \
                       cached_property
                       
import numpy as np

from matplotlib import scale
from matplotlib import transforms
from matplotlib.ticker import NullFormatter, ScalarFormatter
from matplotlib.ticker import Locator

from cytoflow.operations.logicle_ext.Logicle import Logicle

class LogicleScale(HasTraits, scale.ScaleBase):
    """
    A matplotlib scale that transforms the data using the `logicle` function
    
    This scaling method implements a "linear-like" region around 0, and a
    "log-like" region for large values, with a very smooth transition between
    them.  It's particularly good for compensated data, and data where you have
    "negative" events (events with a fluorescence of ~0.)
    
    If you don't have any data around 0, you might be better of with a more
    traditional log scale or a Hyperlog.
    
    The transformation has one parameter, `W`, which specifies the width of
    the "linear" range in log10 decades.  You can estimate an "optimal" value 
    with `estimate()`, or you can set it to a fixed value like 0.5.
    
    Attributes
    ----------
    range : Float
        the input range of the channel.  no default!
    W : Float (default = 0.5)
        for each channel, the width of the linear range, in log10 decades.  
        can estimate, or use a fixed value like 0.5.
    M : Float (default = 4.5)
        The width of the entire display, in log10 decades
    A : Float (default = 0.0)
        for each channel, additional decades of negative data to include.  
        the display usually captures all the data, so 0 is fine to start.
    
    References
    ----------
    [1] A new "Logicle" display method avoids deceptive effects of logarithmic 
        scaling for low signals and compensated data.
        Parks DR, Roederer M, Moore WA.
        Cytometry A. 2006 Jun;69(6):541-51.
        PMID: 16604519
        http://onlinelibrary.wiley.com/doi/10.1002/cyto.a.20258/full
        
    [2] Update for the logicle data scale including operational code 
        implementations.
        Moore WA, Parks DR.
        Cytometry A. 2012 Apr;81(4):273-7. 
        doi: 10.1002/cyto.a.22030 
        PMID: 22411901
        http://onlinelibrary.wiley.com/doi/10.1002/cyto.a.22030/full
    """
    
    name = "logicle"
    
    range = Float
    W = Float(0.5, desc="the width of the linear range, in log10 decades.")
    M = Float(4.5, desc = "the width of the display in log10 decades")
    A = Float(0.0, desc = "additional decades of negative data to include.")
    
    logicle = Property(Instance(Logicle), depends_on = "[range, W, M, A]")
    
    def __init__(self, axis, **kwargs):
        HasTraits.__init__(self, **kwargs)
    
    def get_transform(self):
        """
        Returns the matplotlib.transform instance that does the actual 
        transformation
        """
        return LogicleScale.LogicleTransform(logicle = self.logicle)
    
    def set_default_locators_and_formatters(self, axis):
        """
        Set the locators and formatters to reasonable defaults for
        linear scaling.
        """
        axis.set_major_locator(LogicleMajorLocator())
        axis.set_major_formatter(ScalarFormatter())
        axis.set_minor_locator(LogicleMinorLocator())
        axis.set_minor_formatter(NullFormatter())        
    
    @cached_property
    def _get_logicle(self):
        return Logicle(self.range, self.W, self.M, self.A)
    
    class LogicleTransform(HasTraits, transforms.Transform):
        # There are two value members that must be defined.
        # ``input_dims`` and ``output_dims`` specify number of input
        # dimensions and output dimensions to the transformation.
        # These are used by the transformation framework to do some
        # error checking and prevent incompatible transformations from
        # being connected together.  When defining transforms for a
        # scale, which are, by definition, separable and have only one
        # dimension, these members should always be set to 1.
        input_dims = 1
        output_dims = 1
        is_separable = True
        has_inverse = True
        
        # the Logicle instance
        logicle = Instance(Logicle)
        
        def __init__(self, **kwargs):
            transforms.Transform.__init__(self)
            HasTraits.__init__(self, **kwargs)
        
        def transform_non_affine(self, values):
            scale = np.vectorize(self.logicle.scale)
            return scale(values)

        def inverted(self):
            return LogicleScale.InvertedLogicleTransform(logicle = self.logicle)
        
    class InvertedLogicleTransform(HasTraits, transforms.Transform):
        input_dims = 1
        output_dims = 1
        is_separable = True
        has_inverse = True
     
        # the Logicle instance
        logicle = Instance(Logicle)
        
        def __init__(self, **kwargs):
            transforms.Transform.__init__(self)
            HasTraits.__init__(self, **kwargs)
        
        def transform_non_affine(self, values):
            inverse = np.vectorize(self.logicle.inverse)
            return inverse(values)
        
        def inverted(self):
            return LogicleScale.LogicleTransform(logicle = self.logicle)
        
        
class LogicleMajorLocator(Locator):
    """
    Determine the tick locations for logicle axes.
    Based on matplotlib.LogLocator
    """

    def set_params(self):
        """Empty"""
        pass

    def __call__(self):
        'Return the locations of the ticks'
        vmin, vmax = self.axis.get_view_interval()
        return self.tick_values(vmin, vmax)

    def tick_values(self, vmin, vmax):
        'Every decade, including 0 and negative'
        
        # get us decade-aligned min and max
        vmin, vmax = self.view_limits(vmin, vmax)
              
        if vmin < 0:
            ticks = [-1.0 * 10 ** x for x in np.arange(np.log10(-1.0 * vmin), 1, -1)]
            ticks.append(0.0)
            ticks.extend( [10 ** x for x in np.arange(2, np.log10(vmax), 1)])
        else:
            ticks = [0.0] if vmin == 0.0 else []
            ticks.extend( [10 ** x for x in np.arange(1, np.log10(vmax), 1)])

        return self.raise_if_exceeds(np.asarray(ticks))

    def view_limits(self, vmin, vmax):
        'Try to choose the view limits intelligently'

        if vmax < vmin:
            vmin, vmax = vmax, vmin
            
        # get the nearest decade that contains the data
        if vmax > 0:
            vmax = 10 ** np.ceil(np.log10(vmax))
        else: 
            vmax = -1.0 * 10 ** np.ceil(np.log10(-1.0 * vmax))    

        if vmin > 0:
            vmin = 10 ** np.ceil(np.log10(vmin))
        else: 
            vmin = -1.0 * 10 ** np.ceil(np.log10(-1.0 * vmin))           

        return transforms.nonsingular(vmin, vmax)
    
class LogicleMinorLocator(Locator):
    """
    Determine the tick locations for logicle axes.
    Based on matplotlib.LogLocator
    """

    def set_params(self):
        """Empty"""
        pass

    def __call__(self):
        'Return the locations of the ticks'
        vmin, vmax = self.axis.get_view_interval()
        return self.tick_values(vmin, vmax)

    def tick_values(self, vmin, vmax):
        'Every tenth decade, including 0 and negative'
        
        # get us decade-aligned min and max
        vmin, vmax = self.view_limits(vmin, vmax)
              
        if vmin < 0:
            lt = [np.arange(10 ** x, 10 ** (x - 1), -1.0 * (10 ** (x-1)))
                  for x in np.arange(np.log10(-1.0 * vmin), 1, -1)]
            
            # flatten and take the negative
            lt = [-1.0 * item for sublist in lt for item in sublist]

            gt = [np.arange(10 ** x, 10 ** (x + 1), 10 ** x)
                  for x in np.arange(1, np.log10(vmax))]
            
            # flatten
            gt = [item for sublist in gt for item in sublist]
            
            ticks = lt
            ticks.extend(gt)
        else:
            
            ticks = [np.arange(10 ** x, 10 ** (x + 1), 10 ** x)
                     for x in np.arange(np.log10(vmin), np.log10(vmax))]
            ticks = [item for sublist in ticks for item in sublist]

        return self.raise_if_exceeds(np.asarray(ticks))

    def view_limits(self, vmin, vmax):
        'Try to choose the view limits intelligently'
        
        return vmin, vmax
# 
#         if vmax < vmin:
#             vmin, vmax = vmax, vmin
#             
#         # get the nearest decade that contains the data
#         if vmax > 0:
#             vmax = 10 ** np.ceil(np.log10(vmax))
#         else: 
#             vmax = -1.0 * 10 ** np.ceil(np.log10(-1.0 * vmax))    
# 
#         if vmin > 0:
#             vmin = 10 ** np.ceil(np.log10(vmin))
#         else: 
#             vmin = -1.0 * 10 ** np.ceil(np.log10(-1.0 * vmin))           
#          
#         return vmin, vmax
         


scale.register_scale(LogicleScale)