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

    @_dm.reference(category="multiple", add_heading=False, )
    def overlay_by_span(
        self: Series,
        other: Series,
    ) -> None:
        r"""
................................................................................

## `overlay_by_span`

Called as `x.overlay_by_span(...)` (method form) or
`datapie.overlay_by_span(x, ...)` (function form).

==Writes the whole span of another series over this one, from the other series' first observation to its last.==

    self.overlay_by_span(other)

Everything inside that stretch comes from `other`, including the periods
where `other` has no observation. `overlay_by_observation` takes only
the periods `other` actually carries.


**Input arguments.**


???+ input "other"
    The series to lay on top. It is copied first, so it is not
    modified.


### Returns


Nothing; the series is modified in place.


### Examples


The gap in `other` wipes out the observation this series held in
2020-Q4:

    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2., 3., 4.]))
    >>> y = dp.Series(start=dp.qq(2020, 3),
    ...     values=np.array([30., np.nan, 50.]))
    >>> x.overlay_by_span(y)
    >>> x.get_data()[:, 0].tolist()
    [1.0, 2.0, 30.0, nan, 50.0]


### Algorithm


The resulting time series is determined the following way:

1. The span of the resulting series starts at the earliest start
period of the two series and ends at the latest end period of the
two series.

2. The observations from the `self` (current) time series are used
to fill the resulting time span.

3. Within the span of the `other` time series (from the first
available observation to the last available observation), the
observations from this `other` time series are superimposed on the
resulting time series, including any in-sample missing observations.


................................................................................
        """
        other_copy = other.copy()
        _bc.broadcast_variants_when_needed(self, other_copy, )
        self.set_data(other_copy.span, other_copy.data, )
        self.trim()



    @_dm.reference(category="multiple", add_heading=False, )
    def overlay_by_observation(
        self,
        other,
    ) -> None:
        r"""
................................................................................

## `overlay_by_observation`

Called as `x.overlay_by_observation(...)` (method form) or
`datapie.overlay_by_observation(x, ...)` (function form).

==Writes the observations of another series over this one period by period, only where the other series has one.==

    self.overlay_by_observation(other)

Where `other` is missing, this series keeps what it had -- the whole
difference from `overlay_by_span`, which hands the gaps over as well.


**Input arguments.**


???+ input "other"
    The series to lay on top. **Unlike the other three methods here it
    is not copied first.** If `other` holds a single variant while this
    series holds several, `other` is widened where it stands and comes
    back with more variants than it had.


### Returns


Nothing; the series is modified in place.


### Examples


The same pair as `overlay_by_span`, where the observation in 2020-Q4
now survives:

    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2., 3., 4.]))
    >>> y = dp.Series(start=dp.qq(2020, 3),
    ...     values=np.array([30., np.nan, 50.]))
    >>> x.overlay_by_observation(y)
    >>> x.get_data()[:, 0].tolist()
    [1.0, 2.0, 30.0, 4.0, 50.0]


### Algorithm


The resulting time series is determined the following way:

1. The span of the resulting series starts at the earliest start
period of the two series and ends at the latest end period of the
two series.

2. The observations from the `self` (current) time series are used
to fill the resulting time span.

3. For each period where the `other` time series has a valid
(non-missing) observation, that observation is superimposed on the
resulting time series, replacing the value from `self` at that
period.


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



    @_dm.reference(category="multiple", add_heading=False, )
    def underlay_by_span(
        self,
        other,
    ) -> None:
        r"""
................................................................................

## `underlay_by_span`

Called as `x.underlay_by_span(...)` (method form) or
`datapie.underlay_by_span(x, ...)` (function form).

==Slides another series in underneath this one, so this series wins across its whole span and `other` shows only outside it.==

    self.underlay_by_span(other)

This series keeps everything it had between its first and last
observation, its internal gaps included, and `other` reaches only the
periods before and after. `underlay_by_observation` fills those internal
gaps instead.


**Input arguments.**


???+ input "other"
    The series to lay underneath. It is not modified.


### Returns


Nothing; the series is modified in place.


### Examples


The gap this series has in 2020-Q2 stays a gap, and `other` only
reaches 2021-Q1:

    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., np.nan, 3., 4.]))
    >>> y = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([10., 20., 30., 40., 50.]))
    >>> x.underlay_by_span(y)
    >>> x.get_data()[:, 0].tolist()
    [1.0, nan, 3.0, 4.0, 50.0]


### Algorithm


The resulting time series is determined the following way:

1. The span of the resulting series starts at the earliest start
period of the two series and ends at the latest end period of the
two series.

2. The observations from the `other` time series are used to fill
the resulting time span.

3. Within the span of the `self` time series (from the first
available observation to the last available observation), the
observations from this `self` time series are superimposed on the
resulting time series, including any in-sample missing observations.


................................................................................
        """
        new_self = other.copy()
        new_self.overlay_by_span(self, )
        self._shallow_copy_data(new_self, )



    @_dm.reference(category="multiple", add_heading=False, )
    def underlay_by_observation(
        self,
        other,
    ) -> None:
        r"""
................................................................................

## `underlay_by_observation`

Called as `x.underlay_by_observation(...)` (method form) or
`datapie.underlay_by_observation(x, ...)` (function form).

==Slides another series in underneath this one period by period, so `other` shows through only where this series has no observation.==

    self.underlay_by_observation(other)

This series wins wherever it holds a value, and `other` supplies the
rest, inside the span as well as outside it.


**Input arguments.**


???+ input "other"
    The series to lay underneath. It is not modified.


### Returns


Nothing; the series is modified in place.


### Examples


The same pair as `underlay_by_span`, where the gap in 2020-Q2 is now
filled from `other`:

    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., np.nan, 3., 4.]))
    >>> y = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([10., 20., 30., 40., 50.]))
    >>> x.underlay_by_observation(y)
    >>> x.get_data()[:, 0].tolist()
    [1.0, 20.0, 3.0, 4.0, 50.0]


### Algorithm


The resulting time series is determined the following way:

1. The span of the resulting series starts at the earliest start
period of the two series and ends at the latest end period of the
two series.

2. The observations from the `other` time series are used to fill
the resulting time span.

3. For each period where the `self` time series has a valid
(non-missing) observation, that observation is superimposed on the
resulting time series, replacing the value from `other` at that
period.


................................................................................
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

