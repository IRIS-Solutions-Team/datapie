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


    #[

    @_dm.reference(category="multiple", )
    def overlay_by_span(
        self: Series,
        other: Series,
    ) -> None:
        r"""
==Overlay another series, including its internal missing values==

#### Syntax

Method form:

    series.overlay_by_span(
        other,
    )

Function form:

    new_series = datapie.overlay_by_span(
        series,
        other,
    )

#### Input arguments

!!! input "series"
    The receiving series, or the source to copy in the function form.

!!! input "other"
    The series whose whole span takes precedence, at the same frequency.
    Required; there are no optional arguments. Variant counts must match,
    or one series must have a single variant that can be repeated to match
    the other.

#### Returns

!!! returns "None — method form"
    Method form: no return value; the receiving series is changed in place.

!!! returns "new_series — function form"
    Function form: a combined copy of `series`, leaving `series` unchanged.

#### Mutation

The method updates the receiver's data and may extend its span or repeat
its single variant. `other` is copied before variant broadcasting and is
not changed. The function form leaves both input series unchanged.
The receiver's description is retained.

#### Details

Values from `other` replace every observation within its span, including
internal missing values. Outside that span, the receiver's values remain.
The combined span covers both inputs, then rows missing in all variants
are trimmed from both ends. Internal missing rows are not trimmed.

#### See also

[`overlay_by_observation`](#overlay_by_observation),
[`underlay_by_span`](#underlay_by_span),
[`underlay_by_observation`](#underlay_by_observation).
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

#### Syntax

Method form:

    series.overlay_by_observation(
        other,
    )

Function form:

    new_series = datapie.overlay_by_observation(
        series,
        other,
    )

#### Input arguments

!!! input "series"
    The receiving series, or the source to copy in the function form.

!!! input "other"
    The series whose nonmissing observations take precedence, at the same frequency.
    Required; there are no optional arguments. Variant counts must match,
    or one series must have a single variant that can be repeated to match
    the other.

#### Returns

!!! returns "None — method form"
    Method form: no return value; the receiving series is changed in place.

!!! returns "new_series — function form"
    Function form: a combined copy of `series`, leaving `series` unchanged.
    The function can still change `other` as described below.

#### Mutation

The method updates the receiver's data and may extend its span or repeat
its single variant. When both series are nonempty, broadcasting also
repeats `other` in place if it has a single variant and the receiver has
several. This can change `other` in both method and function forms.
Pass a copy of `other` to avoid that side effect.
The receiver's description is retained.

#### Details

Only nonmissing observations from `other` replace the receiver's values.
Missing observations in `other` leave the receiver's observations intact.
The result covers both spans and is not trimmed at the ends.
An empty `other` leaves the receiver unchanged; an empty receiver takes
a copy of `other`'s start and data without variant broadcasting.

#### See also

[`overlay_by_span`](#overlay_by_span),
[`underlay_by_span`](#underlay_by_span),
[`underlay_by_observation`](#underlay_by_observation).
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

#### Syntax

Method form:

    series.underlay_by_span(
        other,
    )

Function form:

    new_series = datapie.underlay_by_span(
        series,
        other,
    )

#### Input arguments

!!! input "series"
    The receiving series, or the source to copy in the function form.

!!! input "other"
    The underlying series, at the same frequency.
    Required; there are no optional arguments. Variant counts must match,
    or one series must have a single variant that can be repeated to match
    the other.

#### Returns

!!! returns "None — method form"
    Method form: no return value; the receiving series is changed in place.

!!! returns "new_series — function form"
    Function form: a combined copy of `series`, leaving `series` unchanged.

#### Mutation

The method replaces the receiver's data and may extend its span or repeat
its single variant. `other` is copied and is not changed. The function
form leaves both inputs unchanged. The receiver's description is retained.

#### Details

The receiver's whole span takes precedence, including internal missing
values: observations from `other` are used only outside that span.
The combined span covers both inputs, then rows missing in all variants
are trimmed from both ends. Internal missing rows are not trimmed.

#### See also

[`overlay_by_span`](#overlay_by_span),
[`overlay_by_observation`](#overlay_by_observation),
[`underlay_by_observation`](#underlay_by_observation).
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

#### Syntax

Method form:

    series.underlay_by_observation(
        other,
    )

Function form:

    new_series = datapie.underlay_by_observation(
        series,
        other,
    )

#### Input arguments

!!! input "series"
    The receiving series, or the source to copy in the function form.

!!! input "other"
    The underlying series, at the same frequency.
    Required; there are no optional arguments. Variant counts must match,
    or one series must have a single variant that can be repeated to match
    the other.

#### Returns

!!! returns "None — method form"
    Method form: no return value; the receiving series is changed in place.

!!! returns "new_series — function form"
    Function form: a combined copy of `series`, leaving `series` unchanged.

#### Mutation

The method replaces the receiver's data and may extend its span or repeat
its single variant. Internally, a copy of `other` overlays the receiver's
observations; this step can broadcast the receiver itself before its data
are replaced. `other` is not changed. The function form first copies
`series`, so both input series are unchanged even when broadcasting occurs.
The receiver's description is retained.

#### Details

Nonmissing receiver observations are preserved. Missing positions and
periods outside the receiver's span are filled from `other`.
The result covers both spans and is not trimmed at the ends.
An empty `other` leaves the receiver's start and values unchanged;
an empty receiver takes a copy of `other`'s start and data.

#### See also

[`overlay_by_span`](#overlay_by_span),
[`overlay_by_observation`](#overlay_by_observation),
[`underlay_by_span`](#underlay_by_span).
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

