r"""
"""


#[

from __future__ import annotations

import textwrap as _tw

from ._functionalize import FUNC_STRING

#]


#-------------------------------------------------------------------------------
# Mixin methods
#-------------------------------------------------------------------------------


class Mixin:
    #[

    def shift(
        self,
        by: ShiftType = -1,
        **kwargs,
    ) -> None:
        r"""
................................................................................

## `Series.shift`

Called as `x.shift(...)` (method form) or
`datapie.shift(x, ...)` (function form).

==Moves a time series in time, either by retiming it or by replacing each observation with an earlier one.==

    self.shift(by=-1, **kwargs)

A number leaves the observations alone and moves the start date. The
strings mostly do the opposite, keeping the span and rewriting the
values; `"yoy"` is the exception and retimes like a number.


**Input arguments.**


???+ input "by"
    A whole number of periods, or one of four strings — a float takes
    the string route and fails.

    A numeric `by` is subtracted from the start date, so the sign runs
    opposite to what you may expect: `by=-1` moves the series one
    period later, and `by=1` moves it one period earlier. Left alone it
    is `-1`.

    A string `by` is one of the following:

    | Value    | Effect
    |----------|--------
    | `"yoy"`  | Retimes by a whole year, like a number does — the same as passing minus the number of periods in a year, so the series moves one year later
    | `"soy"`  | Replaces every observation with the one from the first period of its year
    | `"eopy"` | Replaces every observation with the one from the last period of the previous year
    | `"tty"`  | Replaces every observation with the one from the previous period, except in the first period of each year

    Because `"eopy"` reaches into the year before the data begins, a
    series not already covering that year comes back empty. Any other
    string is turned into a method name and looked up, so a misspelling
    fails with `AttributeError: 'Series' object has no attribute
    '_shift_nonsense'`.

???+ input "**kwargs"
    Passed on to the string forms. Only `"tty"` reads anything from
    them: `neutral_value` is what it writes in the first period of each
    year, and left alone it is `None`, which leaves that period
    missing.


### Returns


Nothing; the series is modified in place. An empty series is left
alone. Periods left without a source observation come back missing, and
missing observations at either end are then trimmed off, so a series
can come back shorter than it went in.


### Examples


A numeric shift keeps the values and moves the dates:

    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([10., 20., 30., 40.]))
    >>> x.shift(-1)
    >>> x.start
    qq(2020,2)
    >>> x.get_data()[:, 0].tolist()
    [10.0, 20.0, 30.0, 40.0]

A string shift keeps the dates and rewrites the values:

    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([10., 20., 30., 40.]))
    >>> x.shift("soy")
    >>> x.start
    qq(2020,1)
    >>> x.get_data()[:, 0].tolist()
    [10.0, 10.0, 10.0, 10.0]

With `"tty"` the first period of the year takes the `neutral_value`
instead of an earlier observation:

    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([10., 20., 30., 40.]))
    >>> x.shift("tty", neutral_value=0)
    >>> x.start
    qq(2020,1)
    >>> x.get_data()[:, 0].tolist()
    [0.0, 10.0, 20.0, 30.0]

................................................................................
        """
        if isinstance(by, int):
            self._shift_by_number(by, **kwargs, )
        else:
            method_name = f"_shift_{by}"
            getattr(self, method_name)(**kwargs, )

    def redate(
        self,
        new_date: Period,
        old_date: Period | None = None,
    ) -> None:
        r"""
................................................................................

## `Series.redate`

Called as `x.redate(...)` (method form) or
`datapie.redate(x, ...)` (function form).

==Restamps a time series onto new periods, keeping the observations and their order.==

    self.redate(new_date, old_date=None)

Where `shift` counts periods, this names the period to land on. The
values never change; only their time stamps do.


**Input arguments.**


???+ input "new_date"
    The period the series is moved onto.

???+ input "old_date"
    The period being moved from. Left as `None` the move is measured
    from the start, so `new_date` simply becomes the new start. Given
    an `old_date`, the series slides so that whichever observation sat
    at `old_date` now sits at `new_date`.


### Returns


Nothing; the series is modified in place.


### Examples


Without `old_date` the start becomes `new_date`:

    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([10., 20., 30., 40.]))
    >>> x.redate(dp.qq(2021, 1))
    >>> x.start
    qq(2021,1)
    >>> x.get_data()[:, 0].tolist()
    [10.0, 20.0, 30.0, 40.0]

With `old_date`, the third observation is pinned to 2021-Q1 and the
start moves to keep the spacing:

    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([10., 20., 30., 40.]))
    >>> x.redate(dp.qq(2021, 1), dp.qq(2020, 3))
    >>> x.start
    qq(2020,3)
    >>> float(x.get_data(dp.qq(2021, 1))[0, 0])
    30.0

................................................................................
        """
        if old_date is None:
            self.start = new_date
        else:
            self.start = new_date - (old_date - self.start)

    #]


#-------------------------------------------------------------------------------
# Functional forms
#-------------------------------------------------------------------------------


_functional_forms = {"shift", "redate", }

for n in _functional_forms:
    code = FUNC_STRING.format(n=n, )
    exec(_tw.dedent(code, ), globals(), )

__all__ = tuple(_functional_forms)

