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
    ················································································


    Overview of moving window functions:

    | Function | Description
    |----------|-------------
    | `mov_sum` | Moving sum, $y_t = \sum_{i=0}^{k-1} x_{t-i}$
    | `mov_avg` | Moving average, $y_t = \frac{1}{k} \sum_{i=0}^{k-1} x_{t-i}$
    | `mov_mean` | Same as `mov_avg`
    | `mov_prod` | Moving product, $y_t = \prod_{i=0}^{k-1} x_{t-i}$

    where

    * $k$ is the window length determined by the `window` input argument
    (note that $k$ above is a positive integer while `window` needs to be
    entered as a negative integer).



    ### Function for creating new Series objects ###

    ```
    new = irispie.mov_sum(self, window=None, )
    new = irispie.mov_avg(self, window=None, )
    new = irispie.mov_mean(self, window=None, )
    new = irispie.mov_prod(self, window=None, )
    ```


    ### Methods for changing existing Series objects in-place ###


    ```
    self.mov_sum(window=None, )
    self.mov_avg(window=None, )
    self.mov_mean(window=None, )
    self.mov_prod(window=None, )
    ```


    ### Input arguments ###


    ???+ input "self"
    Time series on whose data a moving function is calculated (see the
    overview table above).

    ???+ input "window"
    A negative interger determining the number of observations to include
    in the moving window, counting from the current time period backwards
    (the minus sign is a convention to indicate that the window goes
    backwards in time). If `window=None` (or not specified), the default
    window is derived from the time series frequency:

    | Date frequency | Default window |
    |----------------|---------------:|
    | `YEARLY`       |             –1 |
    | `QUARTERLY`    |             –4 |
    | `MONTHLY`      |            –12 |
    | `WEEKLY`       |            –52 |
    | `DAILY`        |           –365 |
    | Otherwise      |             –4 |

    Note that the default windows for `DAILY` and `WEEKLY` frequencies are
    fixed numbers and do not depend on the actual number of days in a
    calendar year or the actual number of weeks in a calendar year.


    ### Returns ###


    ???+ returns "new"
    New time series with data calculated as a moving window function of the
    original data.

    ???+ returns "self"
    Time series with data replaced by the moving window function of the
    original data.

    ················································································
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

    # ==========================================================================
    #  ### `moving_window(func, window=None)`
    #
    #  Replaces every observation with the result of applying `func` to the
    #  window of observations ending at that period.
    #
    #  This is the engine under `mov_sum`, `mov_avg`, `mov_mean` and
    #  `mov_prod`, and it accepts any function of your own that reduces an
    #  array along an axis.
    #
    #  **Parameters.** `func` is applied to the stacked windows with
    #  `axis=2`, so it has to accept an `axis` keyword. The `numpy`
    #  reductions do; a plain function of one argument does not, and raises
    #  `TypeError`.
    #
    #  `window` is how many observations go into the window, written as a
    #  negative integer because the window reaches backwards from the
    #  current period. Left as `None` it is minus the number of periods a
    #  year holds at the frequency of the series: -1 yearly, -2 half-yearly,
    #  -4 quarterly, -12 monthly, -52 weekly, -365 daily, with integer and
    #  unknown frequencies falling back to -4. Zero or a positive number
    #  raises `ValueError: index can't contain negative values`, a message
    #  that points at the opposite of the mistake.
    #
    #  **Returns.** Nothing; the series is modified in place.
    #
    #  The first periods have no full window behind them, so they come back
    #  missing and are then trimmed away: a window of `-k` costs `k-1`
    #  periods off the front and moves the start later. A missing
    #  observation anywhere in the data does the same locally, since every
    #  window touching it comes out missing.
    #
    #  **Examples.** Eight quarters in, five out, starting three quarters
    #  later than the input:
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(start=dp.qq(2020, 1),
    #      ...     values=np.array([1., 2., 3., 4., 5., 6., 7., 8.]))
    #      >>> x.moving_window(np.sum, window=-4)
    #      >>> x.start
    #      qq(2020,4)
    #      >>> x.get_data()[:, 0].tolist()
    #      [10.0, 14.0, 18.0, 22.0, 26.0]
    #
    # ==========================================================================

    @_dm.reference(category="moving", )
    def mov_sum(self, window: int | None = None, ) -> None:
        r"""
    ................................................................................

    ==Moving sum==


    See documentation of [moving window calculations](#moving-window-calculations) or
    `help(irispie.Series.moving_window)`.

    ................................................................................
        """
        self.moving_window(_np.sum, window=window, )

    # ==========================================================================
    #  ### `mov_sum(window=None)`
    #
    #  Replaces every observation with the sum over the window ending at
    #  that period.
    #
    #  **Parameters.** `window` behaves exactly as described under
    #  `moving_window`, defaults included.
    #
    #  **Returns.** Nothing; the series is modified in place. The periods
    #  lost off the front are described under `moving_window`.
    #
    #  **Examples.**
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(start=dp.qq(2020, 1),
    #      ...     values=np.array([1., 2., 3., 4., 5., 6., 7., 8.]))
    #      >>> x.mov_sum()
    #      >>> x.get_data()[:, 0].tolist()
    #      [10.0, 14.0, 18.0, 22.0, 26.0]
    #
    # ==========================================================================

    @_dm.reference(category="moving", )
    def mov_avg(self, window: int | None = None, ) -> None:
        r"""
    ................................................................................

    ==Moving average==


    See documentation of [moving window calculations](#moving-window-calculations) or
    `help(irispie.Series.moving_window)`.

    ................................................................................
        """
        self.moving_window(_np.mean, window=window, )

    # ==========================================================================
    #  ### `mov_avg(window=None)`
    #
    #  Replaces every observation with the average over the window ending
    #  at that period. `mov_mean` is another name for this method.
    #
    #  **Parameters.** `window` behaves exactly as described under
    #  `moving_window`, defaults included.
    #
    #  **Returns.** Nothing; the series is modified in place. The periods
    #  lost off the front are described under `moving_window`.
    #
    #  **Examples.**
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(start=dp.qq(2020, 1),
    #      ...     values=np.array([1., 2., 3., 4., 5., 6., 7., 8.]))
    #      >>> x.mov_avg()
    #      >>> x.get_data()[:, 0].tolist()
    #      [2.5, 3.5, 4.5, 5.5, 6.5]
    #
    # ==========================================================================

    @_dm.reference(category="moving", )
    def mov_mean(self, window: int | None = None, ) -> None:
        r"""
    ................................................................................

    ==Moving average==


    See documentation of [moving window calculations](#moving-window-calculations) or
    `help(irispie.Series.moving_window)`.

    ................................................................................
        """
        self.moving_window(_np.mean, window=window, )

    # ==========================================================================
    #  ### `mov_mean(window=None)`
    #
    #  Replaces every observation with the average over the window ending
    #  at that period.
    #
    #  Another name for `mov_avg`. The two call the same function with the
    #  same arguments, so pick whichever reads better.
    #
    #  **Parameters.** `window` behaves exactly as described under
    #  `moving_window`, defaults included.
    #
    #  **Returns.** Nothing; the series is modified in place. The periods
    #  lost off the front are described under moving_window.
    #
    #  **Examples.**
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(start=dp.qq(2020, 1),
    #      ...     values=np.array([1., 2., 3., 4., 5., 6., 7., 8.]))
    #      >>> x.mov_mean()
    #      >>> x.get_data()[:, 0].tolist()
    #      [2.5, 3.5, 4.5, 5.5, 6.5]
    #
    # ==========================================================================

    @_dm.reference(category="moving", )
    def mov_prod(self, window: int | None = None, ) -> None:
        r"""
................................................................................

==Moving product==


See documentation of [moving window calculations](#moving-window-calculations) or
`help(irispie.Series.moving_window)`.

................................................................................
        """
        self.moving_window(_np.prod, window=window, )

    # ==========================================================================
    #  ### `mov_prod(window=None)`
    #
    #  Replaces every observation with the product over the window ending
    #  at that period.
    #
    #  **Parameters.** `window` behaves exactly as described under
    #  `moving_window`, defaults included.
    #
    #  **Returns.** Nothing; the series is modified in place. The periods
    #  lost off the front are described under `moving_window`.
    #
    #  **Examples.**
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(start=dp.qq(2020, 1),
    #      ...     values=np.array([1., 2., 3., 4., 5., 6., 7., 8.]))
    #      >>> x.mov_prod()
    #      >>> x.get_data()[:, 0].tolist()
    #      [24.0, 120.0, 360.0, 840.0, 1680.0]
    #
    # ==========================================================================


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

