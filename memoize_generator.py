#! /usr/bin/env python
"""
Copyright (C) 2011 by Peter A. Donis.
Released under the open source MIT license:
http://www.opensource.org/licenses/MIT

A decorator for memoizing generators that works with both
ordinary generator functions and generators that are methods
on classes. See the documentation for the underlying class,
``MemoizedGenerator``, for more details on the general idea
behind memoizing generators.
"""

from AllPurposeDecorator import AllPurposeDecorator
from MemoizedGenerator import MemoizedGenerator


class memoize_generator(AllPurposeDecorator):
    """Decorator for memoizing generators.
    
    This decorator wraps the ``MemoizedGenerator`` class so that it
    can be used for methods as well as ordinary functions.
    """
    
    def _decorated(self, cls=None, instance=None):
        """Memoize the function we are decorating before returning it.
        
        Assumes that the function being decorated is a generator.
        """
        return MemoizedGenerator(self._func)
