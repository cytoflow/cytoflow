#!/usr/bin/env python3.8
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
cytoflowgui.editors.vertical_notebook_editor
--------------------------------------------

"""

from traits.api import HasTraits

from traitsui.basic_editor_factory import BasicEditorFactory
from traits.api import Bool, Any, List, Instance, Undefined, on_trait_change, Str, Callable
from traits.trait_base import user_name_for
from traitsui.ui_traits import AView
from traitsui.qt4.editor import Editor

from .vertical_notebook import VerticalNotebook


class _VerticalNotebookEditor(Editor):
    """ 
    Traits UI vertical notebook editor for editing lists of objects with traits.
    """

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
                                                       'delete',
                                                       'double_click')).set(editor=self)
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
        self.notebook.pages = [self._create_page(obj) for obj in self.value]

    def update_editor_item(self, event):
        """ 
        Handles an update to some subset of the trait's list.
        """
        
        # Replace the updated notebook pages:
        self.notebook.pages[event.index: event.index + len(event.removed)] \
            = [self._create_page(obj) for obj in event.added]

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
        for obj in old:
            notebook.close(self._find_page(obj))

        for obj in new:
            notebook.open(self._find_page(obj))

    def _selected_list_items_changed(self, event):
        self._selected_list_changed(event.removed, event.added)

    @on_trait_change('notebook:pages:is_open')
    def _page_state_modified(self, page, name, old, is_open):
        if self.factory.multiple_open:
            obj = page.data
            if is_open:
                if obj not in self.selected_list:
                    self.selected_list.append(obj)
            elif obj in self.selected_list:
                self.selected_list.remove(obj)
        elif is_open:
            self.selected_item = page.data
        else:
            self.selected_item = None

    #-- Private Methods ------------------------------------------------------

    def _create_page(self, obj):
        """ 
        Creates and returns a notebook page for a specified object with traits.
        """
        # Create a new notebook page:
        page = self.notebook.create_page().set(data = obj)

        # Create the Traits UI for the object to put in the notebook page:                                
        ui = obj.edit_traits(parent=page.parent,
                             view=self.factory.view,
                             handler=self.factory.handler_factory(obj) if self.factory.handler_factory else None,
                             kind='subpanel').set(parent=self.ui)

        # Get the name of the page being added to the notebook:
        name = ''
        page_name = self.factory.page_name
        if page_name[0:1] == '.':
            if getattr(obj, page_name[1:], Undefined) is not Undefined:
                page.register_name_listener(obj, page_name[1:])
        else:
            name = page_name

        if name == '':
            name = user_name_for(obj.__class__.__name__)

        # Make sure the name is not a duplicate, then save it in the page:
        if page.name == '':
            self.pages[name] = count = self.pages.get(name, 0) + 1
            if count > 1:
                name += (' %d' % count)
            page.name = name

        # Get the page description
        page_desc = self.factory.page_description
        if page_desc[0:1] == '.':
            if getattr(ui.context['object'], page_desc[1:], Undefined) is not Undefined:
                page.register_description_listener(ui.context['object'], page_desc[1:])
            elif getattr(ui.context['handler'], page_desc[1:], Undefined) is not Undefined:
                page.register_description_listener(ui.context['handler'], page_desc[1:])
            
        # Get the page icon
        page_icon = self.factory.page_icon
        if page_icon[0:1] == '.':
            if getattr(ui.context['object'], page_icon[1:], Undefined) is not Undefined:
                page.register_icon_listener(ui.context['object'], page_icon[1:])
            elif getattr(ui.context['handler'], page_icon[1:], Undefined) is not Undefined:
                page.register_icon_listener(ui.context['handler'], page_icon[1:])
                
        # Is the page deletable?
        page_deletable = self.factory.page_deletable
        if page_deletable[0:1] == '.':
            if getattr(ui.context['object'], page_deletable[1:], Undefined) is not Undefined:
                page.register_deletable_listener(ui.context['object'], page_deletable[1:])
            elif getattr(ui.context['handler'], page_deletable[1:], Undefined) is not Undefined:
                page.register_deletable_listener(ui.context['handler'], page_deletable[1:])


        # Save the Traits UI in the page so it can dispose of it later:
        page.ui = ui

        # Return the new notebook page
        return page

    def _find_page(self, obj):
        """ 
        Find the notebook page corresponding to a specified object. Returns
        the page if found, and **None** otherwise.
        """
        for page in self.notebook.pages:
            if obj is page.data:
                return page

        return None


class VerticalNotebookEditor(BasicEditorFactory):

    # The editor class to be created:
    klass = _VerticalNotebookEditor

    # Allow multiple open pages at once?
    multiple_open = Bool(False)
    
    # Include a "delete" button?
    delete = Bool(False)

    # List member trait to read the notebook page name from
    page_name = Str

    # List member trait to read the notebook page description from
    page_description = Str
    
    # List member trait to read the notebook page icon from
    # If None, then use right-arrow for "closed" and down-arrow for "open"
    # The type of this trait is toolkit-specific; for example, the pyface.qt
    # type is a QtGui.QStyle.StandardPixmap
    page_icon = Str
    
    # List member trait to specify whether the page is deletable
    # If the "delete" trait, above, is True, then this list member
    # trait will enable or disable the "delete" button
    page_deletable = Str

    # Name of the view to use for each page:
    view = AView
    
    # A factory to produce a handler from an object
    handler_factory = Callable

    # Name of the trait to synchronize notebook page
    # selection with:
    selected = Str

if __name__ == '__main__':

    from traitsui.api import View, Group, Item
    from traits.api import Button
    from pyface.qt import QtGui

    class TestPageClass(HasTraits):
        trait1 = Str
        trait2 = Str
        trait3 = Bool
        trait4 = Bool
        trait5 = Button
        icon = Str

        traits_view = View(Group(Item(name='trait1'),
                                 Item(name='trait2'),
                                 Item(name='trait3'),
                                 Item(name='trait4'),
                                 Item(name='trait5')))
        
    class TestList(HasTraits):
        el = List(TestPageClass)

        view = View(
            Group(
                Item(name='el',
                     id='table',
                     #editor = ListEditor()
                     editor=VerticalNotebookEditor(page_name='.trait1',
                                                   page_description='.trait2',
                                                   page_icon='.icon',
                                                   view='traits_view',
                                                   multiple_open=False)
                     )
            ),
            resizable=True
        )

    test = TestList()
    test.el.append(TestPageClass(trait1="one", trait2="two", icon='ok'))
    test.el.append(TestPageClass(trait1="three", trait2="four", icon='error'))
    test.configure_traits()
