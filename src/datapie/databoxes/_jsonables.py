r"""
"""


#[

from __future__ import annotations

import json as _js
import documark as _dm

from ..series import Series

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Any, Self

#]


def mixin(klass: type, ) -> type:
    r"""
    """
    #[
    klass.series_to_jsonable = series_to_jsonable
    klass.series_to_json_file = series_to_json_file
    klass.series_from_jsonable = classmethod(series_from_jsonable, )
    klass.series_from_json_file = classmethod(series_from_json_file, )
    return klass
    #]


#-------------------------------------------------------------------------------
# Functions to be used as methods in Databox class
#-------------------------------------------------------------------------------


@_dm.reference(category="import_export", )
def series_to_jsonable(self, **kwargs, ) -> dict[str, Any]:
    r"""
................................................................................

==Convert all time series in the databox to a JSON-serializable dictionary==

This method converts all time series contained in the databox into a
JSON-serializable dictionary format.

    jsonable = self.series_to_jsonable(**kwargs, )


### Input arguments ###

???+ input "self"
    The databox object containing the time series to be converted.

???+ input "**kwargs"
    Additional keyword arguments to be passed to the `to_jsonable` method of each
    `Series` object. See the documentation of the `Series.to_jsonable` method in the
    `Series` class for details on the available options.


### Returns ###

???+ returns "jsonable"
    A dictionary where each key is the name of a time series in the databox and
    each value is the JSON-serializable dictionary representation of that time series.

................................................................................
    """
    #[
    return {
        key: value.to_jsonable(**kwargs, )
        for key, value in self.items()
        if isinstance(value, Series, )
    }
    #]


@_dm.reference(category="import_export", )
def series_to_json_file(
    self,
    file_name: str,
    *,
    json_dump_settings: dict | None = None,
    **kwargs,
) -> None:
    r"""
................................................................................

==Save all time series in the databox to a JSON file==

This method saves all time series contained in the databox to a JSON file.

    self.series_to_json_file(
        file_name,
        json_dump_settings=None,
        series_to_jsonable_settings=None,
    )


### Input arguments ###

???+ input "self"
    The databox object containing the time series to be saved.

???+ input "file_name"
    The name of the JSON file to which the time series will be saved.

???+ input "json_dump_settings"
    A dictionary of settings to be passed to the `json.dump` function when
    writing the JSON file. If `None`, default settings will be used alongside
    with `indent=4`.

???+ input "series_to_jsonable_settings"
    A dictionary of settings to be passed to the `series_to_jsonable` method
    of the databox. If `None`, default settings will be used.
    See [the documentation of the `Series.to_jsonable`](time_series.html#to_jsonable).

................................................................................
    """
    #[
    jsonable = self.series_to_jsonable(**kwargs, )
    json_dump_settings = json_dump_settings or {"indent": 4, }
    with open(file_name, "wt", encoding="utf-8") as f:
        _js.dump(jsonable, f, **json_dump_settings, )
    #]


@_dm.reference(
    category="constructor",
    call_name="Databox.seres_from_jsonable",
)
def series_from_jsonable(
    klass,
    jsonable: dict[str, Any],
    **kwargs,
) -> Self:
    r"""
................................................................................

==Create a databox from a JSON-serializable dictionary of time series==

This class method creates a databox from a JSON-serializable dictionary where
each key is the name of a time series and each value is the JSON-serializable
dictionary representation of that time series.

    self = Databox.series_from_jsonable(
        jsonable,
        **kwargs,
    )


### Input arguments ###

???+ input "jsonable"
    A dictionary where each key is the name of a time series and each value is
    the JSON-serializable dictionary representation of that time series.

???+ input "**kwargs"
    Additional keyword arguments to be passed to the `Series.from_jsonable`
    method. See
    [the documentation of the `Series.from_jsonable`](time_series.html#from_jsonable)
    method in the`Series` class for details on the available options.


### Returns ###

???+ returns "self"
    A Databox object containing the time series created from the JSON-serializable
    dictionary.

................................................................................
    """
    #[
    return klass({
        key: Series.from_jsonable(value, **kwargs, )
        for key, value in jsonable.items()
    })
    #]


@_dm.reference(
    category="constructor",
    call_name="Databox.seres_from_json_file",
)
def series_from_json_file(
    klass,
    file_name: str,
    json_load_settings: dict | None = None,
    **kwargs,
) -> Self:
    r"""
................................................................................

==Create a databox from a JSON file of time series==

This class method creates a databox from a JSON file containing a
JSON-serializable dictionary where each key is the name of a time series and
each value is the JSON-serializable dictionary representation of that time series.

    self = Databox.series_from_json_file(
        file_name,
        series_from_jsonable_settings=None,
        json_load_settings=None,
    )


### Input arguments ###

???+ input "file_name"
    The name of the JSON file containing the time series data.

???+ input "series_from_jsonable_settings"
    Additional dictionary with keyword arguments to be passed to the `Series.from_jsonable`
    method. See [the documentation of the `Series.from_jsonable`](time_series.html#from_jsonable).

???+ input "json_load_settings"
    A dictionary of settings to be passed to the `json.load` function when
    reading the JSON file. If `None`, default settings will be used.


### Returns ###

???+ returns "self"
    A Databox object containing the time series created from the JSON file.

................................................................................
    """
    #[
    json_load_settings = json_load_settings or {}
    with open(file_name, "rt", encoding="utf-8") as f:
        jsonable = _js.load(f, **json_load_settings, )
    return klass.series_from_jsonable(jsonable, **kwargs, )
    #]


#-------------------------------------------------------------------------------

