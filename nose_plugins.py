'''
Created on Dec 2, 2015

@author: brian
'''

from nose.plugins import Plugin
import logging

log = logging.getLogger('nose.plugins.mplplugin')

class MplPlugin(Plugin):
    name = 'mplplugin'
    enabled = True
    def configure(self, options, conf):
        pass # always on
    def begin(self):
        log.info ('Loading the matplotlib Agg backend')
        import matplotlib
        matplotlib.use("Agg")
