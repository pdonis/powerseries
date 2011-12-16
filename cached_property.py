#! /usr/bin/env python
"""
Copyright (C) 2011 by Peter A. Donis.
Released under the open source MIT license:
http://www.opensource.org/licenses/MIT

A read-only property decorator that caches its result in
the instance dictionary, so the actual underlying function
only gets called once. Useful when computing the function
is expensive, or when (as in the case of the ``PowerSeries``
class) it is desired to have the property return the same
object every time, to take maximum advantage of other
optimizations such as memoizing each series' generator.
"""


class cached_property(object):
    """Decorator class for cached property.
    
    This decorator works the same as the built-in ``property``
    decorator, but caches the property value in the instance
    dictionary so that the underlying function is only called
    once. The property is read-only.
    """
    
    def __init__(self, fget, name=None, doc=None):
        self.__fget = fget
        self.__name = name or fget.__name__
        self.__doc__ = doc
    
    def __get__(self, instance, cls):
        if instance is None:
            return self
        result = self.__fget(instance)
        setattr(instance, self.__name, result)
        return result
