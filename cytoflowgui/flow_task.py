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

"""
Created on Feb 11, 2015

@author: brian
"""

import os.path, webbrowser, pathlib

import yaml.parser

from traits.api import Instance, List, Str, on_trait_change
from pyface.tasks.api import Task, TaskLayout, PaneItem, VSplitter
from pyface.tasks.action.api import SMenu, SMenuBar, SToolBar, TaskAction, TaskToggleGroup
from pyface.api import (FileDialog, ImageResource, AboutDialog, information, 
                        confirm, OK, YES, NO, ConfirmationDialog, warning,
                        error)
from envisage.api import Plugin, ExtensionPoint, contributes_to
from envisage.ui.tasks.api import TaskFactory

from cytoflowgui.workflow_pane import WorkflowDockPane
from cytoflowgui.view_pane import ViewDockPane, PlotParamsPane
from cytoflowgui.help_pane import HelpDockPane
from cytoflowgui.workflow import Workflow
from cytoflowgui.op_plugins import IOperationPlugin, ImportPlugin, OP_PLUGIN_EXT
from cytoflowgui.view_plugins import IViewPlugin, VIEW_PLUGIN_EXT
from cytoflowgui.workflow_item import WorkflowItem
from cytoflowgui.util import DefaultFileDialog
from cytoflowgui.serialization import save_yaml, load_yaml, save_notebook

from cytoflowgui.mailto import mailto

class FlowTask(Task):
    """
    classdocs
    """
    
    id = "edu.mit.synbio.cytoflowgui.flow_task"
    name = "Cytometry analysis"
    
    # the main workflow instance.
    model = Instance(Workflow)
        
    # the center pane
    workflow_pane = Instance(WorkflowDockPane)
    view_pane = Instance(ViewDockPane)
    help_pane = Instance(HelpDockPane)
    plot_params_pane = Instance(PlotParamsPane)
    
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
                        SMenu(TaskToggleGroup(),
                              id = 'View', name = '&View'),
                        SMenu(TaskAction(name = 'Online documentation...',
                                         method = 'on_docs'),
                                         TaskAction(name = 'Report a problem....',
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
                                       image=ImageResource('jupyter')),
                           TaskAction(method = "on_calibrate",
                                      name = "Calibrate FCS...",
                                      tooltip = "Calibrate FCS files",
                                      image = ImageResource('tasbe')),
                           TaskAction(method = 'on_problem',
                                      name = "Report a bug...",
                                      tooltib = "Report a bug",
                                      image = ImageResource('bug')))]
#                            TaskAction(method='on_prefs',
#                                       name = "Prefs",
#                                       tooltip='Preferences',
#                                       image=ImageResource('prefs')),
    
    # the file to save to if the user clicks "save" and has already clicked
    # "open" or "save as".
    filename = Str
        
    def initialized(self):
        if self.filename:
            self.open_file(self.filename)

        
    def activated(self):
        
        # if we're coming back from the TASBE task, re-load the saved
        # workflow
        if self.model.backup_workflow:
            self.model.workflow = self.model.backup_workflow
            self.model.backup_workflow = []
            return
        
        # else, set up a new workflow
        # add the import op
        if not self.model.workflow:
            self.add_operation(ImportPlugin().id) 
            self.model.selected = self.model.workflow[0]
                    
        self.model.modified = False
    
    def _default_layout_default(self):
        return TaskLayout(left = VSplitter(PaneItem("edu.mit.synbio.cytoflowgui.workflow_pane", width = 350),
                                           PaneItem("edu.mit.synbio.cytoflowgui.help_pane", width = 350, height = 350)),
                          right = VSplitter(PaneItem("edu.mit.synbio.cytoflowgui.view_traits_pane", width = 350),
                                            PaneItem("edu.mit.synbio.cytoflowgui.params_pane", width = 350, height = 350)),
                          top_left_corner = 'left',
                          bottom_left_corner = 'left',
                          top_right_corner = 'right',
                          bottom_right_corner = 'right')
     
    def create_central_pane(self):   
        # set the toolbar image size
        # this isn't really the right place for this, but it's the only
        # place control passes back to user code before the toolbar
        # is created.
        
        dpi = self.window.control.physicalDpiX()
        self.tool_bars[0].image_size = (int(0.4 * dpi), int(0.4 * dpi))
        return self.application.plot_pane
     
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
        
        self.plot_params_pane = PlotParamsPane(model = self.model,
                                               task = self)
        
        return [self.workflow_pane, self.view_pane, self.help_pane, self.plot_params_pane]
        
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
            

    def open_file(self, path):
        
        try:
            new_workflow = load_yaml(path)

            # a few things to take care of when reloading.
            # we do this in the try block to catch people who
            # load valid YAML files that aren't from cytoflow.
            
            for wi_idx, wi in enumerate(new_workflow):
                
                # get wi lock
                wi.lock.acquire()
                
                # clear the wi status
                wi.status = "loading"
    
                # re-link the linked list.
                if wi_idx > 0:
                    wi.previous_wi = new_workflow[wi_idx - 1]
                
                if wi_idx < len(new_workflow) - 1:
                    wi.next_wi = new_workflow[wi_idx + 1]

        except yaml.parser.ParserError as e:
            error(None,
                  "Parser error loading {} -- is it a Cytoflow file?\n\n{}"
                  .format(path, str(e)))
            return
        except Exception as e:
            error(None,
                  "{} loading {} -- is it a Cytoflow file?\n\n{}"
                  .format(e.__class__.__name__, path, str(e)))
            return
        
        # check that the FCS files are all there
        
        wi = new_workflow[0]
        assert(wi.operation.id == "edu.mit.synbio.cytoflow.operations.import")
        missing_tubes = 0
        for tube in wi.operation.tubes:
            file = pathlib.Path(tube.file)
            if not file.exists():
                missing_tubes += 1
                
        if missing_tubes == len(wi.operation.tubes):
            warning(self.window.control,
                    "Cytoflow couldn't find any of the FCS files from that "
                    "workflow.  If they've been moved, please open one FCS "
                    "file to show Cytoflow where they've been moved to.")
            
            dialog = FileDialog(parent = self.window.control, 
                                action = 'open',
                                wildcard = (FileDialog.create_wildcard("FCS files", "*.fcs *.lmd")))  # @UndefinedVariable
            
            if dialog.open() == OK:
                # find the "best" file match -- ie, the one with the longest
                # tail match
                fcs_path = pathlib.Path(dialog.path).parts
                best_path_len = -1
                                
                for tube in wi.operation.tubes:
                    tube_path = pathlib.Path(tube.file).parts
                    
                    for i in range(len(fcs_path)):
                        if list(reversed(fcs_path))[:i] == list(reversed(tube_path))[:i] and i > best_path_len:
                            best_path_len = i
                            
                if best_path_len >= 0:
                    for tube in wi.operation.tubes:
                        tube_path = pathlib.Path(tube.file).parts
                        new_path = fcs_path[:-1 * best_path_len] + tube_path[-1 * best_path_len :]
                        tube.file = str(pathlib.Path(*new_path))
                        
        elif missing_tubes > 0:
            warning(self.window.control,
                    "Cytoflow couldn't find some of the FCS files from that "
                    "workflow.  You'll need to re-load them from the Import "
                    "operation.")

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
            
        ret = confirm(parent = None,
                      message = "Do you want to execute the workflow now?",
                      title = "Run workflow?")
        
        if ret == YES:
            self.model.run_all()

        
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
        task = next(x for x in self.window.tasks if x.id == 'edu.mit.synbio.cytoflowgui.export_task')
        self.window.activate_task(task)        


    def on_calibrate(self):
        task = next(x for x in self.window.tasks if x.id == 'edu.mit.synbio.cytoflowgui.tasbe_task')
        self.window.activate_task(task)
        
            
    def on_notebook(self):
        """
        Shows a dialog to export the workflow to an Jupyter notebook
        """

        dialog = DefaultFileDialog(parent = self.window.control,
                                   action = 'save as',
                                   default_suffix = "ipynb",
                                   wildcard = (FileDialog.create_wildcard("Jupyter notebook", "*.ipynb") + ';' + #@UndefinedVariable  
                                               FileDialog.create_wildcard("All files", "*")))  # @UndefinedVariable
        if dialog.open() == OK:
            save_notebook(self.model.workflow, dialog.path)

    
    def on_prefs(self):
        pass
    
    def on_docs(self):
        webbrowser.open_new_tab("https://cytoflow.readthedocs.io/en/stable/manual.html")

    
    def on_problem(self):

        log = str(self._get_package_versions()) + "\n" + self.application.application_log.getvalue()
        
        msg = "The best way to report a problem is send an application log to " \
              "the developer.  You can do so by either sending me an email " \
              "with the log in it, or saving the log to a file and filing a " \
              "new issue on GitHub at " \
              "https://github.com/bpteague/cytoflow/issues/new" 
        
        dialog = ConfirmationDialog(message = msg,
                                    informative = "Which would you like to do?",
                                    yes_label = "Send an email...",
                                    no_label = "Save to a file...")
                
        if dialog.open() == NO:
            dialog = DefaultFileDialog(parent = self.window.control,
                                       action = 'save as', 
                                       default_suffix = "log",
                                       wildcard = (FileDialog.create_wildcard("Log files", "*.log") + ';' + #@UndefinedVariable  
                                                   FileDialog.create_wildcard("All files", "*")))                    #@UndefinedVariable  
            
            if dialog.open() == OK:
                with open(dialog.path, 'w') as f:
                    f.write(log)
                  
                webbrowser.open_new_tab("https://github.com/bpteague/cytoflow/issues/new")
                  
            return
        
        information(None, "I'll now try to open your email client and create a "
                    "new message to the developer.  Debugging logs are "
                    "attached.  Please fill out the template bug report and " 
                    "send -- thank you for reporting a bug!")

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

        mailto("bpteague@gmail.com", 
               subject = "Cytoflow bug report",
               body = body)
    
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
        from statsmodels import __version__ as stats_version
        from pyface import __version__ as pyf_version
        from envisage import __version__ as env_version
        from traits import __version__ as trt_version
        from traitsui import __version__ as trt_ui_version
        from yapf import __version__ as yapf_version
        from nbformat import __version__ as nb_version
        from yaml import __version__ as yaml_version
        
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
                "statsmodels" : stats_version,
                "pyface" : pyf_version,
                "envisage" : env_version,
                "traits" : trt_version,
                "traitsui" : trt_ui_version,
                "nbformat" : nb_version,
                "yapf" : yapf_version,
                "yaml" : yaml_version}
        
        
    def on_about(self):
        versions = self._get_package_versions()
        text = ["<b>Cytoflow {0}</b>".format(versions['cytoflow']),
                "<p>"]
        
        ver_text = ["{0} {1}".format(key, value) for key, value in versions.items()]
        
        text.extend(ver_text)
        
        text.extend(["Icons from the <a href=http://tango.freedesktop.org>Tango Desktop Project</a>",
                "<a href=https://thenounproject.com/search/?q=setup&i=14287>Settings icon</a> by Paulo Sa Ferreira from <a href=https://thenounproject.com>The Noun Project</a>",
                "<a href=https://thenounproject.com/search/?q=processing&i=849831>Processing icon</a> by Gregor Cresnar from <a href=https://thenounproject.com>The Noun Project</a>",
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
        return [TaskFactory(id = 'edu.mit.synbio.cytoflowgui.flow_task',
                            name = 'Cytometry analysis',
                            factory = lambda **x: FlowTask(application = self.application,
                                                           op_plugins = self.op_plugins,
                                                           view_plugins = self.view_plugins,
                                                           model = self.application.model,
                                                           filename = self.application.filename,
                                                           **x))]
