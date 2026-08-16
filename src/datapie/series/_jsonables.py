r"""
"""


#[

from __future__ import annotations

import documark as _dm

from ..periods import Period
from ..frequencies import Frequency

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Self, Callable

#]


#-------------------------------------------------------------------------------
# Mixin methods
#-------------------------------------------------------------------------------


class Mixin:
    #[

    @_dm.reference(category="serialization", add_heading=False, )
    def to_jsonable(
        self,
        *,
        period_to_string: Callable = Period.to_sdmx_string,
        include_description: bool = True,
        include_frequency: bool = True,
        allow_multiple_variants: bool = False,
    ) -> dict:
        r"""
................................................................................

## `to_jsonable`

==Turns a time series into a plain dictionary that can be written out as JSON.==

    jsonable = self.to_jsonable(
        *,
        period_to_string=Period.to_sdmx_string,
        include_description=True,
        include_frequency=True,
        allow_multiple_variants=False,
    )

Every argument is keyword-only.


**Input arguments.**


???+ input "period_to_string"
    Turns the start period into text. Left alone it writes the SDMX
    form, `"2020-Q1"`; `Period.to_iso_string` writes `"2020-01-01"`
    instead. Any function taking a `Period` and returning a string will
    do. Whatever you choose here has to be matched by
    `period_from_string` when the dictionary is read back.

???+ input "include_description"
    Whether the `"description"` key appears at all. On when left alone.

???+ input "include_frequency"
    Whether the `"frequency"` key appears at all. On when left alone,
    and worth keeping: `from_jsonable` needs it to read non-daily ISO
    periods.

???+ input "allow_multiple_variants"
    Not implemented. Setting it to `True` raises `NotImplementedError`.


A series holding more than one variant cannot be written at all, and
the two ways out are both closed: the `ValueError` you get tells you to
pass `allow_multiple_variants=True`, which then raises
`NotImplementedError`.

Missing observations are written through unchanged. That is no trouble
in the dictionary itself, but `NaN` is not valid JSON, so handing the
result to the standard `json` module -- as `Databox.series_to_json_file`
does -- writes `{"values": [1.0, NaN, 3.0]}`, which a strict reader
rejects.


### Returns


A dictionary holding `"description"`, `"frequency"`, `"start"` and
`"values"`, the first two only if you asked for them. `"values"` is a
tuple. For an empty series `"start"` is `None`, `"values"` is `()` and
`"frequency"` is `"?"`.


### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1), values=np.array([1., 2.]))
    >>> x.to_jsonable(include_description=False)
    {'frequency': 'Q', 'start': '2020-Q1', 'values': (1.0, 2.0)}

................................................................................
        """
        if allow_multiple_variants:
            raise NotImplementedError("allow_multiple_variants=True is not implemented yet.")
        #
        if self.num_variants > 1 and not allow_multiple_variants:
            raise ValueError("The series has multiple variants. Set allow_multiple_variants=True to serialize all variants.")
        #
        jsonable = {}
        #
        if include_description:
            jsonable["description"] = self.get_description() or ""
        #
        if include_frequency:
            jsonable["frequency"] = self.frequency.to_jsonable()
        #
        jsonable["start"] = (
            period_to_string(self.start)
            if self.start is not None else None
        )
        #
        jsonable["values"] = self.get_values(unpack_singleton=not allow_multiple_variants)
        #
        return jsonable


    @classmethod
    @_dm.reference(
        category="constructor",
        call_name="Series.from_jsonable",
        add_heading=False,
    )
    def from_jsonable(
        klass,
        jsonable: dict,
        *,
        period_from_string: Callable = Period.from_sdmx_string,
        frequency_included: bool = True,
        description_included: bool = True,
        allow_multiple_variants: bool = False,
    ) -> Self:
        r"""
................................................................................

## `Series.from_jsonable`

==Builds a time series from a dictionary of the kind `to_jsonable` produces.==

    self = Series.from_jsonable(
        jsonable,
        *,
        period_from_string=Period.from_sdmx_string,
        frequency_included=True,
        description_included=True,
        allow_multiple_variants=False,
    )

This is a class method: call it on the class, as
`Series.from_jsonable(d)`, not on a series you already have. Everything
after `jsonable` is keyword-only.


**Input arguments.**


???+ input "jsonable"
    The dictionary to read, laid out the way `to_jsonable` writes one.

???+ input "period_from_string"
    Parses the start period, and has to match the way it was written.
    Left alone it reads the SDMX form, `"2020-Q1"`;
    `Period.from_iso_string` reads `"2020-01-01"`, and for anything but
    daily periods it needs the frequency to be present. Any function
    taking a string and a `frequency=` keyword will do.

???+ input "frequency_included"
    Whether the `"frequency"` key is there to be read. On when left
    alone.

???+ input "description_included"
    Whether the `"description"` key is there to be read. On when left
    alone; switched off, the new series gets an empty description
    whatever the dictionary holds.

???+ input "allow_multiple_variants"
    Not implemented. Setting it to `True` raises `NotImplementedError`.


The flags have to match the ones used when writing, and they are
spelled differently at the two ends -- `include_frequency` going out
against `frequency_included` coming back. Writing with
`include_frequency=False` and reading with the default
`frequency_included=True` raises `KeyError: 'frequency'`, and the same
goes for the description. Reading ISO periods with the default SDMX
parser raises `ValueError: not enough values to unpack (expected 2, got
1)`, which does not obviously point at the parser.


### Returns


A new series. When the stored start or values are empty you get an
empty series instead, carrying the description if
`description_included` was left on.


### Examples


A round trip, description included:

    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2.]), description="GDP")
    >>> y = dp.Series.from_jsonable(x.to_jsonable())
    >>> y.get_data()[:, 0].tolist()
    [1.0, 2.0]
    >>> y.get_description()
    'GDP'

................................................................................
        """
        if allow_multiple_variants:
            raise NotImplementedError("allow_multiple_variants=True is not implemented yet.")
        #
        frequency = (
            Frequency.from_jsonable(jsonable["frequency"], )
            if frequency_included else None
        )
        #
        start = (
            period_from_string(jsonable["start"], frequency=frequency, )
            if jsonable["start"] else None
        )
        #
        values = jsonable["values"]
        if not allow_multiple_variants:
            values = tuple(values)
        #
        description = (
            jsonable["description"]
            if description_included else None
        )
        #
        if not start or not values:
            return klass.void(description=description, )
        #
        return klass(
            start=start,
            values=values,
            description=description,
        )


        #]

