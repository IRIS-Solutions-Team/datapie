"""
Univariate time series filters
"""


#[

from __future__ import annotations

from numbers import Real
from collections.abc import Iterable, Callable
from types import EllipsisType
from typing import Self, Literal
import numpy as _np
import documark as _dm

from ..periods import Period
from ..frequencies import Frequency
from .. import periods as _periods

from ._functionalize import FUNC_STRING

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .main import Series

#]


_DEFAULT_FILTER_INFORMATION = "two_sided"

_AUTO_SMOOTH = {
    Frequency.YEARLY: (10*1)**2,
    Frequency.HALFYEARLY: (10*2)**2,
    Frequency.QUARTERLY: (10*4)**2,
    Frequency.MONTHLY: (10*12)**2,
    "default": (10*4)**2,
}


def _get_default_smooth(frequency, ):
    """
    Default smoothing parameter (lambda)
    """
    return _AUTO_SMOOTH.get(frequency, _AUTO_SMOOTH["default"])


class _ConstrainedHodrickPrescottFilter:
    """
    """
    #[
    def __init__(
        self,
        num_periods: int,
        smooth: Real,
        #
        level_where: list[int] | None = None,
        change_where: list[int] | None = None,
        information: Literal["two_sided", "one_sided"] = _DEFAULT_FILTER_INFORMATION,
    ) -> None:
        self._num_periods = num_periods
        self._smooth = smooth
        self._num_extra_rows = 0
        self._create_plain_filter_matrix()
        self._add_level_constraints(level_where, )
        self._add_change_constraints(change_where, )
        self.filter_data = getattr(self, f"filter_data_{information}", )

    def filter_data_two_sided(
        self,
        data: _np.ndarray,
        #
        level_data: _np.ndarray | None = None,
        change_data: _np.ndarray | None = None,
    ) -> tuple[_np.ndarray, _np.ndarray]:
        r"""
        """
        F = self._add_eye_for_observations(data, )
        extended_data = self._extend_data(data, level_data, change_data, )
        enforced_zeros_where = _np.where(_np.isnan(data, ))
        extended_data[enforced_zeros_where] = 0
        trend_data = _np.linalg.solve(F, extended_data, )
        extended_data[enforced_zeros_where] = _np.nan
        gap_data = extended_data - trend_data
        if self._num_extra_rows > 0:
            trend_data = trend_data[:-self._num_extra_rows, :]
            gap_data = gap_data[:-self._num_extra_rows, :]
        return trend_data, gap_data

    def filter_data_one_sided(
        self,
        data: _np.ndarray,
        #
        level_data: _np.ndarray | None = None,
        change_data: _np.ndarray | None = None,
    ) -> tuple[_np.ndarray, _np.ndarray]:
        """
        """
        # Implement the one-sided version of the filter by looping through the
        # data and applying the two-sided filter to the data up to the current
        # period. This is not the most efficient way to implement the one-sided
        # filter, but it is straightforward and works correctly. However, keep
        # the level and change constraints affective in each iteration.
        #
        # Initialize trend and gap data as arrays with NaNs
        trend_data = _np.full_like(data, _np.nan, )
        gap_data = _np.full_like(data, _np.nan, )
        #
        for i in range(self._num_periods, ):
            data_up_to_i = _np.array(data, )
            data_up_to_i[i+1:] = _np.nan
            # Keep level and change constraints unchanged on the entire horizon;
            # we want to apply even the "future" constraints in each iteration
            # even though this is a one-sided filter.
            #
            trend_data_up_to_i, gap_data_up_to_i, = self.filter_data_two_sided(
                data_up_to_i,
                level_data=level_data,
                change_data=change_data,
            )
            trend_data[i,:] = trend_data_up_to_i[i,:]
            gap_data[i,:] = gap_data_up_to_i[i,:]
        #
        return trend_data, gap_data,

    def _add_eye_for_observations(
        self,
        data: _np.ndarray,
    ) -> None:
        """
        Add 1 to the F diagonal for each row where an observation is available
        """
        #[
        F = _np.array(self._F, )
        quasi_eye = _np.diag(_np.float64(~_np.isnan(data.flatten(), )))
        F[:self._num_periods, :self._num_periods] += quasi_eye
        return F
        #]

    def _extend_data(
        self,
        data: _np.ndarray,
        level_data: _np.ndarray | None,
        change_data: _np.ndarray | None,
    ) -> _np.ndarray:
        """
        """
        extended_data = data.copy() if data.ndim > 1 else data.copy().reshape(-1, 1)
        tile_dim = (1, extended_data.shape[1], )
        if level_data is not None:
            extended_data = _np.vstack((extended_data, _np.tile(level_data, tile_dim), ), )
        if change_data is not None:
            extended_data = _np.vstack((extended_data, _np.tile(change_data, tile_dim), ), )
        return extended_data

    def _create_plain_filter_matrix(self, ) -> None:
        """
        """
        K = _np.zeros((self._num_periods-2, self._num_periods), dtype=float)
        for i in range(self._num_periods-2):
            K[i,i] = 1
            K[i,i+2] = 1
        for i in range(self._num_periods-2):
            K[i,i+1] = -2
        self._F = self._smooth * (K.T @ K)

    def _add_level_constraints(self, level_where: list[int], ):
        if not level_where:
            return
        num_constraints = len(level_where)
        self._num_extra_rows += num_constraints
        extra_rows = _np.zeros((num_constraints, self._num_periods, ), dtype=float)
        extra_variants = _np.zeros((self._num_periods + num_constraints, num_constraints, ), dtype=float)
        for i, j in enumerate(level_where, ):
            extra_rows[i, j] = 1
            extra_variants[j, i] = 1
        self._F = _np.vstack((self._F, extra_rows, ))
        self._F = _np.hstack((self._F, extra_variants, ))

    def _add_change_constraints(self, change_where: list[int], ):
        if not change_where:
            return
        num_constraints = len(change_where)
        extra_rows = _np.zeros((num_constraints, self._F.shape[1], ), dtype=float, )
        extra_variants = _np.zeros((self._F.shape[0] + num_constraints, num_constraints, ), dtype=float, )
        for i, j in enumerate(change_where, ):
            extra_rows[i, [j-1, j]] = (-1, 1)
            extra_variants[[j-1, j], i] = (-1, 1)
        self._F = _np.vstack((self._F, extra_rows, ))
        self._F = _np.hstack((self._F, extra_variants, ))
        self._num_extra_rows += num_constraints
    #]


#-------------------------------------------------------------------------------
# Mixin methods
#-------------------------------------------------------------------------------


class Mixin:

    @staticmethod
    @_dm.topic(title="Hodrick-Prescott forms", anchor="hodrick-prescott-forms", priority=120)
    def _hodrick_prescott_reference():
        r"""
==Separate a series into a smooth trend and a gap==

### Syntax

#### Method form

    series.hpf_trend(span=..., smooth=None, log=False, level=None, change=None, information='two_sided')
    series.hpf_gap(span=..., smooth=None, log=False, level=None, change=None, information='two_sided')

#### Function form

    trend, gap = datapie.hpf(series, span=..., smooth=None, log=False, level=None, change=None, information='two_sided')
    new_series = datapie.hpf_trend(series, span=..., smooth=None, log=False, level=None, change=None, information='two_sided')
    new_series = datapie.hpf_gap(series, span=..., smooth=None, log=False, level=None, change=None, information='two_sided')

### Input arguments

!!! input "series"

    The series to filter.

!!! input "span"

    The output periods; the default, `...`, means the current span. The result covers the full interval between the first and last requested periods.

!!! input "smooth"

    How strongly the trend is smoothed. Larger values give a smoother trend. The default, `None`, selects `100` for yearly data, `400` for half-yearly, `1600` for quarterly, `14400` for monthly, and `1600` for other frequencies.

!!! input "log"

    Whether to filter logarithms and convert the results back. The default is `False`. With `True`, the gap is the input divided by the trend, rather than input minus trend. Input and constraint values must be positive for real-valued logarithms.

!!! input "level"

    An optional series fixing the trend at selected levels. Missing entries impose no constraint. The default is `None`. Only its first variant is used.

!!! input "change"

    An optional series fixing changes in the trend. Use differences in ordinary mode and gross rates of change in log mode. The default is `None`. Only its first variant is used.

!!! input "information"

    The default, `"two_sided"`, uses all observations. `"one_sided"` uses observations only up to the current period, but retains all supplied constraints. One-sided filtering can fail when the trend is not sufficiently determined.

### Method form returns

!!! returns "None"

    `hpf_trend` replaces the series with its trend; `hpf_gap` replaces it with its gap. `Series.hpf()` is not supported and raises `NotImplementedError`.

### Function form returns

!!! returns "trend, gap"

    `datapie.hpf` returns two new series containing the trend and gap. The input is unchanged.

!!! returns "new_series"

    `datapie.hpf_trend` and `datapie.hpf_gap` each return a new series containing the requested component. The input is unchanged.

All filter options are keyword-only. Missing input observations remain missing in the gap. Missing rows at the ends of each result are removed.

??? note "Details"

    The calculation covers the entire combined span of the input data, requested output periods, and constraint series—not only the periods common to them. Results are then restricted to the requested output interval.

    The filter balances squared distances from available observations against changes in the trend's slope, subject to the level and change constraints. Variants are filtered independently using the same constraints. A change constraint at the first calculation period is ignored because no preceding trend value is available.
        """
        pass

    #[

    @_dm.reference(category="filtering", )
    def hpf(self, ):
        r"""
==Reserve the in-place trend-gap entry point==

Calling `x.hpf()` raises `NotImplementedError`. Use `datapie.hpf` to obtain both components, or `hpf_trend` and `hpf_gap` to keep one component in place.

#### See also

[Hodrick-Prescott forms](#hodrick-prescott-forms)
        """
        raise NotImplementedError

    @_dm.reference(category="filtering", )
    def hpf_trend(self, *args, **kwargs):
        r"""
==Replace the series with its Hodrick-Prescott trend==

#### See also

[Hodrick-Prescott forms](#hodrick-prescott-forms)
        """
        start_date, trend_data, _ = _data_hpf(self, *args, **kwargs, )
        self._replace_start_and_values(start_date, trend_data, )

    @_dm.reference(category="filtering", )
    def hpf_gap(self, *args, **kwargs):
        r"""
==Replace the series with its Hodrick-Prescott gap==

#### See also

[Hodrick-Prescott forms](#hodrick-prescott-forms)
        """
        start_date, _, gap_data = _data_hpf(self, *args, **kwargs, )
        self._replace_start_and_values(start_date, gap_data, )

    #]


#-------------------------------------------------------------------------------
# Functional forms
#-------------------------------------------------------------------------------


def hpf(self, *args, **kwargs, ) -> tuple[Series, Series]:
    r"""
==Return the Hodrick-Prescott trend and gap==

#### Syntax

    trend, gap = datapie.hpf(
        x,
        span=...,
        smooth=None,
        log=False,
        level=None,
        change=None,
        information="two_sided",
    )

#### Returns

!!! returns "trend, gap"
    Two new series containing the trend and gap. The input is unchanged.

#### See also

[Hodrick-Prescott forms](#hodrick-prescott-forms) for the shared input arguments.
    """
    start_date, trend_data, gap_data = _data_hpf(self, *args, **kwargs, )
    trend = type(self)(start_date=start_date, values=trend_data, )
    gap = type(self)(start_date=start_date, values=gap_data, )
    return trend, gap


_functional_forms = {"hpf", }


for n in ("hpf_trend", "hpf_gap", ):
    exec(FUNC_STRING.format(n=n, ), globals(), locals(), )
    _functional_forms.add(n, )


__all__ = tuple(_functional_forms)


#-------------------------------------------------------------------------------


def _data_hpf(
    self,
    *,
    span: Iterable[Period] | EllipsisType = ...,
    smooth: Real | None = None,
    log: bool = False,
    level: Series | None = None,
    change: Series | None = None,
    information: Literal["two_sided", "one_sided"] = _DEFAULT_FILTER_INFORMATION,
) -> tuple[Period, _np.ndarray, _np.ndarray]:
    """
    Hodrick-Prescott filter run on a multi-variant data matrix
    """
    #[
    span = self.resolve_periods(span, )
    encompassing_span, *from_until = _periods.get_encompassing_span(self, level, change, span, )
    num_periods = len(encompassing_span, )
    own_data = self.get_data_from_until(from_until, )
    level_data, level_where = _prepare_constraints(level, from_until, )
    change_data, change_where = _prepare_constraints(change, from_until, )
    change_data, change_where = _remove_first_date_change(change_data, change_where, )
    #
    if log:
        own_data = _np.log(own_data, )
        level_data = _np.log(level_data, ) if level_data is not None else None
        change_data = _np.log(change_data, ) if change_data is not None else None
    #
    if smooth is None:
        smooth = _get_default_smooth(self.frequency, )
    #
    hp = _ConstrainedHodrickPrescottFilter(
        num_periods=num_periods,
        smooth=smooth,
        level_where=level_where,
        change_where=change_where,
        information=information,
    )
    #
    trend_data = []
    gap_data = []
    for data_variant in own_data.T:
        data_variant = data_variant.reshape(-1, 1)
        trend_data_variant, gap_data_variant = hp.filter_data(
            data_variant,
            level_data=level_data,
            change_data=change_data,
        )
        trend_data.append(trend_data_variant, )
        gap_data.append(gap_data_variant, )
    #
    trend_data = _np.hstack(trend_data, )
    gap_data = _np.hstack(gap_data, )
    #
    if span:
        new_start_date = min(span, )
        new_end_date = max(span, )
        clip_start = new_start_date - from_until[0]
        clip_end = new_end_date - from_until[0] + 1
        trend_data = trend_data[clip_start:clip_end, ...]
        gap_data = gap_data[clip_start:clip_end, ...]
    else:
        new_start_date = None
        trend_data = trend_data[[], ...]
        gap_data = gap_data[[], ...]
    #
    if log:
        trend_data = _np.exp(trend_data, )
        gap_data = _np.exp(gap_data, )
    #
    return new_start_date, trend_data, gap_data,
    #]


def _prepare_constraints(
    constraint: Self | None,
    from_until: tuple[Period, Period, ],
) -> tuple[_np.ndarray | None, list[int] | None, ]:
    #[
    if constraint is None:
        return None, None
    data = constraint.get_data_from_until(from_until, 0, )
    where = list(_np.where(~_np.isnan(data.reshape(-1, ), ), )[0])
    data = data[where, :]
    return data, where
    #]


def _remove_first_date_change(
    change_data: _np.ndarray | None,
    change_where: list[int] | None,
) -> tuple[_np.ndarray, list[int], ]:
    #[
    if change_where and 0 in change_where:
        where = change_where.index(0)
        change_where.pop(where)
        change_data = _np.delete(change_data, where, axis=0)
        if not change_where:
            change_data = None
            change_where = None
    return change_data, change_where
    #]

