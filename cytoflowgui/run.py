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

try:
    import faulthandler       # @UnresolvedImport
    faulthandler.enable()     # @UndefinedVariable
except:
    # if there's no console, this fails
    pass

import sys, multiprocessing, logging, traceback, threading, argparse

logger = logging.getLogger(__name__)

def log_notification_handler(_, trait_name, old, new):
    
    (exc_type, exc_value, tb) = sys.exc_info()
    logger.debug('Exception occurred in traits notification '
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
    logger.debug("Global exception: {0}\n{1}: {2}".format(tb_str, typ, val))
    
    tb_str = traceback.format_tb(tb)[-1]
    logging.error("Error: {0}: {1}\nLocation: {2}Thread: Main"
                  .format(typ, val, tb_str))
                         
def run_gui():
    try:
        # if we're running as a one-click from a MacOS app,
        # we need to reset the working directory
        import os; os.chdir(sys._MEIPASS)  # @UndefinedVariable
    except:
        # if we're not running as a one-click, fail gracefully
        pass

    # this is ridiculous, but here's the situation.  Qt5 now uses Chromium
    # as their web renderer.  Chromium needs OpenGL.  if you don't
    # initialize OpoenGL here, things crash on some platforms.
    
    # so now i guess we depend on opengl too. 
    
    from OpenGL import GL  # @UnresolvedImport @UnusedImport

    # need to import these before a QCoreApplication is instantiated.  and that seems
    # to happen in .... 'import cytoflow' ??
    import pyface.qt.QtWebKit  # @UnusedImport
   
    # take care of the 3 places in the cytoflow module that
    # need different behavior in a GUI
    import cytoflow
    cytoflow.RUNNING_IN_GUI = True
            
    # check that we're using the right Qt API
    from pyface.qt import qt_api

    cmd_line = " ".join(sys.argv)
    
    if qt_api == "pyside":
        print("Cytoflow uses PyQT; but it is trying to use PySide instead.")
        print(" - Make sure PyQT is installed.")
        print(" - If both are installed, and you don't need both, uninstall PySide.")
        print(" - If you must have both installed, select PyQT by setting the")
        print("   environment variable QT_API to \"pyqt5\"")
        print("   * eg, on Linux, type on the command line:")
        print("     QT_API=\"pyqt5\" " + cmd_line)
        print("   * on Windows, try: ")
        print("     setx QT_API \"pyqt5\"")

        sys.exit(1)
    
    # parse args
    parser = argparse.ArgumentParser(description = 'Cytoflow GUI')
    parser.add_argument("--debug", action = 'store_true')
    parser.add_argument("filename", nargs='?', default = "")
    
    args = parser.parse_args()
    
    # start the remote process

    remote_process, remote_workflow_connection, remote_canvas_connection, queue_listener = start_remote_process()
    
    # getting real tired of the matplotlib deprecation warnings
    import warnings
    warnings.filterwarnings('ignore', '.*is deprecated and replaced with.*')
    
    # if we're frozen, add _MEIPASS to the pyface search path for icons etc
    if getattr(sys, 'frozen', False):
        from pyface.resource_manager import resource_manager
        resource_manager.extra_paths.append(sys._MEIPASS)    # @UndefinedVariable
        
    # these three lines stop pkg_resources from trying to load resources
    # from the __main__ module, which is frozen (and thus not loadable.)
    from pyface.image_resource import ImageResource
    icon = ImageResource('icon')
    icon.search_path = []
    
    # monkey patch the resource manager to use SVGs for icons
    import pyface.resource.resource_manager
    pyface.resource.resource_manager.ResourceManager.IMAGE_EXTENSIONS.append('.svg')
    
    # monkey patch checklist editor to stop lowercasing
    import traitsui.qt4.check_list_editor  # @UnusedImport
    traitsui.qt4.check_list_editor.capitalize = lambda s: s
    
    # define and install a message handler for Qt errors
    from traits.api import push_exception_handler
                             
    def QtMsgHandler(msg_type, msg_context, msg_string):
        # Convert Qt msg type to logging level
        log_level = [logging.DEBUG,
                     logging.WARN,
                     logging.ERROR,
                     logging.FATAL] [ int(msg_type) ]
        logging.log(log_level, 'Qt message: ' + msg_string)
        
    from pyface.qt.QtCore import qInstallMessageHandler  # @UnresolvedImport
    qInstallMessageHandler(QtMsgHandler)
    
    # install a global (gui) error handler for traits notifications
    push_exception_handler(handler = log_notification_handler,
                           reraise_exceptions = False, 
                           main = True)
    
    sys.excepthook = log_excepthook
    
    # Import, then load, the envisage plugins
    
    from envisage.core_plugin import CorePlugin
    from envisage.ui.tasks.tasks_plugin import TasksPlugin
    
    from cytoflowgui.flow_task import FlowTaskPlugin
    #from cytoflowgui.tasbe_task import TASBETaskPlugin
    #from cytoflowgui.export_task import ExportFigurePlugin
    from cytoflowgui.cytoflow_application import CytoflowApplication
    #from cytoflowgui.op_plugins.import_op import ImportPlugin
    #from cytoflowgui.op_plugins.threshold import ThresholdPlugin
    from cytoflowgui.op_plugins import (ImportPlugin, 
                                        ThresholdPlugin,
                                        RangePlugin, 
                                        QuadPlugin,
                                        Range2DPlugin, 
                                        PolygonPlugin, 
                                        BinningPlugin,
                                        GaussianMixture1DPlugin, 
                                        GaussianMixture2DPlugin,
                                        DensityGatePlugin, 
                                        BleedthroughLinearPlugin,
                                        BeadCalibrationPlugin, 
                                        AutofluorescencePlugin,
                                        #ColorTranslationPlugin, 
                                        #TasbePlugin, 
                                        ChannelStatisticPlugin,
                                        TransformStatisticPlugin,
                                        RatioPlugin,
                                        FlowPeaksPlugin,
                                        KMeansPlugin,
                                        PCAPlugin)
    
    from cytoflowgui.view_plugins import (HistogramPlugin, 
                                          Histogram2DPlugin, 
                                          ScatterplotPlugin,
                                          BarChartPlugin,
                                          Stats1DPlugin, 
                                          Kde1DPlugin, 
                                          Kde2DPlugin,
                                          ViolinPlotPlugin,
                                          TablePlugin, 
                                          Stats2DPlugin, 
                                          DensityPlugin,
                                          ParallelCoordinatesPlugin,
                                          RadvizPlugin)

    plugins = [CorePlugin(), TasksPlugin(), FlowTaskPlugin()]#, TASBETaskPlugin(),
               #ExportFigurePlugin()]    

    # ordered as we want them to show up in the toolbar    
    view_plugins = [HistogramPlugin(),
                    ScatterplotPlugin(),
                    Histogram2DPlugin(),
                    DensityPlugin(),
                    Kde1DPlugin(),
                    Kde2DPlugin(),
                    RadvizPlugin(),
                    ParallelCoordinatesPlugin(),
                    ViolinPlotPlugin(),
                    BarChartPlugin(),
                    Stats1DPlugin(),
                    Stats2DPlugin(),
                    TablePlugin()]
    
    plugins.extend(view_plugins)
    
    op_plugins = [ImportPlugin(),
                  ThresholdPlugin(),
                  RangePlugin(),
                  QuadPlugin(),
                  Range2DPlugin(),
                  PolygonPlugin(),
                  ChannelStatisticPlugin(),
                  TransformStatisticPlugin(),
                  RatioPlugin(),
                  BinningPlugin(),
                  GaussianMixture1DPlugin(),
                  GaussianMixture2DPlugin(),
                  DensityGatePlugin(),
                  KMeansPlugin(),
                  FlowPeaksPlugin(),
                  PCAPlugin(),
                  AutofluorescencePlugin(),
                  BleedthroughLinearPlugin(),
                  BeadCalibrationPlugin()]
                  #ColorTranslationPlugin(),
                  #TasbePlugin()]

    plugins.extend(op_plugins)
    
    # start the app

    app = CytoflowApplication(id = 'edu.mit.synbio.cytoflow',
                              plugins = plugins,
                              icon = icon,
                              remote_process = remote_process,
                              remote_workflow_connection = remote_workflow_connection,
                              remote_canvas_connection = remote_canvas_connection,
                              filename = args.filename,
                              debug = args.debug)

    from pyface.qt import QtGui
    QtGui.QApplication.instance().setStyle(QtGui.QStyleFactory.create('Fusion'))

    app.run()

    remote_process.join()
    queue_listener.stop()
    logging.shutdown()
    

        
def monitor_remote_process(proc):
    proc.join()
    if proc.exitcode:
        logging.error("Remote process exited with {}".format(proc.exitcode))
    

def start_remote_process():

        # communications channels
        parent_workflow_conn, child_workflow_conn = multiprocessing.Pipe()  
        parent_mpl_conn, child_matplotlib_conn = multiprocessing.Pipe()
        running_event = multiprocessing.Event()

        # logging
        from logging.handlers import QueueListener
        from cytoflowgui.utility import CallbackHandler
        log_q = multiprocessing.Queue()
        def handle(record):
            logger = logging.getLogger(record.name)
            if logger.isEnabledFor(record.levelno):
                logger.handle(record)
                
        handler = CallbackHandler(handle)
        queue_listener = QueueListener(log_q, handler)
        queue_listener.start()
   
        remote_process = multiprocessing.Process(target = remote_main,
                                                 name = "remote process",
                                                 args = [parent_workflow_conn,
                                                         parent_mpl_conn,
                                                         log_q,
                                                         running_event])
        
        remote_process.daemon = True
        remote_process.start() 
        running_event.wait()
        
        remote_process_thread = threading.Thread(target = monitor_remote_process,
                                                 name = "monitor remote process",
                                                 args = [remote_process])
        remote_process_thread.daemon = True
        remote_process_thread.start()
        
        return (remote_process, child_workflow_conn, child_matplotlib_conn, queue_listener)
    

def remote_main(parent_workflow_conn, parent_mpl_conn, log_q, running_event):
    # this should only ever be main method after a spawn() call 
    # (not fork). So we should have a fresh logger to set up.
        
    # messages that end up at the root logger to go log_q
    from logging.handlers import QueueHandler
    h = QueueHandler(log_q) 
    logging.getLogger().addHandler(h)
    
    # make sure the root logger has a level of DEBUG -- we'll sort out what
    # to show or not on the local logger
    logging.getLogger().setLevel(logging.DEBUG)
    
    # We want matplotlib to use our backend .... in both the GUI and the
    # remote process.  Must be called BEFORE cytoflow is imported
    
    import matplotlib
    matplotlib.use('module://cytoflowgui.matplotlib_backend_remote')
    
    # start threads
    
    from traits.api import push_exception_handler    
    from cytoflowgui.workflow import RemoteWorkflow
    
    # install a global (gui) error handler for traits notifications
    push_exception_handler(handler = log_notification_handler,
                           reraise_exceptions = False,
                           main = True)
    
    sys.excepthook = log_excepthook
    
    # take care of the 3 places in the cytoflow module that
    # need different behavior in a GUI
    import cytoflow
    cytoflow.RUNNING_IN_GUI = True
    
    running_event.set()
    RemoteWorkflow().run(parent_workflow_conn, parent_mpl_conn)

if __name__ == '__main__':
    multiprocessing.freeze_support()
    multiprocessing.set_start_method('spawn')
    run_gui()
