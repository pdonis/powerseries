#! /usr/bin/env python
"""
Copyright (C) 2011 by Peter A. Donis.
Released under the open source MIT license:
http://www.opensource.org/licenses/MIT
"""

from new import instancemethod


class AllPurposeDecorator(object):
    """Generic decorator that can wrap both ordinary functions and methods.
    
    This class allows a decorator to wrap both ordinary functions and
    methods of classes. It is intended to be used as a mixin class by
    decorators implemented as classes.
    
    An instance of this class can be used as a decorator in the following ways:
    
      - If the decorator is called directly (i.e., the ``__call__`` method is
        invoked), it assumes that the decorator it wraps is an ordinary
        function and just returns it directly;
      
      - If the decorator is accessed as an attribute via the descriptor
        protocol (i.e., the ``__get__`` method is invoked), it assumes
        that the decorator it wraps is a method, and forms a bound
        method instance using the instance passed to it as ``self``; the
        bound method is returned as the decorator.
      
      - If the decorator is accessed via the descriptor protocol from a
        class instead of a class instance (i.e., the ``instance`` parameter
        to ``__get__`` is ``None``), it forms an unbound method using the
        class given, and returns that as the decorator. This usage should
        be extremely rare, but it is provided for consistency with the
        normal behavior of methods called via the class instead of the
        instance.
    """
    
    def __init__(self, func):
        # The base decorated function (which may be modified, see below)
        self._func = func
        # Containers for storing manufactured methods
        self.__clsmap = {}
        self.__instmap = {}
    
    def _decorated(self, cls=None, instance=None):
        """Return the decorated function.
        
        This method is for internal use only; it can be implemented by
        subclasses to modify the actual decorated function before it is
        returned. The ``cls`` and ``instance`` parameters are supplied so
        this method can tell how it was invoked. If it is not overridden,
        the function passed when this class was instantiated (i.e., when
        it was invoked as a decorator) will be returned unchanged.
        
        Note that factoring out this method, in addition to allowing
        subclasses to modify the decorated function, ensures that the
        right thing is done automatically when the decorated function
        itself is a higher-order function (e.g., a generator function).
        Since this method is called every time the decorated function
        is accessed, a new instance of whatever it returns will be
        created (e.g., a new generator will be realized), which is
        exactly the expected semantics.
        """
        return self._func
    
    def __call__(self, *args, **kwargs):
        """Direct function call syntax support.
        
        This makes an instance of this class work just like the underlying
        decorator function when called directly. This use case assumes
        that the underlying decorator is an ordinary function, not a method.
        """
        return self._decorated()(*args, **kwargs)
    
    def __get__(self, instance, cls):
        """Descriptor protocol support.
        
        This makes an instance of this class function correctly when it
        is used to decorate a method on a user-defined class. We store
        a map of methods keyed by the ``id`` attribute of the instance,
        so that we can return a customized method for each instance. We
        do the same for classes, but this use case should be rare (see
        the class docstring above).
        """
        if instance:
            key = id(instance)
            if  key not in self.__instmap:
                self.__instmap[key] = instancemethod(self._decorated(cls, instance), instance, cls)
            deco = self.__instmap[key]
        elif cls:
            key = id(cls)
            if key not in self.__clsmap:
                self.__clsmap[key] = instancemethod(self._decorated(cls), None, cls)
            deco = self.__clsmap[key]
        else:
            raise ValueError("Must supply instance or class to descriptor.")
        return deco
