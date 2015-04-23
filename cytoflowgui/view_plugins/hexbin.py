'''
Created on Apr 23, 2015

@author: brian
'''

from traitsui.api import View, Item, Controller, EnumEditor
from envisage.api import Plugin, contributes_to
from traits.api import provides, Property, Instance, DelegatesTo

from cytoflow import HexbinView
from cytoflowgui.workflow_item import WorkflowItem
from cytoflowgui.subset_editor import SubsetEditor
from cytoflowgui.subset_model import SubsetModel
from cytoflowgui.view_plugins.i_view_plugin \
    import IViewPlugin, VIEW_PLUGIN_EXT, ViewHandlerMixin

class HexbinHandler(Controller, ViewHandlerMixin):
    '''
    classdocs
    '''

    def default_traits_view(self):
        return View(Item('object.name'),
                    Item('object.xchannel',
                         editor=EnumEditor(name='handler.channels'),
                         label = "Channel"),
                    Item('object.ychannel',
                         editor=EnumEditor(name='handler.channels'),
                         label = "Channel"),
                    Item('object.xfacet',
                         editor=EnumEditor(name='handler.conditions'),
                         label = "Horizontal\nFacet"),
                    Item('object.yfacet',
                         editor=EnumEditor(name='handler.conditions'),
                         label = "Vertical\nFacet"),
                    Item('object.huefacet',
                         editor=EnumEditor(name='handler.conditions'),
                         label="Color\nFacet"),
                    Item('_'),
                    Item('object.subset',
                         label="Subset",
                         editor = SubsetEditor(experiment = "handler.wi.result")))


@provides(IViewPlugin)
class HexbinPlugin(Plugin):
    """
    classdocs
    """

    id = 'edu.mit.synbio.cytoflowgui.view.hexbin'
    view_id = 'edu.mit.synbio.cytoflow.view.hexbin'
    short_name = "HexBin"
    
    def get_view(self):
        view = HexbinView()
        view.handler_factory = HexbinHandler
        return view

    @contributes_to(VIEW_PLUGIN_EXT)
    def get_plugin(self):
        return self
        