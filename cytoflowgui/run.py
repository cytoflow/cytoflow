"""
Created on Feb 11, 2015

@author: brian
"""

from traits.etsconfig.api import ETSConfig
ETSConfig.toolkit = 'qt4'

import logging

from envisage.core_plugin import CorePlugin
from envisage.ui.tasks.tasks_plugin import TasksPlugin

from flow_task import FlowTaskPlugin
from cytoflow_application import CytoflowApplication
from op_plugins import ImportPlugin, ThresholdPlugin, HLogPlugin, RangePlugin, \
                       Range2DPlugin, PolygonPlugin
from view_plugins import HistogramPlugin, HexbinPlugin, ScatterplotPlugin, \
                         BarChartPlugin, Stats1DPlugin

def run_gui(argv):
    
    logging.basicConfig(level=logging.DEBUG)
    
    debug = ("--debug" in argv)

    plugins = [CorePlugin(), TasksPlugin(), FlowTaskPlugin(debug = debug),
               ImportPlugin(), ThresholdPlugin(), HistogramPlugin(),
               HLogPlugin(), HexbinPlugin(), ScatterplotPlugin(), RangePlugin(),
               Range2DPlugin(), PolygonPlugin(), BarChartPlugin(), 
               Stats1DPlugin()]
    
    app = CytoflowApplication(id = 'edu.mit.synbio.cytoflow',
                              plugins = plugins)
    app.run()
    
    logging.shutdown()

if __name__ == '__main__':
    import sys
    run_gui(sys.argv)
