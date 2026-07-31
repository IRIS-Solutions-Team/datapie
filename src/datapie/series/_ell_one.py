r"""
"""


#[

from __future__ import annotations

from typing import Literal
import functools as _ft
import numpy as _np
import daqp as _qp
import ctypes as _ct

from ..periods import Period
from .main import Series

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable
    from numbers import Real
    from typing import Any, Callable, Self

#]


OrderType = Literal[1, 2]


def lonf(
    input_series,
    order: OrderType,
    smooth: Real,
    #
    span: Iterable[Period] | None = None,
) -> tuple[Self, Self]:
    r"""
................................................................................

==L1-norm filter==

................................................................................
    """

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

# ==========================================================================
#  ### `lonf(input_series, order, smooth, span=None)`
#
#  Splits a time series into a smooth trend and the gap around it, and
#  returns the two as new series.
#
#  This is an L1-norm relative of the Hodrick-Prescott filter: the trend
#  comes out as straight segments joined at a few breaks rather than a
#  curve that bends everywhere.
#
#  **Parameters.** `input_series` is read and never modified. `order` must
#  be `1` or `2` and has no default; any other value raises `KeyError`.
#  `smooth` has no default either, and the larger it is, the smoother the
#  trend and the more of the movement goes into the gap. `span` is the
#  stretch of periods to filter, and left as `None` it is the whole span
#  the series covers; it has to lie inside the observed data.
#
#  **Returns.** A pair, `(trend_series, gap_series)`, both new `Series`
#  starting at the first period of the resolved span, which added back
#  together reproduce the input over that span.
#
#  Two things happen quietly. A single missing observation anywhere in the
#  span turns the whole result into an empty series rather than an error.
#  Only the first variant is filtered, and any others are dropped.
#
#  **Examples.** Trend and gap add back up to the data they came from:
#
#      >>> import numpy as np
#      >>> import datapie as dp
#      >>> x = dp.Series(start=dp.qq(2020, 1),
#      ...     values=np.array(
#      ...         [1., 3., 2., 5., 4., 7., 6., 9., 8., 11., 10., 13.]))
#      >>> trend, gap = dp.lonf(x, 1, 1.0)
#      >>> np.allclose(trend.get_data() + gap.get_data(), x.get_data())
#      True
#
#  One missing observation empties the result:
#
#      >>> x = dp.Series(start=dp.qq(2020, 1),
#      ...     values=np.array([1., 3., np.nan, 5., 4., 7.]))
#      >>> trend, gap = dp.lonf(x, 1, 1.0)
#      >>> trend.num_periods
#      0
#
# ==========================================================================

_functional_forms = {"lonf", }
__all__ = tuple(_functional_forms)


def _lonf_for_variant(
    solve: Callable,
    data: _np.ndarray,
    D: _np.ndarray,
) -> tuple[tuple[Real, ...], tuple[Real, ...]]:
    r"""
    """
    data = data.flatten()
    data.dtype = _ct.c_double
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


FUNCTIONAL_FORMS = ("lonf", )

