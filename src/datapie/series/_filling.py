"""
"""


#[

from __future__ import annotations

import functools as _ft
import textwrap as _tw
import numpy as _np
import documark as _dm
from typing import Literal

from ..periods import Period
from ._functionalize import FUNC_STRING

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Any, Callable, EllipsisType
    from collections.abc import Iterable
    from numbers import Real
    from .main import Series

#]


FUNCTIONAL_FORMS = (
    "fill_missing",
)


Method = Literal[
    "next",
    "previous",
    "nearest",
    "linear",
    "log_linear",
    "constant",
    "from_series",
]


#-------------------------------------------------------------------------------
# Mixin methods
#-------------------------------------------------------------------------------


class Mixin:
    #[

    @_dm.reference(category="homogenizing", )
    def fill_missing(
        self,
        method: Method,
        method_args: Any | None = None,
        span: Iterable[Period] | EllipsisType | None = None,
    ) -> None:
        r"""
................................................................................

## `Series.fill_missing`

Called as `x.fill_missing(...)` (method form) or
`datapie.fill_missing(x, ...)` (function form).

==Replaces the missing observations in a time series using a chosen rule.==

    self.fill_missing(
        method,
        method_args=None,
        span=None,
    )

**Input arguments.**


???+ input "method"
    The rule to fill with. Required, and an unknown name raises
    `KeyError`.

    | Method          | Description
    |-----------------|-------------
    | `"next"`        | Copy the next available observation
    | `"previous"`    | Copy the previous available observation
    | `"nearest"`     | Copy the nearest available observation
    | `"linear"`      | Interpolate between the observations on either side
    | `"log_linear"`  | Interpolate between them in logs
    | `"constant"`    | Write a fixed number
    | `"from_series"` | Take the values from another series

    `"series"` is accepted as an older name for `"from_series"`.

???+ input "method_args"
    Whatever the rule needs: the number for `"constant"`, the other
    series for `"from_series"`. Every other rule ignores it. With
    `"constant"` and `method_args` left as `None` the gaps are refilled
    with missing values, so the series comes back unchanged.

???+ input "span"
    The stretch of periods to fill. Left as `None` it is the span the
    series already covers; a wider span lets the filling reach beyond
    the data.


Despite their names, `"linear"` and `"log_linear"` only interpolate.
Past the first and last observation they repeat that end value rather
than continuing the line. Periods that no rule could reach stay
missing, and missing periods at the ends are then trimmed off, so the
series can come back shorter than the `span` asked for -- a variant
missing throughout comes back empty.


### Returns


Nothing; the series is modified in place.


### Examples


A span reaching one period before the data and two after it. The two
interior gaps are interpolated, while the three periods outside the
data take the nearest end value:

    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 2),
    ...     values=np.array([2., np.nan, np.nan, 8.]))
    >>> x.fill_missing("linear", None,
    ...     dp.Span(dp.qq(2020, 1), dp.qq(2021, 3)))
    >>> x.get_data()[:, 0].tolist()
    [2.0, 2.0, 4.0, 6.0, 8.0, 8.0, 8.0]

`"next"` has no later observation to copy after 2021-Q1, so those
periods stay missing and are trimmed:

    >>> x = dp.Series(start=dp.qq(2020, 2),
    ...     values=np.array([2., np.nan, np.nan, 8.]))
    >>> x.fill_missing("next", None,
    ...     dp.Span(dp.qq(2020, 1), dp.qq(2021, 3)))
    >>> x.end
    qq(2021,1)

................................................................................
        """
        fill_func = _FILL_METHOD_DISPATCH[method]
        data, span, = self.get_data_and_periods(span, )
        new_data = [
            fill_func(variant, method_args, span=span, ).T
            for variant in data.T
        ]
        self.set_data(span, new_data, )

    #]


#-------------------------------------------------------------------------------
# Functional forms
#-------------------------------------------------------------------------------


_functional_forms = {"fill_missing", }

for n in _functional_forms:
    code = FUNC_STRING.format(n=n, )
    exec(_tw.dedent(code, ), )

__all__ = tuple(_functional_forms)


#-------------------------------------------------------------------------------


def _fill_neighbor(
    data,
    method_args: Any | None,
    func: Callable,
    **kwargs,
) -> _np.ndarray:
    """
    """
    index_nan = _np.isnan(data)
    if _np.all(index_nan):
        return data
    where_obs = _np.where(~index_nan)[0].astype(_np.float64, )
    if where_obs.size == 0:
        return data
    where_nan = _np.where(index_nan)[0]
    for i in where_nan:
        j = func(i, where_obs, )
        data[i] = data[j] if j is not None else _np.nan
    return data


def _fill_interp(
    data: _np.ndarray,
    method_args: Any | None,
    func: Callable,
    **kwargs,
) -> _np.ndarray:
    """
    """
    index_nan = _np.isnan(data)
    if _np.all(index_nan):
        return data
    where_obs = _np.where(~index_nan)[0].astype(_np.float64, )
    if where_obs.size == 0:
        return data
    where_nan = _np.where(index_nan)[0]
    for i in where_nan:
        prev = _previous_index(i, where_obs, )
        next_ = _next_index(i, where_obs, )
        if prev is not None and next_ is not None:
            data[i] = func(data[prev], data[next_], prev, next_, i, )
            continue
        if prev is not None:
            data[i] = data[prev]
            continue
        if next_ is not None:
            data[i] = data[next_]
            continue
    return data


def _interpolation_linear(
    previous_value: Real,
    next_value: Real,
    previous_index: int,
    next_index: int,
    curr_index: int,
    /,
) -> Real:
    """
    """
    diff = next_value - previous_value
    scale_diff = (curr_index - previous_index) / (next_index - previous_index)
    return previous_value + diff * scale_diff


def _interpolation_log_linear(
    previous_value: Real,
    next_value: Real,
    previous_index: int,
    next_index: int,
    curr_index: int,
    /,
) -> Real:
    """
    """
    return _np.exp(_interpolation_linear(
        _np.log(previous_value),
        _np.log(next_value),
        previous_index,
        next_index,
        curr_index,
    ))


def _fill_constant(
    data: _np.ndarray,
    method_args: Real,
    **kwargs,
) -> _np.ndarray:
    """
    """
    constant = method_args
    index_nan = _np.isnan(data)
    data[index_nan] = constant
    return data


def fill_from_series(
    values: _np.ndarray,
    method_args: Series,
    span: Iterable[Period],
) -> _np.ndarray:
    r"""
................................................................................

## `fill_from_series`

==Fills the missing entries of an array with the observations another time series holds over the same span, and returns the array.==

    values = fill_from_series(values, method_args, span)

This is what backs the `"from_series"` rule of `fill_missing`, and is
not meant to be called on its own.


**Input arguments.**


???+ input "values"
    The array whose missing entries are to be filled. It is modified in
    place as well as returned.

???+ input "method_args"
    The time `Series` to take the replacement values from. Periods that
    series does not cover stay missing.

???+ input "span"
    The periods the `values` array corresponds to, used to read the
    matching stretch out of `method_args`.


### Returns


The same array, with its missing entries filled where `method_args`
had an observation.

................................................................................
    """
    series = method_args
    fill_values = series.get_data(span, )
    index_nan = _np.isnan(values)
    values[index_nan] = fill_values.flatten()[index_nan]
    return values


def _next_index(i: int, where_obs: _np.ndarray, /, ) -> int:
    """
    """
    #[
    where_obs_minus_i = where_obs - i
    index_negative = where_obs_minus_i < 0
    if _np.all(index_negative):
        return None
    where_obs_minus_i[index_negative] = _np.inf
    index = _np.argmin(where_obs_minus_i)
    return int(where_obs[index])
    #]


def _previous_index(i: int, where_obs: _np.ndarray, /, ) -> int:
    """
    """
    #[
    i_minus_where_obs = i - where_obs
    index_negative = i_minus_where_obs < 0
    if _np.all(index_negative):
        return None
    i_minus_where_obs[index_negative] = _np.inf
    index = _np.argmin(i_minus_where_obs)
    return int(where_obs[index])
    #]


def _nearest_index(i: int, where_obs: _np.ndarray, /, ) -> int:
    """
    """
    #[
    i_minus_where_obs = _np.abs(i - where_obs)
    index = _np.argmin(i_minus_where_obs)
    return int(where_obs[index])
    #]


_FILL_METHOD_DISPATCH = {
    "next": _ft.partial(_fill_neighbor, func=_next_index, ),
    "previous": _ft.partial(_fill_neighbor, func=_previous_index, ),
    "nearest": _ft.partial(_fill_neighbor, func=_nearest_index, ),
    "linear": _ft.partial(_fill_interp, func=_interpolation_linear, ),
    "log_linear": _ft.partial(_fill_interp, func=_interpolation_log_linear, ),
    "constant": _fill_constant,
    "from_series": fill_from_series,
    #
    # Aliases for backward compatibility
    "series": fill_from_series,
}


