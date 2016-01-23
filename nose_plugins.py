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
