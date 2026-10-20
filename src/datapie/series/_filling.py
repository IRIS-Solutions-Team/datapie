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
==Replace missing observations using a chosen rule==

#### Syntax

##### Method form

    x.fill_missing(
        method,
        method_args=None,
        span=None,
    )

##### Function form

    new_series = datapie.fill_missing(
        x,
        method,
        method_args=None,
        span=None,
    )

#### Input arguments

!!! input "method"
    The filling rule. `"next"`, `"previous"` and `"nearest"` copy an available neighbor; a nearest-neighbor tie selects the earlier value. `"linear"` and `"log_linear"` interpolate in values and logarithms, respectively. `"constant"` uses a fixed value. `"from_series"` reads another series; `"series"` is an alias.

!!! input "method_args"
    The fixed value for `"constant"` or the source series for `"from_series"`. Other rules ignore it. The default is `None`, which leaves entries missing when used with `"constant"`.

!!! input "span"
    The periods to fill; the default, `None`, means the current span. The requested span can extend beyond the current data.

#### Method form returns

!!! returns "None"
    The series is changed in place.

#### Function form returns

!!! returns "new_series"
    A new series with the result. The input series is unchanged.

??? note "Details"
    Neighbors and interpolation endpoints are taken only from the requested span. `"next"` and `"previous"` leave missing values where no suitable neighbor exists. Interpolation repeats the nearest endpoint outside the observed interval; it does not extend a slope.

    An entirely missing variant has no neighbors or interpolation endpoints. Log interpolation requires positive endpoints for real-valued results. Missing rows at the ends of the series are removed after assignment.

    For `"from_series"`, a single source variant is supported; source variants are not matched separately to destination variants.
        """
        fill_func = _FILL_METHOD_DISPATCH[method]
        data, span, = self.get_data_and_periods(span, )
        for variant in data.T:
            fill_func(variant, method_args, span=span, )
        self.set_data(span, data, )

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
==Fill missing array entries from another series==

#### Syntax

    values = fill_from_series(
        values,
        method_args,
        span,
    )

#### Input arguments

!!! input "values"
    The one-dimensional array to fill.

!!! input "method_args"
    The source series. Its values over the requested span must match the length of `values`; use a single source variant.

!!! input "span"
    The periods corresponding to the array entries.

#### Returns

!!! returns "values"
    The same array, changed in place. Only missing entries are replaced; missing source values remain missing. The source series is unchanged.

This support function implements the source-series filling rule and is not available directly from `datapie`.

#### See also

[`fill_missing`](#fill_missing)
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


