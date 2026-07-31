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

    # ==========================================================================
    #  ### `to_jsonable(*, period_to_string=Period.to_sdmx_string,
    #   include_description=True, include_frequency=True,
    #   allow_multiple_variants=False)`
    #
    #  Turns a time series into a plain dictionary that can be written out
    #  as JSON.
    #
    #  **Parameters.** Every argument is keyword-only.
    #
    #  `period_to_string` turns the start period into text. Left alone it
    #  writes the SDMX form such as `"2020-Q1"`; `Period.to_iso_string`
    #  writes `"2020-01-01"` instead.
    #
    #  `include_description` and `include_frequency` decide whether those
    #  two keys appear at all. Both are on when left alone.
    #
    #  `allow_multiple_variants` is not implemented. Setting it to `True`
    #  raises `NotImplementedError`.
    #
    #  **Returns.** A dictionary holding `"description"`, `"frequency"`,
    #  `"start"` and `"values"`, the first two only if you asked for them.
    #  `"start"` is `None` for an empty series, and `"values"` is a tuple.
    #
    #  A series holding more than one variant cannot be written at all. The
    #  `ValueError` you get tells you to pass `allow_multiple_variants=True`,
    #  which then raises `NotImplementedError`.
    #
    #  Missing observations are written through unchanged. That is not a
    #  problem here, but `NaN` is not valid JSON, so passing the result to
    #  the standard `json` module -- as `Databox.series_to_json_file`
    #  does -- produces a file that a strict reader will reject.
    #
    #  **Examples.**
    #
    #      >>> import datapie as dp
    #      >>> import numpy as np
    #      >>> x = dp.Series(start=dp.qq(2020, 1), values=np.array([1., 2.]))
    #      >>> x.to_jsonable(include_description=False)
    #      {'frequency': 'Q', 'start': '2020-Q1', 'values': (1.0, 2.0)}
    #
    # ==========================================================================

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

    # ==========================================================================
    #  ### `Series.from_jsonable(jsonable, *,
    #   period_from_string=Period.from_sdmx_string,
    #   frequency_included=True, description_included=True,
    #   allow_multiple_variants=False)`
    #
    #  Builds a time series from a dictionary of the kind `to_jsonable`
    #  produces.
    #
    #  This one is called on the class rather than on a series, as
    #  `Series.from_jsonable(d)`.
    #
    #  **Parameters.** Everything after `jsonable` is keyword-only.
    #
    #  `period_from_string` parses the start period and has to match the
    #  way it was written. Left alone it reads the SDMX form, while
    #  `Period.from_iso_string` reads ISO dates.
    #
    #  `frequency_included` and `description_included` say whether those
    #  keys are there to be read. Both are on when left alone.
    #
    #  `allow_multiple_variants` is not implemented. Setting it to `True`
    #  raises `NotImplementedError`.
    #
    #  **Returns.** A new series. When the stored start or values are
    #  empty you get an empty series instead, and it carries the
    #  description only if `description_included` was left on.
    #
    #  The flags have to match the ones used when writing, and they are
    #  spelled differently at the two ends. Writing with
    #  `include_frequency=False` and reading with the default
    #  `frequency_included=True` raises `KeyError: 'frequency'`, and the
    #  same goes for the description. Reading ISO dates with the default
    #  SDMX parser raises `ValueError`.
    #
    #  **Examples.**
    #
    #      >>> import numpy as np
    #      >>> import datapie as dp
    #      >>> x = dp.Series(start=dp.qq(2020, 1),
    #      ...     values=np.array([1., 2.]), description="GDP")
    #      >>> y = dp.Series.from_jsonable(x.to_jsonable())
    #      >>> y.get_data()[:, 0].tolist()
    #      [1.0, 2.0]
    #      >>> y.get_description()
    #      'GDP'
    #
    # ==========================================================================

        #]

