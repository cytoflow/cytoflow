#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2022
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
cytoflowgui.flow_task
---------------------

The main `pyface.tasks.task.Task`, and its associated `pyface.tasks.i_task_pane.ITaskPane`
and `envisage.plugin.Plugin`. 

- `FlowTask` -- the `pyface.tasks.task.Task` that allows the user to analyze flow data.

- `FlowTaskPane` -- the central `pyface.tasks.i_task_pane.ITaskPane` that contains the
  current `IWorkflowView`.
  
- `FlowTaskPlugin` -- the `envisage.plugin.Plugin` that provides the task factory and
  preferences pane.
"""

import os.path, webbrowser, pathlib, sys, warnings

import yaml.parser
from textwrap import dedent

import nbformat as nbf
from yapf.yapflib.yapf_api import FormatCode

from traits.api import Instance, Str, List, on_trait_change, provides, DelegatesTo
from pyface.tasks.api import ITaskPane, TaskPane, Task, TaskLayout, PaneItem, VSplitter  # @UnresolvedImport
from pyface.tasks.action.api import SMenu, SMenuBar, SToolBar, TaskAction, TaskToggleGroup, SGroup
# from pyface.tasks.action.dock_pane_toggle_group import DockPaneToggleGroup, DockPaneToggleAction, ActionItem
from pyface.api import (FileDialog, ImageResource, AboutDialog,  # @UnresolvedImport
                        confirm, OK, YES, ConfirmationDialog, warning,  # @UnresolvedImport
                        error)  # @UnresolvedImport
from pyface.qt import QtGui

from envisage.ui.tasks.api import TaskFactory
from envisage.ui.tasks.action.preferences_action import PreferencesAction
from envisage.api import Plugin

from .workflow_pane import WorkflowDockPane
from .view_pane import ViewDockPane, PlotParamsPane
from .help_pane import HelpDockPane
from .experiment_pane import ExperimentBrowserDockPane
from .matplotlib_backend_local import FigureCanvasQTAggLocal
from .workflow import LocalWorkflow
from .workflow_controller import WorkflowController
from .util import DefaultFileDialog
from .workflow.serialization import save_yaml, load_yaml


@provides(ITaskPane)
class FlowTaskPane(TaskPane):
    """
    The center pane for the UI; contains the matplotlib canvas for plotting
    data views.
    """
    
    id = 'edu.mit.synbio.cytoflow.flow_task_pane'
    name = 'Cytometry Data Viewer'
    
    model = Instance(LocalWorkflow)
    """The shared `LocalWorkflow` model. Set by the task factory"""
    
    handler = Instance(WorkflowController)
    """The shared `WorkflowController`. Set by the task factory"""
    
    layout = Instance(QtGui.QVBoxLayout)                    # @UndefinedVariable
    """The main layout"""
    
    canvas = Instance(FigureCanvasQTAggLocal)
    """The local `matplotlib` canvas, an instance of `FigureCanvasQTAggLocal`"""
        
    def create(self, parent):      
        """Create a layout for the tab widget and the main view"""
        
        self.layout = layout = QtGui.QVBoxLayout()          # @UndefinedVariable
        self.control = QtGui.QWidget()                      # @UndefinedVariable
        self.control.setLayout(layout)
        
        tabs_ui = self.handler.edit_traits(view = 'selected_view_plot_name_view',
                                           context = self.model,
                                           kind = 'subpanel',
                                           parent = parent)
         
        self.layout.addWidget(tabs_ui.control) 
        
        # usually we would add the main plot here -- but a Qt widget
        # can only be part of one layout at a time.  so instead we
        # need to create that layout here, then dynamically add
        # the canvas when the task is activated (see activate(), below)
        
        
    def activate(self):
        """Activate this task by adding the canvas widget to the task pane layout"""
        if self.canvas.layout():
            self.canvas.layout().removeWidget(self.canvas)
        self.layout.addWidget(self.canvas)


class FlowTask(Task):
    """
    This class coordinates all the views and panels on the main model. Thus, you
    can think of it as an MVC controller - this is where all the UI handlers for
    things like the menu and menu bar buttons are.
    """
    
    id = "edu.mit.synbio.cytoflowgui.flow_task"
    """This tasks's GUID"""
    
    name = "Cytometry analysis"
    """This task's name"""
    
    # the main workflow instance.
    model = Instance(LocalWorkflow)
    """The shared `LocalWorkflow` model"""
    
    # the handler that connects it to various views
    handler = Instance(WorkflowController)
    """The shared `WorkflowController` controller"""
        
    # side panes
    workflow_pane = Instance(WorkflowDockPane)
    """The workflow dock pane"""
    
    view_pane = Instance(ViewDockPane)
    """The view configuration dock pane"""
    
    browser_pane = Instance(ExperimentBrowserDockPane)
    """The experiment browser dock pane"""
    
    help_pane = Instance(HelpDockPane)
    """The help dock pane"""
    
    plot_params_pane = Instance(PlotParamsPane)
    """The plot parameters dock pane"""
    
    # plugin lists, to setup the interface
    op_plugins = DelegatesTo('handler')
    """The operation plugins"""
    
    view_plugins = DelegatesTo('handler')
    """The view plugins"""
    
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
                              PreferencesAction(),
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
    """The menu bar schema"""
    
    tool_bars = [ SToolBar(SGroup(TaskAction(method='on_new',
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
                                  TaskAction(method = 'on_problem',
                                             name = "Report a bug...",
                                             tooltib = "Report a bug",
                                             image = ImageResource('bug')),
                                  PreferencesAction(image = ImageResource('prefs'))),
                           SGroup(TaskAction(method = 'on_toggle_workflow',
                                             name = 'Workflow',
                                             tooltip = 'Toggle workflow pane',
                                             image = ImageResource('workflow')),
                                  TaskAction(method = 'on_toggle_view',
                                                    name = 'View Properties',
                                                    tooltip = 'Toggle view properties pane',
                                                    image = ImageResource('view_pane')),
                                  TaskAction(method = 'on_toggle_plot_params',
                                                    name = 'Plot Parameters',
                                                    tooltip = 'Toggle plot parameters pane',
                                                    image = ImageResource('plot_params')),
                                  TaskAction(method = 'on_toggle_browser',
                                                    name = 'Browser',
                                                    tooltip = 'Toggle experiment browser pane',
                                                    image = ImageResource('browser')),
                                  TaskAction(method = 'on_toggle_help',
                                                    name = 'Help',
                                                    tooltip = 'Toggle help pane',
                                                    image = ImageResource('help'))))]
    """The tool bar schema"""

    
    filename = Str
    """
    The file to save to if the user clicks "save" and has already clicked
    "open" or "save as".
    """
        
    def initialized(self):
        """
        Called when the task is about to be activated in a TaskWindow for
        the first time.  Called before `activated`. If a filename was given
        on the command line, load it.
        """
        
        if self.filename:
            self.open_file(self.filename)

        
    def activated(self):
        """ 
        Called after the task has been activated in a TaskWindow.  Initialize the
        model with an import operation and activate the central pane.
        """
    
        # add the import op
        if not self.model.workflow:
            self.handler.add_operation('edu.mit.synbio.cytoflow.operations.import') 
    
        self.window.central_pane.activate()
    
        self.model.modified = False
    
    def _default_layout_default(self):
        """
        Returns the default layout for the dock panes.
        """
        
        pane_size = 400
        return TaskLayout(left = VSplitter(PaneItem("edu.mit.synbio.cytoflowgui.workflow_pane", width = pane_size),
                                           PaneItem("edu.mit.synbio.cytoflowgui.experiment_pane", width = pane_size),
                                           PaneItem("edu.mit.synbio.cytoflowgui.help_pane", width = pane_size, height = pane_size)),
                          right = VSplitter(PaneItem("edu.mit.synbio.cytoflowgui.view_traits_pane", width = pane_size),
                                            PaneItem("edu.mit.synbio.cytoflowgui.params_pane", width = pane_size, height = pane_size)),
                          top_left_corner = 'left',
                          bottom_left_corner = 'left',
                          top_right_corner = 'right',
                          bottom_right_corner = 'right')
     
    def create_central_pane(self):  
        """
        Initialize the toolbar image size and return the central `FlowTaskPane`
        """
    
        # this isn't really the right place for this, but it's the only
        # place control passes back to user code before the toolbar
        # is created.
    
        self.tool_bars[0].image_size = (32, 32)
    
        return FlowTaskPane(canvas = self.application.canvas,
                            model = self.application.model, 
                            handler = self.handler)
             
    def create_dock_panes(self):
        """
        Create and initialize the dock panes
        """
                
        self.workflow_pane = WorkflowDockPane(model = self.model, 
                                              handler = self.handler,
                                              plugins = self.op_plugins,
                                              task = self)
        
        self.view_pane = ViewDockPane(model = self.model,
                                      handler = self.handler,
                                      plugins = self.view_plugins,
                                      task = self)
        
        self.plot_params_pane = PlotParamsPane(model = self.model,
                                               handler = self.handler)
        
        self.browser_pane = ExperimentBrowserDockPane(model = self.model,
                                                      handler = self.handler,
                                                      task = self)

        self.help_pane = HelpDockPane(model = self.model,
                                      view_plugins = self.view_plugins,
                                      op_plugins = self.op_plugins,
                                      task = self)
        
        return [self.workflow_pane, self.view_pane, self.plot_params_pane,
                self.browser_pane, self.help_pane, ]
        
    def on_new(self):
        """
        Create a new workflow when the "New..." button or menu item is clicked
        """
        
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
        self.handler.add_operation('edu.mit.synbio.cytoflow.operations.import')
        
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
        """
        Load a new workflow from a file
        """
        
        with warnings.catch_warnings(record = True) as w:
            try:
            
                new_workflow = load_yaml(path)
                
                if w:
                    warning(None, w[-1].message.__str__())
            
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
        
        # are we just running a smoke test?
        if 'startup_test' in new_workflow[0].metadata:
            def quit_app(app):
                app.exit(force = True)
                
            from pyface.timer.api import do_after  # @UnresolvedImport
            do_after(5*1000, quit_app, self.application)
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
            from cytoflowgui.utility.event_tracer import record_events 
            
            with record_events() as container:
                self.model.workflow = new_workflow
                                
            container.save_to_directory(os.getcwd()) 
        else:
            self.model.workflow = new_workflow
            self.model.modified = False
            
        for wi in self.model.workflow:
            wi.lock.release()
            
        if self.model.debug:
            self.model.run_all()
        else:
            ret = confirm(parent = None,
                          message = "Do you want to execute the workflow now?",
                          title = "Run workflow?")
            
            if ret == YES:
                self.model.run_all()
        
    def on_save(self):
        """ Save the workflow to the current filename  """
        if self.filename:
            save_yaml(self.model.workflow, self.filename)
            self.model.modified = False
        else:
            self.on_save_as()
            
    def on_save_as(self):
        """ Save the workflow to a different file"""
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
        Switch to the `ExportTask` task
        """
        
        task = next(x for x in self.window.tasks if x.id == 'edu.mit.synbio.cytoflowgui.export_task')
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
            self.save_notebook(self.model.workflow, dialog.path)

    
    def on_prefs(self):
        """
        Event handler for the "preferences" button -- currently, do nothing
        """
        pass
    
    
    def on_docs(self):
        """
        Event handler for the "Online documentation...." menu item.
        Opens a webbrowser to the online manual at readthedocs.io
        """
        
        webbrowser.open_new_tab("https://cytoflow.readthedocs.io/en/stable/manual.html")

    
    def on_problem(self):
        """
        Event handler for the bug report button & menu item.
        Saves the in-memory log to disk, then opens a webbrowser to the 
        new issue page on GitHub.
        """

        log = str(self._get_package_versions()) + "\n" + self.application.application_log.getvalue()
        
        msg = "The best way to report a problem is send an application log to " \
              "the developers.  If you click 'Yes' below, you will be given then " \
              "opportunity to save the log to a file and then file a " \
              "new issue on GitHub at " \
              "https://github.com/cytoflow/cytoflow/issues/new" 
        
        dialog = ConfirmationDialog(message = msg,
                                    informative = "Would you like to report an issue to the developers?")
                
        if dialog.open() == YES:
            dialog = DefaultFileDialog(parent = self.window.control,
                                       action = 'save as', 
                                       default_suffix = "log",
                                       wildcard = (FileDialog.create_wildcard("Log files", "*.log") + ';' + #@UndefinedVariable  
                                                   FileDialog.create_wildcard("All files", "*")))                    #@UndefinedVariable  
            
            if dialog.open() == OK:
                with open(dialog.path, 'w') as f:
                    f.write(log)
                  
                webbrowser.open_new_tab("https://github.com/cytoflow/cytoflow/issues/new")
                  
            return
        
        
    def on_toggle_workflow(self):
        """Toggle the visibility of the workflow pane"""
        self.workflow_pane.visible = not self.workflow_pane.visible
        
        
    def on_toggle_view(self):
        """Toggle the visibility of the view properties pane"""
        self.view_pane.visible = not self.view_pane.visible
        
        
    def on_toggle_plot_params(self):
        """Toggle the visibility of the plot parameters pane"""
        self.plot_params_pane.visible = not self.plot_params_pane.visible
        
        
    def on_toggle_browser(self):
        """Toggle the visiblity of the experiment browser pane"""
        self.browser_pane.visible = not self.browser_pane.visible
        
        
    def on_toggle_help(self):
        """Toggle the visiblity of the help pane"""
        self.help_pane.visible = not self.help_pane.visible
        
    
    def _get_package_versions(self):    
        from importlib.metadata import version as get_version
        cf_version = get_version('cytoflow')
        from fcsparser.fcsparser import __version__ as fcs_version
        pd_version = get_version('pandas')
        np_version = get_version('numpy')
        nxp_version = get_version('numexpr')
        btl_version = get_version('bottleneck')
        sns_version = get_version('seaborn')
        mpl_version = get_version('matplotlib')
        scipy_version = get_version('scipy')
        skl_version = get_version('scikit-learn')
        stats_version = get_version('statsmodels')
        pyf_version = get_version('pyface')
        env_version = get_version('envisage')
        trt_version = get_version('traits')
        trt_ui_version = get_version('traitsui')
        yapf_version = get_version('yapf')
        nb_version = get_version('nbformat')
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
        """
        Event handler for "About..." menu item.  Shows an about dialog box.
        """
        
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

    # Jupyter notebook serialization
    def save_notebook(self, workflow, path):
        """
        Saves the workflow to a Jupyter notebook.
        """
        
        nb = nbf.v4.new_notebook()
        
        # todo serialize here
        header = dedent("""\
            from cytoflow import *""")
        nb['cells'].append(nbf.v4.new_code_cell(header))
            
        for i, wi in enumerate(workflow):
            try:
                code = wi.operation.get_notebook_code(i)
                code = FormatCode(code, style_config = 'pep8')[0]
            except Exception as e:
                error(parent = None,
                      message = "Had trouble serializing the {} operation:\n{}"
                                .format(wi.operation.friendly_id,
                                        repr(e)))
            
            nb['cells'].append(nbf.v4.new_code_cell(code))
                        
            for view in wi.views:
                try:
                    code = view.get_notebook_code(i)
                    code = FormatCode(code, style_config = 'pep8')[0]
                except Exception as e:
                    error(parent = None,
                          message = "Had trouble serializing the {} view of the {} operation:\n{}"
                                     .format(view.friendly_id, 
                                             wi.operation.friendly_id,
                                             repr(e)))
                
                nb['cells'].append(nbf.v4.new_code_cell(code))
                
        with open(path, 'w') as f:
            nbf.write(nb, f)

        
class FlowTaskPlugin(Plugin):
    """
    An Envisage plugin wrapping FlowTask
    """

    # Extension point IDs.
    PREFERENCES       = 'envisage.preferences'
    PREFERENCES_PANES = 'envisage.ui.tasks.preferences_panes'
    TASKS             = 'envisage.ui.tasks.tasks' 
    
    #### 'IPlugin' interface ##################################################

    # The plugin's unique identifier.
    id = 'edu.mit.synbio.cytoflow'

    # The plugin's name (suitable for displaying to the user).
    name = 'Cytoflow'

    ###########################################################################
    # Protected interface.
    ###########################################################################

    preferences = List(contributes_to = PREFERENCES)
    def _preferences_default(self):
        filename = os.path.join(os.path.dirname(__file__), 'preferences.ini')
        return [ 'file://' + filename ]
    
    preferences_panes = List(contributes_to = PREFERENCES_PANES)
    def _preferences_panes_default(self):
        from .preferences import CytoflowPreferencesPane
        return [CytoflowPreferencesPane]

    tasks = List(contributes_to = TASKS)
    def _tasks_default(self):
        return [TaskFactory(id = 'edu.mit.synbio.cytoflowgui.flow_task',
                            name = 'Cytometry analysis',
                            factory = lambda **x: FlowTask(application = self.application,
                                                           model = self.application.model,
                                                           handler = self.application.controller,
                                                           filename = self.application.filename,
                                                           **x))]
