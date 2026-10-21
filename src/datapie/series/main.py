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
from . import _ell_one
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


Periods = Period | Iterable[Period] | Span | EllipsisType | None
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
    _ell_one.Mixin,
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
# Time series

==Store observations over time, with one or more parallel variants==

A `Series` holds a continuous run of periods. Its data rows are periods;
its columns are variants, such as alternative forecasts or simulations.
All variants share the same time span. Missing observations are stored as
`numpy.nan`, including gaps between observations.

Many methods change the series in place. Arithmetic operators and the built-in
`abs` and `round` return new series. Available function forms are described
alongside their methods and leave the input series unchanged.

#### Attributes

| Name | Type | Access | Meaning |
| --- | --- | --- | --- |
| `start` | `Period` or `None` | Writable | Period of the first row. Assigning a new start moves the time axis without changing values. |
| `data` | NumPy array | Writable | Values arranged as period rows and variant columns. Direct writes do not automatically trim missing rows. |
| `data_type` | NumPy dtype | Writable | Data type used when creating or converting observations. Assigning it does not convert existing values. |
| `shape` | Pair of integers | Read-only | Number of periods and variants. |
| `num_periods` | Integer | Read-only | Number of rows, including internal missing rows. |
| `num_variants` | Integer | Read-only | Number of columns. |
| `is_singleton` | Boolean | Read-only | Whether there is exactly one variant. |
| `start_period`, `start_date` | `Period` or `None` | Read-only | Other names for reading `start`. |
| `end`, `end_period`, `end_date` | `Period` or `None` | Read-only | Last period, calculated from the start and row count. |
| `span`, `range` | `Span` or empty tuple | Read-only | Inclusive start-to-end span; empty tuple when no start is set. |
| `periods`, `dates` | Tuple of periods | Read-only | All periods in the span. |
| `from_until` | Pair of periods or `None` values | Read-only | Start and end together. |
| `frequency` | `Frequency` | Read-only | Frequency of the start period, or `Frequency.UNKNOWN` without a start. |
| `is_empty` | Boolean | Read-only | Whether there are no data entries, including a series with zero variants. |
| `has_missing` | Boolean | Read-only | Whether any stored value is missing. |

The description is read and changed using `get_description` and `set_description`.

#### Missing observations

`trim` removes rows missing in every variant from the two ends (leading and
trailing missing observations), not from the middle. Several methods trim after
writing data, but direct attribute writes and some transformations do not.
`reset` clears the start and description; `empty` retains them. If the start is
retained with no rows, `end` is the period before the start.

#### See also

[Arithmetic operations](#arithmetic-protocols),
[Comparisons](#comparison-protocols),
[Iteration, combination, and display](#container-protocols),
[`extract_variants`](#extract_variants), [`iter_own_variants`](#iter_own_variants)
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
        period_value_pairs: Iterable[tuple[Period, Any]] | None = None,
        populate: bool = True,
    ) -> None:
        r"""
==Create an empty or populated time series==

#### Syntax

    series = Series(
        start=start,
        values=values,
    )
    series = Series(
        periods=periods,
        values=values,
    )
    series = Series(
        periods=periods,
        func=func,
    )
    series = Series(
        period_value_pairs=period_value_pairs,
    )

#### Input arguments

!!! input "num_variants"

    Integer, default `1`. Number of variants to create. With `start` and a NumPy array, the array determines the number instead.

!!! input "data_type"

    NumPy data type, default `numpy.float64`. Missing values require a type that supports NaN.

!!! input "description"

    Text label, default `""`.

!!! input "start"

    `Period` or `None`, default `None`. First period for the supplied values.

!!! input "start_date"

    Legacy name for `start`, default `None`. Used only when `start` is not supplied.

!!! input "periods"

    Periods to populate, default `None`. Accepts a period iterable or span. With `func`, it must also support `len`.

!!! input "dates"

    Legacy name for `periods`, default `None`. Used only when `periods` is not supplied.

!!! input "frequency"

    `Frequency` or `None`, default `None`. Accepted for compatibility; the supplied periods determine the frequency.

!!! input "values"

    Values to store, default `None`. A NumPy array uses rows for periods
    and columns for variants; a one-dimensional array is one variant.
    A Python list supplies separate variants, while a tuple supplies values
    over time for one variant. With period-based input, the last supplied
    variant is repeated when more variants are requested.

!!! input "func"

    Zero-argument callable, default `None`. Called once for each period and each variant.

!!! input "period_value_pairs"

    Iterable of `(Period, value)` pairs, default `None`. Alternative to separate periods and values; an empty iterable creates an empty series.

!!! input "populate"

    Boolean, default `True`. If `False`, create an empty series without using the population inputs.

#### Returns

!!! returns "series"

    New `Series`. The initializer itself returns `None`.

??? note "Details"

    All inputs are keyword-only. The four combinations shown above are
    supported, as is `Series()` without population inputs. Other combinations
    are not supported.

    Population removes all-missing rows from the edges. If all data are missing,
    the result is reset and its description is cleared.
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
            test = tuple(
                x is not None
                for x in (start, periods, values, func, period_value_pairs, )
            )
            populator = _SERIES_POPULATOR.get(test, _invalid_constructor)
            populator(
                self,
                start=start,
                periods=periods,
                frequency=frequency,
                values=values,
                func=func,
                period_value_pairs=period_value_pairs,
            )

    @_dm.reference(category="constructor", )
    def copy(self, ) -> Self:
        r"""
==Make an independent copy of the series==

#### Syntax

    new_series = series.copy()

#### Returns

!!! returns "new_series"

    New series of the same class, with copied data and start period and the same description. The original is unchanged.
        """
        new = type(self)(populate=False, )
        new.start = None
        if self.start is not None:
            new.start = self.start.copy()
        new.data = _np.array(self.data, )
        new.data_type = self.data_type
        new._description = self._description
        return new

    def _copy_with_no_data(self, ) -> Self:
        r"""
        """
        new = type(self)(populate=False, )
        new.start = self.start
        new._description = self._description
        return new

    @classmethod
    @_dm.reference(category="constructor", )
    def void(
        klass,
        num_variants: int = 1,
        data_type: type = _np.float64,
        description: str = "",
    ) -> Self:
        r"""
==Create an empty series with a chosen number of variants==

#### Syntax

    series = Series.void(
        num_variants=1,
        data_type=numpy.float64,
        description="",
    )

#### Input arguments

!!! input "num_variants"

    Integer, default `1`. Number of variants.

!!! input "data_type"

    NumPy data type, default `numpy.float64`.

!!! input "description"

    Text label, default `""`.

#### Returns

!!! returns "series"

    New empty series with no start period and the requested variants and description.
        """
        return klass(
            num_variants=num_variants,
            data_type=data_type,
            description=description,
            populate=False,
        )

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
==Create a series from a start period and a NumPy array==

#### Syntax

    series = Series.from_start_and_array(
        start,
        array,
        description="",
        trim=True,
    )

#### Input arguments

!!! input "start"

    `Period` for the first row.

!!! input "array"

    NumPy array of observations. Rows are periods and columns are variants; a one-dimensional array becomes one variant.

!!! input "description"

    Text label, default `""`.

!!! input "trim"

    Boolean, default `True`. Remove all-missing rows from both ends.

#### Returns

!!! returns "series"

    New series. The array is not explicitly copied, so values may share storage with the input.

??? note "Details"

    Arrays with more than two dimensions are reshaped to period rows
    and variant columns. If trimming removes all observations, the start and
    description are cleared.
        """
        self = klass()
        self.start = start
        self.data = _reshape_numpy_array(array, )
        self.set_description(description, )
        if trim:
            self.trim()
        return self

    @_dm.reference(category="manipulation", )
    def reset(self, ) -> None:
        r"""
==Clear the series and its description==

#### Syntax

    series.reset()

#### Returns

!!! returns "None"

    Change the series in place. Keep the variant count and data type, but remove all rows, the start period and the description.
        """
        self.__init__(
            num_variants=self.num_variants,
            data_type=self.data_type,
        )

    def _create_periods_of_missing_values(self, num_rows: int = 0, ) -> _np.ndarray:
        """
        """
        return _np.full(
            (num_rows, self.shape[1], ),
            _np.nan,
            dtype=self.data_type,
        )

    @property
    @_dm.reference(category="property", )
    def shape(self, ) -> tuple[int, int]:
        r"""
==Read the period and variant counts==

#### Syntax

    series.shape

#### Returns

!!! returns "value"

    Pair of integers: number of rows and number of columns.

#### See also

[Series attributes](#attributes)
        """
        return self.data.shape

    @property
    @_dm.reference(category="property", )
    def num_periods(self, ) -> int:
        r"""
==Read the number of stored periods==

#### Syntax

    series.num_periods

#### Returns

!!! returns "value"

    Integer row count, including internal missing rows.

#### See also

[Series attributes](#attributes)
        """
        return self.data.shape[0]

    @property
    @_dm.reference(category="property", )
    def num_variants(self, ) -> int:
        r"""
==Read the number of variants==

#### Syntax

    series.num_variants

#### Returns

!!! returns "value"

    Integer column count.

#### See also

[Series attributes](#attributes)
        """
        return self.data.shape[1]

    @property
    @_dm.reference(category="property", )
    def is_singleton(self, ) -> bool:
        r"""
==Test whether there is one variant==

#### Syntax

    series.is_singleton

#### Returns

!!! returns "value"

    Boolean: `True` when exactly one variant is stored.

#### See also

[Series attributes](#attributes)
        """
        return self.data.shape[1] == 1

    @property
    @_dm.reference(category="property", )
    def span(self, ):
        r"""
==Read the stored time span==

#### Syntax

    series.span

#### Returns

!!! returns "value"

    `Span` from start to end, or `()` without a start. Also available as `range`.

#### See also

[Series attributes](#attributes)
        """
        return Span(self.start, self.end, ) if self.start else ()

    range = span

    @property
    @_dm.reference(category="property", )
    def from_until(self, ):
        r"""
==Read the start and end together==

#### Syntax

    series.from_until

#### Returns

!!! returns "value"

    Pair containing the start and end periods.

#### See also

[Series attributes](#attributes)
        """
        return self.start, self.end

    @property
    @_dm.reference(category="property", )
    def periods(self, ) -> tuple[Period, ...]:
        r"""
==Read all periods in the span==

#### Syntax

    series.periods

#### Returns

!!! returns "value"

    Tuple of periods. Also available as `dates`.

#### See also

[Series attributes](#attributes)
        """
        return tuple(self.span, )

    dates = periods

    @property
    @_dm.reference(category="property", call_name="start", )
    def _start(self):
        r"""
==Read or assign the first period==

#### Syntax

    series.start

#### Returns

!!! returns "value"

    `Period` or `None`. The public `start` attribute is writable; assigning a new period changes the time axis, not the values.

#### See also

[Series attributes](#attributes)
        """
        raise NotImplementedError

    @property
    @_dm.reference(category="property", )
    def start_period(self, ):
        r"""
==Read the first period==

#### Syntax

    series.start_period

#### Returns

!!! returns "value"

    `Period` or `None`. Also available as `start_date`; both are read-only names for `start`.

#### See also

[Series attributes](#attributes)
        """
        return self.start

    start_date = start_period

    @property
    @_dm.reference(category="property", )
    def end(self):
        r"""
==Read the last period==

#### Syntax

    series.end

#### Returns

!!! returns "value"

    `Period` or `None`. Also available as `end_period` and `end_date`. A series emptied without clearing its start reports the period before the start.

#### See also

[Series attributes](#attributes)
        """
        return (
            self.start + self.data.shape[0] - 1
            if self.start else None
        )

    end_period = end
    end_date = end

    @property
    @_dm.reference(category="property", )
    def frequency(self, ):
        r"""
==Read the time frequency==

#### Syntax

    series.frequency

#### Returns

!!! returns "value"

    `Frequency` of the start period, or `Frequency.UNKNOWN` without a start.

#### See also

[Series attributes](#attributes)
        """
        return (
            self.start.frequency
            if self.start is not None
            else Frequency.UNKNOWN
        )

    @property
    @_dm.reference(category="property", )
    def is_empty(self, ) -> bool:
        r"""
==Test whether the series has no data entries==

#### Syntax

    series.is_empty

#### Returns

!!! returns "value"

    Boolean; also `True` for a series with zero variants.

#### See also

[Series attributes](#attributes)
        """
        return not self.data.size

    @property
    @_dm.reference(category="property", )
    def has_missing(self, ):
        r"""
==Test whether any stored observation is missing==

#### Syntax

    series.has_missing

#### Returns

!!! returns "value"

    Boolean; `False` for an empty series.

#### See also

[Series attributes](#attributes)
        """
        return bool((not self.is_empty) and _np.isnan(self.data).any())

    @_dm.reference(category="information", )
    def any_missing(self, *args, ) -> bool:
        r"""
==Test whether any selected value is missing==

#### Syntax

    result = series.any_missing(
        *args,
    )

#### Input arguments

!!! input "*args"

    Optional periods followed by variants, as in `get_data`. Omit both to
    inspect the whole series. Requested periods outside its span are missing.

#### Returns

!!! returns "result"

    Boolean: whether any selected value is NaN. An empty selection returns
    `False`. The series is unchanged.

#### See also

[`all_missing`](#all_missing), [`get_data`](#get_data)
        """
        return self._func_missing(_np.any, *args, )

    @_dm.reference(category="information", )
    def where_missing(self, *args, ) -> tuple[Period]:
        r"""
==Find periods with missing selected observations==

#### Syntax

    periods = series.where_missing(
        *args,
    )

#### Input arguments

!!! input "*args"

    Optional periods followed by variants, as in `get_data`. Omit both to
    inspect the whole series. Requested periods outside its span are missing.

#### Returns

!!! returns "periods"

    Tuple of periods with a missing selected variant. The series is unchanged.

With restricted or reordered periods, the reported labels still come from
the beginning of the stored span. Only whole-span requests reliably match
the selected observations to their period labels.

#### See also

[`any_missing`](#any_missing), [`get_data`](#get_data)
        """
        data = self.get_data(*args, )
        missing_mask = _np.isnan(data).any(axis=1, )
        return tuple(p for p, m in zip(self.span, missing_mask, ) if m)

    @_dm.reference(category="information", )
    def all_missing(self, *args, ) -> bool:
        r"""
==Test whether all selected values are missing==

#### Syntax

    result = series.all_missing(
        *args,
    )

#### Input arguments

!!! input "*args"

    Optional periods followed by variants, as in `get_data`. Omit both to
    inspect the whole series. Requested periods outside its span are missing.

#### Returns

!!! returns "result"

    Boolean: whether all selected values are NaN. An empty selection returns
    `True`. The series is unchanged.

#### See also

[`any_missing`](#any_missing), [`get_data`](#get_data)
        """
        return self._func_missing(_np.all, *args, )

    @_dm.reference(category="information", )
    def count_missing(self, *args, ) -> int:
        r"""
==Test whether the missing-value count is nonzero==

#### Syntax

    result = series.count_missing(
        *args,
    )

#### Input arguments

!!! input "*args"

    Optional periods followed by variants, as in `get_data`. Omit both to
    inspect the whole series. Requested periods outside its span are missing.

#### Returns

!!! returns "result"

    Boolean, not a numerical count: whether at least one selected value is
    missing. An empty selection returns `False`. The series is unchanged.

#### See also

[`any_missing`](#any_missing), [`get_data`](#get_data)
        """
        return self._func_missing(_np.count_nonzero, *args, )

    def _func_missing(self, func, *args, ) -> bool:
        """
        """
        data = self.get_data(*args, )
        return bool(func(_np.isnan(data)))

    @_dm.reference(category="manipulation", )
    def set_data(
        self,
        dates: Periods,
        data: Any | Series,
        variants: VariantsRequestType = None,
    ) -> None:
        r"""
==Write observations at selected periods and variants==

#### Syntax

    series.set_data(
        dates,
        data,
        variants=None,
    )

#### Input arguments

!!! input "dates"

    One period, iterable of periods, span, `None` or `...`. `None` and `...` select the current span.

!!! input "data"

    Values to write: a number, NumPy array, tuple, list of variants,
    or another series. Array rows correspond to periods. A list supplies
    variants rather than consecutive observations. A source series is read
    at the requested periods; the last supplied variant is repeated if needed.

!!! input "variants"

    Zero-based integer, iterable of integers, slice or `None`, default `None`. Select columns to write; `None` and `...` select all.

#### Returns

!!! returns "None"

    Change the series in place. Extend the span if necessary, fill intervening rows with NaN, write the selected observations, and trim all-missing edge rows.
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

    def _get_data_and_recreate(
        self,
        *args,
    ) -> _np.ndarray:
        """
        """
        periods, pos, variants, expanded_data, = self._resolve_periods_and_positions(*args, )
        data = expanded_data[_np.ix_(pos, variants)]
        num_variants = data.shape[1]
        new = Series(num_variants=num_variants, data_type=self.data_type, )
        if periods:
            new.set_data(periods, data, )
        return new

    def _resolve_periods_and_positions(
        self,
        periods: Periods | None | EllipsisType = None,
        variants: VariantsRequestType = None,
    ) -> tuple[Iterable[Period], Iterable[int], Iterable[int], _np.ndarray]:
        """
        """
        variants = self._resolve_variants(variants)
        periods = self.resolve_periods(periods, )
        if not periods:
            periods = ()
            pos = ()
            data = self._create_periods_of_missing_values(num_rows=0, )[:, variants]
            return periods, pos, variants, data,
        base_date = self.start or min(periods, )
        pos, add_before, add_after = _get_date_positions(periods, base_date, self.shape[0], )
        expanded_data = self._create_expanded_data(add_before, add_after, )
        if not isinstance(pos, Iterable):
            pos = (pos, )
        return periods, pos, variants, expanded_data,

    @_dm.reference(category="manipulation", )
    def alter_num_variants(
        self,
        new_num: int,
    ) -> Self:
        r"""
==Change the number of variants==

#### Syntax

    series.alter_num_variants(
        new_num,
    )

#### Input arguments

!!! input "new_num"

    Required nonnegative integer target count. Expansion copies the final
    variant; shrinking removes columns from the right. Expansion requires at
    least one existing variant to copy.

#### Returns

!!! returns "None"

    Change the data columns in place, without trimming rows or changing the
    start or description. An equal target leaves the series unchanged.

Despite its return annotation, this method does not return the series.
Use `extract_variants` to keep or reorder particular columns.

There is no top-level function form.

#### See also

[`expand_num_variants`](#expand_num_variants), [`shrink_num_variants`](#shrink_num_variants), [`extract_variants`](#extract_variants)
        """
        if new_num < self.num_variants:
            self.shrink_num_variants(new_num, )
        elif new_num > self.num_variants:
            self.expand_num_variants(new_num, )

    @_dm.reference(category="manipulation", )
    def expand_num_variants(
        self,
        new_num: int,
    ) -> None:
        r"""
==Add copies of the last variant==

#### Syntax

    series.expand_num_variants(
        new_num,
    )

#### Input arguments

!!! input "new_num"

    Required integer target count, at least the current count. Smaller
    targets raise `ValueError`. At least one existing column is required,
    even when the target equals the current count.

#### Returns

!!! returns "None"

    Append copies of the final column in place, including its missing
    observations. Existing columns, time span, and description are retained;
    no trimming follows. An equal target adds no columns.

A zero-variant series raises an indexing error because it has no final column
to copy.

There is no top-level function form.

#### See also

[`alter_num_variants`](#alter_num_variants), [`shrink_num_variants`](#shrink_num_variants)
        """
        add = new_num - self.num_variants
        if add < 0:
            raise ValueError("Use shrink_num_variants to shrink the number of variants")
        data = _np.tile(self.data[:, (-1, )], (1, add, ))
        self.data = _np.hstack((self.data, data, ), )

    @_dm.reference(category="manipulation", )
    def shrink_num_variants(
        self,
        new_num: int,
    ) -> None:
        r"""
==Remove variants from the right==

#### Syntax

    series.shrink_num_variants(
        new_num,
    )

#### Input arguments

!!! input "new_num"

    Required nonnegative integer target count, smaller than the current
    count. Larger targets raise `ValueError`.

#### Returns

!!! returns "None"

    Remove trailing columns in place without trimming rows or changing the
    start or description. A target of zero removes all columns.

An equal target also removes all columns: the implementation slices to
`:-0` in this case. Use `alter_num_variants` when an equal target should leave
the series unchanged.

There is no top-level function form.

#### See also

[`alter_num_variants`](#alter_num_variants), [`expand_num_variants`](#expand_num_variants)
        """
        remove = self.num_variants - new_num
        if remove < 0:
            raise ValueError("Use expand_num_variants to expand the number of variants")
        self.data = self.data[:, :-remove]

    @_dm.reference(category="information", )
    def get_values(
        self,
        *args,
        unpack_singleton: bool = True,
        **kwargs,
    ) -> list[tuple[Real, ...]] | tuple[Real, ...]:
        r"""
==Read selected values as ordinary Python tuples==

#### Syntax

    values = series.get_values(
        *args,
        unpack_singleton=True,
        **kwargs,
    )

#### Input arguments

!!! input "*args"

    Optional periods followed by variants, passed to `get_data`.

!!! input "**kwargs"

    Named inputs passed to `get_data`. The period selector is `periods`; variant selection is positional.

!!! input "unpack_singleton"

    Boolean, default `True`. If `False`, return one tuple per variant in a list. If `True`, return the first variant only, even when several variants are selected.

#### Returns

!!! returns "values"

    Tuple for the first variant, or list of tuples when unpacking is disabled. The series is unchanged.

#### See also

[`get_data_and_periods`](#get_data_and_periods), [`get_data_from_until`](#get_data_from_until)
        """
        data = self.get_data(*args, **kwargs, )
        values = [ tuple(data_column.tolist()) for data_column in data.T ]
        return _has_variants.unpack_singleton(
            values,
            unpack_singleton=unpack_singleton,
        )

    @_dm.reference(category="information", )
    def get_data(self, *args, **kwargs, ) -> _np.ndarray:
        r"""
==Read selected observations as a NumPy array==

#### Syntax

    data = series.get_data(
        periods,
        variants,
    )
    data = series.get_data()

#### Input arguments

!!! input "*args"

    The first input selects periods; the second selects variants.
    Omitting them selects the current span and all variants. Periods can be
    a period, iterable, span, `None` or `...`; variants can be an integer,
    integer iterable, slice, `None` or `...`. The period input can also be
    named `periods`; variant selection is positional.

!!! input "**kwargs"

    Named period selection, supplied as `periods`. Omit it to read the current span.

#### Returns

!!! returns "data"

    Independent two-dimensional NumPy array, with period rows and variant columns. Requested periods outside the series contain NaN. Reading does not change the series.

#### See also

[`get_data_and_periods`](#get_data_and_periods), [`get_data_from_until`](#get_data_from_until)
        """
        return self.get_data_and_periods(*args, **kwargs, )[0]

    @_dm.reference(category="information", )
    def get_data_and_periods(
        self,
        periods: Iterable[Period] | None | EllipsisType = ...,
        *args,
    ) -> _np.ndarray:
        r"""
==Read observations together with their periods==

#### Syntax

    data, periods = series.get_data_and_periods(
        periods,
        *args,
    )

#### Input arguments

!!! input "periods"

    Default `...` selects the stored span. Period, iterable of periods, or span. `None`, `...`, and `slice(None)`
    select the stored span. Open-ended spans resolve against the series.
    Request order and duplicate periods are retained.

!!! input "*args"

    Optional positional variant selector: zero-based integer, integer iterable,
    slice, `None`, or `...`. Omitted, `None`, and `...` select all columns.
    Negative indexes count from the end; order and duplicates are retained.
    This selector cannot be supplied by keyword.

#### Returns

!!! returns "data, periods"

    Pair of an independent two-dimensional NumPy array and the tuple of
    resolved periods. Rows correspond to periods; columns correspond to variants.
    Out-of-span observations contain NaN.

Reading does not change or extend the series. Use a data type supporting NaN
for out-of-span requests.
The result is a pair despite the array-only return annotation.

There is no top-level function form.

#### See also

[`get_data`](#get_data), [`get_values`](#get_values), [`get_data_from_until`](#get_data_from_until)
        """
        periods, pos, variants, expanded_values, = self._resolve_periods_and_positions(periods, *args, )
        return expanded_values[_np.ix_(pos, variants)], periods,

    @_dm.reference(category="information", )
    def get_data_variant(
        self,
        periods: Periods,
        variant: Real | None = None,
    ) -> _np.ndarray:
        r"""
==Read one variant at selected periods==

#### Syntax

    data = series.get_data_variant(
        periods,
        variant=None,
    )

#### Input arguments

!!! input "periods"

    Required. Period, iterable of periods, or span. `None`, `...`, and `slice(None)`
    select the stored span. Open-ended spans resolve against the series.
    Request order and duplicate periods are retained.

!!! input "variant"

    Zero-based integer column index; default `None` selects the first column.
    Zero and indexes greater than or equal to the variant count also select
    the first column. Negative indexes count from the end and must be in range.

#### Returns

!!! returns "data"

    Independent two-dimensional NumPy array with one column and one row per
    requested period. Out-of-span observations contain NaN.

Reading does not change or extend the series. Use a data type supporting NaN
for out-of-span requests.
At least one variant is required.

There is no top-level function form.

#### See also

[`get_data`](#get_data), [`get_data_variant_from_until`](#get_data_variant_from_until)
        """
        variant = variant if variant and variant<self.data.shape[1] else 0
        return self.get_data(periods, variant, )

    @_dm.reference(category="information", )
    def get_data_from_until(
        self,
        from_until,
        *args,
    ) -> _np.ndarray:
        r"""
==Read observations between two periods==

#### Syntax

    data = series.get_data_from_until(
        from_until,
        *args,
    )

#### Input arguments

!!! input "from_until"

    Required pair of first and last periods, inclusive. Read all intervening
    periods. Reversed endpoints give no rows. `(None, None)` gives an empty
    block, not the stored span. A single `None` is not an open-end selector;
    `...` is not supported.

!!! input "*args"

    Optional positional variant selector: zero-based integer, integer iterable,
    slice, `None`, or `...`. Omitted, `None`, and `...` select all columns.
    Negative indexes count from the end; order and duplicates are retained.
    This selector cannot be supplied by keyword.

#### Returns

!!! returns "data"

    Independent two-dimensional NumPy array with interval rows and selected
    variant columns. Out-of-span observations contain NaN.

Reading does not change or extend the series. Use a data type supporting NaN
for out-of-span requests.
Use `get_data()` for the stored span, or `get_data((first, last))` to read
just two endpoint observations rather than the whole interval.

There is no top-level function form.

#### See also

[`get_data`](#get_data), [`get_data_variant_from_until`](#get_data_variant_from_until)
        """
        if all(p is None for p in from_until):
            from_until = ()
        _, pos, variants, expanded_data = self._resolve_periods_and_positions(from_until, *args, )
        if not pos:
            return self._create_periods_of_missing_values(num_rows=0, )[:, variants]
        from_pos, to_pos, = pos[0], pos[-1]+1,
        return expanded_data[from_pos:to_pos, variants]

    @_dm.reference(category="information", )
    def get_data_variant_from_until(
        self,
        from_until: Iterable[Period],
        variant: int | None = None,
    ) -> _np.ndarray:
        r"""
==Read one variant between two periods==

#### Syntax

    data = series.get_data_variant_from_until(
        from_until,
        variant=None,
    )

#### Input arguments

!!! input "from_until"

    Required pair of first and last periods, inclusive. Read all intervening
    periods. Reversed endpoints give no rows. `(None, None)` gives an empty
    block, not the stored span. A single `None` is not an open-end selector;
    `...` is not supported.

!!! input "variant"

    Zero-based integer column index; default `None` selects the first column.
    Zero and indexes greater than or equal to the variant count also select
    the first column. Negative indexes count from the end and must be in range.

#### Returns

!!! returns "data"

    Independent two-dimensional NumPy array with one column and interval
    rows. Out-of-span observations contain NaN.

Reading does not change or extend the series. Use a data type supporting NaN
for out-of-span requests.
At least one variant is required.

There is no top-level function form.

#### See also

[`get_data_variant`](#get_data_variant), [`get_data_from_until`](#get_data_from_until)
        """
        variant = variant if variant and variant < self.data.shape[1] else 0
        return self.get_data_from_until(from_until, variant, )

    @_dm.reference(category="manipulation", )
    def extract_variants(
        self,
        variants,
    ) -> None:
        r"""
==Keep and reorder selected variants==

#### Syntax

    series.extract_variants(
        variants,
    )

#### Input arguments

!!! input "variants"

    Required zero-based integer or iterable of integers. Keep columns in
    request order, including duplicates. Negative indexes count from the end;
    out-of-range indexes raise an indexing error. An empty iterable keeps no
    columns. `None`, `...`, and slices are not general all-variant selectors
    here, unlike selectors accepted by data retrieval methods.

#### Returns

!!! returns "None"

    Replace the data columns in place with the selection. Retain time rows,
    start, and description. No trimming follows, even when all retained
    observations are missing or no columns remain.

Copy the series first to preserve the original column selection.

There is no top-level function form.

#### See also

[`alter_num_variants`](#alter_num_variants), [`iter_own_variants`](#iter_own_variants)
        """
        if not isinstance(variants, Iterable):
            variants = (variants, )
        else:
            variants = tuple(c for c in variants)
        self.data = self.data[:, variants]

    @_dm.reference(category="manipulation", )
    def set_start(
        self,
        new_start: Period,
    ) -> Self:
        r"""
==Move the time axis to a new first period==

#### Syntax

    series.set_start(
        new_start,
    )

#### Input arguments

!!! input "new_start"

    Replacement `Period`. Its frequency is not checked against the current one.

#### Returns

!!! returns "series"

    The same series, changed in place. Values are unchanged.
        """
        self.start = new_start
        return self

    @_dm.reference(category="indexing", )
    def resolve_periods(self, periods, ) -> tuple[Period]:
        r"""
==Resolve a period selection against the series==

#### Syntax

    periods = series.resolve_periods(
        periods,
    )

#### Input arguments

!!! input "periods"

    Period, iterable of periods, span, `None`, `...` or `slice(None)`. `None`, `...` and the empty slice select the current span; open-ended spans are resolved against the series.

#### Returns

!!! returns "periods"

    Tuple of selected periods in request order. A whole-span request without a start returns an empty tuple. The series is unchanged.
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

    @_dm.reference(category="multiple", )
    def hstack(self, *args, ):
        r"""
==Combine series side by side as variants==

#### Syntax

    new_series = series.hstack(
        *args,
    )

#### Input arguments

!!! input "*args"

    Additional series, appended in order. Spans are aligned to cover all inputs; uncovered periods are filled with NaN. Plain numbers are not generally supported.

#### Returns

!!! returns "new_series"

    New combined series with an empty description. With no additional inputs, return a copy preserving the description. Input series are unchanged.

#### See also

[Iteration, combination, and display](#container-protocols)
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


    @_dm.reference(category="homogenizing", )
    def clip(
        self,
        new_start: Period | None,
        new_end: Period | None,
    ) -> None:
        r"""
==Keep observations within an inclusive period interval==

#### Syntax

    series.clip(
        new_start,
        new_end,
    )

#### Input arguments

!!! input "new_start"

    `Period` or `None`. First period to keep; `None` retains the current start.

!!! input "new_end"

    `Period` or `None`. Last period to keep; `None` retains the current end.

#### Returns

!!! returns "None"

    Shorten the series in place. Bounds beyond the existing span do not extend it. No additional trimming follows.

??? note "Details"

    A disjoint or reversed interval can leave no rows while retaining a start period.
        """
        if new_start is None or new_start < self.start:
            new_start = self.start
        if new_end is None or new_end > self.end:
            new_end = self.end
        if new_start == self.start and new_end == self.end:
            return
        self.data = self.get_data_from_until((new_start, new_end, ), )
        self.start = new_start


    @_dm.reference(category="manipulation", )
    def empty(
        self,
        *,
        num_variants: int | None = None
    ) -> None:
        r"""
==Remove all observations while keeping the start and description==

#### Syntax

    series.empty(
        num_variants=None,
    )

#### Input arguments

!!! input "num_variants"

    Integer or `None`, default `None`. Optional new variant count; `None` keeps the current count.

#### Returns

!!! returns "None"

    Change the series in place. Keep the start, description and data type. Use `reset` to clear the start and description too.
        """
        num_variants = num_variants if num_variants is not None else self.num_variants
        self.data = _np.empty((0, num_variants), dtype=self.data_type)

    @_dm.reference(category="manipulation", )
    def replace_where(
        self,
        test: Callable,
        new_value: Real,
    ) -> None:
        r"""
==Replace observations that satisfy a test==

#### Syntax

    series.replace_where(
        test,
        new_value,
    )

#### Input arguments

!!! input "test"

    Callable receiving the whole data array and normally returning a Boolean mask selecting values to replace.

!!! input "new_value"

    Number to write at the selected positions.

#### Returns

!!! returns "None"

    Change the series in place, then trim all-missing edge rows. The test receives the live data and can itself change it.
        """
        self.data[test(self.data)] = new_value
        self.trim()

    def _shallow_copy_data(
        self,
        other: Self,
    ) -> None:
        """
        """
        for n in ("start", "data", "data_type", ):
            setattr(self, n, getattr(other, n, ))

    @_dm.reference(category="information", )
    def __iter__(self, ):
        r"""
==Read each variant once==

#### See also

[Iteration, combination, and display](#container-protocols)
        """
        return self.iter_own_variants()

    @_dm.reference(category="information", )
    def __and__(self, other, ):
        r"""
==Combine series as additional variants==

#### See also

[Iteration, combination, and display](#container-protocols)
        """
        return self.hstack(other, )

    __or__ = __and__

    @_dm.reference(category="manipulation", )
    def trim(self, ) -> None:
        r"""
==Remove missing rows from the two ends==

#### Syntax

    series.trim()

#### Returns

!!! returns "series"

    The same series, changed in place. Only rows missing in every variant are removed; gaps in the middle remain. Empty or all-missing data are reset, clearing the start and description.
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

    def _create_expanded_data(self, add_before, add_after, ):
        num_variants = self.num_variants
        data_before = _np.full((add_before, num_variants), _np.nan, dtype=self.data_type, )
        data_after = _np.full((add_after, num_variants), _np.nan, dtype=self.data_type, )
        return _np.concatenate((data_before, self.data, data_after, ), axis=0, )

    def _check_data_shape(self, data, ):
        if data.shape[1] != self.data.shape[1]:
            raise Exception("Time series data being assigned must preserve the number of variants")

    @_dm.reference(category="information", )
    def __bool__(self, ):
        r"""
==Test whether the series contains data entries==

#### See also

[Iteration, combination, and display](#container-protocols)
        """
        return self.data.size > 0

    @_dm.reference(category="manipulation", )
    def __neg__(self):
        r"""
==Negate observations in a copy==

#### See also

[Arithmetic operations](#arithmetic-protocols)
        """
        output = self.copy()
        output.data = -output.data
        return output

    @_dm.reference(category="manipulation", )
    def __pos__(self):
        r"""
==Return a copy==

#### See also

[Arithmetic operations](#arithmetic-protocols)
        """
        return self.copy()

    @_dm.reference(category="manipulation", )
    def __add__(self, other, ) -> Self | _np.ndarray | Real:
        r"""
==Add aligned observations==

#### See also

[Arithmetic operations](#arithmetic-protocols)
        """
        # arg = other.data if isinstance(other, type(self)) else other
        return self._binop(other, _op.add, )

    @_dm.reference(category="manipulation", )
    def __radd__(self, other):
        r"""
==Add the series to a left operand==

#### See also

[Arithmetic operations](#arithmetic-protocols)
        """
        return self.apply(lambda data: data.__radd__(other))

    @_dm.reference(category="manipulation", )
    def __mul__(self, other) -> Self|_np.ndarray:
        r"""
==Multiply aligned observations==

#### See also

[Arithmetic operations](#arithmetic-protocols)
        """
        # arg = other.data if isinstance(other, type(self)) else other
        return self._binop(other, _op.mul, )

    @_dm.reference(category="manipulation", )
    def __rmul__(self, other):
        r"""
==Multiply a left operand by the series==

#### See also

[Arithmetic operations](#arithmetic-protocols)
        """
        return self.apply(lambda data: data.__rmul__(other))

    @_dm.reference(category="manipulation", )
    def __sub__(self, other):
        r"""
==Subtract aligned observations==

#### See also

[Arithmetic operations](#arithmetic-protocols)
        """
        # arg = other.data if isinstance(other, type(self)) else other
        return self._binop(other, _op.sub, )

    @_dm.reference(category="manipulation", )
    def __rsub__(self, other):
        r"""
==Subtract observations from a left operand==

#### See also

[Arithmetic operations](#arithmetic-protocols)
        """
        return self.apply(lambda data: data.__rsub__(other))

    @_dm.reference(category="manipulation", )
    def __pow__(self, other):
        r"""
==Raise aligned observations to powers==

#### See also

[Arithmetic operations](#arithmetic-protocols)
        """
        # FIXME: 1 ** numpy.nan -> 1 !!!!!
        # arg = other.data if isinstance(other, type(self)) else other
        return self._binop(other, _op.pow, )

    @_dm.reference(category="manipulation", )
    def __rpow__(self, other):
        r"""
==Raise a left operand to series powers==

#### See also

[Arithmetic operations](#arithmetic-protocols)
        """
        return self.apply(lambda data: data.__rpow__(other))

    @_dm.reference(category="manipulation", )
    def __truediv__(self, other):
        r"""
==Divide aligned observations==

#### See also

[Arithmetic operations](#arithmetic-protocols)
        """
        # arg = other.data if isinstance(other, type(self)) else other
        return self._binop(other, _op.truediv, )

    @_dm.reference(category="manipulation", )
    def __rtruediv__(self, other):
        r"""
==Divide a left operand by observations==

#### See also

[Arithmetic operations](#arithmetic-protocols)
        """
        return self.apply(lambda data: data.__rtruediv__(other))

    @_dm.reference(category="manipulation", )
    def __floordiv__(self, other):
        r"""
==Floor-divide aligned observations==

#### See also

[Arithmetic operations](#arithmetic-protocols)
        """
        return self._binop(other, _op.floordiv, )

    @_dm.reference(category="manipulation", )
    def __rfloordiv__(self, other):
        r"""
==Floor-divide a left operand by observations==

#### See also

[Arithmetic operations](#arithmetic-protocols)
        """
        return self.apply(lambda data: data.__rfloordiv__(other))

    @_dm.reference(category="manipulation", )
    def __mod__(self, other):
        r"""
==Calculate aligned remainders==

#### See also

[Arithmetic operations](#arithmetic-protocols)
        """
        return self._binop(other, _op.mod, )

    @_dm.reference(category="manipulation", )
    def __rmod__(self, other, ):
        r"""
==Calculate left-operand remainders==

#### See also

[Arithmetic operations](#arithmetic-protocols)
        """
        return self.apply(lambda data: data.__rmod__(other))

    @_dm.reference(category="manipulation", )
    def __abs__(self, *args, **kwargs, ) -> Self:
        r"""
==Return a copy with absolute observations==

#### See also

[Arithmetic operations](#arithmetic-protocols)
        """
        new = self.copy()
        new.abs(*args, **kwargs, )
        return new

    @_dm.reference(category="manipulation", )
    def abs(self, *args, **kwargs, ) -> None:
        r"""
==Replace observations with their absolute values==

#### See also

[Elementwise functions](#elementwise-functions) for syntax, arguments,
return values, and mutation behavior.
        """
        self.data = _np.abs(self.data, *args, **kwargs, )

    @_dm.reference(category="manipulation", )
    def __round__(self, *args, **kwargs, ) -> Self:
        r"""
==Return a copy with rounded observations==

#### See also

[Arithmetic operations](#arithmetic-protocols)
        """
        new = self.copy()
        new.round(*args, **kwargs, )
        return new

    @_dm.reference(category="manipulation", )
    def round(self, *args, **kwargs, ) -> None:
        r"""
==Round observations to a chosen precision==

#### See also

[Elementwise functions](#elementwise-functions) for syntax, arguments,
return values, and mutation behavior.
        """
        self.data = _np.round(self.data, *args, **kwargs, )

    for n in ["gt", "lt", "ge", "le", "eq", "ne", ]:
        exec(f"def __{n}__(self, other): return self._binop(other, _op.{n}, )", )

    for _comparison_name in ("gt", "lt", "ge", "le", "eq", "ne", ):
        _comparison_method = locals()[f"__{_comparison_name}__"]
        _comparison_method.__doc__ = (
            "==Compare observations elementwise==\n\n"
            "#### See also\n\n"
            "[Comparisons](#comparison-protocols)"
        )
        _dm.reference(category="comparison", )(_comparison_method)


    @_dm.reference(category="comparison", )
    def same_as(self, other: Self, ) -> bool:
        r"""
==Test whether two series contain the same information==

#### Syntax

    result = series.same_as(
        other,
    )

#### Input arguments

!!! input "other"

    Series to compare. An object of an incompatible class returns `False`.

#### Returns

!!! returns "result"

    Boolean. Frequency, start, values and description must match; corresponding NaNs count as equal. Neither series is changed.

#### See also

[Comparisons](#comparison-protocols)
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

    @_dm.reference(category="manipulation", )
    def apply(self, func, *args, **kwargs, ):
        r"""
==Apply a callable to the observation array==

#### Syntax

    result = series.apply(
        func,
        *args,
        **kwargs,
    )

#### Input arguments

!!! input "func"

    Callable receiving the whole stored data array. It must return a NumPy-style array or scalar, not a plain Python number.

!!! input "*args"

    Additional positional inputs passed to the callable.

!!! input "**kwargs"

    Named inputs passed to the callable. The `axis` option, if supplied, also determines how the result is returned.

#### Returns

!!! returns "result"

    A new series for results with observations over time, or the callable's array or scalar for a reduction over time. Unsupported result sizes raise an error.

#### Mutation

The callable receives live data and may change the original series. Use a callable that does not modify its input when the original must be preserved.

??? note "Details"

    A result with the same dimensions as the input becomes a new series.
    One result per period also becomes a series when `axis` is omitted or `1`.
    A scalar is returned directly when `axis` is omitted. One result per
    variant is returned directly when `axis=0`. Series results are trimmed.
        """
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
        num_dimes = new_values.ndim
        if num_dimes == 1:
            new_values = new_values.reshape(-1, 1)
        elif num_dimes > 2:
            new_values = new_values.reshape(new_values.shape[0], -1)
        self.data = new_values
        self.data_type = new_values.dtype
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

    @_dm.reference(category="information", )
    def iter_periods_and_values(self, unpack_singleton=True, ):
        r"""
==Read each period together with its values==

#### Syntax

    iterator = series.iter_periods_and_values(
        unpack_singleton=True,
    )

#### Input arguments

!!! input "unpack_singleton"

    Boolean, default `True`. For a single variant, yield a number instead of a one-item list. With `False`, always yield lists.

#### Returns

!!! returns "iterator"

    Finite iterator of `(Period, values)` pairs over the whole span, including missing observations. Reading does not change the series.
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
        for period, data_row in zip(self.span, self.data, ):
            yield period, data_row_func(data_row.tolist(), )

    @_dm.reference(category="information", )
    def iter_variants(self, ) -> Iterator[Self]:
        r"""
==Read variants and keep repeating the last==

#### Syntax

    iterator = series.iter_variants()

#### Returns

!!! returns "iterator"

    Iterator of single-variant series in column order, followed by the final
    variant indefinitely. Each yielded series is trimmed at both ends; an
    all-missing variant becomes a reset, empty series.

At least one variant is required; a zero-variant input fails when consumed.
Use a bounded consumer rather than converting this infinite iterator to a list.
Iteration itself does not change the receiver. Yielded series retain its
description unless reset and can share observation storage with it; copy before
modifying when independence matters.

There is no top-level function form.

#### See also

[`iter_own_variants`](#iter_own_variants), [`iter_data_variants_from_until`](#iter_data_variants_from_until)
        """
        for data in self.iter_data_variants_from_until(..., ):
            new = self._copy_with_no_data()
            new._replace_data(data, )
            yield new

    @_dm.reference(category="information", )
    def iter_own_variants(self, ) -> Iterator[Self]:
        r"""
==Read each variant once as a series==

#### Syntax

    iterator = series.iter_own_variants()

#### Returns

!!! returns "iterator"

    Finite iterator of single-variant series, in column order. Zero variants
    give an empty iterator. Each yielded series is trimmed at both ends;
    an all-missing variant becomes a reset, empty series.

Iteration itself does not change the receiver. Yielded series retain the
original description unless reset, but can share their observation storage with
the original. Copy a yielded series before modifying it if independence matters.
The built-in `iter(series)` uses this finite iterator too.

There is no top-level function form.

#### See also

[`iter_variants`](#iter_variants), [`iter_own_data_variants_from_until`](#iter_own_data_variants_from_until), [`iter_periods_and_values`](#iter_periods_and_values)
        """
        for data in self.iter_own_data_variants_from_until(..., ):
            new = self._copy_with_no_data()
            new._replace_data(data, )
            yield new

    @_dm.reference(category="information", )
    def iter_own_data_variants_from_until(self, from_until, ) -> Iterator[_np.ndarray]:
        r"""
==Read each variant's data once==

#### Syntax

    iterator = series.iter_own_data_variants_from_until(
        from_until,
    )

#### Input arguments

!!! input "from_until"

    Required pair of first and last periods, inclusive, or `...` for the
    stored span. With explicit endpoints, all intervening periods are read
    and out-of-span values contain NaN. Reversed endpoints and `(None, None)`
    give no rows. A single `None` is not an open-end selector.

#### Returns

!!! returns "iterator"

    Finite iterator of one-dimensional NumPy arrays, one per variant in
    column order. Zero variants give an empty iterator. Missing values and
    all-missing edge rows are retained.

With `...`, the arrays are views of the original data: writing through them
changes the series without automatic trimming. Explicit endpoints first create
an independent data block, so its yielded column arrays do not share storage
with the original. Iteration itself does not mutate or extend the series.
Use a data type supporting NaN for out-of-span requests.

There is no top-level function form.

#### See also

[`iter_data_variants_from_until`](#iter_data_variants_from_until), [`iter_own_variants`](#iter_own_variants), [`get_data_from_until`](#get_data_from_until)
        """
        if from_until is ...:
            data_from_until = self.data
        else:
            data_from_until = self.get_data_from_until(from_until, )
        return iter(data_from_until.T, )

    @_dm.reference(category="information", )
    def iter_data_variants_from_until(self, from_until, ) -> Iterator[_np.ndarray]:
        r"""
==Read variant data and keep repeating the last==

#### Syntax

    iterator = series.iter_data_variants_from_until(
        from_until,
    )

#### Input arguments

!!! input "from_until"

    Required pair of first and last periods, inclusive, or `...` for the
    stored span. With explicit endpoints, all intervening periods are read
    and out-of-span values contain NaN. Reversed endpoints and `(None, None)`
    give no rows. A single `None` is not an open-end selector.

#### Returns

!!! returns "iterator"

    Iterator of one-dimensional NumPy arrays in column order, then the last
    array indefinitely. It repeats the same final array object, not a fresh
    copy. With zero variants, it yields `None` indefinitely.

Use a bounded consumer rather than converting this infinite iterator to a list.
Missing values and all-missing edge rows are retained. With `...`, arrays share
the original data, so writes change the series without automatic trimming.
Explicit endpoints create an independent data block first. Iteration itself
does not mutate or extend the series. Use a data type supporting NaN for
out-of-span requests.

There is no top-level function form.

#### See also

[`iter_own_data_variants_from_until`](#iter_own_data_variants_from_until), [`iter_variants`](#iter_variants), [`get_data_from_until`](#get_data_from_until)
        """
        return _iterators.exhaust_then_last(self.iter_own_data_variants_from_until(from_until, ), )

    @_dm.reference(category="manipulation", )
    def logistic(self, ) -> Self:
        r"""
==Replace observations with their logistic values==

#### See also

[Elementwise functions](#elementwise-functions) for syntax, arguments,
return values, and mutation behavior.
        """
        self.data = 1 / (1 + _np.exp(-self.data))




    @staticmethod
    @_dm.topic(title="Arithmetic operations", anchor="arithmetic-protocols", priority=30)
    def _document_arithmetic_protocols():
        r"""
==Calculate arithmetic results from series observations==

### Syntax

    +series
    -series
    series + other
    series - other
    series * other
    series / other
    series // other
    series % other
    series ** other
    abs(series)
    round(series, ndigits)

### Input arguments

!!! input "other"

    Another series or a compatible number or array. Series are aligned over their combined span; uncovered periods contain NaN. A single variant can be combined with several variants.

!!! input "ndigits"

    Integer decimal places, default `0`, for the built-in `round`.

### Returns

!!! returns "new_series"

    New series of calculated observations. The operands are unchanged. Unary plus copies the series; unary minus negates it. Built-in `abs` and `round` also return copies.

??? note "Details"

    Two-series results have an empty description. Operations with a
    number or array normally keep the copied description. Binary results can
    trim all-missing edge rows; unary signs, `abs` and `round` do not trim.
    Reflected arithmetic supports the other operand on the left. NumPy
    broadcasting and missing-value rules apply.

### See also

[`apply`](#apply), [Comparisons](#comparison-protocols)
        """
        pass

    @staticmethod
    @_dm.topic(title="Comparisons", anchor="comparison-protocols", priority=20)
    def _document_comparison_protocols():
        r"""
==Compare observations period by period==

### Syntax

    series == other
    series != other
    series < other
    series <= other
    series > other
    series >= other

### Input arguments

!!! input "other"

    Another series or a compatible number or array. Series are aligned over their combined span, and one variant can be compared with several variants.

### Returns

!!! returns "new_series"

    New series of Boolean comparison results, not one overall answer. Neither operand is changed. Comparisons with NaN are false except `!=`, which is true.

### See also

[`same_as`](#same_as), [Iteration, combination, and display](#container-protocols)
        """
        pass

    @staticmethod
    @_dm.topic(title="Iteration, combination, and display", anchor="container-protocols", priority=10)
    def _document_container_protocols():
        r"""
==Iterate, test, combine and display a series==

### Syntax

    iter(series)
    bool(series)
    series & other
    series | other
    repr(series)
    str(series)
    ~series

### Input arguments

!!! input "other"

    Series to append as additional variants using `&` or `|`.

### Returns

!!! returns "iter(series)"

    Finite iterator of single-variant series, not individual observations.

!!! returns "bool(series)"

    Boolean: whether the series contains any data entries. Missing values and false comparison results still count as entries.

!!! returns "series & other, series | other"

    New combined series from `hstack`. These operators are not logical AND and OR.

!!! returns "repr(series), str(series)"

    Text displaying the frequency, span, dimensions, description and observations. Missing values are shown as `⋅`.

!!! returns "~series"

    Short-display operation, currently unavailable.

### Mutation

These operations do not change the receiver. Iterated series can share data with it.

### See also

[`hstack`](#hstack), [`extract_variants`](#extract_variants), [`iter_own_variants`](#iter_own_variants), [`iter_periods_and_values`](#iter_periods_and_values)
        """
        pass


    #]

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
    r"""
==Combine series columns through the first series==

#### Syntax

    new_series = hstack(
        first,
        *args,
    )

#### Input arguments

!!! input "first"

    Series to which the other columns are appended.

!!! input "*args"

    Additional inputs passed to `first.hstack`.

#### Returns

!!! returns "new_series"

    New combined series. Inputs are unchanged.

#### See also

[`Series.hstack`](#hstack)
    """
    return first.hstack(*args)


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


def _from_period_value_pairs(
    self,
    period_value_pairs: Iterable[tuple[Period, Any]],
    frequency: Frequency | None = None,
    **kwargs,
) -> None:
    r"""
    Create a new time series from an iterable of period-value pairs
    """
    #[
    period_value_pairs = tuple(period_value_pairs, )
    if not period_value_pairs:
        return
    periods, values = zip(*period_value_pairs, )
    _from_periods_and_values(
        self,
        periods=periods,
        values=values,
        frequency=frequency,
    )
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


#
# Keys are (start, periods, values, func, period_value_pairs, ) presence tests
#
_SERIES_POPULATOR = {
    (False, False, False, False, False): lambda self, **kwargs: None,
    (True,  False, True,  False, False): _from_start_and_values,
    (False, True,  True,  False, False): _from_periods_and_values,
    (False, True,  False, True,  False): _from_periods_and_func,
    (False, False, False, False, True): _from_period_value_pairs,
}

