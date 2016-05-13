#!/usr/bin/env python2.7

# (c) Massachusetts Institute of Technology 2015-2016
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

import logging, sys, multiprocessing, StringIO, os

from traits.etsconfig.api import ETSConfig
ETSConfig.toolkit = 'qt4'

import matplotlib

# We want matplotlib to use our backend
matplotlib.use('module://cytoflowgui.matplotlib_backend')

from envisage.core_plugin import CorePlugin
from envisage.ui.tasks.tasks_plugin import TasksPlugin
from pyface.image_resource import ImageResource

from flow_task import FlowTaskPlugin
from cytoflow_application import CytoflowApplication
from op_plugins import ImportPlugin, ThresholdPlugin, RangePlugin, \
                       Range2DPlugin, PolygonPlugin, BinningPlugin
from view_plugins import HistogramPlugin, HexbinPlugin, ScatterplotPlugin, \
                         BarChartPlugin, Stats1DPlugin

import cytoflowgui.matplotlib_backend as mpl_backend
import cytoflowgui.workflow as workflow

import cytoflowgui.util as util

# from https://github.com/pyinstaller/pyinstaller/wiki/Recipe-Multiprocessing

# Module multiprocessing is organized differently in Python 3.4+
try:
    # Python 3.4+
    if sys.platform.startswith('win'):
        import multiprocessing.popen_spawn_win32 as forking
    else:
        import multiprocessing.popen_fork as forking
except ImportError:
    import multiprocessing.forking as forking

if sys.platform.startswith('win'):
    # First define a modified version of Popen.
    class _Popen(forking.Popen):
        def __init__(self, *args, **kw):
            if hasattr(sys, 'frozen'):
                # We have to set original _MEIPASS2 value from sys._MEIPASS
                # to get --onefile mode working.
                os.putenv('_MEIPASS2', sys._MEIPASS)
            try:
                super(_Popen, self).__init__(*args, **kw)
            finally:
                if hasattr(sys, 'frozen'):
                    # On some platforms (e.g. AIX) 'os.unsetenv()' is not
                    # available. In those cases we cannot delete the variable
                    # but only set it to the empty string. The bootloader
                    # can handle this case.
                    if hasattr(os, 'unsetenv'):
                        os.unsetenv('_MEIPASS2')
                    else:
                        os.putenv('_MEIPASS2', '')

    # Second override 'Popen' class with our modified version.
    forking.Popen = _Popen
                         
def run_gui():
    logging.basicConfig(level=logging.DEBUG)
    util.parent_log = StringIO.StringIO()
    log_handler = logging.StreamHandler(util.parent_log)
    log_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s:%(name)s:%(message)s"))
    logging.getLogger().addHandler(log_handler)
    
    debug = ("--debug" in sys.argv)

    plugins = [CorePlugin(), TasksPlugin(), FlowTaskPlugin(debug = debug),
               ImportPlugin(), ThresholdPlugin(), HistogramPlugin(),
               HexbinPlugin(), ScatterplotPlugin(), RangePlugin(),
               Range2DPlugin(), PolygonPlugin(), BarChartPlugin(), 
               Stats1DPlugin(), BinningPlugin()]
    
    app = CytoflowApplication(id = 'edu.mit.synbio.cytoflow',
                              plugins = plugins,
                              icon = ImageResource('icon'))
    app.run()
    
    logging.shutdown()
    
def remote_main(workflow_parent_conn, mpl_parent_conn):
    
    logging.basicConfig(level=logging.DEBUG)
    util.child_log = StringIO.StringIO()
    log_handler = logging.StreamHandler(util.child_log)
    log_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s:%(name)s:%(message)s"))
    logging.getLogger().addHandler(log_handler)
    
    # connect the remote pipes
    workflow.parent_conn = workflow_parent_conn
    mpl_backend.parent_conn = mpl_parent_conn
    
    # run the remote workflow
    workflow.RemoteWorkflow().run()


if __name__ == '__main__':
    multiprocessing.freeze_support()
    
    from pyface.qt import qt_api
    
    if qt_api == "pyside":
        print "Cytoflow uses PyQT; but it is trying to use PySide instead."
        print " - Make sure PyQT is installed."
        print " - If both are installed, and you don't need both, uninstall PySide."
        print " - If you must have both installed, select PyQT by setting the"
        print "   environment variable QT_API to \"pyqt\""
        print "   * eg, on Linux, type on the command line:"
        print "     QT_API=\"pyqt\" python run.py"
        print "   * on Windows, try: "
        print "     setx QT_API \"pyqt\""

        sys.exit(1)
        
    # set up the child process
    workflow_parent_conn, workflow_child_conn = multiprocessing.Pipe()
    mpl_parent_conn, mpl_child_conn = multiprocessing.Pipe()

    # connect the local pipes
    workflow.child_conn = workflow_child_conn       
    mpl_backend.child_conn = mpl_child_conn   

    # start the child process
    remote_process = multiprocessing.Process(target = remote_main,
                                             name = "remote",
                                             args = (workflow_parent_conn, 
                                                     mpl_parent_conn))
    remote_process.daemon = True
    remote_process.start()    
    
    run_gui()
