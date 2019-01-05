#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2019
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

'''
Principal Component Analysis
----------------------------

Use principal components analysis (PCA) to decompose a multivariate data
set into orthogonal components that explain a maximum amount of variance.

Creates new "channels" named ``{name}_1 ... {name}_n``,
where ``name`` is the :attr:`name` attribute and ``n`` is :attr:`num_components`.

The same decomposition may not be appropriate for different subsets of the data set.
If this is the case, you can use the :attr:`by` attribute to specify 
metadata by which to aggregate the data before estimating (and applying) a 
model.  The PCA parameters such as the number of components and the kernel
are the same across each subset, though.

.. object:: Name
    
    The operation name; determines the name of the new columns.
        
.. object:: Channels

    The channels to apply the decomposition to.

.. object:: Scale

    Re-scale the data in the specified channels before fitting.

.. object:: Num components

    How many components to fit to the data?  Must be a positive integer.
    
.. object:: By

    A list of metadata attributes to aggregate the data before estimating
    the model.  For example, if the experiment has two pieces of metadata,
    ``Time`` and ``Dox``, setting :attr:`by` to ``["Time", "Dox"]`` will 
    fit the model separately to each subset of the data with a unique 
    combination of ``Time`` and ``Dox``.
        
.. object:: Whiten

    Scale each component to unit variance?  May be useful if you will
    be using unsupervized clustering (such as K-means).

'''
import warnings

from traitsui.api import (View, Item, Controller, ButtonEditor, InstanceEditor,
                          VGroup, HGroup, EnumEditor, CheckListEditor, TextEditor)
from envisage.api import Plugin, contributes_to
from traits.api import (HasTraits, provides, Callable, List, Str, on_trait_change,
                        Property, DelegatesTo, Event, Bool, Dict)
from pyface.api import ImageResource

import cytoflow.utility as util

from cytoflow.operations.pca import PCAOp
from cytoflow.views.i_selectionview import IView

from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin, PluginViewMixin
from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT, shared_op_traits
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.subset import ISubset, SubsetListEditor
from cytoflowgui.op_plugins.i_op_plugin import PluginOpMixin, PluginHelpMixin
from cytoflowgui.vertical_list_editor import VerticalListEditor

from cytoflowgui.workflow import Changed
from cytoflowgui.serialization import camel_registry, traits_repr, traits_str, dedent

PCAOp.__repr__ = traits_repr

class _Channel(HasTraits):
    channel = Str
    scale = util.ScaleEnum
    
    def __repr__(self):
        return traits_repr(self)


class PCAHandler(OpHandlerMixin, Controller):
    
    add_channel = Event
    remove_channel = Event
    
    def default_traits_view(self):
        return View(Item('name',
                         editor = TextEditor(auto_set = False)),
                    VGroup(Item('channels_list',
                                editor = VerticalListEditor(editor = InstanceEditor(view = self.channel_traits_view()),
                                                            style = 'custom',
                                                            mutable = False),
                                style = 'custom'),
                    Item('handler.add_channel',
                         editor = ButtonEditor(value = True,
                                               label = "Add a channel"),
                         show_label = False),
                    Item('handler.remove_channel',
                         editor = ButtonEditor(value = True,
                                               label = "Remove a channel")),
                    show_labels = False),
                    VGroup(Item('num_components',
                                editor = TextEditor(auto_set = False),
                                label = "Num\nComponents"),
                           Item('whiten'),
                           Item('by',
                                editor = CheckListEditor(cols = 2,
                                                         name = 'handler.previous_conditions_names'),
                                label = 'Group\nEstimates\nBy',
                                style = 'custom'),
                           label = "Estimate parameters"),
                    VGroup(Item('subset_list',
                                show_label = False,
                                editor = SubsetListEditor(conditions = "context.previous_wi.conditions",
                                                          metadata = "context.previous_wi.metadata",
                                                          when = "'experiment' not in vars() or not experiment")),
                           label = "Subset",
                           show_border = False,
                           show_labels = False),
                    Item('do_estimate',
                         editor = ButtonEditor(value = True,
                                               label = "Estimate!"),
                         show_label = False),
                    shared_op_traits)

    # MAGIC: called when add_control is set
    def _add_channel_fired(self):
        self.model.channels_list.append(_Channel())
        
    def _remove_channel_fired(self):
        if self.model.channels_list:
            self.model.channels_list.pop()   
            
    def channel_traits_view(self):
        return View(HGroup(Item('channel',
                                editor = EnumEditor(name = 'handler.context.previous_wi.channels')),
                           Item('scale')),
                    handler = self)

class PCAPluginOp(PluginOpMixin, PCAOp):
    handler_factory = Callable(PCAHandler)
    
    channels_list = List(_Channel, estimate = True)    
    channels = List(Str, transient = True)
    scale = Dict(Str, util.ScaleEnum, transient = True)
    by = List(Str, estimate = True)
    num_components = util.PositiveCInt(2, allow_zero = False, estimate = True)
    whiten = Bool(False, estimate = True)

    @on_trait_change('channels_list_items, channels_list.+', post_init = True)
    def _channels_changed(self, obj, name, old, new):
        self.changed = (Changed.ESTIMATE, ('channels_list', self.channels_list))
    
    # bits to support the subset editor
    
    subset_list = List(ISubset, estimate = True)    
    subset = Property(Str, depends_on = "subset_list.str")
        
    # MAGIC - returns the value of the "subset" Property, above
    def _get_subset(self):
        return " and ".join([subset.str for subset in self.subset_list if subset.str])
    
    @on_trait_change('subset_list.str')
    def _subset_changed(self, obj, name, old, new):
        self.changed = (Changed.ESTIMATE, ('subset_list', self.subset_list))
    
    def estimate(self, experiment):
        for i, channel_i in enumerate(self.channels_list):
            for j, channel_j in enumerate(self.channels_list):
                if channel_i.channel == channel_j.channel and i != j:
                    raise util.CytoflowOpError("Channel {0} is included more than once"
                                               .format(channel_i.channel))
                                               
        self.channels = []
        self.scale = {}
        for channel in self.channels_list:
            self.channels.append(channel.channel)
            self.scale[channel.channel] = channel.scale
            
        super().estimate(experiment, subset = self.subset)
        self.changed = (Changed.ESTIMATE_RESULT, self)
        
    def apply(self, experiment):
        for i, channel_i in enumerate(self.channels_list):
            for j, channel_j in enumerate(self.channels_list):
                if channel_i.channel == channel_j.channel and i != j:
                    raise util.CytoflowOpError("Channel {0} is included more than once"
                                               .format(channel_i.channel))
                                               
        self.channels = []
        self.scale = {}
        for channel in self.channels_list:
            self.channels.append(channel.channel)
            self.scale[channel.channel] = channel.scale
            
        return super().apply(experiment)
        
        
    def clear_estimate(self):
        self._pca.clear()
        self.changed = (Changed.ESTIMATE_RESULT, self)
    
    def get_notebook_code(self, idx):
        op = PCAOp()
        op.copy_traits(self, op.copyable_trait_names())
        
        for channel in self.channels_list:
            op.channels.append(channel.channel)
            op.scale[channel.channel] = channel.scale

        return dedent("""
        op_{idx} = {repr}
        
        op_{idx}.estimate(ex_{prev_idx}{subset})
        ex_{idx} = op_{idx}.apply(ex_{prev_idx})
        """
        .format(repr = repr(op),
                idx = idx,
                prev_idx = idx - 1,
                subset = ", subset = " + repr(self.subset) if self.subset else ""))
        


@provides(IOperationPlugin)
class PCAPlugin(Plugin, PluginHelpMixin):

    id = 'edu.mit.synbio.cytoflowgui.op_plugins.pca'
    operation_id = 'edu.mit.synbio.cytoflow.operations.pca'

    short_name = "Principal Component Analysis"
    menu_group = "Calibration"
    
    def get_operation(self):
        return PCAPluginOp()
    
    def get_icon(self):
        return ImageResource('pca')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    
### Serialization
@camel_registry.dumper(PCAPluginOp, 'pca', version = 1)
def _dump(op):
    return dict(name = op.name,
                channels_list = op.channels_list,
                num_components = op.num_components,
                whiten = op.whiten,
                by = op.by,
                subset_list = op.subset_list)
    
@camel_registry.loader('pca', version = 1)
def _load(data, version):
    return PCAPluginOp(**data)

@camel_registry.dumper(_Channel, 'pca-channel', version = 1)
def _dump_channel(channel):
    return dict(channel = channel.channel,
                scale = channel.scale)
    
@camel_registry.loader('pca-channel', version = 1)
def _load_channel(data, version):
    return _Channel(**data)