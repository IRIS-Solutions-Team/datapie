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
        """
        Broadcast variants to match the specified number of variants
        """
        if self.data.shape[1] == num_variants:
            return
        if self.data.shape[1] == 1:
            self.data = _np.repeat(self.data, num_variants, axis=1, )
            return
        raise _wrongdoings.Error("Cannot broadcast variants")

    # ==========================================================================
    #  ### `broadcast_variants(num_variants)`
    #
    #  Copies the single variant of a time series out into `num_variants`
    #  identical variants.
    #
    #  A variant is one column of the series, and operations that combine
    #  two series need both of them to carry the same number of columns.
    #  This is how a series holding one variant is widened to meet another.
    #
    #  **Parameters.** `num_variants` is a plain count, not another series.
    #  The series must hold a single variant, or already hold
    #  `num_variants` of them, in which case nothing happens. Any other
    #  count raises `wrongdoings.Error`; the method never shrinks a series
    #  to a smaller positive count.
    #
    #  **Returns.** Nothing; the series is modified in place.
    #
    #  **Examples.** One variant widened into three:
    #
    #      >>> import datapie as dp
    #      >>> import numpy as np
    #      >>> x = dp.Series(start=dp.qq(2020, 1),
    #      ...     values=np.array([1.0, 2.0]))
    #      >>> x.broadcast_variants(3)
    #      >>> x.get_data().tolist()
    #      [[1.0, 1.0, 1.0], [2.0, 2.0, 2.0]]
    #
    # ==========================================================================

    #]


#-------------------------------------------------------------------------------
# Standalone functions for use across modules
#-------------------------------------------------------------------------------


def broadcast_variants_when_needed(
    self: Series,
    other: Series,
) -> None:
    r"""
    Broadcast variants between two Series objects if needed
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


# ==========================================================================
#  ### `broadcast_variants_when_needed(self, other)`
#
#  Gives two time series the same number of variants by widening whichever
#  of them holds a single variant.
#
#  Use it before combining two series, when you do not know in advance
#  which of the two is the single-variant one.
#
#  **Parameters.** `self` and `other` are the two series to reconcile.
#  Either one may be modified in place, `other` included, so a series
#  passed in as the second argument can come back wider than it went in.
#  Matching counts are left alone. If both series hold more than one
#  variant and the counts differ, `wrongdoings.Error` is raised.
#
#  **Returns.** Nothing; the widening happens in place.
#
#  **Examples.** The second argument is the one that changes here:
#
#      >>> import numpy as np
#      >>> import datapie as dp
#      >>> from datapie.series import _broadcasts
#      >>> x = dp.Series(start=dp.qq(2020, 1),
#      ...     values=np.array([[1.0, 2.0], [3.0, 4.0]]))
#      >>> y = dp.Series(start=dp.qq(2020, 1),
#      ...     values=np.array([1.0, 2.0]))
#      >>> _broadcasts.broadcast_variants_when_needed(x, y)
#      >>> y.num_variants
#      2
#
# ==========================================================================

