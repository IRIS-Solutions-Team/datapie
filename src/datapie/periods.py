"""
Time periods and time spans
"""


#[

from __future__ import annotations

# Standard library imports
from numbers import Real
import re as _re
import functools as _ft
import datetime as _dt
import calendar as _ca

# Typing imports
from typing import Self, Any, Protocol, Literal, runtime_checkable
from collections.abc import Iterable, Callable, Iterator

# Third-party imports
import documark as _dm

# Application imports
from . import wrongdoings as _wrongdoings

# Local imports
from .frequencies import Frequency

# Typing imports for TYPE_CHECKING
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .ez_plotly import PlotlyDateAxisModeType

#]


__all__ = (
    "yy", "hh", "qq", "mm", "dd", "ii",
    "Span", "EmptySpan", "start", "end",
    "Period", "periods_from_sdmx_strings", "periods_from_iso_strings", "periods_from_python_dates", "periods_from_until", "periods_from_to",
    "get_printable_span",
    "period_indexes",
    "get_encompassing_span",
    "PERIOD_CLASS_FROM_FREQUENCY_RESOLUTION",
    "refrequent", "convert_to_new_freq",
    "daily_serial_from_ymd",
)


PositionType = Literal["start", "middle", "end", ]


_COMPACT_MONTH_STRINGS = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


def _get_compact_year_string(year: int, ) -> str:
    return str(year)[-2:]


SDMX_REXP_FORMATS = {
    Frequency.YEARLY: (4, _re.compile(r"\d\d\d\d", ), ),
    Frequency.HALFYEARLY: (7, _re.compile(r"\d\d\d\d-H\d", ), ),
    Frequency.QUARTERLY: (7, _re.compile(r"\d\d\d\d-Q\d", ), ),
    Frequency.MONTHLY: (7, _re.compile(r"\d\d\d\d-\d\d", ), ),
    Frequency.WEEKLY: (8, _re.compile(r"\d\d\d\d-W\d\d", ), ),
    Frequency.DAILY: (10, _re.compile(r"\d\d\d\d-\d\d-\d\d", ), ),
    Frequency.INTEGER: (None, _re.compile(r"\([\-\+]?\d+\),", ), ),
}


BASE_YEAR = 2020


@runtime_checkable
class ResolutionContextProtocol(Protocol, ):
    """
    Context protocol for contextual period resolution
    """
    start_date = ...
    end_date = ...


class ResolutionContext:
    r"""
................................................................................

## `ResolutionContext`

==Holds the start and end periods that contextual periods resolve against.==

    context = ResolutionContext(start_date=None, end_date=None, )

A two-attribute container, nothing more. Anything else carrying `start_date`
and `end_date` attributes serves just as well -- the protocol
`ResolutionContextProtocol` is what the resolving code actually asks for, and
it is `runtime_checkable`.

................................................................................
    """
    #[

    def __init__(
        self,
        start_date: Period | None = None,
        end_date: Period | None = None,
    ) -> None:
        """
        """
        self.start_date = start_date
        self.end_date = end_date

    #]


@runtime_checkable
class ResolvableProtocol(Protocol, ):
    """
    Contextual period protocol
    """
    needs_resolve = ...
    def resolve(self, context: ResolutionContextProtocol) -> Any: ...


def _check_periods(first, second, ) -> None:
    if str(type(first)) == str(type(second)):
        return
    message = "Cannot handle periods of different time frequencies in this context"
    raise _wrongdoings.Error(message, )


def _check_periods_decorator(func: Callable, ) -> Callable:
    def wrapper(*args, **kwargs):
        _check_periods(args[0], args[1], )
        return func(*args, **kwargs, )
    return wrapper


def _remove_blanks(func: Callable,) -> Callable:
    def wrapper(*args, **kwargs, ):
        return func(*args, **kwargs, ).replace(" ", "", )
    return wrapper


class _SpannableMixin:
    """
    """
    #[

    def __rshift__(self, end: Self | None, ) -> Span:
        """
        Period >> Period or Period >> None
        """
        return Span(self, end, 1)

    def __rrshift__(self, start: Self | None, ) -> Span:
        """
        None >> Period
        """
        return Span(start, self, 1)

    def __lshift__(self, start: Self | None, ) -> Span:
        """
        Period << Period or Period << None
        """
        return Span(start, self, -1)

    def __rlshift__(self, end: Self | None, ) -> Span:
        """
        None << Period
        """
        return Span(self, end, -1)

    def __pow__(self, len_dir: int, ) -> Span:
        r"""
        Period ** int
        """
        if len_dir == 1 or len_dir == -1:
            return self
        if len_dir > 0:
            return Span(self, self + len_dir - 1, 1, )
        if len_dir < 0:
            return Span(self, self + len_dir + 1, -1, )
        if len_dir == 0:
            return EmptySpan()
        raise ValueError("Invalid span len_dir")

    #]


def _period_constructor_with_ellipsis(
    func: Callable,
) -> Callable:
    """
    """
    #[
    @_ft.wraps(func, )
    def wrapper(*args, ):
        try:
            index = args.index(Ellipsis, )
            start = func(*args[:index], ) if args[:index] else None
            end = func(*args[index+1:], ) if args[index+1:] else None
            return Span(start, end, )
        except ValueError:
            return func(*args, )
    return wrapper
    #]



@_dm.reference(
    path=("data_management", "periods.md", ),
    categories={
        "constructor": "Creating new time periods",
        "arithmetics_comparison": "Adding, subtracting, and comparing time periods",
        "refrequency": "Converting time periods to different frequencies",
        "conversion": "Converting time periods to different representations",
        "print": "Converting time periods to strings",
    },
)
class Period(
    _SpannableMixin,
):
    r"""
................................................................................

Time periods
=============

A `Period` is one point on a calendar of a fixed frequency: one year, one
half-year, one quarter, one month, one day, or one numbered observation.
Whatever the frequency, the whole state of the object is a single integer
`serial`; the frequency itself lives on the class, not on the instance, so two
periods of different frequencies are two different types.

| Frequency   | Class              | Call         | Serial
|-------------|--------------------|--------------|--------
| Yearly      | `YearlyPeriod`     | `yy(y)`      | `y`
| Half-yearly | `HalfyearlyPeriod` | `hh(y, h)`   | `y*2 + h - 1`
| Quarterly   | `QuarterlyPeriod`  | `qq(y, q)`   | `y*4 + q - 1`
| Monthly     | `MonthlyPeriod`    | `mm(y, m)`   | `y*12 + m - 1`
| Daily       | `DailyPeriod`      | `dd(y, m, d)`| Gregorian ordinal
| Integer     | `IntegerPeriod`    | `ii(n)`      | `n`

Because the serial is a plain integer, arithmetic is integer arithmetic: `per
+ k` moves forward by `k` periods of that frequency, and `per - other` counts
the periods between two of them. Anything mixing two frequencies is refused --
`_check_periods` compares the two types and raises `wrongdoings.Error("Cannot
handle periods of different time frequencies in this context")`. That covers
`==` and `!=` as well, so periods of unlike frequency cannot be compared for
equality at all; they raise rather than return `False`.

Periods are not validated on construction. A segment outside the natural range
rolls over into the next year without complaint: `qq(2020, 9)` gives
`qq(2022,1)` and `mm(2020, 13)` gives `mm(2021,1)`.

`Period` itself is an abstract base and is not meant to be instantiated. Three
of its methods -- `to_ymd`, `to_sdmx_string` and `to_compact_string` -- are
written as `return self.to_x(...)`, which is a call to themselves, so reaching
any of them on a class that does not override it ends in `RecursionError`
rather than a `NotImplementedError`.

................................................................................
    """
    #[

    frequency = None
    plotly_xaxis_type = None
    needs_resolve = False
    _POSITION_FROM_PLOTLY_MODE = {
        "instant": "start",
        "period": "middle",
    }

    @property
    @_dm.reference(
        category="property",
        call_name="frequency",
    )
    def _frequency():
        r"""
................................................................................

## `Period.frequency`

==Time frequency of the time period, as a read-only property.==

    freq = self.frequency

A `Frequency` enum member, carried on the class rather than on the
instance, so every period of the same frequency shares it.
`Period.frequency` itself is `None`.

Note that the entry on the reference page is attached to a separate stub,
`_frequency`, whose getter is declared without a `self` parameter; the
real `frequency` is the plain class attribute that each subclass sets.
Reaching `self._frequency` raises `TypeError: Period._frequency() takes 0
positional arguments but 1 was given`.

................................................................................
        """
        raise NotImplementedError

    @_dm.reference(
        category=None,
        call_name="Time period constructors",
        call_name_is_code=False,
        priority=20,
    )
    def __init__(self, serial: int = 0, ) -> None:
        r"""
................................................................................

## Time period constructors

==Create a time period of a given frequency from a year and a segment.==

    per = yy(year)
    per = hh(year, halfyear)
    per = qq(year, quarter)
    per = mm(year, month)
    per = dd(year, month, day_in_month)
    per = dd(year, None, day_in_year)
    per = ii(number)

Each constructor is a module-level function, also reachable as an
attribute of `Period` (`Period.qq`, `Period.yy`, and so on) because the
module rebinds them onto the class after they are built.


**Input arguments.**


???+ input "year"
    Calendar year as an integer. Not range-checked.

???+ input "halfyear, quarter, month, day_in_month, day_in_year"
    The segment within the year. Not range-checked: a value past
    the end of the year rolls forward, so `qq(2020, 9)` gives
    `qq(2022,1)`.

???+ input "number"
    Observation number for an integer period. Any integer, including zero
    and negatives.


### Returns


A `Period` of the matching subclass. Every one of these constructors
except `dd` also accepts `...` among its arguments, in which case it
returns a `Span` instead -- see the constructor entries themselves.


### Examples


    >>> import datapie as dp
    >>> dp.qq(2020, 1)
    qq(2020,1)
    >>> dp.dd(2020, None, 60)
    dd(2020,2,29)

................................................................................
        """
        self.serial = int(serial)

    def copy(self, ) -> Self:
        r"""
................................................................................

## `Period.copy`

==Create a copy of the time period.==

    new = self.copy()

Builds a fresh object of the same class and copies the serial across.
Periods are immutable in practice -- every operation on one returns a new
object rather than changing it -- so a copy is rarely needed.


### Returns


A new `Period` of the same class, equal to `self`.

................................................................................
        """
        new = type(self)()
        new.serial = self.serial
        return new

    @_dm.reference(
        category=None,
        call_name="Time period arithmetics",
        call_name_is_code=False,
        priority=30,
    )
    def time_period_arithmetics():
        r"""
................................................................................

## Time period arithmetics

==Adding integers to periods, and subtracting one period from another.==

    new_per = per + k
    new_per = k + per
    new_per = per - k
    num = per - other

Adding or subtracting an integer moves the period by that many periods of
its own frequency. The integer is passed through `int()`, so a float is
truncated rather than rejected: `qq(2020,1) + 1.9` gives `qq(2020,2)`.

Subtracting another period counts the periods between the two and returns
a plain integer. Both must be of the same frequency; otherwise
`wrongdoings.Error` is raised.

There is no `__rsub__` on `Period`, so `k - per` raises rather than
producing anything.


### Returns


A new `Period` when an integer is added or subtracted; a plain `int` when
one period is subtracted from another.

................................................................................
        """

    @_dm.reference(
        category=None,
        call_name="Time period comparison",
        call_name_is_code=False,
        priority=20,
    )
    def time_period_comparison():
        r"""
................................................................................

## Time period comparison

==Comparing two periods of the same frequency.==

| Operation | Description
|-----------|-------------
| `==`      | The two periods are the same period
| `!=`      | The two periods are not the same period
| `<`       | Earlier than
| `<=`      | Earlier than or equal to
| `>`       | Later than
| `>=`      | Later than or equal to

Every one of the six compares the serials, and every one first calls
`_check_periods`, so both operands must be of the same frequency. This
includes `==` and `!=`: comparing a quarterly period with a monthly one
raises `wrongdoings.Error` rather than returning `False`. Comparing a
period with anything that is not a period raises the same way.

Hashing does not follow the same rule. `__hash__` mixes the serial with
the frequency, so two periods of different frequencies hash apart and can
sit in the same set or dictionary without ever being compared.

................................................................................
        """
        raise NotImplementedError

    @staticmethod
    @_dm.reference(
        category="constructor",
        call_name="Period.from_iso_string",
    )
    def from_iso_string(
        iso_string: str,
        frequency: Frequency = Frequency.DAILY,
    ) -> Self:
        r"""
................................................................................

## `Period.from_iso_string`

==Create a time period from an ISO-8601 date string.==

    per = Period.from_iso_string(iso_string, frequency=Frequency.DAILY, )

The string is split on `-` into exactly three parts, so it must carry the
full `yyyy-mm-dd` form; a shorter string such as `"2020-05"` raises
`ValueError`. The three parts are then handed to the `from_ymd` of the
class for `frequency`, which for anything below daily keeps only what its
own frequency can hold -- `"2020-05-17"` read as quarterly gives
`qq(2020,2)`, the day silently dropped.


**Input arguments.**


???+ input "iso_string"
    A `yyyy-mm-dd` string.

???+ input "frequency"
    The frequency of the period to build. Daily when left alone. Passing
    `None` explicitly is *not* the same as leaving it alone: it raises
    `KeyError: None`, since `None` is not a key of the frequency-to-class
    table.


### Returns


A `Period` of the class matching `frequency`.


### Examples


    >>> import datapie as dp
    >>> dp.Period.from_iso_string("2020-05-17")
    dd(2020,5,17)

................................................................................
        """
        year, month, day = iso_string.split("-", )
        period_constructor = PERIOD_CLASS_FROM_FREQUENCY_RESOLUTION[frequency].from_ymd
        return period_constructor(int(year), int(month), int(day), )

    @staticmethod
    @_dm.reference(
        category="constructor",
        call_name="Period.from_python_date",
    )
    def from_python_date(
        python_date: _dt.date,
        frequency: Frequency = Frequency.DAILY,
    ) -> Self:
        r"""
................................................................................

## `Period.from_python_date`

==Create a time period from a Python date.==

    per = Period.from_python_date(
        python_date, frequency=Frequency.DAILY,
    )

Reads `.year`, `.month` and `.day` off the object and passes them to the
`from_ymd` of the class for `frequency`, so a `datetime.datetime` works as
well as a `datetime.date` -- the time of day is simply not looked at.


**Input arguments.**


???+ input "python_date"
    A `datetime.date` or `datetime.datetime`.

???+ input "frequency"
    The frequency of the period to build. Daily when left alone. As with
    `from_iso_string`, passing `None` explicitly raises `KeyError: None`
    rather than falling back to daily.


### Returns


A `Period` of the class matching `frequency`.

................................................................................
        """
        year, month, day = python_date.year, python_date.month, python_date.day
        period_constructor = PERIOD_CLASS_FROM_FREQUENCY_RESOLUTION[frequency].from_ymd
        return period_constructor(int(year), int(month), int(day), )

    @staticmethod
    @_dm.reference(
        category="constructor",
        call_name="Period.from_sdmx_string",
    )
    def from_sdmx_string(
        sdmx_string: str,
        frequency: Frequency | None = None,
    ) -> Self:
        r"""
................................................................................

## `Period.from_sdmx_string`

==Creates a time period from its SDMX string form, working out the frequency from the shape of the string unless you name it.==

    period = Period.from_sdmx_string(
        sdmx_string,
        frequency=None,
    )

This is the counterpart of `to_sdmx_string`, and it recognises the four
shapes that method writes:

| String         | Frequency  | Period
|----------------|------------|--------
| `2020`         | Yearly     | `yy(2020)`
| `2020-H1`      | Half-yearly| `hh(2020,1)`
| `2020-Q1`      | Quarterly  | `qq(2020,1)`
| `2020-01`      | Monthly    | `mm(2020,1)`
| `2020-01-15`   | Daily      | `dd(2020,1,15)`

Integer periods are the exception. `ii(1).to_sdmx_string()` writes `(1)`,
but the pattern this function matches against expects a trailing comma, so
`(1)` is not recognised and raises as though it were nonsense. The string
does not round-trip; see the `frequencies.py` log.


**Input arguments.**


???+ input "sdmx_string"
    The text to read. Surrounding whitespace is stripped. A string
    matching none of the shapes above raises `Error: Cannot determine
    time frequency from "..."; probably not a valid SDMX string.`

???+ input "frequency"
    Names the frequency instead of having it inferred, which saves the
    pattern match when you already know it. **It is not checked against
    the string.** A frequency that disagrees is trusted and the parse
    then fails inside the target class, so
    `Period.from_sdmx_string("2020-Q1", Frequency.MONTHLY)` raises
    `ValueError: invalid literal for int() with base 10: 'Q1'` rather
    than saying the frequency was wrong.


### Returns


A new period of the resolved frequency.


### Examples


The frequency follows from the shape of the string:

    >>> import datapie as dp
    >>> dp.Period.from_sdmx_string("2020-Q1")
    qq(2020,1)
    >>> dp.Period.from_sdmx_string("2020")
    yy(2020)
    >>> dp.Period.from_sdmx_string("2020-01-15")
    dd(2020,1,15)

A round trip through the string form:

    >>> dp.Period.from_sdmx_string(dp.mm(2020, 7).to_sdmx_string())
    mm(2020,7)

................................................................................
        """
        frequency = Frequency.from_sdmx_string(sdmx_string, ) if frequency is None else frequency
        return PERIOD_CLASS_FROM_FREQUENCY_RESOLUTION[frequency].from_sdmx_string(sdmx_string, )

    @staticmethod
    @_dm.reference(
        category="constructor",
        call_name="Period.from_ymd",
    )
    def from_ymd(freq: Frequency, *args, ) -> Self:
        r"""
................................................................................

## `Period.from_ymd`

==Create a time period from a calendar year, month and day.==

    per = Period.from_ymd(freq, year, month=1, day=1, )

The arguments after `freq` are forwarded untouched to the `from_ymd` of
the class for that frequency, and each class keeps only what it can hold.
A regular period converts the month to its own segment through
`month_to_segment` and ignores the day entirely, so
`Period.from_ymd(Frequency.QUARTERLY, 2020, 5, 17)` gives `qq(2020,2)`.

Only the six frequencies in the frequency-to-class table are accepted.
`Frequency.WEEKLY` has no class of its own and raises `KeyError:
<Frequency.WEEKLY: 52>`.


**Input arguments.**


???+ input "freq"
    The frequency of the period to build.

???+ input "year, month, day"
    Calendar year, month and day. Month and day are optional and
    default to 1; both are dropped for frequencies that cannot
    hold them.


### Returns


A `Period` of the class matching `freq`.

................................................................................
        """
        return PERIOD_CLASS_FROM_FREQUENCY_RESOLUTION[freq].from_ymd(*args, )

    @staticmethod
    @_dm.reference(
        category="constructor",
        call_name="Period.from_year_segment",
    )
    def from_year_segment(freq: Frequency, *args, ) -> Self:
        r"""
................................................................................

## `Period.from_year_segment`

==Create a time period from a calendar year and a segment within it.==

    per = Period.from_year_segment(freq, year, segment, )

The segment means whatever the frequency makes of it: a half-year, a
quarter, a month, or -- for daily periods -- the day within the year. For
integer periods the year is ignored altogether and the segment becomes the
serial.

Nothing is range-checked. A segment past the end of the year rolls into
the following year, so `Period.from_year_segment(Frequency.QUARTERLY,
2020, 9)` gives `qq(2022,1)`. Regular frequencies also accept the string
`"end"` in place of a number, which resolves to the last segment of the
year.


**Input arguments.**


???+ input "freq"
    The frequency of the period to build.

???+ input "year"
    Calendar year as an integer.

???+ input "segment"
    Segment within the year, or the string `"end"`.


### Returns


A `Period` of the class matching `freq`.

................................................................................
        """
        return PERIOD_CLASS_FROM_FREQUENCY_RESOLUTION[freq].from_year_segment(*args, )

    period_from_ymd = from_ymd
    dater_from_ymd = from_ymd

    @staticmethod
    @_dm.reference(
        category="constructor",
        call_name="Period.today",
    )
    def today(freq: Frequency, ) -> Self:
        r"""
................................................................................

## `Period.today`

==Creates the period containing today's date, at the frequency you ask for.==

    period = Period.today(freq)

Reads the system date once and converts it, so the result depends on
the clock of the machine it runs on.


**Input arguments.**


???+ input "freq"
    The frequency of the period to create, either a `Frequency` member
    or the integer behind it -- `Period.today(4)` and
    `Period.today(Frequency.QUARTERLY)` give the same period.

    Only the calendar frequencies work. `Frequency.INTEGER` has no
    calendar, and asking for it raises `KeyError` naming the current
    year, because the integer period class has no `from_ymd`. `None`
    raises `KeyError: None`.


### Returns


A new period of the requested frequency, the one that contains today.


### Examples


Today at daily frequency is today:

    >>> import datetime
    >>> import datapie as dp
    >>> today = dp.Period.today(dp.Frequency.DAILY)
    >>> today.to_python_date() == datetime.date.today()
    True

The integer value of the frequency does just as well:

    >>> dp.Period.today(4) == dp.Period.today(dp.Frequency.QUARTERLY)
    True

................................................................................
        """
        t = _dt.date.today()
        return PERIOD_CLASS_FROM_FREQUENCY_RESOLUTION[freq].from_ymd(t.year, t.month, t.day, )

    @property
    def start(self, ) -> Self:
        r"""
................................................................................

## `Period.start`

==The period itself, as a read-only property.==

    per = self.start

A `Period` is one period, so its start is itself. The property exists so
that a period and a `Span` can be handed to the same code: both answer
`start` and `end`. `start_date` is a legacy alias for the same property.

................................................................................
        """
        return self

    start_date = start

    @property
    def end(self, ) -> Self:
        r"""
................................................................................

## `Period.end`

==The period itself, as a read-only property.==

    per = self.end

The counterpart of `start`, and likewise the period itself. `end_date` is
a legacy alias.

................................................................................
        """
        return self

    end_date = end

    @property
    @_dm.reference(category="property", )
    def year(self, ) -> int:
        r"""
................................................................................

## `Period.year`

==Calendar year of the time period, as a read-only property.==

    y = self.year

Each frequency supplies its own implementation. The one on `Period` has a
body of `...`, so any class that does not override it -- `IntegerPeriod`
among them -- returns `None` instead of raising.

................................................................................
        """
        ...

    @property
    @_dm.reference(category="property", )
    def segment(self, ) -> int:
        r"""
................................................................................

## `Period.segment`

==Segment of the period within its calendar year.==

    s = self.segment

The half-year, quarter, month, or day-in-year, counted from 1. `period` is
an alias for the same value.

As with `year`, the base implementation is `...` and returns `None` on any
class that does not override it, `IntegerPeriod` included. On
`DailyPeriod` the override is reached but raises, because
`to_year_segment` builds a `date` where it needs an ordinal.

................................................................................
        """
        ...

    @_dm.reference(category="refrequency", )
    def refrequent(self, new_freq: Frequency, *args ,**kwargs, ) -> Self:
        r"""
................................................................................

## `Period.refrequent`

Called as `x.refrequent(...)` (method form) or
`datapie.refrequent(x, ...)` (function form).

==Convert the period to a different time frequency.==

    new_per = self.refrequent(new_freq, position="start", )

Goes through the calendar: the period is resolved to a year, month and day
with `to_ymd`, and those are handed to the `from_ymd` of the target class.
Converting downwards is exact; converting upwards is not, and `position`
decides which period of the finer frequency is landed on.

`convert_to_new_frequency`, `convert_to_new_freq` and `convert` are
aliases of this method, and the module-level `refrequent` does the same
thing with the period as its first argument.


**Input arguments.**


???+ input "new_freq"
    The frequency to convert to.

???+ input "position"
    Passed on to `to_ymd`; `"start"`, `"middle"` or `"end"`. Only matters
    when converting to a finer frequency.


### Returns


A new `Period` of the class matching `new_freq`.


### Examples


    >>> import datapie as dp
    >>> dp.qq(2020, 3).refrequent(dp.Frequency.YEARLY)
    yy(2020)
    >>> dp.yy(2020).refrequent(dp.Frequency.QUARTERLY, position="end")
    qq(2020,4)

................................................................................
        """
        year, month, day = self.to_ymd(*args, **kwargs, )
        new_class = PERIOD_CLASS_FROM_FREQUENCY_RESOLUTION[new_freq]
        return new_class.from_ymd(year, month, day, )

    convert_to_new_frequency = refrequent
    convert_to_new_freq = refrequent
    convert = refrequent

    @_dm.reference(category="conversion", )
    def to_ymd(self, **kwargs, ) -> tuple[int, int, int]:
        r"""
................................................................................

## `Period.to_ymd`

==Calendar year, month and day of the time period.==

    year, month, day = self.to_ymd(position="start", )

A period below daily frequency covers a stretch of days, so one date has
to be picked out of it; `position` decides which. The mapping is a lookup
table on each class, not a calculation:

| Frequency   | `"start"`     | `"middle"`    | `"end"`
|-------------|---------------|---------------|------------
| Yearly      | Jan 1         | Jun 30        | Dec 31
| Half-yearly | Jan 1 / Jul 1 | Mar 15/Sep 15 | Jun 30/Dec 31
| Quarterly   | 1st of Q      | 15th of mid   | last of Q
| Monthly     | 1st           | 15th          | last of month
| Daily       | the day       | the day       | the day

February's last day is looked up per year, so `mm(2020,2).to_ymd("end")`
gives 29. Note that yearly `"middle"` is June 30, not the 15th of the
middle month as the other frequencies would suggest.

`IntegerPeriod` has no `to_ymd` of its own, and the one on `Period` calls
itself, so `ii(4).to_ymd()` ends in `RecursionError`.


**Input arguments.**


???+ input "position"
    `"start"`, `"middle"` or `"end"`. An unrecognised value raises
    `KeyError`.


### Returns


A `(year, month, day)` tuple of integers.

................................................................................
        """
        return self.to_ymd(**kwargs, )

    @_dm.reference(category="print", )
    def to_iso_string(self, **kwargs, ) -> str:
        r"""
................................................................................

## `Period.to_iso_string`

==ISO-8601 representation of the time period.==

    iso_string = self.to_iso_string(position="start", )

Resolves the period to a date with `to_ymd` and formats it `yyyy-mm-dd`,
so every frequency comes out in the same shape and `position` decides
which day of the period is shown.


**Input arguments.**


???+ input "position"
    Passed straight to `to_ymd`.


### Returns


A `yyyy-mm-dd` string.


### Examples


    >>> import datapie as dp
    >>> dp.qq(2020, 1).to_iso_string()
    '2020-01-01'
    >>> dp.qq(2020, 1).to_iso_string(position="end")
    '2020-03-31'

................................................................................
        """
        year, month, day = self.to_ymd(**kwargs, )
        return f"{year:04g}-{month:02g}-{day:02g}"

    @_dm.reference(category="print", )
    def to_sdmx_string(self, ) -> str:
        r"""
................................................................................

## `Period.to_sdmx_string`

==SDMX representation of the time period.==

    sdmx_string = self.to_sdmx_string()

Frequency-specific, and the form `Period.from_sdmx_string` reads back:

| Frequency   | Format       | Example
|-------------|--------------|--------------
| Yearly      | `yyyy`       | `2030`
| Half-yearly | `yyyy-Hh`    | `2030-H1`
| Quarterly   | `yyyy-Qq`    | `2030-Q1`
| Monthly     | `yyyy-mm`    | `2030-01`
| Daily       | `yyyy-mm-dd` | `2030-01-01`
| Integer     | `(n)`        | `(1)`

This is also what `str()` and `repr()` of a period go through for the
regular frequencies. There is no weekly row: no weekly period class
exists.

The implementation on `Period` calls itself, so a class that does not
override it ends in `RecursionError`.


### Returns


The SDMX string for this period.

................................................................................
        """
        return self.to_sdmx_string()

    @_dm.reference(category="print", )
    def to_compact_string(self, ) -> str:
        r"""
................................................................................

## `Period.to_compact_string`

==Short representation of the time period, with a two-digit year.==

    compact_string = self.to_compact_string()

| Frequency   | Format    | Example
|-------------|-----------|----------
| Yearly      | `yyY`     | `30Y`
| Half-yearly | `yyHh`    | `30H1`
| Quarterly   | `yyQq`    | `30Q1`
| Monthly     | `yyMmm`   | `30M01`
| Daily       | `yymmmdd` | `30Jan01`
| Integer     | `(n)`     | `(1)`

The year is the last two digits of the calendar year, so two centuries are
indistinguishable. For integer periods this is the same string as
`to_sdmx_string`, the two names being bound to one function.

As with `to_sdmx_string`, the implementation on `Period` calls itself.


### Returns


The compact string for this period.

................................................................................
        """
        return self.to_compact_string()

    @_dm.reference(category="conversion", )
    def to_python_date(
        self,
        position: PositionType = "start",
    ) -> _dt.date:
        r"""
................................................................................

## `Period.to_python_date`

==Converts the period to a `datetime.date`, choosing where inside the period to land.==

    date = self.to_python_date(
        position="start",
    )

A period covers a stretch of calendar, and a `datetime.date` is a
single day, so the conversion has to pick one. `position` makes that
choice.


**Input arguments.**


???+ input "position"
    Which day of the period to return, one of `"start"`, `"middle"` or
    `"end"`. Each period class carries its own table:

    | Frequency    | `"start"` | `"middle"` | `"end"`
    |--------------|-----------|------------|---------
    | Yearly       | 1 Jan     | 30 Jun     | 31 Dec
    | Half-yearly  | 1st day   | 15 Mar, 15 Sep | last day
    | Quarterly    | 1st day   | 15th of the middle month | last day
    | Monthly      | 1st day   | 15th       | last day
    | Daily        | the day itself | the day itself | the day itself

    Note that the yearly `"middle"` is 30 June, not the 15th of a
    middle month -- a year has no single middle month. February's
    `"end"` is resolved against the actual year, so leap years give the
    29th.


### Returns


A `datetime.date`.

Integer periods have no calendar at all. `ii(5).to_python_date()` does
not raise a helpful error: it recurses until Python gives up with
`RecursionError: maximum recursion depth exceeded`.


### Examples


The three positions of one quarter:

    >>> import datapie as dp
    >>> dp.qq(2020, 3).to_python_date()
    datetime.date(2020, 7, 1)
    >>> dp.qq(2020, 3).to_python_date("middle")
    datetime.date(2020, 8, 15)
    >>> dp.qq(2020, 3).to_python_date("end")
    datetime.date(2020, 9, 30)

A year is the exception to the "15th of the middle month" rule:

    >>> dp.yy(2020).to_python_date("middle")
    datetime.date(2020, 6, 30)

................................................................................
        """
        return _dt.date(*self.to_ymd(position=position, ))

    def to_plotly_date(
        self,
        mode: PlotlyDateAxisModeType = "period",
    ) -> _dt.date:
        position = self._POSITION_FROM_PLOTLY_MODE[mode]
        return self.to_python_date(position=position, )

    def to_plotly_edge_before(
        self,
        mode: PlotlyDateAxisModeType = "period",
    ) -> _dt.date:
        r"""
        """
        return {
            "period": self.to_python_date(position="start", ),
            "instant": (self - 1).to_python_date(position="middle", ),
        }[mode]

    def to_plotly_edge_after(
        self,
        mode: PlotlyDateAxisModeType = "period",
    ) -> _dt.date:
        r"""
        """
        return {
            "period": self.to_python_date(position="end", ),
            "instant": self.to_python_date(position="middle", ),
        }[mode]

    @_dm.reference(category="information", )
    def get_distance_from_origin(self, ) -> int:
        r"""
................................................................................

## `Period.get_distance_from_origin`

==Counts how many periods separate this one from the package's origin period.==

    distance = self.get_distance_from_origin()

The origin is the start of 2020 for every calendar frequency, and 0 for
integer periods. So `yy(2020)`, `hh(2020,1)`, `qq(2020,1)`, `mm(2020,1)`
and `dd(2020,1,1)` all sit at distance 0, each counted in its own units.


**Input arguments.**


None.


### Returns


An integer, counted in periods of this period's own frequency. It is
negative for periods before the origin -- `qq(2019,1)` is `-4` and
`mm(2019,1)` is `-12`.


### Examples


The origin itself, and one year either side of it:

    >>> import datapie as dp
    >>> dp.qq(2020, 1).get_distance_from_origin()
    0
    >>> dp.qq(2019, 1).get_distance_from_origin()
    -4
    >>> dp.mm(2021, 1).get_distance_from_origin()
    12

Integer periods count from zero instead:

    >>> dp.ii(5).get_distance_from_origin()
    5

................................................................................
        """
        return self.serial - self.origin

    @_dm.no_reference
    def resolve(self, context: ResolutionContextProtocol) -> Self:
        return self

    def __bool__(self) -> bool:
        return not self.needs_resolve

    def __len__(self):
        return 1

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return self.to_sdmx_string()

    _databox_repr = __str__

    def __format__(self, *args) -> str:
        str_format = args[0] if args else ""
        return ("{period_str:"+str_format+"}").format(period_str=self.__str__())

    def __iter__(self) -> Iterator[Self]:
        yield self

    def __hash__(self, ) -> int:
        return hash((int(self.serial), hash(self.frequency), ))

    def __add__(self, other: int, ) -> Self:
        r"""
................................................................................

==Add integer to time period==

Add an integer value to a time period, moving it forward by the number of
periods (if positive) or backward (if negative).

    new_period = period + k
    new_period = k + period


### Input arguments ###


???+ input "period"
    Time period to which the integer is added.

???+ input "k"
    Integer value to add to the time period. Positive values move the
    period forward, while negative values move it backward. The addition is
    frequency specific.


### Returns ###


???+ returns "new_period"
    New time period resulting from the addition of the integer value.


### See also ###

* [Time period arithmetics](#time-period-arithmetics)

................................................................................
        """
        return type(self)(self.serial + int(other))

    __radd__ = __add__

    def __sub__(self, other: Self | int) -> Self | int:
        r"""
................................................................................

==Subtract time period or integer from time period==

Subtraction operations can be performed between two time periods or between a
time period and an integer. These operations are crucial for calculating the
distance between periods or adjusting a period's position in time.

* **Subtracting a time period**: Calculate the number of periods between
two time periods. Both periods must be of the same frequency.

* **Subtracting an integer**: Move a time period backward or forward by the
specified number of periods. The integer specifies how many periods of the
respective frequency to move backward or forward.


    result = self - other
    new_period = self - k


### Input arguments ###


???+ input "other"
    The time period to subtract from `self`. The `result` is the number of
    periods between `self` and `other`. The subtraction is frequency specific.

???+ input "k"
    Integer value to subtract from `self`. Positive values move the period
    backward, while negative values move it forward. The subtraction is
    frequency specific.


### Returns ###


???+ returns "result"
    The number of periods between two time periods if `other` is a `Period`.

???+ returns "new_period"
    A new `Period` object representing the time period shifted backward by the
    specified number of periods if `other` is an integer.

................................................................................
    """
        if _is_period(other, ):
            return self._sub_period(other)
        else:
            return self.__add__(-int(other))

    @_check_periods_decorator
    def _sub_period(self, other: Self) -> int:
        return self.serial - other.serial

    def __index__(self):
        return self.serial

    def __eq__(self, other: Self, ) -> bool:
        r"""
................................................................................

==True if time period is equal to another time period==

See documentation for [time period comparison](#time-period-comparison).

................................................................................
        """
        _check_periods(self, other, )
        return self.serial == other.serial

    def __ne__(self, other: Self, ) -> bool:
        r"""
................................................................................

==True if time period is not equal to another time period==

See documentation for [time period comparison](#time-period-comparison).

................................................................................
        """
        _check_periods(self, other, )
        return self.serial != other.serial

    def __lt__(self, other: Self, ) -> bool:
        r"""
................................................................................

==True if time period is earlier than another time period==

See documentation for [time period comparison](#time-period-comparison).

................................................................................
        """
        _check_periods(self, other, )
        return self.serial < other.serial

    def __le__(self, other: Self, ) -> bool:
        r"""
................................................................................

==True if time period is earlier than or equal to another time period==

See documentation for [time period comparison](#time-period-comparison).

................................................................................
        """
        _check_periods(self, other, )
        return self.serial <= other.serial

    def __gt__(self, other: Self, ) -> bool:
        r"""
................................................................................

==True if time period is later than another time period==

See documentation for [time period comparison](#time-period-comparison).

................................................................................
        """
        _check_periods(self, other, )
        return self.serial > other.serial

    def __ge__(self, other: Self, ) -> bool:
        r"""
................................................................................

==True if time period is later than or equal to another time period==

See documentation for [time period comparison](#time-period-comparison).

................................................................................
        """
        _check_periods(self, other, )
        return self.serial >= other.serial

    @_dm.reference(
        category="arithmetics_comparison",
    )
    def shift(
        self,
        by: int | str = -1,
    ) -> Self:
        r"""
................................................................................

## `Period.shift`

==Move the period, either by a number of periods or to a named landmark.==

    new_per = self.shift(by=-1, )

Despite what the older docstring says, this does **not** modify the period
in place and does not return `None`: periods are never mutated, and
`shift` hands back a new one. `self` is left exactly as it was.

`by` is either an integer or one of four string codes:

| `by`            | Result
|-----------------|--------------------------------------------
| an integer      | `self + by`; the default `-1` is one back
| `"yoy"`         | The same segment one year earlier
| `"boy"`, `"soy"`| The first period of this calendar year
| `"eopy"`        | The last period of the previous year
| `"tty"`         | The period before, or `None` in segment 1

The `"tty"` case is the one to watch: it returns `None` rather than a
period whenever `self` is the first segment of its year, so the result
cannot be used without checking. An unrecognised string is not rejected as
such -- it falls through to `self + by`, where `int()` raises
`ValueError`.

The named codes lean on `create_soy`, `create_eopy` and `create_tty`,
which `IntegerPeriod` does not define, so `ii(4).shift("soy")` raises
`AttributeError`.


**Input arguments.**


???+ input "by"
    An integer number of periods, or one of the string codes above.


### Returns


A new `Period`, or `None` from `"tty"` in the first segment of a year.

................................................................................
        """
        match by:
            case "yoy":
                return self - self.frequency.value
            case "boy" | "soy":
                return self.create_soy()
            case "eopy":
                return self.create_eopy()
            case "tty":
                return self.create_tty()
            case _:
                return self + by

    #]


class IntegerPeriod(Period, ):
    r"""
................................................................................

## `IntegerPeriod`

==Periods that are numbered observations rather than calendar dates.==

    per = ii(number)

The serial *is* the number, with no calendar behind it, so `ii(0)` is the
origin and negatives are ordinary. Prints as `(n)` in both the SDMX and the
compact form.

Because there is no calendar, the class supplies none of the calendar
machinery: `to_ymd`, `to_year_segment`, `get_year`, `create_soy`,
`create_eopy`, `create_tty` and `to_daily` are all absent. Reaching for one of
them fails in one of two ways -- `to_ymd`, and everything built on it such as
`to_iso_string`, `to_python_date` and `refrequent`, ends in `RecursionError`
through the self-calling stub on `Period`, while the rest raise
`AttributeError`. The `year` and `segment` properties return `None`.

................................................................................
    """
    #[

    frequency = Frequency.INTEGER
    plotly_xaxis_type = "linear"
    needs_resolve = False
    half_period = 0.5
    origin = 0

    @classmethod
    def from_sdmx_string(klass, sdmx_string: str, ) -> IntegerPeriod:
        sdmx_string = sdmx_string.strip().removeprefix("(").removesuffix(")")
        return klass(int(sdmx_string))

    def to_sdmx_string(self, ) -> str:
        return f"({self.serial})"

    to_compact_string = to_sdmx_string

    def __repr__(self) -> str:
        return f"ii({self.serial})"

    def to_plotly_date(self, *args, **kwargs, ) -> Real:
        return self.serial

    def to_plotly_edge_before(self, *args, **kwargs, ) -> Real:
        return self.serial - self.half_period

    def to_plotly_edge_after(self, *args, **kwargs, ) -> Real:
        return self.serial + self.half_period

    @classmethod
    def from_year_segment(
        klass,
        year: Any,
        segment: int = 0,
    ) -> Self:
        r"""
        """
        serial = int(segment)
        return klass(serial)

    from_year_period = from_year_segment

    #]


class DailyPeriod(Period, ):
    r"""
................................................................................

## `DailyPeriod`

==Periods of one calendar day, serialised as the Gregorian ordinal.==

    per = dd(year, month, day)
    per = dd(year, None, day_in_year)

The serial is `datetime.date.toordinal()`, so arithmetic on a daily period is
arithmetic on days and leap years look after themselves. The origin is January
1st of 2020.

Beyond the shared interface it adds `create_som` (start of month) and
`create_eopm` (end of the previous month).

`to_year_segment` does not work: it builds a `date` for the start of the year
where it needs that date's ordinal, so subtracting it raises `TypeError`.
Everything routed through it goes the same way -- the `segment` and `period`
properties, and `create_tty`.

................................................................................
    """
    #[

    frequency: Frequency = Frequency.DAILY
    plotly_xaxis_type = "date"
    needs_resolve = False
    origin = _dt.date(BASE_YEAR, 1, 1).toordinal()

    @classmethod
    def from_ymd(klass: type, year: int, month: int=1, day: int=1) -> Self:
        serial = daily_serial_from_ymd(year, month, day, )
        return klass(serial)

    @classmethod
    def from_year_segment(
        klass,
        year: int,
        segment: int = 1,
    ) -> Self:
        r"""
        """
        boy_serial = _dt.date(year, 1, 1).toordinal()
        serial = boy_serial + int(segment) - 1
        return klass(serial)

    from_year_period = from_year_segment

    @classmethod
    def from_sdmx_string(klass, sdmx_string: str, ) -> Self:
        year, month, day, *_ = sdmx_string.split("-")
        return klass.from_ymd(int(year), int(month), int(day))

    @classmethod
    def from_iso_string(klass, iso_string: str, ) -> Self:
        """
        """
        year, month, day, *_ = iso_string.split("-", )
        return klass.from_ymd(int(year), int(month), int(day), )

    @property
    def year(self, ) -> int:
        return _dt.date.fromordinal(self.serial).year

    @property
    def month(self, ) -> int:
        return _dt.date.fromordinal(self.serial).month

    @property
    def day(self, ) -> int:
        return _dt.date.fromordinal(self.serial).day

    @property
    def segment(self, ) -> int:
        return self.to_year_segment()[1]

    @property
    def period(self, ) -> int:
        return self.segment

    def to_sdmx_string(self, **kwargs) -> str:
        year, month, day = self.to_ymd()
        return f"{year:04g}-{month:02g}-{day:02g}"

    def to_compact_string(self, **kwargs) -> str:
        year, month, day = self.to_ymd()
        year_string = _get_compact_year_string(year)
        month_string = _COMPACT_MONTH_STRINGS[month-1]
        return f"{year_string}{month_string}{day:02g}"

    def to_year_segment(self) -> tuple[int, int]:
        boy_serial = _dt.date(_dt.date.fromordinal(self.serial).year, 1, 1)
        per = self.serial - boy_serial + 1
        year = _dt.date.fromordinal(self.serial).year
        return year, per

    def to_ymd(self, **kwargs) -> tuple[int, int, int]:
        py_date = _dt.date.fromordinal(self.serial)
        return py_date.year, py_date.month, py_date.day

    def get_year(self, ) -> int:
        return _dt.date.fromordinal(self.serial).year

    @_remove_blanks
    def __repr__(self) -> str:
        return f"dd{self.to_ymd()}"

    def create_soy(self, ) -> Self:
        year = self.get_year()
        serial = _dt.date(year, 1, 1).toordinal()
        return type(self)(serial)

    def create_som(self, ) -> Self:
        year, month, _ = self.to_ymd()
        serial = _dt.date(year, month, 1).toordinal()
        return type(self)(serial)

    def create_eoy(self, ) -> Self:
        year = self.get_year()
        serial = _dt.date(year, 12, 31).toordinal()
        return type(self)(serial)

    def create_eopy(self, ) -> Self:
        year = self.get_year()
        serial = _dt.date(year-1, 12, 31).toordinal()
        return type(self)(serial)

    def create_eopm(self, ) -> Self:
        return self.create_som() - 1

    def create_tty(self, ) -> Self | None:
        _, seg = self.to_year_segment()
        return self - 1 if seg > 1 else None

    def to_daily(self, **kwargs, ) -> Self:
        return self

    #]


def _serial_from_ysf(year: int, per: int, freq: int) -> int:
    return int(year)*int(freq) + int(per) - 1


class RegularPeriodMixin:
    r"""
................................................................................

## `RegularPeriodMixin`

==Shared behaviour of the four evenly-dividing frequencies.==

Mixed into `YearlyPeriod`, `HalfyearlyPeriod`, `QuarterlyPeriod` and
`MonthlyPeriod`, all of which serialise as `year*frequency + segment - 1`.
That single formula is what makes their arithmetic exact: adding 1 always
moves to the next segment, and a year boundary needs no special case.

It supplies `from_year_segment`, `from_ymd`, `from_iso_string`, the `year`,
`segment` and `period` properties, `to_year_segment`, `to_ymd`, `to_daily` and
the `create_soy` / `create_eoy` / `create_eopy` / `create_tty` family. Each
concrete class contributes only its `frequency`, its `_MONTH_DAY_RESOLUTION`
table, its string forms, and a `month_to_segment` that maps a calendar month
onto its own segment.

................................................................................
    """
    #[

    plotly_xaxis_type = "date"

    @classmethod
    def from_year_segment(
            klass: type,
            year: int,
            per: int | str = 1,
        ) -> Self:
        per = per if per != "end" else klass.frequency.value
        new_serial = _serial_from_ysf(year, per, klass.frequency.value)
        return klass(new_serial, )

    from_year_period = from_year_segment

    @classmethod
    def from_ymd(klass, year: int, month: int=1, day: int=1, ) -> Self:
        return klass.from_year_segment(year, klass.month_to_segment(month, ), )

    @classmethod
    def from_iso_string(klass, iso_string: str, ) -> Self:
        """
        """
        year, month, day, *_ = iso_string.split("-", )
        return klass.from_ymd(int(year), int(month), int(day), )

    @property
    def year(self, ) -> int:
        return self.to_year_segment()[0]

    @property
    def segment(self, ) -> int:
        return self.to_year_segment()[1]

    @property
    def period(self, ) -> int:
        return self.segment

    def to_year_segment(self) -> tuple[int, int]:
        return self.serial//self.frequency.value, self.serial%self.frequency.value+1

    def get_year(self) -> int:
        return self.to_year_segment()[0]

    def to_ymd(
        self,
        position: PositionType = "start",
    ) -> tuple[int, int, int]:
        year, per = self.to_year_segment()
        month, day = self._MONTH_DAY_RESOLUTION[position][per]
        if day is None:
            _, day = _ca.monthrange(year, month)
        return year, month, day

    def __str__(self, ) -> str:
        return self.to_sdmx_string()

    def create_soy(self, ) -> Self:
        year, *_ = self.to_year_segment()
        return self.from_year_segment(year, 1)

    create_boy = create_soy

    def create_eoy(self, ) -> Self:
        year, *_ = self.to_year_segment()
        return self.from_year_segment(year, "end")

    def create_eopy(self, ) -> Self:
        year, *_ = self.to_year_segment()
        return self.from_year_segment(year-1, self.frequency.value)

    def create_tty(self, ) -> Self | None:
        _, seg = self.to_year_segment()
        return self - 1 if seg > 1 else None

    def to_daily(
        self,
        position: PositionType = "start"
    ) -> DailyPeriod:
        try:
            return DailyPeriod.from_ymd(*self.to_ymd(position=position, ), )
        except:
            raise _wrongdoings.Error("Cannot convert period to daily period.")

    #]


class YearlyPeriod(RegularPeriodMixin, Period, ):
    """
    """
    #[

    frequency: Frequency = Frequency.YEARLY
    needs_resolve: bool = False
    origin = _serial_from_ysf(BASE_YEAR, 1, Frequency.YEARLY)
    _MONTH_DAY_RESOLUTION = {
        "start": {1: (1, 1)},
        "middle": {1: (6, 30)},
        "end": {1: (12, 31)},
    }

    @classmethod
    def from_sdmx_string(klass, sdmx_string: str, ) -> YearlyPeriod:
        return klass(int(sdmx_string.strip()))

    def to_sdmx_string(self, ) -> str:
        return f"{self.get_year():04g}"

    def to_compact_string(self, ) -> str:
        year_string = _get_compact_year_string(self.get_year())
        return f"{year_string}Y"

    @_remove_blanks
    def __repr__(self) -> str: return f"yy({self.get_year()})"

    @staticmethod
    def month_to_segment(month: int, ) -> int:
        return 1

    #]


class HalfyearlyPeriod(RegularPeriodMixin, Period, ):
    #[
    frequency: Frequency = Frequency.HALFYEARLY
    needs_resolve: bool = False
    origin = _serial_from_ysf(BASE_YEAR, 1, Frequency.HALFYEARLY)
    _MONTH_DAY_RESOLUTION = {
        "start": {1: (1, 1), 2: (7, 1)},
        "middle": {1: (3, 15), 2: (9, 15)},
        "end": {1: (6, 30), 2: (12, 31)}
    }

    @classmethod
    def from_sdmx_string(klass, sdmx_string: str, ) -> HalfyearlyPeriod:
        year, halfyear = sdmx_string.strip().split("-H")
        return klass.from_year_segment(int(year), int(halfyear))

    def to_sdmx_string(self, ) -> str:
        year, per = self.to_year_segment()
        return f"{year:04g}-{self.frequency.letter}{per:1g}"

    def to_compact_string(self, ) -> str:
        year, per = self.to_year_segment()
        year_string = _get_compact_year_string(year)
        return f"{year_string}{self.frequency.letter}{per:1g}"

    @_remove_blanks
    def __repr__(self) -> str: return f"hh{self.to_year_segment()}"

    def get_month(
        self,
        position: PositionType = "start",
    ) -> int:
        _, per = self.to_year_segment()
        return month_resolution[position][per]

    @staticmethod
    def month_to_segment(month: int, ) -> int:
        return 1+((month-1)//6)
    #]


class QuarterlyPeriod(RegularPeriodMixin, Period, ):
    """
    """
    #[

    frequency: Frequency = Frequency.QUARTERLY
    needs_resolve: bool = False
    origin = _serial_from_ysf(BASE_YEAR, 1, Frequency.QUARTERLY)
    _MONTH_DAY_RESOLUTION = {
        "start": {1: (1, 1), 2: (4, 1), 3: (7, 1), 4: (10, 1)},
        "middle": {1: (2, 15), 2: (5, 15), 3: (8, 15), 4: (11, 15)},
        "end": {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)},
    }

    @classmethod
    def from_sdmx_string(klass, sdmx_string: str, ) -> QuarterlyPeriod:
        year, quarter = sdmx_string.strip().split("-Q")
        return klass.from_year_segment(int(year), int(quarter))

    def to_sdmx_string(self, ) -> str:
        year, per = self.to_year_segment()
        return f"{year:04g}-{self.frequency.letter}{per:1g}"

    def to_compact_string(self, ) -> str:
        year, per = self.to_year_segment()
        year_string = _get_compact_year_string(year)
        return f"{year_string}{self.frequency.letter}{per:1g}"

    @_remove_blanks
    def __repr__(self) -> str: return f"qq{self.to_year_segment()}"

    @staticmethod
    def month_to_segment(month: int, ) -> int:
        return 1+((month-1)//3)

    #]


class MonthlyPeriod(RegularPeriodMixin, Period, ):
    #[
    frequency: Frequency = Frequency.MONTHLY
    needs_resolve: bool = False
    origin = _serial_from_ysf(BASE_YEAR, 1, Frequency.MONTHLY)
    _MONTH_DAY_RESOLUTION = {
        "start": { m: (m, 1) for m in range(1, 13) },
        "middle": { m: (m, 15) for m in range(1, 13) },
        "end": { m: ((m, _ca.monthrange(1970, m)[1]) if m != 2 else (m, None)) for m in range(1, 13) },
    }

    @classmethod
    def from_sdmx_string(klass, sdmx_string: str, ) -> MonthlyPeriod:
        year, month = sdmx_string.strip().split("-")
        return klass.from_year_segment(int(year), int(month))

    def to_sdmx_string(self, ) -> str:
        year, per = self.to_year_segment()
        return f"{year:04g}-{per:02g}"

    def to_compact_string(self, ) -> str:
        year, per = self.to_year_segment()
        year_string = _get_compact_year_string(year)
        return f"{year_string}{self.frequency.letter}{per:02g}"

    @_remove_blanks
    def __repr__(self) -> str: return f"mm{self.to_year_segment()}"

    @staticmethod
    def month_to_segment(month: int, ) -> int:
        return month
    #]


class UnknownPeriod:
    r"""
................................................................................

## `UnknownPeriod`

==Placeholder for the unknown frequency; builds nothing.==

Registered in the frequency-to-class table under `Frequency.UNKNOWN`, and
holds a single method, `from_sdmx_string`, which returns `None` whatever it is
given. So a period read with the unknown frequency comes back as `None` rather
than raising, and nothing else about the class is usable -- it is not a
`Period` subclass and has no serial, no arithmetic and no string forms.

................................................................................
    """
    #[

    def from_sdmx_string(sdmx_string: str, ) -> None:
        return None

    #]


yy = _period_constructor_with_ellipsis(YearlyPeriod.from_year_segment, )
yy.__doc__ = r"""
................................................................................

## `irispie.yy`

==Create a yearly period, or a yearly span when given an ellipsis.==

    per = yy(year)
    span = yy(from_year, ..., until_year)

`yy`, `hh`, `qq`, `mm` and `ii` are all built the same way: the underlying
`from_year_segment` of the matching class, wrapped so that an `...` among the
arguments turns the call into a `Span`. The wrapper splits the argument list
at the ellipsis, builds a period from each side, and returns `Span(start,
end)`; a side with no arguments becomes `None`, which the span resolves from
its context later.

So `qq(2020,1,...,2021,4)` is the span of quarters from 2020Q1 to 2021Q4,
`qq(2020,1,...)` runs from 2020Q1 to the context's end, and `qq(...,2021,4)`
from the context's start to 2021Q4.

Nothing is range-checked; see the shared notes under the `Period`
constructors.


**Input arguments.**


???+ input "year"
    Calendar year as an integer.


### Returns


A `YearlyPeriod`, or a `Span` of them if `...` was passed.

................................................................................
"""
yy.__name__ = "irispie.yy"
yy = _dm.reference(category="constructor", )(yy)


hh = _period_constructor_with_ellipsis(HalfyearlyPeriod.from_year_segment, )
hh.__doc__ = r"""
................................................................................

## `irispie.hh`

==Create a half-yearly period, or a half-yearly span with an ellipsis.==

    per = hh(year, halfyear)
    span = hh(from_year, from_half, ..., until_year, until_half)

`halfyear` is 1 or 2. See `yy` for how the ellipsis form works.


### Returns


A `HalfyearlyPeriod`, or a `Span` of them if `...` was passed.

................................................................................
"""
hh.__name__ = "irispie.hh"
hh = _dm.reference(category="constructor", )(hh)


qq = _period_constructor_with_ellipsis(QuarterlyPeriod.from_year_segment)
qq.__doc__ = r"""
................................................................................

## `irispie.qq`

==Create a quarterly period, or a quarterly span with an ellipsis.==

    per = qq(year, quarter)
    span = qq(from_year, from_qtr, ..., until_year, until_qtr)

`quarter` is 1 to 4. See `yy` for how the ellipsis form works.


### Returns


A `QuarterlyPeriod`, or a `Span` of them if `...` was passed.

................................................................................
"""
qq.__name__ = "irispie.qq"
qq = _dm.reference(category="constructor", )(qq)


mm = _period_constructor_with_ellipsis(MonthlyPeriod.from_year_segment)
mm.__doc__ = r"""
................................................................................

## `irispie.mm`

==Create a monthly period, or a monthly span with an ellipsis.==

    per = mm(year, month)
    span = mm(from_year, from_month, ..., until_year, until_month)

`month` is 1 to 12. See `yy` for how the ellipsis form works.


### Returns


A `MonthlyPeriod`, or a `Span` of them if `...` was passed.

................................................................................
"""
mm.__name__ = "irispie.mm"
mm = _dm.reference(category="constructor", )(mm)


ii = _period_constructor_with_ellipsis(IntegerPeriod)
ii.__doc__ = r"""
................................................................................

## `irispie.ii`

==Create an integer period, or a span of them with an ellipsis.==

    per = ii(number)
    span = ii(from_number, ..., until_number)

Unlike the other four, `ii` wraps the `IntegerPeriod` class itself rather than
a `from_year_segment`, so its single argument is the serial. See `yy` for how
the ellipsis form works.


### Returns


An `IntegerPeriod`, or a `Span` of them if `...` was passed.

................................................................................
"""
ii.__name__ = "irispie.ii"
ii = _dm.reference(category="constructor", )(ii)


@_dm.reference(
    category="constructor",
    call_name="irispie.dd",
)
def dd(year: int, month: int | None, day: int) -> DailyPeriod:
    r"""
................................................................................

## `irispie.dd`

==Create a daily-frequency time period.==

    per = dd(year, month, day_in_month)
    per = dd(year, None, day_in_year)

Passing `None` for the month switches the third argument from a day within the
month to a day within the year, counted from 1, so `dd(2020, None, 60)` is the
60th day of 2020 -- February 29th, that year being a leap year.

Unlike `yy`, `hh`, `qq`, `mm` and `ii`, `dd` is a plain function and does
**not** accept `...` to build a `Span`.


**Input arguments.**


???+ input "year"
    Calendar year as an integer.

???+ input "month"
    Calendar month, or `None` to read the third argument as a day within
    the year.

???+ input "day"
    Day within the month, or within the year when `month` is `None`.


### Returns


A `DailyPeriod`.

................................................................................
    """
    if month is None:
        return DailyPeriod.from_year_segment(year, day)
    else:
        return DailyPeriod.from_ymd(year, month, day)


for n in ("yy", "hh", "qq", "mm", "dd", "ii", ):
    setattr(Period, n, locals()[n], )


def daily_serial_from_ymd(year: int, month: int, day: int, ) -> int:
    r"""
................................................................................

## `daily_serial_from_ymd`

==Serial number of a calendar date, as used by daily periods.==

    serial = daily_serial_from_ymd(year, month, day, )

The Gregorian ordinal of the date -- `datetime.date(...).toordinal()` -- and
so the serial a `DailyPeriod` for that date carries. Raises `ValueError` for a
date that does not exist.


**Input arguments.**


???+ input "year, month, day"
    Calendar year, month and day of a date that exists.


### Returns


The ordinal as an integer.

................................................................................
    """
    return _dt.date(year, month, day).toordinal()


@_dm.reference(
    path=("data_management", "spans.md", ),
    categories={
        "constructor": "Creating new time spans",
        "arithmetics": "Arithmetic operations on time spans",
        "manipulation": "Manipulating time spans",
        "print": "Converting time spans to strings",
        "property": None,
    },
)
class Span:
    r"""
................................................................................

Time spans
===========

A `Span` holds three things: a start period, an end period, and an integer
step. Everything else is worked out from them -- the direction is the sign of
the step, the frequency comes from the class of the start period, and
iterating walks the serials from one end to the other.

    span = Span(start_per, end_per, step=1)
    span = start_per >> end_per

Either endpoint may be left open, in which case it is filled with one of the
two contextual sentinels, `start` and `end`, and the span carries
`needs_resolve=True` until `resolve` is given a context to fill them from. An
unresolved span has no length and cannot be iterated: `__len__` and `__iter__`
both return `None`, so `len(span)` and `list(span)` raise `TypeError` rather
than reporting the span is not ready.

A span also works as a context manager, though `__enter__` returns it
unchanged and `__exit__` does nothing.

................................................................................
    """
    #[

    __slots__ = (
        "_start",
        "_end",
        "_step",
        "needs_resolve",
    )

    @_dm.reference(
        category="constructor",
        call_name="Span",
        priority=20,
    )
    def __init__(
        self,
        from_per: Period | str | None = None,
        until_per: Period | str | None = None,
        step: int = 1,
    ) -> None:
        r"""
................................................................................

## `Span`

==Create a new time span.==

    span = Span(from_per, until_per, step=1, )

The two endpoints may be `Period` objects, SDMX strings, or `None`.
Strings are converted through `Period.from_sdmx_string`, so
`Span("2020-Q1", "2020-Q4")` is the same as writing the two periods out.
`None` is replaced by a contextual sentinel: `start` for the opening
endpoint and `end` for the closing one, swapped over when the step is
negative.

The frequency check only fires when both endpoints are already periods,
and it is applied to the *arguments* rather than to the converted
endpoints. Two strings therefore always pass it, whatever they say, so
`Span("2020-Q1", "2020-05")` builds a span with a quarterly start and a
monthly end.

### Shorthand operators

    span = start_per >> end_per
    span = end_per << start_per

`>>` builds the forward span and is equivalent to `Span(start_per,
end_per, 1)`. `<<` is meant to be the backward counterpart, and its step
sign is exactly what the line above promises -- what goes wrong is the
operand order. `__rshift__` returns `Span(self, end, 1)`, putting the left
operand first; `__lshift__` returns `Span(start, self, -1)`, putting the
right operand first. The two are reversed with respect to each other, and
it is that swap, not the negative step, that empties the range.

So `qq(2020,4) << qq(2020,1)` has length 0 and iterates to nothing, while
the documented equivalent `Span(qq(2020,4), qq(2020,1), -1)` walks all
four quarters. Write the constructor out for a backward span.


**Input arguments.**


???+ input "from_per"
    Opening endpoint: a `Period`, an SDMX string, or `None`.

???+ input "until_per"
    Closing endpoint, in the same three forms.

???+ input "step"
    Signed stride in periods, 1 when left alone. The sign sets the
    direction; the magnitude thins the span out.


### Returns


A new `Span`.


### Examples


    >>> import datapie as dp
    >>> list(dp.Span(dp.qq(2020,1), dp.qq(2020,4), 2))
    [qq(2020,1), qq(2020,3)]

................................................................................
        """
        if step > 0:
            default_from_per = start
            default_until_per = end
        else:
            default_from_per = end
            default_until_per = start
        self._start = (
            resolve_period_or_string(from_per, )
            if from_per is not None
            else default_from_per
        )
        self._end = (
            resolve_period_or_string(until_per, )
            if until_per is not None
            else default_until_per
        )
        self._step = int(step)
        self.needs_resolve = self._start.needs_resolve or self._end.needs_resolve
        if not self.needs_resolve:
            _check_periods(from_per, until_per)

    @_dm.reference(category="constructor", )
    def copy(self, ) -> Self:
        r"""
................................................................................

## `Span.copy`

==Creates an independent copy of the time span.==

    new_span = self.copy()

The copy carries the same start, end and step. What it buys you is
freedom to use the in-place `shift`, `shift_start` and `shift_end`
without disturbing the span you started from.


**Input arguments.**


None.


### Returns


A new `Span` covering the same periods in the same direction.


### Examples


Shifting the copy leaves the original where it was:

    >>> import datapie as dp
    >>> span = dp.qq(2020, 1) >> dp.qq(2020, 4)
    >>> other = span.copy()
    >>> other.shift(4)
    >>> str(span.start), str(other.start)
    ('2020-Q1', '2021-Q1')

................................................................................
        """
        return type(self)(
            from_per=self._start,
            until_per=self._end,
            step=self._step,
        )

    @classmethod
    def encompassing(klass, *args, ) -> Self:
        r"""
................................................................................

## `Span.encompassing`

==Build the smallest span covering everything it is given.==

    span = Span.encompassing(*args)

Each argument is either an object carrying `start_date` and `end_date`
attributes, or an iterable of periods; the earliest start and the latest
end found across all of them become the endpoints. Arguments that are
`None`, and periods that are `None` inside an iterable, are ignored.

This is the first element of what the module-level `get_encompassing_span`
returns, which also hands back the two endpoints separately.


**Input arguments.**


???+ input "*args"
    Objects carrying `start_date` and `end_date` attributes, or iterables
    of periods. `None` arguments are skipped.


### Returns


A `Span` running from the earliest start to the latest end, with step 1.
Given nothing usable, both endpoints come back as the contextual
sentinels, so the span is unresolved rather than empty.

................................................................................
        """
        return get_encompassing_span(*args, )[0]

    @property
    @_dm.reference(category="property", )
    def start(self):
        """==Start period of the time span=="""
        return self._start

    start_date = start

    @property
    @_dm.reference(category="property", )
    def end(self):
        """==End period of the time span=="""
        return self._end

    end_date = end

    @property
    @_dm.reference(category="property", )
    def step(self):
        """==Step size of the time span=="""
        return self._step

    @property
    def _class(self):
        return type(self._start) if not self.needs_resolve else None

    @property
    @_dm.reference(category="property", )
    def direction(self, ) -> Literal["forward", "backward", ]:
        """==Direction of the time span=="""
        return "forward" if self._step > 0 else "backward"

    @property
    def _serials(self) -> range | None:
        return range(self._start.serial, self._end.serial+_sign(self._step), self._step) if not self.needs_resolve else None

    # @property
    # def needs_resolve(self) -> bool:
        # return bool(self._start and self._end)

    @property
    @_dm.reference(category="property", )
    def frequency(self) -> Frequency:
        """==Frequency of the time span=="""
        return self._class.frequency

    @_dm.reference(category="manipulation", )
    def reverse(self, ) -> Self:
        r"""
................................................................................

## `Span.reverse`

==Creates a new span running the other way, from this one's end back to its start.==

    new_span = self.reverse()

Swaps the two endpoints and negates the step, so a forward span comes
back as a backward one over the same stretch of calendar. The span it
is called on is left alone; the in-place counterpart of this method
does not exist.


**Input arguments.**


None.


### Returns


A new `Span`. Reversing twice gives back the original.


### Examples


    >>> import datapie as dp
    >>> span = dp.qq(2020, 1) >> dp.qq(2020, 3)
    >>> [str(p) for p in span.reverse()]
    ['2020-Q3', '2020-Q2', '2020-Q1']
    >>> [str(p) for p in span]
    ['2020-Q1', '2020-Q2', '2020-Q3']

The step flips sign with it:

    >>> span.reverse().step
    -1

................................................................................
        """
        return type(self)(self._end, self._start, -self._step, )

    @_dm.reference(category="manipulation", )
    def refrequent(self, new_freq: Frequency | int, ) -> Self:
        r"""
................................................................................

## `Span.refrequent`

==Convert the span to a different time frequency.==

    new_span = self.refrequent(new_freq, )

Converts the two endpoints and keeps the step. Which end of each period is
landed on depends on the direction, so that the new span covers the same
stretch of calendar rather than shrinking inside it: for a forward span
the start is taken at the start of its period and the end at the end of
its period, and the other way round for a backward one.

Only steps of 1 and -1 are handled. Any other step raises
`wrongdoings.Error("Refrequenting time spans with steps other than 1 or -1
is not supported.")`. A span already at `new_freq` is copied unchanged.


**Input arguments.**


???+ input "new_freq"
    The frequency to convert to.


### Returns


A new `Span` at the new frequency.


### Examples


    >>> import datapie as dp
    >>> (dp.qq(2020,1) >> dp.qq(2020,4)).refrequent(dp.Frequency.MONTHLY)
    Span(mm(2020,1), mm(2020,12))

................................................................................
        """
        if self.frequency == new_freq:
            return type(self)(self._start, self._end, self._step, )
        if self._step == 1:
            new_start = self._start.refrequent(new_freq, position="start", )
            new_end = self._end.refrequent(new_freq, position="end", )
        elif self._step == -1:
            new_start = self._start.refrequent(new_freq, position="end", )
            new_end = self._end.refrequent(new_freq, position="start", )
        else:
            raise _wrongdoings.Error("Refrequenting time spans with steps other than 1 or -1 is not supported.")
        return type(self)(new_start, new_end, self._step, )

    @_dm.reference(category="manipulation", )
    def shift_end(
        self,
        by: int,
    ) -> None:
        r"""
................................................................................

## `Span.shift_end`

==Moves the end of the span, changing its length, in place.==

    self.shift_end(by)

Only the end moves; the start stays where it is, so the span gets
longer or shorter. Use `shift` to move both ends together and keep the
length.


**Input arguments.**


???+ input "by"
    The number of periods to move the end by. For a forward span a
    positive `by` extends it and a negative one shortens it. Shortening
    past the start does not raise; it produces a span that yields no
    periods.


### Returns


Nothing. The span is modified in place.


### Examples


Two quarters added to the end of a four-quarter span:

    >>> import datapie as dp
    >>> span = dp.qq(2020, 1) >> dp.qq(2020, 4)
    >>> span.shift_end(2)
    >>> str(span.start), str(span.end)
    ('2020-Q1', '2021-Q2')
    >>> len(list(span))
    6

................................................................................
        """
        self._end += by

    @_dm.reference(category="manipulation", )
    def shift_start(
        self,
        by: int,
    ) -> None:
        r"""
................................................................................

## `Span.shift_start`

==Moves the start of the span, changing its length, in place.==

    self.shift_start(by)

The mirror image of `shift_end`: only the start moves, so a forward
span grows when `by` is negative and shrinks when it is positive.


**Input arguments.**


???+ input "by"
    The number of periods to move the start by. For a forward span a
    negative `by` reaches further back and lengthens the span, while a
    positive one moves the start forward and shortens it.


### Returns


Nothing. The span is modified in place.


### Examples


One quarter added to the front of a four-quarter span:

    >>> import datapie as dp
    >>> span = dp.qq(2020, 1) >> dp.qq(2020, 4)
    >>> span.shift_start(-1)
    >>> str(span.start), str(span.end)
    ('2019-Q4', '2020-Q4')
    >>> len(list(span))
    5

................................................................................
        """
        self._start += by

    def to_plotly_dates(self, *args, **kwargs, ) -> tuple[str]:
        return tuple(t.to_plotly_date(*args, **kwargs, ) for t in self)

    @_dm.reference(category="print", )
    def to_iso_strings(self, *args, **kwargs, ) -> tuple[str]:
        r"""
................................................................................

## `Span.to_iso_strings`

==Writes every period of the span as an ISO-8601 date string.==

    iso_strings = self.to_iso_strings(*args, **kwargs, )

Each period is handed to its own `to_iso_string`, so the day returned
for a period longer than a day depends on `position`, exactly as it
does for a single period.


**Input arguments.**


???+ input "*args, **kwargs"
    Forwarded unchanged to `to_iso_string` on each period. The one worth
    knowing is `position`, which picks the day inside each period and is
    `"start"` unless you change it.


### Returns


A tuple of strings, one per period, in the order the span runs -- so a
reversed span comes back in reverse.


### Examples


    >>> import datapie as dp
    >>> span = dp.qq(2020, 1) >> dp.qq(2020, 2)
    >>> span.to_iso_strings()
    ('2020-01-01', '2020-04-01')
    >>> span.to_iso_strings(position="end")
    ('2020-03-31', '2020-06-30')

................................................................................
        """
        return tuple(t.to_iso_string(*args, **kwargs, ) for t in self)

    @_dm.reference(category="print", )
    def to_sdmx_strings(self, *args, **kwargs, ) -> tuple[str]:
        r"""
................................................................................

## `Span.to_sdmx_strings`

==Writes every period of the span as an SDMX string.==

    sdmx_strings = self.to_sdmx_strings(*args, **kwargs, )

Each period is handed to its own `to_sdmx_string`, giving the same
frequency-specific forms `Period.from_sdmx_string` reads back:
`2020-Q1` for quarterly, `2020-01` for monthly, `2020` for yearly.


**Input arguments.**


???+ input "*args, **kwargs"
    Forwarded unchanged to `to_sdmx_string` on each period; normally
    called with none. Unlike `to_iso_strings` there is no `position` to
    give -- passing one raises `TypeError:
    QuarterlyPeriod.to_sdmx_string() got an unexpected keyword argument
    'position'`.


### Returns


A tuple of strings, one per period, in the order the span runs.


### Examples


    >>> import datapie as dp
    >>> span = dp.qq(2020, 1) >> dp.qq(2020, 3)
    >>> span.to_sdmx_strings()
    ('2020-Q1', '2020-Q2', '2020-Q3')

................................................................................
        """
        return tuple(t.to_sdmx_string(*args, **kwargs, ) for t in self)

    @_dm.reference(category="print", )
    def to_compact_strings(self, *args, **kwargs, ) -> tuple[str]:
        r"""
................................................................................

## `Span.to_compact_strings`

==Compact string for every period in the span.==

    compact_strings = self.to_compact_strings()

Calls `to_compact_string` on each period in turn and collects the results.
Any arguments are passed straight through to each period.


**Input arguments.**


???+ input "*args, **kwargs"
    Forwarded unchanged to `to_compact_string` on each period; normally
    called with none.


### Returns


A tuple of compact strings, in iteration order.

................................................................................
        """
        return tuple(t.to_compact_string(*args, **kwargs, ) for t in self)

    def to_python_dates(self, *args, **kwargs, ) -> tuple[_dt.date]:
        return tuple(t.to_python_date(*args, **kwargs, ) for t in self)

    def __len__(self) -> int|None:
        return len(self._serials) if not self.needs_resolve else None

    def __str__(self) -> str:
        return repr(self)

    def __repr__(self) -> str:
        start_rep = self._start.__repr__()
        end_rep = self._end.__repr__()
        step_rep = f", {self._step}" if self._step!=1 else ""
        return f"Span({start_rep}, {end_rep}{step_rep})"

    @_dm.reference(
        category="arithmetics",
        call_name="+",
    )
    def __add__(self, offset: int) -> Self:
        r"""
................................................................................

## `+`

==Shifts the whole span by a number of periods, leaving its length unchanged.==

    new_span = self + offset
    new_span = offset + self

Both ends move together, so the span keeps its length, its step and its
direction, and simply sits somewhere else on the timeline. Either
operand order works. This returns a new span; `shift` is the in-place
counterpart.


**Input arguments.**


???+ input "offset"
    The number of periods to move by, positive forward and negative
    back. A non-integer is not rejected: the offset is added to each
    endpoint's serial and truncated, so `span + 1.5` moves the span one
    period forward and `span + -1.5` moves it one period back.


### Returns


A new `Span` with the same step and the same number of periods.


### Examples


The same shift written both ways:

    >>> import datapie as dp
    >>> span = dp.qq(2020, 1) >> dp.qq(2020, 2)
    >>> str((span + 4).start), str((4 + span).start)
    ('2021-Q1', '2021-Q1')

The original is untouched:

    >>> str(span.start)
    '2020-Q1'

................................................................................
        """
        return type(self)(self._start+offset, self._end+offset, self._step)

    __radd__ = __add__

    def __rshift__(
        self,
        step: int,
    ) -> Self:
        r"""
................................................................................

## `>>`

==Set a positive step on the span.==

    new_span = self >> step

Returns a copy of the span carrying the given step; the endpoints are left
alone. A **negative** step raises `ValueError("Step must be positive when
using the >> operator.")`.

The guard tests `step < 0`, so a step of `0` is not caught despite the
message: it yields a span that raises `ValueError: range() arg 3 must not
be zero` the first time its length or its contents are asked for.

Note that this is a different operation from `>>` between two periods,
which builds a span rather than restepping one.


**Input arguments.**


???+ input "step"
    The step to set. Must not be negative.


### Returns


A new `Span` with the same endpoints and the new step.

................................................................................
        """
        if step < 0:
            raise ValueError("Step must be positive when using the >> operator.")
        return type(self)(self._start, self._end, step, )

    def __lshift__(
        self,
        step: int,
    ) -> Self:
        r"""
................................................................................

## `<<`

==Set a negative step on the span.==

    new_span = self << step

The mirror of `>>`: returns a copy with the given step, and raises
`ValueError("Step must be negative when using the << operator.")` for a
**positive** step. The guard tests `step > 0`, so zero slips through here
too, with the same delayed failure.

Setting a negative step this way does not swap the endpoints, so on a
forward span the result iterates to nothing.


**Input arguments.**


???+ input "step"
    The step to set. Must not be positive.


### Returns


A new `Span` with the same endpoints and the new step.

................................................................................
        """
        if step > 0:
            raise ValueError("Step must be negative when using the << operator.")
        return type(self)(self._start, self._end, step, )

    @_dm.reference(
        category="arithmetics",
        call_name="-",
    )
    def __sub__(self, offset: Period | int, ) -> range | Self:
        r"""
................................................................................

## `-`

==Shift the span back, or measure it against a period.==

    new_span = self - offset
    distances = self - per

With an integer, both endpoints move back by that many periods and a new
span comes back. With a `Period`, the result is instead a `range` of the
distances from that period to each end of the span.

The `range` is built as `range(start - per, end - per, step)` and so stops
one short: for a four-period span, `span - span.start` gives `range(0,
3)`, three values rather than four. Iterating the span itself adds the
extra step that this is missing, so the two do not line up.

On an unresolved span the `Period` form returns `None`.


**Input arguments.**


???+ input "offset"
    An integer number of periods, or a `Period` to measure against.


### Returns


A new `Span` for an integer; a `range` (or `None`) for a period.

................................................................................
        """
        if _is_period(offset, ):
            return range(self._start-offset, self._end-offset, self._step) if not self.needs_resolve else None
        else:
            return type(self)(self._start-offset, self._end-offset, self._step)

    def __rsub__(self, ather: Period, ) -> range|None:
        if _is_period(other, ):
            return range(other-self._start, other-self._end, -self._step) if not self.needs_resolve else None
        else:
            return None

    def __iter__(self, ) -> Iterable:
        return (self._class(x) for x in self._serials) if not self.needs_resolve else None

    def __getitem__(self, i: int, ) -> Period | tuple[Period] | None:
        if isinstance(i, int):
            return self._class(self._serials[i]) if not self.needs_resolve else None
        elif isinstance(i, slice):
            indexes = range(*i.indices(len(self)))
            return tuple(t for i, t in enumerate(self) if i in indexes)

    def resolve(self, context: ResolutionContextProtocol, ) -> Self:
        resolved_start = self._start if self._start else self._start.resolve(context, )
        resolved_end = self._end if self._end else self._end.resolve(context, )
        return type(self)(resolved_start, resolved_end, self._step, )

    @_dm.reference(category="manipulation", )
    def shift(self, by: int) -> None:
        r"""
................................................................................

## `Span.shift`

==Moves the whole span by a number of periods, in place, keeping its length.==

    self.shift(by)

Both ends move together, so the span keeps its length, its step and its
direction. The copy-returning counterpart is `+`, which leaves the
original alone.


**Input arguments.**


???+ input "by"
    The number of periods to move by, positive forward and negative
    back.


### Returns


Nothing. The span is modified in place.


### Examples


    >>> import datapie as dp
    >>> span = dp.qq(2020, 1) >> dp.qq(2020, 2)
    >>> span.shift(4)
    >>> str(span.start), str(span.end)
    ('2021-Q1', '2021-Q2')
    >>> len(list(span))
    2

................................................................................
        """
        self._start += by
        self._end += by

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def __eq__(self, other: Self) -> bool:
        return self._start==other._start and self._end==other._end and self._step==other._step

    def __bool__(self) -> bool:
        return not self.needs_resolve

    #]


class EmptySpan:
    r"""
................................................................................

## `EmptySpan`

==A span holding no periods at all.==

    span = EmptySpan()

A singleton -- `__new__` caches the first instance on the class, so every call
gives back the same object. It has no endpoints (`start_date` and `end_date`
are `None`), a length of zero, iterates to nothing, and takes `shift` without
doing anything.

It is what `per ** 0` returns. It is not a `Span` and shares no other part of
that interface, so anything expecting a real span -- `start`, `step`,
`frequency`, the arithmetic operators -- fails on it.

................................................................................
    """
    #[
    start_date = None
    end_date = None
    step = None
    needs_resolve = False

    def __new__(
        klass,
        *args,
        **kwargs,
    ) -> Self:
        """
        """
        if not hasattr(klass, "_instance"):
            klass._instance = super().__new__(klass, *args, **kwargs, )
        return klass._instance

    def __iter__(self, ) -> Iterable:
        return iter(())

    def __len__(self, ) -> int:
        return 0

    def shift(self, *args, **kwargs, ) -> None:
        pass

    #]




def _sign(x: Real, ) -> int:
    return 1 if x>0 else (0 if x==0 else -1)


def period_indexes(periods: Iterable[Period | None], base: Period) -> Iterable[int]:
    r"""
................................................................................

## `period_indexes`

==Offsets of a sequence of periods from a base period.==

    indexes = period_indexes(periods, base, )

Yields `per - base` for each period, which for same-frequency periods is the
integer number of periods between them. A `None` in the input passes through
as `None`, so the output lines up with the input position by position.

This is a generator, not a tuple: it is consumed once.


**Input arguments.**


???+ input "periods"
    An iterable of periods, which may hold `None`s.

???+ input "base"
    The period the offsets are counted from. Must share its frequency
    with every period in `periods`.


### Returns


A generator of integers and `None`s.

................................................................................
    """
    return (
        (t - base) if t is not None else None
        for t in periods
    )


class ContextualPeriod(
    Period,
    _SpannableMixin,
):
    r"""
................................................................................

## `ContextualPeriod`

==A period that stands for "wherever the data starts (or ends)".==

Two instances are created at module level and are the ones normally used:
`start` and `end`, which resolve to the `start_date` and `end_date` of
whatever context they are given. Adding or subtracting an integer carries an
offset along, so `start + 2` is "two periods after the beginning".

A contextual period is falsey (`bool()` is `False`) and carries
`needs_resolve=True`; that is how `Span` and the code around it tell a real
period from a placeholder. Calling `resolve(context)` reads the named
attribute off the context and applies the offset.

It subclasses `Period` but supports almost none of it: there is no serial, so
comparisons, `to_ymd`, the string forms and the rest are unusable.


### Examples


    >>> import datapie as dp
    >>> from datapie.periods import ResolutionContext, start
    >>> ctx = ResolutionContext(dp.qq(2020,1), dp.qq(2020,4))
    >>> (start + 2).resolve(ctx)
    qq(2020,3)

................................................................................
    """
    #[
    needs_resolve = True

    def __init__(self, resolve_from: str, offset: int=0) -> None:
        self._resolve_from = resolve_from
        self._offset = offset

    def __add__(self, offset: int) -> None:
        return type(self)(self._resolve_from, self._offset+offset, )

    def __sub__(self, offset: int) -> None:
        return type(self)(self._resolve_from, self._offset-offset, )

    def __str__(self) -> str:
        return "<>." + self._resolve_from.replace("_date", "") + (f"{self._offset:+g}" if self._offset else "")

    def __repr__(self) -> str:
        return self.__str__()

    def __bool__(self) -> bool:
        return False

    def resolve(self, context: ResolutionContextProtocol) -> Period:
        return getattr(context, self._resolve_from) + self._offset
    #]


# ..............................................................................
#
# ## `start`, `end`
#
# ==The two contextual sentinels standing for the ends of the data.==
#
#     from datapie.periods import start, end
#
# `start` resolves to a context's `start_date` and `end` to its `end_date`. They
# are the values a `Span` uses for an endpoint left as `None`, which is why an
# open-ended span prints as `Span(<>.start, <>.end)`. Both accept an integer
# offset -- `start + 2`, `end - 1` -- which is carried along until resolution.
# See `ContextualPeriod`.
#
# ..............................................................................
start = ContextualPeriod("start_date", )
end = ContextualPeriod("end_date", )


def resolve_period_or_integer(input_period: Any, ) -> Period:
    r"""
................................................................................

## `resolve_period_or_integer`

==Turn a bare number into an integer period, and leave periods alone.==

    per = resolve_period_or_integer(input_period)

Anything that is a real number becomes `IntegerPeriod(int(...))`; anything
else, periods included, is returned untouched. Note that the test is on being
a number, not on failing to be a period, so a non-numeric non-period also
passes straight through.


**Input arguments.**


???+ input "input_period"
    Any object. Real numbers are converted; everything else is passed
    back unchanged.


### Returns


A `Period`, or whatever was passed in if it was neither.

................................................................................
    """
    return (
        IntegerPeriod(int(input_period))
        if isinstance(input_period, Real) else input_period
    )


def resolve_period_or_string(input_period: Period | str, ) -> Period:
    r"""
................................................................................

## `resolve_period_or_string`

==Turn an SDMX string into a period, and leave periods alone.==

    per = resolve_period_or_string(input_period)

Strings go through `Period.from_sdmx_string`, which infers the frequency from
the shape of the string. Anything else is returned untouched. This is what
lets `Span` accept string endpoints.


**Input arguments.**


???+ input "input_period"
    Any object. Strings are converted; everything else is passed back
    unchanged.


### Returns


A `Period`, or whatever was passed in if it was not a string.

................................................................................
    """
    return (
        Period.from_sdmx_string(input_period, )
        if isinstance(input_period, str, )
        else input_period
    )


# ..............................................................................
#
# ## `PERIOD_CLASS_FROM_FREQUENCY_RESOLUTION`
#
# ==Maps a `Frequency` onto the class that implements it.==
#
# The table every frequency-taking constructor goes through --
# `Period.from_ymd`, `from_sdmx_string`, `from_iso_string`, `refrequent` and the
# rest all look the class up here rather than branching.
#
# | Frequency  | Class
# |------------|-------------------
# | `INTEGER`  | `IntegerPeriod`
# | `YEARLY`   | `YearlyPeriod`
# | `HALFYEARLY` | `HalfyearlyPeriod`
# | `QUARTERLY`| `QuarterlyPeriod`
# | `MONTHLY`  | `MonthlyPeriod`
# | `DAILY`    | `DailyPeriod`
# | `UNKNOWN`  | `UnknownPeriod`
#
# `Frequency.WEEKLY` is absent, so every route through this table raises
# `KeyError` for weekly data even though the frequency itself exists and has an
# SDMX format defined for it.
#
# ..............................................................................
PERIOD_CLASS_FROM_FREQUENCY_RESOLUTION = {
    Frequency.INTEGER: IntegerPeriod,
    Frequency.YEARLY: YearlyPeriod,
    Frequency.HALFYEARLY: HalfyearlyPeriod,
    Frequency.QUARTERLY: QuarterlyPeriod,
    Frequency.MONTHLY: MonthlyPeriod,
    Frequency.DAILY: DailyPeriod,
    Frequency.UNKNOWN: UnknownPeriod,
}


def periods_from_sdmx_strings(
    sdmx_strings: Iterable[str],
    frequency: Frequency | None = None,
) -> tuple[Period]:
    r"""
................................................................................

## `periods_from_sdmx_strings`

==Read a sequence of SDMX strings into a tuple of periods.==

    periods = periods_from_sdmx_strings(sdmx_strings, frequency=None, )

The frequency is settled once, not per string: left as `None`, it is inferred
from the **first** string and then applied to all of them. A sequence that
mixes frequencies is therefore not detected as such; the later strings are
parsed as though they were the first one's frequency, and fail or misread
depending on the shapes involved.

An empty input returns an empty tuple without touching the frequency.


**Input arguments.**


???+ input "sdmx_strings"
    An iterable of SDMX strings.

???+ input "frequency"
    The frequency to read them as, or `None` to infer it from the first.


### Returns


A tuple of periods, one per string.

................................................................................
    """
    sdmx_strings = tuple(sdmx_strings)
    if not sdmx_strings:
        return ()
    frequency = (
        Frequency.from_sdmx_string(sdmx_strings[0], )
        if frequency is None else frequency
    )
    period_class = PERIOD_CLASS_FROM_FREQUENCY_RESOLUTION[frequency]
    return tuple(period_class.from_sdmx_string(i) for i in sdmx_strings)


def periods_from_iso_strings(
    iso_strings: Iterable[str],
    *,
    frequency: Frequency | None = None,
) -> tuple[Period]:
    r"""
................................................................................

## `periods_from_iso_strings`

==Read a sequence of ISO-8601 strings into a tuple of periods.==

    periods = periods_from_iso_strings(iso_strings, *, frequency=None, )

Unlike the SDMX reader, nothing is inferred: `frequency` defaults to daily
when left as `None`. Each string is passed to the `from_iso_string` of the
matching class, so a lower frequency keeps only what it can hold.

`frequency` is keyword-only here, while on `periods_from_sdmx_strings` it is
positional.


**Input arguments.**


???+ input "iso_strings"
    An iterable of `yyyy-mm-dd` strings.

???+ input "frequency"
    Keyword-only. The frequency to read them as; daily when `None`.


### Returns


A tuple of periods, one per string.

................................................................................
    """
    if frequency is None:
        frequency = Frequency.DAILY
    period_class = PERIOD_CLASS_FROM_FREQUENCY_RESOLUTION[frequency]
    return tuple(period_class.from_iso_string(i, ) for i in iso_strings)


def periods_from_python_dates(
    python_dates: Iterable[_dt.date],
    *,
    frequency: Frequency | None = None,
) -> tuple[Period]:
    r"""
................................................................................

## `periods_from_python_dates`

==Convert a sequence of Python dates into a tuple of periods.==

    periods = periods_from_python_dates(python_dates, *, frequency=None, )

`frequency` is keyword-only and defaults to daily. Each date goes through
`Period.from_python_date`.


**Input arguments.**


???+ input "python_dates"
    An iterable of `datetime.date` or `datetime.datetime` objects.

???+ input "frequency"
    Keyword-only. The frequency to convert to; daily when `None`.


### Returns


A tuple of periods, one per date.

................................................................................
    """
    if frequency is None:
        frequency = Frequency.DAILY
    return tuple(Period.from_python_date(i, frequency=frequency, ) for i in python_dates)


def get_encompassing_span(
    *args: tuple[ResolutionContextProtocol | None, ...],
) -> tuple[Span, Period, Period, ]:
    r"""
................................................................................

## `get_encompassing_span`

==Smallest span covering everything given, plus its two endpoints.==

    span, start_per, end_per = get_encompassing_span(*args)

Each argument is either an object carrying `start_date` and `end_date`, or an
iterable of periods. `None` arguments are skipped, as are `None` periods
inside an iterable.

Given nothing it can use, the two endpoints come back as `None` and the span
is built from the contextual sentinels, so the result is an unresolved span
rather than an empty one.


**Input arguments.**


???+ input "*args"
    Objects carrying `start_date` and `end_date` attributes, or iterables
    of periods. `None` arguments, and `None` periods inside an iterable,
    are skipped.


### Returns


A three-tuple: the `Span`, the earliest start, and the latest end.

................................................................................
    """
    start_dates = tuple(_get_period(i, "start_date", min, ) for i in args if i is not None)
    end_periods = tuple( _get_period(i, "end_date", max, ) for i in args if i is not None)
    start_dates = tuple(i for i in start_dates if i is not None)
    end_periods = tuple(i for i in end_periods if i is not None)
    start = min(start_dates) if start_dates else None
    end = max(end_periods) if end_periods else None
    return Span(start, end), start, end,


def _get_period(something, attr_name, select_func, ) -> Period | None:
    if hasattr(something, attr_name, ):
        return getattr(something, attr_name, )
    try:
        return select_func(i for i in something if i is not None)
    except:
        return None


def periods_from_until(
    start_per: Period,
    end_per: Period,
    step: int = 1,
) -> tuple[Period]:
    r"""
................................................................................

## `periods_from_until`

==Every period from one to another, as a tuple.==

    periods = periods_from_until(start_per, end_per, step=1, )

Both endpoints are included. The two must be of the same frequency; otherwise
`wrongdoings.Error` is raised.

A pair given the wrong way round is not an error: the underlying `range` is
empty, so an empty tuple comes back with nothing said. `periods_from_to` is an
alias of this function.


**Input arguments.**


???+ input "start_per, end_per"
    The two endpoints, both included.

???+ input "step"
    Stride in periods, 1 when left alone.


### Returns


A tuple of periods.


### Examples


    >>> import datapie as dp
    >>> from datapie.periods import periods_from_until
    >>> periods_from_until(dp.qq(2020,1), dp.qq(2020,4), 2)
    (qq(2020,1), qq(2020,3))

................................................................................
    """
    _check_periods(start_per, end_per, )
    serials = range(start_per.serial, end_per.serial + 1, step, )
    period_class = type(start_per)
    return tuple(period_class(x) for x in serials)


periods_from_to = periods_from_until


def ensure_period_tuple(
    period_or_string: Iterable[Period] | str,
    frequency: Frequency | None = None,
) -> tuple[Period, ...]:
    r"""
................................................................................

## `ensure_period_tuple`

==Coerce periods-or-a-string into a tuple of periods.==

    periods = ensure_period_tuple(period_or_string, frequency=None, )

Given anything iterable, it is simply turned into a tuple. Given a string, it
is handed to `_period_tuple_from_string`, which understands `...` and `>>` as
range separators and `,` as a list separator.

The string path does not work. Every branch of `_period_tuple_from_string`
calls its helpers with the frequency and the strings the wrong way round, so a
plain period string raises `KeyError`, and the range and list forms raise
`TypeError: 'NoneType' object is not iterable`. Only the iterable path is
usable today.


**Input arguments.**


???+ input "period_or_string"
    An iterable of periods, or a string.

???+ input "frequency"
    Only reaches the string path, which does not work; see above.


### Returns


A tuple of periods.

................................................................................
    """
    #[
    if isinstance(period_or_string, str):
        return _period_tuple_from_string(period_or_string, frequency, )
    else:
        return tuple(period_or_string)
    #]


def _period_tuple_from_string(
    period_string: str,
    frequency: Frequency | None = None,
) -> tuple[Period, ...]:
    """
    """
    #[
    if "..." in period_string:
        start, end = period_string.split("...")
        return tuple(periods_from_to(*periods_from_sdmx_strings(frequency, (start, end, ))))
    if ">>" in period_string:
        start, end = period_string.split(">>")
        return tuple(periods_from_to(*periods_from_sdmx_strings(frequency, (start, end, ))))
    if "," in period_string:
        return tuple(periods_from_sdmx_strings(frequency, period_string.split(",")))
    return (Period.from_sdmx_string(frequency, period_string), )
    #]


def _is_period(x: Any, ) -> bool:
    return isinstance(x, Period, )


def refrequent(
    period: Period,
    new_freq: Frequency,
    *args,
    **kwargs,
) -> Period:
    r"""
................................................................................

## `refrequent`

Called as `x.refrequent(...)` (method form) or
`datapie.refrequent(x, ...)` (function form).

==Convert a period to a different frequency.==

    new_per = refrequent(period, new_freq, position="start", )

The same operation as the `Period.refrequent` method, written as a function
with the period first. `convert_to_new_freq` is an alias.


**Input arguments.**


???+ input "period"
    The period to convert.

???+ input "new_freq"
    The frequency to convert to.

???+ input "*args, **kwargs"
    Forwarded to `to_ymd`, which is where `position` is read.


### Returns


A new `Period` at the new frequency.

................................................................................
    """
    year, month, day = period.to_ymd(*args, **kwargs, )
    new_class = PERIOD_CLASS_FROM_FREQUENCY_RESOLUTION[new_freq]
    return new_class.from_ymd(year, month, day, )


def spans_from_short_span(
    short_span: Iterable[Period],
    max_lag: int = 0,
    max_lead: int = 0,
) -> tuple[tuple[Period], tuple[Period]]:
    r"""
................................................................................

## `spans_from_short_span`

==Widen a span by a lag and a lead, returning both the short and long form.==

    short, long = spans_from_short_span(short_span, max_lag=0, max_lead=0, )

The input is first normalised: its first and last periods are taken and every
period between them filled in, so gaps in the input are closed and a step
other than 1 is lost.

The two shifts are **added**, not subtracted, so a lag has to be passed as a
negative number to widen the span backwards. Passing `max_lag=1` moves the
opening end forward instead, giving a long span that does not contain the
short one.


**Input arguments.**


???+ input "short_span"
    An iterable of periods. Only its first and last are used.

???+ input "max_lag"
    Added to the opening end, so pass a negative number to widen
    backwards.

???+ input "max_lead"
    Added to the closing end.


### Returns


A two-tuple of period tuples: the normalised short span and the long span.

................................................................................
    """
    short_span = tuple(short_span)
    short_span = periods_from_until(short_span[0], short_span[-1], )
    long_span = long_span_from_short_span(short_span, max_lag, max_lead, )
    return short_span, long_span,


def long_span_from_short_span(
    short_span: Iterable[Period],
    max_lag: int = 0,
    max_lead: int = 0,
) -> tuple[Period]:
    r"""
................................................................................

## `long_span_from_short_span`

==The long span alone, for a given lag and lead.==

    long = long_span_from_short_span(short_span, max_lag=0, max_lead=0, )

The second half of `spans_from_short_span`, and it takes the same sign
convention: both shifts are added, so a widening lag is a negative number.
Indexes its argument directly, so it needs a sequence rather than any
iterable.


**Input arguments.**


???+ input "short_span"
    A sequence of periods; it is indexed, not iterated.

???+ input "max_lag, max_lead"
    Both added to the respective ends, as in `spans_from_short_span`.


### Returns


A tuple of periods from `short_span[0] + max_lag` to `short_span[-1] +
max_lead`.

................................................................................
    """
    return periods_from_until(short_span[0]+max_lag, short_span[-1]+max_lead, )


def spans_from_long_span(
    long_span: Iterable[Period],
    max_lag: int = 0,
    max_lead: int = 0,
) -> Span:
    r"""
................................................................................

## `spans_from_long_span`

==Narrow a long span back down by a lag and a lead.==

    short, long = spans_from_long_span(long_span, max_lag=0, max_lead=0, )

The inverse of `spans_from_short_span`: the shifts are subtracted here rather
than added, so the same pair of numbers undoes what that function did.

Annotated `-> Span`, but it returns a two-tuple of period tuples, in the order
short-then-long -- the reverse of the naming of its own argument.


**Input arguments.**


???+ input "long_span"
    An iterable of periods. Only its first and last are used.

???+ input "max_lag, max_lead"
    Both subtracted, undoing what `spans_from_short_span` added.


### Returns


A two-tuple of period tuples: the short span and the normalised long span.

................................................................................
    """
    long_span = tuple(long_span)
    long_span = periods_from_until(long_span[0], long_span[-1], )
    short_span = periods_from_until(long_span[0]-max_lag, long_span[-1]-max_lead, )
    return short_span, long_span,


convert_to_new_freq = refrequent


SPAN_ELLIPSIS = "…"


def get_printable_span(*args, ) -> str:
    r"""
................................................................................

## `get_printable_span`

==Join periods into one display string.==

    text = get_printable_span(*args)

Each argument is put through `str()` and the results joined with a horizontal
ellipsis, `…`. Usually called with two periods to render a span as
`2020-Q1…2020-Q4`, but it takes any number of them; with none it returns an
empty string.


**Input arguments.**


???+ input "*args"
    Any number of periods, or anything else `str()` accepts.


### Returns


The joined string.

................................................................................
    """
    return SPAN_ELLIPSIS.join(str(i) for i in args)

def extend_span(
    span: Iterable[Period],
    min_shift: int,
    max_shift: int,
    prepend_initial: bool,
    append_terminal: bool,
) -> tuple[Period, Period]:
    r"""
................................................................................

## `extend_span`

==Endpoints of a span, optionally pushed out by a lag and a lead.==

    start_per, end_per = extend_span(
        span, min_shift, max_shift, prepend_initial, append_terminal,
    )

Takes the first and last periods of `span` and moves each one only if the
matching flag is set: `prepend_initial` adds `min_shift` to the start,
`append_terminal` adds `max_shift` to the end. Both shifts are added, so
`min_shift` is expected to be negative for the start to move backwards. With
both flags `False` the endpoints come back unchanged.


**Input arguments.**


???+ input "span"
    An iterable of periods. Only its first and last are used.

???+ input "min_shift, max_shift"
    Added to the start and the end respectively, and only when the
    matching flag is set. `min_shift` is expected to be negative.

???+ input "prepend_initial, append_terminal"
    Whether to move the start and the end at all.


### Returns


A two-tuple, the start period and the end period.

................................................................................
    """
    range_tuple = tuple(t for t in span)
    start_date, end_date, = range_tuple[0], range_tuple[-1],
    if prepend_initial:
        start_date += min_shift
    if append_terminal:
        end_date += max_shift
    return start_date, end_date,

