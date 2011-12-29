Power Series Recursive Formulas
===============================

This document provides a convenient quick reference for the recursion
formulas used to construct the generators for power series operations.
All but the last two are taken directly from the McIlroy paper; the
last two are derived using similar methods.

The following operations are assumed to be known and formulas are not
given here:

- Head extraction (take the first term only, with all subsequent terms
  zero);

- Tail extraction (this shifts the series one term to the left, so the
  head term is omitted);

- Multiplication by x (this shifts the series one term to the right,
  with an initial zero term);

- Addition (adding a number to a series just adds to the constant term;
  adding two series is obviously term by term);

- Multiplication by a number (this just multiplies each term by the
  given number);

- Differentiation (term by term using the standard formula);

- Integration (term by term using the standard formula after the initial
  constant);

The key to deriving recursion formulas for power series operations is to
represent a series as the head plus x times the tail:

    F = f0 + x F1

By expanding the various series involved in each operation in this way,
we can reduce the operation to other known operations, such as those
given above and those defined below prior to the operation of interest,
*plus* the operation of interest itself, provided it is applied with a
different set of arguments (i.e., no infinite loops).

Multiplication
--------------

This is the first significant operation, from which the others are built.
We have two series, F and G, which multiply as follows:

    F * G = (f0 + x F1) * (g0 + x G1)
          = f0 g0 + x (f0 G1 + g0 F1 + x F1 * G1)

All of the operations are known, so this formula is sufficient to
implement multiplication recursively.

Composition
-----------

This is the first operation to require expanding the target series
explicitly. We seek a series C = F(G) defined by

    C = c0 + x C1 = f0 + (g0 + x G1) * F1(G)

If g0 is not zero, the sum for the first term c0 will be infinite; so
we stipulate that g0 = 0. This gives

    C = c0 + x C1 = f0 + x G1 * F1(G)

Now everything is finite and all operations are known, so this formula
is sufficient to implement composition recursively.

Exponentiation
--------------

This operation is the first to make use of differentiation and
integration. The key fact that enables recursion is that integration
first yields its constant before requiring any computation of other
terms, so an integral of a series can refer to that same series
without causing an infinite regress.

We seek a series E = exp(F) defined by

    E = e0 + x E1 = exp(f0 + x F1) = exp(f0) exp(x F1)

To ensure that e0 is rational we stipulate that f0 = 0, which makes
e0 = 1. Then we use a neat trick; differentiating E = exp(F) gives

    dE/dx = d/dx exp(F) = exp(F) dF/dx = E * dF/dx

which we can then integrate to obtain

    E = integral(E * dF/dx) + e0

This is sufficient to implement the recursive generator, since all
operations are now known, and the constant e0 is known to be 1 so
the integral can get started.

Reciprocal
----------

Here we seek a series R = 1 / F, or F * R = 1, so that

    F * R = f0 r0 + x (f0 R1 + r0 F1 + x F1 * R1) = 1

We can see that r0 = 1 / f0, and the coefficient of x must be zero,
which gives

    R1 = - 1 / f0 (F1 * (r0 + x R1))

So we have

    R = r0 + x R1 = 1 / f0 (1 - x F1 * R)

This is sufficient to implement a recursive generator since the
first term of R is known, so the multiplication by R will not
cause an infinite regress.

Inverse
-------

We seek a series I such that F(I(x)) = x. We find that the initial
term i0 must be a root of F, so to keep i0 rational, we stipulate
that i0 = 0 and therefore f0 = 0. Then we expand F as

    F = x F1 = x (f1 + x F2)

and similarly

    I = x I1 = x (i1 + x I2)

From our formula above for composition we have

    F(I) = x I1 * F1(I) = x

Expanding F1(I) using the composition formula again and dividing
through by x gives

    I1 * F1(I) = I1 * (f1 + x I1 F2(I)) = 1

Moving the x term to the other side and dividing through by f1,
we get

    I1 = 1 / f1 (1 - x I1 * I1 * F2(I))

This is now sufficient to implement the generator recursively.
Note that the first term of I being zero is also required so
that the composition F2(I) can proceed.

Square Root
-----------

We seek a series S such that S * S = F. This expands to

    (s0 + x S1) * (s0 + x S1) = f0 + x F1

which in turn expands to

    s0 * s0 + x (2 s0 S1 + x S1 * S1) = f0 + x F1

We see that s0 = sqrt(f0) and we rearrange the remaining terms to
obtain

    F1 = s0 S1 + (s0 + x S1) * S1 = (s0 + S) * S1

We know how to take reciprocals of series, so we can rearrange this
to

    S1 = F1 / (s0 + S)

and we now have a formula that can be used to implement a generator.
The only caveat is that if f0 = 0, we can't proceed, because the
reciprocal will throw an error (since it requires 1 / s0 and hence
1 / f0 to not be a division by zero).

Logarithm
---------

We can't actually take the log of a series directly, because our
series are implicitly based on Taylor expanding around x = 0, and
log(0) diverges. But we can take the log of 1 + F for a series F,
which amounts to requiring f0 = 0 and Taylor expanding around x = 1
instead.

We use the fact that d/dx log(1 + F) = 1/(1 + F) dF/dx; this can be
integrated to give the simple formula

    L = integral(dF/dx / (1 + F))

where we can see that the integration constant is zero because
L = 0 when F = 0 (i.e., when 1 + F = 1). Again, since this is an
integral, it yields a constant before needing any terms from
recursing on itself, so there will be no infinite regress.
