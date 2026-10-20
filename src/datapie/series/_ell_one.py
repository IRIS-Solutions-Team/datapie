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

    @staticmethod
    @_dm.topic(title="L1 filter forms", anchor="l1-filter-forms", priority=110)
    def _lonf_reference():
        r"""
==Separate a series into a piecewise-smooth trend and a gap==

### Syntax

#### Method form

    series.lonf_trend(order, smooth, span=None)
    series.lonf_gap(order, smooth, span=None)

#### Function form

    trend, gap = datapie.lonf(series, order, smooth, span=None)
    new_series = datapie.lonf_trend(series, order, smooth, span=None)
    new_series = datapie.lonf_gap(series, order, smooth, span=None)

### Input arguments

!!! input "series"

    The series to filter. Function forms leave it unchanged.

!!! input "order"

    The difference order to smooth: `1` favors flat segments and `2` favors straight sloping segments. Required.

!!! input "smooth"

    The strength of smoothing. Larger values put more weight on a smooth trend. Required.

!!! input "span"

    The periods to filter; the default, `None`, means the current span. Supply a nonempty, consecutive span within the available data.

### Method form returns

!!! returns "None"

    `lonf_trend` replaces the series with its trend; `lonf_gap` replaces it with the difference between the input and trend. Calling `series.lonf()` itself raises `NotImplementedError`; use the function form to obtain both components.

### Function form returns

!!! returns "trend, gap"

    `datapie.lonf` returns two new series containing the trend and gap. The input is unchanged.

!!! returns "new_series"

    `datapie.lonf_trend` and `datapie.lonf_gap` return a new series containing the requested component. The input is unchanged.

Only the first input variant is retained in the output. Missing observations are not filled before filtering and may produce missing or unusable results.

??? note "Details"

    The filter uses an L1 penalty on first or second differences, which favors a
    trend built from a small number of flat or straight segments. Results cover
    the requested span, with missing rows at the ends removed.
    """
        pass

    @_dm.reference(category="filtering", )
    def lonf(self, ):
        r"""
==Reserve the in-place trend-gap entry point==

Calling `series.lonf()` is not supported. Use `datapie.lonf` to obtain
both components, or `lonf_trend` and `lonf_gap` to keep one component
in place.

### See also

[L1 filter forms](#l1-filter-forms)
        """
        raise NotImplementedError

    @_dm.reference(category="filtering", )
    def lonf_trend(self, *args, **kwargs):
        r"""
==Replace the series with its L1-filter trend==

#### See also

[L1 filter forms](#l1-filter-forms)
        """
        trend, _ = lonf(self, *args, **kwargs, )
        self._replace_start_and_values(trend.start, trend.data, )

    @_dm.reference(category="filtering", )
    def lonf_gap(self, *args, **kwargs):
        r"""
==Replace the series with its L1-filter gap==

#### See also

[L1 filter forms](#l1-filter-forms)
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

#### See also

[L1 filter forms](#l1-filter-forms) for input arguments, component methods and function forms.
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

