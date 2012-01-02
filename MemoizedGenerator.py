#! /usr/bin/env python
"""
Copyright (C) 2011 by Peter A. Donis.
Released under the open source MIT license:
http://www.opensource.org/licenses/MIT

A wrapper class for generators that "memoizes" them, so that even
if the generator is realized multiple times, each term only gets
computed once (after that the result is simply returned from a
cache).

This class was written for use by the ``PowerSeries`` class, but
the implementation is general. For example, it correctly handles
finite-length generators, even though all ``PowerSeries`` instances
will look infinite as far as this class is concerned (i.e., a
wrapped ``PowerSeries`` generator will never set the class's
internal ``__empty`` flag to ``True``). However, there is one
issue it does not handle correctly: it memoizes all realizations
of its generator, even if they are called with different arguements,
which is fine for ``PowerSeries`` but is not the desired generic
behavior. A more "production" implementation that handles this issue
correctly is in the ``plib`` library, available from PyPI at:

    http://pypi.python.org/pypi/plib

Functional programming types will note that this implementation
is done using a class, not a function. Doing it as a function in
Python would require some inelegant hacks with mutable containers
since Python does not allow a closure's inner function to mutate
variables in the closure's outer function. (Python 2.7 adds the
``nonlocal`` keyword to allow such behavior, but I didn't want to
require 2.7 for this since many Linux distributions are still at
2.6 as of this writing.) Lisp hackers will of course make smug
comments on this limitation of Python's, but I don't care. :-)

Typical usage and comparison with non-memoized generators:
    
    >>> def gen():
    ...     for n in xrange(2):
    ...         print "Yielding", n
    ...         yield n
    ...     print "Stopping"
    ...
    >>> g1 = gen()
    >>> g2 = gen()
    >>> next(g1)
    Yielding 0
    0
    >>> next(g2)
    Yielding 0
    0
    >>> next(g2)
    Yielding 1
    1
    >>> next(g1)
    Yielding 1
    1
    >>> def tryit(g):
    ...     try:
    ...         next(g)
    ...     except StopIteration:
    ...         pass
    >>> tryit(g1)
    Stopping
    >>> tryit(g2)
    Stopping
    >>> gen = MemoizedGenerator(gen)
    >>> g3 = gen()
    >>> g4 = gen()
    >>> next(g3)
    Yielding 0
    0
    >>> next(g4)
    0
    >>> next(g4)
    Yielding 1
    1
    >>> next(g3)
    1
    >>> tryit(g3)
    Stopping
    >>> tryit(g4)
"""

from itertools import count


class MemoizedGenerator(object):
    """Memoize a generator to avoid computing any term more than once.
    
    Generic implementation of a "memoized" generator for cases where each
    term of the generator is expensive to compute, but it is known that
    every realization of the generator will compute the same terms. This
    class allows multiple realizations of the generator to share a
    single computation of each term.
    
    This class can be used to wrap a generator directly, but it only
    works for ordinary functions (i.e., not methods). For ease of use
    and flexibility, it is recommended that the ``memoize_generator``
    decorator be used instead, since that automatically handles both
    ordinary functions and methods.
    
    Note that this class is *not* thread-safe; it assumes that all
    realizations of the memoized generator run in the same thread,
    so that it is guaranteed that no more than one realization will
    be mutating the memoization fields at a time.
    
    Note also that this class memoizes all realizations of its underlying
    generator, even if they are invoked with different arguments. For
    the usage here, this is not an issue, but it may be for other use
    cases. The more "production" implementation in the ``plib`` library
    handles this issue correctly; it can be found on PyPI at:
        
        http://pypi.python.org/pypi/plib
    """
    
    def __init__(self, gen):
        # The underlying generator
        self.__gen = gen
        # Memoization fields
        self.__cache = []
        self.__iter = None
        self.__empty = False
    
    def __call__(self, *args, **kwargs):
        """Make instances of this class callable.
        
        This method must be present, and must be a generator
        function, so that class instances work the same as their
        underlying generators.
        """
        if not (self.__empty or self.__iter):
            self.__iter = self.__gen(*args, **kwargs)
        for n in count():
            # First check the cache
            if n < len(self.__cache):
                yield self.__cache[n]
            # See if another copy of the generator emptied it
            # since our last iteration
            elif self.__empty:
                break
            # If none of the above, advance the generator
            # (which may empty it)
            else:
                try:
                    term = next(self.__iter)
                except StopIteration:
                    self.__empty = True
                    break
                else:
                    self.__cache.append(term)
                    yield term


if __name__ == '__main__':
    import doctest
    doctest.testmod()
