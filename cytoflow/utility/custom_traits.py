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
Created on Oct 12, 2015

@author: brian
'''

from __future__ import absolute_import

from traits.api import BaseInt, BaseFloat, BaseEnum
from . import scale

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
        
class ScaleEnum(BaseEnum):
    info_text = 'an enum containing one of the registered scales'

    def __init__ ( self, *args, **metadata ):
        """ Returns an Enum trait with values from the registered scales
        """
        self.name = ''
        self.values = scale._scale_mapping.keys()
        self.init_fast_validator( 5, self.values )
        super( BaseEnum, self ).__init__(scale._scale_default, **metadata )
        
    def get_default_value(self):
        # this is so silly.  get_default_value is ... called once?  as traits
        # sets up?  idunno.  anyways, instead of returning _scale_default, we
        # need to return a reference to a function that returns _scale_Default.
        
        return (7, (self._get_default_value, (), None))
    
    def _get_default_value(self):
        return scale._scale_default
