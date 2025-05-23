# This file was automatically generated by SWIG (https://www.swig.org).
# Version 4.2.0
#
# Do not make changes to this file unless you know what you are doing - modify
# the SWIG interface file instead.

from sys import version_info as _swig_python_version_info

try:
  import _Logicle
except:
  from . import _Logicle


try:
    import builtins as __builtin__
except ImportError:
    import __builtin__

def _swig_repr(self):
    try:
        strthis = "proxy of " + self.this.__repr__()
    except __builtin__.Exception:
        strthis = ""
    return "<%s.%s; %s >" % (self.__class__.__module__, self.__class__.__name__, strthis,)


def _swig_setattr_nondynamic_instance_variable(set):
    def set_instance_attr(self, name, value):
        if name == "this":
            set(self, name, value)
        elif name == "thisown":
            self.this.own(value)
        elif hasattr(self, name) and isinstance(getattr(type(self), name), property):
            set(self, name, value)
        else:
            raise AttributeError("You cannot add instance attributes to %s" % self)
    return set_instance_attr


def _swig_setattr_nondynamic_class_variable(set):
    def set_class_attr(cls, name, value):
        if hasattr(cls, name) and not isinstance(getattr(cls, name), property):
            set(cls, name, value)
        else:
            raise AttributeError("You cannot add class attributes to %s" % cls)
    return set_class_attr


def _swig_add_metaclass(metaclass):
    """Class decorator for adding a metaclass to a SWIG wrapped class - a slimmed down version of six.add_metaclass"""
    def wrapper(cls):
        return metaclass(cls.__name__, cls.__bases__, cls.__dict__.copy())
    return wrapper


class _SwigNonDynamicMeta(type):
    """Meta class to enforce nondynamic attributes (no new attributes) for a class"""
    __setattr__ = _swig_setattr_nondynamic_class_variable(type.__setattr__)


class Logicle(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc="The membership flag")
    __repr__ = _swig_repr

    def __init__(self, *args):
        _Logicle.Logicle_swiginit(self, _Logicle.new_Logicle(*args))
    __swig_destroy__ = _Logicle.delete_Logicle

    def T(self):
        return _Logicle.Logicle_T(self)

    def W(self):
        return _Logicle.Logicle_W(self)

    def M(self):
        return _Logicle.Logicle_M(self)

    def A(self):
        return _Logicle.Logicle_A(self)

    def a(self):
        return _Logicle.Logicle_a(self)

    def b(self):
        return _Logicle.Logicle_b(self)

    def c(self):
        return _Logicle.Logicle_c(self)

    def d(self):
        return _Logicle.Logicle_d(self)

    def f(self):
        return _Logicle.Logicle_f(self)

    def w(self):
        return _Logicle.Logicle_w(self)

    def x0(self):
        return _Logicle.Logicle_x0(self)

    def x1(self):
        return _Logicle.Logicle_x1(self)

    def x2(self):
        return _Logicle.Logicle_x2(self)

    def scale(self, value):
        return _Logicle.Logicle_scale(self, value)

    def inverse(self, scale):
        return _Logicle.Logicle_inverse(self, scale)

    def dynamicRange(self):
        return _Logicle.Logicle_dynamicRange(self)

    def axisLabels(self, label):
        return _Logicle.Logicle_axisLabels(self, label)

# Register Logicle in _Logicle:
_Logicle.Logicle_swigregister(Logicle)
cvar = _Logicle.cvar
Logicle.DEFAULT_DECADES = _Logicle.cvar.Logicle_DEFAULT_DECADES

class FastLogicle(Logicle):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc="The membership flag")
    __repr__ = _swig_repr

    def __init__(self, *args):
        _Logicle.FastLogicle_swiginit(self, _Logicle.new_FastLogicle(*args))
    __swig_destroy__ = _Logicle.delete_FastLogicle

    def scale(self, value):
        return _Logicle.FastLogicle_scale(self, value)

    def bins(self):
        return _Logicle.FastLogicle_bins(self)

    def intScale(self, value):
        return _Logicle.FastLogicle_intScale(self, value)

    def inverse(self, *args):
        return _Logicle.FastLogicle_inverse(self, *args)

# Register FastLogicle in _Logicle:
_Logicle.FastLogicle_swigregister(FastLogicle)
FastLogicle.DEFAULT_BINS = _Logicle.cvar.FastLogicle_DEFAULT_BINS


