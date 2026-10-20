r"""
"""


#[

from __future__ import annotations

from typing import Literal
import documark as _dm
import numpy as _np

from .. import periods as _periods
from . import _broadcasts as _bc
from ._functionalize import FUNC_STRING

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .main import Series

#]


LayMethod = Literal["by_span", "by_observation"]


#-------------------------------------------------------------------------------
# Mixin methods
#-------------------------------------------------------------------------------


class Mixin:

    @staticmethod
    @_dm.topic(title="Overlay and underlay", anchor="overlay-and-underlay", priority=130)
    def _overlay_underlay_reference():
        r"""
==Combine two series using span or observation precedence==

### Syntax

#### Method form

    series.overlay_by_span(other)
    series.overlay_by_observation(other)
    series.underlay_by_span(other)
    series.underlay_by_observation(other)

#### Function form

    new_series = datapie.overlay_by_span(series, other)
    new_series = datapie.overlay_by_observation(series, other)
    new_series = datapie.underlay_by_span(series, other)
    new_series = datapie.underlay_by_observation(series, other)

### Input arguments

!!! input "series"

    The series to combine with `other`.

!!! input "other"

    The other series, at the same frequency. A single variant can be repeated to match a series with several variants.

### Method form returns

!!! returns "None"

    The receiving series is changed in place.

### Function form returns

!!! returns "new_series"

    A combined copy of `series`. The input `series` is unchanged; the note below describes a possible change to `other`.

Overlay gives `other` precedence; underlay preserves the receiving series instead. The span-based methods preserve the preferred series' whole span, including its internal missing values. The observation-based methods preserve only its nonmissing observations and fill the remaining positions from the other series.

??? note "Details"

    The combined result covers both series' spans, with missing rows at the ends removed by the span-based methods.

    `overlay_by_observation` may change `other` by repeating its single variant to match a receiving series with several variants. The other three operations copy `other` before combining the data.
        """
        pass

    #[

    @_dm.reference(category="multiple", )
    def overlay_by_span(
        self: Series,
        other: Series,
    ) -> None:
        r"""
==Overlay another series, including its internal missing values==

#### See also

[Overlay and underlay](#overlay-and-underlay)
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
==Overlay the available observations of another series==

#### See also

[Overlay and underlay](#overlay-and-underlay)
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
        encompassing_span, *from_until = _periods.get_encompassing_span(self, other)
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
==Underlay another series while preserving the current span==

#### See also

[Overlay and underlay](#overlay-and-underlay)
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
==Fill missing observations from an underlying series==

#### See also

[Overlay and underlay](#overlay-and-underlay)
        """
        new_self = other.copy()
        new_self.overlay_by_observation(self)
        self._shallow_copy_data(new_self)


    #]


#-------------------------------------------------------------------------------
# Functional forms
#-------------------------------------------------------------------------------


_functional_forms = {
    "overlay_by_span",
    "overlay_by_observation",
    "underlay_by_span",
    "underlay_by_observation",
}

for n in _functional_forms:
    code = FUNC_STRING.format(n=n, )
    exec(code, globals(), locals(), )

__all__ = tuple(_functional_forms)

