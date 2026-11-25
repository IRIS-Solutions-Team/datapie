"""
Univariate time series filters
"""


#[

from __future__ import annotations

# Standard library imports
import textwrap as _tw

# Third-party imports
import numpy as _np
import documark as _dm

# Application imports
from ..periods import Period, Span
from ._functionalize import FUNC_STRING

# Typing imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from types import EllipsisType
    from collections.abc import Iterable
    from .main import Series

#]


_DEFAULT_ALPHA = 0.3
_DEFAULT_BETA = 0.3
_DEFAULT_DECAY = 0.9


def _cum_avg(
    periods: tuple[Period, ...] | None,
    values: _np.ndarray,
) -> _np.ndarray:
    """
    Cumulative average filter.
    
    Computes the cumulative arithmetic mean of all observations up to each time point.
    For missing observations, the previous cumulative average is propagated.
    """
    #[
    
    result = _np.full_like(values, _np.nan)
    
    # Vectorized NaN detection
    valid_mask = ~_np.isnan(values)
    valid_indices = _np.where(valid_mask)[0]
    
    if len(valid_indices) == 0:
        # All values are NaN
        return result
    
    first_valid_idx = valid_indices[0]
    result[first_valid_idx] = values[first_valid_idx]  # CA_0 = X_0
    
    count = 1
    cumsum = values[first_valid_idx]
    
    # Apply cumulative average
    for i in range(first_valid_idx + 1, len(values)):
        if valid_mask[i]:
            count += 1
            cumsum += values[i]
            result[i] = cumsum / count
        else:
            # Propagate previous cumulative average for missing observations
            result[i] = result[i - 1]
    
    return result
    
    #]


def _exp_smooth(
    periods: tuple[Period, ...] | None,
    values: _np.ndarray,
    alpha: float,
) -> _np.ndarray:
    """
    Simple exponential smoothing filter implementation.

    Uses the recursive formula: S_t = alpha * X_t + (1 - alpha) * S_{t-1}
    where S_0 = X_0 (first observation is used as initial value).
    """
    #[

    result = _np.full_like(values, _np.nan)

    # Vectorized NaN detection
    valid_mask = ~_np.isnan(values)
    valid_indices = _np.where(valid_mask)[0]

    if len(valid_indices) == 0:
        # All values are NaN
        return result

    first_valid_idx = valid_indices[0]
    result[first_valid_idx] = values[first_valid_idx]  # S_0 = X_0

    # Apply exponential smoothing recursively
    for i in range(first_valid_idx + 1, len(values)):
        if valid_mask[i]:
            result[i] = alpha * values[i] + (1 - alpha) * result[i - 1]
        else:
            # Propagate previous smoothed value for missing observations
            result[i] = result[i - 1]

    return result

    #]


def _double_exp_smooth(
    periods: tuple[Period, ...],
    values: _np.ndarray,
    alpha: float,
    beta: float,
) -> _np.ndarray:
    """
    Double exponential smoothing filter implementation (Holt's method).

    Uses the recursive formulas:
    - Level: L_t = alpha * X_t + (1 - alpha) * (L_{t-1} + T_{t-1})
    - Slope: T_t = beta * (L_t - L_{t-1}) + (1 - beta) * T_{t-1}
    - Smoothed: S_t = L_t

    Initial values: L_0 = X_0, T_0 = slope between first two valid observations
    """
    #[

    result = _np.full_like(values, _np.nan)

    # Vectorized NaN detection
    valid_mask = ~_np.isnan(values)
    valid_indices = _np.where(valid_mask)[0]

    if len(valid_indices) == 0:
        # All values are NaN
        return result

    first_valid_idx = valid_indices[0]

    # Initialize level
    level = values[first_valid_idx]
    result[first_valid_idx] = level

    if len(valid_indices) < 2:
        # Only one valid value, use simple exponential smoothing
        for i in range(first_valid_idx + 1, len(values)):
            if valid_mask[i]:
                level = alpha * values[i] + (1 - alpha) * level
                result[i] = level
            else:
                result[i] = level
        return result

    second_valid_idx = valid_indices[1]

    # Initialize slope using first two valid observations, accounting for distance
    periods_between = second_valid_idx - first_valid_idx
    slope = (values[second_valid_idx] - values[first_valid_idx]) / periods_between
    result[second_valid_idx] = level + slope * periods_between

    # Update level and slope with second observation
    new_level = alpha * values[second_valid_idx] + (1 - alpha) * (level + slope * periods_between)
    new_slope = beta * (new_level - level) / periods_between + (1 - beta) * slope
    level, slope = new_level, new_slope

    # Apply double exponential smoothing recursively
    for i in range(second_valid_idx + 1, len(values)):
        if valid_mask[i]:
            # Update with actual observation
            new_level = alpha * values[i] + (1 - alpha) * (level + slope)
            new_slope = beta * (new_level - level) + (1 - beta) * slope
            result[i] = new_level
            level, slope = new_level, new_slope
        else:
            # Propagate forecast for missing observations
            result[i] = level + slope
            # Update level and slope assuming forecast was correct
            new_level = alpha * result[i] + (1 - alpha) * (level + slope)
            new_slope = beta * (new_level - level) + (1 - beta) * slope
            level, slope = new_level, new_slope

    return result

    #]


def _decay_avg(
    periods: tuple[Period, ...] | None,
    values: _np.ndarray,
    decay: float,
) -> _np.ndarray:
    """
    Decay average filter with geometrically decaying weights.
    
    Computes a weighted average where weights decay geometrically backwards in time:
    W_t = [1, decay, decay^2, decay^3, ...] for observations [X_t, X_{t-1}, X_{t-2}, ...]
    
    Uses recursive computation: DA_t = (X_t + decay * DA_{t-1} * N_{t-1}) / (1 + decay * N_{t-1})
    where N_t is the effective number of observations contributing to DA_t.
    
    For missing observations, the previous decay average is propagated and the
    effective count is scaled by the decay factor.
    
    Special case: When decay = 1, delegates to cumulative average for numerical stability.
    """
    #[
    
    # Special case: decay = 1 is equivalent to cumulative average
    if decay == 1.0:
        return _cum_avg(periods, values)
    
    result = _np.full_like(values, _np.nan)
    
    # Vectorized NaN detection
    valid_mask = ~_np.isnan(values)
    valid_indices = _np.where(valid_mask)[0]
    
    if len(valid_indices) == 0:
        # All values are NaN
        return result
    
    first_valid_idx = valid_indices[0]
    result[first_valid_idx] = values[first_valid_idx]  # DA_0 = X_0
    
    # Track effective count of observations (for proper normalization)
    effective_count = 1.0
    
    # Apply decay average recursively
    for i in range(first_valid_idx + 1, len(values)):
        if valid_mask[i]:
            # Update with actual observation: DA_t = (X_t + decay * DA_{t-1} * N_{t-1}) / (1 + decay * N_{t-1})
            numerator = values[i] + decay * result[i - 1] * effective_count
            denominator = 1 + decay * effective_count
            result[i] = numerator / denominator
            effective_count = denominator  # Update effective count
        else:
            # Propagate previous decay average for missing observations
            result[i] = result[i - 1]
            # Scale effective count by decay factor (represents time passage without new data)
            effective_count = decay * effective_count
    
    return result
    
    #]


class Mixin:
    """
    Mixin class to add univariate filtering functionality to Series
    """


    #[

    @_dm.reference(
        category="filtering",
        call_name="univariate_filters",
        anchor="univariate-time-series-filters",
    )
    def univariate_filters(self, ) -> None:
        r"""
<a id="univariate_filters"></a>

==Retain the univariate-filter documentation placeholder==

#### Syntax

    series.univariate_filters()

#### Input arguments

!!! input "series"

    Any series; this placeholder does not inspect or filter its observations.

#### Returns

!!! returns "None"

    No data, span, or other series attributes are changed. There is no function form.

Use a named filter to perform a calculation:
[`exp_smooth`](#exp_smooth), [`double_exp_smooth`](#double_exp_smooth),
[`decay_avg`](#decay_avg), or [`cum_avg`](#cum_avg).
        """
        pass

    @_dm.reference(category="filtering")
    def exp_smooth(
        self,
        span: Span | Iterable[Period] | EllipsisType = ...,
        alpha: float = _DEFAULT_ALPHA,
    ) -> None:
        r"""
==Apply simple exponential smoothing==

#### Syntax

    series.exp_smooth(
        span=...,
        alpha=0.3,
    )
    result = datapie.exp_smooth(
        series,
        span=...,
        alpha=0.3,
    )

#### Input arguments

!!! input "series"

    The series to filter.

!!! input "span"

    Periods to filter; `...` (default) selects the current span. Filtering
    covers the full interval between the first and last requested periods. An
    empty span leaves the series unchanged.

!!! input "alpha"

    Weight on the latest observation; `0.3` by default. Must satisfy
    `0 < alpha <= 1`; otherwise `ValueError` is raised.

#### Returns

!!! returns "None — method form"

    The method replaces the series with the filtered values in place.

!!! returns "result — function form"

    The function returns a new series containing the filtered values; the input is unchanged.

The first available observation initializes the result. Thereafter, the result
is `alpha * current + (1 - alpha) * previous_result`. Missing observations
repeat the previous result.

Each variant is filtered independently, starting at its first nonmissing value in
the requested interval. Earlier positions stay missing; an all-missing interval
stays missing. Values outside the interval are kept. A wider span extends the
series without shortening it; these filters do not trim missing rows at the ends.
Use floating-point data, especially when extending a series with missing values.
Arguments may be passed positionally or by keyword in the order shown.

#### See also

[`double_exp_smooth`](#double_exp_smooth), [`decay_avg`](#decay_avg), [`cum_avg`](#cum_avg)
        """
        if not (0 < alpha <= 1):
            raise ValueError("Alpha must be between 0 and 1 (exclusive of 0, inclusive of 1)")

        self._apply_to_variants(
            _exp_smooth,
            span=span,
            #
            alpha=alpha,
        )

    @_dm.reference(category="filtering")
    def double_exp_smooth(
        self,
        alpha: float = _DEFAULT_ALPHA,
        beta: float = _DEFAULT_BETA,
        span: Span | Iterable[Period] | EllipsisType = ...,
    ) -> None:
        r"""
==Apply smoothing that also tracks a slope==

#### Syntax

    series.double_exp_smooth(
        alpha=0.3,
        beta=0.3,
        span=...,
    )
    result = datapie.double_exp_smooth(
        series,
        alpha=0.3,
        beta=0.3,
        span=...,
    )

#### Input arguments

!!! input "series"

    The series to filter.

!!! input "span"

    Periods to filter; `...` (default) selects the current span. Filtering
    covers the full interval between the first and last requested periods. An
    empty span leaves the series unchanged.

!!! input "alpha"

    Weight on the current observation when updating the level; `0.3` by
    default. Must satisfy `0 < alpha <= 1`; otherwise `ValueError` is raised.

!!! input "beta"

    Weight on the latest level change when updating the slope; `0.3` by
    default. Must satisfy `0 <= beta <= 1`; otherwise `ValueError` is raised.

#### Returns

!!! returns "None — method form"

    The method replaces the series with the filtered values in place.

!!! returns "result — function form"

    The function returns a new series containing the filtered values; the input is unchanged.

Holt smoothing updates a level and slope; the output is the level, not a
separate slope series. The first available value initializes the level. The first
two available values initialize the slope using their elapsed period distance.
Missing positions between those first two values remain missing. Later missing
observations use a one-step level-plus-slope forecast and advance the level.
With only one available observation, subsequent positions repeat its level.

Each variant is filtered independently, starting at its first nonmissing value in
the requested interval. Earlier positions stay missing; an all-missing interval
stays missing. Values outside the interval are kept. A wider span extends the
series without shortening it; these filters do not trim missing rows at the ends.
Use floating-point data, especially when extending a series with missing values.
Arguments may be passed positionally or by keyword in the order shown.

#### See also

[`exp_smooth`](#exp_smooth), [`decay_avg`](#decay_avg), [`cum_avg`](#cum_avg)
        """
        if not (0 < alpha <= 1):
            raise ValueError("Alpha must be between 0 and 1 (exclusive of 0, inclusive of 1)")
        if not (0 <= beta <= 1):
            raise ValueError("Beta must be between 0 and 1 (inclusive)")

        self._apply_to_variants(
            _double_exp_smooth,
            span=span,
            #
            alpha=alpha,
            beta=beta,
        )

    @_dm.reference(category="filtering")
    def decay_avg(
        self,
        span: Span | Iterable[Period] | EllipsisType = ...,
        decay: float = _DEFAULT_DECAY,
    ) -> None:
        r"""
==Average observations with declining weights==

#### Syntax

    series.decay_avg(
        span=...,
        decay=0.9,
    )
    result = datapie.decay_avg(
        series,
        span=...,
        decay=0.9,
    )

#### Input arguments

!!! input "series"

    The series to filter.

!!! input "span"

    Periods to filter; `...` (default) selects the current span. Filtering
    covers the full interval between the first and last requested periods. An
    empty span leaves the series unchanged.

!!! input "decay"

    Weight retained by past observations per elapsed period; `0.9` by
    default. Must satisfy `0 < decay <= 1`; otherwise `ValueError` is raised.
    `1` gives the same result as `cum_avg`.

#### Returns

!!! returns "None — method form"

    The method replaces the series with the filtered values in place.

!!! returns "result — function form"

    The function returns a new series containing the filtered values; the input is unchanged.

The first available value initializes the average. Older observations receive
geometrically declining weights, normalized by their total weight. Missing
observations repeat the previous result but reduce the carried weight by `decay`,
so elapsed missing periods still reduce the influence of older data.

Each variant is filtered independently, starting at its first nonmissing value in
the requested interval. Earlier positions stay missing; an all-missing interval
stays missing. Values outside the interval are kept. A wider span extends the
series without shortening it; these filters do not trim missing rows at the ends.
Use floating-point data, especially when extending a series with missing values.
Arguments may be passed positionally or by keyword in the order shown.

#### See also

[`exp_smooth`](#exp_smooth), [`double_exp_smooth`](#double_exp_smooth), [`cum_avg`](#cum_avg)
        """
        if not (0 < decay <= 1):
            raise ValueError("Decay must be between 0 and 1 (exclusive of 0, inclusive of 1)")

        self._apply_to_variants(
            _decay_avg,
            span=span,
            #
            decay=decay,
        )

    @_dm.reference(category="filtering")
    def cum_avg(
        self,
        span: Span | Iterable[Period] | EllipsisType = ...,
    ) -> None:
        r"""
==Calculate the average of observations seen so far==

#### Syntax

    series.cum_avg(
        span=...,
    )
    result = datapie.cum_avg(
        series,
        span=...,
    )

#### Input arguments

!!! input "series"

    The series to filter.

!!! input "span"

    Periods to filter; `...` (default) selects the current span. Filtering
    covers the full interval between the first and last requested periods. An
    empty span leaves the series unchanged.

#### Returns

!!! returns "None — method form"

    The method replaces the series with the filtered values in place.

!!! returns "result — function form"

    The function returns a new series containing the filtered values; the input is unchanged.

At each period, the result is the arithmetic mean of all available observations
since filtering began. The count includes observations, not elapsed periods.
Missing observations repeat the previous result without increasing the count.

Each variant is filtered independently, starting at its first nonmissing value in
the requested interval. Earlier positions stay missing; an all-missing interval
stays missing. Values outside the interval are kept. A wider span extends the
series without shortening it; these filters do not trim missing rows at the ends.
Use floating-point data, especially when extending a series with missing values.
Arguments may be passed positionally or by keyword in the order shown.

#### See also

[`exp_smooth`](#exp_smooth), [`double_exp_smooth`](#double_exp_smooth), [`decay_avg`](#decay_avg)
        """
        self._apply_to_variants(
            _cum_avg,
            span=span,
        )

    #]
    #]


# Create functional forms
_functional_forms = {
    "exp_smooth",
    "double_exp_smooth",
    "decay_avg",
    "cum_avg",
}

for n in _functional_forms:
    code = FUNC_STRING.format(n=n, )
    exec(_tw.dedent(code, ), globals(), )
    globals()[n].__doc__ = getattr(Mixin, n).__doc__

__all__ = tuple(_functional_forms)

