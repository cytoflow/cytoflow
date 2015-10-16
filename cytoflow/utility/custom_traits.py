'''
Created on Oct 12, 2015

@author: brian
'''

from traits.api import BaseInt, BaseFloat

class PositiveInt(BaseInt):
    
    allow_zero = False
    info_text = 'a positive integer'
    
    def validate(self, obj, name, value):
        value = super(PositiveInt, self).validate(obj, name, value)
        if (value > 0 or (self.allow_zero and value >= 0)):
            return value 
        
        self.error(obj, name, value)
        
        
class PositiveFloat(BaseFloat):
    
    allow_zero = False
    info_text = 'a positive float'
    
    def validate(self, obj, name, value):
        value = super(PositiveFloat, self).validate(obj, name, value)
        if (value > 0.0 or (self.allow_zero and value >= 0.0)):
            return value 
        
        self.error(obj, name, value)