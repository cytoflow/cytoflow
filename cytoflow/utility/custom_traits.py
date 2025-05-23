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
cytoflow.utility.custom_traits
------------------------------

Custom traits for `cytoflow`

`PositiveInt`, `PositiveFloat` -- versions of `traits.trait_types.Int` and `traits.trait_types.Float` that must be 
positive (and optionally 0).

`PositiveCInt`, `PositiveCFloat` -- versions of `traits.trait_types.CInt`, `traits.trait_types.CFloat` that must
be positive (and optionally 0).

`IntOrNone`, `FloatOrNone` -- versions of `traits.trait_types.Int` and `traits.trait_types.Float` that may also
hold the value ``None``.

`CIntOrNone`, `CFloatOrNone` -- versions of `traits.trait_types.CInt` and `traits.trait_types.CFloat` that may also
hold the value ``None``.

`ScaleEnum` -- an enumeration whose value is one of the registered scales.

`Removed` -- a trait that was present in a previous version but was removed.

`Deprecated` -- a trait that was present in a previous version but was renamed. 
"""

from warnings import warn
import inspect

from traits.api import (BaseInt, BaseCInt, BaseFloat, BaseCFloat, BaseEnum, 
                        BaseStr, TraitType)
from traits.trait_errors import TraitError
from . import scale
from . import CytoflowError, CytoflowWarning

import cytoflow


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
    Defines a trait whose converted value must be a positive integer
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
    Defines a trait whose converted value must be a positive float
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
    """
    Defines a trait whose value must be a float or None
    """
    
    info_text = 'a float or None'
    
    def validate(self, obj, name, value):
        if value == "" or value == None:
            return None
        else:
            return super().validate(obj, name, value)

class CFloatOrNone(BaseCFloat):
    """
    Defines a trait whose converted value must be a float or None
    """
    
    info_text = 'a float or None'
    
    def validate(self, obj, name, value):
        if value == None or value == "":
            return None
        else:
            return super().validate(obj, name, value)
        
    
class UnitFloat(BaseFloat):
    """
    Defines a trait whose value must be a float between 0 and 1 (inclusive)
    """
    
    def validate(self, obj, name, value):
        value = super().validate(obj, name, value)
        if value < 0.0:
            return 0.0
        if value > 1.0:
            return 1.0
        return value

class IntOrNone(BaseInt):
    """
    Defines a trait whose value must be an integer or None
    """
    
    info_text = 'an int or None'
    
    def validate(self, obj, name, value):
        if value == None:
            return None
        else:
            return super().validate(obj, name, value)
        
class CIntOrNone(BaseCInt):
    """
    Defines a trait whose converted value must be an integer or None
    """
    
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
        self.name = None
        self.values = list(scale._scale_mapping.keys())
        super(BaseEnum, self).__init__(scale._scale_default, **metadata )
        
    def get_default_value(self):
        # this is so silly.  get_default_value is ... called once?  as traits
        # sets up?  idunno.  anyways, instead of returning _scale_default, we
        # need to return a reference to a function that returns _scale_default.
        
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
        
    def __init__(self, **metadata):
        metadata.setdefault('err_string', 'Trait {} has been removed')
        metadata.setdefault('transient', True)
        super().__init__(**metadata)
    
    def get(self, obj, name):
        if not cytoflow.RUNNING_IN_GUI:
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
        if not cytoflow.RUNNING_IN_GUI:
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
    Names a trait that was present in a previous version but was renamed.  
    When the trait is accessed, a warning is raised, and the access
    is passed through to the new trait.
    
    Trait metadata:
        - **new** : the name of the new trait
        
        - **err_string** : the error string in the error
        
        - **gui** : if ``True``, don't return a backtrace (because it's very slow)

    """
    
    def __init__(self, **metadata):
        metadata.setdefault('err_string', 'Trait {} is deprecated; please use {}')
        metadata.setdefault('transient', True)
        super().__init__(**metadata)
      
    def get(self, obj, name):
        if not cytoflow.RUNNING_IN_GUI:
            curframe = inspect.currentframe()
            calframe = inspect.getouterframes(curframe)
            if calframe[1][3] != "copy_traits" and calframe[1][3] != 'trait_get':
                warn(self.err_string.format(name, self.new), CytoflowWarning)
                
        return getattr(obj, self.new)
    
    def set(self, obj, name, value):
        if not cytoflow.RUNNING_IN_GUI:
            curframe = inspect.currentframe()
            calframe = inspect.getouterframes(curframe)
            if calframe[1][3] != "copy_traits":
                warn(self.err_string.format(name, self.new), CytoflowWarning)
        setattr(obj, self.new, value)
        
class ChangedStr(BaseStr):
    """
    When an invalid type is set, return a custom string.
    """
    
    def __init__(self, **metadata):
        metadata.setdefault('err_string', "This trait now takes a Str.")
        super().__init__(**metadata)
    
    def error(self, _, name, value):
        err = TraitError(object, name, self.full_info(object, name, value), value)
        err.args = (err.args[0] + " " + self.err_string,)
        raise err
        
    