"""
Temporal change functions
"""


#[

from __future__ import annotations

from typing import Self, Callable
from numbers import Real
import numpy as _np
import textwrap as _tw
import documark as _dm

from ..periods import Span
from ._functionalize import FUNC_STRING
from ._categories import CATEGORIES

#]


#-------------------------------------------------------------------------------
# Mixin methodsFunctions to be mixed in
#-------------------------------------------------------------------------------


class Mixin:
    #[

    @_dm.reference(
        category=None,
        call_name=CATEGORIES["temporal_change"],
        call_name_is_code=False,
        priority=20,
    )
    def temporal_change(
        self,
        by: int | str,
        func: Callable,
        **kwargs,
    ) -> None:
        r"""
································································

==Compares every observation with an earlier one and replaces it with the result of `func`.==

    self.temporal_change(by, func, **kwargs)

This is the engine under `diff`, `diff_log`, `pct`, `roc` and their
annualized counterparts, and where the `shift` argument they all take
is decided. Note that the first argument is called `by` here, while the
methods built on it call the same thing `shift`.

Functions with a free `shift`, where $x_t$ is the current observation
and $x_s$ the earlier one:

| Function      | Description
|---------------|-------------
| `diff`        | First difference, $y_t = x_t - x_s$
| `diff_log`    | First difference of logs, $y_t = \log x_t - \log x_s$
| `pct`         | Percent change, $y_t = 100 \cdot (x_t/x_s - 1)$
| `roc`         | Gross rate of change, $y_t = x_t/x_s$

Functions with a fixed shift of $-1$, where $a$ is the number of
periods in a year at the frequency of the series:

| Function      | Description
|---------------|-------------
| `adiff`       | Annualized first difference, $y_t = a \cdot (x_t - x_{t-1})$
| `adiff_log`   | Annualized first difference of logs, $y_t = a \cdot (\log x_t - \log x_{t-1})$
| `apct`        | Annualized percent change, $y_t = 100 \cdot \left[ (x_t/x_{t-1})^a - 1 \right]$
| `aroc`        | Annualized gross rate of change, $y_t = (x_t/x_{t-1})^a$


**Input arguments.**


???+ input "by"
    Which earlier period to compare against. A negative integer counts
    that many periods back, so `-1` is the previous period and `-4` the
    same period a year earlier in quarterly data. Zero, a positive
    number and a non-integer all raise `ValueError: Time shift must be
    a negative integer or a string`.

    It can also be one of four strings:

    | Value     | Reference period $s$
    |-----------|----------------------
    | `"yoy"`   | A whole year back, $s = t - a$
    | `"soy"`   | The first period of the current year
    | `"eopy"`  | The last period of the previous year
    | `"tty"`   | As `-1`, except in the first period of each year, where the observation is left as it stands

    Any other string reaches the shifting machinery and fails there
    with `AttributeError: 'Series' object has no attribute
    '_shift_nonsense'`, naming a method you never called.

???+ input "func"
    Takes the current and the earlier value and returns the result.

???+ input "**kwargs"
    Passed on to the shift, which is how the built-in methods supply
    `neutral_value`.


### Returns


Nothing; the series is modified in place. Periods left with nothing to
compare against come back missing and are trimmed.


### Examples


Your own `func`, differencing against the previous period. The first
period has nothing behind it, so the series comes back one period
shorter, starting a quarter later:

    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([100., 110., 121., 133.1]))
    >>> x.temporal_change(-1, lambda a, b: a - b)
    >>> x.start
    qq(2020,2)
    >>> [round(v, 4) for v in x.get_data()[:, 0].tolist()]
    [10.0, 11.0, 12.1]

With `"soy"` every period has a reference, so nothing is trimmed and
the first quarter compares against itself:

    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([100., 110., 121., 133.1]))
    >>> x.diff("soy")
    >>> [round(v, 4) for v in x.get_data()[:, 0].tolist()]
    [0.0, 10.0, 21.0, 33.1]

································································
        """
        _catch_invalid_shift(by, )
        other = self.copy()
        other.shift(by, **kwargs, )
        self._binop(other, func, new=self, )



    @_dm.reference(
        category=None,
        call_name=CATEGORIES["temporal_change_conversion"],
        call_name_is_code=False,
        priority=19,
    )
    def temporal_change_conversion(self, ):
        r"""
································································

==Carries the shared documentation for the five methods that convert one measure of change into another.==

    self.temporal_change_conversion()

Calling it does nothing: the body is a single `pass`. It exists only to
carry this overview in the reference documentation.

The five it stands for each rewrite the values of the series in place
and take no arguments:

| Function          | Description
|-------------------|-------------
| `roc_from_pct`    | Convert percent change to gross rate of change
| `pct_from_roc`    | Convert gross rate of change to percent change
| `pct_from_apct`   | Convert annualized percent change to percent change
| `roc_from_apct`   | Convert annualized percent change to gross rate of change
| `roc_from_aroc`   | Documented as converting an annualized gross rate to a per-period one; see its own entry, where the behaviour differs from the name

The three that undo an annualization -- `pct_from_apct`,
`roc_from_apct` and `roc_from_aroc` -- use the number of periods in a
year for the series' frequency; the other two do not look at the
frequency at all.


### Returns


`None`, and the series is untouched.


### Examples


The two that ignore the frequency invert each other, up to floating-point
error -- the round trip below is rounded because it does not come back
exactly:

    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([10., 20.]))
    >>> x.roc_from_pct()
    >>> x.get_data()[:, 0].tolist()
    [1.1, 1.2]
    >>> x.pct_from_roc()
    >>> [round(v, 10) for v in x.get_data()[:, 0].tolist()]
    [10.0, 20.0]

································································
        """
        pass



    @_dm.reference(category="temporal_change", add_heading=False, )
    def diff(
        self,
        shift: int | str = -1,
    ) -> None:
        r"""
································································

## `diff`

Called as `x.diff(...)` (method form) or `datapie.diff(x, ...)` (function form).

==Replaces every observation with its change from an earlier period, as a difference in levels.==

    self.diff(shift=-1)


**Input arguments.**


???+ input "shift"
    Which earlier period to compare against. Described in full under
    the temporal change calculations; `-1`, the previous period, when
    left alone.


### Returns


Nothing; the series is modified in place.


### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([100., 110., 121., 133.1]))
    >>> x.diff()
    >>> [round(v, 4) for v in x.get_data()[:, 0].tolist()]
    [10.0, 11.0, 12.1]

································································
        """
        self.temporal_change(shift, lambda x, y: x - y, neutral_value=0, )



    @_dm.reference(category="temporal_change", add_heading=False, )
    def adiff(self, ) -> None:
        r"""
································································

## `adiff`

Called as `x.adiff(...)` (method form) or
`datapie.adiff(x, ...)` (function form).

==Replaces every observation with its change from the previous period, scaled up to a yearly rate.==

    self.adiff()

The difference against the previous period is multiplied by the number
of periods in a year, so quarterly differences are multiplied by four.
There is no `shift`; it is always `-1`.


**Input arguments.**


???+ input "self"
    The series whose values are rewritten. There are no other
    arguments.


### Returns


Nothing; the series is modified in place.


### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([100., 110., 121., 133.1]))
    >>> x.adiff()
    >>> [round(v, 4) for v in x.get_data()[:, 0].tolist()]
    [40.0, 44.0, 48.4]

································································
        """
        shift = -1
        factor = self.frequency.value or 1
        self.temporal_change(shift, lambda x, y: factor*(x - y), neutral_value=0, )



    @_dm.reference(category="temporal_change", add_heading=False, )
    def diff_log(
        self,
        shift: int | str = -1,
    ) -> None:
        r"""
································································

## `diff_log`

Called as `x.diff_log(...)` (method form) or
`datapie.diff_log(x, ...)` (function form).

==Replaces every observation with the change in its logarithm from an earlier period.==

    self.diff_log(shift=-1)

Close to a proportional change for small movements, and it adds up
across periods, which a percent change does not.


**Input arguments.**


???+ input "shift"
    Which earlier period to compare against. Described in full under
    the temporal change calculations; `-1`, the previous period, when
    left alone.


### Returns


Nothing; the series is modified in place.


### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([100., 110., 121., 133.1]))
    >>> x.diff_log()
    >>> [round(v, 4) for v in x.get_data()[:, 0].tolist()]
    [0.0953, 0.0953, 0.0953]

································································
        """
        self.temporal_change(shift, lambda x, y: _np.log(x) - _np.log(y), neutral_value=0, )



    @_dm.reference(category="temporal_change", add_heading=False, )
    def adiff_log(self, ) -> None:
        r"""
································································

## `adiff_log`

Called as `x.adiff_log(...)` (method form) or
`datapie.adiff_log(x, ...)` (function form).

==Replaces every observation with the change in its logarithm from the previous period, scaled up to a yearly rate.==

    self.adiff_log()

The log difference is multiplied by the number of periods in a year.
There is no `shift`; it is always `-1`.


**Input arguments.**


???+ input "self"
    The series whose values are rewritten. There are no other
    arguments.


### Returns


Nothing; the series is modified in place.


### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([100., 110., 121., 133.1]))
    >>> x.adiff_log()
    >>> [round(v, 4) for v in x.get_data()[:, 0].tolist()]
    [0.3812, 0.3812, 0.3812]

································································
        """
        shift = -1
        factor = self.frequency.value or 1
        self.temporal_change(shift, lambda x, y: factor*(_np.log(x) - _np.log(y)), neutral_value=0, )



    @_dm.reference(category="temporal_change", add_heading=False, )
    def roc(
        self,
        shift: int | str = -1,
    ) -> None:
        r"""
································································

## `roc`

Called as `x.roc(...)` (method form) or `datapie.roc(x, ...)` (function form).

==Replaces every observation with its gross rate of change against an earlier period.==

    self.roc(shift=-1)

A gross rate is the ratio itself, so growth of ten percent comes out as
`1.1` rather than `10`.


**Input arguments.**


???+ input "shift"
    Which earlier period to compare against. Described in full under
    the temporal change calculations; `-1`, the previous period, when
    left alone.


### Returns


Nothing; the series is modified in place.


### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([100., 110., 121., 133.1]))
    >>> x.roc()
    >>> [round(v, 4) for v in x.get_data()[:, 0].tolist()]
    [1.1, 1.1, 1.1]

································································
        """
        self.temporal_change(shift, lambda x, y: x/y, neutral_value=1, )



    @_dm.reference(category="temporal_change", add_heading=False, )
    def aroc(
        self,
    ) -> None:
        r"""
································································

## `aroc`

Called as `x.aroc(...)` (method form) or `datapie.aroc(x, ...)` (function form).

==Replaces every observation with its gross rate of change against the previous period, compounded to a yearly rate.==

    self.aroc()

The ratio is raised to the number of periods in a year, so a quarterly
ratio of `1.1` becomes `1.1**4`. There is no `shift`; it is always
`-1`.


**Input arguments.**


???+ input "self"
    The series whose values are rewritten. There are no other
    arguments.


### Returns


Nothing; the series is modified in place.


### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([100., 110., 121., 133.1]))
    >>> x.aroc()
    >>> [round(v, 4) for v in x.get_data()[:, 0].tolist()]
    [1.4641, 1.4641, 1.4641]

································································
        """
        shift = -1
        factor = self.frequency.value or 1
        self.temporal_change(shift, lambda x, y: (x/y)**factor, neutral_value=1, )



    @_dm.reference(category="temporal_change", add_heading=False, )
    def pct(
        self,
        shift: int | str = -1,
    ) -> None:
        r"""
································································

## `pct`

Called as `x.pct(...)` (method form) or `datapie.pct(x, ...)` (function form).

==Replaces every observation with its percent change against an earlier period.==

    self.pct(shift=-1)


**Input arguments.**


???+ input "shift"
    Which earlier period to compare against. Described in full under
    the temporal change calculations; `-1`, the previous period, when
    left alone.


### Returns


Nothing; the series is modified in place.


### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([100., 110., 121., 133.1]))
    >>> x.pct()
    >>> [round(v, 4) for v in x.get_data()[:, 0].tolist()]
    [10.0, 10.0, 10.0]

································································
        """
        self.temporal_change(shift, lambda x, y: 100*(x/y - 1), neutral_value=None, )



    @_dm.reference(category="temporal_change", add_heading=False, )
    def apct(
        self,
    ) -> None:
        r"""
································································

## `apct`

Called as `x.apct(...)` (method form) or `datapie.apct(x, ...)` (function form).

==Replaces every observation with its percent change against the previous period, compounded to a yearly rate.==

    self.apct()

Ten percent a quarter compounds to just over forty-six percent a year,
not forty. There is no `shift`; it is always `-1`.


**Input arguments.**


???+ input "self"
    The series whose values are rewritten. There are no other
    arguments.


### Returns


Nothing; the series is modified in place.


### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([100., 110., 121., 133.1]))
    >>> x.apct()
    >>> [round(v, 4) for v in x.get_data()[:, 0].tolist()]
    [46.41, 46.41, 46.41]

································································
        """
        shift = -1
        factor = self.frequency.value or 1
        self.temporal_change(shift, lambda x, y: 100*((x/y)**factor - 1), neutral_value=None, )



    @_dm.reference(category="temporal_change_conversion", add_heading=False, )
    def roc_from_pct(
        self,
    ) -> None:
        r"""
································································

## `roc_from_pct`

Called as `x.roc_from_pct(...)` (method form) or
`datapie.roc_from_pct(x, ...)` (function form).

==Reads the values as percent changes and rewrites them as gross rates of change.==

    self.roc_from_pct()

Ten percent becomes `1.1`. The frequency is not consulted, so this is a
plain rescaling and nothing is annualized either way.


**Input arguments.**


???+ input "self"
    The series whose values are rewritten. There are no other
    arguments.


### Returns


Nothing; the series is modified in place.


### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1), values=np.array([10., 20.]))
    >>> x.roc_from_pct()
    >>> [round(v, 4) for v in x.get_data()[:, 0].tolist()]
    [1.1, 1.2]

································································
        """
        self.data = 1 + self.data/100



    @_dm.reference(category="temporal_change_conversion", add_heading=False, )
    def pct_from_roc(
        self,
    ) -> None:
        r"""
································································

## `pct_from_roc`

Called as `x.pct_from_roc(...)` (method form) or
`datapie.pct_from_roc(x, ...)` (function form).

==Reads the values as gross rates of change and rewrites them as percent changes.==

    self.pct_from_roc()

The inverse of `roc_from_pct`, and like it the frequency plays no part.


**Input arguments.**


???+ input "self"
    The series whose values are rewritten. There are no other
    arguments.


### Returns


Nothing; the series is modified in place.


### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1), values=np.array([1.1, 1.2]))
    >>> x.pct_from_roc()
    >>> [round(v, 4) for v in x.get_data()[:, 0].tolist()]
    [10.0, 20.0]

································································
        """
        self.data = 100*(self.data - 1)



    @_dm.reference(category="temporal_change_conversion", add_heading=False, )
    def pct_from_apct(
        self,
    ) -> None:
        r"""
································································

## `pct_from_apct`

Called as `x.pct_from_apct(...)` (method form) or
`datapie.pct_from_apct(x, ...)` (function form).

==Reads the values as annualized percent changes and rewrites them as percent changes per period.==

    self.pct_from_apct()

The yearly figure is spread back over the periods in a year, so an
annualized ten percent becomes about 2.41 percent a quarter.


**Input arguments.**


???+ input "self"
    The series whose values are rewritten. There are no other
    arguments.


### Returns


Nothing; the series is modified in place.


### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1), values=np.array([10., 20.]))
    >>> x.pct_from_apct()
    >>> [round(v, 4) for v in x.get_data()[:, 0].tolist()]
    [2.4114, 4.6635]

································································
        """
        factor = self.frequency.value or 1
        self.data = 100*((1 + self.data/100)**(1/factor) - 1)



    @_dm.reference(category="temporal_change_conversion", add_heading=False, )
    def roc_from_apct(
        self,
    ) -> None:
        r"""
································································

## `roc_from_apct`

Called as `x.roc_from_apct(...)` (method form) or
`datapie.roc_from_apct(x, ...)` (function form).

==Reads the values as annualized percent changes and rewrites them as gross rates of change per period.==

    self.roc_from_apct()

Does what `pct_from_apct` does and leaves the result as a ratio rather
than a percentage.


**Input arguments.**


???+ input "self"
    The series whose values are rewritten. There are no other
    arguments.


### Returns


Nothing; the series is modified in place.


### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1), values=np.array([10., 20.]))
    >>> x.roc_from_apct()
    >>> [round(v, 4) for v in x.get_data()[:, 0].tolist()]
    [1.0241, 1.0466]

································································
        """
        factor = self.frequency.value or 1
        self.data = (1 + self.data/100)**(1/factor)



    @_dm.reference(category="temporal_change_conversion", add_heading=False, )
    def roc_from_aroc(
        self,
    ) -> None:
        r"""
································································

## `roc_from_aroc`

Called as `x.roc_from_aroc(...)` (method form) or
`datapie.roc_from_aroc(x, ...)` (function form).

==Raises every value to the power of the number of periods in a year.==

    self.roc_from_aroc()

The name says it converts an annualized gross rate into a per-period
one, but the code raises to the number of periods in a year where its
siblings divide by it, so it annualizes a second time instead. A
quarterly series of `1.1` comes back as `1.4641`, not as the
`1.1**(1/4)` the name implies. Use `roc_from_apct` for the
de-annualizing behaviour.


**Input arguments.**


???+ input "self"
    The series whose values are rewritten. There are no other
    arguments.


### Returns


Nothing; the series is modified in place.


### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1), values=np.array([1.1, 1.2]))
    >>> x.roc_from_aroc()
    >>> [round(v, 4) for v in x.get_data()[:, 0].tolist()]
    [1.4641, 2.0736]

································································
        """
        factor = self.frequency.value or 1
        self.data = self.data**factor



    @_dm.reference(category="temporal_cumulation", add_heading=False, )
    def cum_diff(self, *args, **kwargs, ) -> None:
        r"""
································································

## `cum_diff`

Called as `x.cum_diff(...)` (method form) or
`datapie.cum_diff(x, ...)` (function form).

==Rebuilds a series of levels from a series of first differences.==

    self.cum_diff(shift=-1, initial=None, span=None)

Left alone, `initial` is `0`.


**Input arguments.**


???+ input "shift, initial, span"
    Described in full under the temporal cumulation calculations.


### Returns


Nothing; the series is modified in place.


### Examples


Undoing the matching change calculation:

    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([100., 110., 121., 133.1]))
    >>> x.diff()
    >>> x.cum_diff(initial=100.)
    >>> [round(v, 4) for v in x.get_data()[:, 0].tolist()]
    [100.0, 110.0, 121.0, 133.1]

································································
        """
        self.temporal_cumulation("diff", *args, **kwargs, )



    @_dm.reference(category="temporal_cumulation", add_heading=False, )
    def cum_diff_log(self, *args, **kwargs, ) -> None:
        r"""
································································

## `cum_diff_log`

Called as `x.cum_diff_log(...)` (method form) or
`datapie.cum_diff_log(x, ...)` (function form).

==Rebuilds a series of levels from a series of log differences.==

    self.cum_diff_log(shift=-1, initial=None, span=None)

The default `initial` of `0` cannot be used here: the cumulation
multiplies, so a start of `0` leaves every value `0` and the series
comes back as zeros. Always pass a starting level.


**Input arguments.**


???+ input "shift, initial, span"
    Described in full under the temporal cumulation calculations.


### Returns


Nothing; the series is modified in place.


### Examples


Undoing the matching change calculation:

    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([100., 110., 121., 133.1]))
    >>> x.diff_log()
    >>> x.cum_diff_log(initial=100.)
    >>> [round(v, 4) for v in x.get_data()[:, 0].tolist()]
    [100.0, 110.0, 121.0, 133.1]

································································
        """
        self.temporal_cumulation("diff_log", *args, **kwargs, )



    @_dm.reference(category="temporal_cumulation", add_heading=False, )
    def cum_pct(self, *args, **kwargs, ) -> None:
        r"""
································································

## `cum_pct`

Called as `x.cum_pct(...)` (method form) or
`datapie.cum_pct(x, ...)` (function form).

==Rebuilds a series of levels from a series of percent changes.==

    self.cum_pct(shift=-1, initial=None, span=None)

Left alone, `initial` is `1`, which gives an index rather than a level.


**Input arguments.**


???+ input "shift, initial, span"
    Described in full under the temporal cumulation calculations.


### Returns


Nothing; the series is modified in place.


### Examples


Undoing the matching change calculation:

    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([100., 110., 121., 133.1]))
    >>> x.pct()
    >>> x.cum_pct(initial=100.)
    >>> [round(v, 4) for v in x.get_data()[:, 0].tolist()]
    [100.0, 110.0, 121.0, 133.1]

································································
        """
        self.temporal_cumulation("pct", *args, **kwargs, )



    @_dm.reference(category="temporal_cumulation", add_heading=False, )
    def cum_roc(self, *args, **kwargs, ) -> None:
        r"""
································································

## `cum_roc`

Called as `x.cum_roc(...)` (method form) or
`datapie.cum_roc(x, ...)` (function form).

==Rebuilds a series of levels from a series of gross rates of change.==

    self.cum_roc(shift=-1, initial=None, span=None)

Left alone, `initial` is `1`, which gives an index rather than a level.


**Input arguments.**


???+ input "shift, initial, span"
    Described in full under the temporal cumulation calculations.


### Returns


Nothing; the series is modified in place.


### Examples


Undoing the matching change calculation:

    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([100., 110., 121., 133.1]))
    >>> x.roc()
    >>> x.cum_roc(initial=100.)
    >>> [round(v, 4) for v in x.get_data()[:, 0].tolist()]
    [100.0, 110.0, 121.0, 133.1]

································································
        """
        self.temporal_cumulation("roc", *args, **kwargs, )



    @_dm.reference(
        category=None,
        call_name=CATEGORIES["temporal_cumulation"],
        call_name_is_code=False,
        priority=20,
    )
    def temporal_cumulation(
        self,
        func_name: str,
        shift: int | str = -1,
        initial: Real | Self | None = None,
        span: Span | None = None,
    ) -> None:
        r"""
································································

==Rebuilds a series of levels from a series of changes, undoing what `diff`, `diff_log`, `pct` or `roc` did.==

    self.temporal_cumulation(func_name, shift=-1, initial=None, span=None)

This is the engine under `cum_diff`, `cum_diff_log`, `cum_pct` and
`cum_roc`, and where their shared arguments are decided.

Each period is rebuilt from the one `shift` periods earlier, with $c_t$
the change the series carries at $t$ and $k$ the lag:

| `func_name`  | Description
|--------------|-------------
| `"diff"`     | $y_t = y_{t-k} + c_t$
| `"diff_log"` | $y_t = y_{t-k} \cdot \exp(c_t)$
| `"pct"`      | $y_t = y_{t-k} \cdot (1 + c_t/100)$
| `"roc"`      | $y_t = y_{t-k} \cdot c_t$

Periods with no predecessor inside the span take `initial`.


**Input arguments.**


???+ input "func_name"
    One of `"diff"`, `"diff_log"`, `"pct"` and `"roc"`, saying which
    change the values represent. The four `cum_*` methods each fill it
    in.

???+ input "shift"
    The lag the changes were computed at, `-1` when left alone, with
    the same rules as under the temporal change calculations.

???+ input "initial"
    The level to start from. Left as `None` it is `0` for `"diff"` and
    `"diff_log"` and `1` for `"pct"` and `"roc"`. For `"diff_log"` that
    default is useless: the cumulation multiplies, so a start of `0`
    stays `0` and the whole series comes back as zeros. Pass a real
    starting level there.

???+ input "span"
    The stretch to cumulate over, the whole series when left as `None`.
    Its direction chooses between the forward and the backward routine.


### Returns


Nothing; the series is modified in place. Cumulating gives back the
period that the change calculation trimmed, so the series grows one
period at the front.


### Examples


Differences turned back into levels, starting at 100. Note the start
moving back to 2020-Q1:

    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([100., 110., 121., 133.1]))
    >>> x.diff()
    >>> x.start
    qq(2020,2)
    >>> x.cum_diff(initial=100.)
    >>> x.start
    qq(2020,1)
    >>> [round(v, 4) for v in x.get_data()[:, 0].tolist()]
    [100.0, 110.0, 121.0, 133.1]

································································
        """
        _catch_invalid_shift(shift, )
        span = Span(None, None, ) if span is None else span
        span = span.resolve(self, )
        direction = span.direction
        factory = _CUMULATIVE_FACTORY[func_name]
        cum_func = factory[direction]
        initial = factory["initial"] if initial is None else initial
        #
        if direction == "forward":
            _cumulate_forward(self, shift, cum_func, initial, span, )
        #
        elif direction == "backward":
            _cumulate_backward(self, shift, cum_func, initial, span, )


    #]


#-------------------------------------------------------------------------------
# Functional forms
#-------------------------------------------------------------------------------


_functional_forms = {
    # "temporal_change",
    "diff",
    "adiff",
    "diff_log",
    "adiff_log",
    "pct",
    "apct",
    "roc",
    "aroc",
    # "temporal_change_conversion",
    "roc_from_pct",
    "pct_from_roc",
    "pct_from_apct",
    "roc_from_apct",
    "roc_from_aroc",
    # "temporal_cumulation",
    "cum_diff",
    "cum_diff_log",
    "cum_pct",
    "cum_roc",
}

for n in _functional_forms:
    code = FUNC_STRING.format(n=n, )
    exec(_tw.dedent(code, ), )


__all__ = tuple(_functional_forms)


#-------------------------------------------------------------------------------


def _cumulate_forward(self, shift, cum_func, initial, span, ) -> None:
    """
    """
    zipped_span = tuple((t, t.shift(shift, )) for t in span)
    zipped_span = tuple((t, sh) for t, sh in zipped_span if sh is not None)
    min_period = min((sh for t, sh in zipped_span), default=span.start_date, )
    initial_span = Span(min_period, span.end_date, )
    change = self.copy()
    self.empty()
    self.set_data(initial_span, initial)
    for t, sh in zipped_span:
        new_data = cum_func(self.get_data(sh, ), change.get_data(t, ), )
        self.set_data(t, new_data)


def _cumulate_backward(self, shift, cum_func, initial, shifted_backward_range, ) -> None:
    """
    """
    orig_range_shifted = Span(self.start_date, self.end_date, -1, )
    orig_range_shifted.shift(shift, )
    shifted_backward_range = shifted_backward_range.resolve(orig_range_shifted, )
    backward_range = shifted_backward_range.copy()
    backward_range.shift(-shift, )
    initial_span = Span(min(shifted_backward_range), backward_range.start_date, )
    orig = self.copy()
    self.empty()
    self.set_data(initial_span, initial, )
    for t, sh in zip(backward_range, shifted_backward_range, ):
        new_data = cum_func(self.get_data(t, ), orig.get_data(t, ), )
        self.set_data(sh, new_data, )



_CUMULATIVE_FACTORY = {
    "diff": {
        "forward": lambda x_past, change_curr: x_past + change_curr,
        "backward": lambda x_future, change_future: x_future - change_future,
        "initial": 0,
    },
    "diff_log": {
        "forward": lambda x_past, change_curr: x_past * _np.exp(change_curr),
        "backward": lambda x_future, change_future: x_future / _np.exp(change_future),
        "initial": 0,
    },
    "pct": {
        "forward": lambda x_past, change_curr: x_past * (1 + change_curr/100),
        "backward": lambda x_future, change_future: x_future / (1 + change_future/100),
        "initial": 1,
    },
    "roc": {
        "forward": lambda x_past, change_curr: x_past * change_curr,
        "backward": lambda x_future, change_future: x_future / change_future,
        "initial": 1,
    },
}


def _catch_invalid_shift(shift: int | str, ):
    """
    """
    if not isinstance(shift, str) and (int(shift) != shift or shift >= 0):
        raise ValueError("Time shift must be a negative integer or a string")


def _roc_from_pct(pct: Real, ) -> Real:
    """
    """
    return 1 + pct/100


