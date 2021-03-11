'''
Created on Jan 23, 2021

@author: brian
'''
from pyface.qt import QtGui

from traits.api import HasTraits, Callable
from traitsui.api import InstanceEditor, Handler
from traitsui.qt4.instance_editor import CustomEditor as _InstanceEditor

class _InstanceHandlerEditor(_InstanceEditor):
    """
    Override InstanceEditor to use a factory to get the handler for 
    the instance we're editing. This lets us both change the handler we
    use depending on the instance, as well as look in that handler for
    the view.
    """
    
    def resynch_editor(self):
        """ Resynchronizes the contents of the editor when the object trait
        changes externally to the editor.
        """
        panel = self._panel
        if panel is not None:
            # Dispose of the previous contents of the panel:
            layout = panel.layout()
            if layout is None:
                layout = QtGui.QVBoxLayout(panel)
                layout.setContentsMargins(0, 0, 0, 0)
            elif self._ui is not None:
                self._ui.dispose()
                self._ui = None
            else:
                child = layout.takeAt(0)
                while child is not None:
                    child = layout.takeAt(0)

                del child

            # Create the new content for the panel:
#             stretch = 0
            value = self.value
            if not isinstance(value, HasTraits):
                str_value = ""
                if value is not None:
                    str_value = self.str_value
                control = QtGui.QLabel(str_value)
            else:
                handler = self.factory.handler_factory(value) if self.factory.handler_factory else None

                view = self.view_for(value, self.item_for(value), handler)
                context = value.trait_context()
                if isinstance(value, Handler):
                    handler = value
                context.setdefault("context", self.object)
                context.setdefault("context_handler", self.ui.handler)
                self._ui = ui = view.ui(
                    context,
                    panel,
                    "subpanel",
                    value.trait_view_elements(),
                    handler,
                    self.factory.id,
                )
                control = ui.control
                self.scrollable = ui._scrollable
                ui.parent = self.ui

#                 if view.resizable or view.scrollable or ui._scrollable:
#                     stretch = 1

            # FIXME: Handle stretch.
            layout.addWidget(control)
            
    def view_for(self, object, item, handler):  # @ReservedAssignment
        """ Returns the view to use for a specified object.
        """
        view = ""
        if item is not None:
            view = item.get_view()

        if view == "":
            view = self.view

        if handler is None:
            return self.ui.handler.trait_view_for(
                self.ui.info, view, object, self.object_name, self.name
            )
        else:
            return handler.trait_view_for(
                self.ui.info, view, object, self.object_name, self.name
            )            
            

class InstanceHandlerEditor(InstanceEditor):
    custom_editor_class = _InstanceHandlerEditor
    
    handler_factory = Callable
    
    def custom_editor(self, ui, object, name, description, parent):  # @ReservedAssignment
        """ Generates an editor using the "custom" style.
        """
        return _InstanceHandlerEditor(
            parent,
            factory=self,
            ui=ui,
            object=object,
            name=name,
            description=description,
        )