"""
Time series indexing inlay
"""


#[

from __future__ import annotations

import textwrap as _tw
import numpy as _np
import documark as _dm

from ._categories import CATEGORIES
from ._functionalize import FUNC_STRING

#]


#-------------------------------------------------------------------------------
# Mixin methods
#-------------------------------------------------------------------------------


class Mixin:
    #[

    @_dm.reference(
        category=None,
        call_name=CATEGORIES["indexing"],
        call_name_is_code=False,
        priority=30,
    )
    def indexing(self, /, ) -> None:
        r"""
················································································

==Carries the documentation for the four ways a time series can be indexed.==

    self.indexing()

Calling it raises `NotImplementedError`. It exists only to carry this
overview in the reference documentation; the four syntaxes below are the
working things.

Note the square versus round brackets:

| Indexing                                           | Description
|----------------------------------------------------|-------------
| `self[shift]`                                      | Time shift
| `self[dates]`, `self[dates, variants]`             | Data extraction
| `self[dates] = ...`, `self[dates, variants] = ...` | Data assignment
| `self(dates)`, `self(dates, variants)`             | Time `Series` recreation

Throughout, `dates` is a `Period`, a tuple of `Periods`, or a time
`Span`; `variants` is an integer, a tuple of integers, or a `slice`.


### Time shift


    self[shift]

An **integer** index is read as a time shift. It returns a new series --
the original is not changed -- with the same values stamped `shift`
periods away.

The sign runs opposite to what you may expect, exactly as in `shift`
itself: the number is subtracted from the start, so `self[-1]` moves the
series one period later and `self[1]` one period earlier. `True` and
`False` are integers in Python, so `self[True]` shifts by one rather
than doing anything with a boolean.


### Data extraction


    self[dates]
    self[dates, variants]

Returns a two-dimensional `numpy` array, time running down the rows and
variants across the columns, even when only one of either is asked for.
Periods outside the series come back missing rather than raising, as in
`get_data`.


### Data assignment


    self[dates] = ...
    self[dates, variants] = ...

Writes into the series through `set_data`, so it grows the span when the
periods fall outside it and trims afterwards.


### Time `Series` recreation


    self(dates)
    self(dates, variants)

Returns a new time `Series` built from the selected data, where the
square-bracket form would return a bare array.


### Returns


Nothing; this method raises `NotImplementedError` if called.


### Examples


A time shift, an extraction and a recreation from the same series:

    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2., 3.]))
    >>> x[-1].start
    qq(2020,2)
    >>> x[dp.qq(2020, 2)].tolist()
    [[2.0]]
    >>> x(dp.Span(dp.qq(2020, 1), dp.qq(2020, 2))).num_periods
    2

Assignment writes in place:

    >>> x[dp.qq(2020, 2)] = 99.
    >>> x.get_data()[:, 0].tolist()
    [1.0, 99.0, 3.0]

················································································
        """
        raise NotImplementedError

    def __getitem__(
        self,
        index: int | tuple,
    ) -> _np.ndarray:
        """
        Get data self[dates] or self[dates, variants]
        """
        if isinstance(index, int, ):
            # Time shift
            new = self.copy()
            new.shift(index, )
            return new
        else:
            # Extract data
            if isinstance(index, tuple, ):
                dates, variants = index
            else:
                dates, variants = index, None
            return self.get_data(dates, variants, )

    def __setitem__(
        self,
        index: int | tuple,
        data,
    ) -> None:
        """
        Set data self[dates] = ... or self[dates, variants] = ...
        """
        if not isinstance(index, tuple):
            index = (index, None, )
        return self.set_data(index[0], data, index[1], )

    def __call__(
        self,
        *index,
    ) -> Self:
        """
        Create a new time series based on date retrieved by self[dates] or self[dates, variants]
        """
        return self._get_data_and_recreate(*index, )

    @_dm.reference(category="indexing", )
    def reverse_variants(self, ) -> None:
        r"""
················································································

## `Series.reverse_variants`

Called as `x.reverse_variants(...)` (method form) or
`datapie.reverse_variants(x, ...)` (function form).

==Reverses the order of the variants, that is the columns, of the time series.==

    self.reverse_variants()
    self.reverse_columns()

The time dimension is untouched: every column keeps its own values in
their own periods, and only the order of the columns changes.
`reverse_columns` is the same method under another name.


### Returns


Nothing; the series is modified in place.


### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([[1., 2.], [3., 4.]]))
    >>> x.reverse_variants()
    >>> x.get_data().tolist()
    [[2.0, 1.0], [4.0, 3.0]]

················································································
        """
        self.data = self.data[:, ::-1]

    @_dm.reference(category="indexing", )
    def reverse_periods(self, ) -> None:
        r"""
················································································

## `Series.reverse_periods`

Called as `x.reverse_periods(...)` (method form) or
`datapie.reverse_periods(x, ...)` (function form).

==Reverses the order of the observations in time, leaving the periods where they are.==

    self.reverse_periods()
    self.reverse_rows()

The rows of the data are flipped while `start` stays put, so the series
covers the same span as before and the last observation now sits at the
first period. It is the values that are reversed, not the time stamps --
nothing here re-dates the series. `reverse_rows` is the same method
under another name.


### Returns


Nothing; the series is modified in place.


### Examples


The span is unchanged and the values run backwards through it:

    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2., 3.]))
    >>> x.reverse_periods()
    >>> x.start
    qq(2020,1)
    >>> x.get_data()[:, 0].tolist()
    [3.0, 2.0, 1.0]

················································································
        """
        self.data = self.data[::-1, :]

    reverse_columns = reverse_variants
    reverse_rows = reverse_periods

    #]


#---------------------------------------------------------------------------------
# Functional forms
#---------------------------------------------------------------------------------


__all__ = (
    "reverse_variants",
    "reverse_columns",
    "reverse_periods",
    "reverse_rows",
)


for n in __all__:
    code = FUNC_STRING.format(n=n, )
    exec(_tw.dedent(code, ), )


