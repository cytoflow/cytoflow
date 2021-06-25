'''
Created on Jan 16, 2021

@author: brian
'''

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
    
