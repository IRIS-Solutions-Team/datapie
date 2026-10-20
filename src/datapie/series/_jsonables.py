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

    @_dm.reference(category="serialization", )
    def to_jsonable(
        self,
        *,
        period_to_string: Callable = Period.to_sdmx_string,
        include_description: bool = True,
        include_frequency: bool = True,
        allow_multiple_variants: bool = False,
    ) -> dict:
        r"""
==Turn a single-variant series into a dictionary for JSON==

#### Syntax

    jsonable = series.to_jsonable(
        period_to_string=Period.to_sdmx_string,
        include_description=True,
        include_frequency=True,
        allow_multiple_variants=False,
    )

#### Input arguments

!!! input "period_to_string"
    A function that converts the start Period to text.
    Default: `Period.to_sdmx_string`. Use a matching parser when reading it back.

!!! input "include_description"
    Whether to include the description. Default: `True`.

!!! input "include_frequency"
    Whether to include the frequency's one-letter code. Default: `True`.

!!! input "allow_multiple_variants"
    Default: `False`. Only single-variant serialization is supported;
    setting this to `True` raises `NotImplementedError`.

#### Returns

!!! returns "jsonable"
    A dictionary with `"start"` and `"values"`, and optionally `"description"`
    and `"frequency"`. Values are a tuple. For an empty single-variant series,
    the start is `None`, values are empty, and frequency is `"?"` when included.

#### Mutation

Leaves the series unchanged. All input arguments are keyword-only.

#### Details

A series with multiple variants cannot be serialized by this method.
Missing observations remain numeric NaN values, not JSON `null`; further
conversion may be needed for strict JSON.

#### See also

`Series.from_jsonable`.
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
==Create a series from a dictionary of saved observations==

#### Syntax

    new_series = Series.from_jsonable(
        jsonable,
        period_from_string=Period.from_sdmx_string,
        frequency_included=True,
        description_included=True,
        allow_multiple_variants=False,
    )

#### Input arguments

!!! input "jsonable"
    A dictionary containing `"start"` and `"values"`, and the frequency
    and description when their inclusion flags are enabled.

!!! input "period_from_string"
    A function that reads the start text and accepts a `frequency=` keyword.
    Default: `Period.from_sdmx_string`. It must match the saved period format.

!!! input "frequency_included"
    Whether to read the `"frequency"` key. Default: `True`.
    When disabled, no frequency is supplied to the period parser.

!!! input "description_included"
    Whether to read the `"description"` key. Default: `True`.
    When disabled, the new series has an empty description.

!!! input "allow_multiple_variants"
    Default: `False`. Setting this to `True` raises `NotImplementedError`.

#### Returns

!!! returns "new_series"
    A new Series. An empty start or empty values produces an empty series.
    The usual constructor trimming of missing rows at either end applies.

#### Mutation

Leaves the dictionary unchanged. Arguments after `jsonable` are keyword-only.

#### Details

The inclusion flags must match the dictionary's keys. Some period formats
need a frequency to identify the intended kind of period.

#### See also

`to_jsonable`.
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

