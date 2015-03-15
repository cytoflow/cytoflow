from traitsui.api import ModelView

from envisage.api import Plugin

class Threshold(ModelView):
    
    pass

class ThresholdPlugin(Plugin):
    
    id = 'edu.mit.synbio.cytoflow.threshold_plugin'
    
    name = "Threshold Operation"
    