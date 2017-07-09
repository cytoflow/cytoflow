#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2017
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

from traits.api import Bool
from .i_view import IView

class ISelectionView(IView):
    """A decorator that lets you add (possibly interactive) selections to an IView.
    
    Note that this is a Decorator *design pattern*, not a Python `@decorator`.
    
    Attributes
    ----------
    interactive : Bool
        Is this view's interactivity turned on?
        
    """

    interactive = Bool(False, transient = True)