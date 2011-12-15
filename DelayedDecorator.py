#! /usr/bin/env python
"""
Copyright (C) 2011 by Peter A. Donis.
Released under the open source MIT license:
http://www.opensource.org/licenses/MIT

Decorator wrapper class to delay decorating the base function until
it is actually invoked. The use case that prompted writing this class
was the desire to "memoize" the generator encapsulated in the
``PowerSeries`` class. The obvious Pythonic way to do this is to
write a decorator that can be applied to a method on the class, and
make the method a generator function which the decorator then turns
into a memoized generator. However, if the decorator is implemented
in the usual way, this does not work properly; the memoization is done
at the class level, when what is really desired is to do it at the
instance level. In other words, the usual decorator implementation
would make the decorated method a normal member of the class, but
that would result in the memoized generator becoming common to *all*
instances of the class. Since each instance represents a different
power series, and hence a different generator, this is not what is
needed.

The solution is to delay applying the decorator until the decorated
function is actually called. For an ordinary function, this does
not really change anything; but for a method, it means the decorator
wrapper can now use the descriptor protocol to be invoked each time
the method is called on a new instance of the class. Then the
decorator can be applied separately for each instance; in the case
of the ``PowerSeries`` class, it means each series gets its own
memoized generator, as desired. As a side effect, the decorator is
also applied the first time the method is called as an unbound
method on the class itself; this use case should be very rare, but
it is supported for consistency with the behavior of normal methods.
"""

from new import instancemethod


class DelayedDecorator(object):
    """Wrapper that delays decorating a function until it is invoked.
    
    This class allows a decorator to be used with both ordinary functions and
    methods of classes. It wraps the function passed to it with the decorator
    passed to it, but with some special handling:
      
      - If the wrapped function is an ordinary function, it will be decorated
        the first time it is called.
      
      - If the wrapped function is a method of a class, it will be decorated
        separately the first time it is called on each instance of the class.
        It will also be decorated separately the first time it is called as
        an unbound method of the class itself (though this use case should
        be rare).
    """
    
    def __init__(self, deco, func):
        # The base decorated function (which may be modified, see below)
        self._func = func
        # The decorator that will be applied
        self._deco = deco
        # Variable to monitor calling as an ordinary function
        self.__decofunc = None
        # Variable to monitor calling as an unbound method
        self.__clsfunc = None
    
    def _decorated(self, cls=None, instance=None):
        """Return the decorated function.
        
        This method is for internal use only; it can be implemented by
        subclasses to modify the actual decorated function before it is
        returned. The ``cls`` and ``instance`` parameters are supplied so
        this method can tell how it was invoked. If it is not overridden,
        the base function stored when this class was instantiated will
        be decorated by the decorator passed when this class was instantiated,
        and then returned.
        
        Note that factoring out this method, in addition to allowing
        subclasses to modify the decorated function, ensures that the
        right thing is done automatically when the decorated function
        itself is a higher-order function (e.g., a generator function).
        Since this method is called every time the decorated function
        is accessed, a new instance of whatever it returns will be
        created (e.g., a new generator will be realized), which is
        exactly the expected semantics.
        """
        return self._deco(self._func)
    
    def __call__(self, *args, **kwargs):
        """Direct function call syntax support.
        
        This makes an instance of this class work just like the underlying
        decorator function when called directly. This use case assumes
        that the underlying decorator is an ordinary function, not a method.
        An internal reference to the decorated function is stored so that
        future direct calls will get the stored function.
        """
        if not self.__decofunc:
            self.__decofunc = self._decorated()
        return self.__decofunc(*args, **kwargs)
    
    def __get__(self, instance, cls):
        """Descriptor protocol support.
        
        This makes an instance of this class function correctly when it
        is used to decorate a method on a user-defined class. If called
        as a bound method, we store the decorated function in the instance
        dictionary, so we will not be called again for that instance. If
        called as an unbound method, we store a reference to the decorated
        function internally and use it on future unbound method calls.
        """
        if instance:
            deco = instancemethod(self._decorated(cls, instance), instance, cls)
            # This prevents us from being called again for this instance
            setattr(instance, self._func.__name__, deco)
        elif cls:
            if not self.__clsfunc:
                self.__clsfunc = instancemethod(self._decorated(cls), None, cls)
            deco = self.__clsfunc
        else:
            raise ValueError("Must supply instance or class to descriptor.")
        return deco
