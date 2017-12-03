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
Created on Feb 11, 2015

@author: brian
"""

# from traits.etsconfig.api import ETSConfig
# ETSConfig.toolkit = 'qt4'

import os.path
from camel import Camel

from traits.api import Instance, List, Bool, on_trait_change, Any, Unicode, TraitError
from pyface.tasks.api import Task, TaskLayout, PaneItem
from pyface.tasks.action.api import SMenu, SMenuBar, SToolBar, TaskAction
from pyface.api import FileDialog, ImageResource, AboutDialog, information, error, confirm, OK, YES
from envisage.api import Plugin, ExtensionPoint, contributes_to
from envisage.ui.tasks.api import TaskFactory

from cytoflowgui.flow_task_pane import FlowTaskPane
from cytoflowgui.workflow_pane import WorkflowDockPane
from cytoflowgui.view_pane import ViewDockPane
from cytoflowgui.help_pane import HelpDockPane
from cytoflowgui.workflow import Workflow
from cytoflowgui.op_plugins import IOperationPlugin, ImportPlugin, OP_PLUGIN_EXT
from cytoflowgui.view_plugins import IViewPlugin, VIEW_PLUGIN_EXT
from cytoflowgui.workflow_item import WorkflowItem
from cytoflowgui.util import DefaultFileDialog
from cytoflowgui.serialization import save_yaml, load_yaml, save_notebook

# from . import mailto

class FlowTask(Task):
    """
    classdocs
    """
    
    id = "edu.mit.synbio.cytoflow.flow_task"
    name = "Cytometry analysis"
    
    # the main workflow instance.
    model = Instance(Workflow)
        
    # the center pane
    plot_pane = Instance(FlowTaskPane)
    workflow_pane = Instance(WorkflowDockPane)
    view_pane = Instance(ViewDockPane)
    help_pane = Instance(HelpDockPane)
    
    # plugin lists, to setup the interface
    op_plugins = List(IOperationPlugin)
    view_plugins = List(IViewPlugin)
    
    menu_bar = SMenuBar(SMenu(TaskAction(name='Open...',
                                         method='on_open',
                                         accelerator='Ctrl+O'),
                              TaskAction(name='Save',
                                         #image='save', 
                                         method='on_save',
                                         accelerator='Ctrl+S'),
                              TaskAction(name='Save As...',
                                         method='on_save_as',
                                         accelerator='Ctrl+e'),
                              TaskAction(name='Save Plot...',
                                         method='on_export',
                                         accelerator='Ctrl+x'),
                            TaskAction(name='Export Jupyter notebook...',
                                       method='on_notebook',
                                       accelerator='Ctrl+I'),                              
#                               TaskAction(name='Preferences...',
#                                          method='on_prefs',
#                                          accelerator='Ctrl+P'),
                              id='File', name='&File'),
                        SMenu(id = 'View', name = '&View'),
                        SMenu(TaskAction(name = 'Report a problem....',
                                         method = 'on_problem'),
                              TaskAction(name='About...',
                                         method='on_about'),
                              id="Help", name ="&Help"))
    
    tool_bars = [ SToolBar(TaskAction(method='on_new',
                                      name = "New",
                                      tooltip='New workflow',
                                      image=ImageResource('new')),
                           TaskAction(method='on_open',
                                      name = "Open",
                                      tooltip='Open a file',
                                      image=ImageResource('open')),
                           TaskAction(method='on_save',
                                      name = "Save",
                                      tooltip='Save the current file',
                                      image=ImageResource('save')),
                           TaskAction(method='on_export',
                                      name = "Save Plot",
                                      tooltip='Save the current plot',
                                      image=ImageResource('export')),
                            TaskAction(method='on_notebook',
                                       name='Notebook',
                                       tooltip="Export to an Jupyter notebook...",
                                       image=ImageResource('ipython')),
#                            TaskAction(method='on_prefs',
#                                       name = "Prefs",
#                                       tooltip='Preferences',
#                                       image=ImageResource('prefs')),
                           image_size = (32, 32))]
    
    # the file to save to if the user clicks "save" and has already clicked
    # "open" or "save as".
    filename = Unicode
    
    def prepare_destroy(self):
        self.model.shutdown_remote_process()
    
    def activated(self):
        # add the import op
        self.add_operation(ImportPlugin().id) 
        self.model.selected = self.model.workflow[0]
        
        # if we're debugging, add a few data bits
        if self.model.debug:
            from cytoflow import Tube
                        
            import_op = self.model.workflow[0].operation
            import_op.conditions = {"Dox" : "float", "Well" : "category"}
#             import_op.conditions["Dox"] = "float"
#             import_op.conditions["Well"] = "category"
         
            tube1 = Tube(file = "../cytoflow/tests/data/Plate01/CFP_Well_A4.fcs",
                         conditions = {"Dox" : 0.0, "Well" : 'A'})
         
            tube2 = Tube(file = "../cytoflow/tests/data/Plate01/RFP_Well_A3.fcs",
                         conditions = {"Dox" : 10.0, "Well" : 'A'})
             
            tube3 = Tube(file = "../cytoflow/tests/data/Plate01/CFP_Well_B4.fcs",
                         conditions = {"Dox" : 0.0, "Well" : 'B'})
         
            tube4 = Tube(file = "../cytoflow/tests/data/Plate01/RFP_Well_A6.fcs",
                         conditions = {"Dox" : 10.0, "Well" : 'B'})
         
            import_op.tubes = [tube1, tube2, tube3, tube4]
            
#             from cytoflowgui.op_plugins import ChannelStatisticPlugin

#             self.add_operation(ChannelStatisticPlugin().id)
#             stat_op = self.model.workflow[1].operation
#             stat_op.name = "Test"
#             stat_op.channel = "Y2-A"
#             stat_op.statistic_name = "Geom.Mean"
#             stat_op.by = ["Dox", "Well"]
#             self.model.selected = self.model.workflow[1]
                    
        self.model.modified = False
    
    def _default_layout_default(self):
        return TaskLayout(left = PaneItem("edu.mit.synbio.workflow_pane"),
                          right = PaneItem("edu.mit.synbio.view_traits_pane"))
     
    def create_central_pane(self):
        self.plot_pane = FlowTaskPane(model = self.model)
        return self.plot_pane
     
    def create_dock_panes(self):
        self.workflow_pane = WorkflowDockPane(model = self.model, 
                                              plugins = self.op_plugins,
                                              task = self)
        
        self.view_pane = ViewDockPane(model = self.model,
                                      plugins = self.view_plugins,
                                      task = self)
        
        self.help_pane = HelpDockPane(view_plugins = self.view_plugins,
                                      op_plugins = self.op_plugins,
                                      task = self)
        
        return [self.workflow_pane, self.view_pane, self.help_pane]
        
    def on_new(self):
        if self.model.modified:
            ret = confirm(parent = None,
                          message = "Are you sure you want to discard the current workflow?",
                          title = "Clear workflow?")
            
            if ret != YES:
                return
            
        self.filename = ""
        self.window.title = "Cytoflow"
        
        # clear the workflow
        self.model.workflow = []
        
        # add the import op
        self.add_operation(ImportPlugin().id) 
        
        # and select the operation
        self.model.selected = self.model.workflow[0]
        
        self.model.modified = False
     
        
    def on_open(self):
        """ 
        Shows a dialog to open a file.
        """
        
        if self.model.modified:
            ret = confirm(parent = None,
                          message = "Are you sure you want to discard the current workflow?",
                          title = "Clear workflow?")
            
            if ret != YES:
                return
        
        dialog = FileDialog(parent = self.window.control, 
                            action = 'open',
                            wildcard = (FileDialog.create_wildcard("Cytoflow workflow", "*.flow") + ';' +  #@UndefinedVariable  
                                        FileDialog.create_wildcard("All files", "*"))) #@UndefinedVariable  
        if dialog.open() == OK:
            self.open_file(dialog.path)
            self.filename = dialog.path
            self.window.title = "Cytoflow - " + self.filename
            
#     def open_file(self, path):
#         f = open(path, 'r')
#         unpickler = pickle.Unpickler(f)
#         
#         try:
#             version = unpickler.load()
#         except TraitError:
#             error(parent = None,
#                   message = "This doesn't look like a Cytoflow file. Or maybe "
#                             "you tried to load a workflow older than version "
#                             "0.5?")
#             return
#         
#         if version != self.model.version:
#             ret = confirm(parent = None,
#                           message = "This is Cytoflow {}, but you're trying "
#                           "to load a workflow from version {}. This may or "
#                           "may not work!  Are you sure you want to proceed?"
#                           .format(self.model.version, version),
#                           title = "Load workflow?")
#             if ret != YES:
#                 return
# 
#         try:
#             new_workflow = unpickler.load()
#         except TraitError:
#             error(parent = None,
#                   message = "Error trying to load the workflow.")
#             return
# 
#         # a few things to take care of when reloading
#         for wi_idx, wi in enumerate(new_workflow):
#             
#             # get wi lock
#             wi.lock.acquire()
#             
#             # clear the wi status
#             wi.status = "loading"
# 
#             # re-link the linked list.  i thought this would get taken care
#             # of in deserialization, but i guess not...
#             if wi_idx > 0:
#                 wi.previous_wi = new_workflow[wi_idx - 1]
# 
#         # replace the current workflow with the one we just loaded
#         
#         if False:  # for debugging the loading of things
#             from .event_tracer import record_events 
#             
#             with record_events() as container:
#                 self.model.workflow = new_workflow
#                                 
#             container.save_to_directory(os.getcwd()) 
#         else:
#             self.model.workflow = new_workflow
#             self.model.modified = False
#             
#         for wi in self.model.workflow:
#             wi.lock.release()

    def open_file(self, path):
        
        new_workflow = load_yaml(path)
        
        # a few things to take care of when reloading
        for wi_idx, wi in enumerate(new_workflow):
            
            # get wi lock
            wi.lock.acquire()
            
            # clear the wi status
            wi.status = "loading"

            # re-link the linked list.  i thought this would get taken care
            # of in deserialization, but i guess not...
            if wi_idx > 0:
                wi.previous_wi = new_workflow[wi_idx - 1]

        # replace the current workflow with the one we just loaded
        
        if False:  # for debugging the loading of things
            from .event_tracer import record_events 
            
            with record_events() as container:
                self.model.workflow = new_workflow
                                
            container.save_to_directory(os.getcwd()) 
        else:
            self.model.workflow = new_workflow
            self.model.modified = False
            
        for wi in self.model.workflow:
            wi.lock.release()

        
    def on_save(self):
        """ Save the file to the previous filename  """
        if self.filename:
            save_yaml(self.model.workflow, self.filename)
            self.model.modified = False
        else:
            self.on_save_as()
            
    def on_save_as(self):
        dialog = DefaultFileDialog(parent = self.window.control,
                                   action = 'save as', 
                                   default_suffix = "flow",
                                   wildcard = (FileDialog.create_wildcard("Cytoflow workflow", "*.flow") + ';' + #@UndefinedVariable  
                                               FileDialog.create_wildcard("All files", "*")))                    #@UndefinedVariable  
        
        if dialog.open() == OK:
            save_yaml(self.model.workflow, dialog.path)
            self.filename = dialog.path
            self.model.modified = False
            self.window.title = "Cytoflow - " + self.filename
            
    @on_trait_change('model.modified', post_init = True)
    def _on_model_modified(self, val):
        if val:
            if not self.window.title.endswith("*"):
                self.window.title += "*"
        else:
            if self.window.title.endswith("*"):
                self.window.title = self.window.title[:-1]
        
    def on_export(self):
        """
        Shows a dialog to export a file
        """
                
        information(None, "This will save exactly what you see on the screen "
                          "to a file.", "Export")
        
        f = ""
        filetypes_groups = self.plot_pane.canvas.get_supported_filetypes_grouped()
        filename_exts = []
        for name, ext in filetypes_groups.items():
            if f:
                f += ";"
            f += FileDialog.create_wildcard(name, " ".join(["*." + e for e in ext])) #@UndefinedVariable  
            filename_exts.append(ext)
        
        dialog = FileDialog(parent = self.window.control,
                            action = 'save as',
                            wildcard = f)
        
        if dialog.open() == OK:
            filetypes = list(self.plot_pane.canvas.get_supported_filetypes().keys())
            if not [ext for ext in ["." + ext for ext in filetypes] if dialog.path.endswith(ext)]:
                selected_exts = filename_exts[dialog.wildcard_index]
                ext = sorted(selected_exts, key = len)[0]
                dialog.path += "."
                dialog.path += ext
                
            self.plot_pane.export(dialog.path)

                
            
    def on_notebook(self):
        """
        Shows a dialog to export the workflow to an Jupyter notebook
        """
    
        dialog = FileDialog(parent = self.window.control,
                            action = 'save as',
                            wildcard = '*.ipynb')
        if dialog.open() == OK:
            save_notebook(self.model.workflow, dialog.path)

    
    def on_prefs(self):
        pass
    
    def on_problem(self):
        
        information(None, "Your email client will now create a new message to the "
                    "developer.  Debugging logs are attached.  Please fill "
                    "out the template bug report and send -- thank you for "
                    "reporting a bug!")

        log = self.application.application_log.getvalue()
        
        versions = ["{0} {1}".format(key, value) for key, value in self._get_package_versions().items()]

        body = """
Thank you for your bug report!  Please fill out the following template.

PLATFORM (Mac, PC, Linux, other):

OPERATING SYSTEM (eg OSX 10.7, Windows 8.1):

SEVERITY (Critical? Major? Minor? Enhancement?):

DESCRIPTION:
  - What were you trying to do?
  - What happened?
  - What did you expect to happen?
  

PACKAGE VERSIONS: {0}

DEBUG LOG: {1}
""".format(versions, log)

#         mailto.mailto("teague@mit.edu", 
#                       subject = "Cytoflow bug report",
#                       body = body)
    
    def _get_package_versions(self):
    
        import sys
        from cytoflow import __version__ as cf_version
        from fcsparser import __version__ as fcs_version
        from pandas import __version__ as pd_version
        from numpy import __version__ as np_version
        from numexpr import __version__ as nxp_version
        from bottleneck import __version__ as btl_version
        from seaborn import __version__ as sns_version
        from matplotlib import __version__ as mpl_version
        from scipy import __version__ as scipy_version
        from sklearn import __version__ as skl_version
        from pyface import __version__ as pyf_version
        from envisage import __version__ as env_version
        from traits import __version__ as trt_version
        from traitsui import __version__ as trt_ui_version
        
        return {"python" : sys.version,
                "cytoflow" : cf_version,
                "fcsparser" : fcs_version,
                "pandas" : pd_version,
                "numpy" : np_version,
                "numexpr" : nxp_version,
                "bottleneck" : btl_version,
                "seaborn" : sns_version,
                "matplotlib" : mpl_version,
                "scipy" : scipy_version,
                "scikit-learn" : skl_version,
                "pyface" : pyf_version,
                "envisage" : env_version,
                "traits" : trt_version,
                "traitsui" : trt_ui_version}
        
        
    def on_about(self):
        versions = self._get_package_versions()
        text = ["<b>Cytoflow {0}</b>".format(versions['cytoflow']),
                "<p>"]
        
        ver_text = ["{0} {1}".format(key, value) for key, value in versions.items()]
        
        text.extend(ver_text)
        
        text.extend(["Icons from the <a href=http://tango.freedesktop.org>Tango Desktop Project</a>",
                "<a href=https://thenounproject.com/search/?q=setup&i=14287>Settings icon</a> by Paulo Sa Ferreira from <a href=https://thenounproject.com>The Noun Project</a>",
                "<a href=http://www.freepik.com/free-photos-vectors/background>App icon from Starline - Freepik.com</a>",
                "Cuvette image from Wikimedia Commons user <a href=http://commons.wikimedia.org/wiki/File:Hellma_Large_cone_cytometry_cell.JPG>HellmaUSA</a>"])
        
        dialog = AboutDialog(text = text,
                             parent = self.window.control,
                             title = "About",
                             image = ImageResource('cuvette'),
                             additions = text)
        dialog.open()
        
    @on_trait_change('model.selected', post_init = True)
    def _on_select_op(self, selected):
        if selected:
            self.view_pane.enabled = (selected is not None)
            self.view_pane.default_view = selected.default_view.id if selected.default_view else ""
            self.view_pane.selected_view = selected.current_view.id if selected.current_view else ""
            self.help_pane.help_id = selected.operation.id
        else:
            self.view_pane.enabled = False
            
    @on_trait_change('view_pane.selected_view', post_init = True)
    def _on_select_view(self, view_id):
        
        if not view_id:
            return
        
        # if we already have an instantiated view object, find it
        try:
            self.model.selected.current_view = next((x for x in self.model.selected.views if x.id == view_id))
        except StopIteration:
            # else make the new view
            plugin = next((x for x in self.view_plugins if x.view_id == view_id))
            view = plugin.get_view()
            self.model.selected.views.append(view)
            self.model.selected.current_view = view
            
        self.help_pane.help_id = view_id
    
    def add_operation(self, op_id):
        # first, find the matching plugin
        plugin = next((x for x in self.op_plugins if x.id == op_id))
        
        # next, get an operation
        op = plugin.get_operation()
        
        # make a new workflow item
        wi = WorkflowItem(operation = op,
                          deletable = (op_id != 'edu.mit.synbio.cytoflowgui.op_plugins.import'))
        
        # if the op has a default view, add it to the wi
        try:
            wi.default_view = op.default_view()
            wi.views.append(wi.default_view)
            wi.current_view = wi.default_view
        except AttributeError:
            pass
        
        # figure out where to add it
        if self.model.selected:
            idx = self.model.workflow.index(self.model.selected) + 1
        else:
            idx = len(self.model.workflow)
             
        # the add_remove_items handler takes care of updating the linked list
        self.model.workflow.insert(idx, wi)
        
        # and make sure to actually select the new wi
        self.model.selected = wi
        
        
class FlowTaskPlugin(Plugin):
    """
    An Envisage plugin wrapping FlowTask
    """

    # Extension point IDs.
    PREFERENCES       = 'envisage.preferences'
    PREFERENCES_PANES = 'envisage.ui.tasks.preferences_panes'
    TASKS             = 'envisage.ui.tasks.tasks'
    
    # these need to be declared in a Plugin instance; we pass them to
    # the task instance thru its factory, below.
    op_plugins = ExtensionPoint(List(IOperationPlugin), OP_PLUGIN_EXT)
    view_plugins = ExtensionPoint(List(IViewPlugin), VIEW_PLUGIN_EXT)
    
    debug = Bool(False)
    remote_connection = Any

    #### 'IPlugin' interface ##################################################

    # The plugin's unique identifier.
    id = 'edu.mit.synbio.cytoflow'

    # The plugin's name (suitable for displaying to the user).
    name = 'Cytoflow'

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
        from cytoflow import __version__ as cf_version

        return [TaskFactory(id = 'edu.mit.synbio.cytoflow.flow_task',
                            name = 'Cytometry analysis',
                            factory = lambda **x: FlowTask(application = self.application,
                                                           op_plugins = self.op_plugins,
                                                           view_plugins = self.view_plugins,
                                                           model = Workflow(self.remote_connection,
                                                                            version = cf_version,
                                                                            debug = self.debug),
                                                           **x))]
