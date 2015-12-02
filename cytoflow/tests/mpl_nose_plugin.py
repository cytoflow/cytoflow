'''
Created on Dec 2, 2015

@author: brian
'''

from nose.plugins import Plugin
class MplPlugin(Plugin):
    enabled = True
    def configure(self, options, conf):
        pass # always on
    def begin(self):
        import matplotlib
        matplotlib.use("Agg")