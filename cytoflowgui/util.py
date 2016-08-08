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

from traits.api import Event, Undefined

from Queue import Queue, PriorityQueue
import heapq, sys, threading

import numpy as np
import scipy.stats
import cytoflow.utility as util

# http://stackoverflow.com/questions/1977362/how-to-create-module-wide-variables-in-python
this = sys.modules[__name__]
this.parent_log = None
this.child_log = None

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

class UniqueQueue(Queue):
    """
    A Queue that only allows one copy of each item.
    """
    
    def _init(self, maxsize):
        Queue._init(self, maxsize)
        self.values = set()

    def _put(self, item, heappush=heapq.heappush):
        if item[1] not in self.values:
            self.values.add(item[1])
            Queue._put(self, item, heappush)
        else:
            pass

    def _get(self, heappop=heapq.heappop):
        item = Queue._get(self, heappop)
        self.values.remove(item[1])
        return item
    
class DelayedEvent(Event):
    def set ( self, obj, name, value ):
        delay = self._metadata['delay']
        
        def fire(self, obj, name, value):
            self.value = Undefined
            obj.trait_property_changed( name, Undefined, value )
            
        if self.value is not Undefined and self._timer and self._timer.is_alive():
            return
        
        self._timer = threading.Timer(delay, fire, (self, obj, name, value))
        self._timer.start()

    def get ( self, obj, name ):
        return Undefined           
        

summary_functions = {"Mean" : np.mean,
                     "Geom.Mean" : util.geom_mean,
                     "Count" : len}

mean_95ci = lambda x: util.ci(x, np.mean, boots = 100)
geomean_95ci = lambda x: util.ci(x, util.geom_mean, boots = 100)
error_functions = {"Std.Dev." : np.std,
                   "S.E.M" : scipy.stats.sem,
                   "Mean 95% CI" : mean_95ci,
                   "Geom.Mean 95% CI" : geomean_95ci}