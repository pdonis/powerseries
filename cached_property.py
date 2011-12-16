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

class CachedProperty(object):
    """Non-data descriptor class for cached property.
    
    The expected typical use case is to be called from the
    cached_property function, which generates the name of
    the property automatically, but the class can also be
    instantiated directly with an explicit name supplied.
    """
    
    def __init__(self, aname, fget, doc=None):
        self.aname = aname
        self.fget = fget
        self.__doc__ = doc
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        result = self.fget(obj)
        setattr(obj, self.aname, result)
        return result


def cached_property(fget, doc=None):
    """Function to return cached property instance.
    
    We need this as a wrapper to supply the name of the property
    by magic rather than force the user to enter it by hand;
    this is done by looking up the name of the fget function
    (which also allows this function to be used as a decorator
    and have the intended effect).
    """
    
    if doc is None:
        doc = fget.__doc__
    return CachedProperty(fget.__name__, fget, doc)
