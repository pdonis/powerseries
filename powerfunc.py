#! /usr/bin/env python
"""
Copyright (C) 2011 by Peter A. Donis.
Released under the open source MIT license:
http://www.opensource.org/licenses/MIT

This module uses the representation of power series as
generators in the ``PowerSeries`` class to actually compute
functions, taking rational or floating point numbers as
arguments. In principle this is straightforward; we just
sum the terms. However, the ``PowerSeries`` class represents
series formally and does not deal at all with convergence;
but to actually use series to compute their corresponding
functions, convergence is a critical issue.
"""

from fractions import Fraction
from itertools import islice


class DivergenceError(ArithmeticError): pass


class PowerFunction(object):
    """Wrap a power series and compute its function.
    
    A power series is represented as an iterable of coefficients; the
    nth term is the coefficient of x**n. Uses this representation to
    compute the value of F(x), where F is the function whose power
    series is represented. Convergence testing is supported; an
    exception is raised if a divergent value is requested.
    
    Note that, although this class was written to work with the
    ``PowerSeries`` class, it can actually work with any iterable
    that yields terms of a series.
    """
    
    error = Fraction(1, 10000)
    
    ratio_max = 5
    
    def __init__(self, series):
        self.__series = series
    
    @property
    def series(self):
        return self.__series
    
    def __call__(self, x, terms=None, error=None, figures=None):
        """Compute the function of this power series on x.
        
        The ``terms`` argument controls how many terms of the series
        are used for the computation. In the default case, where
        ``terms`` is ``None``, the series is computed until it
        converges to within the desired error tolerance (the
        ``error`` argument controls this) or the desired number of
        significant figures (the ``figures`` argument controls this;
        internally, it is converted to an error tolerance equal to
        1 / 10^figures). In this case, ``DivergenceError`` is raised
        if the series fails to converge; a number of different
        convergence criteria are used, as described in the docstring
        for the ``test_convergence`` method, below.
        
        If ``terms`` is provided, that number of terms is computed
        and their sum returned, regardless of convergence. (If a
        divergent value is requested, an overflow may occur; no
        checking is done to avoid this.)
        """
        if isinstance(x, (int, long)):
            x = Fraction(x, 1)
        elif isinstance(x, float):
            x = Fraction.from_float(x)
        if not isinstance(x, Fraction):
            raise ValueError("Power series function requires fraction as argument.")
        if terms is not None:
            return sum(t * (x**n) for n, t in enumerate(islice(self.__series, terms)))
        if figures is not None:
            error = Fraction(1, 10**figures)
        elif error is None:
            error = self.error
        error = abs(error)
        result = last = Fraction(0, 1)
        self._clear_testfields()
        xt = Fraction(1, 1)
        for n, t in enumerate(self.__series):
            try:
                term = t * xt
                result += term
            except OverflowError:
                raise DivergenceError("Series diverged to overflow point.")
            # This will raise DivergenceError if necessary
            if self.test_convergence(x, n, term, last, result, error):
                break
            last = term
            xt *= x
        return result
    
    def _clear_testfields(self):
        # Internal method to clear convergence testing fields
        self.__ratio_last = None  # last nonzero term for ratio test
        self.__ratio_count = 0  # number of times the ratio test has failed
    
    def test_convergence(self, x, n, term, last, result, error):
        """Test series convergence.
        """
        if term != 0:
            if abs(term) < (error * result):
                return True
            if self.__ratio_last and ((term / self.__ratio_last) > 1):
                self.__ratio_count += 1
            if self.__ratio_count > self.ratio_max:
                raise DivergenceError("Series failed ratio test.")
            self.__ratio_last = term
        return False
