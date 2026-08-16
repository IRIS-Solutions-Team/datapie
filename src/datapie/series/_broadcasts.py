r"""
Broadcast functionality for time series
"""


#[

from __future__ import annotations

import numpy as _np
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

    def broadcast_variants(self, num_variants, ) -> None:
        r"""
................................................................................

## `broadcast_variants`

==Copies the single variant of a time series out into `num_variants` identical variants.==

    self.broadcast_variants(num_variants)

A variant is one column. Operations that combine two series need both to
carry the same number of columns.


**Input arguments.**


???+ input "num_variants"
    A plain count, not another series. Nothing happens when the series
    already holds that many. Otherwise it must hold exactly one variant,
    or `wrongdoings.Error` is raised; the method never shrinks.


### Returns


Nothing; the series is modified in place.


### Examples


One variant widened into three:

    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1.0, 2.0]))
    >>> x.broadcast_variants(3)
    >>> x.get_data().tolist()
    [[1.0, 1.0, 1.0], [2.0, 2.0, 2.0]]

................................................................................
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
................................................................................

## `broadcast_variants_when_needed`

==Gives two time series the same number of variants by widening whichever of them holds a single variant.==

    broadcast_variants_when_needed(self, other)

For combining two series when you do not know which of the two holds the
single variant. Matching counts are left alone; if both hold more than
one variant and the counts differ, `wrongdoings.Error` is raised.


**Input arguments.**


???+ input "self"
    One of the two series to reconcile. It is widened in place when it
    holds a single variant and `other` holds more.

???+ input "other"
    The other series to reconcile. It is widened in place on the same
    terms, so a series passed in as the second argument can come back
    wider than it went in.


### Returns


Nothing; the widening happens in place.


### Examples


The second argument is the one that changes here:

    >>> import numpy as np
    >>> import datapie as dp
    >>> from datapie.series import _broadcasts
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([[1.0, 2.0], [3.0, 4.0]]))
    >>> y = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1.0, 2.0]))
    >>> _broadcasts.broadcast_variants_when_needed(x, y)
    >>> y.num_variants
    2

................................................................................
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



