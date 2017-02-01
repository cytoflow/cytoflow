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

'''
Created on Apr 18, 2015

@author: brian
'''

from traits.api import Event, Undefined, Unicode

from pyface.ui.qt4.file_dialog import FileDialog

from Queue import PriorityQueue
import heapq, threading

class UniquePriorityQueue(PriorityQueue):
    """
    A PriorityQueue that only allows one copy of each item.
    http://stackoverflow.com/questions/5997189/how-can-i-make-a-unique-value-priority-queue-in-python
    """
    
    def _init(self, maxsize):
        PriorityQueue._init(self, maxsize)
        self.values = set()

    def _put(self, item, heappush=heapq.heappush):
        if item[1] not in self.values:
            self.values.add(item[1])
            PriorityQueue._put(self, item, heappush)
        else:
            pass

    def _get(self, heappop=heapq.heappop):
        item = PriorityQueue._get(self, heappop)
        self.values.remove(item[1])
        return item

class DelayedEvent(Event):
    def __init__(self, **kwargs):
        self._lock = threading.RLock()
        self._timers = {}
        super(DelayedEvent, self).__init__(**kwargs)
        
    def set ( self, obj, name, value ):
        delay = self._metadata['delay']
        
        def fire(self, obj, name, value):
            self._lock.acquire()
            del self._timers[value]
            obj.trait_property_changed(name, Undefined, value)
            self._lock.release()
            
        self._lock.acquire()
        if value in self._timers:
            self._lock.release()
            return

        self._timers[value] = threading.Timer(delay, fire, (self, obj, name, value))
        self._timers[value].start()
        self._lock.release()

    def get ( self, obj, name ):
        return Undefined           
    
def filter_unpicklable(obj):
    if type(obj) is list:
        return [filter_unpicklable(x) for x in obj]
    elif type(obj) is dict:
        return {x: filter_unpicklable(obj[x]) for x in obj}
    else:
        if not hasattr(obj, '__getstate__') and not isinstance(obj,
                  (basestring, int, long, float, tuple, list, set, dict)):
            return "filtered: {}".format(type(obj))
        else:
            return obj
        
class DefaultFileDialog(FileDialog):
    default_suffix = Unicode
    
    def _create_control(self, parent):
        dlg = FileDialog._create_control(self, parent)
        dlg.setDefaultSuffix(self.default_suffix)
        return dlg


