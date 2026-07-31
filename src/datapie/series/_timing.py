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

==Shift the time series start date==

Shift the start date of the time series by a number of periods or to a specific
date.

    self.shift(by=-1, )

### Input arguments ###

???+ input "self"
    The current time series object that will be shifted.

???+ input "by"
    The number of periods to shift the observations by. If `by` is a string,
    the observations are manipulated as follows:

    * `"yoy"`: Shift all observations by one year back.

    * `"soy"`: Shift to the start of the year.

    * `"eopy"`: Shift to the end of the previous year.

................................................................................
        """
        if isinstance(by, int):
            self._shift_by_number(by, **kwargs, )
        else:
            method_name = f"_shift_{by}"
            getattr(self, method_name)(**kwargs, )

    # ==========================================================================
    #  ### `shift(by=-1, **kwargs)`
    #
    #  Moves a time series in time, either by retiming it or by replacing
    #  each observation with an earlier one.
    #
    #  The two kinds of `by` do quite different things. A number leaves the
    #  observations exactly as they are and moves the start date, so the
    #  same values end up stamped with different periods. A string leaves
    #  the span alone and rewrites the values.
    #
    #  **Parameters.** A numeric `by` is subtracted from the start date, so
    #  the sign runs opposite to what you may expect: `by=-1` moves the
    #  series one period later, and `by=1` moves it one period earlier.
    #  Left alone it is `-1`. This is the form the temporal change methods
    #  use, where lining a series up against its own past means pushing the
    #  copy forward.
    #
    #  A string `by` is one of `"yoy"`, `"soy"`, `"eopy"` and `"tty"`.
    #  `"yoy"` retimes by a whole year, like a number does. `"soy"`
    #  replaces every observation with the one from the first period of its
    #  year, `"eopy"` with the one from the last period of the previous
    #  year, and `"tty"` with the previous period except at the start of a
    #  year. Because `"eopy"` reaches into the year before the data begins,
    #  a series not already covering that year comes back empty. Any other
    #  string is turned into a method name and looked up, so a misspelling
    #  fails with `AttributeError: 'Series' object has no attribute
    #  '_shift_nonsense'`.
    #
    #  **Returns.** Nothing; the series is modified in place. An empty
    #  series is left alone.
    #
    #  **Examples.** A numeric shift keeps the values and moves the dates:
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(start=dp.qq(2020, 1),
    #      ...     values=np.array([10., 20., 30., 40.]))
    #      >>> x.shift(-1)
    #      >>> x.start
    #      qq(2020,2)
    #      >>> x.get_data()[:, 0].tolist()
    #      [10.0, 20.0, 30.0, 40.0]
    #
    #  A string shift keeps the dates and rewrites the values:
    #
    #      >>> x = dp.Series(start=dp.qq(2020, 1),
    #      ...     values=np.array([10., 20., 30., 40.]))
    #      >>> x.shift("soy")
    #      >>> x.start
    #      qq(2020,1)
    #      >>> x.get_data()[:, 0].tolist()
    #      [10.0, 10.0, 10.0, 10.0]
    #
    # ==========================================================================

    def redate(
        self,
        new_date: Period,
        old_date: Period | None = None,
    ) -> None:
        r"""
        """
        if old_date is None:
            self.start = new_date
        else:
            self.start = new_date - (old_date - self.start)

    # ==========================================================================
    #  ### `redate(new_date, old_date=None)`
    #
    #  Restamps a time series onto new periods, keeping the observations
    #  and their order.
    #
    #  Where `shift` counts periods, this names the period you want the
    #  series to land on, which is easier when you know the target date but
    #  not the distance to it. The values never change; only their time
    #  stamps do.
    #
    #  **Parameters.** `new_date` is the period the series is moved onto.
    #  `old_date` is the period being moved from, and left as `None` the
    #  move is measured from the start, so `new_date` simply becomes the
    #  new start. Given an `old_date`, the series slides so that whichever
    #  observation sat at `old_date` now sits at `new_date`.
    #
    #  **Returns.** Nothing; the series is modified in place.
    #
    #  **Examples.** Without `old_date` the start becomes `new_date`:
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(start=dp.qq(2020, 1),
    #      ...     values=np.array([10., 20., 30., 40.]))
    #      >>> x.redate(dp.qq(2021, 1))
    #      >>> x.start
    #      qq(2021,1)
    #      >>> x.get_data()[:, 0].tolist()
    #      [10.0, 20.0, 30.0, 40.0]
    #
    #  With `old_date`, the third observation is pinned to 2021-Q1 and the
    #  start moves to keep the spacing:
    #
    #      >>> x = dp.Series(start=dp.qq(2020, 1),
    #      ...     values=np.array([10., 20., 30., 40.]))
    #      >>> x.redate(dp.qq(2021, 1), dp.qq(2020, 3))
    #      >>> x.start
    #      qq(2020,3)
    #      >>> float(x.get_data(dp.qq(2021, 1))[0, 0])
    #      30.0
    #
    # ==========================================================================

    #]


#-------------------------------------------------------------------------------
# Functional forms
#-------------------------------------------------------------------------------


_functional_forms = {"shift", "redate", }

for n in _functional_forms:
    code = FUNC_STRING.format(n=n, )
    exec(_tw.dedent(code, ), globals(), )

__all__ = tuple(_functional_forms)

