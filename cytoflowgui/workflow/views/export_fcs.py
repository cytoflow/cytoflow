#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2021
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
Export FCS
-----

Exports FCS files from after this operation. Only really useful if
you've done a calibration step or created derivative channels using
the ratio option. As you set the options, the main plot shows a table
of the files that will be created.

.. object:: Base 
    The prefix of the FCS file names

.. object:: By 

    A list of metadata attributes to aggregate the data before exporting.
    For example, if the experiment has two pieces of metadata,
    ``Time`` and ``Dox``, setting :attr:`by` to ``["Time", "Dox"]`` will export
    one file for each subset of the data with a unique combination of
    ``Time`` and ``Dox``.
    
.. object:: Keywords 

    If you want to add more keywords to the FCS files' TEXT segment, 
    specify them here.
        
.. object: Subset
 
    Select a subset of the data to export
    
.. object:: Export...

    Choose a folder and export the FCS files.

"""

from textwrap import dedent

from traits.api import provides, Str, List, HasTraits, observe, Property

import matplotlib.pyplot as plt
from matplotlib.table import Table

from cytoflow import ExportFCS
import cytoflow.utility as util


from cytoflowgui.workflow.serialization import camel_registry, traits_repr
from ..subset import ISubset
from .view_base import IWorkflowView, WorkflowView, BasePlotParams

ExportFCS.__repr__ = traits_repr

class ExportKeyword(HasTraits):
    keyword = Str
    value = Str
    
    def __repr__(self):
        return traits_repr(self)
    

@provides(IWorkflowView)
class ExportFCSWorkflowView(WorkflowView, ExportFCS): 
    plot_params = BasePlotParams() # this is unused -- no view, not passed to plot()
    
    keywords_list = List(ExportKeyword)
    export_status = Str(status = True)
     
    # override the base class's "subset" with one that is dynamically generated /
    # updated from subset_list
    subset = Property(Str, observe = "subset_list.items.str")
    subset_list = List(ISubset, estimate = True)
        
    # bits to support the subset editor
    @observe('subset_list:items.str')
    def _on_subset_changed(self, _):
        self.changed = 'subset_list'
        
    # MAGIC - returns the value of the "subset" Property, above
    def _get_subset(self):
        return " and ".join([subset.str for subset in self.subset_list if subset.str])
        
    def enum_conditions_and_files(self, experiment):
        """
        Return an iterator over the conditions and file names that this export will
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
                        filename = self.base + '_' + '_'.join(parts) + '.fcs'
                    else:
                        filename = '_'.join(parts) + '.fcs'
                    
                    return tuple(values + [filename])
                        
                else:
                    if self._returned:
                        raise StopIteration
                    else:
                        self._returned = True
                        return None
            
        return file_enum(self.by, self.base, self._include_by, experiment)
    
    
    def plot(self, experiment, plot_name = None, **kwargs):
        """Plot a table of the conditions, filenames, and number of events"""
        
        if experiment is None:
            raise util.CytoflowViewError('experiment', "No experiment specified")   
        
        if self.subset:
            try:
                experiment = experiment.query(self.subset)
            except Exception as e:
                raise util.CytoflowViewError('subset',
                                             "Subset string '{0}' isn't valid"
                                             .format(self.subset)) from e
                
            if len(experiment) == 0:
                raise util.CytoflowViewError('subset',
                                             "Subset string '{0}' returned no values"
                                             .format(self.subset))
                
        # if path is set, actually do an export. this isn't terribly elegant,
        # but this is the only place we have an experiment!
        if self.path:
            
        
        num_cols = len(self.by) + 2
        
        fig = plt.figure()
        ax = fig.add_subplot(111)
        
        # hide the plot axes that matplotlib tries to make
        ax.xaxis.set_visible(False)
        ax.yaxis.set_visible(False)
        for sp in ax.spines.values():
            sp.set_color('w')
            sp.set_zorder(0)
        
        loc = 'upper left'
        bbox = None
        
        t = Table(ax, loc, bbox, **kwargs)
        t.auto_set_font_size(False)
        for c in range(num_cols):
            t.auto_set_column_width(c)

        width = [0.2] * num_cols

        height = t._approx_text_height() * 1.8
        
        t.add_cell(0, 0, width = width[0], height = height, text = "#")
        for ci, c in enumerate(self.by):
            ci = ci + 1
            t.add_cell(0, ci, width = width[ci], height = height, text = c)
            
        ci = len(self.by) + 1
        t.add_cell(0, ci, width = width[ci], height = height, text = "Filename")
        
#         ci = len(self.by) + 2
#         t.add_cell(0, ci, width = width[ci], height = height, text = "Events")
            
        for ri, row in enumerate(self.enum_conditions_and_files(experiment)):
            t.add_cell(ri+1, 0, "{:g}".format(ri + 1))
            for ci, col in enumerate(row):
                t.add_cell(ri+1,
                           ci+1,
                           width = width[ci+1],
                           height = height,
                           text = col)
                                    
        ax.add_table(t)
        
        
    def export(self, experiment):
        self.keywords = {k.keyword : k.value for k in self.keywords_list}
        super().export(experiment)

        
    def get_notebook_code(self, idx):
        view = ExportFCS()
        view.copy_traits(self, view.copyable_trait_names())

        return dedent("""
        {repr}.plot(ex_{idx})
        """
        .format(repr = repr(view),
                idx = idx))

           
### Serialization

@camel_registry.dumper(ExportFCSWorkflowView, 'export-fcs-view', version = 1)
def _dump(view):
    return dict(keywords_list = view.keywords_list,
                base = view.base,
                by = view.by,
                subset_list = view.subset_list)
    
@camel_registry.loader('table-view', version = 1)
def _load(data, version):
    return ExportFCSWorkflowView(**data)
