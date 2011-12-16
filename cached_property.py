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

Typical usage:

    >>> class Test(object):
    ...     def test(self):
    ...         print "Doing initial calculation..."
    ...         return "Test done."
    ...     test = cached_property(test)
    ... 
    >>> t = Test()
    >>> 'test' in t.__dict__
    False
    >>> print t.test
    Doing initial calculation...
    Test done.
    >>> 'test' in t.__dict__
    True
    >>> print t.test
    Test done.

The cached value can be explicitly deleted from the instance
dict, or overwritten by an explicit assignment to the
attribute. Deletion "resets" the property, so it has to be
computed again on the next access.

    >>> del t.test
    >>> 'test' in t.__dict__
    False
    >>> t.test = "Other value."
    >>> print t.test
    Other value.
    >>> del t.test
    >>> print t.test
    Doing initial calculation...
    Test done.

One other wrinkle: ``hasattr`` also triggers the property
computation.

    >>> del t.test
    >>> hasattr(t, 'test')
    Doing initial calculation...
    True
    >>> 'test' in t.__dict__
    True
    >>> print t.test
    Test done.
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


if __name__ == '__main__':
    import doctest
    doctest.testmod()
