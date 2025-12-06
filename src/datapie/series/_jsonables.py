r"""
"""


#[

from __future__ import annotations

import documark as _dm

from ..dates import Period, Frequency

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Self, Callable

#]


def mixin(klass: type, ) -> type:
    r"""
    Inlay the steady state methods in the class
    """
    #[
    klass.to_jsonable = to_jsonable
    klass.from_jsonable = classmethod(from_jsonable, )
    return klass
    #]


#-------------------------------------------------------------------------------
# Functions to be used as methods in Series class
#-------------------------------------------------------------------------------


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
................................................................................

==Convert time series to a JSON-serializable dictionary==

This method converts the time series into a JSON-serializable dictionary format.
It includes options to include or exclude the description and frequency of the
series, as well as handling multiple variants.

    jsonable = self.to_jsonable(
        period_to_string=Period.to_sdmx_string,
        include_description=True,
        include_frequency=True,
        allow_multiple_variants=False,
    )


### Input arguments ###

???+ input "period_to_string"
    Function to convert a Period object to a string; choose from:
    * Period.to_sdmx_string (default): Converts to SDMX format (e.g., "2023-Q1").
    * Period.to_iso_string: Converts to ISO format (e.g., "2023-01-01").
    * custom function taking a Period and returning a string.

???+ input "include_description"
    If `True` (default), the `jsonable` dictionary includes the series
    description.

???+ input "include_frequency"
    If `True` (default), the `jsonable` dictionary includes the series
    frequency; this is recommended for clarity and robustness.

???+ input "allow_multiple_variants"
    Not implemented yet.


### Returns ###

???+ returns "jsonable"
    A dictionary representing the time series in a JSON-serializable format.

................................................................................
    """
    #[
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
    #]


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
................................................................................

==Create time series from a JSON-serializable dictionary==

This class method creates a time series from a JSON-serializable dictionary.

    self = Series.from_jsonable(
        jsonable,
        period_from_string=Period.from_sdmx_string,
        frequency_included=True,
        description_included=True,
        allow_multiple_variants=False,
    )


### Input arguments ###

???+ input "jsonable"
    A dictionary representing the time series in a JSON-serializable format.

???+ input "period_from_string"
    Function to convert a string to a Period object; choose from:
    * Period.from_sdmx_string (default): Parses SDMX format (e.g., "2023-Q1").
    * Period.from_iso_string: Parses ISO format (e.g., "2023-01-01"), needs a `frequency` to be included for non-daily periods.
    * custom function taking a string and a frequency, and returning a Period.

???+ input "frequency_included"
    If `True` (default), the `jsonable` dictionary is expected to include the
    series frequency represented as a single letter.

???+ input "description_included"
    If `True` (default), the `jsonable` dictionary is expected to include the
    series description.

???+ input "allow_multiple_variants"
    Not implemented yet.


### Returns ###

???+ returns "self"
    A time series object created from the `jsonable` dictionary.

................................................................................
    """
    #[
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
        return klass.as_empty(description=description, )
    #
    return klass(
        start=start,
        values=values,
        description=description,
    )
    #]


#-------------------------------------------------------------------------------

