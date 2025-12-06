r"""
"""


#[

from __future__ import annotations

from typing import Literal
import documark as _dm
import numpy as _np

from .. import dates as _dates
from . import _broadcasts as _bc

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .main import Series

#]


__all__ = ()


LayMethod = Literal["by_span", "by_observation"]


def mixin(klass: type, ) -> type:
    r"""
    Inlay the steady state methods in the class
    """
    #[
    klass.overlay_by_span = overlay_by_span
    klass.overlay_by_observation = overlay_by_observation
    klass.underlay_by_span = underlay_by_span
    klass.underlay_by_observation = underlay_by_observation
    return klass
    #]


#-------------------------------------------------------------------------------
# Functions to be used as methods in Series class
#-------------------------------------------------------------------------------


@_dm.reference(category="multiple", )
def overlay_by_span(
    self: Series,
    other: Series,
) -> None:
    r"""
................................................................................

==Overlay the current series with another series by span==

Overlay the values of another time series onto the current time series on the
entire span of the other time series, i.e. from the start to the end period
regardless of missing in-sample values.


    self.overlay_by_span(other, )


### Input arguments ###

???+ input "self"
    The current time series object.

???+ input "other"
    The time series object whose values will be overlaid onto the current time
    series.

???+ input "method"
    The method to use for overlaying the values. The default (and currently the
    only available) method is `"by_span"`.


### Returns ###

This method modifies `self` in place and returns `None`.


### Details ###

???+ abstract "Algorithm"

    The resulting time series is determined the following way:

    1. The span of the resulting series starts at the earliest start period of the two
    series and ends at the latest end period of the two series.

    2. The observations from the `self` (current) time series used to fill the
    resulting time span.

    3. Within the span of the `other` time series (from the first available
    observation to the last available observation), the observations from this
    `other` time series are superimposed on the resulting time series, including any
    in-sample missing observations.

................................................................................
    """
    other_copy = other.copy()
    _bc.broadcast_variants_when_needed(self, other_copy, )
    self.set_data(other_copy.span, other_copy.data, )
    self.trim()


@_dm.reference(category="multiple", )
def overlay_by_observation(
    self,
    other,
) -> None:
    r"""
................................................................................

==Overlay the current series with another series by observation==

Overlay the values of another time series onto the current time series
observation by observation, only where the other time series has valid
(non-missing) observations.

    self.overlay_by_observation(other, )


### Input arguments ###

???+ input "self"
    The current time series object.

???+ input "other"
    The time series object whose values will be overlaid onto the current time
    series.


### Returns ###

This method modifies `self` in place and returns `None`.


### Details ###

???+ abstract "Algorithm"

    The resulting time series is determined the following way:

    1. The span of the resulting series starts at the earliest start period of the two
    series and ends at the latest end period of the two series.

    2. The observations from the `self` (current) time series are used to fill the
    resulting time span.

    3. For each period where the `other` time series has a valid (non-missing)
    observation, that observation is superimposed on the resulting time series,
    replacing the value from `self` at that period.

................................................................................
    """
    # Handle empty series cases
    if self.is_empty and other.is_empty:
        return
    #
    if self.is_empty:
        self.start = other.start
        self.data = _np.array(other.data)
        return
    #
    if other.is_empty:
        return
    #
    # Broadcast variants if needed
    _bc.broadcast_variants_when_needed(self, other)
    #
    # Get encompassing span and from_until tuple for data extraction
    encompassing_span, *from_until = _dates.get_encompassing_span(self, other)
    #
    # Get data for both series over the encompassing span
    self_data = self.get_data_from_until(from_until)
    other_data = other.get_data_from_until(from_until)
    #
    # Create boolean indices for non-NaN values
    other_valid = ~_np.isnan(other_data)
    #
    # For overlay: use other's values where other has valid data
    result_data = _np.array(self_data)
    result_data[other_valid] = other_data[other_valid]
    #
    # Set the result data directly
    self.start = encompassing_span.start
    self.data = result_data


@_dm.reference(category="multiple", )
def underlay_by_span(
    self,
    other,
) -> None:
    r"""
................................................................................

==Underlay the current series with another series by span==

Underlay the values of another time series beneath the current time series on
the entire span of the other time series, i.e. from the start to the end period
regardless of missing in-sample values.

    self.underlay_by_span(other, )


### Input arguments ###

???+ input "self"
    The current time series object.

???+ input "other"
    The time series object whose values will be underlaid beneath the current
    time series.

???+ input "method"
    The method to use for underlaying the values. The default (and currently the
    only available) method is `"by_span"`.


### Returns ###

This method modifies `self` in place and returns `None`.


### Details ###

???+ abstract "Algorithm"
    The resulting time series is determined the following way:

    1. The span of the resulting series starts at the earliest start period of the two
    series and ends at the latest end period of the two series.

    2. The observations from the `other` time series used to fill the
    resulting time span.

    3. Within the span of the `self` time series (from the first available
    observation to the last available observation), the observations from this
    `self` time series are superimposed on the resulting time series, including any
    in-sample missing observations.

................................................................................
    """
    new_self = other.copy()
    new_self.overlay_by_span(self, )
    self._shallow_copy_data(new_self, )


@_dm.reference(category="multiple", )
def underlay_by_observation(
    self,
    other,
) -> None:
    r"""
................................................................................

==Underlay the current series with another series by observation==

Underlay the values of another time series beneath the current time series
observation by observation, only where the current time series has missing
observations.

    self.underlay_by_observation(other, )


### Input arguments ###

???+ input "self"
    The current time series object.

???+ input "other"
    The time series object whose values will be underlaid beneath the current
    time series.


### Returns ###

This method modifies `self` in place and returns `None`.


### Details ###

???+ abstract "Algorithm"

    The resulting time series is determined the following way:

    1. The span of the resulting series starts at the earliest start period of the two
    series and ends at the latest end period of the two series.

    2. The observations from the `other` time series are used to fill the
    resulting time span.

    3. For each period where the `self` time series has a valid (non-missing)
    observation, that observation is superimposed on the resulting time series,
    replacing the value from `other` at that period.

................................................................................
    """
    new_self = other.copy()
    new_self.overlay_by_observation(self)
    self._shallow_copy_data(new_self)


#-------------------------------------------------------------------------------


FUNCTIONAL_FORMS = (
    "overlay_by_span",
    "overlay_by_observation",
    "underlay_by_span",
    "underlay_by_observation",
)

