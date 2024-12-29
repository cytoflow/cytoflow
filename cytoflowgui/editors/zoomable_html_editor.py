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
cytoflowgui.editors.zoomable_html_editor
----------------------------------------

An HTML "editor" that is high-DPI aware.

Derived from `traitsui.editors.html_editor`

Adapted from:
https://github.com/enthought/traitsui/blob/master/traitsui/editors/html_editor.py
https://github.com/enthought/traitsui/blob/master/traitsui/qt4/html_editor.py
"""


from pyface.qt import QtGui, QtWebKit

from traitsui.editors.html_editor import ToolkitEditorFactory
from traitsui.qt.html_editor import SimpleEditor as _HTMLEditor  # @UnresolvedImport

class _ZoomableHTMLEditor(_HTMLEditor):
    """ Simple style editor for zoomable HTML.
    """

    def init(self, parent):
        """ Finishes initializing the editor by creating the underlying toolkit
            widget.
        """
        self.control = QtWebKit.QWebView()
        self.control.setSizePolicy(
            QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding
        )
        
        dpi = self.control.physicalDpiX()
        self.control.setZoomFactor(dpi / 120)

        self.base_url = self.factory.base_url
        self.sync_value(self.factory.base_url_name, "base_url", "from")
        


class ZoomableHTMLEditor(ToolkitEditorFactory):
    """ Editor factory for zoomable HTML editors.
    """
    klass = _ZoomableHTMLEditor


    

    
    