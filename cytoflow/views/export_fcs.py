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
cytoflow.views.export_fcs
-------------------------
"""

from pathlib import Path
from copy import copy

from traits.api import (Constant, List, Str, Bool, Dict, Directory, 
                        HasStrictTraits)

import cytoflow.utility as util

class ExportFCS(HasStrictTraits):
    """
    Exports events as FCS files.  
    
    This isn't a traditional view, in that it doesn't implement :meth:`plot`.
    Instead, use :meth:`enum_files` to figure out which files will be created
    from a particular experiment, and :meth:`export` to export the FCS files.
    
    The Cytoflow attributes will be encoded in keywords in the FCS TEXT
    segment, starting with the characters ``CF_``.
    
    Attributes
    ----------
    base : Str
        The prefix of the FCS filenames
        
    path : Directory
        The directory to export to.
        
    by : List(Str)
        A list of conditions from :attr:`~.Experiment.conditions`; each unique
        combination of conditions will be exported to an FCS file.
        
    keywords : Dict(Str, Str)
        The FCS files are exported with only the minimum of required keywords.
        If you want to add more keywords to the FCS files' TEXT segment, 
        specify them here.
        
    subset : str
        A Python expression used to select a subset of the data
    
    Examples
    --------
    
    Make a little data set.
            
    >>> import cytoflow as flow
    >>> import_op = flow.ImportOp()
    >>> import_op.tubes = [flow.Tube(file = "Plate01/RFP_Well_A3.fcs",
    ...                              conditions = {'Dox' : 10.0}),
    ...                    flow.Tube(file = "Plate01/CFP_Well_A4.fcs",
    ...                              conditions = {'Dox' : 1.0})]
    >>> import_op.conditions = {'Dox' : 'float'}
    >>> ex = import_op.apply()
        
    Export the data
        
    >>> import tempfile
    >>> flow.ExportFCS(path = 'export/',
    ...                by = ["Dox"],
    ...                subset = "Dox == 10.0").export(ex)
        
    """
    
    # traits   
    id = Constant("edu.mit.synbio.cytoflow.view.table")
    friendly_id = Constant("Table View") 
    
    base = Str
    path = Directory(exists = True)
    by = List(Str)
    keywords = Dict(Str, Str)
    
    subset = Str
    
    _include_by = Bool(True)
    
    def enum_files(self, experiment):
        """
        Return an iterator over the file names that this export module will
        produce from a given experiment.
        
        Parameters
        ----------
        experiment : Experiment
            The :class:`.Experiment` to export
        """
        if experiment is None:
            raise util.CytoflowViewError('experiment', "No experiment specified")   
        
        if len(self.by) == 0:
            raise util.CytoflowViewError('by',
                                         "You must specify some variables in `by`")

        for b in self.by:
            if b not in experiment.conditions:
                raise util.CytoflowOpError('by',
                                           "Aggregation metadata {} not found, "
                                           "must be one of {}"
                                           .format(b, experiment.conditions))
                
        if self.subset:
            try:
                experiment = experiment.query(self.subset)
            except util.CytoflowError as e:
                raise util.CytoflowViewError('subset', str(e)) from e
            except Exception as e:
                raise util.CytoflowViewError('subset',
                                             "Subset string '{0}' isn't valid"
                                             .format(self.subset)) from e
                 
            if len(experiment) == 0:
                raise util.CytoflowViewError('subset',
                                             "Subset string '{0}' returned no events"
                                             .format(self.subset))
                        
        class file_enum(object):
            
            def __init__(self, by, base, _include_by, experiment):
                self._iter = None
                self._returned = False
                self.by = by
                self.base = base
                self._include_by = _include_by
                
                if by:
                    self._iter = experiment.data.groupby(by).__iter__()
                
            def __iter__(self):
                return self
            
            def __next__(self):
                if self._iter:
                    values = next(self._iter)[0]
                    
                    if len(self.by) == 1:
                        values = [values]
                    
                    parts = []
                    for i, name in enumerate(self.by):
                        if self._include_by:
                            parts.append(name + '_' + str(values[i]))
                        else:
                            parts.append(str(values[i]))
                        
                    if self.base:
                        return self.base + '_' + '_'.join(parts) + '.fcs'
                    else:
                        return '_'.join(parts) + '.fcs'
                        
                else:
                    if self._returned:
                        raise StopIteration
                    else:
                        self._returned = True
                        return None
            
        return file_enum(self.by, self.base, self._include_by, experiment)
    
    def export(self, experiment):
        """
        Export FCS files from an experiment.
        
        Parameters
        ----------
        experiment : Experiment
            The :class:`.Experiment` to export
        """
        
        if not self.path:
            raise util.CytoflowOpError('path',
                                       'Must specify an output directory')
        
        d = Path(self.path)
        
        if not d.is_dir():
            raise util.CytoflowOpError('path',
                                       'Output directory {} must exist')
        
        # also tests for good experiment, self.by
        for filename in self.enum_files(experiment):
            p = d / filename
            if p.is_file():
                raise util.CytoflowOpError('path',
                                           'File {} already exists'
                                           .format(p)) 
                
        if self.subset:
            try:
                experiment = experiment.query(self.subset)
            except util.CytoflowError as e:
                raise util.CytoflowViewError('subset', str(e)) from e
            except Exception as e:
                raise util.CytoflowViewError('subset',
                                             "Subset string '{0}' isn't valid"
                                             .format(self.subset)) from e
                 
            if len(experiment) == 0:
                raise util.CytoflowViewError('subset',
                                             "Subset string '{0}' returned no events"
                                             .format(self.subset))
                
        for group, data_subset in experiment.data.groupby(self.by):
            data_subset = data_subset[experiment.channels]
            
            if len(self.by) == 1:
                group = [group]
            
            parts = []
            kws = copy(self.keywords)
            for i, name in enumerate(self.by):
                if self._include_by:
                    parts.append(name + '_' + str(group[i]))
                else:
                    parts.append(str(group[i]))
                    
                kws["CF_" + name] = str(group[i])
                
            if self.base:
                filename = self.base + '_' + '_'.join(parts) + '.fcs'
            else:
                filename = '_'.join(parts) + '.fcs'
                
        
            full_path = d / filename
            util.write_fcs(str(full_path), 
                           experiment.channels, 
                           data_subset.values,
                           compat_chn_names = False,
                           compat_negative = False,
                           **kws)
            
            
    
    