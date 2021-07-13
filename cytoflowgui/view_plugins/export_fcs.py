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
----------

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

from traits.api import provides, Event, observe, List
from traitsui.api import (View, Item, VGroup, ButtonEditor, CheckListEditor)
from envisage.api import Plugin
from pyface.api import ImageResource, DirectoryDialog, OK

from ..workflow.views import ExportFCSWorkflowView
from ..editors import SubsetListEditor, ColorTextEditor, InstanceHandlerEditor
from ..subset_controllers import subset_handler_factory

from .i_view_plugin import IViewPlugin, VIEW_PLUGIN_EXT
from .view_plugin_base import ViewHandler, PluginHelpMixin
    
class ExportFCSHandler(ViewHandler):   
    export = Event()

    view_traits_view = \
        View(VGroup(
             VGroup(Item('by',
                         editor = CheckListEditor(cols = 2,
                                                  name = 'context_handler.conditions_names'),
                         label = 'Group\nEstimates\nBy',
                         style = 'custom')),
             VGroup(Item('subset_list',
                         show_label = False,
                         editor = SubsetListEditor(conditions = "context_handler.conditions",
                                                   editor = InstanceHandlerEditor(view = 'subset_view',
                                                                                  handler_factory = subset_handler_factory),
                                                   mutable = False)),
                    label = "Subset",
                    show_border = False,
                    show_labels = False),
            Item('handler.export',
                 editor = ButtonEditor(label = "Export..."),
                 show_label = False),
            label = "Export FCS",
            show_border = False),

            Item('context.view_warning',
                 resizable = True,
                 visible_when = 'context.view_warning',
                 editor = ColorTextEditor(foreground_color = "#000000",
                                         background_color = "#ffff99")),
            Item('context.view_error',
                 resizable = True,
                 visible_when = 'context.view_error',
                 editor = ColorTextEditor(foreground_color = "#000000",
                                          background_color = "#ff9191")))
        
    view_params_view = View() # empty view -- no parameters for exporting FCS
    
    @observe('export')
    def _on_export(self, _):
                  
        self.model.path = ""
        
        dialog = DirectoryDialog(parent = None,
                                 message = "Directory to save FCS files...")
  
        if dialog.open() != OK:
            return
          
        self.model.path = dialog.path

    @observe('model.by.items,model.subset')
    def _reset_path(self, _):
        self.model.path = ""
    

@provides(IViewPlugin)
class ExportFCSPlugin(Plugin, PluginHelpMixin):

    id = 'edu.mit.synbio.cytoflowgui.view.exportfcs'
    view_id = 'edu.mit.synbio.cytoflow.view.exportfcs'
    short_name = "Export FCS"
    
    def get_view(self):
        return ExportFCSWorkflowView()
    
    def get_handler(self, model, context):
        if isinstance(model, ExportFCSWorkflowView):
            return ExportFCSHandler(model = model, context = context)
        else:
            return None

    def get_icon(self):
        return ImageResource('export')

    plugin = List(contributes_to = VIEW_PLUGIN_EXT)
    def _plugin_default(self):
        return [self]
