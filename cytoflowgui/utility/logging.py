#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2022
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

"""
cytoflowgui.utility.logging
---------------------------

Logging utilities for `cytoflowgui`
"""

import sys, traceback, threading, logging 

class CallbackHandler(logging.Handler):
    def __init__(self, callback, **kwargs):
        super().__init__(**kwargs)
        self._callback = callback
        
    def emit(self, record):
        self._callback(record)
        
def log_exception():
    (exc_type, exc_value, tb) = sys.exc_info()

    err_string = traceback.format_exception_only(exc_type, exc_value)[0]
    err_loc = traceback.format_tb(tb)[-1]
    err_ctx = threading.current_thread().name
    
    logging.debug("Exception in {0}: {1}"
                  .format(err_ctx,
                          "".join( traceback.format_exception(exc_type, exc_value, tb) )))
    
    logging.error("Error: {0}\nLocation: {1}Thread: {2}" \
                  .format(err_string, err_loc, err_ctx) )
    
