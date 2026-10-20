r"""
Broadcast functionality for time series
"""


#[

from __future__ import annotations

import numpy as _np
import documark as _dm
from .. import wrongdoings as _wrongdoings

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Self
    from .main import Series

#]


#-------------------------------------------------------------------------------
# Mixin methods
#-------------------------------------------------------------------------------


class Mixin:
    #[

    @_dm.reference(category="multiple", call_name="Series.broadcast_variants", )
    def broadcast_variants(self, num_variants, ) -> None:
        r"""
==Repeat a single variant to match a requested variant count==

#### Syntax

    series.broadcast_variants(
        num_variants,
    )

#### Input arguments

!!! input "num_variants"
    The target number of columns, as a nonnegative integer.
    Zero creates a zero-column data array.

#### Returns

!!! returns "None"
    No return value. The series is changed in place.

#### Mutation

Repeats the data columns in place, keeping dates and description unchanged.
Matching counts require no change. A different count is possible only when
the series currently has one variant.

#### Details

A series with several variants cannot be broadcast to a different count.

#### See also

`alter_num_variants`.
        """
        if self.data.shape[1] == num_variants:
            return
        if self.data.shape[1] == 1:
            self.data = _np.repeat(self.data, num_variants, axis=1, )
            return
        raise _wrongdoings.Error("Cannot broadcast variants")

    #]


#-------------------------------------------------------------------------------
# Standalone functions for use across modules
#-------------------------------------------------------------------------------


def broadcast_variants_when_needed(
    self: Series,
    other: Series,
) -> None:
    r"""
==Match two series' variant counts by repeating a single variant==

#### Syntax

    broadcast_variants_when_needed(
        series,
        other,
    )

#### Input arguments

!!! input "other"
    The second Series whose variant count is matched to the first Series.

#### Returns

!!! returns "None"
    No return value. Either series may be changed in place.

#### Mutation

If counts differ, repeats whichever series has one variant to match the
other count. Matching counts require no change. Dates and descriptions
are unchanged.

#### Details

The operation fails when counts differ and neither series has one variant.

#### See also

`broadcast_variants`.
    """
    #[
    if self.num_variants == other.num_variants:
        return
    if self.num_variants == 1:
        self.broadcast_variants(other.num_variants, )
        return
    if other.num_variants == 1:
        other.broadcast_variants(self.num_variants, )
        return
    raise _wrongdoings.Error("Cannot broadcast time series variants")
    #]



