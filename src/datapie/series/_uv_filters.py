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
        category=None,
        call_name="Univariate time series filters",
        call_name_is_code=False,
        priority=20,
    )
    def univariate_filters(self, ) -> None:
        r"""
············································································

==Carries the documentation shared by the four univariate filters in this file -- `exp_smooth`, `double_exp_smooth`, `decay_avg` and `cum_avg`.==

    self.univariate_filters()

Calling it does nothing: the body is a single `pass`. It exists only to
carry this overview in the reference documentation.

All four change the series in place and return nothing. `y =
x.cum_avg()` leaves `y` set to `None`, and the raw values in `x` are
already gone; copy with `x.copy()` first if you need them.

Missing observations inside the data are filled in, silently. Three of
the four carry the previous filtered value forward into the gap, and
`double_exp_smooth` writes its own forecast there instead.

Missing observations before the first observation are left alone. Each
filter starts at the first period holding a number and uses it
unchanged as its own starting value.

`span` can grow the series and never shrinks it. Left alone it is `...`,
the whole span currently covered; a `span` reaching past the data
extends the series permanently and moves `start` and `end`.

Every variant (column) is filtered on its own, with no information
passing between variants.

Watch where `span` sits in the argument list. It comes first in
`exp_smooth`, `decay_avg` and `cum_avg`, so in `x.exp_smooth(0.5)` the
`0.5` is taken as `span` and the call fails with `TypeError: 'float'
object is not iterable`. The functional forms hand their arguments
straight to the method, so `dp.exp_smooth(x, 0.5)` fails the same way.
Pass every argument by keyword.


### Returns


`None`, and the series is untouched.


### Examples


A `span` reaching back before the data extends the series, and the added
periods stay missing, since each filter starts at the first period that
carries an observation -- the same rule that leaves a leading gap
already in the data alone:

    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1.0, 2.0, 3.0, 4.0]))
    >>> x.cum_avg(span=dp.Span(dp.qq(2019, 3), dp.qq(2020, 4)))
    >>> x.get_data()[:, 0].tolist()
    [nan, nan, 1.0, 1.5, 2.0, 2.5]

A `span` reaching past the data extends it forward, and there the
filter does write values:

    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1.0, 2.0, 3.0, 4.0]))
    >>> x.cum_avg(span=dp.Span(dp.qq(2020, 1), dp.qq(2021, 2)))
    >>> x.get_data()[:, 0].tolist()
    [1.0, 1.5, 2.0, 2.5, 2.5, 2.5]

············································································
        """
        pass

    @_dm.reference(category="filtering")
    def exp_smooth(
        self,
        span: Span | Iterable[Period] | EllipsisType = ...,
        alpha: float = _DEFAULT_ALPHA,
    ) -> None:
        r"""
············································································

## `Series.exp_smooth`

Called as `x.exp_smooth(...)` (method form) or
`datapie.exp_smooth(x, ...)` (function form).

==Simple exponential smoothing filter. Smooths each variant of the series in place by exponentially weighted averaging.==

    self.exp_smooth(span=..., alpha=0.3)

Each filtered value is a weighted average of the current observation and
the previous filtered value, so the weight given to older data falls off
geometrically.


**Input arguments.**


???+ input "span"
    The periods to filter over. See **Univariate time series filters**
    for what `span` does, and note that it comes first here, so in
    `x.exp_smooth(0.5)` the `0.5` is taken as `span`.

???+ input "alpha"
    The weight on the current observation, so a larger value tracks the
    data more closely and smooths less. It must satisfy `0 < alpha <=
    1` or a `ValueError` is raised. Left alone it is 0.3, which smooths
    heavily; `alpha=1` returns gap-free data unchanged.


### Returns


Nothing; the series is modified in place.


### Examples


The third period has no observation, so it is filled with the previous
filtered value of 1.5 rather than left missing:

    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1.0, 2.0, np.nan, 4.0, 5.0]))
    >>> x.exp_smooth(alpha=0.5)
    >>> x.get_data()[:, 0].tolist()
    [1.0, 1.5, 1.5, 2.75, 3.875]


### Algorithm


Writing $S_t$ for the filtered value and $X_t$ for the observation, the
recursion is

$$
S_t = \alpha \, X_t + (1 - \alpha) \, S_{t-1}
$$

started at the first period that carries an observation, with $S_0 =
X_0$.


**See Also.** `dp.exp_smooth(x, alpha=0.5)` leaves `x` unchanged and
returns a filtered copy.

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

    @_dm.reference(category="filtering")
    def double_exp_smooth(
        self,
        alpha: float = _DEFAULT_ALPHA,
        beta: float = _DEFAULT_BETA,
        span: Span | Iterable[Period] | EllipsisType = ...,
    ) -> None:
        r"""
············································································

## `Series.double_exp_smooth`

Called as `x.double_exp_smooth(...)` (method form) or
`datapie.double_exp_smooth(x, ...)` (function form).

==Double exponential smoothing filter. Smooths each variant of the series in place while tracking a trend, using Holt's two-parameter method.==

    self.double_exp_smooth(alpha=0.3, beta=0.3, span=...)

It carries both a level and a slope, so unlike `exp_smooth` it follows
a rising or falling series instead of lagging behind it. The argument
order here is not the one the other three filters use: `alpha` and
`beta` come first and `span` last.


**Input arguments.**


???+ input "alpha"
    Smooths the level. It must satisfy `0 < alpha <= 1`; breaching
    either bound raises `ValueError`. Left alone it is 0.3.

???+ input "beta"
    Smooths the slope. It must satisfy `0 <= beta <= 1`, so zero is
    allowed here although it is not for `alpha`; breaching either bound
    raises `ValueError`. Left alone it is 0.3.

???+ input "span"
    The periods to filter over. See **Univariate time series filters**.
    Alone among the four filters it comes last here, not first.


Given fewer than two observations the method quietly falls back to
simple exponential smoothing.


### Returns


Nothing; the series is modified in place.


### Examples


A single missing observation does more than leave a hole. The forecast
written into the gap is fed back into the recursion as though it had
been observed, which lifts the following value to 6.0 -- above every
number in the data. Compare a series with no gap:

    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1.0, 3.0, 2.0, 5.0, 4.0]))
    >>> x.double_exp_smooth(0.5, 0.2)
    >>> x.get_data()[:, 0].tolist()
    [1.0, 3.0, 3.5, 5.1, 5.39]

against the same series with the middle observation missing:

    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1.0, 3.0, np.nan, 5.0, 4.0]))
    >>> x.double_exp_smooth(0.5, 0.2)
    >>> x.get_data()[:, 0].tolist()
    [1.0, 3.0, 5.0, 6.0, 5.9]

The second observation comes back unchanged in both, because the
starting slope is fitted to the first two observations.


### Algorithm


Holt's recursion carries a level $L_t$ and a slope $T_t$, updated as

$$
L_t = \alpha \, X_t + (1 - \alpha) \, (L_{t-1} + T_{t-1})
$$

$$
T_t = \beta \, (L_t - L_{t-1}) + (1 - \beta) \, T_{t-1}
$$

and writes the level back into the series. It starts with $L_0 = X_0$
and a slope taken from the first two observations.


**See Also.** `dp.double_exp_smooth(x, 0.5, 0.2)` leaves `x` unchanged
and returns a filtered copy.

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

    @_dm.reference(category="filtering")
    def decay_avg(
        self,
        span: Span | Iterable[Period] | EllipsisType = ...,
        decay: float = _DEFAULT_DECAY,
    ) -> None:
        r"""
············································································

## `Series.decay_avg`

Called as `x.decay_avg(...)` (method form) or
`datapie.decay_avg(x, ...)` (function form).

==Decay average filter with geometrically decaying weights. Replaces each variant of the series in place with a weighted average of every observation up to that period, weighted so that older data counts for less.==

    self.decay_avg(span=..., decay=0.9)

The weights going backwards in time are 1, `decay`, `decay` squared, and
so on, so older data fades out gradually rather than dropping out at the
edge of a fixed window.


**Input arguments.**


???+ input "span"
    The periods to filter over. See **Univariate time series filters**
    for what `span` does, and note that it comes first here, so in
    `x.decay_avg(0.5)` the `0.5` is taken as `span`.

???+ input "decay"
    Sets how fast the past fades, and higher values keep more of it.
    The check is `0 < decay <= 1`, so `decay=1` is accepted and
    silently gives the plain cumulative average of `cum_avg`, while
    `decay=0` raises `ValueError`. Left alone it is 0.9.


### Returns


Nothing; the series is modified in place.


### Examples


Across the gap in the third period the previous value is repeated, and
the weight carried by the past is scaled down by `decay` even though no
new observation arrived. Values are rounded here only to keep the line
short:

    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1.0, 2.0, np.nan, 4.0, 5.0]))
    >>> x.decay_avg(decay=0.9)
    >>> [round(v, 4) for v in x.get_data()[:, 0].tolist()]
    [1.0, 1.5263, 1.5263, 2.5006, 3.2614]


### Algorithm


Writing $\delta$ for the `decay`,

$$
DA_t = \frac{X_t + \delta \, DA_{t-1} \, N_{t-1}}{1 + \delta \, N_{t-1}}
$$

where $N_t = 1 + \delta \, N_{t-1}$ is the effective number of
observations behind the current value, started at the first observed
period with $DA_0 = X_0$ and $N_0 = 1$.


**See Also.** `cum_avg` does the same thing as `decay_avg(decay=1)`.
`dp.decay_avg(x, decay=0.9)` leaves `x` unchanged and returns a
filtered copy.

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

    @_dm.reference(category="filtering")
    def cum_avg(
        self,
        span: Span | Iterable[Period] | EllipsisType = ...,
    ) -> None:
        r"""
············································································

## `Series.cum_avg`

Called as `x.cum_avg(...)` (method form) or
`datapie.cum_avg(x, ...)` (function form).

==Cumulative average filter. Replaces each variant of the series in place with the running mean of all observations up to and including each period.==

    self.cum_avg(span=...)

The divisor is the number of observations seen, not the number of
periods elapsed, and the two part company as soon as there is a gap.


**Input arguments.**


???+ input "span"
    The periods to filter over. See **Univariate time series filters**.
    There are no other arguments.


### Returns


Nothing; the series is modified in place.


### Examples


The third period has no observation, so the running mean does not move.
The fourth then divides a total of 7.0 by the three observations seen,
not by the four periods elapsed:

    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1.0, 2.0, np.nan, 4.0, 5.0]))
    >>> x.cum_avg()
    >>> x.get_data()[:, 0].tolist()
    [1.0, 1.5, 1.5, 2.3333333333333335, 3.0]


### Algorithm


With no gaps,

$$
CA_t = \frac{X_1 + X_2 + \cdots + X_t}{t}
$$

Once there is a gap the divisor is the number of observations seen
rather than $t$, which is what the example above shows.


**See Also.** `decay_avg(decay=1)` does exactly the same thing.
`dp.cum_avg(x)` leaves `x` unchanged and returns a filtered copy.

············································································
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

__all__ = tuple(_functional_forms)

