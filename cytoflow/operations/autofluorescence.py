#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2017
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

"""
cytoflow.operations.autofluorescence
------------------------------------
"""

from traits.api import (HasStrictTraits, Str, CFloat, File, Dict,
                        Instance, List, Constant, provides)
                       
import numpy as np

import cytoflow.views
import cytoflow.utility as util

from .i_operation import IOperation
from .import_op import Tube, ImportOp, check_tube

from pandas import DataFrame
from ..experiment import Experiment

@provides(IOperation)
class AutofluorescenceOp(HasStrictTraits):
    """
    Apply autofluorescence correction to a set of fluorescence channels.
    
    The :meth:`estimate` function loads a separate FCS file (not part of the input
    :class:`.Experiment`) and computes the untransformed median and standard deviation 
    of the blank cells.  Then, :meth:`apply` subtracts the median from the 
    experiment data.
    
    To use, set the :attr:`blank_file` property to point to an FCS file with
    unstained or nonfluorescing cells in it; set the :attr:`channels` 
    property to a  list of channels to correct.
    
    :meth:`apply` also adds the ``af_median`` and ``af_stdev`` metadata to the 
    corrected channels, representing the median and standard deviation of the 
    measured blank distributions.
    
    Attributes
    ----------       
    channels : List(Str)
        The channels to correct.
        
    blank_file : File
        The filename of a file with "blank" cells (not fluorescent).  Used
        to :meth:`estimate` the autofluorescence.
        
    Examples
    --------
    Create a small experiment:
    
    .. plot::
        :context: close-figs
    
        >>> import cytoflow as flow
        >>> import_op = flow.ImportOp()
        >>> import_op.tubes = [flow.Tube(file = "tasbe/rby.fcs")]
        >>> ex = import_op.apply()
    
    Create and parameterize the operation
    
    .. plot::
        :context: close-figs

        >>> af_op = flow.AutofluorescenceOp()
        >>> af_op.channels = ["Pacific Blue-A", "FITC-A", "PE-Tx-Red-YG-A"]
        >>> af_op.blank_file = "tasbe/blank.fcs"
    
    Estimate the model parameters
    
    .. plot::
        :context: close-figs 
    
        >>> af_op.estimate(ex)
    
    Plot the diagnostic plot
    
    .. plot::
        :context: close-figs

        >>> af_op.default_view().plot(ex)  

    Apply the operation to the experiment
    
    .. plot::
        :context: close-figs
    
        >>> ex2 = af_op.apply(ex)  
        
    """
    
    # traits
    id = Constant('edu.mit.synbio.cytoflow.operations.autofluorescence')
    friendly_id = Constant("Autofluorescence correction")
    
    name = Constant("Autofluorescence")
    channels = List(Str)
    blank_file = File(exists = True)
    blank_frame = Instance(DataFrame)

    _af_median = Dict(Str, CFloat, transient = True)
    _af_stdev = Dict(Str, CFloat, transient = True)
    
    def estimate(self, experiment, subset = None): 
        """
        Estimate the autofluorescence from :attr:`blank_file` in channels
        specified in :attr:`channels`.  
        
        Parameters
        ----------
        experiment : Experiment
            The experiment to which this operation is applied
            
        subset : str (default = "")
            An expression that specifies the events used to compute the 
            autofluorescence

        """
        if experiment is None:
            raise util.CytoflowOpError('experiment', 
                                       "No experiment specified")
        
        if not self.channels:
            raise util.CytoflowOpError('channels', "No channels specified")

        if not set(self.channels) <= set(experiment.channels):
            raise util.CytoflowOpError('channels', 
                                       "Specified channels that weren't found "
                                       "in the experiment.")

        # don't have to validate that blank_file exists; should crap out on 
        # trying to set a bad value
        
        # make a little Experiment
        channels = {experiment.metadata[c]["fcs_name"] : c for c in experiment.channels}
        name_metadata = experiment.metadata['name_metadata']
        if ( self.blank_file != '' ):
            check_tube(self.blank_file, experiment)
            blank_exp = ImportOp(tubes = [Tube(file = self.blank_file)], 
                                 channels = channels,
                                 name_metadata = name_metadata).apply()
        else:
            blank_exp = ImportOp(tubes = [Tube(frame = self.blank_frame)], 
                                 channels = channels,
                                 name_metadata = name_metadata).apply()
        
        # apply previous operations
        for op in experiment.history:
            blank_exp = op.apply(blank_exp)
            
        # subset it
        if subset:
            try:
                blank_exp = blank_exp.query(subset)
            except Exception as exc:
                raise util.CytoflowOpError('subset', 
                                           "Subset string '{0}' isn't valid"
                                           .format(subset)) from exc
                            
            if len(blank_exp.data) == 0:
                raise util.CytoflowOpError('subset',
                                           "Subset string '{0}' returned no events"
                                      .format(subset))
        
        for channel in self.channels:
            channel_min = blank_exp[channel].quantile(0.025)
            channel_max = blank_exp[channel].quantile(0.975)
            
            blank_exp[channel] = blank_exp[channel].clip(channel_min,
                                                         channel_max)
            
            self._af_median[channel] = np.median(blank_exp[channel])
            self._af_stdev[channel] = np.std(blank_exp[channel])    
                
    def apply(self, experiment):
        """
        Applies the autofluorescence correction to channels in an experiment.
        
        Parameters
        ----------
        experiment : Experiment
            the experiment to which this op is applied
            
        Returns
        -------
        Experiment
            a new experiment with the autofluorescence median subtracted.  The
            corrected channels have the following metadata added to them:
            
            - **af_median** : Float
              The median of the non-fluorescent distribution
        
            - **af_stdev** : Float
              The standard deviation of the non-fluorescent distribution
        """
        
        if experiment is None:
            raise util.CytoflowOpError('experiment', "No experiment specified")
        
        if not self.channels:
            raise util.CytoflowOpError('channels', "No channels specified")
        
        if not self._af_median:
            raise util.CytoflowOpError(None, "Autofluorescence values aren't set. Did "
                                       "you forget to run estimate()?")
        
        if not set(self._af_median.keys()) <= set(experiment.channels) or \
           not set(self._af_stdev.keys()) <= set(experiment.channels):
            raise util.CytoflowOpError(None, "Autofluorescence estimates aren't set, or are "
                               "different than those in the experiment "
                               "parameter. Did you forget to run estimate()?")

        if not set(self._af_median.keys()) == set(self._af_stdev.keys()):
            raise util.CytoflowOpError(None, "Median and stdev keys are different! "
                                  "What the hell happened?!")
        
        if not set(self.channels) == set(self._af_median.keys()):
            raise util.CytoflowOpError('channels', "Estimated channels differ from the channels "
                               "parameter.  Did you forget to (re)run estimate()?")
        
        new_experiment = experiment.clone()
                
        for channel in self.channels:
            new_experiment[channel] = \
                experiment[channel] - self._af_median[channel]
                
            new_experiment.metadata[channel]['af_median'] = self._af_median[channel]
            new_experiment.metadata[channel]['af_stdev'] = self._af_stdev[channel]

        new_experiment.history.append(self.clone_traits(transient = lambda t: True))

        return new_experiment
    
    def default_view(self, **kwargs):
        """
        Returns a diagnostic plot to see if the autofluorescence estimation
        is working.
        
        Returns
        -------
        IView
            An diagnostic view, call :meth:`~AutofluorescenceDiagnosticView.plot` 
            to see the diagnostic plots
        """
        return AutofluorescenceDiagnosticView(op = self, **kwargs)
    
    
@provides(cytoflow.views.IView)
class AutofluorescenceDiagnosticView(HasStrictTraits):
    """
    Plots a histogram of each channel, and its median in red.  Serves as a
    diagnostic for the autofluorescence correction.
    
    Attributes
    ----------
    op : Instance(AutofluorescenceOp)
        The :class:`AutofluorescenceOp` whose parameters we're viewing. Set 
        automatically if you created the instance using 
        :meth:`AutofluorescenceOp.default_view`.
    
    subset : str (default = "")
        An expression that specifies the events that are plotted in the histograms
    """
    
    # traits   
    id = Constant('edu.mit.synbio.cytoflow.view.autofluorescencediagnosticview')
    friendly_id = Constant("Autofluorescence Diagnostic")

    op = Instance(AutofluorescenceOp)    
    subset = Str
    
    def plot(self, experiment, **kwargs):
        """
        Plot a faceted histogram view of a channel
        """
        
        if experiment is None:
            raise util.CytoflowViewError('experiment', "No experiment specified")
        
        if not self.op.channels:
            raise util.CytoflowViewError('op', "No channels specified")
        
        if not self.op._af_median:
            raise util.CytoflowViewError('op', 
                                         "Autofluorescence values aren't set. Did "
                                         "you forget to run estimate()?")
            
        if not set(self.op._af_median.keys()) <= set(experiment.channels) or \
           not set(self.op._af_stdev.keys()) <= set(experiment.channels):
            raise util.CytoflowViewError('op', 
                                       "Autofluorescence estimates aren't set, or are "
                                       "different than those in the experiment "
                                       "parameter. Did you forget to run estimate()?")

        if not set(self.op._af_median.keys()) == set(self.op._af_stdev.keys()):
            raise util.CytoflowOpError('op',
                                       "Median and stdev keys are different! "
                                       "What the hell happened?!")
        
        if not set(self.op.channels) == set(self.op._af_median.keys()):
            raise util.CytoflowOpError('op', 
                                       "Estimated channels differ from the channels "
                                       "parameter.  Did you forget to (re)run estimate()?")
        
        import matplotlib.pyplot as plt
        import seaborn as sns  # @UnusedImport
        
        kwargs.setdefault('histtype', 'stepfilled')
        kwargs.setdefault('alpha', 0.5)
        kwargs.setdefault('antialiased', True)
           
        # make a little Experiment
        try:
            channels = {experiment.metadata[c]["fcs_name"] : c for c in experiment.channels}
            name_metadata = experiment.metadata['name_metadata']
            if ( self.op.blank_file != '' ):
                check_tube(self.op.blank_file, experiment)
                blank_exp = ImportOp(tubes = [Tube(file = self.op.blank_file)], 
                                     channels = channels,
                                     name_metadata = name_metadata).apply()
            else:
                blank_exp = ImportOp(tubes = [Tube(frame = self.op.blank_frame)], 
                                     channels = channels,
                                     name_metadata = name_metadata).apply()
        except util.CytoflowOpError as e:
            raise util.CytoflowViewError('op', e.__str__()) from e
        
        # apply previous operations
        for op in experiment.history:
            blank_exp = op.apply(blank_exp)
            
        # subset it
        if self.subset:
            try:
                blank_exp = blank_exp.query(self.subset)
            except Exception as exc:
                raise util.CytoflowOpError('subset',
                                           "Subset string '{0}' isn't valid"
                                           .format(self.subset)) from exc
                            
            if len(blank_exp.data) == 0:
                raise util.CytoflowOpError('subset',
                                           "Subset string '{0}' returned no events"
                                           .format(self.subset))

        plt.figure()
        
        for idx, channel in enumerate(self.op.channels):
            d = blank_exp.data[channel]
            plt.subplot(len(self.op.channels), 1, idx+1)
            plt.title(channel)
            plt.hist(d, bins = 200, **kwargs)
            
            plt.axvline(self.op._af_median[channel], color = 'r')
            
        plt.tight_layout(pad = 0.8)
