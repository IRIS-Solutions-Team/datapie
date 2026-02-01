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
from .. import wrongdoings as _wrongdoings

#]


__all__ = (
    "is_sdmx_string",
    "Frequency",
    "YEARLY", "HALFYEARLY", "QUARTERLY", "MONTHLY", "WEEKLY", "DAILY",
    "REGULAR_FREQUENCIES",
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

Time frequencies are simple integer values that represent the number of time
periods within a year, plus two special frequencies: a so-called "integer"
frequency (for simple numbered observations without relation to calendar time),
and a representation for unknown or unspecified frequencies. For convenience,
the `Frequency` enum provides a set of predefined names for all the time
frequencies available.

The `Frequencies` are classified into regular and
irregular frequencies. Regular frequencies are those that are evenly spaced
within a year no matter the year, while irregular frequencies are those that
vary in the number of periods within a year due to human calendar conventions
and irregularities.


| Integer value | `Frequency` enum       | Regular           | Description
|--------------:|------------------------|:-----------------:|-------------
| 1             | `irispie.YEARLY`       | :material-check:  | Yearly frequency
| 2             | `irispie.HALFYEARLY`   | :material-check:  | Half-yearly frequency
| 4             | `irispie.QUARTERLY`    | :material-check:  | Quarterly frequency
| 12            | `irispie.MONTHLY`      | :material-check:  | Monthly frequency
| 52            | `irispie.WEEKLY`       |                   | Weekly frequency
| 365           | `irispie.DAILY`        |                   | Daily frequency
| 0             | `irispie.INTEGER`      |                   | Integer frequency (numbered observations)
| -1            | `irispie.UNKNOWN`      |                   | Unknown or unspecified frequency


The most often direct use of `Frequencies` in frequency conversion methods, such
as `aggregate` and `disaggregate` for time [`Series`](time_series.md) and whenever a
custom check of time period or time series properties is needed.

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
    )
    def from_letter(
        klass,
        string: str,
    ) -> Self:
        r"""
................................................................................

==Determine frequency from a letter==

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
    )
    def from_sdmx_string(
        klass,
        sdmx_string: str,
    ) -> Self | NoReturn:
        r"""
................................................................................

==Determine frequency of an SDMX string==

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
    @_dm.reference(category="property", )
    def letter(self, ) -> str:
        r"""==Single letter representation of time frequency=="""
        return self.name[0] if self is not self.UNKNOWN else "?"

    def to_jsonable(self, ) -> str:
        r"""
        """
        return str(self.letter)

    @classmethod
    def from_jsonable(
        klass,
        jsonable: str,
    ) -> Self:
        r"""
        """
        return klass.from_letter(jsonable, )

    @property
    @_dm.reference(category="property", )
    def is_regular(self, ) -> bool:
        r"""==True for regular time frequency=="""
        return self in REGULAR_FREQUENCIES

    def __str__(self, ) -> str:
        return self.name

    #]


REGULAR_FREQUENCIES = (
   Frequency.YEARLY,
   Frequency.HALFYEARLY,
   Frequency.QUARTERLY,
   Frequency.MONTHLY,
)


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


YEARLY = Frequency.YEARLY
HALFYEARLY = Frequency.HALFYEARLY
QUARTERLY = Frequency.QUARTERLY
MONTHLY = Frequency.MONTHLY
WEEKLY = Frequency.WEEKLY
DAILY = Frequency.DAILY


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
    """
    #[
    input_string = input_string.strip()
    for pattern in SDMX_PATTERNS.values():
        if pattern.fullmatch(input_string, ):
            return True
    return False
    #]

