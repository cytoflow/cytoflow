'''
Created on Mar 10, 2016

@author: brian
'''

from __future__ import print_function

from traits.api import HasTraits, Int, on_trait_change, Instance
from multiprocessing.managers import BaseManager, NamespaceProxy
import time

class T(HasTraits):
    i = Int(3)
    
    def pr(self, j):
        print("j: {0}".format(j))
        
class M(HasTraits):
    t = Instance(T, ())

class TraitsManager(BaseManager):
    pass

class HasTraitsProxy(NamespaceProxy):
    # We need to expose the same __dunder__ methods as NamespaceProxy,
    # in addition to the b method.
    _exposed_ = ('__getattribute__', '__setattr__', '__delattr__', 'traits', 'pr')
    
    def __getattr__(self, key):
        print("key {0}".format(key))
        if key[0] == '_':
            return object.__getattribute__(self, key)
        callmethod = object.__getattribute__(self, '_callmethod')
        
        if key in callmethod('traits', ()):
            return callmethod('__getattribute__', (key,))
        else:
            return lambda *args, **kwds: callmethod(key, args, kwds)
    
    def __setattr__(self, key, value):
        if key[0] == '_':
            return object.__setattr__(self, key, value)
        callmethod = object.__getattribute__(self, '_callmethod')
        return callmethod('__setattr__', (key, value))
    def __delattr__(self, key):
        if key[0] == '_':
            return object.__delattr__(self, key)
        callmethod = object.__getattribute__(self, '_callmethod')
        return callmethod('__delattr__', (key,))

# 
#     def pr(self, j):
#         callmethod = object.__getattribute__(self, '_callmethod')
#         return callmethod('pr', (j, ))

TraitsManager.register('T', T, proxytype = HasTraitsProxy)
TraitsManager.register('M', M, proxytype = HasTraitsProxy)

if __name__ == '__main__':
    manager = TraitsManager()
    manager.start()
    
    t = manager.T()
    
    print(t.i)
    t.i = 5
    print(t.i)
    
    t.pr(7)

    
    #print(t.i)
    #t.i = 5
    #print(t.i)
    #t.pr(7)