#! /usr/bin/env python
"""
Copyright (C) 2011 by Peter A. Donis.
Released under the open source MIT license:
http://www.opensource.org/licenses/MIT

A class decorator that ensures that only one instance of
the class exists for each distinct set of constructor
arguments.

Typical usage:
    
    >>> @cached_class
    ... class Test(object):
    ...     def __init__(self, *args, **kwds):
    ...         self.args = args
    ...         self.kwds = kwds
    ...
    >>> t1 = Test(0, a=1)
    >>> t1.args
    (0,)
    >>> t1.kwds
    {'a': 1}

A second call to the class with the same arguments will
return the same instance:

    >>> t1a = Test(0, a=1)
    >>> t1a.args
    (0,)
    >>> t1a.kwds
    {'a': 1}
    >>> t1a is t1
    True

Each new set of arguments creates a new instance; partial
matches are still new sets of arguments:

    >>> t2 = Test(1, b=2)
    >>> t2.args
    (1,)
    >>> t2.kwds
    {'b': 2}
    >>> t2 is t1
    False
    >>> t3 = Test(0, b=2)
    >>> t3.args
    (0,)
    >>> t3.kwds
    {'b': 2}
    >>> any(t3 is t for t in (t1, t2))
    False
    >>> t4 = Test(1, a=1)
    >>> t4.args
    (1,)
    >>> t4.kwds
    {'a': 1}
    >>> any(t4 is t for t in (t1, t2, t3))
    False

An empty set of arguments is also treated as a distinct
set of arguments and is cached like any other:

    >>> t5 = Test()
    >>> t5.args
    ()
    >>> t5.kwds
    {}
    >>> any(t5 is t for t in (t1, t2, t3, t4))
    False
    >>> t5a = Test()
    >>> t5a is t5
    True

The same goes for positional-only or keyword-only sets
of arguments:

    >>> t6 = Test(0)
    >>> t6.args
    (0,)
    >>> t6.kwds
    {}
    >>> any(t6 is t for t in (t1, t2, t3, t4, t5))
    False
    >>> t6a = Test(0)
    >>> t6a is t6
    True
    >>> t7 = Test(a=1)
    >>> t7.args
    ()
    >>> t7.kwds
    {'a': 1}
    >>> any(t7 is t for t in (t1, t2, t3, t4, t5, t6))
    False
    >>> t7a = Test(a=1)
    >>> t7a is t7
    True

There is also no possibility of "overlap" between
positional and keyword arguments, even if they have
the same values:

    >>> t8 = Test('a', 'a')
    >>> t8.args
    ('a', 'a')
    >>> t8.kwds
    {}
    >>> t9 = Test(a='a')
    >>> t9.args
    ()
    >>> t9.kwds
    {'a': 'a'}
    >>> t9 is t8
    False
    >>> t10 = Test('a', a='a')
    >>> t10.args
    ('a',)
    >>> t10.kwds
    {'a': 'a'}
    >>> t10 is t8
    False
    >>> t10 is t9
    False

Finally, unhashable arguments return a new instance
each time, even for values that compare equal:

    >>> t11 = Test([])
    >>> t12 = Test([])
    >>> t11 is t12
    False
    >>> (t11.args == t12.args) and (t11.kwds == t12.kwds)
    True
    >>> t13 = Test(a=[])
    >>> t14 = Test(a=[])
    >>> t13 is t14
    False
    >>> (t13.args == t14.args) and (t13.kwds == t14.kwds)
    True
    >>> t15 = Test([], a=[])
    >>> t16 = Test([], a=[])
    >>> t15 is t16
    False
    >>> (t15.args == t16.args) and (t15.kwds == t16.kwds)
    True
    
"""

from functools import wraps


def cached_class(klass):
    """Decorator to cache class instances by constructor arguments.
    
    We "tuple-ize" the keyword arguments dictionary since
    dicts are mutable; keywords themselves are strings and
    so are always hashable, but if any arguments (keyword
    or positional) are non-hashable, that set of arguments
    is not cached.
    """
    cache = {}
    @wraps(klass, assigned=('__name__', '__module__'), updated=())
    class _decorated(klass):
        # The wraps decorator can't do this because __doc__
        # isn't writable once the class is created
        __doc__ = klass.__doc__
        def __new__(cls, *args, **kwds):
            key = args + tuple(kwds.iteritems())
            try:
                inst = cache.get(key, None)
            except TypeError:
                # Can't cache this set of arguments
                inst = key = None
            if inst is None:
                # Technically this is cheating, but it works,
                # and takes care of initializing the instance
                # (so we can override __init__ below safely);
                # calling up to klass.__new__ would be the
                # "official" way to create the instance, but
                # that raises DeprecationWarning if there are
                # args or kwds and klass does not override
                # __new__ (which most classes don't), because
                # object.__new__ takes no parameters (and in
                # Python 3 the warning will become an error)
                inst = klass(*args, **kwds)
                # This makes isinstance and issubclass work
                # properly
                inst.__class__ = _decorated
                if key is not None:
                    cache[key] = inst
            return inst
        def __init__(self, *args, **kwds):
            # This will be called every time __new__ is
            # called, so we skip initializing here and do
            # it only when the instance is created above
            pass
    return _decorated


if __name__ == '__main__':
    import doctest
    doctest.testmod()
