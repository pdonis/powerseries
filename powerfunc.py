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
functions, convergence is of course an issue. The
``PowerFunction`` class in this module implements simple
convergence testing; it also supports computing a fixed
number of terms of the series, which it can do regardless
of convergence issues.

Test with the example functions from ``powerseries.py``:
    
    >>> from powerseries import *
    >>> names = ['exp', 'sin', 'cos', 'tan', 'sec', 'arcsin', 'arctan', 'sinh', 'cosh', 'tanh', 'arcsinh', 'arctanh']
    >>> for name in names:
    ...     f = PowerFunction(globals()['%sseries' % name]())
    ...     print name
    ...     print "f(0)", f(0)
    ...     print "f(1)", f(1)
    ...     print "f(1) to 10 figures", f(1, figures=10)
    ...
    exp
    f(0) 1
    f(1) 685/252
    f(1) to 10 figures 8463398743/3113510400
    sin
    f(0) 0
    f(1) 305353/362880
    f(1) to 10 figures 1100370038249/1307674368000
    cos
    f(0) 1
    f(1) 4357/8064
    f(1) to 10 figures 47102631757/87178291200
    tan
    f(0) 0
    f(1) 303520407357844/194896477400625
    f(1) to 10 figures 13462551943417438991627782493239751857561132563391/8644205195683235286768595007647709520704677734375
    sec
    f(0) 1
    f(1) 900520175377937141/486580401635328000
    f(1) to 10 figures 1209256320656611108711592273611327639089852593897960622737339/653363978554530140571699423545967107290604544983040000000000
    arcsin
    f(0) 0
    f(1) 9934553633062508667548681803105637/6814870934827565564370797513932800
    f(1) to 10 figures 9934553633062508667548681803105637/6814870934827565564370797513932800
    arctan
    f(0) 0
    f(1) 77030060483083029083/96845140757687397075
    f(1) to 10 figures 77030060483083029083/96845140757687397075
    sinh
    f(0) 0
    f(1) 426457/362880
    f(1) to 10 figures 1536780478171/1307674368000
    cosh
    f(0) 1
    f(1) 6913/4480
    f(1) to 10 figures 44841044309/29059430400
    tanh
    f(0) 0
    f(1) 12517580680408876/16436269594119375
    f(1) to 10 figures 140071833206259684360514733360266214425802526857/183919259482622027378055212928674670653291015625
    arcsinh
    f(0) 0
    f(1) 6014169722227115002607630537270917/6814870934827565564370797513932800
    f(1) to 10 figures 6014169722227115002607630537270917/6814870934827565564370797513932800
    arctanh
    f(0) 0
    f(1) 250947670863258378883/96845140757687397075
    f(1) to 10 figures 250947670863258378883/96845140757687397075
"""

from collections import deque
from fractions import Fraction
from itertools import islice


class DivergenceError(ArithmeticError): pass


class PowerFunction(object):
    """Wrap a power series and compute its function.
    
    A power series is represented as an iterable of coefficients; the
    nth term is the coefficient of x**n. This representation is used
    to compute the value of F(x), where F is the function whose power
    series is represented. Convergence testing is supported; an
    exception is raised if a divergent value is requested. Computing
    a fixed number of terms, regardless of convergence, is also
    supported. ``DivergenceError`` is raised if a divergent value
    is requested; divergence is detected by the convergence testing
    code, or by an overflow occurring.
    
    Note that, although this class was written to work with the
    ``PowerSeries`` class, it can actually work with any iterable
    that yields terms of a series.
    """
    
    error = Fraction(1, 10000)
    error_terms = 1
    terms_max = 50
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
        if the series fails to converge. The only other caveat is
        that we only compute ``terms_max`` terms; this ensures that
        we don't loop forever (or at least for a very long time) in
        cases where we are close to the edge of the circle of
        convergence (for example, computingthe tangent of a number
        close to pi/2).
        
        If ``terms`` is provided, that number of terms is computed
        and their sum returned, regardless of convergence. However,
        if an overflow occurs before the requested number of terms
        is computed, ``DivergenceError`` is raised.
        """
        if isinstance(x, (int, long)):
            x = Fraction(x, 1)
        elif isinstance(x, float):
            x = Fraction.from_float(x)
        if not isinstance(x, Fraction):
            raise ValueError("Power series function requires fraction as argument.")
        if terms is None:
            terms = self.terms_max
        if figures is not None:
            error = Fraction(1, 10**figures)
        elif error is None:
            error = self.error
        error = abs(error)
        result = Fraction(0, 1)
        self._clear_testfields()
        xt = Fraction(1, 1)
        for n, t in enumerate(islice(self.__series, terms)):
            try:
                term = t * xt
                result += term
            except OverflowError:
                raise DivergenceError("Series diverged to overflow point.")
            # This will raise DivergenceError if necessary
            if self.converged(x, n, term, result, error):
                break
            xt *= x
        return result
    
    def _clear_testfields(self):
        # Internal method to clear convergence testing fields
        self.__terms_last = deque(maxlen=self.error_terms)
        self.__ratio_last = None  # last nonzero term for ratio test
        self.__ratio_count = 0  # number of times the ratio test has failed
    
    def converged(self, x, n, term, result, error):
        """Test series convergence.
        
        Determining convergence is straightforward: we just check
        that some number of terms (specified by the ``error_terms``
        class field) change the result by less than ``error``.
        
        Determining divergence is more complicated, since we
        don't have a symbolic representation of the function the
        series is computing, we only have the terms of the series.
        So the only classic test we can easily apply is the ratio
        test: if the ratio of a term to the preceding (nonzero)
        term is > 1 for some number of terms (determined by the
        class field ``ratio_max``), we conclude that the series is
        diverging. This is still not an analytical proof, of course;
        but it is a reasonable heuristic, and it works for all of
        the example series in ``powerseries.py``. The only caveat
        is that some series (e.g., arctan) start diverging only
        after a large number of terms for values of x close to
        the convergence limit (e.g., try arctan(1.01)), so the
        divergence test may not spot them unless the ``terms``
        parameter is set high enough.
        
        Note that this definition of divergence also cannot take
        account of periodic functions; our series representation
        corresponds to a Taylor expansion about x = 0, so it only
        converges within the circle of convergence centered on
        that value. For example, computing the tangent of pi will
        diverge, even though the proper analytical value of tan(pi)
        is 0, because computing that would require us to expand the
        series around x = pi. This is not seen as an issue because
        the calling code can always apply an offset to x before
        invoking the series function.
        """
        if term != 0:
            self.__terms_last.append(term)
            if abs(sum(self.__terms_last)) < abs(error * result):
                return True
            if self.__ratio_last and (abs(term / self.__ratio_last) > 1):
                self.__ratio_count += 1
            if self.__ratio_count > self.ratio_max:
                raise DivergenceError("Series failed ratio test.")
            self.__ratio_last = term
        return False


if __name__ == '__main__':
    import doctest
    doctest.testmod()
