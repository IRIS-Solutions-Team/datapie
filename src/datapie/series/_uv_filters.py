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


# ==========================================================================
#  ### Behaviour shared by all four filters in this file -
#  `exp_smooth`, `double_exp_smooth`, `decay_avg` and `cum_avg`.
#
#  They change the series in place and return nothing. `y = x.cum_avg()`
#  leaves `y` set to `None`, and the raw values in `x` are already gone;
#  copy with `x.copy()` first if you need them.
#
#  Missing observations inside the data are filled in, silently. Three of
#  the four carry the previous filtered value forward into the gap, and
#  `double_exp_smooth` writes its own forecast there instead.
#
#  Missing observations before the first observation are left alone. Each
#  filter starts at the first period holding a number and uses it
#  unchanged as its own starting value.
#
#  `span` can grow the series and never shrinks it. Left alone it is `...`,
#  the whole span currently covered; a `span` reaching past the data
#  extends the series permanently and moves `start` and `end`.
#
#  Every variant (column) is filtered on its own, with no information
#  passing between variants.
#
#  Watch where `span` sits in the argument list. It comes first in
#  `exp_smooth`, `decay_avg` and `cum_avg`, so in `x.exp_smooth(0.5)` the
#  `0.5` is taken as `span`. Pass every argument by keyword.
#
#  **Examples**
#
#      >>> import numpy as np
#      >>> import datapie as dp
#      >>> x = dp.Series(start=dp.qq(2020, 1),
#      ...     values=np.array([1.0, 2.0, 3.0, 4.0]))
#      >>> x.cum_avg(span=dp.Span(dp.qq(2019, 3), dp.qq(2020, 4)))
#      >>> x.get_data()[:, 0].tolist()
#      [nan, nan, 1.0, 1.5, 2.0, 2.5]
#
#      >>> x = dp.Series(start=dp.qq(2020, 1),
#      ...     values=np.array([1.0, 2.0, 3.0, 4.0]))
#      >>> x.cum_avg(span=dp.Span(dp.qq(2020, 1), dp.qq(2021, 2)))
#      >>> x.get_data()[:, 0].tolist()
#      [1.0, 1.5, 2.0, 2.5, 2.5, 2.5]
#
# ==========================================================================


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

    @_dm.reference(category="filtering")
    def exp_smooth(
        self,
        span: Span | Iterable[Period] | EllipsisType = ...,
        alpha: float = _DEFAULT_ALPHA,
    ) -> None:
        r"""
············································································

==Simple exponential smoothing filter==

Apply simple exponential smoothing to each variant of the time series.
Uses the recursive formula: S_t = alpha * X_t + (1 - alpha) * S_{t-1}

### Input arguments ###

???+ input "alpha"
Smoothing parameter (0 < alpha <= 1). Higher values give more weight
to recent observations.

???+ input "span"
Time span to apply the filter to. If `span=...` (default), uses the
full span of the time series.

### Returns ###

???+ returns "None"
This method modifies `self` in-place and does not return a value.

············································································
        """
        if not (0 < alpha <= 1):
            raise ValueError("Alpha must be between 0 and 1 (exclusive of 0, inclusive of 1)")

        self._apply_to_variants(
            _exp_smooth,
            span=span,
            #
            alpha=alpha,
        )

    # ==========================================================================
    #  ### `exp_smooth(span=..., alpha=0.3)`
    #
    #  Simple exponential smoothing filter. Smooths each variant of the
    #  series in place by exponentially weighted averaging.
    #
    #  Each filtered value is a weighted average of the current
    #  observation and the previous filtered value, so the weight given to
    #  older data falls off geometrically. Use it to strip short-lived
    #  noise out of a series while keeping its level.
    #
    #  **Parameters.** `alpha` is the weight on the current observation,
    #  so a larger value tracks the data more closely and smooths less. It
    #  must satisfy `0 < alpha <= 1` or a `ValueError` is raised. Left
    #  alone it is 0.3, which smooths heavily; `alpha=1` returns gap-free
    #  data unchanged. For `span`, see the shared block at the top of this
    #  file.
    #
    #  **Returns.** Nothing; the series is modified in place.
    #
    #  **Examples.** The third period has no observation, so it is filled
    #  with the previous filtered value of 1.5 rather than left missing:
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(start=dp.qq(2020, 1),
    #      ...     values=np.array([1.0, 2.0, np.nan, 4.0, 5.0]))
    #      >>> x.exp_smooth(alpha=0.5)
    #      >>> x.get_data()[:, 0].tolist()
    #      [1.0, 1.5, 1.5, 2.75, 3.875]
    #
    #  `dp.exp_smooth(x, alpha=0.5)` leaves `x` unchanged; see the final
    #  block of this file.
    #
    # ==========================================================================

    @_dm.reference(category="filtering")
    def double_exp_smooth(
        self,
        alpha: float = _DEFAULT_ALPHA,
        beta: float = _DEFAULT_BETA,
        span: Span | Iterable[Period] | EllipsisType = ...,
    ) -> None:
        r"""
············································································

==Double exponential smoothing filter (Holt's method)==

Apply double exponential smoothing to each variant of the time series.
Captures both level and slope components using two smoothing parameters.

### Input arguments ###

???+ input "alpha"
Level smoothing parameter (0 < alpha <= 1). Controls how quickly the
level component adapts to new observations.

???+ input "beta"
Slope smoothing parameter (0 <= beta <= 1). Controls how quickly the
slope component adapts to changes in the slope.

???+ input "span"
Time span to apply the filter to. If `span=...` (default), uses the
full span of the time series.

### Returns ###

???+ returns "None"
This method modifies `self` in-place and does not return a value.

············································································
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

    # ==========================================================================
    #  ### `double_exp_smooth(alpha=0.3, beta=0.3, span=...)`
    #
    #  Double exponential smoothing filter. Smooths each variant of the
    #  series in place while tracking a trend, using Holt's two-parameter
    #  method.
    #
    #  It carries both a level and a slope, so unlike `exp_smooth` it
    #  follows a rising or falling series instead of lagging behind it.
    #  The argument order here is not the one the other three filters use:
    #  `alpha` and `beta` come first and `span` last.
    #
    #  **Parameters.** `alpha` smooths the level and must satisfy
    #  `0 < alpha <= 1`. `beta` smooths the slope and must satisfy
    #  `0 <= beta <= 1`, so zero is allowed here although it is not for
    #  `alpha`; breaching either bound raises `ValueError`. Both are 0.3
    #  when left alone. Given fewer than two observations the method
    #  quietly falls back to simple exponential smoothing. For `span`, see
    #  the shared block at the top of this file.
    #
    #  **Returns.** Nothing; the series is modified in place.
    #
    #  **Examples.** A single missing observation does more than leave a
    #  hole. The forecast written into the gap is fed back into the
    #  recursion as though it had been observed, which lifts the following
    #  value to 6.0 -- above every number in the data. Compare a series
    #  with no gap:
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(start=dp.qq(2020, 1),
    #      ...     values=np.array([1.0, 3.0, 2.0, 5.0, 4.0]))
    #      >>> x.double_exp_smooth(0.5, 0.2)
    #      >>> x.get_data()[:, 0].tolist()
    #      [1.0, 3.0, 3.5, 5.1, 5.39]
    #
    #  against the same series with the middle observation missing:
    #
    #      >>> x = dp.Series(start=dp.qq(2020, 1),
    #      ...     values=np.array([1.0, 3.0, np.nan, 5.0, 4.0]))
    #      >>> x.double_exp_smooth(0.5, 0.2)
    #      >>> x.get_data()[:, 0].tolist()
    #      [1.0, 3.0, 5.0, 6.0, 5.9]
    #
    #  The second observation comes back unchanged in both, because the
    #  starting slope is fitted to the first two observations.
    #
    #  `dp.double_exp_smooth(x, 0.5, 0.2)` leaves `x` unchanged; see the
    #  final block of this file.
    #
    # ==========================================================================

    @_dm.reference(category="filtering")
    def decay_avg(
        self,
        span: Span | Iterable[Period] | EllipsisType = ...,
        decay: float = _DEFAULT_DECAY,
    ) -> None:
        r"""
············································································

==Decay average filter with geometrically decaying weights==

Apply a decay average filter to each variant of the time series.
Weights decay geometrically backwards in time: [1, decay, decay^2, decay^3, ...].
Implemented as a recursive algorithm for efficient time evolution tracking.

### Input arguments ###

???+ input "decay"
Decay factor for weights (0 < decay < 1). Higher values give more weight
to historical observations. Common values: 0.9, 0.8, 0.7.

???+ input "span"
Time span to apply the filter to. If `span=...` (default), uses the
full span of the time series.

### Returns ###

???+ returns "None"
This method modifies `self` in-place and does not return a value.

### Notes ###

The filter uses the recursive formula:
DA_t = (X_t + decay * DA_{t-1} * N_{t-1}) / (1 + decay * N_{t-1})

where DA_t is the decay average at time t, X_t is the observation
at time t, and N_{t-1} is the effective count of previous observations.

For missing observations, the previous decay average is propagated
and the effective count is scaled by the decay factor.

············································································
        """
        if not (0 < decay <= 1):
            raise ValueError("Decay must be between 0 and 1 (exclusive of 0, inclusive of 1)")

        self._apply_to_variants(
            _decay_avg,
            span=span,
            #
            decay=decay,
        )

    # ==========================================================================
    #  ### `decay_avg(span=..., decay=0.9)`
    #
    #  Decay average filter with geometrically decaying weights. Replaces
    #  each variant of the series in place with a weighted average of
    #  every observation up to that period, weighted so that older data
    #  counts for less.
    #
    #  The weights going backwards in time are 1, `decay`, `decay`
    #  squared, and so on. Older data fades out gradually instead of
    #  dropping out all at once, which is what separates this from a
    #  moving average over a fixed window.
    #
    #  **Parameters.** `decay` sets how fast the past fades, and higher
    #  values keep more of it. The check is `0 < decay <= 1`, so `decay=1`
    #  is accepted and silently gives the plain cumulative average of
    #  `cum_avg`, while `decay=0` raises `ValueError`. Left alone it is
    #  0.9. For `span`, see the shared block at the top of this file.
    #
    #  **Returns.** Nothing; the series is modified in place.
    #
    #  **Examples.** Across the gap in the third period the previous value
    #  is repeated, and the weight carried by the past is scaled down by
    #  `decay` even though no new observation arrived. Values are rounded
    #  here only to keep the line short:
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(start=dp.qq(2020, 1),
    #      ...     values=np.array([1.0, 2.0, np.nan, 4.0, 5.0]))
    #      >>> x.decay_avg(decay=0.9)
    #      >>> [round(v, 4) for v in x.get_data()[:, 0].tolist()]
    #      [1.0, 1.5263, 1.5263, 2.5006, 3.2614]
    #
    #  `dp.decay_avg(x, decay=0.9)` leaves `x` unchanged; see the final
    #  block of this file.
    #
    # ==========================================================================

    @_dm.reference(category="filtering")
    def cum_avg(
        self,
        span: Span | Iterable[Period] | EllipsisType = ...,
    ) -> None:
        r"""
············································································

==Cumulative average filter==

Apply a cumulative average filter to each variant of the time series.
Computes the arithmetic mean of all observations from the start up to
each time point.

### Input arguments ###

???+ input "span"
Time span to apply the filter to. If `span=...` (default), uses the
full span of the time series.

### Returns ###

???+ returns "None"
This method modifies `self` in-place and does not return a value.

### Notes ###

The filter computes: CA_t = (X_1 + X_2 + ... + X_t) / t

where CA_t is the cumulative average at time t, and X_i are the
observations from time 1 to t.

For missing observations, the previous cumulative average is propagated.
This is equivalent to decay_avg with decay=1.

············································································
        """
        self._apply_to_variants(
            _cum_avg,
            span=span,
        )

    # ==========================================================================
    #  ### `cum_avg(span=...)`
    #
    #  Cumulative average filter. Replaces each variant of the series
    #  in place with the running mean of all observations up to and
    #  including each period.
    #
    #  Use it when what you want is the average so far rather than the
    #  average of the whole sample: a year-to-date mean, or a line that
    #  settles down as the sample grows. The divisor is the number of
    #  observations seen, not the number of periods elapsed, and the two
    #  part company as soon as there is a gap.
    #
    #  **Parameters.** For `span`, see the shared block at the top of this
    #  file. There are no other arguments.
    #
    #  **Returns.** Nothing; the series is modified in place.
    #
    #  **Examples.** The third period has no observation, so the running
    #  mean does not move. The fourth then divides a total of 7.0 by the
    #  three observations seen, not by the four periods elapsed:
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(start=dp.qq(2020, 1),
    #      ...     values=np.array([1.0, 2.0, np.nan, 4.0, 5.0]))
    #      >>> x.cum_avg()
    #      >>> x.get_data()[:, 0].tolist()
    #      [1.0, 1.5, 1.5, 2.3333333333333335, 3.0]
    #
    #  **See Also.** `decay_avg(decay=1)` does exactly the same thing.
    #  `dp.cum_avg(x)` leaves `x` unchanged; see the final block of this
    #  file.
    #
    # ==========================================================================
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

__all__ = tuple(_functional_forms)


# ==========================================================================
#  ### `cum_avg(x, span=...)` and the other three functional forms
#
#  Module-level counterparts of the four filter methods that leave the
#  original series untouched and hand back a filtered copy.
#
#  The loop above creates `exp_smooth`, `double_exp_smooth`, `decay_avg`
#  and `cum_avg` as plain functions when the module is imported, by
#  running the `FUNC_STRING` template from `_functionalize.py` through
#  `exec`. Each one copies its first argument with `Series.copy()`, calls
#  the method of the same name on the copy, and returns the copy. Since
#  all four methods return `None`, the copy is the only thing handed back.
#
#  Reach for the functional form when you need to keep the unfiltered
#  data, and for the method when you do not. Nothing else differs: the
#  filtering, and everything in the shared block at the top of this file,
#  is the same either way.
#
#  **Parameters.** The first argument is the series to filter, which is
#  read but not changed. Everything after it is handed straight to the
#  method, so the argument-order warning in the shared block applies here
#  too -- in `cum_avg(x, 0.5)` the `0.5` becomes `span`.
#
#  **Returns.** A new `Series` holding the filtered values.
#
#  **Examples.** The function copies, the method overwrites:
#
#      >>> import numpy as np
#      >>> import datapie as dp
#      >>> x = dp.Series(start=dp.qq(2020, 1),
#      ...     values=np.array([1.0, 2.0, np.nan, 4.0, 5.0]))
#      >>> y = dp.cum_avg(x)
#      >>> y.get_data()[:, 0].tolist()
#      [1.0, 1.5, 1.5, 2.3333333333333335, 3.0]
#      >>> x.get_data()[:, 0].tolist()
#      [1.0, 2.0, nan, 4.0, 5.0]
#      >>> x.cum_avg()
#      >>> x.get_data()[:, 0].tolist()
#      [1.0, 1.5, 1.5, 2.3333333333333335, 3.0]
#
#  **Notes.** The `__all__` above lists these four functions and not the
#  methods, so `from datapie import cum_avg` always gives you the copying
#  function.
#
# ==========================================================================

