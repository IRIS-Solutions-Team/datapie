"""
Autoregressive interpolation for frequency disaggregation
"""


#[

from __future__ import annotations

from typing import (Self, Iterable, Literal, )
from numbers import (Real, )
import functools as _ft
import numpy as _np
import documark as _dm

from ..periods import Period
from .. import wrongdoings as _wrongdoings
from . import _conversions as _conversions

#]


FormType = Literal["rate", "multiplicative", "diff", "additive", ]
AggregationType = Literal["sum", "mean", "avg", "last", "first", ]


@_dm.reference(category="conversion", )
def disaggregate_arip(
    self,
    target_period_class: Period,
    model: tuple[FormType, AggregationType],
    target: Self | None = None,
    # indicator: _np.ndarray | None = None,
) -> Self:
    r"""
==Fit a smooth higher-frequency path to lower-frequency observations==

#### Syntax

    start, values = disaggregate_arip(
        x,
        target_period_class,
        model,
        target=None,
    )

#### Input arguments

!!! input "target_period_class"
    The period class for the higher frequency, rather than a frequency value.

!!! input "model"
    A required pair choosing the path and aggregation rule. The path is `"rate"` (`"multiplicative"`) for growth rates or `"diff"` (`"additive"`) for additive changes. The aggregation is `"sum"`, `"mean"` (`"avg"`), `"first"` or `"last"`. A sequence of weights may replace the aggregation name, with one weight per higher-frequency period in each lower-frequency block.

!!! input "target"
    An optional higher-frequency series whose available values are held fixed. The default is `None`. Use a single target variant; the same target path is used for every input variant.

#### Returns

!!! returns "start, values"
    The first higher-frequency period and an array with one column per input variant. An input with no start period gives `(None, None)`. The input and target series are unchanged.

This support function is reached through `disaggregate` with `method="arip"`; it is not available directly from `datapie`.

??? note "Details"
    The fitted path reproduces each available lower-frequency observation according to the selected aggregation rule. If target values fill an entire lower-frequency block, they replace that block's original observation; their aggregate need not match it.

    The rate model estimates average growth from the first and last available observations. The difference model estimates an average additive change. The higher-frequency path minimizes departures from that estimated rule while satisfying the retained observations and targets.

#### See also

[`disaggregate`](#disaggregate), [`disaggregate_arip_data`](#disaggregate_arip_data)
    """
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


@_dm.reference(category="conversion", )
def disaggregate_arip_data(
    low_data_variant_iterator: Iterable[_np.ndarray],
    target_data: _np.ndarray,
    model: tuple[str, str | tuple[Real, ...]],
    num_low_periods: int,
    low_freq: int,
    high_freq: int,
) -> tuple[_np.ndarray, ...]:
    r"""
==Fit higher-frequency paths to arrays of lower-frequency values==

#### Syntax

    values = disaggregate_arip_data(
        low_data_variant_iterator,
        target_data,
        model,
        num_low_periods,
        low_freq,
        high_freq,
    )

#### Input arguments

!!! input "low_data_variant_iterator"
    One one-dimensional array per input variant, each containing `num_low_periods` values.

!!! input "target_data"
    A one-dimensional array covering all higher-frequency periods. Finite values are held fixed; nonfinite entries leave the path unconstrained. The same target applies to every variant.

!!! input "model"
    The path and aggregation pair described in [`disaggregate_arip`](#disaggregate_arip).

!!! input "num_low_periods"
    The number of lower-frequency periods.

!!! input "low_freq"
    The lower frequency, expressed as periods per year.

!!! input "high_freq"
    The higher frequency, expressed as periods per year. Its integer ratio to `low_freq` determines the number of positions per lower-frequency block.

#### Returns

!!! returns "values"
    A tuple containing one higher-frequency array per input variant.

This support function is not available directly from `datapie`. It changes the supplied lower-frequency arrays: observations for blocks completely filled by target values are replaced by missing values before fitting. The target array is unchanged.

#### See also

[`disaggregate_arip`](#disaggregate_arip)
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



