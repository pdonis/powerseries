#! /usr/bin/env python
"""
Copyright (C) 2011 by Peter A. Donis.
Released under the open source MIT license:
http://www.opensource.org/licenses/MIT

Power series representations in Python.
Based on http://doc.cat-v.org/bell_labs/squinting_at_power_series/squint.pdf.
Developed using Python 2.6.5. May not work in earlier versions since some
recent features and builtins are used.

This is a Python implementation of the pseudocode in the above paper by
Doug McIlroy, with some additional operations added that the paper did
not include. Back when the paper was first written, McIlroy noted that
languages with the key features needed for such an implementation were
not in common use. Things are certainly different now; the Python
implementation below is a fairly straightforward expression of the
algorithms in the paper, and it's fast, but McIlroy put a Haskell
implementation on the web in 2007 that's way more compact; see here:

http://www.cs.dartmouth.edu/~doug/powser.html

All of the key Haskell definitions there are one-liners. But I like Python,
and AFAIK no one has done an implementation of this stuff in Python,
so here we go. :-)

In the doctests below, we test some properties of power series using the
example series defined later in this module; the specific series and
operations are described in the individual method and function docstrings.
We also test standard identities that particular series should satisfy, such
as the trig identities. Note that with appropriate series representations of
constants (like ``ONE``), all the identities are satisfied. Finally, we test
whether the series themselves, when treated as functions operating on other
series, give the expected results: for example, that EXP(X) == EXP, i.e.,
that the exponential series, when composed with the series representing x,
gives back itself (and similarly for other series).
    
    >>> ZERO = PowerSeries()
    >>> ONE = nthpower(0)
    >>> X = nthpower(1)
    >>> N = nseries()
    >>> H = harmonicseries()
    >>> AH = altharmonicseries()
    >>> EXP = expseries()
    >>> SIN = sinseries()
    >>> COS = cosseries()
    >>> TAN = tanseries()
    >>> SEC = secseries()
    >>> ARCSIN = arcsinseries()
    >>> ARCTAN = arctanseries()
    >>> SINH = sinhseries()
    >>> COSH = coshseries()
    >>> TANH = tanhseries()
    >>> SECH = sechseries()
    >>> ARCSINH = arcsinhseries()
    >>> ARCTANH = arctanhseries()
    >>> allseries = [S for S in globals().values() if isinstance(S, PowerSeries)]
    >>> testseries = allseries
    >>> all(s == s.xmul.tail for s in testseries)
    True
    >>> all(s == s.head + s.tail.xmul for s in testseries)
    True
    >>> all(s == s + Fraction(0, 1) for s in testseries)
    True
    >>> all(s == Fraction(0, 1) + s for s in testseries)
    True
    >>> all(s == s + ZERO for s in testseries)
    True
    >>> all(s == ZERO + s for s in testseries)
    True
    >>> all(s == s - Fraction(0, 1) for s in testseries)
    True
    >>> all((- s) == Fraction(0, 1) - s for s in testseries)
    True
    >>> all(s == s - ZERO for s in testseries)
    True
    >>> all((- s) == ZERO - s for s in testseries)
    True
    >>> all(s == s * Fraction(1, 1) for s in testseries)
    True
    >>> all(s == Fraction(1, 1) * s for s in testseries)
    True
    >>> all(s == s * ONE for s in testseries)
    True
    >>> all(s == ONE * s for s in testseries)
    True
    >>> all(s == s / Fraction(1, 1) for s in testseries)
    True
    >>> all(s == s / ONE for s in testseries)
    True
    >>> all(s == integ(deriv(s), s.zero) for s in testseries)
    True
    >>> all(s == deriv(integ(s)) for s in testseries)
    True
    >>> all(s(X) == s for s in testseries)
    True
    >>> testseries = [S for S in allseries if S.zero != 0]
    >>> all(s * (ONE / s) == ONE for s in testseries)
    True
    >>> all(sqrt(s) * sqrt(s) == s for s in testseries)
    True
    >>> testseries = [S for S in allseries if S.zero == 0 and S is not ZERO]
    >>> all(inv(inv(s)) == s for s in testseries)
    True
    >>> all(s(inv(s)) == X for s in testseries)
    True
    >>> all(exp(log(s)) - ONE == s for s in testseries)
    True
    >>> inv(X) == X
    True
    >>> exp(ZERO) == ONE
    True
    >>> EXP(ZERO) == ONE
    True
    >>> exp(X) == EXP
    True
    >>> exp(-X) == ONE / EXP
    True
    >>> (SIN * SIN) + (COS * COS) == ONE
    True
    >>> ONE + (TAN * TAN) == (SEC * SEC)
    True
    >>> TWO = Fraction(2, 1) * ONE
    >>> (exp(X) + exp(-X)) / TWO == COSH
    True
    >>> (exp(X) - exp(-X)) / TWO == SINH
    True
    >>> (COSH * COSH) - (SINH * SINH) == ONE
    True
    >>> ONE - (TANH * TANH) == (SECH * SECH)
    True
    
"""

from fractions import Fraction
from itertools import count, islice, izip, izip_longest

from cached_class import cached_class
from cached_property import cached_property
from memoize_generator import memoize_generator


@cached_class
class PowerSeries(object):
    """Power series encapsulation.
    
    Represents a power series as an iterable of coefficients; the nth
    term is the coefficient of x**n. The internal representation is a
    generator that yields the coefficients one by one. Operations on
    the series are implemented as construction of new generator
    functions in terms of existing ones.
    
    Note that we "cache" this class so only one instance of it will
    exist for each distinct power series (as determined by the set
    of arguments). This reduces object churn, particularly for series
    that are commonly used, such as the empty series, and thus helps
    to speed computations.
    """
    
    testlimit = 10
    
    def __init__(self, g=None, f=None, l=None):
        """Construct a PowerSeries from a generator, term function, or list.
        
        If ``g`` is given, construct the series using ``g`` as its generator.
        
        If ``f`` is given, construct the series using ``f`` as the "term
        function"; internally, the function is used to construct a generator
        that represents the series.
        
        If ``l`` is given, construct a finite series with terms from ``l`` in
        order; internally, a generator is constructed that yields the terms.
        
        If none of ``f``, ``g``, ``l`` is present, the series will be empty.
        """
        if g:
            self.__g = g
        elif f:
            def _g():
                for n in count():
                    yield f(n)
            self.__g = _g
        elif l:
            def _l():
                for t in l:
                    yield t
            self.__g = _l
        else:
            # Empty series
            self.__g = None
        # Internal fields for storing cached results of operations
        self.__D = self.__E = self.__R = self.__I = self.__S = self.__L = None
        self.__As = {}
        self.__Ms = {}
        self.__Cs = {}
        self.__Is = {}
    
    @memoize_generator
    def _gen(self):
        """The full generator for this series.
        
        This method is for internal use only; the series generator should be
        accessed publicly via the ``__iter__`` method (or anything that uses
        it, such as a ``for`` loop).
        
        Note that we add an extra loop at the end of the series to yield zero
        elements forever if our own generator exhausts itself. This allows
        every series to look infinite when needed without requiring repetitive
        code in generators.
        
        Note also that we "memoize" our generator so that, if it is realized
        multiple times, the terms don't have to be recomputed. This provides
        a dramatic speedup since computing an operation like multiplication
        requires many realizations of the generator.
        """
        if self.__g:
            for term in self.__g():
                yield term
        while True:
            yield Fraction(0, 1)
    
    def __iter__(self):
        """Return an iterator over the series.
        
        This makes a ``PowerSeries`` an iterable, which combined with the
        properties below makes the notation simple.
        
        Note that we do *not* memoize this method directly; we factor out
        the memoized generator and just realize it here. This is because
        ``__iter__`` is a special method that is handled differently by
        Python, so decorators don't work properly with it.
        """
        return self._gen()
    
    def __eq__(self, other):
        """Test PowerSeries for equality.
        
        Obviously we can't do this perfectly since we would have to check a
        potentially infinite number of terms. The class field ``testlimit``
        determines how many terms we check; it defaults to 10 as a reasonable
        compromise (the doctests run quickly but we are still seeing at least
        5 nonzero terms for comparison even for series like sine and cosine
        where every other term is zero).
        
        Note that if two instances are compared which have the ``testlimit``
        field set to different values, the left object in the comparison
        determines the limit.
        """
        if isinstance(other, PowerSeries):
            return all(s == o for s, o in islice(izip(self, other), self.testlimit))
        return NotImplemented
    
    def __ne__(self, other):
        return not self == other
    
    # PowerSeries instances can't be hashed because that would require series that
    # compare equal to have the same hash values, and there's no easy way to do that
    
    __hash__ = None
    
    def showterms(self, num=None):
        """Convenience method to print the first ``num`` terms.
        
        If ``num`` is not given, it defaults to ``self.testlimit``.
        """
        for term in islice(self, num or self.testlimit):
            print term
    
    @cached_property
    def zero(self):
        """Return the zeroth term of this series.
        """
        for term in self:
            return term
    
    @cached_property
    def head(self):
        """Return a PowerSeries representing the "head" of this one.
        
        The "head" of a power series is the zeroth element only, viewed as a
        series in its own right (meaning, the first and all later elements
        are zero).
        """
        def _h():
            yield self.zero
        return PowerSeries(_h)
    
    @cached_property
    def tail(self):
        """Return a PowerSeries representing the "tail" of this one.
        
        The "tail" of a power series is the original series shifted by one
        term (i.e., the zeroth term of the tail is the first term of the
        original series). This is equivalent to subtracting the zeroth
        term, then dividing by x: tail(S) = 1/x (S - S(0)). See the
        docstring for the ``xmul`` method.
        """
        def _t():
            for term in islice(self, 1, None):
                yield term
        return PowerSeries(_t)
    
    @cached_property
    def xmul(self):
        """Return a PowerSeries representing x * this one.
        
        This is a sort of "inverse" operation to the tail function above;
        the "tail" operation more or less corresponds to dividing the series
        by x. We can test this by testing the identity:
        
        >>> e = expseries()
        >>> e == e.xmul.tail
        True
        
        However, the "division by x" is not complete, because the tail
        leaves out the zeroth term of the original series (see the docstring
        for the ``tail`` method above). So to invert the above test, we have
        to add back the head, giving the identity:
        
        >>> e == e.head + e.tail.xmul
        True
        """
        def _x():
            yield Fraction(0, 1)
            for term in self:
                yield term
        return PowerSeries(_x)
    
    def __add__(self, other):
        """Return a PowerSeries instance that sums self and other.
        
        If ``other`` is a number, it is coerced into a power series
        with that number as the zeroth term (i.e., a constant).
        
        Addition of a number obeys the usual arithmetic identities:
        
        >>> e = expseries()
        >>> e == e + Fraction(0, 1)
        True
        >>> e == Fraction(0, 1) + e
        True
        """
        if isinstance(other, Fraction):
            oid = other
            other = nthpower(0, coeff=other)
        else:
            oid = None
        if isinstance(other, PowerSeries):
            oid = oid or id(other)
            if oid in self.__As:
                return self.__As[oid]
            def _a():
                for terms in izip_longest(self, other, fillvalue=Fraction(0, 1)):
                    yield sum(terms)
            A = self.__As[oid] = PowerSeries(_a)
            return A
        return NotImplemented
    
    __radd__ = __add__
    
    def __sub__(self, other):
        """Return a PowerSeries instance representing self - other.
        
        The addition method handles all the hard work, and the same identities
        hold when subtracting zero:
        
        >>> e = expseries()
        >>> e == e - Fraction(0, 1)
        True
        """
        return self + (- other)
    
    def __rsub__(self, other):
        """Return a PowerSeries instance representing other - self.
        
        Again, the addition method handles the hard work, and we can test a
        similar identity to the above:
        
        >>> e = expseries()
        >>> Fraction(0, 1) - e == (- e)
        True
        """
        return other + (- self)
    
    def __mul__(self, other):
        """Return a PowerSeries instance that multiplies self and other.
        
        Multiplication by a number obeys the usual arithmetic identities:
        
        >>> e = expseries()
        >>> e == e * Fraction(1, 1)
        True
        >>> e == Fraction(1, 1) * e
        True
        
        Since this operation is the key recursive one that others are
        built on, we optimize it to avoid computing series that we know
        will yield all zero elements. This includes the product of a zero
        fraction with ``self``; since we know the terms will all be zero,
        we avoid realizing our own generator.
        """
        if isinstance(other, Fraction):
            if other == 1:
                return self
            if other == 0:
                return PowerSeries()
            if other in self.__Ms:
                return self.__Ms[other]
            def _m():
                for term in self:
                    yield other * term
            oid = other
        elif isinstance(other, PowerSeries):
            oid = id(other)
            if oid in self.__Ms:
                return self.__Ms[oid]
            def _m():
                f0 = self.zero
                g0 = other.zero
                yield f0 * g0
                F = self.tail
                G = other.tail
                mterms = [(F * G).xmul]
                if f0 != 0:
                    mterms.append(f0 * G)
                if g0 != 0:
                    mterms.append(g0 * F)
                for terms in izip(*mterms):
                    yield sum(terms)
        else:
            return NotImplemented
        M = self.__Ms[oid] = PowerSeries(_m)
        return M
    
    __rmul__ = __mul__
    
    def __neg__(self):
        """Return a PowerSeries representing -1 times this one.
        
        Convenience to simplify the notation. Obeys the obvious identity:
        
        >>> e = expseries()
        >>> - (- e) == e
        True
        """
        return Fraction(-1, 1) * self
    
    def __div__(self, other):
        """Easier way of expressing multiplication by the reciprocal.
        
        Obeys the obvious identity that a series divided by itself is 1
        (where "1" here is the series with only the zeroth term nonzero;
        see the ``nthpower`` function below):
        
        >>> e = expseries()
        >>> e / e == nthpower(0)
        True
        >>> e / Fraction(1, 1) == e
        True
        """
        if isinstance(other, Fraction):
            return self * (Fraction(1, 1) / other)
        if isinstance(other, PowerSeries):
            return self * other.reciprocal()
        return NotImplemented
    
    def __rdiv__(self, other):
        """Easier way of accessing the reciprocal of self.
        
        >>> e = expseries()
        >>> e * (Fraction(1, 1) / e) == nthpower(0)
        True
        """
        if isinstance(other, Fraction):
            return other * self.reciprocal()
        return NotImplemented
    
    def compose(self, other):
        """Return a PowerSeries instance that composes self with other.
        
        The identity for series composition is the series representing x:
        
        >>> X = nthpower(1)
        >>> X(X) == X
        True
        """
        oid = id(other)
        if oid in self.__Cs:
            return self.__Cs[oid]
        if isinstance(other, PowerSeries):
            if other.zero != 0:
                raise ValueError("First term of composed PowerSeries must be 0.")
            def _c():
                yield self.zero
                for term in (other.tail * self.tail(other)):
                    yield term
            C = self.__Cs[oid] = PowerSeries(_c)
            return C
        raise TypeError("Can only compose a PowerSeries with another one.")
    
    def __call__(self, other):
        """Alternate, easier notation for ``self.compose(other)``.
        """
        return self.compose(other)
    
    def derivative(self):
        """Return a PowerSeries representing the derivative of this one with respect to x.
        
        Check differentiation of simple powers of x:
        
        >>> all(nthpower(n).derivative() == Fraction(n, 1) * nthpower(n - 1) for n in xrange(10))
        True
        """
        if self.__D:
            return self.__D
        def _d():
            for n, term in enumerate(self.tail):
                yield Fraction(n + 1, 1) * term
        D = self.__D = PowerSeries(_d)
        return D
    
    def integral(self, const=Fraction(0, 1)):
        """Return a PowerSeries representing the integral of this one with respect to x.
        
        Check integration of simple powers of x:
        
        >>> all(nthpower(n).integral() == Fraction(1, n + 1) * nthpower(n + 1) for n in xrange(10))
        True
        
        We can also test differentiation and integration by testing the identities:
        
        >>> cos = cosseries()
        >>> cos == cos.derivative().integral(cos.zero)
        True
        >>> cos == cos.integral().derivative()
        True
        """
        if const in self.__Is:
            return self.__Is[const]
        def _i():
            yield const
            for n, term in enumerate(self):
                yield Fraction(1, n + 1) * term
        I = self.__Is[const] = PowerSeries(_i)
        return I
    
    def exponential(self):
        """Return a PowerSeries representing e ** self.
        
        Note that Python automatically handles the fact that we are recursively including
        the exponentiated series in itself; X appears in its own generator. This works
        because (a) the integral series yields a constant first, so it doesn't need any
        output from X to get started; and (b) Python "lazily" evaluates generators, so
        it doesn't compute the nth term of X until it has already yielded the (n - 1)th
        term. So even though it looks like the code below should infinitely regress before
        yielding anything, it actually works just fine!
        
        We can use this method to express the fact that the exponential series is e^x;
        the ``nthpower`` function below allows us to express "x" as a series with only
        the index 1 term nonzero:
        
        >>> nthpower(1).exponential() == expseries()
        True
        
        We can also express the fact that e^0 == 1:
        
        >>> PowerSeries().exponential() == nthpower(0)
        True
        
        Note that we can't exponentiate a series with a nonzero first term by this
        method.
        """
        if self.__E:
            return self.__E
        if self.zero != 0:
            raise ValueError("First term of exponentiated PowerSeries must be 0.")
        def _e():
            for term in (E * self.derivative()).integral(Fraction(1, 1)):
                yield term
        E = self.__E = PowerSeries(_e)
        return E
    
    def reciprocal(self):
        """Return a PowerSeries representing the reciprocal of self.
        
        Note that the same trick we used in the exponential above also works here; R
        appears in its own generator, but the generator yields a constant first, so
        there is no infinite regress.
        
        The reciprocal obeys the obvious identity F * 1/F = 1:
        
        >>> e = expseries()
        >>> e * e.reciprocal() == nthpower(0)
        True
        
        We can also express the fact that 1/e^x = e^-x:
        
        >>> expseries().reciprocal() == (Fraction(-1, 1) * nthpower(1)).exponential()
        True
        
        Note that we can't take the reciprocal of a series with a zero first term
        by this method.
        """
        if self.__R:
            return self.__R
        if self.zero == 0:
            raise ValueError("Cannot take reciprocal of PowerSeries with first term 0.")
        def _r():
            recip = Fraction(1, 1) / self.zero
            yield recip
            for term in ((- recip) * (self.tail * R)):
                yield term
        R = self.__R = PowerSeries(_r)
        return R
    
    def inverse(self):
        """Return a PowerSeries representing the inverse of self.
        
        The inverse obeys the identity F(inv(F)) == x:
        
        >>> X = nthpower(1)
        >>> N = nseries()
        >>> N(N.inverse()) == X
        True
        
        The series representing x is its own inverse, since it is the
        identity with respect to function composition:
        
        >>> X == X.inverse()
        True
        
        Note that we can't take the inverse of a series with a nonzero first term by
        this method.
        """
        if self.__I:
            return self.__I
        if self.zero != 0:
            raise ValueError("Cannot invert PowerSeries with nonzero first term.")
        if self.tail.zero == 0:
            raise ValueError("Cannot invert PowerSeries whose tail has zero first term.")
        def _i():
            yield Fraction(0, 1)
            F = self.tail
            recip = Fraction(1, 1) / F.zero
            yield recip
            T = I.tail
            for term in ((- recip) * ((T * T) * F.tail(I))):
                yield term
        I = self.__I = PowerSeries(_i)
        return I
    
    def squareroot(self):
        """Return a PowerSeries representing sqrt(self).
        
        The square root obeys the obvious identity:
        
        >>> EXP = expseries()
        >>> (EXP.squareroot() * EXP.squareroot()) == EXP
        True
        
        Note that we can't take the square root of a series with a zero first term by
        this method, because we need to take a reciprocal.
        """
        if self.__S:
            return self.__S
        if self.zero == 0:
            raise ValueError("Cannot take square root of PowerSeries with zero first term.")
        from math import sqrt as _sqrt
        def _s():
            s0 = Fraction.from_float(_sqrt(self.zero))
            yield s0
            for term in (self.tail * (s0 + S).reciprocal()):
                yield term
        S = self.__S = PowerSeries(_s)
        return S
    
    def logarithm(self):
        """Return a PowerSeries representing log(1 + self).
        
        We can't actually take the log of self because log(0) diverges; we can only
        do a power series expansion about some nonzero x0, and the simplest choice
        is obviously x0 = 1. This means we can't take the log of a series with a
        nonzero constant term by this method.
        
        The following is the easiest test of this method:
        
        >>> nthpower(1).logarithm() == altharmonicseries()
        True
        
        We can also express the fact that log(1) == 0, since this corresponds to
        calling this method on the zero series:
        
        >>> PowerSeries().logarithm() == PowerSeries()
        True
        
        Finally, this method obeys the identity:
        
        >>> ONE = nthpower(0)
        >>> X = nthpower(1)
        >>> X.logarithm().exponential() - ONE == X
        True
        """
        if self.__L:
            return self.__L
        if self.zero != 0:
            raise ValueError("Cannot take logarithm of PowerSeries with nonzero first term.")
        def _l():
            for term in (self.derivative() / (Fraction(1, 1) + self)).integral():
                yield term
        L = self.__L = PowerSeries(_l)
        return L


def nthpower(n, coeff=Fraction(1, 1)):
    """A series giving the nth power of x.
    
    These series have many uses, particularly the first two, nthpower(0) and
    nthpower(1), representing 1 and x. We can easily check that the series
    behave as expected for pure powers of x (unfortunately we can't check
    division since we can't take reciprocals for series whose first terms
    are zero, which leaves out all these series except the zeroth):
    
    >>> X = nthpower(1)
    >>> X2 = nthpower(2)
    >>> X * X == X2
    True
    """
    def _n():
        for i in xrange(n):
            yield Fraction(0, 1)
        yield coeff
    return PowerSeries(_n)


# Some convenience functions for PowerSeries

def exp(S):
    """Convenience function for exponentiating PowerSeries.
    
    This can also replace the ``math.exp`` function, extending it to
    take a PowerSeries as an argument.
    """
    from math import exp as _exp
    if isinstance(S, PowerSeries):
        return S.exponential()
    return _exp(S)


def log(S):
    """Convenience function for taking logarithms of PowerSeries.
    
    This can also replace the ``math.log`` function, extending it to
    take a PowerSeries as an argument.
    """
    from math import log as _log
    if isinstance(S, PowerSeries):
        return S.logarithm()
    return _log(S)


def sqrt(S):
    """Convenience function for taking square roots of PowerSeries.
    
    This can also replace the ``math.sqrt`` function, extending it to
    take a PowerSeries as an argument.
    """
    from math import sqrt as _sqrt
    if isinstance(S, PowerSeries):
        return S.squareroot()
    return _sqrt(S)


def inv(S):
    """Convenience function for inverting PowerSeries.
    """
    if isinstance(S, PowerSeries):
        return S.inverse()
    raise TypeError("Cannot invert object of type %s." % type(S))


def deriv(S):
    """Convenience function for differentiating PowerSeries.
    """
    if isinstance(S, PowerSeries):
        return S.derivative()
    raise TypeError("Cannot differentiate object of type %s." % type(S))


def integ(S, const=Fraction(0, 1)):
    """Convenience function for integrating PowerSeries.
    """
    if isinstance(S, PowerSeries):
        return S.integral(const)
    raise TypeError("Cannot integrate object of type %s." % type(S))


# Example series

def constseries(const):
    """An infinite sequence of constant values as a PowerSeries.
    
    The constant series with constant 1 is the series representation of
    1 / 1 - x. We can test this:
    
    >>> ONE = nthpower(0)
    >>> X = nthpower(1)
    >>> constseries(Fraction(1, 1)) == ONE / (ONE - X)
    True
    """
    return PowerSeries(f=lambda n: const)


def altconstseries(const):
    """An infinite sequence of alternating sign constant values as a PowerSeries.
    
    The alternating series with constant 1 is the series representation of
    1 / 1 + x. We can test this:
    
    >>> ONE = nthpower(0)
    >>> X = nthpower(1)
    >>> altconstseries(Fraction(1, 1)) == ONE / (ONE + X)
    True
    """
    return PowerSeries(f=lambda n: Fraction((1, -1)[n % 2], 1) * const)


def nseries():
    """The natural numbers as a PowerSeries.
    """
    return PowerSeries(f=lambda n: Fraction(n, 1))


def harmonicseries():
    """The harmonic series 1/n as a PowerSeries.
    
    The harmonic series is the series representation of - ln(1 - x).
    Even though the exponential series is not directly invertible,
    we can still test this; the inverse of ln(1 - x) is - e^x + 1,
    and this is invertible, so:
    
    >>> ONE = nthpower(0)
    >>> harmonicseries() == - inv(-expseries() + ONE)
    True
    
    Note that this gives a much faster way of computing ln(1 - x) than
    actually inverting -e^x + 1; the latter series, as you can test by
    trying to raise ``testlimit`` high enough and then retrying the
    above doctest, has a computing time that grows rapidly with ``n``,
    while the harmonic series, of course, has constant computing time
    per term (and also has the benefit of not overflowing the stack).
    
    The above also implies that this series is the integral of the
    constant series:
    
    >>> integ(constseries(Fraction(1, 1))) == harmonicseries()
    True
    """
    return PowerSeries(f=lambda n: Fraction(1, n) if n else Fraction(0, 1))


def altharmonicseries():
    """The alternating sign harmonic series as a PowerSeries.
    
    The alternating sign harmonic series is the series representation of
    ln(1 + x). This is the inverse of e^x - 1, and we can test this by
    the same method we used for the harmonic series:
    
    >>> ONE = nthpower(0)
    >>> altharmonicseries() == inv(expseries() - ONE)
    True
    
    The above also implies that this series is the integral of the
    alternating constant series:
    
    >>> integ(altconstseries(Fraction(1, 1))) == altharmonicseries()
    True
    """
    return PowerSeries(f=lambda n: Fraction((-1, 1)[n % 2], n) if n else Fraction(0, 1))


def expseries():
    """The exponential function as a PowerSeries.
    
    We want to avoid using factorials to compute series, since
    that would make us dependent on the speed of the factorial
    implementation. Python's appears to be fast, but the method
    used here appears just as fast and eliminates any dependency
    on the factorial algorithm used. (Similar remarks apply to
    the other series that can be expressed as factorials or other
    complicated term functions.)
    
    We use the fact that exp is the unique solution of
    
    dy/dx = y
    
    with y(0) = 1 to construct the series generator. Note that
    we use the same trick as we did in several methods of the
    ``PowerSeries`` class, where the series appears in its own
    generator. In fact, this is basically the simplest possible
    way that can be done, which reflects the special properties
    of the exponential function.
    
    Check standard properties:
    
    >>> EXP = expseries()
    >>> deriv(EXP) == EXP
    True
    >>> integ(EXP, Fraction(1, 1)) == EXP
    True
    """
    def _exp():
        for term in integ(EXP, Fraction(1, 1)):
            yield term
    EXP = PowerSeries(_exp)
    return EXP


def sinseries():
    """The sine function as a PowerSeries.
    
    See remarks above under ``expseries`` for why we don't use
    the factorial function as our primary implementation.
    
    We use the fact that this function is the unique solution of
    
    d^2y/dx^2 = -y(x)
    
    with dy/dx = 1 and y = 0 as the initial conditions to construct
    the series generator.
    
    Check standard properties:
    
    >>> SIN = sinseries()
    >>> deriv(deriv(SIN)) == - SIN
    True
    """
    def _sin():
        for term in integ(integ(-SIN, Fraction(1, 1))):
            yield term
    SIN = PowerSeries(_sin)
    return SIN


def cosseries():
    """The cosine function as a PowerSeries.
    
    See remarks above under ``expseries`` for why we don't use
    the factorial function as our primary implementation.
    
    We use the fact that this function is the unique solution of
    
    d^2y/dx^2 = -y(x)
    
    with dy/dx = 0 and y = 1 as the initial conditions to construct
    the series generator.
    
    Check standard properties:
    
    >>> SIN = sinseries()
    >>> COS = cosseries()
    >>> deriv(deriv(COS)) == - COS
    True
    >>> deriv(SIN) == COS
    True
    >>> deriv(COS) == - SIN
    True
    """
    def _cos():
        for term in integ(integ(-COS), Fraction(1, 1)):
            yield term
    COS = PowerSeries(_cos)
    return COS


def tanseries():
    """The tangent function as a PowerSeries.
    
    >>> tanseries().showterms()
    0
    1
    0
    1/3
    0
    2/15
    0
    17/315
    0
    62/2835
    
    We use the fact that this function is the unique solution of
    
    dy/dx = 1 + y(x)^2
    
    to construct the series generator. This is not quite as
    simple as taking the ratio of the sine and cosine series,
    but it appears to be just as fast (and should be since it
    involves one multiplication, the same as taking the reciprocal
    of the cosine series would).
    """
    def _tan():
        ONE = nthpower(0)
        for term in integ(ONE + (TAN * TAN)):
            yield term
    TAN = PowerSeries(_tan)
    return TAN


def secseries():
    """The secant function as a PowerSeries.
    
    We use the fact that the integral of sec x is sec x * tan x,
    and our series for tangent, to construct the series. As with
    the tangent series, this is not as simple as taking the
    reciprocal of the cosine series, but should be similar in
    terms of speed (and indeed appears to be).
    
    >>> secseries().showterms()
    1
    0
    1/2
    0
    5/24
    0
    61/720
    0
    277/8064
    0
    """
    def _sec():
        TAN = tanseries()
        for term in integ(SEC * TAN, Fraction(1, 1)):
            yield term
    SEC = PowerSeries(_sec)
    return SEC


def arcsinseries():
    """The arcsine function as a PowerSeries.
    
    >>> arcsinseries().showterms()
    0
    1
    0
    1/6
    0
    3/40
    0
    5/112
    0
    35/1152
    
    We use the fact that arcsin is the integral of
    1 / sqrt(1 - x^2) with a zero integration constant
    to construct the series. This should be at least
    as fast as taking the inverse of the sine series,
    and indeed it appears to be.
    
    Test the inverse property:
    
    >>> SIN = sinseries()
    >>> ARCSIN = arcsinseries()
    >>> SIN == inv(ARCSIN)
    True
    >>> X = nthpower(1)
    >>> ARCSIN(SIN) == X
    True
    >>> SIN(ARCSIN) == X
    True
    """
    def _arcsin():
        ONE = nthpower(0)
        X2 = nthpower(2)
        for term in integ(ONE / sqrt(ONE - X2)):
            yield term
    return PowerSeries(_arcsin)


def arctanseries():
    """The arctangent function as a PowerSeries.
    
    >>> arctanseries().showterms()
    0
    1
    0
    -1/3
    0
    1/5
    0
    -1/7
    0
    1/9
    
    We use the fact that arctangent is the integral of
    1 / (1 + x^2) with a zero integration constant to
    construct the series. We expect this, if anything,
    to be faster than taking the inverse of the tangent
    series, since an inverse involves an extra multiplication.
    
    Test the inverse property:
    
    >>> TAN = tanseries()
    >>> ARCTAN = arctanseries()
    >>> TAN == inv(ARCTAN)
    True
    >>> X = nthpower(1)
    >>> ARCTAN(TAN) == X
    True
    >>> TAN(ARCTAN) == X
    True
    """
    def _arctan():
        ONE = nthpower(0)
        X2 = nthpower(2)
        for term in integ(ONE / (ONE + X2)):
            yield term
    return PowerSeries(_arctan)


def sinhseries():
    """The hyperbolic sine function as a PowerSeries.
    
    See remarks above under ``expseries`` for why we don't use
    the factorial function as our primary implementation.
    
    We use the fact that this function is the unique solution of
    
    d^2y/dx^2 = y(x)
    
    with dy/dx = 1 and y = 0 as the initial conditions to construct
    the series generator.
    
    Check standard properties:
    
    >>> SINH = sinhseries()
    >>> deriv(deriv(SINH)) == SINH
    True
    """
    def _sinh():
        for term in integ(integ(SINH, Fraction(1, 1))):
            yield term
    SINH = PowerSeries(_sinh)
    return SINH


def coshseries():
    """The hyperbolic cosine function as a PowerSeries.
    
    See remarks above under ``expseries`` for why we don't use
    the factorial function as our primary implementation.
    
    We use the fact that this function is the unique solution of
    
    d^2y/dx^2 = y(x)
    
    with dy/dx = 0 and y = 1 as the initial conditions to construct
    the series generator.
    
    Check standard properties:
    
    >>> SINH = sinhseries()
    >>> COSH = coshseries()
    >>> deriv(deriv(COSH)) == COSH
    True
    >>> deriv(SINH) == COSH
    True
    >>> deriv(COSH) == SINH
    True
    """
    def _cosh():
        for term in integ(integ(COSH), Fraction(1, 1)):
            yield term
    COSH = PowerSeries(_cosh)
    return COSH


def tanhseries():
    """The hyperbolic tangent function as a PowerSeries.
    
    >>> tanhseries().showterms()
    0
    1
    0
    -1/3
    0
    2/15
    0
    -17/315
    0
    62/2835
    
    We use the fact that this function is the unique solution of
    
    dy/dx = 1 - y(x)^2
    
    to construct the series generator. Similar remarks apply here as
    with the tangent series, above.
    """
    def _tanh():
        ONE = nthpower(0)
        for term in integ(ONE - (TANH * TANH)):
            yield term
    TANH = PowerSeries(_tanh)
    return TANH


def sechseries():
    """The hyperbolic secant function as a PowerSeries.
    
    We use the fact that the integral of sech x is - sech x * tanh x,
    and the known series for tanh, to construct the series. Similar
    remarks apply here as with the secant series, above.
    
    >>> sechseries().showterms()
    1
    0
    -1/2
    0
    5/24
    0
    -61/720
    0
    277/8064
    0
    """
    def _sech():
        TANH = tanhseries()
        for term in integ(- SECH * TANH, Fraction(1, 1)):
            yield term
    SECH = PowerSeries(_sech)
    return SECH


def arcsinhseries():
    """The hyperbolic arcsine function as a PowerSeries.
    
    >>> arcsinhseries().showterms()
    0
    1
    0
    -1/6
    0
    3/40
    0
    -5/112
    0
    35/1152
    
    We use the fact that arcsinh is the integral of
    1 / sqrt(1 + x^2) with a zero integration constant
    to construct the series. See remarks under the
    arcsin series, above.
    
    Test the inverse property:
    
    >>> SINH = sinhseries()
    >>> ARCSINH = arcsinhseries()
    >>> SINH == inv(ARCSINH)
    True
    >>> X = nthpower(1)
    >>> ARCSINH(SINH) == X
    True
    >>> SINH(ARCSINH) == X
    True
    """
    def _arcsinh():
        ONE = nthpower(0)
        X2 = nthpower(2)
        for term in integ(ONE / sqrt(ONE + X2)):
            yield term
    return PowerSeries(_arcsinh)


def arctanhseries():
    """The hyperbolic arctangent function as a PowerSeries.
    
    >>> arctanhseries().showterms()
    0
    1
    0
    1/3
    0
    1/5
    0
    1/7
    0
    1/9
    
    We use the fact that arctanh is the integral of
    1 / (1 - x^2) with a zero integration constant to
    construct the series. See remarks under the
    arctan series, above.
    
    Test the inverse property:
    
    >>> TANH = tanhseries()
    >>> ARCTANH = arctanhseries()
    >>> TANH == inv(ARCTANH)
    True
    >>> X = nthpower(1)
    >>> ARCTANH(TANH) == X
    True
    >>> TANH(ARCTANH) == X
    True
    """
    def _arctanh():
        ONE = nthpower(0)
        X2 = nthpower(2)
        for term in integ(ONE / (ONE - X2)):
            yield term
    return PowerSeries(_arctanh)


# Alternate implementations of certain series, for comparison

def altnthpower(n, coeff=Fraction(1, 1)):
    """Alternate implementation of nth power using lists.
    
    This implementation tests the usage of a finite list in the
    ``PowerSeries`` constructor. Note that we actually use a
    tuple since that allows the caching of instances by
    constructor argument to work (a list would not be hashable
    so no caching would occur).
    
    Test equivalence with standard nth power function:
    
    >>> all(altnthpower(n) == nthpower(n) for n in xrange(10))
    True
    """
    _l = (coeff,)
    if n > 0:
        _l = ((Fraction(0, 1),) * n) + _l
    return PowerSeries(l=_l)


def altexpseries():
    """Alternate way of representing exp as a PowerSeries.
    
    This is the factorial implementation, provided for
    comparison.
    
    Check alternate representation:
    
    >>> expseries() == altexpseries()
    True
    """
    from math import factorial
    return PowerSeries(f=lambda n: Fraction(1, factorial(n)))


def altsinseries():
    """Alternate way of representing sine as a PowerSeries.
    
    This is the factorial implementation, provided for
    comparison.
    
    Check the alternate representation:
    
    >>> sinseries() == altsinseries()
    True
    """
    from math import factorial
    return PowerSeries(f=lambda n: Fraction((1, -1)[(n//2) % 2], factorial(n)) if (n % 2) == 1 else Fraction(0, 1))


def altcosseries():
    """Alternate way of representing cosine as a PowerSeries.
    
    This is the factorial implementation, provided for
    comparison.
    
    Check the alternate representation:
    
    >>> cosseries() == altcosseries()
    True
    """
    from math import factorial
    return PowerSeries(f=lambda n: Fraction((1, -1)[(n//2) % 2], factorial(n)) if (n % 2) == 0 else Fraction(0, 1))


def alttanseries():
    """Alternate way of representing tangent as a PowerSeries.
    
    Check the alternate representation:
    
    >>> tanseries() == alttanseries()
    True
    """
    return altsinseries() / altcosseries()


def altsecseries():
    """Alternate way of representing secant as a PowerSeries.
    
    Check the alternate representation:
    
    >>> secseries() == altsecseries()
    True
    """
    return altcosseries().reciprocal()


def altarcsinseries():
    """Alternate way of representing arcsin as a PowerSeries.
    
    Check alternate representation:
    
    >>> arcsinseries() == altarcsinseries()
    True
    """
    return altsinseries().inverse()


def altarctanseries():
    """Alternate way of representing arctan as a PowerSeries.
    
    Check alternate representation:
    
    >>> arctanseries() == altarctanseries()
    True
    """
    return alttanseries().inverse()


def altsinhseries():
    """Alternate way of representing hyperbolic sine as a PowerSeries.
    
    This is the factorial implementation, provided for
    comparison.
    
    Check the alternate representation:
    
    >>> sinhseries() == altsinhseries()
    True
    """
    from math import factorial
    return PowerSeries(f=lambda n: Fraction(1, factorial(n)) if (n % 2) == 1 else Fraction(0, 1))


def altcoshseries():
    """Alternate way of representing hyperbolic cosine as a PowerSeries.
    
    This is the factorial implementation, provided for
    comparison.
    
    Check the alternate representation:
    
    >>> coshseries() == altcoshseries()
    True
    """
    from math import factorial
    return PowerSeries(f=lambda n: Fraction(1, factorial(n)) if (n % 2) == 0 else Fraction(0, 1))


def alttanhseries():
    """Alternate way of representing hyperbolic tangent as a PowerSeries.
    
    Check the alternate representation:
    
    >>> tanhseries() == alttanhseries()
    True
    """
    return altsinhseries() / altcoshseries()


def altsechseries():
    """Alternate way of representing hyperbolic secant as a PowerSeries.
    
    Check the alternate representation:
    
    >>> sechseries() == altsechseries()
    True
    """
    return altcoshseries().reciprocal()


def altarcsinhseries():
    """Alternate way of representing hyperbolic arcsin as a PowerSeries.
    
    Check alternate representation:
    
    >>> arcsinhseries() == altarcsinhseries()
    True
    """
    return altsinhseries().inverse()


def altarctanhseries():
    """Alternate way of representing hyperbolic arctan as a PowerSeries.
    
    Check alternate representation:
    
    >>> arctanhseries() == altarctanhseries()
    True
    """
    return alttanhseries().inverse()


if __name__ == '__main__':
    import doctest
    doctest.testmod()
