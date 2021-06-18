#!/usr/bin/env python3.4
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
Created on Feb 11, 2015

@author: brian
"""

# from traits.etsconfig.api import ETSConfig
# ETSConfig.toolkit = 'qt4'

import os.path
from natsort import natsorted
from matplotlib.figure import Figure

from traits.api import Instance, Bool, Any, on_trait_change, HTML, provides, Property, Event
from traitsui.api import (View, Item, VGroup, HGroup, EnumEditor, CheckListEditor, 
                          ButtonEditor, Group, Controller, FileEditor)
from pyface.tasks.api import Task, TaskLayout, PaneItem, TraitsDockPane, ITaskPane, TaskPane
from pyface.tasks.action.api import SMenuBar, SMenu, TaskToggleGroup
from envisage.api import Plugin, contributes_to
from envisage.ui.tasks.api import TaskFactory
from pyface.qt import QtGui
from pyface.api import ImageResource, FileDialog, OK

from cytoflow import BeadCalibrationOp

from .editors import VerticalListEditor, ToggleButtonEditor, ColorTextEditor, InstanceHandlerEditor
from .workflow import LocalWorkflow, WorkflowItem
from .help_pane import HelpDockPane

from .workflow.operations.tasbe_calibration import TasbeCalibrationOp
from .op_plugins import OpHandler
from .view_plugins import ViewHandler

from .matplotlib_backend_local import FigureCanvasQTAggLocal

class BleedthroughControlHandler(Controller):
    control_view = View(HGroup(Item('channel', style = 'readonly'),
                               Item('file', 
                                    editor = FileEditor(dialog_style = 'open'),
                                    show_label = False),
                               show_labels = False))
    
class TranslationControlHandler(Controller):
    control_view = View(HGroup(Item('from_channel', style = 'readonly', show_label = False),
                               Item('', label = '->'),
                               Item('to_channel', style = 'readonly', show_label = False),
                               Item('file', 
                                    editor = FileEditor(dialog_style = 'open'),
                                    show_label = False),
                               show_labels = False))
    
class UnitHandler(Controller):
    unit_view = View(HGroup(Item('channel', style = 'readonly', show_label = False),
                            Item('unit',
                                 editor = EnumEditor(name = 'context_handler.beads_units'),
                                 show_label = False)))

class CalibrationPane(TraitsDockPane):
    
    id = 'edu.mit.synbio.cytoflowgui.calibration_pane'
    name = "TASBE Calibration"

    # the task serving as the dock pane's controller
    task = Instance(Task)
    
    closable = False
    dock_area = 'left'
    floatable = False
    movable = False
    visible = True
    
#     def create_contents(self, parent):
#         """ Create and return the toolkit-specific contents of the dock pane.
#         """
#         self.ui = self.edit_traits(kind = "subpanel", 
#                                    parent = parent,
#                                    context = self.model)
#         return self.ui.control
    
    def create_contents(self, parent):
        """ Create and return the toolkit-specific contents of the dock pane.
        """
    
        self.ui = self.task.handler.edit_traits(view = 'operation_traits_view',
                                                context = self.task.model,
                                                kind='subpanel', 
                                                parent=parent,
                                                scrollable = True)
        return self.ui.control
    
# the central pane
@provides(ITaskPane)
class CalibrationTaskPane(TaskPane):
    """
    The center pane for the UI; contains the matplotlib canvas for plotting
    data views.
    """
    
    id = 'edu.mit.synbio.cytoflow.export_task_pane'
    name = 'Cytometry Data Viewer'
        
    layout = Instance(QtGui.QVBoxLayout)                    # @UndefinedVariable
        
    def create(self, parent):      
        # create a layout for the tab widget and the main view
        self.layout = layout = QtGui.QVBoxLayout()          # @UndefinedVariable
        self.control = QtGui.QWidget()                      # @UndefinedVariable
        self.control.setLayout(layout)

        # usually we would add the main plot here -- but a Qt widget
        # can only be part of one layout at a time.  so instead we
        # need to create that layout here, then dynamically add
        # the canvas when the task is activated (see activate(), below)
        
    def activate(self, canvas):
        if canvas.layout():
            canvas.layout().removeWidget(self.canvas)
        self.layout.addWidget(canvas)
        
        
class TasbeOperationHandler(OpHandler):
                
    beads_name_choices = Property(transient = True)
    beads_units = Property(observe = 'model.beads_name',
                           transient = True)
    experiment_channels = Property
    do_convert = Event
    
    operation_traits_view = \
        View(
              VGroup(
                  Item('blank_file',
                       editor = FileEditor(dialog_style = 'open')),
                  label = "Autofluorescence"),
              VGroup(
                  Item('fsc_channel',
                       editor = EnumEditor(name = 'handler.experiment_channels'),
                       label = "Forward Scatter Channel"),
                  Item('ssc_channel',
                       editor = EnumEditor(name = 'handler.experiment_channels'),
                       label = "Side Scatter Channel"),
                  label = "Morphology"),
              VGroup(
                  Item("channels",
                       editor = CheckListEditor(cols = 2,
                                                name = 'handler.experiment_channels'),
                       style = 'custom'),
                  label = "Channels To Calibrate",
                  show_labels = False),
              VGroup(
                  Item('bleedthrough_list',
                          editor = VerticalListEditor(editor = InstanceHandlerEditor(view = 'control_view',
                                                                                     handler_factory = BleedthroughControlHandler),
                                                      style = 'custom',
                                                      mutable = False),
                          style = 'custom'),
                  label = "Bleedthrough Correction",
                  show_border = False,
                  show_labels = False),
              VGroup(
                  Item('beads_name',
                       editor = EnumEditor(name = 'handler.beads_name_choices'),
                       label = "Beads",
                       width = -125),
                  Item('beads_file',
                       editor = FileEditor(dialog_style = 'open')),
                  Item('units_list',
                          editor = VerticalListEditor(editor = InstanceHandlerEditor(view = 'unit_view',
                                                                                     handler_factory = UnitHandler),
                                                      style = 'custom',
                                                      mutable = False),
                          style = 'custom',
                          label = "Bead\nunits"),
                  Item('bead_peak_quantile',
                       label = "Peak\nQuantile"),
                  Item('bead_brightness_threshold',
                       label = "Peak\nThreshold "),
                  Item('bead_brightness_cutoff',
                       label = "Peak\nCutoff"),
                  label = "Bead Calibration",
                  show_border = False),
              VGroup(
                  Item('do_color_translation',
                       label = "Do color translation?",
                       editor = ToggleButtonEditor(),
                       show_label = False),
                  Item('to_channel',
                       editor = EnumEditor(name = 'channels'),
                       visible_when = 'do_color_translation == True'),
                  Item('mixture_model',
                       label = "Use mixture\nmodel?",
                       visible_when = 'do_color_translation == True'),
                  VGroup(
                      Item('translation_list',
                           editor = VerticalListEditor(editor = InstanceHandlerEditor(view = 'control_view',
                                                                                      handler_factory = TranslationControlHandler),
                                                       style = 'custom',
                                                       mutable = False),
                         style = 'custom'),
                         show_labels = False,
                         visible_when = 'do_color_translation == True'),
                  label = "Color Translation",
                  show_border = False),
              VGroup(
                  Item('status',
                       style = 'readonly'),
                  Item('output_directory'),
                  Item('do_estimate',
                       editor = ButtonEditor(value = True,
                                             label = "Estimate parameters"),
                       show_label = False),
                  Item('handler.do_convert',
                       editor = ButtonEditor(value = True,
                                             label = "Convert files..."),
                       enabled_when = "valid_model == True",
                       show_label = False),
                  label = "Output",
                  show_border = False),
              Item('do_exit',
                   editor = ButtonEditor(value = True,
                                         label = "Return to Cytoflow"),
                   show_label = False),
        Group(Item('context.estimate_warning',
                   label = 'Warning',
                   resizable = True,
                   visible_when = 'context.estimate_warning',
                   editor = ColorTextEditor(foreground_color = "#000000",
                                            background_color = "#ffff99")),
              Item('context.estimate_error',
                    label = 'Error',
                    resizable = True,
                    visible_when = 'context.estimate_error',
                    editor = ColorTextEditor(foreground_color = "#000000",
                                             background_color = "#ff9191")),
              Item('context.op_warning',
                   label = 'Warning',
                   resizable = True,
                   visible_when = 'context.op_warning',
                   editor = ColorTextEditor(foreground_color = "#000000",
                                            background_color = "#ffff99")),
              Item('context.op_error',
                    label = 'Error',
                    resizable = True,
                    visible_when = 'context.op_error',
                    editor = ColorTextEditor(foreground_color = "#000000",
                                            background_color = "#ff9191"))))
    
    def _get_beads_name_choices(self):
        return list(BeadCalibrationOp.BEADS.keys())
    
    def _get_beads_units(self):
        if self.model.beads_name:
            return list(BeadCalibrationOp.BEADS[self.model.beads_name].keys())
        else:
            return []  
        
    def _get_experiment_channels(self):
        if self.model and self.model._experiment:
            return natsorted(self.model._experiment.channels)
        else:
            return []
    
    def _do_convert_fired(self):
        
        dialog = FileDialog(action = 'open files',
                            wildcard = (FileDialog.create_wildcard("FCS files", "*.fcs"))) #@UndefinedVariable  
        if dialog.open() == OK:            
            self.model.input_files = dialog.paths



class TasbeWorkflowItemHandler(Controller):
    def operation_traits_view(self):
        return View(Item('operation',
                         editor = InstanceHandlerEditor(view = 'operation_traits_view',
                                                        handler_factory = TasbeOperationHandler),
                         style = 'custom',
                         show_label = False),
                    handler = self)

                
class TasbeViewHandler(ViewHandler):
    def default_traits_view(self):
        return View(Item('context.view_warning',
                         resizable = True,
                         visible_when = 'context.view_warning',
                         editor = ColorTextEditor(foreground_color = "#000000",
                                                 background_color = "#ffff99")),
                    Item('context.view_error',
                         resizable = True,
                         visible_when = 'context.view_error',
                         editor = ColorTextEditor(foreground_color = "#000000",
                                                  background_color = "#ff9191")))


class TASBETask(Task):
    """
    classdocs
    """
    
    id = "edu.mit.synbio.cytoflowgui.tasbe_task"
    name = "TASBE calibration"
    
    menu_bar = SMenuBar(SMenu(TaskToggleGroup(),
                              id = 'View', name = '&View'))
    
    # the main workflow instance.
    workflow = Instance(LocalWorkflow)
    model = Instance(WorkflowItem)
    op = Instance(TasbeCalibrationOp)
    handler = Instance(TasbeWorkflowItemHandler)
        
    calibration_pane = Instance(CalibrationPane)
    help_pane = Instance(HelpDockPane)
    
#     _cached_help = HTML
    
    canvas = Instance(FigureCanvasQTAggLocal)
    
    debug = Bool(True)
    
    # the connection to the remote process
    remote_process = Any
    queue_listener = Any

    
    def activated(self):
        # we could try saving and restoring the model -- but that's messy. let's just start a new process.
        from .run import start_remote_process
        self.remote_process, remote_workflow_connection, remote_canvas_connection, self.queue_listener = start_remote_process()
        
        self.canvas = FigureCanvasQTAggLocal(Figure(), 
                                             remote_canvas_connection, 
                                             ImageResource('gear').create_image(size = (1000, 1000)))
        
        self.window.central_pane.activate(self.canvas)
        
        self.workflow = LocalWorkflow(remote_workflow_connection,
                                      debug = self.debug)
        
        wi = self.model   
        wi.views.append(wi.default_view)
        wi.current_view = wi.default_view
             
        self.workflow.workflow.append(wi)
        self.workflow.selected = wi
        
#         self.help_pane.html = self.op.get_help()
        
    def prepare_destroy(self):
        self.workflow.shutdown_remote_process(self.remote_process)
        self.queue_listener.stop()

    def _default_layout_default(self):
#         return TaskLayout(left = PaneItem("edu.mit.synbio.cytoflowgui.calibration_pane", width = 350),
#                           right = PaneItem("edu.mit.synbio.cytoflowgui.help_pane", width = 350))
     
        return TaskLayout(left = PaneItem("edu.mit.synbio.cytoflowgui.calibration_pane", width = 350))
    def create_central_pane(self):
        return CalibrationTaskPane()
     
    def create_dock_panes(self):
        self.calibration_pane = CalibrationPane(task = self)
         
#         self.help_pane = HelpDockPane(model = self.model,
#                                       task = self)
        
#         return [self.calibration_pane, self.help_pane]
        return [self.calibration_pane]
    
    @on_trait_change('op:do_exit', post_init = True)
    def activate_cytoflow_task(self):
        task = next(x for x in self.window.tasks if x.id == 'edu.mit.synbio.cytoflowgui.flow_task')
        self.window.activate_task(task)

        
class TASBETaskPlugin(Plugin):
    """
    An Envisage plugin wrapping TASBETask
    """

    # Extension point IDs.
    PREFERENCES       = 'envisage.preferences'
    PREFERENCES_PANES = 'envisage.ui.tasks.preferences_panes'
    TASKS             = 'envisage.ui.tasks.tasks'
    
    debug = Bool(False)
    remote_connection = Any

    #### 'IPlugin' interface ##################################################

    # The plugin's unique identifier.
    id = 'edu.mit.synbio.cytoflow.tasbe'
    
    # the local process's model
    model = Instance(LocalWorkflow)

    # The plugin's name (suitable for displaying to the user).
    name = 'TASBE Calibration'
    
    ###########################################################################
    # Protected interface.
    ###########################################################################

    @contributes_to(PREFERENCES)
    def _get_preferences(self):
        filename = os.path.join(os.path.dirname(__file__), 'preferences.ini')
        return [ 'file://' + filename ]
    
    @contributes_to(PREFERENCES_PANES)
    def _get_preferences_panes(self):
        from .preferences import CytoflowPreferencesPane
        return [CytoflowPreferencesPane]

    @contributes_to(TASKS)
    def _get_tasks(self):
        model = WorkflowItem(operation = TasbeCalibrationOp())
        return [TaskFactory(id = 'edu.mit.synbio.cytoflowgui.tasbe_task',
                            name = 'TASBE Calibration',
                            factory = lambda **x: TASBETask(application = self.application, 
                                                            model = model,
                                                            handler = TasbeWorkflowItemHandler(model = model),
                                                            **x))]
