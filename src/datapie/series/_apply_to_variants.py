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
        """
        ············································································

        ==Apply a function to each variant (column) of a time series==

        Apply a user-defined function to each column (variant) of the time series
        separately. The function receives the periods and values for each variant
        and returns new values with the same number of elements. The original
        time series is modified in-place.

        ### Input arguments ###

        ???+ input "func"
        A function that takes two input arguments:
        - periods: tuple of Period objects
        - values: numpy array of values for one variant
        Returns a numpy array of new values with the same length as the input.

        ???+ input "span"
        Time span to apply the function to. If `span=...` (default), uses the
        full span of the time series.

        ???+ input "**kwargs"
        Additional keyword arguments passed to the function.

        ### Returns ###

        ???+ returns "None"
        This method modifies `self` in-place and does not return a value.

        ············································································
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
        for i, variant_data in enumerate(self.iter_own_data_variants_from_until(from_until)):
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
        """
        Create an extended data array to cover the requested span.

        Always creates a copy of the data array. If the requested span extends
        before or after the current data span, the array is extended with NaN
        values using concatenation for performance.

        ### Input arguments ###

        ???+ input "start_period"
        The requested start period for the span.

        ???+ input "end_period"
        The requested end period for the span.

        ### Returns ###

        ???+ returns "tuple[np.ndarray, tuple[Period, ...]]"
        A tuple containing the extended data array and the tuple of extended periods.
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

