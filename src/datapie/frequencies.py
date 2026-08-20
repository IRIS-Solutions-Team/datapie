"""
Time frequencies
"""


#[

from __future__ import annotations

# Standard library imports
import re as _re
import enum as _en

# Typing imports
from typing import Self, NoReturn

# Third-party imports
import documark as _dm

# Application imports
from . import wrongdoings as _wrongdoings

#]


__all__ = (
    "is_sdmx_string",
    "Frequency",
    "YEARLY", "HALFYEARLY", "QUARTERLY", "MONTHLY", "WEEKLY", "DAILY",
)


@_dm.reference(
    path=("data_management", "frequencies.md", ),
    categories=None,
)
class Frequency(_en.IntEnum):
    r"""
................................................................................

Time frequencies
=================

`Frequency` is an `IntEnum`, so every member **is** an integer: it compares,
sorts and arithmetics like one. The integer is how many periods of that kind
fit in a year, with two members that fall outside that reading.

| Value | Member       | Regular          | Meaning
|------:|--------------|:----------------:|---------
| 1     | `YEARLY`     | :material-check: | One period a year
| 2     | `HALFYEARLY` | :material-check: | Two
| 4     | `QUARTERLY`  | :material-check: | Four
| 12    | `MONTHLY`    | :material-check: | Twelve
| 52    | `WEEKLY`     |                  | Weeks do not divide a year
| 365   | `DAILY`      |                  | Leap years have 366
| 0     | `INTEGER`    |                  | Numbered observations
| -1    | `UNKNOWN`    |                  | Not established

The four regular frequencies are the ones that divide a year evenly, which is
what lets a period of that frequency be held as a single serial,
`year*frequency + segment - 1`. `is_regular` reports it.

`ANNUAL` and `HALFANNUAL` are aliases of `YEARLY` and `HALFYEARLY` -- the same
objects, not separate members. Iterating `Frequency` does not yield them, and
neither does anything that searches the members.

Six of the eight members are re-exported at package level, so they can be
written `dp.QUARTERLY`. `INTEGER` and `UNKNOWN` are not, and have to be
reached through the class.

Where you meet a `Frequency`: the conversion methods on time
[`Series`](time_series.md) -- `aggregate` and `disaggregate` -- take one, and
so does any code that has to ask what kind of period or series it is holding.

................................................................................
    """
    #[

    INTEGER = 0
    YEARLY = 1
    ANNUAL = 1
    HALFYEARLY = 2
    HALFANNUAL = 2
    QUARTERLY = 4
    MONTHLY = 12
    WEEKLY = 52
    DAILY = 365
    UNKNOWN = -1

    @classmethod
    @_dm.reference(
        category="constructor",
        call_name="Frequency.from_letter",
        add_heading=False,
    )
    def from_letter(
        klass,
        string: str,
    ) -> Self:
        r"""
................................................................................

## `Frequency.from_letter`

==Determine a frequency from the first letter of a string.==

    freq = Frequency.from_letter(string)

Underscores are removed, the rest is upper-cased, and **only the first
character is looked at**; the first member whose name starts with that
letter wins. So `"Q"`, `"q"`, `"quarterly"` and `"__quarterly__"` all give
`QUARTERLY`. A first character of `"?"` is special-cased to `UNKNOWN`, and
since only that character is read, `"?abc"` and `"_?_"` give `UNKNOWN`
too.

The string is **not** stripped, unlike the one `from_sdmx_string` takes,
so a leading space is read as the letter and matches nothing.

Two things follow from matching on one letter. `"A"` matches nothing,
because `ANNUAL` is an alias and aliases are not iterated; and any string
beginning with the same letter as a member resolves to that member, so
`"__description__"` gives `DAILY`.


**Input arguments.**


???+ input "string"
    Any non-empty string. Only its first character is used, after
    underscores are dropped and the case is folded.


### Returns


The matching `Frequency` member.

An unmatched letter raises a bare `StopIteration` carrying no message,
rather than a `ValueError` naming the input. An empty string raises
`IndexError` before the search starts.


### Examples


    >>> import datapie as dp
    >>> dp.Frequency.from_letter("Q")
    <Frequency.QUARTERLY: 4>
    >>> dp.Frequency.from_letter("?")
    <Frequency.UNKNOWN: -1>

................................................................................
        """
        letter = string.replace("_", "").upper()[0]
        if letter == "?":
            return klass.UNKNOWN
        return next( x for x in klass if x.name.startswith(letter) )

    @classmethod
    @_dm.reference(
        category="constructor",
        call_name="Frequency.from_sdmx_string",
        add_heading=False,
    )
    def from_sdmx_string(
        klass,
        sdmx_string: str,
    ) -> Self | NoReturn:
        r"""
................................................................................

## `Frequency.from_sdmx_string`

==Determine a frequency from the shape of an SDMX string.==

    freq = Frequency.from_sdmx_string(sdmx_string)

The string is stripped and tested against the patterns in `SDMX_PATTERNS`,
one per frequency, with `fullmatch` -- the pattern has to cover the whole
string, not a prefix of it. Under that rule the patterns are disjoint, so
at most one can ever match and the order they are tried in makes no
difference to the answer.

Only the half-year and the quarter numbers are range-checked; a month or a
week is any two digits. See `SDMX_PATTERNS` for the patterns themselves.

The `INTEGER` pattern ends in a comma, which the string an integer period
prints does not have.


**Input arguments.**


???+ input "sdmx_string"
    The string to classify. Leading and trailing whitespace is ignored.


### Returns


The matching `Frequency` member.

A string matching nothing raises `wrongdoings.Error` quoting it: `Cannot
determine time frequency from "..."; probably not a valid SDMX string.`


### Examples


    >>> import datapie as dp
    >>> dp.Frequency.from_sdmx_string("2020-Q1")
    <Frequency.QUARTERLY: 4>

................................................................................
        """
        sdmx_string = sdmx_string.strip()
        for freq, pattern in SDMX_PATTERNS.items():
            if pattern.fullmatch(sdmx_string, ):
                return freq
        raise _wrongdoings.Error(
            f"Cannot determine time frequency from \"{sdmx_string}\"; "
            f"probably not a valid SDMX string."
        )

    @property
    @_dm.reference(category="property", add_heading=False, )
    def letter(self, ) -> str:
        r"""
................................................................................

## `letter`

==Single-letter code for the frequency, as a read-only property.==

    code = freq.letter

The first letter of the member's name, except `UNKNOWN`, which gives
`"?"`. `from_letter` reads the same codes back, so the two round-trip for
every member.


### Returns


A one-character string: `I`, `Y`, `H`, `Q`, `M`, `W`, `D` or `?`.

................................................................................
        """
        return self.name[0] if self is not self.UNKNOWN else "?"

    def to_jsonable(self, ) -> str:
        r"""
................................................................................

## `to_jsonable`

==The frequency as a one-letter string, for JSON serialisation.==

    text = freq.to_jsonable()

The `letter` property handed back as a plain `str`. Paired with
`from_jsonable`, and the round trip holds for all eight members.


### Returns


A one-character string.

................................................................................
        """
        return str(self.letter)

    @classmethod
    def from_jsonable(
        klass,
        jsonable: str,
    ) -> Self:
        r"""
................................................................................

## `Frequency.from_jsonable`

==Rebuild a frequency from the one-letter string `to_jsonable` wrote.==

    freq = Frequency.from_jsonable(jsonable)

Delegates straight to `from_letter`, so everything said there about
matching on the first letter, and about the exceptions, applies here too.


**Input arguments.**


???+ input "jsonable"
    The one-character code.


### Returns


The matching `Frequency` member.

................................................................................
        """
        return klass.from_letter(jsonable, )

    @property
    @_dm.reference(category="property", add_heading=False, )
    def is_regular(self, ) -> bool:
        r"""
................................................................................

## `is_regular`

==True when the frequency divides a year evenly.==

    flag = freq.is_regular

True for `YEARLY`, `HALFYEARLY`, `QUARTERLY` and `MONTHLY`; false for
`WEEKLY`, `DAILY`, `INTEGER` and `UNKNOWN`. It is the line between the
frequencies whose periods can be held as `year*frequency + segment - 1`
and those that need a scheme of their own.


### Returns


`True` or `False`.

................................................................................
        """
        return self in _REGULAR_FREQUENCIES

    def __str__(self, ) -> str:
        return self.name

    #]


_REGULAR_FREQUENCIES = (
   Frequency.YEARLY,
   Frequency.HALFYEARLY,
   Frequency.QUARTERLY,
   Frequency.MONTHLY,
)


# ..............................................................................
#
# ## Frequency member docstrings
#
# ==Seven short docstrings assigned to individual members.==
#
# One assignment each for `YEARLY`, `HALFYEARLY`, `QUARTERLY`, `MONTHLY`,
# `WEEKLY`, `DAILY` and `INTEGER`, so that `help()` on a member says something
# more specific than the class does.
#
# `UNKNOWN` gets no assignment, so it keeps the class docstring instead --
# `Frequency.UNKNOWN.__doc__` is the whole "Time frequencies" page.
#
# None of the seven carries `@_dm.reference`, so none reaches the rendered
# reference page; they show only through `help()` or a source read.
#
# ..............................................................................
Frequency.YEARLY.__doc__ = r"""
................................................................................

==Create a yearly frequency representation==

See documentation for the time [`Frequency`](frequencies.md).

................................................................................
"""


Frequency.HALFYEARLY.__doc__ = r"""
................................................................................

==Create a half-yearly frequency representation==

See documentation for the time [`Frequency`](frequencies.md).

................................................................................
"""


Frequency.QUARTERLY.__doc__ = r"""
................................................................................

==Create a quarterly frequency representation==

See documentation for the time [`Frequency`](frequencies.md).

................................................................................
"""


Frequency.MONTHLY.__doc__ = r"""
................................................................................

==Create a monthly frequency representation==

See documentation for the time [`Frequency`](frequencies.md).

................................................................................
"""


Frequency.WEEKLY.__doc__ = r"""
................................................................................

==Create a weekly frequency representation==

See documentation for the time [`Frequency`](frequencies.md).

................................................................................
"""


Frequency.DAILY.__doc__ = r"""
................................................................................

==Create a daily frequency representation==

See documentation for the time [`Frequency`](frequencies.md).

................................................................................
"""


Frequency.INTEGER.__doc__ = r"""
................................................................................

==Create an integer frequency representation==

See documentation for the time [`Frequency`](frequencies.md).

................................................................................
"""


# ..............................................................................
#
# ## Module-level frequency names
#
# ==Six members re-exported so they can be written `dp.QUARTERLY`.==
#
#     YEARLY = Frequency.YEARLY
#     HALFYEARLY = Frequency.HALFYEARLY
#     QUARTERLY = Frequency.QUARTERLY
#     MONTHLY = Frequency.MONTHLY
#     WEEKLY = Frequency.WEEKLY
#     DAILY = Frequency.DAILY
#
# The same objects as the members, not copies, so `dp.QUARTERLY is
# Frequency.QUARTERLY`. These six are what `__all__` exports; the two left out
# are noted in the `Frequency` overview.
#
# ..............................................................................
YEARLY = Frequency.YEARLY
HALFYEARLY = Frequency.HALFYEARLY
QUARTERLY = Frequency.QUARTERLY
MONTHLY = Frequency.MONTHLY
WEEKLY = Frequency.WEEKLY
DAILY = Frequency.DAILY


# ..............................................................................
#
# ## `SDMX_PATTERNS`
#
# ==One compiled regular expression per frequency, keyed by member.==
#
# The table that `from_sdmx_string` and `is_sdmx_string` both walk.
#
# | Frequency    | Pattern                | Example
# |--------------|------------------------|-------------
# | `YEARLY`     | `\d\d\d\d`             | `2020`
# | `HALFYEARLY` | `\d\d\d\d-H[12]`       | `2020-H1`
# | `QUARTERLY`  | `\d\d\d\d-Q[1234]`     | `2020-Q1`
# | `MONTHLY`    | `\d\d\d\d-\d\d`        | `2020-01`
# | `WEEKLY`     | `\d\d\d\d-W[012345]\d` | `2020-W01`
# | `DAILY`      | `\d\d\d\d-\d\d-\d\d`   | `2020-01-01`
# | `INTEGER`    | `\([-+]?\d+\),`         | `(1),`
#
# Both callers use `fullmatch`, so a pattern has to cover the whole string. That
# is what keeps the seven apart: no string matches two of them, `\d\d\d\d` does
# not take the front of `2020-Q1`, and `MONTHLY` does not take `2020-01-01`. The
# order of the dictionary therefore carries no meaning -- shuffling it leaves
# every classification unchanged.
#
# Only `[12]` and `[1234]` bound anything. A month or a week is any two digits,
# so `"2020-00"`, `"2020-99"`, `"2020-13"` and `"2020-W59"` all classify. The
# table answers what shape a string has, not whether it names a period that
# exists.
#
# Public by name but not in `__all__`, so it is reached as
# `frequencies.SDMX_PATTERNS`. `UNKNOWN` has no entry of its own: a string
# matching nothing is an error, not an unknown frequency.
#
# ..............................................................................
SDMX_PATTERNS = {
    Frequency.YEARLY: _re.compile(r"\d\d\d\d", ),
    Frequency.HALFYEARLY: _re.compile(r"\d\d\d\d-H[12]", ),
    Frequency.QUARTERLY: _re.compile(r"\d\d\d\d-Q[1234]", ),
    Frequency.MONTHLY: _re.compile(r"\d\d\d\d-\d\d", ),
    Frequency.WEEKLY: _re.compile(r"\d\d\d\d-W[012345]\d", ),
    Frequency.DAILY: _re.compile(r"\d\d\d\d-\d\d-\d\d", ),
    Frequency.INTEGER: _re.compile(r"\([\-\+]?\d+\),", ),
}


def is_sdmx_string(
    input_string: str,
) -> bool:
    r"""
................................................................................

## `is_sdmx_string`

==True when a string has the shape of an SDMX period string.==

    flag = is_sdmx_string(input_string)

The same walk over `SDMX_PATTERNS` that `from_sdmx_string` makes, reporting
only whether anything matched. The one to use where a non-match is expected
and an exception would be in the way.


**Input arguments.**


???+ input "input_string"
    The string to test. Leading and trailing whitespace is ignored.


### Returns


`True` if some pattern matches the whole string, `False` otherwise.


### Examples


    >>> import datapie as dp
    >>> dp.is_sdmx_string("2020-Q1")
    True
    >>> dp.is_sdmx_string("(1)")
    False

................................................................................
    """
    #[
    input_string = input_string.strip()
    for pattern in SDMX_PATTERNS.values():
        if pattern.fullmatch(input_string, ):
            return True
    return False
    #]

