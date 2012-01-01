#! /usr/bin/env python
"""
Copyright (C) 2011 by Peter A. Donis.
Released under the open source MIT license:
http://www.opensource.org/licenses/MIT

A wrapper class for generators that makes them indexable like a
sequence. Not strictly needed for ``PowerSeries``, but it's a
natural follow-on to memoizing generators so why not try it?

Note that for a real "production" implementation we would refactor
``MemoizedGenerator`` so this class could inherit from it. We don't
bother doing that here since it's more illustrative to have each
class standing alone. A more "production" implementation is given
in the ``plib`` library, available from PyPI at:

    http://pypi.python.org/pypi/plib

That implementation also handles the issue of memoizing separately
for different arguments; see the ``MemoizedGenerator`` docstring.

Typical usage (note that, as with ``MemoizedGenerator``, this
decorator only works as-is on ordinary functions; to use on
methods, use ``DelayedDecorator``):
    
    >>> @IndexedGenerator
    ... def numgen():
    ...     for i in xrange(10):
    ...         print "Yielding", i
    ...         yield i
    ...
    >>> ng = numgen()
    >>> for n in ng:
    ...     print n
    ...
    Yielding 0
    0
    Yielding 1
    1
    Yielding 2
    2
    Yielding 3
    3
    Yielding 4
    4
    Yielding 5
    5
    Yielding 6
    6
    Yielding 7
    7
    Yielding 8
    8
    Yielding 9
    9

Now that the generator is exhausted, further iteration
won't yield any more items, and explicit calls to ``next``
will raise ``StopIteration``:

    >>> for n in ng:
    ...     print n
    ...
    >>> next(ng)
    Traceback (most recent call last):
    ...
    StopIteration

We can still continue to index into the generator like a
sequence, even though it is exhausted:

    >>> for k in xrange(10):
    ...     print ng[k]
    ...
    0
    1
    2
    3
    4
    5
    6
    7
    8
    9

If we realize the generator again, we can iterate through
it again, but we won't actually advance the underlying
generator any more; it is already exhausted and we are
retrieving items from the cache:

    >>> for n in numgen():
    ...     print n
    ...
    0
    1
    2
    3
    4
    5
    6
    7
    8
    9

The same goes for explicit calls to ``next``; we can
start iteration over again but only from the cache:

    >>> next(numgen())
    0
    >>> next(numgen())
    0

Indexing into the generator forces it to iterate to the
requested index:

    >>> @IndexedGenerator
    ... def numgen1():
    ...     for i in xrange(10):
    ...         print "Yielding", i
    ...         yield i
    ...
    >>> ng1 = numgen1()
    >>> ng1[4]
    Yielding 0
    Yielding 1
    Yielding 2
    Yielding 3
    Yielding 4
    4

Requesting an index that's already been iterated past in
the underlying generator will, once again, retrieve from
the cache:

    >>> ng1[2]
    2

Note that indexing is separate from iteration, just as with
a regular sequence; we can still iterate over all the items
one time, even though we've indexed halfway in (so we only see
the underlying generator yield for the last 5 items, the first
5 come from the cache):

    >>> for n in ng1:
    ...     print n
    ...
    0
    1
    2
    3
    4
    Yielding 5
    5
    Yielding 6
    6
    Yielding 7
    7
    Yielding 8
    8
    Yielding 9
    9

But again, we can only iterate once for a given realization
of the generator:

    >>> for n in ng1:
    ...     print n
    ...

Note that if the generator has not been exhausted, negative
indexes don't work, because we don't have a sequence length
to normalize them to:

    >>> @IndexedGenerator
    ... def numgen2():
    ...     for i in xrange(10):
    ...         print "Yielding", i
    ...         yield i
    ...
    >>> ng2 = numgen2()
    >>> ng2[0]
    Yielding 0
    0
    >>> ng2[-1]
    Traceback (most recent call last):
    ...
    IndexError: sequence index out of range

However, once the generator is exhausted, it knows its
length, and negative indexes will now work (note that
asking for a high enough *positive* index has the effect
of exhausting the generator, but it is not exhausted until
we go beyond the last item, not just to it):

    >>> ng2[9]
    Yielding 1
    Yielding 2
    Yielding 3
    Yielding 4
    Yielding 5
    Yielding 6
    Yielding 7
    Yielding 8
    Yielding 9
    9
    >>> ng2[-1]
    Traceback (most recent call last):
    ...
    IndexError: sequence index out of range
    >>> ng2[10]
    Traceback (most recent call last):
    ...
    IndexError: sequence index out of range
    >>> ng2[-1]
    9

Note that this implementation does not support slicing, since that
adds considerable complication; the implementation in ``plib``
(see above) does.
"""

from itertools import count


class indexediterator(object):
    # Helper class to be returned as the actual generator with
    # indexing; wraps the generator in an iterator that also
    # supports item retrieval by index.
    
    def __init__(self, gen):
        self.__gen = gen  # the generator that created us
        self.__iter = gen._iterable()
    
    def __iter__(self):
        # Return the generator function; note that we return
        # the same one each time, which matches the semantics
        # of actual generators (i.e., once the generator function
        # is called, iter(gen) returns the same iterator and does
        # not reset the state)
        return self.__iter
    
    def next(self):
        # Return next item from generator
        term = next(self.__iter)
        if term == self.__gen.sentinel:
            raise StopIteration
        return term
    
    def __len__(self):
        # If the generator is exhausted, we know its length, so
        # we can use that information; if not, we raise TypeError,
        # just like any other object with no length
        result = self.__gen._itemcount()
        if result is None:
            raise TypeError, "object of type %s has no len()" % self.__class__.__name__
        return result
    
    def __getitem__(self, index):
        # Return the item at index, advancing the generator if
        # necessary; if the generator is exhausted before index,
        # raise IndexError, just like any other sequence when an
        # index out of range is requested
        result = self.__gen._retrieve(index)
        if result is self.__gen.sentinel:
            raise IndexError, "sequence index out of range"
        return result


class IndexedGenerator(object):
    """Make a generator indexable like a sequence.
    
    A side benefit is that the generator is memoized as well,
    since we have to keep a cache of already generated elements
    so we don't have to re-realize the generator if the element
    at a given index is accessed more than once.
    
    Note that the sequence is not mutable. Also note that, while
    it behaves like a sequence for indexing, it behaves like a
    generator with regard to iteration; repeated calls to ``next``
    (or something like a ``for`` loop) will eventually exhaust
    it and ``StopIteration`` will be raised, even though indexing
    into it will still retrieve items already yielded.
    
    Like ``MemoizedGenerator``, this class can only be used
    directly to decorate an ordinary function. It is recommended
    that the ``indexable_generator`` decorator be used instead
    since it works on methods as well.
    """
    
    sentinel = object()
    
    def __init__(self, gen):
        # The underlying generator
        self.__gen = gen
        # Memoization fields
        self.__cache = []
        self.__iter = None
        self.__empty = False
    
    def _retrieve(self, n):
        # Retrieve the nth item from the generator, advancing
        # it if necessary
        
        # First, negative indexes are invalid unless the generator
        # is exhausted, so check that first
        if n < 0:
            end = self._itemcount()
            if (end is None) or (end == 0):
                # No length known yet, or no items at all
                return self.sentinel
            else:
                return self.__cache[end + n]
        # Now try to advance the generator (which may empty it,
        # or it may already be empty)
        while (not self.__empty) and (n >= len(self.__cache)):
            try:
                term = next(self.__iter)
            except StopIteration:
                self.__empty = True
            else:
                self.__cache.append(term)
        if self.__empty and (n >= len(self.__cache)):
            return self.sentinel
        return self.__cache[n]
    
    def _iterable(self):
        # Yield terms from the generator
        for n in count():
            term = self._retrieve(n)
            if term is self.sentinel:
                break
            yield term
    
    def _itemcount(self):
        # Once we are exhausted, the number of items in the
        # sequence is known, so we can provide it; otherwise
        # we return None
        if self.__empty:
            return len(self.__cache)
        return None
    
    def __call__(self, *args, **kwargs):
        """Make instances of this class callable.
        
        This method must be present, and must be a generator
        function, so that class instances work the same as their
        underlying generators.
        """
        if not (self.__empty or self.__iter):
            self.__iter = self.__gen(*args, **kwargs)
        return indexediterator(self)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
