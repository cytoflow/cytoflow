from traits.etsconfig.api import ETSConfig
ETSConfig.toolkit = 'qt4'

from pyface.qt import QtCore, QtGui

from pyface.widget import Widget
from pyface.tasks.dock_pane import DockPane

from traits.api \
    import HasTraits, HasPrivateTraits, Instance, List, Str, Bool, Property, \
           Event, Any, on_trait_change, cached_property

from traitsui.api import UI

from traitsui.editor \
    import Editor

class VerticalNotebookPage(HasPrivateTraits):
    """ A class representing a vertical page within a notebook. """

    #-- Public Traits ----------------------------------------------------------

    # The name of the page (displayed on its 'tab') [Set by client]:
    name = Str
    
    # The description of the page (displayed in smaller text in the button):
    description = Str

    # The Traits UI associated with this page [Set by client]:
    ui = Instance(UI)
    
    # The Qt window the page represents
    # control = Instance(QtGui.QWidget)

    # Optional client data associated with the page [Set/Get by client]:
    data = Any

    # The HasTraits object whose trait we look at to set the page name
    name_object = Instance(HasTraits)

    # The name of the *name_object* trait that signals a page name change 
    # [Set by client]:
    name_object_trait = Str
    
    # The HasTraits object whose trait we look at to set the page description
    description_object = Instance(HasTraits)
    
    # The name of the *description_object* trait that signals a page description 
    # change [Set by client]
    description_object_trait = Str

    # The parent window for the client page [Get by client]:
    parent = Property

    #-- Traits for use by the Notebook/Sizer -----------------------------------

    # The current open status of the notebook page:
    is_open = Bool(False)

    # The minimum size for the page:
    min_size = Property

    # The open size property for the page:
    #open_size = Property

    # The closed size property for the page:
    #closed_size = Property

    #-- Private Traits ---------------------------------------------------------

    # The notebook this page is associated with:
    notebook = Instance( 'VerticalNotebook' )

    # The control representing the open page:
    control = Property
    
    # The control representing the button that opens and closes the control
    button = Property

    #-- Public Methods ---------------------------------------------------------

    def close ( self ):
        """ Closes the notebook page. """

        if self.name_object is not None:
            self.name_object.on_trait_change(self._name_updated, 
                                             self.name_object_trait,
                                             remove = True )
            self.name_object = None
            
        if self.description_object is not None:
            self.description_object.on_trait_change(self._description_updated,
                                                    self.description_object_trait,
                                                    remove = True)

        if self.ui is not None:
            self.ui.dispose()
            self.ui = None
        
        #if self.control is not None:
        #    self.control = None
        
#     def set_size (self, x, y, w, h):
#         """ Sets the size of the current active page. """
#         if self.is_open:
#             self.open_page.control.setGeometry(x, y, w, h)
#         else:
#             self.closed_page.control.setGeometry(x, y, w, h)
            
    def register_name_listener(self, model, trait):
        """ Registers a listener on the specified object trait for a page name
            change.
        """
        # Save the information, so we can unregister it later:
        self.name_object, self.name_object_trait = model, trait
 
        # Register the listener:
        self.name_object.on_trait_change(self._name_updated, trait)
 
        # Make sure the name gets initialized:
        self._name_updated()
        
    def register_description_listener(self, model, trait):
        """
        Registers a listener on the specified object trait for a page 
        description change
        """
        
        # save the info so we can unregister it later
        self.description_object, self.description_object_trait = model, trait
        
        # register the listener
        self.description_object.on_trait_change(self._description_updated, trait)
        
        # make sure the description gets initialized
        self._description_updated()

    #-- Property Implementations -----------------------------------------------

#     def _get_min_size ( self ):
#         """ Returns the minimum size for the page.
#         """
#         dxo, dyo = self.open_page.size
#         dxc, dyc = self.closed_page.size
#         if self.is_open:
#             return (max(dxo, dxc), dyo)
# 
#         return (max(dxo, dxc), dyc)
# 
#     def _get_open_size ( self ):
#         """ Returns the open size for the page.
#         """
#         return self.open_page.size
# 
#     def _get_closed_size ( self ):
#         """ Returns the closed size for the page.
#         """
#         return self.closed_page.size

    def _handle_page_toggle(self):
        if self.is_open:
            self.notebook.close(self)
        else:
            self.notebook.open(self)
            
    @cached_property
    def _get_button ( self ):
        """ Returns the 'closed' form of the notebook page.
        """
        new_button = QtGui.QCommandLinkButton(self.notebook.control)
        new_button.setVisible(True)
        new_button.setCheckable(True)
        new_button.setFlat(False)
        new_button.setAutoFillBackground(True)
        new_button.clicked.connect(self._handle_page_toggle)
        return new_button
        #return None
 
    #@cached_property
    def _get_control ( self ):
        """ Returns the 'open' form of the notebook page.
        """
        #self.ui.control.setVisible(self.is_open)
        return self.ui.control

    def _get_parent ( self ):
        """ Returns the parent window for the client's window.
        """
        return self.notebook.control

    #-- Trait Event Handlers ---------------------------------------------------

#     def _ui_changed ( self, ui ):
#         """ Handles the ui trait being changed.
#         """
#         if ui is not None:
#             self.control = ui.control

#     def _control_changed ( self, control ):
#         """ Handles the control for the page being changed.
#         """
#         if control is not None:
#             #self.open_page.control.GetSizer().Add( control, 1, wx.EXPAND )
#             self._is_open_changed( self.is_open )

    def _is_open_changed ( self, is_open ):
        """ Handles the 'is_open' state of the page being changed.
        """
        
        #self.notebook.control.setUpdatesEnabled(False)
        self.control.setVisible(is_open)
        self.button.setChecked(is_open)
        if is_open:
            self.button.setIcon(self.button.style().
                                standardIcon(QtGui.QStyle.SP_ArrowDown))
        else: 
            self.button.setIcon(self.button.style().
                                standardIcon(QtGui.QStyle.SP_ArrowRight))
        #self.open_page.setVisible(is_open)
        
        #self.notebook._refresh()

#         if is_open:
#             self.closed_page.resize(0, 0)
#         else:
#             self.open_page.resize(0, 0)

    def _name_changed ( self, name ):
        """ Handles the name trait being changed.
        """
        self.button.setText(name)
        #self.open_page.text = name
        
    def _description_changed(self, description):
        self.button.setDescription(description)

    def _name_updated ( self ):
        """ 
        Handles a signal that the associated object's page name has changed.
        """
        nb = self.notebook
        handler_name = None

        method = None
        editor = nb.editor
        if editor is not None:
            method = getattr( editor.ui.handler,
                 '%s_%s_page_name' % ( editor.object_name, editor.name ), None )
        if method is not None:
            handler_name = method( editor.ui.info, self.name_object )

        if handler_name is not None:
            self.name = handler_name
        else:
            self.name = getattr( self.name_object, 
                                 self.name_object_trait ) or '???'
            
            
    def _description_updated(self):
        """
        Handles the signal that the associated object's description has changed.
        """
        nb = self.notebook
        handler_name = None
        
        method = None
        editor = nb.editor
        if editor is not None:
            method = getattr(editor.ui.handler,
                             '%s_%s_page_description' % 
                                (editor.object_name, editor.name), 
                             None)
        if method is not None:
            handler_name = method(editor.ui.info, self.description_object)
        
        if handler_name is not None:
            self.description = handler_name
        else:
            self.description = getattr(self.description_object, 
                                       self.description_object_trait) or ''

    #-- ThemedControl Mouse Event Handlers -------------------------------------
# 
#     def open_left_down ( self, x, y, event ):
#         """ Handles the user clicking on an open notebook page to close it.
#         """
#         if not self.notebook.double_click:
#             self.notebook.close(self)
# 
#     def open_left_dclick ( self, x, y, event ):
#         """ Handles the user double clicking on an open notebook page to close
#             it.
#         """
#         if self.notebook.double_click:
#             self.notebook.close(self)
# 
#     def closed_left_down ( self, x, y, event ):
#         """ Handles the user clicking on a closed notebook page to open it.
#         """
#         if not self.notebook.double_click:
#             self.notebook.open(self)
# 
#     def closed_left_dclick ( self, x, y, event ):
#         """ Handles the user double clicking on a closed notebook page to open
#             it.
#         """
#         if self.notebook.double_click:
#             self.notebook.open(self)

#-------------------------------------------------------------------------------
#  'ThemedVerticalNotebook' class:
#-------------------------------------------------------------------------------

class VerticalNotebook(HasPrivateTraits):
    """ Defines a ThemedVerticalNotebook class for displaying a series of pages
        organized vertically, as opposed to horizontally like a standard
        notebook.
    """

    #-- Public Traits ----------------------------------------------------------

    # Allow multiple open pages at once?
    multiple_open = Bool( False )

    # Should the notebook be scrollable?
    scrollable = Bool( False )

    # Use double clicks (True) or single clicks (False) to open/close pages:
    # double_click = Bool( False )

    # The pages contained in the notebook:
    pages = List( VerticalNotebookPage )

    # The traits UI editor this notebook is associated with (if any):
    editor = Instance( Editor )

    #-- Private Traits ---------------------------------------------------------

    # The Qt control used to represent the notebook:
    control = Instance(QtGui.QWidget)
    layout = Instance(QtGui.QVBoxLayout)

    #-- Public Methods ---------------------------------------------------------

    def create_control ( self, parent ):
        """ Creates the underlying Qt window used for the notebook.
        """
        
        self.layout = QtGui.QVBoxLayout()
        self.layout.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        
        # Create the correct type of window based on whether or not it should
        # be scrollable:
        if self.scrollable:
            self.control = QtGui.QScrollArea()
            self.control.setFrameShape(QtGui.QFrame.NoFrame)
            self.control.setWidgetResizable(True)
            
            panel = QtGui.QWidget()
            panel.setLayout(self.layout)
            self.control.setWidget(panel)
        else:
            self.control = QtGui.QWidget()
            self.control.setLayout(self.layout)

        return self.control

    def create_page ( self ):
        """ Creates a new **VerticalNotebook** object representing a notebook page and
            returns it as the result.
        """
        return VerticalNotebookPage(notebook = self)

    def open ( self, page ):
        """ Handles opening a specified notebook page.
        """
        if (page is not None) and (not page.is_open):
            if not self.multiple_open:
                for a_page in self.pages:
                    a_page.is_open = False

            page.is_open = True

            #self._refresh()

    def close(self, page):
        """ Handles closing a specified notebook page.
        """
        if (page is not None) and page.is_open:
            page.is_open = False
            #self._refresh()

    #-- Trait Event Handlers ---------------------------------------------------

    def _pages_changed ( self, old, new ):
        """ Handles the notebook's pages being changed.
        """
        for page in old:
            page.close()

        self._refresh()

    def _pages_items_changed ( self, event ):
        """ Handles some of the notebook's pages being changed.
        """
        for page in event.removed:
            page.close()

        self._refresh()

    def _multiple_open_changed ( self, multiple_open ):
        """ Handles the 'multiple_open' flag being changed.
        """
        if not multiple_open:
            first = True
            for page in self.pages:
                if first and page.is_open:
                    first = False
                else:
                    page.is_open = False

        #self._refresh()

    #-- wx.Python Event Handlers -----------------------------------------------
# 
#     def _erase_background ( self, event ):
#         """ Do not erase the background here (do it in the 'on_paint' handler).
#         """
#         pass

#     def _paint ( self, event ):
#         """ Paint the background using the associated ImageSlice object.
#         """
#         paint_parent( wx.PaintDC( self.control ), self.control )

    #-- Private Methods --------------------------------------------------------

    def _refresh ( self ):
        """ Refresh the layout and contents of the notebook.
        """
        
        self.control.setUpdatesEnabled(False)
        
        while self.layout.count() > 0:
            self.layout.takeAt(0)
            
        for page in self.pages:
            self.layout.addWidget(page.button)
            #page.closed_page.setVisible(not page.is_open)
            self.layout.addWidget(page.control)
            page.control.setVisible(page.is_open)
            
        self.control.setUpdatesEnabled(True)
#         if control is not None:
#             # Set the virtual size of the canvas (so scroll bars work right):
#             sizer = control.GetSizer()
#             if control.GetSize()[0] == 0:
#                 control.SetSize( sizer.CalcInit() )
#             control.SetVirtualSize( sizer.CalcMin() )
#             control.Layout()
#             control.Refresh()

#-------------------------------------------------------------------------------
#  'ThemedVerticalNotebookSizer' class:
#-------------------------------------------------------------------------------

# class ThemedVerticalNotebookSizer ( wx.PySizer ):
#     """ Defines a sizer that correctly sizes a themed vertical notebook's
#         children to implement the vertical notebook UI object.
#     """
# 
#     def __init__ ( self, notebook ):
#         """ Initializes the object.
#         """
#         super( ThemedVerticalNotebookSizer, self ).__init__()
# 
#         # Save the notebook reference:
#         self._notebook = notebook
# 
#     def CalcMin ( self ):
#         """ Calculates the minimum size of the control by aggregating the
#             sizes of the open and closed pages.
#         """
#         tdx, tdy = 0, 0
#         for page in self._notebook.pages:
#             dx, dy = page.min_size
#             tdx    = max( tdx, dx )
#             tdy   += dy
# 
#         return wx.Size( tdx, tdy )
# 
#     def CalcInit ( self ):
#         """ Calculates a reasonable initial size of the control by aggregating
#             the sizes of the open and closed pages.
#         """
#         tdx, tdy = 0, 0
#         open_dy  = closed_dy = 0
#         for page in self._notebook.pages:
#             dxo, dyo = page.open_size
#             dxc, dyc = page.closed_size
#             tdx      = max( tdx, dxo, dxc )
#             if dyo > open_dy:
#                 tdy += (dyo - open_dy + closed_dy)
#                 open_dy, closed_dy = dyo, dyc
#             else:
#                 tdy += dyc
# 
#         return wx.Size( tdx, min( tdy, screen_dy / 2 ) )
# 
#     def RecalcSizes ( self ):
#         """ Layout the contents of the sizer based on the sizer's current size
#             and position.
#         """
#         x, y     = self.GetPositionTuple()
#         tdx, tdy = self.GetSizeTuple()
#         cdy      = ody = 0
#         for page in self._notebook.pages:
#             dx, dy = page.min_size
#             if page.is_open:
#                 ody += dy
#             else:
#                 cdy += dy
# 
#         ady = max( 0, tdy - cdy )
# 
#         for page in self._notebook.pages:
#             dx, dy = page.min_size
#             if page.is_open:
#                 ndy  = (ady * dy) / ody
#                 ady -= ndy
#                 ody -= dy
#                 dy   = ndy
#             page.set_size( x, y, tdx, dy )
#             y += dy

if __name__ == '__main__':
    
    from traitsui.api import View, Group, Item
    from vertical_notebook_editor import VerticalNotebookEditor

    class TestPageClass(HasTraits):
        trait1 = Str
        trait2 = Bool
        trait3 = Bool
        
        traits_view = View(Group(Item(name='trait1'),
                                 Item(name='trait2'),
                                 Item(name='trait3')))
        
    class TestList(HasTraits):
        el = List(TestPageClass)
    
        view = View( 
                    Group( 
                          Item(name = 'el', 
                               id = 'table',
                               #editor = ListEditor() 
                               editor = VerticalNotebookEditor(page_name = '.trait1',
                                                               view = 'traits_view')
                               )
                          )
                    )
        
    test = TestList()
    test.el.append(TestPageClass(trait1="one", trait2="two"))
    test.el.append(TestPageClass(trait1="three", trait2="four"))
    test.configure_traits()