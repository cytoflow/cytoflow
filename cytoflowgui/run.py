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

try:
    import faulthandler       # @UnresolvedImport
    faulthandler.enable()     # @UndefinedVariable
except:
    # if there's no console, this fails
    pass

import sys, multiprocessing, logging, traceback, threading

from traits.etsconfig.api import ETSConfig
ETSConfig.toolkit = 'qt4'

def log_notification_handler(_, trait_name, old, new):
    
    (exc_type, exc_value, tb) = sys.exc_info()
    logging.debug('Exception occurred in traits notification '
                  'handler for object: %s, trait: %s, old value: %s, '
                  'new value: %s.\n%s\n' % ( object, trait_name, old, new,
                  ''.join( traceback.format_exception(exc_type, exc_value, tb) ) ) )

    err_string = traceback.format_exception_only(exc_type, exc_value)[0]
    err_loc = traceback.format_tb(tb)[-1]
    err_ctx = threading.current_thread().name
    
    logging.error("Error: {0}\nLocation: {1}Thread: {2}" \
                  .format(err_string, err_loc, err_ctx) )
    
def log_excepthook(typ, val, tb):
    tb_str = "".join(traceback.format_tb(tb))
    logging.debug("Global exception: {0}\n{1}: {2}"
                  .format(tb_str, typ, val))
    
    tb_str = traceback.format_tb(tb)[-1]
    logging.error("Error: {0}: {1}\nLocation: {2}Thread: Main"
                  .format(typ, val, tb_str))
                         
def run_gui():
    debug = ("--debug" in sys.argv)

    remote_process, remote_connection = start_remote_process(debug)
    
    # We want matplotlib to use our backend .... in both the GUI and the
    # remote process
    
    import matplotlib
    matplotlib.use('module://cytoflowgui.matplotlib_backend')
    
    # getting real tired of the matplotlib deprecation warnings
    import warnings
    warnings.filterwarnings('ignore', '.*is deprecated and replaced with.*')
    
    from traits.api import push_exception_handler
                             
    def QtMsgHandler(msg_type, msg_string):
        # Convert Qt msg type to logging level
        log_level = [logging.DEBUG,
                     logging.WARN,
                     logging.ERROR,
                     logging.FATAL] [ int(msg_type) ]
        logging.log(log_level, 'Qt message: ' + msg_string.decode('utf-8'))
    
    from envisage.core_plugin import CorePlugin
    from envisage.ui.tasks.tasks_plugin import TasksPlugin
    from pyface.image_resource import ImageResource
    
    from cytoflowgui.flow_task import FlowTaskPlugin
    from cytoflowgui.tasbe_task import TASBETaskPlugin
    from cytoflowgui.cytoflow_application import CytoflowApplication
    from cytoflowgui.op_plugins import (ImportPlugin, ThresholdPlugin, RangePlugin, QuadPlugin,
                            Range2DPlugin, PolygonPlugin, BinningPlugin,
                            GaussianMixture1DPlugin, GaussianMixture2DPlugin,
                            BleedthroughLinearPlugin, BleedthroughPiecewisePlugin,
                            BeadCalibrationPlugin, AutofluorescencePlugin,
                            ColorTranslationPlugin, TasbePlugin, 
                            ChannelStatisticPlugin, TransformStatisticPlugin, 
                            RatioPlugin, DensityGatePlugin, FlowPeaksPlugin,
                            KMeansPlugin, PCAPlugin)
    
    from cytoflowgui.view_plugins import (HistogramPlugin, Histogram2DPlugin, ScatterplotPlugin,
                              BarChartPlugin, Stats1DPlugin, Kde1DPlugin, Kde2DPlugin,
                              ViolinPlotPlugin, TablePlugin, Stats2DPlugin, DensityPlugin,
                              ParallelCoordinatesPlugin, RadvizPlugin)
    
    from cytoflow.utility.custom_traits import Removed, Deprecated
    Removed.gui = True
    Deprecated.gui = True
    
    from pyface.qt import qt_api

    cmd_line = " ".join(sys.argv)
    
    if qt_api == "pyside":
        print("Cytoflow uses PyQT; but it is trying to use PySide instead.")
        print(" - Make sure PyQT is installed.")
        print(" - If both are installed, and you don't need both, uninstall PySide.")
        print(" - If you must have both installed, select PyQT by setting the")
        print("   environment variable QT_API to \"pyqt\"")
        print("   * eg, on Linux, type on the command line:")
        print("     QT_API=\"pyqt\" " + cmd_line)
        print("   * on Windows, try: ")
        print("     setx QT_API \"pyqt\"")

        sys.exit(1)
        
    from pyface.qt.QtCore import qInstallMsgHandler  # @UnresolvedImport
    qInstallMsgHandler(QtMsgHandler)
    
    # if we're frozen, add _MEIPASS to the pyface search path for icons etc
    if getattr(sys, 'frozen', False):
        from pyface.resource_manager import resource_manager
        resource_manager.extra_paths.append(sys._MEIPASS)    # @UndefinedVariable


        
    # install a global (gui) error handler for traits notifications
    push_exception_handler(handler = log_notification_handler,
                           reraise_exceptions = debug, 
                           main = True)
    
    sys.excepthook = log_excepthook

    plugins = [CorePlugin(), TasksPlugin(), FlowTaskPlugin(), TASBETaskPlugin()]    
    
    # reverse of the order on the toolbar
    view_plugins = [TablePlugin(),
                    Stats2DPlugin(),
                    Stats1DPlugin(),
                    BarChartPlugin(),
                    ViolinPlotPlugin(),
#                     Kde2DPlugin(),    # disabled until we can make it faster
                    RadvizPlugin(),
                    ParallelCoordinatesPlugin(),
                    Kde1DPlugin(),
                    DensityPlugin(),
                    Histogram2DPlugin(),
                    ScatterplotPlugin(),
                    HistogramPlugin()]
    
    plugins.extend(view_plugins)
    
    op_plugins = [RatioPlugin(),
                  PCAPlugin(),
                  KMeansPlugin(),
                  FlowPeaksPlugin(),
                  DensityGatePlugin(),
                  TransformStatisticPlugin(),
                  ChannelStatisticPlugin(),
                  TasbePlugin(),
                  ColorTranslationPlugin(),
                  AutofluorescencePlugin(),
                  BeadCalibrationPlugin(),
#                   BleedthroughPiecewisePlugin(),
                  BleedthroughLinearPlugin(),
                  GaussianMixture2DPlugin(),
                  GaussianMixture1DPlugin(),
                  BinningPlugin(),
                  PolygonPlugin(),
                  QuadPlugin(),
                  Range2DPlugin(),
                  RangePlugin(),
                  ThresholdPlugin(),
                  ImportPlugin()]

    plugins.extend(op_plugins)
    
    # these two lines stop pkg_resources from trying to load resources
    # from the __main__ module, which is frozen (and thus not loadable.)
    icon = ImageResource('icon')
    icon.search_path = []

    app = CytoflowApplication(id = 'edu.mit.synbio.cytoflow',
                              plugins = plugins,
                              icon = icon,
                              remote_connection = remote_connection,
                              debug = debug)
    app.run()
    remote_process.join()
    logging.shutdown()
    
def start_remote_process(debug):

        # communications channels
        parent_workflow_conn, child_workflow_conn = multiprocessing.Pipe()  
        parent_mpl_conn, child_matplotlib_conn = multiprocessing.Pipe()
        log_q = multiprocessing.Queue()
        running_event = multiprocessing.Event()
                
        remote_process = multiprocessing.Process(target = remote_main,
                                                 name = "remote process",
                                                 args = [parent_workflow_conn,
                                                         parent_mpl_conn,
                                                         log_q,
                                                         running_event,
                                                         debug])
        
        remote_process.daemon = True
        remote_process.start() 
        running_event.wait()
        
        remote_process_thread = threading.Thread(target = monitor_remote_process,
                                                 name = "monitor remote process",
                                                 args = [remote_process])
        remote_process_thread.daemon = True
        remote_process_thread.start()
        
        return (remote_process, (child_workflow_conn, child_matplotlib_conn, log_q))
    
def remote_main(parent_workflow_conn, parent_mpl_conn, log_q, running_event, debug):
    # We want matplotlib to use our backend .... in both the GUI and the
    # remote process.  Must be called BEFORE cytoflow is imported
    
    import matplotlib
    matplotlib.use('module://cytoflowgui.matplotlib_backend')
    
    from traits.api import push_exception_handler    
    from cytoflowgui.workflow import RemoteWorkflow
    
    # install a global (gui) error handler for traits notifications
    push_exception_handler(handler = log_notification_handler,
                           reraise_exceptions = debug, 
                           main = True)
    
    sys.excepthook = log_excepthook
    
    running_event.set()
    RemoteWorkflow().run(parent_workflow_conn, parent_mpl_conn, log_q)
    
        
def monitor_remote_process(proc):
    proc.join()
    logging.error("Remote process exited with {}".format(proc.exitcode))

if __name__ == '__main__':
    multiprocessing.freeze_support()
    multiprocessing.set_start_method('spawn')
    run_gui()
