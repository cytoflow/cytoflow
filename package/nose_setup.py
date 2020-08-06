'''
Created on Aug 5, 2020

@author: brian
'''
import logging
import os

from nose2.events import Plugin

log = logging.getLogger('nose2.plugins.helloworld')

class HelloWorld(Plugin):
    configSection = 'helloworld'
    commandLineSwitch = (None, 'hello-world', 'Say hello!')

    def startTestRun(self, event):
        log.info('Hello pluginized world!')