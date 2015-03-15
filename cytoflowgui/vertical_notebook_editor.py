"""
Created on Mar 8, 2015

@author: brian
"""

if __name__ == '__main__':
    from traits.etsconfig.api import ETSConfig
    ETSConfig.toolkit = 'qt4'

    import os
    os.environ['TRAITS_DEBUG'] = "1"

from traits.api import HasTraits

from traitsui.basic_editor_factory import BasicEditorFactory
from traits.api \
    import Bool, Any, List, Instance, Undefined, on_trait_change, Str
from traits.trait_base import user_name_for
from traitsui.ui_traits import AView
from traitsui.qt4.editor import Editor

from vertical_notebook import VerticalNotebook


class _VerticalNotebookEditor(Editor):
    """ 
    Traits UI vertical notebook editor for editing lists of objects with traits.
    """

    #-- Trait Definitions ----------------------------------------------------

    # Is the notebook editor scrollable? This values overrides the default:
    scrollable = True

    #-- Private Traits -------------------------------------------------------

    # The currently selected notebook page object (or objects):
    selected_item = Any
    selected_list = List

    # The ThemedVerticalNotebook we use to manage the notebook:
    notebook = Instance(VerticalNotebook)

    # Dictionary of page counts for all unique names:
    pages = Any({})

    #-- Editor Methods -------------------------------------------------------

    def init(self, parent):
        """ 
        Finishes initializing the editor by creating the underlying toolkit widget.
        """
        
        factory = self.factory
        self.notebook = VerticalNotebook(**factory.get('multiple_open',
                                                       'scrollable', 'double_click')).set(editor=self)
        self.control = self.notebook.create_control(parent)

        # Set up the additional 'list items changed' event handler needed for
        # a list based trait:
        self.context_object.on_trait_change(self.update_editor_item,
                                            self.extended_name + '_items?', dispatch='ui')

        # Synchronize the editor selection with the user selection:
        if factory.multiple_open:
            self.sync_value(factory.selected, 'selected_list', 'both',
                            is_list=True)
        else:
            self.sync_value(factory.selected, 'selected_item', 'both')

        self.set_tooltip()

    def update_editor(self):
        """ 
        Updates the editor when the object trait changes externally to the editor.
        """
        
        # Replace all of the current notebook pages:
        self.notebook.pages = [self._create_page(object)
                               for object in self.value]

    def update_editor_item(self, event):
        """ 
        Handles an update to some subset of the trait's list.
        """
        
        # Replace the updated notebook pages:
        self.notebook.pages[ event.index: event.index + len( event.removed ) ] \
            = [self._create_page(object) for object in event.added]

    def dispose(self):
        """ 
        Disposes of the contents of an editor. 
        """
        
        self.context_object.on_trait_change(self.update_editor_item,
                                            self.name + '_items?', remove=True)
        del self.notebook.pages[:]

        super(_VerticalNotebookEditor, self).dispose()

    #-- Trait Event Handlers -------------------------------------------------

    def _selected_item_changed(self, old, new):
        """ 
        Handles the selected item being changed.
        """
        
        if new is not None:
            self.notebook.open(self._find_page(new))
        elif old is not None:
            self.notebook.close(self._find_page(old))

    def _selected_list_changed(self, old, new):
        """ 
        Handles the selected list being changed.
        """
        
        notebook = self.notebook
        for object in old:
            notebook.close(self._find_page(object))

        for object in new:
            notebook.open(self._find_page(object))

    def _selected_list_items_changed(self, event):
        self._selected_list_changed(event.removed, event.added)

    @on_trait_change('notebook:pages:is_open')
    def _page_state_modified(self, page, name, old, is_open):
        if self.factory.multiple_open:
            object = page.data
            if is_open:
                if object not in self.selected_list:
                    self.selected_list.append(object)
            elif object in self.selected_list:
                self.selected_list.remove(object)
        elif is_open:
            self.selected_item = page.data
        else:
            self.selected_item = None

    #-- Private Methods ------------------------------------------------------

    def _create_page(self, object):
        """ 
        Creates and returns a notebook page for a specified object with traits.
        """
        # Create a new notebook page:
        page = self.notebook.create_page()

        # Create the Traits UI for the object to put in the notebook page:
        ui = object.edit_traits(parent=page.parent,
                                view=self.factory.view,
                                kind='subpanel').set(
            parent=self.ui)

        # Get the name of the page being added to the notebook:
        name = ''
        page_name = self.factory.page_name
        if page_name[0:1] == '.':
            if getattr(object, page_name[1:], Undefined) is not Undefined:
                page.register_name_listener(object, page_name[1:])
        else:
            name = page_name

        if name == '':
            name = user_name_for(object.__class__.__name__)

        # Make sure the name is not a duplicate, then save it in the page:
        if page.name == '':
            self.pages[name] = count = self.pages.get(name, 0) + 1
            if count > 1:
                name += (' %d' % count)
            page.name = name

        # Get the page description
        desc = ''
        page_desc = self.factory.page_description
        if page_desc[0:1] == '.':
            if getattr(object, page_desc[1:], Undefined) is not Undefined:
                page.register_description_listener(object, page_desc[1:])
        else:
            desc = page_desc

        # and save it to the page
        if page.description == '':
            page.description = desc

        # Save the Traits UI in the page so it can dispose of it later:
        page.ui = ui

        # Return the new notebook page
        return page

    def _find_page(self, object):
        """ 
        Find the notebook page corresponding to a specified object. Returns
        the page if found, and **None** otherwise.
        """
        for page in self.notebook.pages:
            if object is page.data:
                return page

        return None


class VerticalNotebookEditor(BasicEditorFactory):

    # The editor class to be created:
    klass = _VerticalNotebookEditor

    # Allow multiple open pages at once?
    multiple_open = Bool(False)

    # Should the notebook be scrollable?
    scrollable = Bool(False)

    # List member trait to read the notebook page name from
    page_name = Str

    # List member trait to read the notebook page description from
    page_description = Str

    # Name of the view to use for each page:
    view = AView

    # Name of the trait to synchronize notebook page
    # selection with:
    selected = Str

if __name__ == '__main__':

    from traitsui.api import View, Group, Item

    class TestPageClass(HasTraits):
        trait1 = Str
        trait2 = Str
        trait3 = Bool
        trait4 = Bool

        traits_view = View(Group(Item(name='trait1'),
                                 Item(name='trait2'),
                                 Item(name='trait3'),
                                 Item(name='trait4')))

    class TestList(HasTraits):
        el = List(TestPageClass)

        view = View(
            Group(
                Item(name='el',
                     id='table',
                     #editor = ListEditor()
                     editor=VerticalNotebookEditor(page_name='.trait1',
                                                   page_description='.trait2',
                                                   view='traits_view',
                                                   scrollable=True,
                                                   multiple_open=False)
                     )
            ),
            resizable=True
        )

    test = TestList()
    test.el.append(TestPageClass(trait1="one", trait2="two"))
    test.el.append(TestPageClass(trait1="three", trait2="four"))
    test.configure_traits()
