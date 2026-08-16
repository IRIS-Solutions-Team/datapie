"""
Time series mixin for moving sum, average, product
"""


#[

from __future__ import annotations

from collections.abc import Iterable
from typing import Callable
import numpy as _np
import textwrap as _tw
import documark as _dm

from ._functionalize import FUNC_STRING

#]


#-------------------------------------------------------------------------------
# Mixin methods
#-------------------------------------------------------------------------------


class Mixin:
    #[

    @_dm.reference(
        category=None,
        call_name="Moving window calculations",
        call_name_is_code=False,
        priority=20,
    )
    def moving_window(
        self,
        func: Callable,
        window: int | None = None,
    ) -> None:
        r"""
································································

==Replaces every observation with the result of applying `func` to the window of observations ending at that period.==

    self.moving_window(func, window=None)

This is the engine under `mov_sum`, `mov_avg`, `mov_mean` and
`mov_prod`, and it accepts any function of your own that reduces an
array along an axis. The four named wrappers each supply `func`
themselves and take only `window`:

| Function | Description
|----------|-------------
| `mov_sum` | Moving sum, $y_t = \sum_{i=0}^{k-1} x_{t-i}$
| `mov_avg` | Moving average, $y_t = \frac{1}{k} \sum_{i=0}^{k-1} x_{t-i}$
| `mov_mean` | Same as `mov_avg`
| `mov_prod` | Moving product, $y_t = \prod_{i=0}^{k-1} x_{t-i}$

where $k$ is the window length determined by the `window` input
argument -- note that $k$ here is a positive integer while `window` has
to be entered as a negative one.


**Input arguments.**


???+ input "func"
    Applied to the stacked windows with `axis=2`, so it has to accept
    an `axis` keyword. The `numpy` reductions do; a plain function of
    one argument does not, and raises `TypeError: <lambda>() got an
    unexpected keyword argument 'axis'`. Only `moving_window` takes
    this argument; the four named methods supply it themselves.

???+ input "window"
    How many observations go into the window, written as a negative
    integer because the window reaches backwards from the current
    period, which is itself counted. Left as `None` it is minus the
    number of periods a year holds at the frequency of the series:

    | Date frequency | Default `window` |
    |----------------|-----------------:|
    | `YEARLY`       |               -1 |
    | `HALFYEARLY`   |               -2 |
    | `QUARTERLY`    |               -4 |
    | `MONTHLY`      |              -12 |
    | `WEEKLY`       |              -52 |
    | `DAILY`        |             -365 |
    | Otherwise      |               -4 |

    The `DAILY` and `WEEKLY` defaults are fixed numbers and do not
    depend on the actual number of days or weeks in a calendar year.

    Zero or a positive number raises `ValueError: index can't contain
    negative values`, a message that names the opposite of the mistake.


The first periods have no full window behind them, so they come back
missing and are then trimmed away: a window of `-k` costs `k-1` periods
off the front and moves the start later. A missing observation anywhere
in the data does the same locally, since every window touching it comes
out missing too.


### Returns


Nothing; the series is modified in place.


### Examples


Eight quarters in, five out, starting three quarters later than the
input:

    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2., 3., 4., 5., 6., 7., 8.]))
    >>> x.moving_window(np.sum, window=-4)
    >>> x.start
    qq(2020,4)
    >>> x.get_data()[:, 0].tolist()
    [10.0, 14.0, 18.0, 22.0, 26.0]

································································
        """
        window = (
            window if window is not None
            else _get_default_moving_window(self, )
        )
        window_length = -window
        data = _np.pad(
            self.data,
            pad_width=((window_length-1, 0), (0, 0)),
            mode="constant",
            constant_values=_np.nan,
        )
        data_windows =_np.lib.stride_tricks.sliding_window_view(
            data,
            window_shape=window_length,
            axis=0,
        )
        new_data = func(data_windows, axis=2, )
        self._replace_data(new_data, )


    @_dm.reference(category="moving", add_heading=False, )
    def mov_sum(self, window: int | None = None, ) -> None:
        r"""
································································

## `mov_sum`

==Replaces every observation with the sum over the window ending at that period.==

    self.mov_sum(window=None)


**Input arguments.**


???+ input "window"
    Behaves exactly as described under the moving window
    calculations, defaults included.


### Returns


Nothing; the series is modified in place.


### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2., 3., 4., 5., 6., 7., 8.]))
    >>> x.mov_sum()
    >>> x.get_data()[:, 0].tolist()
    [10.0, 14.0, 18.0, 22.0, 26.0]

································································
        """
        self.moving_window(_np.sum, window=window, )


    @_dm.reference(category="moving", add_heading=False, )
    def mov_avg(self, window: int | None = None, ) -> None:
        r"""
································································

## `mov_avg`

==Replaces every observation with the average over the window ending at that period.==

    self.mov_avg(window=None)

`mov_mean` is another name for this method.


**Input arguments.**


???+ input "window"
    Behaves exactly as described under the moving window
    calculations, defaults included.


### Returns


Nothing; the series is modified in place.


### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2., 3., 4., 5., 6., 7., 8.]))
    >>> x.mov_avg()
    >>> x.get_data()[:, 0].tolist()
    [2.5, 3.5, 4.5, 5.5, 6.5]

································································
        """
        self.moving_window(_np.mean, window=window, )


    @_dm.reference(category="moving", add_heading=False, )
    def mov_mean(self, window: int | None = None, ) -> None:
        r"""
································································

## `mov_mean`

==Replaces every observation with the average over the window ending at that period.==

    self.mov_mean(window=None)

Another name for `mov_avg`; the two are identical.


**Input arguments.**


???+ input "window"
    Behaves exactly as described under the moving window
    calculations, defaults included.


### Returns


Nothing; the series is modified in place.


### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2., 3., 4., 5., 6., 7., 8.]))
    >>> x.mov_mean()
    >>> x.get_data()[:, 0].tolist()
    [2.5, 3.5, 4.5, 5.5, 6.5]

································································
        """
        self.moving_window(_np.mean, window=window, )


    @_dm.reference(category="moving", add_heading=False, )
    def mov_prod(self, window: int | None = None, ) -> None:
        r"""
································································

## `mov_prod`

==Replaces every observation with the product over the window ending at that period.==

    self.mov_prod(window=None)


**Input arguments.**


???+ input "window"
    Behaves exactly as described under the moving window
    calculations, defaults included.


### Returns


Nothing; the series is modified in place.


### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2., 3., 4., 5., 6., 7., 8.]))
    >>> x.mov_prod()
    >>> x.get_data()[:, 0].tolist()
    [24.0, 120.0, 360.0, 840.0, 1680.0]

································································
        """
        self.moving_window(_np.prod, window=window, )



    #]


#-------------------------------------------------------------------------------
# Functional forms
#-------------------------------------------------------------------------------


_functional_forms = {
    "moving_window",
    "mov_sum",
    "mov_avg",
    "mov_mean",
    "mov_prod",
}

for n in _functional_forms:
    code = FUNC_STRING.format(n=n, )
    exec(_tw.dedent(code, ), globals(), )

__all__ = tuple(_functional_forms)


#-------------------------------------------------------------------------------


def _get_default_moving_window(self, ) -> int:
    r"""
    Derive default moving window from time series frequency
    """
    return (
        -self.frequency.value
        if self.frequency is not None and self.frequency.value > 0
        else -4
    )

