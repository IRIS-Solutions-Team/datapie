"""
Apply functions to individual time series variants (columns)
"""


#[

from __future__ import annotations

from typing import Callable, Any
from collections.abc import Iterable
from types import EllipsisType
import numpy as _np

from .. import periods as _periods
from ..periods import Period, Span

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .main import Series

#]


class Mixin:
    """
    Mixin class to add _apply_to_variants functionality to Series
    """

    def _apply_to_variants(
        self,
        func: Callable[[tuple[Period, ...], _np.ndarray], _np.ndarray],
        *,
        span: Span | Iterable[Period] | EllipsisType = ...,
        **kwargs: Any,
    ) -> None:
        r"""
················································································

## `_apply_to_variants`

==Runs a function over each variant of the series in turn, replacing that variant's values with what the function returns.==

    self._apply_to_variants(
        func,
        *,
        span=...,
        **kwargs,
    )

This is the engine under the four filters in `_uv_filters.py` --
`exp_smooth`, `double_exp_smooth`, `decay_avg` and `cum_avg` -- and is
not part of the public interface. Each of them supplies its own `func`
and passes `span` straight through.

The series is extended to cover `span` before the function runs, so a
`span` reaching outside the data grows the series permanently and moves
`start` and `end`. It is never shrunk.


**Input arguments.**


???+ input "func"
    Called once per variant, as `func(periods, values, **kwargs)`.
    `periods` is a tuple of `Period` objects covering the span and
    `values` is a one-dimensional array of that variant's values, the two
    always the same length. It must return a numpy array of exactly the
    same shape; anything else raises, and see the warning below about
    what state the series is left in when it does.

???+ input "span"
    The stretch of periods to work over. Left as `...` it is the whole
    span the series currently covers. An empty span returns immediately
    and changes nothing.

???+ input "**kwargs"
    Passed on to `func` unchanged.


**The series is modified before `func` is validated.** The extended data
and the new start are written onto the object first, and only then is
`func` called and its result checked. So when `func` returns the wrong
type or the wrong shape, the exception leaves behind a series that has
already been extended and re-dated: a four-period series given a span
reaching two periods earlier comes back with six periods starting two
periods earlier, padded with missing values, even though the call
failed. Catching the exception does not undo it. Copy the series first
if that matters.

An integer-typed series cannot be extended at all: the padding is built
with `numpy.nan` in the series' own dtype, which raises
`ValueError: cannot convert float NaN to integer` after a
`RuntimeWarning: invalid value encountered in cast`.


### Returns


Nothing; the series is modified in place.


### Examples


Doubling every value, over the span the series already covers:

    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2., 3., 4.]))
    >>> x._apply_to_variants(lambda periods, values: values * 2)
    >>> x.get_data()[:, 0].tolist()
    [2.0, 4.0, 6.0, 8.0]

A failing `func` still leaves the series extended:

    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2., 3., 4.]))
    >>> try:
    ...     x._apply_to_variants(lambda periods, values: "not an array",
    ...         span=dp.Span(dp.qq(2019, 3), dp.qq(2020, 4)))
    ... except TypeError:
    ...     pass
    >>> x.start, x.num_periods
    (qq(2019,3), 6)

················································································
        """
        # Resolve the span to work with
        span = self.resolve_periods(span)

        if not span:
            # Empty span, nothing to do
            return

        # Get the start and end periods for the span
        start_period = min(span)
        end_period = max(span)

        # Create tuple of Period objects for the span
        periods_tuple = _periods.periods_from_until(start_period, end_period)

        # Create extended data array if necessary
        extended_data, extended_periods = self._create_extended_data_array(start_period, end_period)

        # Update the series with the extended data
        self.data = extended_data
        self.start = extended_periods[0]

        # Create from_until tuple for data extraction
        from_until = (start_period, end_period)

        # Calculate positions in the (potentially extended) data array
        start_pos = start_period - self.start
        end_pos = end_period - self.start + 1

        # Apply function to each variant (column) and assign back directly
        for i, variant_data, in enumerate(self.iter_own_data_variants_from_until(from_until)):
            # Apply the function to this variant
            new_variant_data = func(periods_tuple, variant_data, **kwargs)

            # Validate that the function returned a numpy array
            if not isinstance(new_variant_data, _np.ndarray):
                raise TypeError(
                    f"Function must return a numpy array, got {type(new_variant_data)}"
                )

            # Validate that the function returned the correct shape
            if new_variant_data.shape != variant_data.shape:
                raise ValueError(
                    f"Function must return the same number of elements as input. "
                    f"Expected shape {variant_data.shape}, got {new_variant_data.shape}"
                )

            # Assign directly to the column in the original data
            self.data[start_pos:end_pos, i] = new_variant_data

    def _create_extended_data_array(
        self,
        start_period: Period,
        end_period: Period,
    ) -> tuple[_np.ndarray, tuple[Period, ...]]:
        r"""
················································································

## `_create_extended_data_array`

==Builds a copy of the series data padded out to cover a requested span, and the periods that copy runs over.==

    extended_data, extended_periods = self._create_extended_data_array(
        start_period,
        end_period,
    )

Used by `_apply_to_variants` to make room before a function is applied.
It reads the series and returns new objects; nothing is assigned back
here, and the caller decides what to do with them.

The array is **always** copied, even when no padding is needed, so the
caller never writes through to the series' own data by accident.


**Input arguments.**


???+ input "start_period"
    The first period the result has to cover. If it is later than the
    series' own start, nothing is added at the front -- the array is
    never trimmed to it.

???+ input "end_period"
    The last period the result has to cover, on the same terms at the
    back.


Padding is filled with `numpy.nan` **in the series' own dtype**. For a
float series that is what it appears to be; for an integer series the
cast fails, raising `ValueError: cannot convert float NaN to integer`
after a `RuntimeWarning: invalid value encountered in cast`.


### Returns


A pair. The first entry is the padded copy of the data, one column per
variant. The second is a tuple of the `Period` objects its rows run
over, which starts earlier than the series only if padding was added at
the front.


### Examples


Reaching two periods back adds two missing rows and reports the widened
span, leaving the series itself untouched:

    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2.]))
    >>> data, periods = x._create_extended_data_array(
    ...     dp.qq(2019, 3), dp.qq(2020, 2))
    >>> data[:, 0].tolist()
    [nan, nan, 1.0, 2.0]
    >>> periods[0], x.start
    (qq(2019,3), qq(2020,1))

················································································
        """
        # Check if we need to extend the data array
        current_start = self.start
        current_end = self.end

        extend_before = max(0, current_start - start_period)
        extend_after = max(0, end_period - current_end)

        # Always create a copy of the data array
        extended_data = _np.array(self.data)
        new_start = current_start
        new_end = current_end

        # Need to extend the data array
        num_variants = self.data.shape[1]

        # Create extension arrays filled with NaN
        if extend_before > 0:
            before_array = _np.full((extend_before, num_variants), _np.nan, dtype=self.data.dtype)
            extended_data = _np.concatenate([before_array, extended_data], axis=0)
            new_start = start_period

        if extend_after > 0:
            after_array = _np.full((extend_after, num_variants), _np.nan, dtype=self.data.dtype)
            extended_data = _np.concatenate([extended_data, after_array], axis=0)
            new_end = end_period

        # Create the tuple of extended periods
        extended_periods = _periods.periods_from_until(new_start, new_end)

        return extended_data, extended_periods

