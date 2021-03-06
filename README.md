Python Power Series
===================

Power series representations in Python.
Based on http://doc.cat-v.org/bell_labs/squinting_at_power_series/squint.pdf.

This is a Python implementation of the pseudocode in the above paper by
Doug McIlroy, with some additional operations added that the paper did
not include. I have also added a module that uses the power series
implementation to compute functions represented by series, with simple
convergence testing.

Back when McIlroy's paper was first written, he noted that programming
languages with the key features needed for such an implementation were
not in common use. Things are certainly different now; the Python
implementation given here is a fairly straightforward expression of
the algorithms in the paper, and it's fast, but McIlroy put a Haskell
implementation on the web in 2007 that's way more compact; see here:

http://www.cs.dartmouth.edu/~doug/powser.html

All of the Haskell definitions there are one-liners. But I like Python,
and AFAIK no one has done an implementation of this stuff in Python,
so there you are. :-)

See the docstrings in powerseries.py and powerfunc.py for more information.

Released under the open source MIT license:
http://www.opensource.org/licenses/MIT

Copyright (C) 2011 Peter A. Donis.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
