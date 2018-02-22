#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2017
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
cytoflow.utility.custom_traits
------------------------------

Custom traits for :class:`~cytoflow`
'''

from warnings import warn
import inspect

from traits.api import (BaseInt, BaseCInt, BaseFloat, BaseCFloat, BaseEnum, TraitType)
from . import scale
from . import CytoflowError, CytoflowWarning


class PositiveInt(BaseInt):
    """
    Defines a trait whose value must be a positive integer
    """
    
    info_text = 'a positive integer'
    
    def validate(self, obj, name, value):
        if self.allow_none and value == None:
            return None
        
        value = super().validate(obj, name, value)
        if (value > 0 or (self.allow_zero and value >= 0)):
            return value 
        
        self.error(obj, name, value)
        
class PositiveCInt(BaseCInt):
    """
    Defines a trait whose value must be a positive integer
    """
    
    info_text = 'a positive integer'
    
    def validate(self, obj, name, value):
        if self.allow_none and (value == "" or value == None):
            return None
        
        value = super().validate(obj, name, value)
        if (value > 0 or (self.allow_zero and value >= 0)):
            return value 
        
        self.error(obj, name, value)
        
        
class PositiveFloat(BaseFloat):
    """
    Defines a trait whose value must be a positive float
    """
    
    info_text = 'a positive float'
    
    def validate(self, obj, name, value):
        if self.allow_none and value == None:
            return None
        
        value = super().validate(obj, name, value)
        if (value > 0.0 or (self.allow_zero and value >= 0.0)):
            return value 
        
        self.error(obj, name, value)
        
class PositiveCFloat(BaseCFloat):
    """
    Defines a trait whose value must be a positive float
    """
    
    info_text = 'a positive float'
    
    def validate(self, obj, name, value):
        if self.allow_none and (value == "" or value == None):
            return None
        
        value = super().validate(obj, name, value)
        if (value > 0.0 or (self.allow_zero and value >= 0.0)):
            return value 
        
        self.error(obj, name, value)
        
class FloatOrNone(BaseFloat):
    
    info_text = 'a float or None'
    
    def validate(self, obj, name, value):
        if value == "" or value == None:
            return None
        else:
            return super().validate(obj, name, value)

class CFloatOrNone(BaseCFloat):
    
    info_text = 'a float or None'
    
    def validate(self, obj, name, value):
        if value == None or value == "":
            return None
        else:
            return super().validate(obj, name, value)

class IntOrNone(BaseInt):
    
    info_text = 'an int or None'
    
    def validate(self, obj, name, value):
        if value == None:
            return None
        else:
            return super().validate(obj, name, value)
        
class CIntOrNone(BaseCInt):
    
    info_text = 'an int or None'
    
    def validate(self, obj, name, value):
        if value == None or value == "":
            return None
        else:
            return super().validate(obj, name, value)
        
        
class ScaleEnum(BaseEnum):
    """
    Defines an enumeration that contains one of the registered data scales
    """
    
    info_text = 'an enum containing one of the registered scales'

    def __init__ ( self, *args, **metadata ):
        """ Returns an Enum trait with values from the registered scales
        """
        self.name = ''
        self.values = list(scale._scale_mapping.keys())
        self.init_fast_validator( 5, self.values )
        super(BaseEnum, self).__init__(scale._scale_default, **metadata )
        
    def get_default_value(self):
        # this is so silly.  get_default_value is ... called once?  as traits
        # sets up?  idunno.  anyways, instead of returning _scale_default, we
        # need to return a reference to a function that returns _scale_Default.
        
        return (7, (self._get_default_value, (), None))
    
    def _get_default_value(self):
        return scale._scale_default

class Removed(TraitType):
    """
    Names a trait that was present in a previous version but was removed.
    
    Trait metadata:
    
        - **err_string** : the error string in the error
        
        - **gui** : if ``True``, don't return a backtrace (because it's very slow)
        
        - **warning** : if ``True``, raise a warning when the trait is referenced.
            Otherwise, raise an exception.
        
    """
    
    gui = False
    
    def __init__(self, **metadata):
        metadata.setdefault('err_string', 'Trait {} has been removed')
        metadata.setdefault('transient', True)
        super().__init__(**metadata)
    
    def get(self, obj, name):
        if not self.gui:
            # TODO - this is quite slow.  come up with a better way.
            curframe = inspect.currentframe()
            calframe = inspect.getouterframes(curframe)
            if calframe[1][3] == "copy_traits" or calframe[1][3] == "trait_get":
                return
             
            if self.warning:
                warn(self.err_string.format(name), CytoflowWarning)
            else:
                raise CytoflowError(self.err_string.format(name))
    
    def set(self, obj, name, value):
        if not self.gui:
            curframe = inspect.currentframe()
            calframe = inspect.getouterframes(curframe, 2)
            if calframe[1][3] == "copy_traits":
                return
             
            if self.warning:
                warn(self.err_string.format(name), CytoflowWarning)
            else:
                raise CytoflowError(self.err_string.format(name))
    
class Deprecated(TraitType):  
    """
    Names a trait that was present in a previous version but was renamed in this
    version.  When the trait is accessed, a warning is raised, and the access
    is passed through to the new trait.
    
    Trait metadata:
        - **new** : the name of the new trait
        
        - **err_string** : the error string in the error
        
        - **gui** : if ``True``, don't return a backtrace (because it's very slow)

    """
    gui = False
    
    def __init__(self, **metadata):
        metadata.setdefault('err_string', 'Trait {} is deprecated; please use {}')
        metadata.setdefault('transient', True)
        super().__init__(**metadata)
      
    def get(self, obj, name):
        if not self.gui:
            curframe = inspect.currentframe()
            calframe = inspect.getouterframes(curframe)
            if calframe[1][3] != "copy_traits" and calframe[1][3] != 'trait_get':
                warn(self.err_string.format(name, self.new), CytoflowWarning)
                
        return getattr(obj, self.new)
    
    def set(self, obj, name, value):
        if not self.gui:
            curframe = inspect.currentframe()
            calframe = inspect.getouterframes(curframe)
            if calframe[1][3] != "copy_traits":
                warn(self.err_string.format(name, self.new), CytoflowWarning)
        setattr(obj, self.new, value)
        
    