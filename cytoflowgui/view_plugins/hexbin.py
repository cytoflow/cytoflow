'''
Created on Apr 23, 2015

@author: brian
'''

from traitsui.api import View, Item, Controller, EnumEditor, Handler
from envisage.api import Plugin, contributes_to
from traits.api import provides, Callable, Instance

from cytoflow import HexbinView
from cytoflowgui.subset_editor import SubsetEditor
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
                         label = "X Channel"),
                    Item('object.ychannel',
                         editor=EnumEditor(name='handler.channels'),
                         label = "Y Channel"),
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

class HexbinPluginView(HexbinView):
    handler = Instance(Handler, transient = True)
    handler_factory = Callable(HexbinHandler)
    
    def is_wi_valid(self, wi):
        return wi.result and self.is_valid(wi.result)

    def plot_wi(self, wi, pane):
        pane.plot(wi.result, self)

@provides(IViewPlugin)
class HexbinPlugin(Plugin):
    """
    classdocs
    """

    id = 'edu.mit.synbio.cytoflowgui.view.hexbin'
    view_id = 'edu.mit.synbio.cytoflow.view.hexbin'
    short_name = "HexBin"

    def get_view(self):
        return HexbinPluginView()

    @contributes_to(VIEW_PLUGIN_EXT)
    def get_plugin(self):
        return self
        