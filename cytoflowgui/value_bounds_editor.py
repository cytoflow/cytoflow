#!/usr/bin/env python2.7

# (c) Massachusetts Institute of Technology 2015-2016
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

# for local debugging

if __name__ == '__main__':
    from traits.etsconfig.api import ETSConfig
    ETSConfig.toolkit = 'qt4'

    import os
    os.environ['TRAITS_DEBUG'] = "1"

from pyface.qt import QtGui, QtCore

from traits.api import Any, Str, Trait, List, Bool
from traitsui.editors.api import RangeEditor
from traitsui.qt4.editor import Editor

from range_slider import RangeSlider



class _ValueBoundsEditor(Editor):
    """
    Creates a "range editor" over a specified set of values (instead of a
    defined range.)  Adapted from traitsui.qt4.extra.bounds_editor.
    """

    evaluate = Any

    values = List
    
    # the synchronized values
    low = Any
    high = Any
    
    format = Str

    # the slider positions.  either synchronized to low, high immediately or 
    # when the slider is released, depending on whether auto_set is True or not
    slider_low = Any
    slider_high = Any
    
    low_invalid = Bool(False)
    high_invalid = Bool(False)
    
    # quash slider jiggle
    _updating = Bool(False)

    def init(self, parent):
        """ Finishes initializing the editor by creating the underlying toolkit
            widget.
        """
        factory = self.factory
        
        if not factory.low_name:
            self.low = factory.low

        if not factory.high_name:
            self.high = factory.high

        self.values = factory.values
        
        # TODO - check to see if the values are numeric and sorted.
        # for now, assume they are.

        self.format = factory.format

        self.evaluate = factory.evaluate
        self.sync_value( factory.evaluate_name, 'evaluate', 'from' )
        
        self.sync_value( factory.low_name,  'low',  'both' )
        self.sync_value( factory.high_name, 'high', 'both' )

        self.control = QtGui.QWidget()
        panel = QtGui.QHBoxLayout(self.control)
        panel.setContentsMargins(0, 0, 0, 0)

        self._label_lo = QtGui.QLineEdit(self.format % self.low)
        QtCore.QObject.connect(self._label_lo, QtCore.SIGNAL('editingFinished()'),
                self.update_low_on_enter)
        panel.addWidget(self._label_lo)

        # The default size is a bit too big and probably doesn't need to grow.
        sh = self._label_lo.sizeHint()
        sh.setWidth(sh.width() / 2)
        self._label_lo.setMaximumSize(sh)

        self.control.slider = slider = RangeSlider(QtCore.Qt.Horizontal)
        slider.setTracking(True)
        slider.setMinimum(0)
        slider.setMaximum(10000)
        slider.setPageStep(1000)
        slider.setSingleStep(100)
                
        
#         self._slider_low = self.low
#         self._slider_high = self.high
        
        slider.setLow(self._convert_to_slider(self.low))
        slider.setHigh(self._convert_to_slider(self.high))
        
        QtCore.QObject.connect(slider, QtCore.SIGNAL('sliderMoved(int)'),
                self._slider_moved)
        QtCore.QObject.connect(slider, QtCore.SIGNAL('sliderReleased()'),
                self._slider_released)
        
        panel.addWidget(slider)

        self._label_hi = QtGui.QLineEdit(self.format % self.high)
        QtCore.QObject.connect(self._label_hi, QtCore.SIGNAL('editingFinished()'),
                self.update_high_on_enter)
        panel.addWidget(self._label_hi)

        # The default size is a bit too big and probably doesn't need to grow.
        sh = self._label_hi.sizeHint()
        sh.setWidth(sh.width() / 2)
        self._label_hi.setMaximumSize(sh)

        self.set_tooltip(slider)
        self.set_tooltip(self._label_lo)
        self.set_tooltip(self._label_hi)
        
    def update_editor(self):
        pass

    def update_low_on_enter(self):
        try:
            try:
                low = eval(unicode(self._label_lo.text()).strip())
                if self.evaluate is not None:
                    low = self.evaluate(low)
            except:
                low = self.low
                self._label_lo.setText(self.format % self.low)

#             if not self.factory.is_float:
#                 low = int(low)

            if low > self.high:
                low = self.high
                self._label_lo.setText(self.format % low)

            if low not in self.values:
                raise ValueError
            
            self.low = low
            self.low_invalid = False

#             self.control.slider.setLow(self._convert_to_slider(low))
#             self.low = low
#             
#             slider_high = self._convert_to_slider(self.high)
#             if slider_high < (self.control.slider.minimum() + 
#                               self.control.slider.singleStep()):
#                 self.control.slider.setHigh(slider_high)
        except:
            self.low_invalid = True

    def update_high_on_enter(self):
        try:
            try:
                high = eval(unicode(self._label_hi.text()).strip())
                if self.evaluate is not None:
                    high = self.evaluate(high)
            except:
                high = self.high
                self._label_hi.setText(self.format % self.high)

#             if not self.factory.is_float:
#                 high = int(high)

            if high < self.low:
                high = self.low
                self._label_hi.setText(self.format % high)

            assert high in self.values
            
            self.high = high
            self.high_invalid = False
#             self.control.slider.setHigh(self._convert_to_slider(high))
#             self.high = high
#             
#             slider_low = self._convert_to_slider(self.low)
#             if slider_low > (self.control.slider.maximum() - 
#                              self.control.slider.singleStep()):
#                 self.control.slider.setLow(slider_low) 
        except:
            self.high_invalid = True

    def _slider_moved(self, pos = 0):
        self._updating = True
        self.slider_low = self._convert_from_slider(self.control.slider.low())
        self.slider_high = self._convert_from_slider(self.control.slider.high())
        self._updating = False
        
        if self.factory.auto_set:
            if self.low != self.slider_low:
                self.low = self.slider_low
            if self.high != self.slider_high:
                self.high = self.slider_high
            
    def _slider_released(self):
        if not self.factory.auto_set:
            if self.low != self.slider_low:
                self.low = self.slider_low
            if self.high != self.slider_high:
                self.high = self.slider_high
            

    def _step_width(self):
        return ((self.control.slider.maximum() - self.control.slider.minimum())
                / float(len(self.values) - 1))

    def _convert_from_slider(self, slider_val):
        if len(self.values) == 1:
            return self.values[0]
        
        idx = int(slider_val / self._step_width() + 0.5)

        return self.values[idx]

    def _convert_to_slider(self, value):
        # first we have to find the value in the list.  let's assume, for the
        # sake of argument, that the list is sorted and pretty small, so we can
        # do something costly like a binary search (implemented recursively!)
        
        if value < self.values[0]:
            value = self.values[0]
            
        if value > self.values[-1]:
            value = self.values[-1]
        
        def find_idx(start, end):
            # binary search
            if start == end:
                return start
                
            cut = (start + end) / 2

            if value == self.values[cut]:
                return cut
            if value < self.values[cut]:
                return find_idx(start, cut - 1)
            else:
                return find_idx(cut + 1, end)
            
        idx = find_idx(0, len(self.values) - 1)
        
        return float(idx) * self._step_width() 
    
    def _low_changed(self, low):
        self.slider_low = low

    def _slider_low_changed(self, low):
        if self.control is None:
            return
        if self._label_lo is not None:
            self._label_lo.setText(self.format % low)

        self.low_invalid = False

        if not self._updating:
            self.control.slider.setLow(self._convert_to_slider(low))
            
            slider_high = self._convert_to_slider(self.slider_high)
            if slider_high < (self.control.slider.minimum() + 
                              self.control.slider.singleStep()):
                self.control.slider.setHigh(slider_high)
                
    def _low_invalid_changed(self, invalid):
        self.set_error_state(invalid, self._label_lo)
                
    def _high_changed(self, high):
        self.slider_high = high

    def _slider_high_changed(self, high):
        if self.control is None:
            return
        if self._label_hi is not None:
            self._label_hi.setText(self.format % high)
            
        self.high_invalid = False

        if not self._updating:
            self.control.slider.setHigh(self._convert_to_slider(high))
            
            slider_low = self._convert_to_slider(self.slider_low)
            if slider_low > (self.control.slider.maximum() - 
                             self.control.slider.singleStep()):
                self.control.slider.setLow(slider_low) 
                
    def _high_invalid_changed(self, invalid):
        self.set_error_state(invalid, self._label_hi)
            
    
class ValuesBoundsEditor(RangeEditor):
    
    values = Trait(None, List)
    
    def _get_simple_editor_class(self):
        return _ValueBoundsEditor
    
    def _get_custom_editor_class(self):
        return _ValueBoundsEditor
    
    
if __name__ == "__main__":
    
    from traits.api import Int, HasTraits
    from traitsui.api import View, Item
    
    class T(HasTraits):
        lo = Int(2)
        hi = Int(4)
        
        def _anytrait_changed(self, name, old, new):
            print "{0} changed to {1}".format(name, new)
        
    values = [1,2,3,4,5]
    view = View(Item('lo',
                     editor = ValuesBoundsEditor(values = values, 
                                                 low_name = 'lo',
                                                 high_name = 'hi',
                                                 auto_set = False)))
        
    t = T()
    t.configure_traits(view = view)
    print t.lo
    print t.hi
    
