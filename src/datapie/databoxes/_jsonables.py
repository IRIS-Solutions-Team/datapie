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


#-------------------------------------------------------------------------------
# Mixin methods
#-------------------------------------------------------------------------------


class Mixin:
    #[

    @_dm.reference(category="import_export", )
    def series_to_jsonable(self, **kwargs, ) -> dict[str, Any]:
        r"""
................................................................................

## `Databox.series_to_jsonable`

==Turns every time series in the databox into a plain dictionary that can be written out as JSON.==

    jsonable = self.series_to_jsonable(**kwargs)

The collection-level counterpart of `Series.to_jsonable`, which is
called once per series and does the work.

Only time series are converted. Strings, numbers and everything else the
databox holds are dropped without a word, so the result can be smaller
than the databox and a round trip through it loses those entries.


**Input arguments.**


???+ input "**kwargs"
    Passed to `Series.to_jsonable` for every series, so
    `period_to_string`, `include_description` and `include_frequency`
    are set here and set the same way for all of them. Whatever you
    choose has to be matched by the reading side.


One multi-variant series stops the whole databox. `Series.to_jsonable`
raises `ValueError: The series has multiple variants. Set
allow_multiple_variants=True to serialize`, and passing that flag
raises `NotImplementedError` in turn, so there is no way through.


### Returns


A dictionary from series name to the dictionary `Series.to_jsonable`
produced for it. A databox holding no series at all gives `{}`.


### Examples


The entry that is not a series does not survive:

    >>> import numpy as np
    >>> import datapie as dp
    >>> db = dp.Databox()
    >>> db["gdp"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2.]))
    >>> db["note"] = "not a series"
    >>> sorted(db.series_to_jsonable().keys())
    ['gdp']

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

## `Databox.series_to_json_file`

==Writes every time series in the databox to a JSON file.==

    self.series_to_json_file(
        file_name,
        *,
        json_dump_settings=None,
        **kwargs,
    )

`series_to_jsonable` builds the dictionary and the standard `json`
module writes it, so everything that method says applies here too --
in particular that entries which are not time series are dropped.


**Input arguments.**


???+ input "file_name"
    The path to write to, opened as UTF-8 text. An existing file there is
    overwritten without warning.

???+ input "json_dump_settings"
    Passed to `json.dump`. Left as `None` it is `{"indent": 4}`. A
    dictionary you pass **replaces** that default rather than adding to
    it, so `json_dump_settings={"indent": 0}` is how you get compact
    output. Passing an empty dictionary does not: `{}` is falsy, so it
    falls through to the indented default.

???+ input "**kwargs"
    Passed on to `series_to_jsonable`, and from there to
    `Series.to_jsonable` for every series.


Missing observations are written as a bare `NaN`, which is not valid
JSON. Python's own `json` module reads it back without complaint, and
so does `series_from_json_file`, but a strict reader in another
language will reject the file.


### Returns


Nothing.


### Examples


    >>> import json
    >>> import numpy as np
    >>> import datapie as dp
    >>> db = dp.Databox()
    >>> db["gdp"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2.]))
    >>> db.series_to_json_file("gdp.json")
    >>> sorted(json.load(open("gdp.json"))["gdp"])
    ['description', 'frequency', 'start', 'values']

................................................................................
        """
        #[
        jsonable = self.series_to_jsonable(**kwargs, )
        json_dump_settings = json_dump_settings or {"indent": 4, }
        with open(file_name, "wt", encoding="utf-8") as f:
            _js.dump(jsonable, f, **json_dump_settings, )
        #]

    @classmethod
    @_dm.reference(
        category="constructor",
        call_name="Databox.series_from_jsonable",
    )
    def series_from_jsonable(
        klass,
        jsonable: dict[str, Any],
        **kwargs,
    ) -> Self:
        r"""
................................................................................

## `Databox.series_from_jsonable`

==Builds a databox from a dictionary of the kind `series_to_jsonable` produces.==

    self = Databox.series_from_jsonable(jsonable, **kwargs)

A class method: call it on the class, not on a databox you already have.
Every value in `jsonable` is handed to `Series.from_jsonable`, so every
entry becomes a time series -- there is no way to carry anything else
through.


**Input arguments.**


???+ input "jsonable"
    The dictionary to read, laid out the way `series_to_jsonable` writes
    one: series name to the dictionary for that series.

???+ input "**kwargs"
    Passed to `Series.from_jsonable` for every entry, so
    `period_from_string`, `frequency_included` and `description_included`
    are set here and set the same way for all of them.


Those flags have to match the ones used when writing, and they are
spelled differently at the two ends -- `include_frequency` going out
against `frequency_included` coming back. Writing with
`include_frequency=False` and reading with the default raises
`KeyError: 'frequency'`, and the same goes for the description.


### Returns


A new databox holding one time series per entry.


### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> db = dp.Databox()
    >>> db["gdp"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2.]))
    >>> back = dp.Databox.series_from_jsonable(db.series_to_jsonable())
    >>> back["gdp"].same_as(db["gdp"])
    True

................................................................................
        """
        #[
        return klass({
            key: Series.from_jsonable(value, **kwargs, )
            for key, value in jsonable.items()
        })
        #]

    @classmethod
    @_dm.reference(
        category="constructor",
        call_name="Databox.series_from_json_file",
    )
    def series_from_json_file(
        klass,
        file_name: str,
        json_load_settings: dict | None = None,
        **kwargs,
    ) -> Self:
        r"""
................................................................................

## `Databox.series_from_json_file`

==Builds a databox from a JSON file of the kind `series_to_json_file` writes.==

    self = Databox.series_from_json_file(
        file_name,
        json_load_settings=None,
        **kwargs,
    )

A class method: call it on the class, not on a databox you already have.
The standard `json` module reads the file and `series_from_jsonable`
turns it into a databox, so everything that method says applies here
too.


**Input arguments.**


???+ input "file_name"
    The path to read, opened as UTF-8 text. A missing file raises
    `FileNotFoundError`.

???+ input "json_load_settings"
    Passed to `json.load`. Left as `None` it is `{}`. Unlike
    `json_dump_settings` on the writing side, this one is **not**
    keyword-only and can be passed positionally.

???+ input "**kwargs"
    Passed on to `series_from_jsonable`, and from there to
    `Series.from_jsonable` for every entry.


### Returns


A new databox holding one time series per entry in the file.


### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> db = dp.Databox()
    >>> db["gdp"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2.]), description="GDP")
    >>> db.series_to_json_file("db.json")
    >>> back = dp.Databox.series_from_json_file("db.json")
    >>> back["gdp"].same_as(db["gdp"])
    True

................................................................................
        """
        #[
        json_load_settings = json_load_settings or {}
        with open(file_name, "rt", encoding="utf-8") as f:
            jsonable = _js.load(f, **json_load_settings, )
        return klass.series_from_jsonable(jsonable, **kwargs, )
        #]


#-------------------------------------------------------------------------------

