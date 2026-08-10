r"""
Main time series class definition
"""


#[

from __future__ import annotations

from numbers import Real
from collections.abc import Iterable, Callable
from typing import Self, Any, TypeAlias, NoReturn, Literal
from types import EllipsisType
import numpy as _np
import operator as _op
import documark as _dm

from .. import descriptions as _descriptions
from .. import iterators as _iterators
from .. import periods as _periods
from .. import wrongdoings as _wrongdoings
from .. import has_variants as _has_variants
from ..periods import Period, Span, EmptySpan
from ..frequencies import Frequency

from ._categories import CATEGORIES
from ._functionalize import FUNC_STRING

from . import _apply_to_variants
from . import _broadcasts
from . import _conversions
from . import _elementwise
from . import _extrapolate
from . import _filling
from . import _hp
from . import _indexing
from . import _jsonables
from . import _lays
from . import _moving
from . import _plotly
from . import _statistics
from . import _temporal
from . import _timing
from . import _uv_filters
from . import _views
from . import _x13

#]


#
# The following functions can return either a new time series object if applied
# across variants (axis=1), or a scalar or a list of values if applied across
# time (axis=0)
#


__all__ = (
    "Series",
)


Dates = Period | Iterable[Period] | Span | EllipsisType | None
VariantsRequestType = int | Iterable[int] | slice | None
ShiftType = int | Literal["yoy", "soy", "eopy", "tty", ]
AxisType = Literal[0, 1]


def _get_date_positions(dates, base, num_periods, ):
    pos = tuple(_periods.period_indexes(dates, base, ))
    min_pos = min((x for x in pos if x is not None), default=0)
    max_pos = max((x for x in pos if x is not None), default=0)
    add_before = max(-min_pos, 0)
    add_after = max(max_pos - num_periods + 1, 0)
    pos_adjusted = [
        p + add_before if p is not None else None
        for p in pos
    ]
    return pos_adjusted, add_before, add_after


@_dm.reference(
    path=("data_management", "time_series.md", ),
    categories=CATEGORIES,
)
class Series(
    _indexing.Mixin,
    _elementwise.Mixin,
    _statistics.Mixin,
    _timing.Mixin,
    _lays.Mixin,
    _filling.Mixin,
    _temporal.Mixin,
    _conversions.Mixin,
    _extrapolate.Mixin,
    _moving.Mixin,
    _hp.Mixin,
    _x13.Mixin,
    _plotly.Mixin,
    _broadcasts.Mixin,
    _jsonables.Mixin,
    _descriptions.Mixin,
    _views.Mixin,
    _apply_to_variants.Mixin,
    _uv_filters.Mixin,
):
    r"""
················································································

Time series
============

Time `Series` objects represent numerical time series, organized as rows of
observations stored in [`numpy`](https://numpy.org) arrays and time stamped
using [time `Periods`](periods.md). A `Series` object can hold multiple
variants of the data, stored as mutliple columns.

················································································
    """
    #[

    __slots__ = (
        "start",
        "data",
        "data_type",
        "_description",
    )

    _numeric_format: str = "15g"
    _short_str_format: str = ">15"
    _date_str_format: str = ">12"
    _missing = _np.nan
    _missing_str: str = "⋅"
    _test_missing_period = staticmethod(lambda x: _np.all(_np.isnan(x)))

    @_dm.reference(
        category="constructor",
        call_name="Series",
    )
    def __init__(
        self,
        *,
        num_variants: int = 1,
        data_type: type = _np.float64,
        description: str = "",
        start: Period | None = None,
        start_date: Period | None = None,
        periods: Iterable[Period] | None = None,
        dates: Iterable[Period] | None = None,
        frequency: Frequency | None = None,
        values: Any | None = None,
        func: Callable | None = None,
        populate: bool = True,
    ) -> None:
        """
················································································

==Create a new `Series` object==

    self = Series(
        start=start,
        values=values,
    )


    self = Series(
        periods=periods,
        values=values,
    )


    self = Series(
        periods=periods,
        func=func,
    )


### Input arguments ###

???+ input "start"
    The time [`Period`](periods.md) of the first value in the `values`.

???+ input "periods"
    An iterable of time [`Periods`](periods.md) that will be used to time stamp
    the `values`. The iterable can be e.g. a tuple, a list, a time
    [`Span`](spans.md), or a single time [`Period`](periods.md).

???+ input "values"
    Time series values, supplied either as a single values, a tuple of values,
    or a NumPy array.

???+ input "func"
    A function that will be used to populate the time series; the function
    should not take any input arguments, and should return a single (scalar)
    numerical value; the function will called once for each period and each
    variant.


### Returns ###

???+ returns "None"
    This method modifies `self` in-place and does not return a value.


················································································
        """
        self.start = None
        self.data = _np.empty((0, num_variants), dtype=data_type, )
        self.data_type = self.data.dtype
        self.set_description(description, )
        #
        # Legacy support for start_date and dates
        if start is None and start_date is not None:
            start = start_date
        if periods is None and dates is not None:
            periods = dates
        #
        if populate:
            test = tuple(x is not None for x in (start, periods, values, func))
            populator = _SERIES_POPULATOR.get(test, _invalid_constructor)
            populator(
                self,
                start=start,
                periods=periods,
                frequency=frequency,
                values=values,
                func=func,
            )

    # ==========================================================================
    #  ### `Series(*, start=None, values=None, periods=None, func=None,
    #   num_variants=1, data_type=np.float64, description="",
    #   frequency=None, populate=True)`
    #
    #  Creates a new time series, either from a block of values pinned to a
    #  start period, or from an explicit list of periods.
    #
    #  Every argument is keyword-only, and only three combinations are
    #  accepted. `start` together with `values` lays the values out from
    #  `start` onwards, one row per period. `periods` together with `values`
    #  time stamps the values one by one. `periods` together with `func`
    #  calls `func` once for every period and every variant and stores what
    #  it returns. Calling `Series()` with nothing at all gives you an empty
    #  series you can fill later with `set_data`. Every other combination,
    #  including `start` with `func`, raises `wrongdoings.Error("Invalid
    #  Series object constructor")`.
    #
    #  **Parameters.** `start` is the time period of the first row of
    #  `values`. `periods` is any iterable of periods -- a tuple, a list, a
    #  time `Span`, or a single `Period`.
    #
    #  `values` is where the traps are. A numpy array or a tuple is read as
    #  one entry per period, which is almost always what you want. A *list*
    #  is read as one entry per variant, so `values=[1., 2., 3.]` does not
    #  give you a three-period series; it offers three variants, of which
    #  only the first is kept, and you end up with a single observation. Use
    #  a tuple or a numpy array for a plain series, and a list of tuples when
    #  you really do mean several variants.
    #
    #  `func` is called with no arguments and must return one number. It is
    #  called separately for each period and each variant, so a random
    #  generator produces different draws in each cell.
    #
    #  `num_variants` sets the number of columns, but only when the data
    #  cannot say otherwise. With a one-dimensional array or a tuple in
    #  `values` the series comes out with one column whatever you asked for;
    #  with `func`, or with a list of tuples, `num_variants` is obeyed.
    #
    #  `data_type` is the numpy element type of the stored data, `float64`
    #  unless you change it. Leave it alone. Missing observations are stored
    #  as `nan`, which an integer array cannot hold, and an integer series
    #  raises `ValueError: cannot convert float NaN to integer` the first
    #  time it has to pad -- including inside a plain `get_data()`.
    #
    #  `description` is a free-text label carried with the series and
    #  compared by `same_as`. Left alone it is an empty string.
    #
    #  `frequency` is accepted and never used; the frequency comes from the
    #  periods you supply.
    #
    #  `populate` set to `False` skips the whole filling step and gives you
    #  an empty series regardless of the other arguments; it exists for
    #  internal use.
    #
    #  `start_date` and `dates` are still accepted as old names for `start`
    #  and `periods`. They are used only when the new name is left out.
    #
    #  **Returns.** Nothing. Like every constructor it fills in the new
    #  object rather than returning a value.
    #
    #  Construction trims. Leading and trailing rows that are missing in
    #  every variant are dropped and `start` moves accordingly, so a series
    #  cannot be built with a deliberate gap at either end.
    #
    #  **Examples.** A list of numbers is not a list of observations:
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> dp.Series(start=dp.qq(2020,1), values=[1., 2., 3.]).get_data()
    #      array([[1.]])
    #      >>> dp.Series(start=dp.qq(2020,1), values=(1., 2., 3.)).get_data()
    #      array([[1.],
    #             [2.],
    #             [3.]])
    #
    #  Leading missing values are trimmed away at construction:
    #
    #      >>> x = dp.Series(start=dp.qq(2020,1),
    #      ...     values=np.array([np.nan, 2., 3.]))
    #      >>> x.start
    #      qq(2020,2)
    #
    # ==========================================================================

    def copy(self, ) -> Self:
        r"""
        """
        new = type(self)(populate=False, )
        new.start = None
        if self.start is not None:
            new.start = self.start.copy()
        new.data = _np.array(self.data, )
        new.data_type = self.data_type
        new._description = self._description
        return new

    # ==========================================================================
    #  ### `copy()`
    #
    #  Returns an independent duplicate of the time series.
    #
    #  Almost every method that changes a series changes it in place, so
    #  `copy` is how you keep the original. The values are copied into a new
    #  array, not shared, and the start period and the description come
    #  along, so the copy compares equal under `same_as`.
    #
    #  **Returns.** A new `Series` of the same class. Writing into the
    #  copy's data, or shifting or clipping it, leaves the original alone.
    #
    #  **Examples.**
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(start=dp.qq(2020,1), values=np.array([1., 2.]))
    #      >>> y = x.copy()
    #      >>> y.clip(dp.qq(2020,2), None)
    #      >>> x.num_periods
    #      2
    #
    # ==========================================================================

    @classmethod
    def void(
        klass,
        num_variants: int = 1,
        data_type: type = _np.float64,
        description: str = "",
    ) -> Self:
        r"""
        """
        return klass(
            num_variants=num_variants,
            data_type=data_type,
            description=description,
            populate=False,
        )

    # ==========================================================================
    #  ### `Series.void(num_variants=1, data_type=np.float64, description="")`
    #
    #  Creates an empty time series with a given number of variants.
    #
    #  This is a class method, meaning you call it on the class itself,
    #  `Series.void(...)`, not on an existing series. Use it when you know
    #  how many columns you will need but do not yet have any values or any
    #  periods; `set_data` fills them in afterwards and decides the start
    #  period from the first observation you write.
    #
    #  **Parameters.** `num_variants` is the number of columns the empty
    #  series carries. `data_type` and `description` are the same as in the
    #  constructor.
    #
    #  **Returns.** A new `Series` with no observations, `start` equal to
    #  `None`, and `is_empty` equal to `True`. Unlike `reset`, this keeps
    #  the `description` you pass in.
    #
    #  **Examples.**
    #
    #      >>> import datapie as dp
    #      >>> x = dp.Series.void(num_variants=3)
    #      >>> x.shape
    #      (0, 3)
    #      >>> x.start is None
    #      True
    #
    # ==========================================================================

    @classmethod
    @_dm.reference(
        category="constructor",
        call_name="Series.from_start_and_array",
    )
    def from_start_and_array(
        klass,
        start: Period,
        array: _np.ndarray,
        description: str = "",
        trim: bool = True,
    ) -> Self:
        r"""
················································································

==Create a new `Series` object from a start period and a numpy array==

    self = Series.from_start_and_array(
        start,
        array,
        description="",
        trim=True,
    )


### Input arguments ###

???+ input "start"
    The time [`Period`](periods.md) of the first value in the `array`.

???+ input "array"
    A numpy array containing the time series values. The array is reshaped to a
    two-dimensional array if needed. The individual rows are expected to
    correspond to a continuous sequence of time periods starting from `start`.

???+ input "description"
    A string description of the time series.

???+ input "trim"
    If `True`, the time series date will be trimmed to remove any leading
    or trailing periods that contain only `nan` values.


### Returns ###

???+ returns "self"
    A new `Series` object initialized with the provided start period and
    numpy array.

................................................................................
        """
        self = klass()
        self.start = start
        self.data = _reshape_numpy_array(array, )
        self.set_description(description, )
        if trim:
            self.trim()
        return self

    # ==========================================================================
    #  ### `Series.from_start_and_array(start, array, description="",
    #   trim=True)`
    #
    #  Creates a time series from a start period and a numpy array laid out
    #  one row per period.
    #
    #  This is a class method, called on the class itself. It is the direct
    #  route in from numpy: unlike the constructor it takes the array as a
    #  positional argument and never reinterprets a sequence as a list of
    #  variants, so it is the safer choice when the data already sits in an
    #  array.
    #
    #  **Parameters.** `start` is the period of the first row. `array` holds
    #  the values; a one-dimensional array becomes a single variant, and a
    #  two-dimensional array is read as one column per variant. Rows must be
    #  a continuous run of periods from `start` onwards -- there is no way to
    #  skip a period other than leaving `nan` in it.
    #
    #  `description` is the free-text label, empty by default.
    #
    #  `trim` left alone drops leading and trailing rows that are missing in
    #  every variant and moves `start` forward accordingly. Pass
    #  `trim=False` when the padding is deliberate and you want the span you
    #  asked for.
    #
    #  **Returns.** A new `Series`.
    #
    #  The array is not copied. The series keeps the very array you handed
    #  in, so later writes into your own array show up in the series, and
    #  vice versa. Pass `array.copy()` if that matters.
    #
    #  **Examples.** The array is shared, and the default trims:
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> a = np.array([np.nan, 2., 3.])
    #      >>> x = dp.Series.from_start_and_array(dp.qq(2020,1), a)
    #      >>> x.start
    #      qq(2020,2)
    #      >>> y = dp.Series.from_start_and_array(dp.qq(2020,1), a,
    #      ...     trim=False)
    #      >>> a[1] = 99.
    #      >>> y.get_data().tolist()
    #      [[nan], [99.0], [3.0]]
    #
    # ==========================================================================

    def reset(self, ) -> None:
        self.__init__(
            num_variants=self.num_variants,
            data_type=self.data_type,
        )

    # ==========================================================================
    #  ### `reset()`
    #
    #  Empties the time series in place, keeping only its shape and element
    #  type.
    #
    #  Use it to reuse an existing object rather than build a new one. The
    #  number of variants and the `data_type` survive; everything else goes.
    #
    #  **Returns.** Nothing; the series is modified in place.
    #
    #  The description is also erased, which is easy to miss -- `reset`
    #  rebuilds the object through the constructor, and the constructor's
    #  default description is an empty string. `trim` calls `reset` whenever
    #  every observation is missing, so an all-missing series loses its
    #  description too.
    #
    #  **Examples.**
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(start=dp.qq(2020,1), values=np.array([1., 2.]),
    #      ...     description="gdp")
    #      >>> x.reset()
    #      >>> x.start is None, x.get_description()
    #      (True, '')
    #
    # ==========================================================================

    def _create_periods_of_missing_values(self, num_rows=0) -> _np.ndarray:
        """
        """
        return _np.full(
            (num_rows, self.shape[1], ),
            _np.nan,
            dtype=self.data_type
        )

    @property
    @_dm.reference(category="property", )
    def shape(self, ) -> tuple[int, int]:
        """==Shape of time series data=="""
        return self.data.shape

    # ==========================================================================
    #  ### `shape`
    #
    #  Gives the number of periods and the number of variants as a pair.
    #
    #  A read-only property, written without parentheses. It is the shape of
    #  the underlying numpy array: rows are periods running from `start` to
    #  `end` with no gaps, columns are variants.
    #
    #  **Returns.** A two-element tuple of whole numbers. An empty series
    #  reports zero rows but keeps its column count.
    #
    #  **Examples.**
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> dp.Series(start=dp.qq(2020,1),
    #      ...     values=np.array([[1., 2.], [3., 4.]])).shape
    #      (2, 2)
    #
    # ==========================================================================

    @property
    @_dm.reference(category="property", )
    def num_periods(self, ) -> int:
        """==Number of periods from the first to the last observation=="""
        return self.data.shape[0]

    # ==========================================================================
    #  ### `num_periods`
    #
    #  Gives the number of periods from the first to the last observation.
    #
    #  A read-only property. This counts rows, not observations: periods in
    #  the middle that hold nothing but missing values are included, because
    #  the series is stored as one unbroken block. Leading and trailing
    #  missing rows are not, since they are trimmed away.
    #
    #  **Returns.** A whole number, zero for an empty series.
    #
    #  **Examples.** The gap in the middle still counts:
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> dp.Series(start=dp.qq(2020,1),
    #      ...     values=np.array([1., np.nan, 3.])).num_periods
    #      3
    #
    # ==========================================================================

    @property
    @_dm.reference(category="property", )
    def num_variants(self, ) -> int:
        """==Number of variants (columns) within the `Series` object=="""
        return self.data.shape[1]

    # ==========================================================================
    #  ### `num_variants`
    #
    #  Gives the number of variants, that is the number of columns, in the
    #  time series.
    #
    #  A read-only property. Variants are alternative paths for the same
    #  quantity -- simulation draws, scenarios, forecast vintages -- all
    #  sharing one time span.
    #
    #  **Returns.** A whole number. It stays what it was even when the
    #  series is emptied.
    #
    #  **Examples.**
    #
    #      >>> import datapie as dp
    #      >>> dp.Series.void(num_variants=3).num_variants
    #      3
    #
    # ==========================================================================

    @property
    def is_singleton(self, ) -> bool:
        """
        True for time series with only one variant (column)
        """
        return self.data.shape[1] == 1

    # ==========================================================================
    #  ### `is_singleton`
    #
    #  Says whether the time series holds exactly one variant.
    #
    #  A read-only property. Some methods change what they return depending
    #  on it: `iter_dates_values` hands back bare values for a
    #  single-variant series and lists for a multi-variant one, and `x13`
    #  does the same with the information it reports back. `get_values`
    #  looks as though it does, and does not -- see its own block.
    #
    #  **Returns.** `True` when there is exactly one column, `False`
    #  otherwise.
    #
    #  **Examples.**
    #
    #      >>> import datapie as dp
    #      >>> dp.Series.void(num_variants=2).is_singleton
    #      False
    #
    # ==========================================================================

    @property
    @_dm.reference(category="property", )
    def span(self, ):
        """==Time span of the time series=="""
        return Span(self.start, self.end, ) if self.start else ()

    range = span

    # ==========================================================================
    #  ### `span`, also available as `range`
    #
    #  Gives the time span running from the first to the last observation.
    #
    #  A read-only property. The span is iterable, so you can loop over it,
    #  and it can be handed straight back to `get_data`, `clip` or
    #  `set_data`. `range` is the same property under another name.
    #
    #  **Returns.** A `Span` from `start` to `end`. For an empty series you
    #  get an empty tuple `()`, not an empty `Span` -- it is falsy and
    #  iterates over nothing, but it has none of a span's methods.
    #
    #  **Examples.**
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> dp.Series(start=dp.qq(2020,1), values=np.array([1., 2.])).span
    #      Span(qq(2020,1), qq(2020,2))
    #      >>> dp.Series().span
    #      ()
    #
    # ==========================================================================

    @property
    @_dm.reference(category="property", )
    def from_until(self, ):
        """==Two-tuple with the start date and end date of the time series=="""
        return self.start, self.end

    # ==========================================================================
    #  ### `from_until`
    #
    #  Gives the first and last period of the time series as a pair.
    #
    #  A read-only property. This is the form the `get_data_from_until`
    #  family expects, so it is the quick way to pass one series' coverage
    #  to another.
    #
    #  **Returns.** A two-element tuple, `(start, end)`. Both entries are
    #  `None` for an empty series.
    #
    #  **Examples.**
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(start=dp.qq(2020,1), values=np.array([1., 2.]))
    #      >>> x.from_until
    #      (qq(2020,1), qq(2020,2))
    #
    # ==========================================================================

    @property
    @_dm.reference(category="property", )
    def periods(self, ) -> tuple[Period, ...]:
        """==N-tuple with the periods from the start period to the end period of the time series=="""
        return tuple(self.span, )

    dates = periods

    # ==========================================================================
    #  ### `periods`, also available as `dates`
    #
    #  Lists every period from the start to the end of the time series.
    #
    #  A read-only property. Unlike `span` this is a plain tuple you can
    #  index and measure, which makes it the convenient thing to zip against
    #  the rows of `get_data`. `dates` is the same property under an older
    #  name.
    #
    #  **Returns.** A tuple of `Period` objects, one per row, including
    #  periods whose observations are all missing. Empty for an empty
    #  series.
    #
    #  **Examples.**
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> dp.Series(start=dp.qq(2020,1),
    #      ...     values=np.array([1., np.nan, 3.])).periods
    #      (qq(2020,1), qq(2020,2), qq(2020,3))
    #
    # ==========================================================================

    @property
    @_dm.reference(category="property", call_name="start", )
    def _start(self):
        """==Start date of the time series=="""
        raise NotImplementedError

    # ==========================================================================
    #  ### `start`
    #
    #  Gives the period of the first observation, and re-dates the whole
    #  series when you assign to it.
    #
    #  This is the attribute the rest of the package is built on. A series
    #  stores its values as one unbroken block and stamps them by their
    #  starting period alone, so `start` together with the values is the
    #  entire time dimension of the object; `end`, `span`, `periods` and
    #  `from_until` are all worked out from it and from the number of rows.
    #
    #  Unlike the other entries in this category, `start` is an ordinary
    #  writable attribute rather than a read-only property. Assigning to it
    #  slides the whole series in time without touching a single value:
    #  `x.start = qq(2030,1)` moves a series that began in 2020Q1 ten years
    #  forward, keeping its length. `set_start` does the same thing and
    #  returns the series so the call can be chained. Nothing checks that the
    #  period you assign has the same frequency as the one it replaces, and
    #  since `frequency` is read off `start`, assigning a monthly period to a
    #  quarterly series changes what the series claims to be without
    #  changing its data.
    #
    #  **Returns.** A `Period`, or `None` when the series holds no
    #  observations. It is `None` for a freshly built empty series, but not
    #  for one emptied by `empty()`, which leaves the old start in place.
    #
    #  The `_start` definition carrying this documentation raises
    #  `NotImplementedError` if it is ever reached. It exists to give the
    #  attribute an entry in the generated reference and is never called,
    #  because the attribute shadows it.
    #
    #  **Examples.** Reading it, and re-dating with it:
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(start=dp.qq(2020,1), values=np.array([1., 2.]))
    #      >>> x.start
    #      qq(2020,1)
    #      >>> x.start = dp.qq(2030,1)
    #      >>> x.from_until
    #      (qq(2030,1), qq(2030,2))
    #      >>> dp.Series().start is None
    #      True
    #
    # ==========================================================================

    @property
    def start_period(self, ):
        return self.start

    start_date = start_period

    # ==========================================================================
    #  ### `start_period`, also available as `start_date`
    #
    #  Gives the period of the first observation.
    #
    #  A read-only property that reports the same thing as the plain `start`
    #  attribute; the two names exist so that code written against either
    #  convention keeps working.
    #
    #  **Returns.** A `Period`, or `None` for an empty series.
    #
    #  Note that `start` itself is an ordinary attribute, not a property,
    #  and assigning to it retimes the series without touching the values --
    #  see the `start` block above. `start_period` cannot be assigned to.
    #
    #  **Examples.**
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> dp.Series(start=dp.qq(2020,1),
    #      ...     values=np.array([1., 2.])).start_period
    #      qq(2020,1)
    #
    # ==========================================================================

    @property
    @_dm.reference(category="property", )
    def end(self):
        """==End period of the time series=="""
        return (
            self.start + self.data.shape[0] - 1
            if self.start else None
        )

    end_period = end
    end_date = end

    # ==========================================================================
    #  ### `end`, also available as `end_period` and `end_date`
    #
    #  Gives the period of the last observation.
    #
    #  A read-only property, worked out from `start` and the number of rows
    #  rather than stored.
    #
    #  **Returns.** A `Period`, or `None` when the series has never had a
    #  start period.
    #
    #  A series that was emptied by `empty()` keeps its `start`, and this
    #  property then counts zero rows forward from it and reports the period
    #  *before* the start. Treat `is_empty` rather than `end` as the test
    #  for having no data.
    #
    #  **Examples.**
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(start=dp.qq(2020,1), values=np.array([1., 2.]))
    #      >>> x.end
    #      qq(2020,2)
    #      >>> x.empty()
    #      >>> x.end
    #      qq(2019,4)
    #
    # ==========================================================================

    @property
    @_dm.reference(category="property", )
    def frequency(self, ):
        """==Date frequency of the time series=="""
        return (
            self.start.frequency
            if self.start is not None
            else Frequency.UNKNOWN
        )

    # ==========================================================================
    #  ### `frequency`
    #
    #  Gives the date frequency of the time series.
    #
    #  A read-only property taken from the start period, so it is decided by
    #  the periods you built the series from and cannot be set separately.
    #
    #  **Returns.** A `Frequency` such as `QUARTERLY` or `MONTHLY`. An empty
    #  series, having no start period, reports `Frequency.UNKNOWN`.
    #
    #  **Examples.**
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> dp.Series(start=dp.mm(2020,1),
    #      ...     values=np.array([1., 2.])).frequency
    #      <Frequency.MONTHLY: 12>
    #
    # ==========================================================================

    @property
    @_dm.reference(category="property", )
    def is_empty(self, ) -> bool:
        """==True if the time series is empty=="""
        return not self.data.size

    # ==========================================================================
    #  ### `is_empty`
    #
    #  Says whether the time series holds no observations at all.
    #
    #  A read-only property, and the reliable test for an unpopulated
    #  series: `start` may still be set after `empty()`, and `end` may then
    #  report a period that lies before it.
    #
    #  **Returns.** `True` when there are no rows, `False` otherwise. A
    #  series with rows made up entirely of missing values is not empty --
    #  although trimming will usually have removed them already.
    #
    #  **Examples.**
    #
    #      >>> import datapie as dp
    #      >>> dp.Series().is_empty
    #      True
    #
    # ==========================================================================

    @property
    @_dm.reference(category="property", )
    def has_missing(self, ):
        """==True if the time series is non-empty and contains in-sample missing values=="""
        return bool((not self.is_empty) and _np.isnan(self.data).any())

    # ==========================================================================
    #  ### `has_missing`
    #
    #  Says whether the time series has any missing observation inside its
    #  own span.
    #
    #  A read-only property. Because leading and trailing missing rows are
    #  trimmed away, anything it reports is a genuine hole in the middle of
    #  the data, or a period that some variants cover and others do not.
    #
    #  **Returns.** `True` when at least one value inside the span is
    #  missing, `False` otherwise, and `False` for an empty series.
    #
    #  **Examples.**
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> dp.Series(start=dp.qq(2020,1),
    #      ...     values=np.array([1., np.nan, 3.])).has_missing
    #      True
    #
    # ==========================================================================

    def any_missing(self, *args, ) -> bool:
        """
        """
        return self._func_missing(_np.any, *args, )

    # ==========================================================================
    #  ### `any_missing(*args)`
    #
    #  Says whether any observation is missing.
    #
    #  Unlike the `has_missing` property this is a method you can restrict to
    #  part of the series: whatever you pass is handed straight to
    #  `get_data`, so a period, a list of periods or a `Span` narrows the
    #  question, and an extra argument after that picks variants.
    #
    #  **Parameters.** `args` are the arguments of `get_data`: the periods to
    #  look at, and optionally which variants. With no arguments the whole
    #  series is checked.
    #
    #  Periods outside the current span are not an error. They are treated as
    #  missing, so asking about a period the series does not reach always
    #  answers `True`.
    #
    #  **Returns.** `True` or `False`.
    #
    #  **Examples.**
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(start=dp.qq(2020,1),
    #      ...     values=np.array([1., np.nan, 3.]))
    #      >>> x.any_missing(dp.Span(dp.qq(2020,1), dp.qq(2020,1)))
    #      False
    #      >>> x.any_missing(dp.qq(2030,1))
    #      True
    #
    # ==========================================================================

    def where_missing(self, *args, ) -> tuple[Period]:
        """
        """
        data = self.get_data(*args, )
        missing_mask = _np.isnan(data).any(axis=1, )
        return tuple(p for p, m in zip(self.span, missing_mask, ) if m)

    # ==========================================================================
    #  ### `where_missing(*args)`
    #
    #  Lists the periods at which an observation is missing.
    #
    #  Use it to see where the holes are before filling them. A period counts
    #  as missing when any one of the variants is missing there, not only
    #  when all of them are.
    #
    #  **Parameters.** `args` are the arguments of `get_data`, so you can
    #  narrow the search to a `Span`, a list of periods, or particular
    #  variants. With no arguments the whole series is searched.
    #
    #  **Returns.** A tuple of `Period` objects, empty when nothing is
    #  missing.
    #
    #  Only the no-argument form can be trusted. When you pass periods, the
    #  missing values are found in the data you asked for but the periods
    #  reported are counted from the start of the series, so the answers come
    #  back shifted by the distance between the two. See the log entry for
    #  this file.
    #
    #  **Examples.**
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(start=dp.qq(2020,1),
    #      ...     values=np.array([1., np.nan, 3., np.nan, 5.]))
    #      >>> x.where_missing()
    #      (qq(2020,2), qq(2020,4))
    #
    # ==========================================================================

    def all_missing(self, *args, ) -> bool:
        """
        """
        return self._func_missing(_np.all, *args, )

    # ==========================================================================
    #  ### `all_missing(*args)`
    #
    #  Says whether every observation is missing.
    #
    #  The counterpart of `any_missing`, useful as a guard before running a
    #  filter or a regression on a series that may have turned out empty.
    #
    #  **Parameters.** `args` are the arguments of `get_data`: the periods to
    #  look at, and optionally which variants. With no arguments the whole
    #  series is checked.
    #
    #  **Returns.** `True` or `False`. An empty series, and any request that
    #  selects no periods at all, answers `True` -- there is nothing that is
    #  not missing. Combine it with `is_empty` if that distinction matters.
    #
    #  **Examples.**
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> dp.Series().all_missing()
    #      True
    #      >>> dp.Series(start=dp.qq(2020,1),
    #      ...     values=np.array([1., np.nan])).all_missing()
    #      False
    #
    # ==========================================================================

    def count_missing(self, *args, ) -> int:
        """
        """
        return self._func_missing(_np.count_nonzero, *args, )

    # ==========================================================================
    #  ### `count_missing(*args)`
    #
    #  Reports whether any observation is missing.
    #
    #  **Parameters.** `args` are the arguments of `get_data`: the periods to
    #  look at, and optionally which variants. With no arguments the whole
    #  series is checked.
    #
    #  **Returns.** `True` or `False`, despite the name and despite the
    #  `int` annotation on the method. The count is computed and then passed
    #  through `bool`, so every non-zero count collapses to `True`. The
    #  method as written cannot tell you how many values are missing; use
    #  `len(x.where_missing())`, or count the `nan` entries in
    #  `x.get_data()` yourself. See the log entry for this file.
    #
    #  **Examples.** Two missing values, one answer:
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> dp.Series(start=dp.qq(2020,1),
    #      ...     values=np.array([1., np.nan, 3., np.nan])).count_missing()
    #      True
    #
    # ==========================================================================

    def _func_missing(self, func, *args, ) -> bool:
        """
        """
        data = self.get_data(*args, )
        return bool(func(_np.isnan(data)))

    def set_data(
        self,
        dates: Dates,
        data: Any | Series,
        variants: VariantsRequestType = None,
    ) -> None:
        """
        """
        dates = self.resolve_periods(dates, )
        is_data_ndarray = isinstance(data, _np.ndarray)
        is_empty_data = (
            data is None
            or (is_data_ndarray and data.size == 0)
        )
        if not dates and is_empty_data:
            return
        data = (
            _reshape_numpy_array(data, )
            if is_data_ndarray else data
        )
        vids = self._resolve_variants(variants, )
        if not self.start:
            self.start = next(iter(dates), None, )
            self.data = self._create_periods_of_missing_values(num_rows=1, )
        pos, add_before, add_after = _get_date_positions(dates, self.start, self.shape[0], )
        self.data = self._create_expanded_data(add_before, add_after)
        if add_before:
            self.start -= add_before
        if hasattr(data, "get_data"):
            data = data.get_data(dates)
        #
        data_variants = _has_variants.iter_variants(data, )
        for c, d in zip(vids, data_variants, ):
            self.data[pos, c] = d
        self.trim()

    # ==========================================================================
    #  ### `set_data(dates, data, variants=None)`
    #
    #  Writes values into the time series at the periods you name, extending
    #  the span when they fall outside it.
    #
    #  This is the general way to put data into an existing series. Unlike
    #  `clip` it grows as well as fills: periods before the current start or
    #  after the current end are added, and the rows in between are filled
    #  with missing values.
    #
    #  **Parameters.** `dates` is where to write -- a single `Period`, a list
    #  of them, a `Span`, or `...` for the whole current span. The periods
    #  need not be in order and need not be adjacent.
    #
    #  `data` is what to write. A number is written to every period named.
    #  A numpy array or a tuple is read as one entry per period, in the order
    #  `dates` gives them. A *list* is read as one entry per variant, so
    #  `set_data(span, [7., 8., 9.])` writes 7 to every period rather than
    #  laying the three numbers out in time. Another `Series` may also be
    #  passed, and the values are then taken from it at those same periods.
    #
    #  `variants` picks the columns to write. Left alone every variant is
    #  written. A whole number picks one, and a `slice` or a list of numbers
    #  picks several.
    #
    #  **Returns.** Nothing; the series is modified in place, and both
    #  `start` and `end` may move.
    #
    #  The series is trimmed afterwards, so writing missing values over the
    #  first or last observation shortens the series rather than leaving a
    #  blank edge.
    #
    #  **Examples.** Writing before the start extends the series backwards:
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(start=dp.qq(2020,1), values=np.array([1., 2.]))
    #      >>> x.set_data(dp.qq(2019,4), 0.)
    #      >>> x.start, x.get_data().tolist()
    #      (qq(2019,4), [[0.0], [1.0], [2.0]])
    #
    # ==========================================================================

    def _get_data_and_recreate(
        self,
        *args,
    ) -> _np.ndarray:
        """
        """
        dates, pos, variants, expanded_data = self._resolve_dates_and_positions(*args, )
        data = expanded_data[_np.ix_(pos, variants)]
        num_variants = data.shape[1]
        new = Series(num_variants=num_variants, data_type=self.data_type)
        new.set_data(dates, data)
        return new

    def _resolve_dates_and_positions(
        self,
        dates: Dates,
        variants: VariantsRequestType = None,
    ) -> tuple[Iterable[Period], Iterable[int], Iterable[int], _np.ndarray]:
        """
        """
        dates = self.resolve_periods(dates, )
        variants = self._resolve_variants(variants)
        if not dates:
            dates = ()
            pos = ()
            data = self._create_periods_of_missing_values(num_rows=0, )[:, variants]
            return dates, pos, variants, data
        #
        base_date = self.start or min(dates, )
        pos, add_before, add_after = _get_date_positions(dates, base_date, self.shape[0], )
        data = self._create_expanded_data(add_before, add_after, )
        if not isinstance(pos, Iterable):
            pos = (pos, )
        return dates, pos, variants, data

    def alter_num_variants(
        self,
        new_num: int,
    ) -> Self:
        """
        Alter (expand, shrink) the number of variants in this time series object
        """
        if new_num < self.num_variants:
            self.shrink_num_variants(new_num, )
        elif new_num > self.num_variants:
            self.expand_num_variants(new_num, )

    # ==========================================================================
    #  ### `alter_num_variants(new_num)`
    #
    #  Changes the number of variants to the number you ask for, adding or
    #  dropping columns as needed.
    #
    #  This is the safe front end to `expand_num_variants` and
    #  `shrink_num_variants`: it compares the counts and calls whichever one
    #  applies, and does nothing when the series already has `new_num`
    #  variants.
    #
    #  **Parameters.** `new_num` is the number of variants you want. Growing
    #  copies the last existing variant into every new column; shrinking
    #  drops columns from the right-hand end, and the values in them are
    #  gone.
    #
    #  **Returns.** Nothing; the series is modified in place. The `Self`
    #  annotation on the method is wrong -- neither branch returns anything.
    #
    #  **Examples.** New columns repeat the last one:
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(num_variants=2, start=dp.qq(2020,1),
    #      ...     values=np.array([[1., 2.], [3., 4.]]))
    #      >>> x.alter_num_variants(3)
    #      >>> x.get_data().tolist()
    #      [[1.0, 2.0, 2.0], [3.0, 4.0, 4.0]]
    #
    # ==========================================================================

    def expand_num_variants(
        self,
        new_num: int,
    ) -> None:
        """
        """
        add = new_num - self.num_variants
        if add < 0:
            raise ValueError("Use shrink_num_variants to shrink the number of variants")
        data = _np.tile(self.data[:, (-1, )], (1, add, ))
        self.data = _np.hstack((self.data, data, ), )

    # ==========================================================================
    #  ### `expand_num_variants(new_num)`
    #
    #  Adds variants until the series has `new_num` of them.
    #
    #  Use it to widen a series before combining it with a wider one. Prefer
    #  `alter_num_variants` unless you are certain of the direction.
    #
    #  **Parameters.** `new_num` must be at least the current number of
    #  variants; a smaller number raises `ValueError` telling you to call
    #  `shrink_num_variants` instead.
    #
    #  The new columns are copies of the current *last* variant, not of the
    #  first and not of an average. For a single-variant series that is the
    #  only column, which is the usual case, but for a wider series the
    #  choice matters.
    #
    #  **Returns.** Nothing; the series is modified in place.
    #
    #  **Examples.**
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(num_variants=2, start=dp.qq(2020,1),
    #      ...     values=np.array([[1., 2.], [3., 4.]]))
    #      >>> x.expand_num_variants(4)
    #      >>> x.get_data().tolist()
    #      [[1.0, 2.0, 2.0, 2.0], [3.0, 4.0, 4.0, 4.0]]
    #
    # ==========================================================================

    def shrink_num_variants(
        self,
        new_num: int,
    ) -> None:
        """
        """
        remove = self.num_variants - new_num
        if remove < 0:
            raise ValueError("Use expand_num_variants to expand the number of variants")
        self.data = self.data[:, :-remove]

    # ==========================================================================
    #  ### `shrink_num_variants(new_num)`
    #
    #  Drops variants from the right until the series has `new_num` of them.
    #
    #  **Parameters.** `new_num` must be at most the current number of
    #  variants; a larger number raises `ValueError` telling you to call
    #  `expand_num_variants` instead. The columns removed are the last ones,
    #  and their values are discarded; use `extract_variants` when you need
    #  to choose which ones to keep.
    #
    #  Calling it with the number the series already has empties every
    #  column instead of doing nothing, because dropping "the last zero
    #  columns" is computed as keeping everything up to column zero. Go
    #  through `alter_num_variants`, which checks first and never reaches
    #  this case. See the log entry for this file.
    #
    #  **Returns.** Nothing; the series is modified in place.
    #
    #  **Examples.** Asking for the count it already has wipes the data:
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(num_variants=2, start=dp.qq(2020,1),
    #      ...     values=np.array([[1., 2.], [3., 4.]]))
    #      >>> x.shrink_num_variants(2)
    #      >>> x.shape
    #      (2, 0)
    #
    # ==========================================================================

    def get_values(
        self,
        *args,
        unpack_singleton: bool = True,
        **kwargs,
    ) -> list[tuple[Real, ...]] | tuple[Real, ...]:
        """
        """
        data = self.get_data(*args, **kwargs, )
        values = [ tuple(data_column.tolist()) for data_column in data.T ]
        return _has_variants.unpack_singleton(
            values,
            unpack_singleton=unpack_singleton,
        )

    # ==========================================================================
    #  ### `get_values(*args, unpack_singleton=True, **kwargs)`
    #
    #  Returns the observations as plain Python numbers rather than as a
    #  numpy array.
    #
    #  Use it when the values are going into ordinary Python code, into a
    #  spreadsheet writer, or into JSON, where a numpy array would have to be
    #  converted anyway.
    #
    #  **Parameters.** `args` and `kwargs` go straight to `get_data`, so the
    #  first argument selects periods -- a `Period`, a list of them, a
    #  `Span`, or `...` for the whole span -- and a second selects variants.
    #
    #  `unpack_singleton` left alone hands back one bare tuple instead of a
    #  list holding a single tuple. Set it to `False` to always get the list,
    #  which is what you want in code that must work for any number of
    #  variants.
    #
    #  **Returns.** With `unpack_singleton=False`, a list with one tuple of
    #  numbers per variant. With it left alone, the first of those tuples.
    #
    #  That last sentence is the trap: with the default in force the method
    #  returns the *first variant only*, whatever the number of variants,
    #  because the check for a single variant is never actually made. On a
    #  multi-variant series the other columns disappear without warning.
    #  Always pass `unpack_singleton=False` unless you know there is one
    #  variant. See the log entry for this file.
    #
    #  **Examples.** Two variants in, one variant out:
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(num_variants=2, start=dp.qq(2020,1),
    #      ...     values=np.array([[1., 2.], [3., 4.]]))
    #      >>> x.get_values()
    #      (1.0, 3.0)
    #      >>> x.get_values(unpack_singleton=False)
    #      [(1.0, 3.0), (2.0, 4.0)]
    #
    # ==========================================================================

    def get_data(self, *args, **kwargs, ) -> _np.ndarray:
        return self.get_data_and_periods(*args, **kwargs, )[0]

    # ==========================================================================
    #  ### `get_data(*args, **kwargs)`
    #
    #  Returns the observations for the periods you ask for as a numpy array.
    #
    #  This is the everyday way to get numbers out of a series. The result is
    #  always two-dimensional, one row per period requested and one column
    #  per variant, even when there is only one of either.
    #
    #  **Parameters.** The first argument selects periods: a single `Period`,
    #  a list or tuple of them, a `Span`, or `...` (the default) for the
    #  whole span. Periods may be given in any order, and the rows come back
    #  in the order you asked for them. A second argument selects variants,
    #  as a whole number, a list of numbers, or a `slice`.
    #
    #  Periods outside the current span are not an error and do not extend
    #  the series; they come back as missing values. That is worth knowing,
    #  because a mistyped year returns a column of `nan` rather than
    #  complaining.
    #
    #  **Returns.** A two-dimensional numpy array, freshly built, so writing
    #  into it does not change the series.
    #
    #  **Examples.** Out-of-span periods come back missing, and order is
    #  preserved:
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(start=dp.qq(2020,1), values=np.array([1., 2.]))
    #      >>> x.get_data([dp.qq(2020,2), dp.qq(2030,1)]).tolist()
    #      [[2.0], [nan]]
    #
    # ==========================================================================

    def get_data_and_periods(
        self,
        dates: Iterable[Period] | None | EllipsisType = ...,
        *args,
    ) -> _np.ndarray:
        periods, pos, variants, expanded_values = self._resolve_dates_and_positions(dates, *args, )
        return expanded_values[_np.ix_(pos, variants)], periods

    # ==========================================================================
    #  ### `get_data_and_periods(dates=..., *args)`
    #
    #  Returns the observations together with the periods they belong to.
    #
    #  `get_data` is this method with the periods thrown away. Use this one
    #  when you need to label the rows -- writing a table, plotting, or
    #  lining up two series by hand.
    #
    #  **Parameters.** `dates` selects the periods, exactly as in `get_data`,
    #  and left alone covers the whole span. Any further argument selects
    #  variants.
    #
    #  **Returns.** A two-element tuple. The first entry is the
    #  two-dimensional numpy array of values; the second is a tuple of the
    #  `Period` objects for its rows, in the same order. The `ndarray`
    #  annotation on the method describes only the first entry.
    #
    #  **Examples.**
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(start=dp.qq(2020,1), values=np.array([1., 2.]))
    #      >>> data, periods = x.get_data_and_periods()
    #      >>> periods
    #      (qq(2020,1), qq(2020,2))
    #
    # ==========================================================================

    def get_data_variant(
        self,
        dates: Dates,
        variant: Real | None = None,
    ) -> _np.ndarray:
        """
        """
        variant = variant if variant and variant<self.data.shape[1] else 0
        return self.get_data(dates, variant, )

    # ==========================================================================
    #  ### `get_data_variant(dates, variant=None)`
    #
    #  Returns the observations of a single variant as a one-column numpy
    #  array.
    #
    #  Use it when a routine needs one path at a time out of a series holding
    #  several.
    #
    #  **Parameters.** `dates` selects the periods, as in `get_data`.
    #
    #  `variant` is the column number, counted from zero. Left alone, or set
    #  to zero, you get the first variant. A column number that is not below
    #  the number of variants silently gives you the first variant instead of
    #  raising -- so a typo in the index returns plausible numbers from the
    #  wrong column. Negative numbers are passed through to numpy and count
    #  from the right-hand end, so `-1` gives the last variant.
    #
    #  **Returns.** A two-dimensional numpy array with exactly one column.
    #
    #  **Examples.** An out-of-range variant is not an error:
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(num_variants=2, start=dp.qq(2020,1),
    #      ...     values=np.array([[1., 2.], [3., 4.]]))
    #      >>> x.get_data_variant(..., 5).tolist()
    #      [[1.0], [3.0]]
    #
    # ==========================================================================

    def get_data_from_until(
        self,
        from_until,
        *args,
    ) -> _np.ndarray:
        """
        """
        _, pos, variants, expanded_data \
            = self._resolve_dates_and_positions(from_until, *args, )
        from_pos, to_pos = pos[0], pos[-1]+1
        return expanded_data[from_pos:to_pos, variants]

    # ==========================================================================
    #  ### `get_data_from_until(from_until, *args)`
    #
    #  Returns an unbroken block of observations between two periods.
    #
    #  Where `get_data` takes an explicit list of periods, this takes just
    #  the two ends and returns everything in between, which is what you want
    #  when the rows have to stay contiguous -- for a filter, a regression, or
    #  anything that reads consecutive observations.
    #
    #  **Parameters.** `from_until` is a pair of periods, first and last,
    #  both included. The `from_until` property of another series has exactly
    #  this shape. Any further argument selects variants.
    #
    #  The two ends may lie outside the current span, and the block is then
    #  padded with missing values rather than clipped; this is how two series
    #  of different lengths are lined up before being combined.
    #
    #  A pair given the wrong way round, with the later period first, returns
    #  an empty array rather than raising.
    #
    #  **Returns.** A two-dimensional numpy array.
    #
    #  **Examples.** Asking beyond the end pads instead of failing:
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(start=dp.qq(2020,1), values=np.array([1., 2.]))
    #      >>> x.get_data_from_until((dp.qq(2020,1), dp.qq(2020,3))).tolist()
    #      [[1.0], [2.0], [nan]]
    #
    # ==========================================================================

    def get_data_variant_from_until(
        self,
        from_until: Iterable[Period],
        variant: int | None = None,
    ) -> _np.ndarray:
        """
        """
        variant = variant if variant and variant < self.data.shape[1] else 0
        return self.get_data_from_until(from_until, variant, )

    # ==========================================================================
    #  ### `get_data_variant_from_until(from_until, variant=None)`
    #
    #  Returns an unbroken block of observations for a single variant.
    #
    #  `get_data_from_until` narrowed to one column; use it when a routine
    #  takes one path at a time and needs consecutive periods.
    #
    #  **Parameters.** `from_until` is a pair of periods, first and last,
    #  both included, and may reach outside the series, in which case the
    #  block is padded with missing values.
    #
    #  `variant` is the column number counted from zero. Left alone, or set
    #  to zero, you get the first variant. As in `get_data_variant`, a number
    #  that is not below the number of variants silently falls back to the
    #  first column rather than raising.
    #
    #  **Returns.** A two-dimensional numpy array with one column.
    #
    #  **Examples.**
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(num_variants=2, start=dp.qq(2020,1),
    #      ...     values=np.array([[1., 2.], [3., 4.]]))
    #      >>> x.get_data_variant_from_until(
    #      ...     (dp.qq(2020,1), dp.qq(2020,2)), 1).tolist()
    #      [[2.0], [4.0]]
    #
    # ==========================================================================

    def extract_variants(
        self,
        variants,
    ) -> None:
        if not isinstance(variants, Iterable):
            variants = (variants, )
        else:
            variants = tuple(c for c in variants)
        self.data = self.data[:, variants]

    # ==========================================================================
    #  ### `extract_variants(variants)`
    #
    #  Keeps only the variants you name, in the order you name them.
    #
    #  This is the way to pick particular columns out of a multi-variant
    #  series -- one scenario out of many, or a reordered subset. Unlike
    #  `shrink_num_variants`, which always drops from the right, you choose.
    #
    #  **Parameters.** `variants` is either a single column number or an
    #  iterable of them, counted from zero. Repeats are allowed and duplicate
    #  the column, so the series can come out wider than it went in.
    #  Negative numbers count from the right-hand end. An out-of-range number
    #  raises `IndexError`.
    #
    #  **Returns.** Nothing; the series is modified in place and the
    #  discarded columns are gone. Copy the series first if you need them.
    #
    #  **Examples.** Reordering and duplicating in one call:
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(num_variants=2, start=dp.qq(2020,1),
    #      ...     values=np.array([[1., 2.], [3., 4.]]))
    #      >>> x.extract_variants((1, 1, 0))
    #      >>> x.get_data().tolist()
    #      [[2.0, 2.0, 1.0], [4.0, 4.0, 3.0]]
    #
    # ==========================================================================

    def set_start(
        self,
        new_start: Period,
    ) -> Self:
        self.start = new_start
        return self

    # ==========================================================================
    #  ### `set_start(new_start)`
    #
    #  Moves the whole time series so that its first observation sits at a
    #  new period.
    #
    #  The values are untouched; only their time stamps change. Use it when
    #  a series was read in with the wrong base period, or when a block of
    #  numbers needs to be re-dated wholesale.
    #
    #  **Parameters.** `new_start` is the period the first observation is to
    #  carry. Nothing checks that it has the same frequency as the periods
    #  already in the series, so a quarterly series can silently be told it
    #  starts in a month, and the mismatch shows up only later.
    #
    #  **Returns.** The series itself, so the call can be chained. The
    #  change is made in place all the same -- the original is not preserved.
    #
    #  **Examples.**
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(start=dp.qq(2020,1), values=np.array([1., 2.]))
    #      >>> x.set_start(dp.qq(2030,1)).from_until
    #      (qq(2030,1), qq(2030,2))
    #
    # ==========================================================================

    def resolve_periods(self, periods, ) -> tuple[Period]:
        """
        """
        if periods is None:
            # periods = []
            periods = ...
        if isinstance(periods, slice) and periods == slice(None, ):
            periods = ...
        if periods is ... and self.start is not None:
            periods = Span(None, None, )
        if periods is ... and self.start is None:
            periods = EmptySpan()
        if hasattr(periods, "needs_resolve") and periods.needs_resolve:
            periods = periods.resolve(self, )
        return tuple(
            d.resolve(self) if hasattr(d, "needs_resolve") and d.needs_resolve else d
            for d in periods
        )

    # ==========================================================================
    #  ### `resolve_periods(periods)`
    #
    #  Turns whatever period request you were given into a plain tuple of
    #  periods.
    #
    #  Every method that accepts periods runs them through here first, which
    #  is what lets `...`, `None`, an open-ended `Span` and a bare `Period`
    #  all be used interchangeably. Call it directly when you want to see
    #  which periods a request actually covers.
    #
    #  **Parameters.** `periods` may be a single `Period`, any iterable of
    #  periods, a `Span`, a `slice`, `...`, or `None`.
    #
    #  `None`, `...` and the empty slice `slice(None)` all mean the same
    #  thing: the entire span of this series. On an empty series, which has
    #  no span, they resolve to no periods at all rather than raising.
    #  Open-ended spans, such as one with no end period, are closed off
    #  against this series' own start and end.
    #
    #  **Returns.** A tuple of `Period` objects, possibly empty. Nothing is
    #  changed on the series.
    #
    #  **Examples.** The same answer three ways, and nothing on an empty
    #  series:
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(start=dp.qq(2020,1), values=np.array([1., 2.]))
    #      >>> x.resolve_periods(None) == x.resolve_periods(...)
    #      True
    #      >>> dp.Series().resolve_periods(...)
    #      ()
    #
    # ==========================================================================

    def _resolve_variants(
        self,
        variants: VariantsRequestType,
    ) -> Iterable[int]:
        """
        Resolve variant request to an iterable of integers
        """
        if variants is None or variants is Ellipsis:
            variants = slice(None, )
        if isinstance(variants, slice):
            variants = range(*variants.indices(self.num_variants))
        if not isinstance(variants, Iterable):
            variants = (variants, )
        return variants

    def _shift_by_number(self, by: int, **kwargs, ) -> None:
        r"""
        Shift (lag, lead) start date by a number of periods
        """
        if self.start is None:
            return
        self.start -= by

    def _shift_yoy(self, **kwargs, ) -> None:
        r"""
        Shift the start date by one year back
        """
        self._shift_by_number(-self.frequency.value, )

    def _shift_soy(self, **kwargs, ) -> None:
        r"""
        Replace each observation by the start of the year observation
        """
        new_data = self.get_data(
            t.create_soy()
            for t in self.span
        )
        self._replace_data(new_data, )

    def _shift_eopy(self, **kwargs, ) -> Self:
        r"""
        Replace each observation by the end of the previous year observation
        """
        new_data = self.get_data(
            t.create_eopy()
            for t in self.span
        )
        self._replace_data(new_data, )

    def _shift_tty(
        self,
        by: Any | None = None,
        *,
        neutral_value: int | None = None,
        **kwargs,
    ) -> None:
        r"""
        Replace each observation by the start of the year observation except for
        the start-of-year periods which are filled with a neutral value.
        """
        zipped = tuple((t, t.create_tty(), ) for t in self.span)
        neutral_periods = tuple(t for t, tty in zipped if tty is None)
        periods = (t for t, tty in zipped if tty is not None )
        dty_periods = (tty for _, tty in zipped if tty is not None)
        dty_values = self.get_data(dty_periods, )
        self.set_data(periods, dty_values, )
        self.set_data(neutral_periods, neutral_value, )

    def hstack(self, *args, ):
        """
        """
        if not args:
            return self.copy()
        self_args = (self, *args, )
        if all(i.is_empty for i in self_args):
            num_variants = sum(i.num_variants for i in self_args)
            return Series(num_variants=num_variants, )
        encompassing_span, *from_until = _periods.get_encompassing_span(self, *args, )
        new_data = self.get_data_from_until(from_until, )
        add_data = (
            x.get_data_from_until(from_until, )
            if hasattr(x, "get_data")
            else _create_data_variant_from_number(x, encompassing_span, self.data_type)
            for x in args
        )
        new_data = _np.hstack((new_data, *add_data))
        new = Series(num_variants=new_data.shape[1], )
        new.set_data(encompassing_span, new_data, )
        return new

    # ==========================================================================
    #  ### `hstack(*args)`
    #
    #  Stacks other series and numbers alongside this one as extra variants.
    #
    #  Use it to gather several series, or several scenarios, into one
    #  multi-variant object -- for plotting them together, or for feeding a
    #  routine that expects all the paths in one place. The `&` and `|`
    #  operators do the same thing, so `x & y` is `x.hstack(y)`.
    #
    #  **Parameters.** Each entry in `args` is either another `Series` or a
    #  plain number. Series need not share a span: the result covers the
    #  span encompassing all of them and each contributor is padded with
    #  missing values where it does not reach. A number becomes a column of
    #  that same value repeated over the whole span.
    #
    #  **Returns.** A new `Series` whose variants are those of `self`
    #  followed by those of each argument in turn. Nothing is modified in
    #  place. Called with no arguments at all it returns a copy of `self`.
    #
    #  The description is not carried over. The result always has an empty
    #  description, even when every input shared the same one.
    #
    #  **Examples.** Two series of different length, lined up and padded:
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> a = dp.Series(start=dp.qq(2020,1), values=np.array([1., 2.]))
    #      >>> b = dp.Series(start=dp.qq(2020,2), values=np.array([10.]))
    #      >>> a.hstack(b).get_data().tolist()
    #      [[1.0, nan], [2.0, 10.0]]
    #
    # ==========================================================================

    @_dm.reference(category="homogenizing", )
    def clip(
        self,
        new_start: Period | None,
        new_end: Period | None,
    ) -> None:
        r"""
················································································

==Clip time series to a new start and end period==

    self.clip(new_start, new_end)


### Input arguments ###


???+ input "new_start"
    The new start period for the `self` time series; if `None`, the current
    start period is kept.

???+ input "new_end"
    The new end period for the `self` time series; if `None`, the current
    end period is kept.


### Returns ###


???+ returns "None"
    This method modifies `self` in-place and does not return a value.


················································································
        """
        if new_start is None or new_start < self.start:
            new_start = self.start
        if new_end is None or new_end > self.end:
            new_end = self.end
        if new_start == self.start and new_end == self.end:
            return
        self.data = self.get_data_from_until((new_start, new_end, ), )
        self.start = new_start


    # ==========================================================================
    #  ### `clip(new_start, new_end)`
    #
    #  Cuts the time series down to a shorter span.
    #
    #  Use it to drop a burn-in period, an incomplete final year, or anything
    #  outside the sample you mean to work with.
    #
    #  **Parameters.** `new_start` and `new_end` are the first and last
    #  periods to keep. Either may be `None`, which leaves that end where it
    #  is.
    #
    #  Clipping only ever shortens. A `new_start` earlier than the current
    #  start, or a `new_end` later than the current end, is quietly replaced
    #  by the current one, so this cannot be used to pad a series out --
    #  `set_data` or `get_data_from_until` do that.
    #
    #  **Returns.** Nothing; the series is modified in place and the
    #  discarded observations are gone. Copy it first if you need them.
    #
    #  Two edge cases fail badly rather than loudly. Clipping an empty
    #  series raises an error about mismatched frequencies, because there is
    #  no current start to compare against. Clipping to a span that lies
    #  entirely outside the series leaves an object with no data whose
    #  `start` is after its `end`.
    #
    #  **Examples.** A wider request is ignored, a narrower one obeyed:
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(start=dp.qq(2020,1),
    #      ...     values=np.array([1., 2., 3.]))
    #      >>> x.clip(dp.qq(2019,1), None)
    #      >>> x.from_until
    #      (qq(2020,1), qq(2020,3))
    #      >>> x.clip(dp.qq(2020,2), None)
    #      >>> x.get_data().tolist()
    #      [[2.0], [3.0]]
    #
    # ==========================================================================
    def empty(
        self,
        *,
        num_variants: int | None = None
    ) -> None:
        num_variants = num_variants if num_variants is not None else self.num_variants
        self.data = _np.empty((0, num_variants), dtype=self.data_type)

    # ==========================================================================
    #  ### `empty(*, num_variants=None)`
    #
    #  Throws away every observation, keeping the object itself.
    #
    #  Use it to clear a series you mean to refill with `set_data`, and to
    #  change the number of columns at the same time.
    #
    #  **Parameters.** `num_variants` is keyword-only. Left alone the series
    #  keeps the number of variants it has; give a number to empty and
    #  reshape in one step. Any count is accepted, including zero, since
    #  there is no data left to reconcile it with.
    #
    #  **Returns.** Nothing; the series is modified in place.
    #
    #  Unlike `reset`, this leaves `start` and the description untouched. A
    #  stale `start` with no rows behind it makes `end` report the period
    #  just before the start, and `span` report a backwards span. Use
    #  `is_empty` to test for emptiness, and `reset` when you want the start
    #  period cleared as well.
    #
    #  **Examples.**
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(start=dp.qq(2020,1), values=np.array([1., 2.]))
    #      >>> x.empty(num_variants=3)
    #      >>> x.shape, x.is_empty
    #      ((0, 3), True)
    #      >>> x.start
    #      qq(2020,1)
    #
    # ==========================================================================

    @_dm.reference(category="manipulation", )
    def replace_where(
        self,
        test: Callable,
        new_value: Real,
    ) -> None:
        """
················································································

==Replace time series values that pass a test==

    self.replace_where(
        test,
        new_value,
    )


### Input arguments ###


???+ input "self"
    Time series whose observations will be tested and those passing the test
    replaced.

???+ input "test"
    A function (or a Callable) that takes a numpy array and returns `True` or
    `False` for each individual value.

???+ input "new_value"
    The value to replace the observations that pass the test.


### Returns ###


???+ returns "None"
    This method modifies `self` in-place and does not return a value.


················································································
        """
        self.data[test(self.data)] = new_value
        self.trim()

    # ==========================================================================
    #  ### `replace_where(test, new_value)`
    #
    #  Replaces every observation that passes a test with a single value.
    #
    #  The usual use is cleaning: turning placeholder codes, impossible
    #  negatives or zeros into missing values before anything is estimated
    #  on the data.
    #
    #  **Parameters.** `test` is a function that receives the whole
    #  two-dimensional data array at once -- not one value at a time -- and
    #  returns an array of `True` and `False` of the same shape. Ordinary
    #  numpy comparisons do this, so `lambda d: d < 0` is enough. Missing
    #  values are part of the array your test sees, and comparisons against
    #  `nan` are `False`, so `nan` is left alone unless you test for it with
    #  `np.isnan`.
    #
    #  `new_value` is the single value written wherever the test passed.
    #
    #  **Returns.** Nothing; the series is modified in place, across every
    #  variant.
    #
    #  The series is trimmed afterwards. Replacing values at the beginning or
    #  end with `nan` therefore shortens the series and moves `start`, rather
    #  than leaving missing values at the edges.
    #
    #  **Examples.** Blanking the first observation shortens the series:
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(start=dp.qq(2020,1),
    #      ...     values=np.array([-1., 2., 3.]))
    #      >>> x.replace_where(lambda d: d < 0, np.nan)
    #      >>> x.start, x.get_data().tolist()
    #      (qq(2020,2), [[2.0], [3.0]])
    #
    # ==========================================================================

    def _shallow_copy_data(
        self,
        other: Self,
    ) -> None:
        """
        """
        for n in ("start", "data", "data_type", ):
            setattr(self, n, getattr(other, n, ))

    def __and__(self, other):
        """
        Implement the & operator as hstack
        """
        return self.hstack(other, )

    __or__ = __and__

    @_dm.reference(category="manipulation", )
    def trim(self, ) -> None:
        r"""
................................................................................

==Trim time series data==

Trim leading and trailing missing values from the time series data.

    self.trim()

### Input arguments ###

???+ input "self"
    The time series object to trim.

### Returns ###

This method modifies `self` in place and returns `None`.

................................................................................
        """
        if self.data.size == 0:
            self.reset()
            return self
        num_leading, num_trailing \
            = _get_num_leading_trailing_missing_rows(self.data, )
        if num_trailing == self.data.shape[0]:
            self.reset()
            return self
        if not num_leading and not num_trailing:
            return self
        slice_from = num_leading or None
        slice_to = -num_trailing if num_trailing else None
        self.data = self.data[slice_from:slice_to, ...]
        if slice_from:
            self.start += int(slice_from)
        return self

    # ==========================================================================
    #  ### `trim()`
    #
    #  Drops missing rows from both ends of the time series.
    #
    #  A series is stored as one unbroken block, so its span is defined by
    #  its first and last actual observations. Anything that writes or blanks
    #  values at the edges calls this afterwards to restore that; you rarely
    #  need to call it yourself, except after building a series with
    #  `trim=False` or writing straight into `data`.
    #
    #  Only rows missing in *every* variant are dropped, and only at the
    #  ends. Holes in the middle stay where they are.
    #
    #  **Returns.** The series itself, so the call can be chained, even
    #  though the annotation says `None`. The work is done in place either
    #  way.
    #
    #  When every row is missing the series is reset rather than trimmed, and
    #  a reset also erases the description.
    #
    #  **Examples.**
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series.from_start_and_array(dp.qq(2020,1),
    #      ...     np.array([np.nan, 1., np.nan]), trim=False)
    #      >>> x.trim().from_until
    #      (qq(2020,2), qq(2020,2))
    #
    # ==========================================================================

    def _create_expanded_data(self, add_before, add_after):
        return _np.pad(
            self.data, ((add_before, add_after), (0, 0)),
            mode="constant", constant_values=_np.nan,
        )

    def _check_data_shape(self, data, ):
        if data.shape[1] != self.data.shape[1]:
            raise Exception("Time series data being assigned must preserve the number of variants")

    def __bool__(self, ):
        """
        """
        return self.data.size > 0

    def __neg__(self):
        """
        -self
        """
        output = self.copy()
        output.data = -output.data
        return output

    def __pos__(self):
        """
        +self
        """
        return self.copy()

    def __add__(self, other, ) -> Self | _np.ndarray | Real:
        """
        self + other
        """
        # arg = other.data if isinstance(other, type(self)) else other
        return self._binop(other, _op.add, )

    def __radd__(self, other):
        """
        other + self
        """
        return self.apply(lambda data: data.__radd__(other))

    def __mul__(self, other) -> Self|_np.ndarray:
        """
        self + other
        """
        # arg = other.data if isinstance(other, type(self)) else other
        return self._binop(other, _op.mul, )

    def __rmul__(self, other):
        """
        other + self
        """
        return self.apply(lambda data: data.__rmul__(other))

    def __sub__(self, other):
        """
        self - other
        """
        # arg = other.data if isinstance(other, type(self)) else other
        return self._binop(other, _op.sub, )

    def __rsub__(self, other):
        """
        other - self
        """
        return self.apply(lambda data: data.__rsub__(other))

    def __pow__(self, other):
        """
        self ** other
        """
        # FIXME: 1 ** numpy.nan -> 1 !!!!!
        # arg = other.data if isinstance(other, type(self)) else other
        return self._binop(other, _op.pow, )

    def __rpow__(self, other):
        """
        other ** self
        """
        return self.apply(lambda data: data.__rpow__(other))

    def __truediv__(self, other):
        """
        self - other
        """
        # arg = other.data if isinstance(other, type(self)) else other
        return self._binop(other, _op.truediv, )

    def __rtruediv__(self, other):
        """
        other - self
        """
        return self.apply(lambda data: data.__rtruediv__(other))

    def __floordiv__(self, other):
        """
        self // other
        """
        return self._binop(other, _op.floordiv, )

    def __rfloordiv__(self, other):
        """
        other // self
        """
        return self.apply(lambda data: data.__rfloordiv__(other))

    def __mod__(self, other):
        """
        self % other
        """
        return self._binop(other, _op.mod, )

    def __rmod__(self, other, ):
        """
        other % self
        """
        return self.apply(lambda data: data.__rmod__(other))

    def __abs__(self, *args, **kwargs, ) -> Self:
        """
        abs(self)
        """
        new = self.copy()
        new.abs(*args, **kwargs, )
        return new

    def abs(self, *args, **kwargs, ) -> None:
        r"""
        """
        self.data = _np.abs(self.data, *args, **kwargs, )

    # ==========================================================================
    #  ### `abs(*args, **kwargs)`
    #
    #  Replaces every observation with its absolute value.
    #
    #  **Parameters.** `args` and `kwargs` are passed on to `numpy.abs`.
    #  There is no reason to use them here, and the `out` argument in
    #  particular would write somewhere other than the series.
    #
    #  **Returns.** Nothing; the series is modified in place. Use the
    #  built-in `abs(x)` instead when you want a new series and the original
    #  left alone.
    #
    #  Missing values stay missing, and the series is not trimmed
    #  afterwards, so its span does not change.
    #
    #  **Examples.** In place against not in place:
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(start=dp.qq(2020,1), values=np.array([-1., 2.]))
    #      >>> y = abs(x)
    #      >>> x.get_data().tolist(), y.get_data().tolist()
    #      ([[-1.0], [2.0]], [[1.0], [2.0]])
    #      >>> x.abs()
    #      >>> x.get_data().tolist()
    #      [[1.0], [2.0]]
    #
    # ==========================================================================

    def __round__(self, *args, **kwargs, ) -> Self:
        r"""
        """
        new = self.copy()
        new.round(*args, **kwargs, )
        return new

    def round(self, *args, **kwargs, ) -> None:
        self.data = _np.round(self.data, *args, **kwargs, )

    # ==========================================================================
    #  ### `round(*args, **kwargs)`
    #
    #  Rounds every observation in place.
    #
    #  Used mostly for display, or to strip meaningless precision before
    #  writing a series out to a file.
    #
    #  **Parameters.** `args` and `kwargs` are passed on to `numpy.round`, so
    #  the first argument is the number of decimal places, zero when left
    #  out. A negative number rounds to tens, hundreds and so on. Rounding
    #  follows numpy's rule of going to the nearest even number on an exact
    #  half, so 0.5 becomes 0 and 1.5 becomes 2.
    #
    #  **Returns.** Nothing; the series is modified in place and the original
    #  precision is gone. Use the built-in `round(x, n)` instead when you
    #  want a new series and the original left alone.
    #
    #  **Examples.**
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(start=dp.qq(2020,1),
    #      ...     values=np.array([1.234, 2.567]))
    #      >>> x.round(1)
    #      >>> x.get_data().tolist()
    #      [[1.2], [2.6]]
    #
    # ==========================================================================

    for n in ["gt", "lt", "ge", "le", "eq", "ne", ]:
        exec(f"def __{n}__(self, other): return self._binop(other, _op.{n}, )", )

    @_dm.reference(category="comparison", )
    def same_as(self, other: Self, ) -> bool:
        r"""
................................................................................

==Check if two time series are the same==

    self.same_as(other)


### Input arguments ###

???+ input "self"
    The current time series object.

???+ input "other"
    The time series object to compare with the current time series object.


### Returns ###

???+ returns "bool"
    `True` if the two time series are the same by comparing their start dates,
    numerical values, and descriptions; `False` otherwise.

................................................................................
        """
        if not isinstance(other, type(self)):
            return False
        if self.frequency != other.frequency:
            return False
        if self.start != other.start:
            return False
        if not _np.array_equal(self.data, other.data, equal_nan=True, ):
            return False
        if self.get_description() != other.get_description():
            return False
        return True

    # ==========================================================================
    #  ### `same_as(other)`
    #
    #  Says whether two time series carry the same information.
    #
    #  The comparison operators on a series are elementwise -- `x == y`
    #  returns a series of `True` and `False`, not a single answer -- so this
    #  is the method to use when you want one verdict, for a test or a check
    #  after a round trip through a file.
    #
    #  **Parameters.** `other` is the series to compare against. Anything
    #  that is not a `Series` gives `False` rather than an error.
    #
    #  Four things must match: the frequency, the start period, the values,
    #  and the description. Missing values count as equal to each other,
    #  which is what you want after saving and reloading. The description
    #  counting is the surprise -- two series with identical numbers are not
    #  "the same" if only one of them is labelled.
    #
    #  **Returns.** `True` or `False`.
    #
    #  **Examples.** The numbers agree, the labels do not:
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(start=dp.qq(2020,1), values=np.array([1., 2.]),
    #      ...     description="gdp")
    #      >>> y = x.copy()
    #      >>> y.set_description("GDP")
    #      >>> x.same_as(y)
    #      False
    #
    # ==========================================================================

    def apply(self, func, *args, **kwargs, ):
        new_data = func(self.data, *args, **kwargs, )
        axis = kwargs.get("axis", None, )
        if new_data.shape == self.data.shape:
            new = self.copy()
            new._replace_data(new_data, )
            return new
        elif (axis is None or axis == 1) and new_data.shape == (self.data.shape[0], ):
            new = self.copy()
            new.data = new_data.reshape(self.data.shape[0], 1, )
            new.trim()
            return new
        elif axis is None and new_data.shape == ():
            return new_data
        elif axis == 0 and new_data.shape == (self.data.shape[1], ):
            return new_data
        else:
            raise _wrongdoings.Error(
                "Function applied on a time series resulted"
                " in a data array with an unexpected shape"
            )

    # ==========================================================================
    #  ### `apply(func, *args, **kwargs)`
    #
    #  Runs a numpy function over the data and wraps the result back up as a
    #  time series where that makes sense.
    #
    #  This is the escape hatch: anything numpy can do to a two-dimensional
    #  array can be done to a series through here, without unpacking and
    #  rebuilding it by hand.
    #
    #  **Parameters.** `func` receives the whole two-dimensional data array,
    #  one row per period and one column per variant, and any `args` and
    #  `kwargs` you add are passed on to it. In particular `axis` is passed
    #  through to `func` *and* read here to decide what to build from the
    #  answer.
    #
    #  What comes back depends on the shape `func` returned. An array of the
    #  same shape gives a new series with the same span. One value per period
    #  -- what `axis=1` produces -- gives a single-variant series. One value
    #  per variant, from `axis=0`, is returned as a bare numpy array, since
    #  those numbers are not observations in time. A single number is
    #  returned as it is. Any other shape raises `wrongdoings.Error`.
    #
    #  **Returns.** A new `Series`, a numpy array, or a single number,
    #  according to the rules above. The original series is never changed.
    #
    #  **Examples.** Three periods and two variants, so the two rules give
    #  different shapes. Summing across variants gives a series of three
    #  observations, summing across time gives a bare array of two numbers:
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(num_variants=2, start=dp.qq(2020,1),
    #      ...     values=np.array([[1., 2.], [3., 4.], [5., 6.]]))
    #      >>> x.apply(np.sum, axis=1).get_data().tolist()
    #      [[3.0], [7.0], [11.0]]
    #      >>> x.apply(np.sum, axis=0)
    #      array([ 9., 12.])
    #
    # ==========================================================================

    def _binop(self, other, func, new=None, ):
        if not isinstance(other, type(self)):
            return self.apply(lambda data: func(data, other))
        # FIXME: empty encompassing span
        _, *from_until = _periods.get_encompassing_span(self, other)
        self_data = self.get_data_from_until(from_until, )
        other_data = other.get_data_from_until(from_until, )
        new_data = func(self_data, other_data)
        new = Series(num_variants=new_data.shape[1], ) if new is None else new
        new._replace_start_and_values(from_until[0], new_data, )
        return new


    def _replace_data(
        self,
        new_values,
    ) -> None:
        """
        """
        self.data = new_values
        self.trim()

    def _replace_start_and_values(
        self,
        new_start,
        new_values,
    ) -> None:
        """
        """
        self.start = new_start
        self._replace_data(new_values, )

    def iter_dates_values(self, unpack_singleton=True, ):
        """
        Default iterator is line by line, yielding a tuple of (date, values)
        """
        def _unpack_singleton_data_row(data_list: list[Real], ):
            return _has_variants.unpack_singleton(data_list, True, )
        def _keep_data_row(data_list: list[Real], ):
            return data_list
        data_row_func = (
            _unpack_singleton_data_row
            if self.is_singleton and unpack_singleton
            else _keep_data_row
        )
        for date, data_row in zip(self.span, self.data, ):
            yield date, data_row_func(data_row.tolist(), )

    # ==========================================================================
    #  ### `iter_dates_values(unpack_singleton=True)`
    #
    #  Steps through the time series period by period, giving the period and
    #  its observations together.
    #
    #  This is the readable way to walk a series -- printing it, writing it
    #  out row by row, or checking observations against a rule -- without
    #  having to line up `periods` against `get_data` yourself.
    #
    #  **Parameters.** `unpack_singleton` left alone hands you a bare number
    #  for a single-variant series instead of a one-element list. Set it to
    #  `False` to always get a list, which is what you want in code that has
    #  to work for any number of variants. It makes no difference to a series
    #  with several variants, which always yields a list.
    #
    #  **Returns.** A generator of two-element tuples, each a `Period` and
    #  its value or values. It covers the whole span, including periods whose
    #  observations are missing, and it cannot be restricted to part of the
    #  series. Iterating it consumes it; call the method again for a second
    #  pass.
    #
    #  **Examples.**
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(start=dp.qq(2020,1), values=np.array([1., 2.]))
    #      >>> list(x.iter_dates_values())
    #      [(qq(2020,1), 1.0), (qq(2020,2), 2.0)]
    #
    # ==========================================================================

    def iter_variants(self, ) -> Iterator[Self]:
        """
        """
        for data in self.iter_data_variants_from_until(..., ):
            new = self.copy()
            new._replace_data(data, )
            yield new

    # ==========================================================================
    #  ### `iter_variants()`
    #
    #  Steps through the variants of the time series, giving each one back as
    #  a separate single-variant series.
    #
    #  **Returns.** A generator; the annotation names `Iterator`, which this
    #  file never imports.
    #
    #  The method does not work, and there are two faults behind that, not
    #  one. The data handed to each new series is a flat row of numbers
    #  rather than a column, and the trimming that follows expects two
    #  dimensions, so the first step raises
    #  `numpy.exceptions.AxisError: axis 1 is out of bounds for array of
    #  dimension 1`. This happens for a single-variant series as well as a
    #  multi-variant one, so there is no case in which it succeeds. Behind
    #  it, the loop runs over `iter_data_variants_from_until`, which repeats
    #  its last variant for ever, so with the shape fault repaired the method
    #  would yield series without end rather than stopping after the last
    #  variant. To split a series by variant, copy it and call
    #  `extract_variants` on each copy. See the log entry for this file.
    #
    #  **Examples.**
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(num_variants=2, start=dp.qq(2020,1),
    #      ...     values=np.array([[1., 2.], [3., 4.]]))
    #      >>> try:
    #      ...     next(x.iter_variants())
    #      ... except Exception as error:
    #      ...     type(error).__name__
    #      'AxisError'
    #
    # ==========================================================================

    def iter_own_data_variants_from_until(self, from_until, ) -> Iterator[_np.ndarray]:
        """
        Iterates over the data variants from the given start date to the given end date
        """
        if from_until == ...:
            data_from_until = self.data
        else:
            data_from_until = self.get_data_from_until(from_until, )
        return iter(data_from_until.T, )

    # ==========================================================================
    #  ### `iter_own_data_variants_from_until(from_until)`
    #
    #  Steps through the variants of the time series, giving each one back as
    #  a flat numpy array of values over a chosen span.
    #
    #  Unlike `iter_variants` this hands you the raw numbers rather than
    #  series objects, and it works. It is what the routines that treat each
    #  variant separately -- filters, disaggregation -- iterate over.
    #
    #  **Parameters.** `from_until` is a pair of periods, first and last,
    #  both included, and may reach outside the series, in which case the
    #  values are padded with missing observations. Passing `...` instead
    #  means the whole current span.
    #
    #  **Returns.** An iterator over one-dimensional numpy arrays, one per
    #  variant, each holding that variant's values in time order. It stops
    #  after the last variant.
    #
    #  Whether you can write into those arrays safely depends on what you
    #  asked for. With `...` they are views straight onto the series' own
    #  data, so writing into one changes the series. With an explicit
    #  `from_until` they are freshly built and writing into them is harmless.
    #
    #  **Examples.**
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(num_variants=2, start=dp.qq(2020,1),
    #      ...     values=np.array([[1., 2.], [3., 4.]]))
    #      >>> [d.tolist() for d in
    #      ...     x.iter_own_data_variants_from_until(...)]
    #      [[1.0, 3.0], [2.0, 4.0]]
    #
    # ==========================================================================

    def iter_data_variants_from_until(self, from_until, ) -> Iterator[_np.ndarray]:
        """
        Iterates over the data variants from the given start date to the given end date
        """
        return _iterators.exhaust_then_last(self.iter_own_data_variants_from_until(from_until, ), )

    # ==========================================================================
    #  ### `iter_data_variants_from_until(from_until)`
    #
    #  Steps through the variants as flat numpy arrays, and then repeats the
    #  last one for ever.
    #
    #  The endless repetition is the point. It lets a routine walk several
    #  objects side by side -- say twenty simulation draws against a series
    #  holding a single variant -- and have the narrower one keep supplying
    #  its only variant instead of running out. It is the same rule that lets
    #  a one-variant series stand in for a many-variant one throughout the
    #  package.
    #
    #  **Parameters.** `from_until` is a pair of periods, first and last,
    #  both included, or `...` for the whole current span, exactly as in
    #  `iter_own_data_variants_from_until`.
    #
    #  **Returns.** An iterator over one-dimensional numpy arrays that never
    #  stops. Do not write `for d in ...` over it or hand it to `list`; the
    #  loop will not end. Draw from it as many times as you have variants
    #  elsewhere.
    #
    #  **Examples.** The second variant keeps coming back:
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(num_variants=2, start=dp.qq(2020,1),
    #      ...     values=np.array([[1., 2.], [3., 4.]]))
    #      >>> it = x.iter_data_variants_from_until(...)
    #      >>> [next(it).tolist() for _ in range(4)]
    #      [[1.0, 3.0], [2.0, 4.0], [2.0, 4.0], [2.0, 4.0]]
    #
    # ==========================================================================

    def logistic(self, ) -> Self:
        """
        """
        self.data = 1 / (1 + _np.exp(-self.data))

    # ==========================================================================
    #  ### `logistic()`
    #
    #  Replaces every observation with its logistic transform.
    #
    #  The logistic function turns any number into one between zero and one,
    #  following 1 / (1 + exp(-x)). Use it to map an unbounded series onto a
    #  share or a probability -- the inverse of the log-odds transform often
    #  applied before a rate is modelled.
    #
    #  **Returns.** Nothing; the series is modified in place and the original
    #  values are gone, despite the `Self` annotation on the method. Copy the
    #  series first if you need them back.
    #
    #  There is no inverse method in this class, and the series is not
    #  trimmed afterwards, so its span does not change. A missing observation
    #  stays missing.
    #
    #  **Examples.**
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(start=dp.qq(2020,1), values=np.array([0., 1.]))
    #      >>> x.logistic()
    #      >>> x.get_data().round(4).tolist()
    #      [[0.5], [0.7311]]
    #
    # ==========================================================================

    #]

# ==========================================================================
#  ### `Series`
#
#  Holds a numerical time series: rows of observations stored in a numpy
#  array and time stamped by a start period, optionally in several
#  parallel variants.
#
#  A `Series` is the main object in the package. Its values sit in one
#  unbroken block from the first observation to the last, so it is
#  defined by two things only: the period of the first row, `start`, and
#  the array of values, `data`. There is no period-by-period index, and
#  gaps inside the span are held as missing values rather than as absent
#  rows. Leading and trailing missing rows are trimmed away whenever the
#  data changes, which is why the span tracks the actual observations.
#
#  The columns of the array are called variants: alternative paths for
#  the same quantity, such as simulation draws or scenarios, all sharing
#  one span. Most methods work across every variant at once, and a
#  one-variant series is widened automatically when it meets a wider one.
#
#  Most methods change the series in place and return `None`. The
#  exceptions are the arithmetic operators, `copy`, `hstack` and `apply`,
#  which build a new series. When in doubt, copy first.
#
#  The class is assembled from mixins, one per subject area, so its
#  methods are defined across the files of this folder rather than here:
#  indexing, statistics, timing, temporal changes, frequency conversion,
#  extrapolation, moving windows, the Hodrick-Prescott filter, X13
#  seasonal adjustment, plotting, filling and overlaying, and
#  serialization. This file holds the constructor, the accessors, and the
#  housekeeping the others rely on.
#
#  **Returns.** Instances are built with `Series(...)`, or with the class
#  methods `Series.void` and `Series.from_start_and_array`.
#
#  **Examples.** A quarterly series, its span, and its values:
#
#      >>> import numpy as np
#      >>> import datapie as dp
#      >>> x = dp.Series(start=dp.qq(2020,1),
#      ...     values=np.array([1., 2., 3.]), description="gdp")
#      >>> x.from_until
#      (qq(2020,1), qq(2020,3))
#      >>> (x * 2).get_values()
#      (2.0, 4.0, 6.0)
#
# ==========================================================================


def _get_num_leading_trailing_missing_rows(data: _np.ndarray, ):
    r"""
    """
    #[
    # Boolean index of rows with at least one observation
    boolex_observations = ~_np.all(_np.isnan(data, ), axis=1, )
    if _np.all(boolex_observations, ):
        # All rows have at least one observation
        num_leading = 0
        num_trailing = 0
    elif not _np.any(boolex_observations, ):
        # No row has any observation
        num_leading = 0
        num_trailing = data.shape[0]
    else:
        # Some rows have observations
        num_leading = _np.argmax(boolex_observations)
        num_trailing = _np.argmax(boolex_observations[::-1])
    return num_leading, num_trailing
    #]


def hstack(first, *args) -> Self:
    return first.hstack(*args)

# ==========================================================================
#  ### `hstack(first, *args)`
#
#  Stacks time series and numbers side by side into one multi-variant
#  series.
#
#  The plain-function form of the `hstack` method, for when it reads
#  better to write the operation than to call it on one of its arguments.
#  Everything is handed to `first.hstack(...)`, so the behaviour is
#  identical.
#
#  **Parameters.** `first` must be a `Series`, since the work is done by
#  its method; a number in that position raises `AttributeError`. Each
#  entry in `args` is either another `Series` or a plain number. The
#  result spans all of them, each contributor padded with missing values
#  where it does not reach, and a number becomes a column of that value
#  repeated.
#
#  **Returns.** A new `Series` carrying the variants of `first` followed
#  by those of each argument. Nothing is modified in place, and the
#  description is not carried over.
#
#  **Examples.**
#
#      >>> import numpy as np
#      >>> import datapie as dp
#      >>> from datapie.series.main import hstack
#      >>> a = dp.Series(start=dp.qq(2020,1), values=np.array([1., 2.]))
#      >>> b = dp.Series(start=dp.qq(2020,2), values=np.array([10.]))
#      >>> hstack(a, b).get_data().tolist()
#      [[1.0, nan], [2.0, 10.0]]
#
# ==========================================================================


def _create_data_variant_from_number(
    number: Real,
    span: Span,
    data_type: type,
) -> _np.ndarray:
    return _np.full((len(span), 1), number, dtype=data_type)


def _from_periods_and_values(
    self,
    periods: Iterable[Period] | str,
    values: _np.ndarray | Iterable,
    frequency: Frequency | None = None,
    **kwargs,
) -> None:
    r"""
    """
    #[
    # dates = _periods.ensure_period_tuple(dates, frequency=frequency, )
    self.set_data(periods, values, )
    #]


def _from_periods_and_func(
    self,
    periods: Iterable[Period] | str,
    func: Callable,
    frequency: Frequency | None = None,
    **kwargs,
) -> Self:
    """
    Create a new time series from dates and a function
    """
    #[
    # dates = _periods.ensure_period_tuple(dates, frequency=frequency, )
    data = [
        [func() for j in range(self.num_variants)]
        for i in range(len(periods))
    ]
    data = _np.array(data, dtype=self.data_type)
    self.set_data(periods, data)
    #]


def _from_start_and_values(
    self,
    start: Period,
    values: _np.ndarray | Iterable,
    frequency: Frequency | None = None,
    trim: bool = True,
    **kwargs,
) -> None:
    """
    """
    #[
    # start = _periods.ensure_period_tuple(start, frequency=frequency, )[0]
    self.start = start
    if isinstance(values, _np.ndarray):
        values = _reshape_numpy_array(values, )
    else:
        values = _has_variants.iter_variants(values, )
        values = _np.column_stack([
            v for v, _ in zip(values, range(self.num_variants), )
        ])
    values = values.astype(self.data_type, )
    self.data = values
    #
    if trim:
        self.trim()
    #]


def _reshape_numpy_array(values: _np.ndarray, ) -> _np.ndarray:
    r"""
    Reshape numpy array to a 2D array
    """
    #[
    if values.ndim == 2:
        return values
    if values.ndim < 2:
        return values.reshape(-1, 1, )
    if values.ndim > 2:
        return values.reshape(values.shape[0], -1, )
    #]


def _invalid_constructor(
    self,
    **kwargs,
) -> NoReturn:
    raise _wrongdoings.Error("Invalid Series object constructor")


_SERIES_POPULATOR = {
    (False, False, False, False): lambda self, **kwargs: None,
    (True, False, True, False): _from_start_and_values,
    (False, True, True, False): _from_periods_and_values,
    (False, True, False, True): _from_periods_and_func,
}

