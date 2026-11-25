r"""
"""


#[

from __future__ import annotations

from typing import Literal
import functools as _ft
import numpy as _np
import daqp as _qp
import ctypes as _ct
import documark as _dm

from ..periods import Period
from ._functionalize import FUNC_STRING

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable
    from numbers import Real
    from typing import Any, Callable, Self

#]


OrderType = Literal[1, 2]


class Mixin:
    #[


    @_dm.reference(category="filtering", call_name="lonf", anchor="lonf", )
    def lonf(self, ):
        r"""
==Return the L1-filter trend and gap==

#### Syntax

    trend, gap = datapie.lonf(
        series,
        order,
        smooth,
        span=None,
    )

#### Input arguments

!!! input "series"

    The series to filter.

!!! input "order"

    Required difference order: `1` favors flat trend segments; `2` favors
    straight sloping segments. Other orders are not supported.

!!! input "smooth"

    Required smoothing strength. Larger values put more weight on a smooth
    trend. Use a nonnegative real value; it bounds the dual optimization problem.

!!! input "span"

    Periods to filter; `None` (default) selects the current span. Supply a
    nonempty, consecutive, increasing span within the available data, with more
    periods than `order`. Filtering uses its first and last periods as endpoints.

#### Returns

!!! returns "trend"

    A new Series containing the estimated trend. The input is unchanged.

!!! returns "gap"

    A new Series containing input minus trend. The input is unchanged.

The filter penalizes first or second differences using their L1 norm, favoring
piecewise-flat or piecewise-linear trends. The gap is input minus trend. Results
replace the original span with the requested span; missing rows at the ends are
removed. Missing observations are not filled and can make the solver result unusable.

The current output construction retains only the first input variant. Filter a
single-variant series when this distinction matters. `order`, `smooth`, and `span`
can be passed positionally or by keyword.

There is no pair-returning method: `series.lonf()` raises `NotImplementedError`.
Use the component methods to retain one component in place.

#### See also

[`lonf_trend`](#lonf_trend), [`lonf_gap`](#lonf_gap)
        """
        raise NotImplementedError

    @_dm.reference(category="filtering", )
    def lonf_trend(self, *args, **kwargs):
        r"""
==Replace the series with the L1-filter trend==

#### Syntax

    series.lonf_trend(
        order,
        smooth,
        span=None,
    )
    result = datapie.lonf_trend(
        series,
        order,
        smooth,
        span=None,
    )

#### Input arguments

!!! input "series"

    The series to filter.

!!! input "order"

    Required difference order: `1` favors flat trend segments; `2` favors
    straight sloping segments. Other orders are not supported.

!!! input "smooth"

    Required smoothing strength. Larger values put more weight on a smooth
    trend. Use a nonnegative real value; it bounds the dual optimization problem.

!!! input "span"

    Periods to filter; `None` (default) selects the current span. Supply a
    nonempty, consecutive, increasing span within the available data, with more
    periods than `order`. Filtering uses its first and last periods as endpoints.

#### Returns

!!! returns "None — method form"

    The method replaces the series with the L1-filter trend in place.

!!! returns "result — function form"

    The function returns a new series containing the L1-filter trend; the input is unchanged.

The filter penalizes first or second differences using their L1 norm, favoring
piecewise-flat or piecewise-linear trends. The gap is input minus trend. Results
replace the original span with the requested span; missing rows at the ends are
removed. Missing observations are not filled and can make the solver result unusable.

The current output construction retains only the first input variant. Filter a
single-variant series when this distinction matters. `order`, `smooth`, and `span`
can be passed positionally or by keyword.

#### See also

[`lonf`](#lonf), [`lonf_gap`](#lonf_gap)
        """
        trend, _ = lonf(self, *args, **kwargs, )
        self._replace_start_and_values(trend.start, trend.data, )

    @_dm.reference(category="filtering", )
    def lonf_gap(self, *args, **kwargs):
        r"""
==Replace the series with the L1-filter gap==

#### Syntax

    series.lonf_gap(
        order,
        smooth,
        span=None,
    )
    result = datapie.lonf_gap(
        series,
        order,
        smooth,
        span=None,
    )

#### Input arguments

!!! input "series"

    The series to filter.

!!! input "order"

    Required difference order: `1` favors flat trend segments; `2` favors
    straight sloping segments. Other orders are not supported.

!!! input "smooth"

    Required smoothing strength. Larger values put more weight on a smooth
    trend. Use a nonnegative real value; it bounds the dual optimization problem.

!!! input "span"

    Periods to filter; `None` (default) selects the current span. Supply a
    nonempty, consecutive, increasing span within the available data, with more
    periods than `order`. Filtering uses its first and last periods as endpoints.

#### Returns

!!! returns "None — method form"

    The method replaces the series with the L1-filter gap in place.

!!! returns "result — function form"

    The function returns a new series containing the L1-filter gap; the input is unchanged.

The filter penalizes first or second differences using their L1 norm, favoring
piecewise-flat or piecewise-linear trends. The gap is input minus trend. Results
replace the original span with the requested span; missing rows at the ends are
removed. Missing observations are not filled and can make the solver result unusable.

The current output construction retains only the first input variant. Filter a
single-variant series when this distinction matters. `order`, `smooth`, and `span`
can be passed positionally or by keyword.

#### See also

[`lonf`](#lonf), [`lonf_trend`](#lonf_trend)
        """
        _, gap = lonf(self, *args, **kwargs, )
        self._replace_start_and_values(gap.start, gap.data, )

    #]



@_dm.reference(category="filtering", )
def lonf(
    input_series,
    order: OrderType,
    smooth: Real,
    #
    span: Iterable[Period] | None = None,
) -> tuple[Self, Self]:
    r"""
==Return the L1-filter trend and gap==

#### Syntax

    trend, gap = datapie.lonf(
        series,
        order,
        smooth,
        span=None,
    )

#### Input arguments

!!! input "series"

    The series to filter.

!!! input "order"

    Required difference order: `1` favors flat trend segments; `2` favors
    straight sloping segments. Other orders are not supported.

!!! input "smooth"

    Required smoothing strength. Larger values put more weight on a smooth
    trend. Use a nonnegative real value; it bounds the dual optimization problem.

!!! input "span"

    Periods to filter; `None` (default) selects the current span. Supply a
    nonempty, consecutive, increasing span within the available data, with more
    periods than `order`. Filtering uses its first and last periods as endpoints.

#### Returns

!!! returns "trend"

    A new Series containing the estimated trend. The input is unchanged.

!!! returns "gap"

    A new Series containing input minus trend. The input is unchanged.

The filter penalizes first or second differences using their L1 norm, favoring
piecewise-flat or piecewise-linear trends. The gap is input minus trend. Results
replace the original span with the requested span; missing rows at the ends are
removed. Missing observations are not filled and can make the solver result unusable.

The current output construction retains only the first input variant. Filter a
single-variant series when this distinction matters. `order`, `smooth`, and `span`
can be passed positionally or by keyword.

There is no pair-returning method: `series.lonf()` raises `NotImplementedError`.
Use the component methods to retain one component in place.

#### See also

[`lonf_trend`](#lonf_trend), [`lonf_gap`](#lonf_gap)
    """
    from .main import Series

    # Resolve periods
    periods = input_series.resolve_periods(span, )
    start_period = periods[0]
    end_period = periods[-1]
    from_until = (start_period, end_period, )
    num_periods = len(periods)

    # Set up solver function
    matrix_setup_func = _MATRIX_SETUP_DISPATCH[order]
    d, D, = matrix_setup_func(num_periods, )
    H = D @ D.T;
    A = _np.eye(num_periods-order, dtype=_ct.c_double, )
    bounds = _np.full((num_periods-order, ), smooth, dtype=_ct.c_double, );
    sense = _np.full((num_periods-order, ), 0, dtype=_ct.c_int, )
    solve = _ft.partial(_qp.solve, H=H, A=A, bupper=bounds, blower=-bounds, sense=sense, )

    # Iterate over data variants and solve the QP problem
    trend_data_variants = []
    gap_data_variants = []
    for data in input_series.iter_own_data_variants_from_until(from_until, ):
        trend_data, gap_data = _lonf_for_variant(solve, data, D, )
        trend_data_variants.append(trend_data, )
        gap_data_variants.append(gap_data, )

    # Create output series
    trend_series = Series(start=start_period, values=trend_data_variants, )
    gap_series = Series(start=start_period, values=gap_data_variants, )

    return trend_series, gap_series,

_functional_forms = {"lonf", }

for n in ("lonf_trend", "lonf_gap", ):
    exec(FUNC_STRING.format(n=n, ), globals(), locals(), )
    globals()[n].__doc__ = getattr(Mixin, n).__doc__
    _functional_forms.add(n, )

__all__ = tuple(_functional_forms)


def _lonf_for_variant(
    solve: Callable,
    data: _np.ndarray,
    D: _np.ndarray,
) -> tuple[tuple[Real, ...], tuple[Real, ...]]:
    r"""
    """
    data = _np.array(data, dtype=_ct.c_double, ).reshape(-1)
    f = -D @ data;
    x, *_ = solve(f=f, )
    gap_data = D.T @ x;
    trend_data = data - gap_data;
    trend_data = tuple(trend_data.flatten().tolist())
    gap_data = tuple(gap_data.flatten().tolist())
    return trend_data, gap_data,


def _first_order_matrix_setup(
    num_periods: int,
) -> tuple[_np.ndarray, _np.ndarray]:
    r"""
    """
    order = 1
    d = _np.eye(num_periods-order, num_periods, dtype=_ct.c_double, )
    D = _np.eye(num_periods-order, num_periods, dtype=_ct.c_double, )
    D[:, 1:] = D[:, 1:] - d[:, :-1];
    return d, D,


def _second_order_matrix_setup(
    num_periods: int,
) -> tuple[_np.ndarray, _np.ndarray]:
    r"""
    """
    order = 2
    d = _np.eye(num_periods-order, num_periods, dtype=_ct.c_double, )
    D = _np.eye(num_periods-order, num_periods, dtype=_ct.c_double, )
    D[:, 1:] = D[:, 1:] - 2 * d[:, :-1] 
    D[:, 2:] = D[:, 2:] + d[:, :-2]
    return d, D,


_MATRIX_SETUP_DISPATCH = {
    1: _first_order_matrix_setup,
    2: _second_order_matrix_setup,
}


FUNCTIONAL_FORMS = ("lonf", "lonf_trend", "lonf_gap", )

