#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2022
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
cytoflowgui.editors.vertical_list_editor
----------------------------------------

A vertical editor for lists, derived from `traitsui.editors.list_editor.ListEditor`,
with the same API.

.. note::
    The difference between this class and the underlying **ListEditor** is that 
    this class doesn't use a scroll area.  Instead, as items are added, it
    expands.  To enable this behavior, make sure you ask for the 'simple'
    editor style, NOT 'custom'!

"""

from pyface.qt import QtCore, QtGui
from pyface.api import ImageResource  # @UnresolvedImport

from traits.api import Instance

from traitsui.api import ListEditor
from traitsui.qt.list_editor import CustomEditor as _ListEditor
from traitsui.qt.helper import IconButton

from traitsui.editors.list_editor import ListItemProxy

class _VerticalListEditor(_ListEditor):
    
    delete_mapper = Instance(QtCore.QSignalMapper)
    
    def init(self, parent):
        """ Finishes initializing the editor by creating the underlying toolkit
            widget.
        """
        # Initialize the trait handler to use:
        trait_handler = self.factory.trait_handler
        if trait_handler is None:
            trait_handler = self.object.base_trait(self.name).handler
        self._trait_handler = trait_handler

        #Create a mapper to identify which icon button requested a contextmenu
        self.mapper = QtCore.QSignalMapper(self.control)
        self.delete_mapper = QtCore.QSignalMapper(self.control)

        # Create a widget with a grid layout as the container.
        self.control = QtGui.QWidget()
        self.control.setSizePolicy(QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)
        layout = QtGui.QGridLayout(self.control)
        layout.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Remember the editor to use for each individual list item:
        editor = self.factory.editor
        if editor is None:
            editor = trait_handler.item_trait.get_editor()
        self._editor = getattr(editor, self.kind)

        # Set up the additional 'list items changed' event handler needed for
        # a list based trait. Note that we want to fire the update_editor_item
        # only when the items in the list change and not when intermediate
        # traits change. Therefore, replace "." by ":" in the extended_name
        # when setting up the listener.
        extended_name = self.extended_name.replace('.', ':')
        self.context_object.on_trait_change(
            self.update_editor_item,
            extended_name + '_items?',
            dispatch='ui')
        self.set_tooltip()


    #-------------------------------------------------------------------------
    #  Updates the editor when the object trait changes external to the editor:
    #-------------------------------------------------------------------------

    def update_editor(self):
        """ Updates the editor when the object trait changes externally to the
            editor.
        """
        self.mapper = QtCore.QSignalMapper(self.control)
        self.delete_mapper = QtCore.QSignalMapper(self.control)

        # Disconnect the editor from any control about to be destroyed:
        self._dispose_items()

        layout = self.control.layout()

        # Create all of the list item trait editors:
        trait_handler = self._trait_handler
        resizable = ((trait_handler.minlen != trait_handler.maxlen) and
                     self.mutable)
        item_trait = trait_handler.item_trait

        is_fake = (resizable and (len(self.value) == 0))
        if is_fake:
            self.empty_list()
        else:
            # Asking the mapper to send the sender to the callback method
            self.mapper.mapped.connect(self.popup_menu)
            
        self.delete_mapper.mapped.connect(self._delete_item)

        editor = self._editor
        for index, value in enumerate(self.value):
            row, column = divmod(index, self.factory.columns)

            # Account for the fact that we have <columns> number of
            # pairs
            column = column * 2

            if resizable:
                # Connecting the new button to the mapper
                control = IconButton('list_editor.png', self.popup_mapper.map)
                self.mapper.setMapping(control, index)

                layout.addWidget(control, row, column)
                
            if self.factory.deletable:
                # Connecting the new button to the mapper
                del_button = QtGui.QPushButton(self.control)
                del_button.setVisible(True)
                del_button.setFlat(True)
                del_button.setEnabled(True)
                
                del_button.setIcon(ImageResource('close').create_icon())
                del_button.setIconSize(QtCore.QSize(16, 16))
                
                del_button.clicked.connect(self.delete_mapper.map)
                self.delete_mapper.setMapping(del_button, index)

                layout.addWidget(del_button, row, column)
                

            proxy = ListItemProxy(self.object, self.name, index, item_trait,
                                  value)
            if resizable:
                control.proxy = proxy
            peditor = editor(self.ui, proxy, 'value', self.description,
                             self.control).trait_set(object_name='')
            peditor.prepare(self.control)
            pcontrol = peditor.control
            pcontrol.proxy = proxy

            if isinstance(pcontrol, QtGui.QWidget):
                layout.addWidget(pcontrol, row, column + 1)
            else:
                layout.addLayout(pcontrol, row, column + 1)

    def _dispose_items(self):
        """ Disposes of each current list item.
        """
        layout = self.control.layout()
        child = layout.takeAt(0)
        while child is not None:
            control = child.widget()
            if control is not None:
                editor = getattr(control, '_editor', None)
                if editor is not None:
                    editor.dispose()
                    editor.control = None
                control.setParent(None)
                control.deleteLater()
            child = layout.takeAt(0)
        del child
        
    def _delete_item(self, index):
        del self.value[index]

class VerticalListEditor(ListEditor):
    
    def _get_simple_editor_class(self):
        return _VerticalListEditor
