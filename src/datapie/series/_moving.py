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

    _documark_topic__reference_moving_windows = r"""
documark = {title = "Moving windows", anchor = "moving-windows", priority = 170}

==Calculate sums, averages or products over moving windows==

### Syntax

#### Method form

    series.mov_sum(window=None)
    series.mov_avg(window=None)
    series.mov_mean(window=None)
    series.mov_prod(window=None)

#### Function form

    new_series = datapie.mov_sum(series, window=None)
    new_series = datapie.mov_avg(series, window=None)
    new_series = datapie.mov_mean(series, window=None)
    new_series = datapie.mov_prod(series, window=None)

### Input arguments

!!! input "series"

    The series on which to calculate moving results.

!!! input "window"

    A negative integer window length or None, with default None. A window of -k
    includes the current period and the previous k-1 periods. None uses one year
    at the series frequency: -1 yearly, -2 half-yearly, -4 quarterly, -12
    monthly, -52 weekly or -365 daily. For a non-calendar or unknown frequency
    it uses -4.

### Returns

!!! returns "None — method form"

    No return value. The series is changed in place.

!!! returns "new_series — function form"

    A new Series containing the result. The input series is left unchanged.

The named operations calculate a sum, average (`mov_avg` and `mov_mean`),
or product for each variant separately. A missing observation makes every
window containing it missing. The first `k-1` periods have no complete
window and are missing too. Missing rows at either end are removed; a
window longer than the data can leave an empty series.
    """


    @_dm.reference(category="moving", )
    def moving_window(
        self,
        func: Callable,
        window: int | None = None,
    ) -> None:
        r"""
==Apply a function to trailing observation windows==

#### Syntax

##### Method form

    series.moving_window(
        func,
        window=None,
    )

##### Function form

    new_series = datapie.moving_window(
        series,
        func,
        window=None,
    )

#### Input arguments

!!! input "func"
    A function that reduces each window to a result. It must accept the keyword
    axis.

!!! input "window"
    A negative integer window length or None, with default None. A window of -k
    includes the current period and the previous k-1 periods. None uses one year
    at the series frequency: -1 yearly, -2 half-yearly, -4 quarterly, -12
    monthly, -52 weekly or -365 daily. For a non-calendar or unknown frequency
    it uses -4.

#### Returns

!!! returns "None — method form"
    No return value. The series is changed in place.

!!! returns "new_series — function form"
    A new Series containing the result. The input series is left unchanged.

Missing rows at either end of the result are removed. Whether a missing
observation makes a window missing depends on the supplied function.

#### See also

[Moving windows](#moving-windows).

??? note "Details"

    The function receives an array with periods, variants and window
    positions as its three axes. It is called with `axis=2`.
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


    @_dm.reference(category="moving", )
    def mov_sum(self, window: int | None = None, ) -> None:
        r"""
==Calculate trailing moving sums==

#### See also

[Moving windows](#moving-windows).
        """
        self.moving_window(_np.sum, window=window, )


    @_dm.reference(category="moving", )
    def mov_avg(self, window: int | None = None, ) -> None:
        r"""
==Calculate trailing moving averages==

#### See also

[Moving windows](#moving-windows).
        """
        self.moving_window(_np.mean, window=window, )


    @_dm.reference(category="moving", )
    def mov_mean(self, window: int | None = None, ) -> None:
        r"""
==Calculate trailing moving means==

#### See also

[Moving windows](#moving-windows).
        """
        self.moving_window(_np.mean, window=window, )


    @_dm.reference(category="moving", )
    def mov_prod(self, window: int | None = None, ) -> None:
        r"""
==Calculate trailing moving products==

#### See also

[Moving windows](#moving-windows).
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
    globals()[n].__doc__ = getattr(Mixin, n).__doc__

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

