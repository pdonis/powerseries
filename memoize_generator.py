#! /usr/bin/env python
"""
Copyright (C) 2011 by Peter A. Donis.
Released under the open source MIT license:
http://www.opensource.org/licenses/MIT

A decorator for memoizing generators that works with both
ordinary generator functions and generators that are methods
on classes, and delays decoration of its generator so that
if it is a method, each instance of its class gets its own
memoized generator. See the documentation for the underlying
class, ``MemoizedGenerator``, for more details on the general
idea behind memoizing generators. See the documentation for
the ``DelayedDecorator`` class for more details on delaying
decoration.
"""

from functools import partial

from DelayedDecorator import DelayedDecorator
from MemoizedGenerator import MemoizedGenerator


memoize_generator = partial(DelayedDecorator, MemoizedGenerator)
