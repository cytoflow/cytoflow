'''
Created on Apr 18, 2015

@author: brian
'''

from Queue import PriorityQueue
import heapq

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