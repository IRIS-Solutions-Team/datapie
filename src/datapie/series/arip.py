"""
"""


#[

from __future__ import annotations

from typing import (Self, Iterable, Literal, )
from numbers import (Real, )
import functools as _ft
import numpy as _np

from ..periods import Period
from .. import wrongdoings as _wrongdoings
from . import _conversions as _conversions

#]


FormType = Literal["rate", "multiplicative", "diff", "additive", ]
AggregationType = Literal["sum", "mean", "avg", "last", "first", ]


def disaggregate_arip(
    self,
    target_period_class: Period,
    model: tuple[FormType, AggregationType],
    target: Self | None = None,
    # indicator: _np.ndarray | None = None,
) -> Self:
    """Autoregressive interpolation"""
    #[
    if not self.start_date:
        return None, None

    low_start_date = self.start_date
    low_end_date = self.end_date
    low_data_variant_iterator \
        = self.iter_own_data_variants_from_until((low_start_date, low_end_date, ), )

    low_freq = self.start_date.frequency
    num_low_periods = self.num_periods
    high_freq = target_period_class.frequency
    num_within = high_freq // low_freq
    num_high_periods = num_low_periods * num_within

    high_start_date = self.start_date.convert(high_freq, position="start", )
    high_end_date = self.end_date.convert(high_freq, position="end", )
    target_data = _get_target_data(
        target,
        high_start_date,
        high_end_date,
        num_high_periods,
    )

    high_data = disaggregate_arip_data(
        low_data_variant_iterator,
        target_data,
        model,
        num_low_periods,
        int(low_freq),
        int(high_freq),
    )

    return high_start_date, _np.column_stack(high_data, )

    #]


# ==========================================================================
#  ### `disaggregate_arip(self, target_period_class, model, target=None)`
#
#  Splits a low-frequency series into higher-frequency values by fitting a
#  smooth autoregressive path that adds back up to the original data.
#
#  It looks for the smoothest high-frequency path consistent with what you
#  already know. Each low-frequency observation is imposed as a
#  constraint, so it is reproduced exactly by its own high-frequency
#  values. This is the routine behind
#  `Series.disaggregate(..., method="arip")` and is normally reached that
#  way rather than called directly.
#
#  **Parameters.** `self` is the low-frequency series to interpolate. It
#  is read and not changed. `target_period_class` is the period class of
#  the frequency to move up to, such as `QuarterlyPeriod`, rather than a
#  `Frequency` value.
#
#  `model` is a pair naming the form of the process and the way the
#  high-frequency values add back up, and it has no default. The form is
#  `"rate"` or `"multiplicative"` for a series that grows by a rate, or
#  `"diff"` or `"additive"` for one that grows by a constant amount. The
#  aggregation is `"sum"`, `"mean"`, `"avg"`, `"first"` or `"last"`,
#  saying whether the low-frequency figure is the sum of its
#  high-frequency values, their average, or the first or last of them. An
#  unrecognised name for either raises `KeyError`.
#
#  In place of a name the aggregation may be a tuple of weights, one for
#  each high-frequency period inside a single low-frequency period -- four
#  of them going from annual to quarterly, not twelve.
#
#  `target` is an optional high-frequency series of values to hold fixed,
#  which is how an indicator is imposed. Wherever it carries an
#  observation the result is pinned to it. Take care when it covers every
#  high-frequency period of a low-frequency period: that period's own
#  observation is then dropped from the system, so the target replaces it
#  rather than being reconciled with it, and the high-frequency values no
#  longer add up to the low-frequency figure. Left as `None` nothing is
#  pinned.
#
#  **Returns.** A pair of the first high-frequency period and a plain
#  array of interpolated values, one column per variant of the input. It
#  does not return a `Series`; the caller assembles one. A series with no
#  start period gives back `(None, None)`.
#
#  **Examples.** Three years split into quarters, with each year's four
#  quarters summing back to the annual figure:
#
#      >>> import numpy as np
#      >>> import datapie as dp
#      >>> from datapie.series.arip import disaggregate_arip
#      >>> from datapie.periods import QuarterlyPeriod
#      >>> y = dp.Series(start=dp.yy(2020),
#      ...     values=np.array([100., 200., 300.]))
#      >>> start, data = disaggregate_arip(y, QuarterlyPeriod, ("rate", "sum"))
#      >>> start
#      qq(2020,1)
#      >>> data.shape
#      (12, 1)
#      >>> [round(v, 4) for v in data[:, 0].reshape(-1, 4).sum(1).tolist()]
#      [100.0, 200.0, 300.0]
#
# ==========================================================================


class _RateForm:
    """
    """
    #[

    @staticmethod
    def get_rho(low_freq, high_freq, low_data_v, ) -> Real:
        """
        """
        first_low_value, last_low_value, num_low_periods \
            = _get_first_last_observations(low_data_v, )
        low_roc = (
            ((last_low_value / first_low_value) ** (1 / num_low_periods))
            if num_low_periods else 1
        )
        return _conversions.convert_roc(low_roc, low_freq, high_freq, )

    @staticmethod
    def get_constant(*args, ) -> Real:
        return 0

    @staticmethod
    def get_sigma_vector(rho, num_high_periods, ) -> _np.ndarray:
        return rho ** _np.arange(num_high_periods, )

    #]


class _DiffForm:
    """
    """
    #[

    @staticmethod
    def get_rho(low_freq, high_freq, low_data_v, ) -> Real:
        """
        """
        return 1

    @staticmethod
    def get_constant(low_freq, high_freq, low_data_v, ) -> Real:
        """
        """
        first_low_value, last_low_value, num_low_periods \
            = _get_first_last_observations(low_data_v, )
        low_diff = (
            (last_low_value - first_low_value) / num_low_periods
            if num_low_periods else 0
        )
        return _conversions.convert_diff(low_diff, low_freq, high_freq, )

    @staticmethod
    def get_sigma_vector(rho, num_high_periods, ) -> _np.ndarray:
        return _np.ones((num_high_periods, ), dtype=float, )

    #]


def _get_first_last_observations(
    low_data_v: _np.ndarray,
) -> tuple[Real, Real]:
    """
    """
    #[
    where_finite, *_ = _np.nonzero(_np.isfinite(low_data_v, ))
    if where_finite.size:
        first_low_value = low_data_v[where_finite[0]]
        last_low_value = low_data_v[where_finite[-1]]
        num_low_periods = where_finite[-1] - where_finite[0]
    else:
        first_low_value = last_low_value = None
        num_low_periods = 0
    return first_low_value, last_low_value, num_low_periods
    #]


def _create_aggregation_vector_sum(num_within, ):
    return [1, ] * num_within


def _create_aggregation_vector_mean(num_within, ):
    return [1/num_within, ] * num_within


def _create_aggregation_vector_first(num_within, ):
    return [1, ] + [0, ]*(num_within-1)


def _create_aggregation_vector_last(num_within, ):
    return [0, ]*(num_within-1) + [1, ]


_CHOOSE_FORM = {
    "rate": _RateForm,
    "multiplicative": _RateForm,
    "diff": _DiffForm,
    "additive": _DiffForm,
}


_CHOOSE_AGGREGATION_VECTOR = {
    "sum": _create_aggregation_vector_sum,
    "mean": _create_aggregation_vector_mean,
    "avg": _create_aggregation_vector_mean,
    "first": _create_aggregation_vector_first,
    "last": _create_aggregation_vector_last,
}


CHOOSE_AGGREGATION_FUNC = {
    "sum": _np.sum,
    "mean": _np.mean,
    "avg": _np.mean,
    "first": lambda x: x[0],
    "last": lambda x: x[-1],
}


def _create_multiplier_column(low_period, num_low_periods, num_within, ):
    multiplier_column = _np.zeros((num_low_periods, num_within, ), dtype=float, )
    multiplier_column[low_period, :] = 1
    return multiplier_column.reshape(-1, 1)


def _create_target_column(high_period, num_high_periods, ):
    target_column = _np.zeros((num_high_periods, ), dtype=float, )
    target_column[high_period] = 1
    return target_column.reshape(-1, 1, )


def _create_aggregation_row(low_period, num_low_periods, num_within, aggregation_vector, ):
    out = _np.zeros((num_low_periods, num_within, ), dtype=float, )
    out[low_period, :] = aggregation_vector
    return out.reshape(1, -1, )


def _create_target_row(high_period, num_high_periods, ):
    target_row = _np.zeros((num_high_periods, ), dtype=float, )
    target_row[high_period] = 1
    return target_row.reshape(1, -1, )


def _detect_full_low_periods(target_data, num_within, ):
    x = target_data.reshape((-1, num_within, ))
    return _np.where(_np.all(_np.isfinite(x, ), axis=1, ))


def _get_target_data(
    target,
    high_start_date,
    high_end_date,
    num_high_periods,
) -> tuple[_np.ndarray, _np.ndarray, _np.ndarray]:
    """
    """
    return (
        target.get_data_from_until((high_start_date, high_end_date), )
        if target is not None else _np.full((num_high_periods, ), _np.nan, dtype=float, )
    )


def _create_basic_system_matrices(
    num_high_periods: int,
    rho: Real,
    const: Real,
    sigma_vector: _np.ndarray,
) -> tuple[_np.ndarray, _np.ndarray]:
    """
    """
    K = _np.zeros((num_high_periods-1, num_high_periods), dtype=float, )
    C = _np.full((num_high_periods-1, 1), const, dtype=float)
    for i in range(num_high_periods-1, ):
        K[i, i+1] = 1 / sigma_vector[i+1]
        K[i, i] = -rho / sigma_vector[i+1]
        C[i, 0] = const / sigma_vector[i+1]
    F = K.T @ K
    C = K.T @ C
    return F, C


def disaggregate_arip_data(
    low_data_variant_iterator: Iterable[_np.ndarray],
    target_data: _np.ndarray,
    model: tuple[str, str | tuple[Real, ...]],
    num_low_periods: int,
    low_freq: int,
    high_freq: int,
) -> tuple[_np.ndarray, ...]:
    """
    """
    where_finite_target, *_ = _np.nonzero(_np.isfinite(target_data, ))
    num_finite_target = where_finite_target.size

    num_within = high_freq // low_freq
    num_high_periods = num_low_periods * num_within
    where_full_low_periods = _detect_full_low_periods(target_data, num_within, )

    form_string, aggregation = model
    form = _CHOOSE_FORM[form_string]
    aggregation_vector = (
        _CHOOSE_AGGREGATION_VECTOR[aggregation](num_within, )
        if isinstance(aggregation, str) else tuple(aggregation)
    )

    create_multiplier_column = _ft.partial(
        _create_multiplier_column,
        num_low_periods=num_low_periods,
        num_within=num_within,
    )

    create_target_column = _ft.partial(
        _create_target_column,
        num_high_periods=num_high_periods,
    )

    create_aggregation_row = _ft.partial(
        _create_aggregation_row,
        num_low_periods=num_low_periods,
        num_within=num_within,
        aggregation_vector=aggregation_vector,
    )

    create_target_row = _ft.partial(
        _create_target_row,
        num_high_periods=num_high_periods,
    )

    high_data = ()

    for low_data_v in low_data_variant_iterator:

        if low_data_v.size != num_low_periods:
            raise _wrongdoings.Critical(
                f"Data variant has {low_data_v.size} periods, "
                f"but {num_low_periods} are required."
            )

        if target_data.size != num_high_periods:
            raise _wrongdoings.Critical(
                f"Target data has {target_data.size} periods, "
                f"but {num_high_periods} are required."
            )

        low_data_v[where_full_low_periods] = _np.nan
        where_finite, *_ = _np.nonzero(_np.isfinite(low_data_v, ))
        num_finite = where_finite.size

        rho = form.get_rho(low_freq, high_freq, low_data_v, )
        const = form.get_constant(low_freq, high_freq, low_data_v, )
        sigma_vector = form.get_sigma_vector(rho, num_high_periods, )

        F, C = _create_basic_system_matrices(
            num_high_periods,
            rho,
            const,
            sigma_vector,
        )

        multiplier_columns = tuple(
            create_multiplier_column(i, )
            for i in where_finite
        )

        target_columns = tuple(
            create_target_column(i, )
            for i in where_finite_target
        )

        right_padding = _np.zeros(
            (1, num_finite+num_finite_target, ),
            dtype=float,
        )

        aggregation_rows = tuple(
            _np.hstack((create_aggregation_row(i, ), right_padding, ), )
            for i in where_finite
        )

        target_rows = tuple(
            _np.hstack((create_target_row(i, ), right_padding, ), )
            for i in where_finite_target
        )

        F = _np.hstack((F, *multiplier_columns, *target_columns, ))
        F = _np.vstack((F, *aggregation_rows, *target_rows, ))

        C = _np.vstack((
            C,
            low_data_v[where_finite].reshape(-1, 1, ),
            target_data[where_finite_target].reshape(-1, 1, ),
        ))

        high_data_v = _np.linalg.solve(F, C, )
        high_data_v = high_data_v[:num_high_periods].flatten()
        high_data += (high_data_v, )

    return high_data


# ==========================================================================
#  ### `disaggregate_arip_data(low_data_variant_iterator, target_data,
#   model, num_low_periods, low_freq, high_freq)`
#
#  Solves the interpolation problem on plain arrays, once for each variant
#  of the data.
#
#  This is the numerical core that `disaggregate_arip` calls once it has
#  worked out the periods and pulled the data out of the series. It knows
#  nothing about time; everything it needs arrives as arrays and counts.
#  Reach for it directly only when you are working with arrays rather than
#  with a `Series`.
#
#  For each variant it builds a linear system: a smoothness part, one row
#  per low-frequency observation forcing the high-frequency values to
#  aggregate back to it, and one row per fixed target value. Solving that
#  system gives the high-frequency path.
#
#  **Parameters.** `low_data_variant_iterator` yields one array of
#  low-frequency values per variant, each of length `num_low_periods`; a
#  variant of any other length raises `Critical`. `target_data` is a flat
#  array of high-frequency values with missing entries where nothing is
#  pinned, and it must hold one value for every high-frequency period, or
#  it also raises `Critical`.
#
#  Where `target_data` supplies a complete set of values for one
#  low-frequency period, that period's own observation is struck out of
#  the system before solving. The target replaces the low-frequency
#  constraint there instead of being reconciled with it, so those
#  high-frequency values need not add back up to the low-frequency figure.
#  The strike-out is written into the array the iterator handed over.
#  `disaggregate_arip` passes copies and is unaffected, but if you call
#  this function with an array of your own, that observation is replaced
#  by a missing value in your array too.
#
#  `model` is the pair described under `disaggregate_arip`.
#  `num_low_periods` is how many low-frequency observations there are, and
#  `low_freq` and `high_freq` are the two frequencies as plain integers,
#  such as `1` and `4` for annual to quarterly. Their ratio gives the
#  number of high-frequency periods inside each low one.
#
#  **Returns.** A tuple holding one flat array per variant, each of
#  `num_low_periods` times that ratio values. Nothing is returned about
#  the periods; the caller supplies those.
#
#  **Examples.** Three annual figures interpolated into twelve quarters,
#  with nothing pinned:
#
#      >>> import numpy as np
#      >>> from datapie.series.arip import disaggregate_arip_data
#      >>> low = np.array([100., 200., 300.])
#      >>> target = np.full(12, np.nan)
#      >>> out = disaggregate_arip_data(iter([low]), target,
#      ...     ("rate", "sum"), 3, 1, 4)
#      >>> len(out)
#      1
#      >>> [round(v, 4) for v in out[0].reshape(-1, 4).sum(1).tolist()]
#      [100.0, 200.0, 300.0]
#
# ==========================================================================

