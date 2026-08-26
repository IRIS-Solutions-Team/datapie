"""
Exporting data to CSV sheets
"""


#[

from __future__ import annotations

from typing import (TYPE_CHECKING, )
import pickle as _pk
import csv as _cs
import numpy as _np
import itertools as _it
import dataclasses as _dc
import functools as _ft
import documark as _dm

from ..periods import Period, EmptySpan
from ..frequencies import Frequency
from .. import wrongdoings as _wrongdoings

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import Any, Callable
    from .main import Databox

#]


_DEFAULT_ROUND = 12
_DEFAULT_DATE_FORMATTER = str
_DESCRIPTION_ROW_HEADING = "__description__"


@_dc.dataclass
class _ExportBlock:
    """
    """
    #[

    databox: Databox | None = None
    frequency: Frequency | None = None
    periods: tuple[Period] | None = None
    names: tuple[str] | None = None
    #
    # Options
    total_num_data_rows: int | None = None
    description_row: bool | None = None
    delimiter: str | None = None
    numeric_format: str | None = None
    nan_str: str | None = None
    round: int | None = None
    date_formatter: Callable | None = None

    def __iter__(self, ):
        """
        """
        def _round(x, /, ):
            if self.round is None:
                return x
            else:
                return _np.round(x, self.round)
        #
        descriptions = _get_descriptions_for_names(self.databox, self.names, )
        num_data_columns = _get_num_data_columns_for_names(self.databox, self.names, )
        data_array = _get_data_array_for_names(self.databox, self.names, self.periods, )
        #
        # Empty row
        empty_row = ("", ) + ("", )*sum(num_data_columns) + ("", )
        #
        # Name row
        name_row = tuple(_it.chain.from_iterable( 
            (n, ) + ("*", )*(num_data_columns[i] - 1)
            for i, n in enumerate(self.names, )
        ))
        yield (_get_frequency_mark(self.frequency), ) + name_row + ("", )
        #
        # Description row
        if self.description_row:
            description_row = tuple(_it.chain.from_iterable( 
                (n, ) + ("*", )*(num_data_columns[i] - 1)
                for i, n in enumerate(descriptions, )
            ))
            yield (_DESCRIPTION_ROW_HEADING, ) + description_row + ("", )
        #
        # Dates and data, row by row
        date_formatter = self.date_formatter or _DEFAULT_DATE_FORMATTER
        for date, data_row in zip(self.periods, data_array, ):
            yield \
                (date_formatter(date, ), ) \
                + tuple(x if not _np.isnan(x) else self.nan_str for x in _round(data_row).tolist()) \
                + ("", )
        #
        # Empty rows afterwards
        for _ in range(self.total_num_data_rows - len(self.periods), ):
            yield empty_row

    #]

#-------------------------------------------------------------------------------
# Mixin methods
#-------------------------------------------------------------------------------

class Mixin:
    #[

    @_dm.reference(category="import_export", )
    def to_csv_file(
        self,
        file_name: str,
        *,
        span: Iterable[Period] | None = None,
        frequency_span: dict | None = None,
        names: Iterable[str] | None = None,
        description_row: bool = False,
        description_heading: str = _DESCRIPTION_ROW_HEADING,
        frequency: Frequency | None = None,
        numeric_format: str = "g",
        nan_str: str = "",
        delimiter: str = ",",
        round: int = _DEFAULT_ROUND,
        date_formatter: Callable | None = None,
        csv_writer_settings: dict | None = {},
        when_empty: Literal["error", "warning", "silent"] = "warning",
        return_info: bool = False,
    ) -> dict[str, Any]:
        r"""


................................................................................

## `Databox.to_csv_file`

==Writes the time series held in a databox to a CSV file, one block of columns per date frequency.==

    self.to_csv_file(
        file_name,
        *,
        span=None,
        frequency_span=None,
        names=None,
        description_row=False,
        description_heading="__description__",
        frequency=None,
        numeric_format="g",
        nan_str="",
        delimiter=",",
        round=12,
        date_formatter=None,
        csv_writer_settings={},
        when_empty="warning",
        return_info=False,
    )

This is the way out of the package and into a spreadsheet or another
program. The file is laid out one block per frequency, side by side.
Each block opens with a column of periods headed by a frequency mark
such as `__quarterly__`, followed by one column per series headed by
its name, and closes with an empty column separating it from the next
block. Blocks covering fewer periods are padded with empty rows so
the columns stay aligned. A series with several variants takes one
column per variant, and the extra columns are headed `*`.

Only time series are written. Strings, numbers, dictionaries and
anything else the databox holds are passed over without a word, and
do not appear in the reported names.


**Input arguments.** Every argument other than `file_name` is
keyword-only.


???+ input "file_name"
    The path to write to. An existing file there is overwritten without
    warning. The directory must already exist; the method does not
    create one, and raises `FileNotFoundError` if it is missing.

???+ input "span"
    Restricts the periods written. It takes precedence over
    `frequency_span`, and it also decides the frequency, which is read
    off its first period -- so giving a span exports that one frequency
    and silently drops every series of any other. An empty `span` raises
    `IndexError: tuple index out of range` before any other check runs.

???+ input "frequency_span"
    Chooses the frequencies and the periods for each, as a dictionary
    from `Frequency` to periods, or to `...` meaning the full span the
    databox holds at that frequency. Left alone every frequency is
    written over its full span. Entries whose value is `None` are
    dropped, and it is ignored entirely when `span` is given.

???+ input "names"
    Chooses which series to write and in what order. Left alone every
    series is written in the order the databox holds them. Names the
    databox does not have are dropped without complaint, so a
    misspelling costs you a column rather than an error.

???+ input "description_row"
    Set to `True` to add a second heading row carrying each series'
    description; series without one get a blank cell.

???+ input "description_heading"
    Does nothing. There is no substitute.

???+ input "frequency"
    Does nothing. Use `frequency_span` or `span` instead.

???+ input "numeric_format"
    Does nothing. There is no substitute.

???+ input "nan_str"
    What a missing observation is written as, an empty string -- so a
    blank cell -- unless you change it.

???+ input "delimiter"
    Separates the columns, a comma unless you change it.

???+ input "round"
    The number of decimal places, and it is **12**, not `None`. Values
    are quietly rounded before they are written unless you pass
    `round=None`, which writes them at full precision.

???+ input "date_formatter"
    Turns a period into the text in the first column of its block. Left
    alone the periods are written in their own standard form: `2020-Q1`
    for quarterly, `2020-01` for monthly, `(1)` for integer-indexed
    series.

???+ input "csv_writer_settings"
    A dictionary of extra arguments for the underlying `csv.writer`,
    such as a quoting rule. `delimiter` and `lineterminator` are already
    supplied by the method, so passing either one here raises
    `TypeError: _csv.writer() got multiple values for keyword argument`.

???+ input "when_empty"
    Decides what happens when there is nothing to write: `"warning"`
    reports it and carries on, `"error"` raises, `"silent"` says
    nothing.

???+ input "return_info"
    Left alone means the method returns nothing. Set it to `True` to get
    the report back.


### Returns


`None`, unless `return_info=True`, in which case a dictionary whose
one key `"names_exported"` holds a tuple of the names actually
written. The `dict[str, Any]` annotation describes only that second
case.

The dangerous case is an export that turns out to have nothing in it.
The file is opened, and therefore truncated, after the check but
whatever the check decided, so with the default `when_empty="warning"`
a databox holding no time series destroys whatever was at `file_name`
and leaves a file of zero length behind. Only `when_empty="error"`
stops before the file is opened. If the target matters, use `"error"`,
or write to a new path.


### Examples


A databox with one series and one entry that is not a series:

    >>> import numpy as np
    >>> import datapie as dp
    >>> db = dp.Databox()
    >>> db["gdp"] = dp.Series(start=dp.qq(2020,1),
    ...     values=np.array([1., 2.]))
    >>> db["note"] = "not a series, and not written"
    >>> db.to_csv_file("out.csv", return_info=True)
    {'names_exported': ('gdp',)}
    >>> open("out.csv").read().splitlines()
    ['__quarterly__,gdp,', '2020-Q1,1.0,', '2020-Q2,2.0,']

Nothing to export still empties the file:

    >>> with open("keep.csv", "w") as fid:
    ...     _ = fid.write("a file you care about")
    >>> dp.Databox().to_csv_file("keep.csv")
    >>> open("keep.csv").read()
    ''

................................................................................
        """
        databox = self.shallow(source_names=names, )
        frequency_span = _resolve_frequency_span(databox, frequency_span, span, )
        frequency_names = _resolve_frequency_names(databox, frequency_span, )
        _catch_empty(frequency_span, frequency_names, when_empty, file_name, )
        #
        total_num_data_rows = _get_total_num_data_rows(frequency_span, )
        export_block_constructor = _ft.partial(
            _ExportBlock,
            databox=databox,
            total_num_data_rows=total_num_data_rows,
            description_row=description_row,
            delimiter=delimiter,
            numeric_format=numeric_format,
            nan_str=nan_str,
            round=round,
            date_formatter=date_formatter,
        )
        export_blocks = (
            export_block_constructor(
                frequency=f,
                periods=frequency_span[f],
                names=frequency_names[f],
            )
            for f in frequency_span.keys()
            if frequency_names[f]
        )
        #
        csv_writer_settings = csv_writer_settings or {}
        with open(file_name, "w+") as fid:
            writer = _cs.writer(fid, delimiter=delimiter, lineterminator="\n", **csv_writer_settings, )
            for row in zip(*export_blocks, ):
                writer.writerow(_it.chain.from_iterable(row))
        #
        info = {
            "names_exported": tuple(_it.chain.from_iterable(frequency_names.values())),
        }
        #
        if return_info:
            return info
        else:
            return


    @_dm.no_reference
    def to_sheet(self, *args, **kwargs, ):
        r"""
................................................................................

## `Databox.to_sheet`


==Writes the databox to a CSV file, under an older name.==

    self.to_sheet(*args, **kwargs)
    
Everything is handed to `to_csv_file` unchanged, so the arguments,
the layout of the file and the traps are the ones documented there.
`to_csv` is a third name for the same method.


**Input arguments.**


???+ input "*args, **kwargs"
    Whatever `to_csv_file` takes. Nothing is checked or altered on the
    way through.


### Returns


Whatever `to_csv_file` returns: `None`, or the report dictionary when
you pass `return_info=True`.

................................................................................
        """
        return self.to_csv_file(*args, **kwargs, )


    # Legacy alias
    to_csv = to_csv_file


    @_dm.reference(category="import_export", )
    def to_pickle_file(
        self,
        file_name: str,
        **kwargs,
    ) -> None:
        r"""
................................................................................

## `Databox.to_pickle_file`


==Writes the whole databox to a file in Python's own binary format.==

    self.to_pickle_file(file_name, **kwargs)

Where `to_csv_file` keeps only the time series, and only their
numbers, this keeps the databox as it stands: descriptions,
multi-variant series, and the entries that are not series at all. It
reads back as a databox equal to the one you saved. Use it to carry
intermediate results between your own scripts, and CSV for anything
another program or another person has to read. This method is also
available under the shorter name `to_pickle`.


**Input arguments.**


???+ input "file_name"
    The path to write to, opened in binary mode. An existing file there
    is overwritten without warning, and the directory must already
    exist.

???+ input "**kwargs"
    Passed to `pickle.dump`. The one worth knowing is `protocol`, which
    lowers the format version so that an older Python can read the file.


### Returns


Nothing.

Two things to keep in mind about this format. It stores the classes
along with the values, so a file written by one version of the
package may fail to load into another, which makes it a poor choice
for archiving. And reading one executes code stored inside it, so
never load a pickle file you did not write yourself.


### Examples


A round trip, description and all:

    >>> import pickle
    >>> import numpy as np
    >>> import datapie as dp
    >>> db = dp.Databox()
    >>> db["gdp"] = dp.Series(start=dp.qq(2020,1),
    ...     values=np.array([1., 2.]), description="Output")
    >>> db.to_pickle_file("db.pkl")
    >>> with open("db.pkl", "rb") as fid:
    ...     back = pickle.load(fid)
    >>> back["gdp"].same_as(db["gdp"])
    True

................................................................................
        """
        with open(file_name, "wb+") as fid:
            _pk.dump(self, fid, **kwargs, )


    to_pickle = to_pickle_file

    #]


#-------------------------------------------------------------------------------


def _get_frequency_mark(frequency, ):
    return "__" + frequency.name.lower() + "__"


def _get_names_to_export(databox, frequency, names, ):
    """
    """
    #[
    names_from_databox = self.get_series_names_by_frequency(frequency)
    names = names_from_databox if names is None else names
    return [n for n in names if n in names_from_databox]
    #]


_DEFAULT_FREQUENCY_SPAN = {
    Frequency.YEARLY: ...,
    Frequency.HALFYEARLY: ...,
    Frequency.QUARTERLY: ...,
    Frequency.MONTHLY: ...,
    Frequency.DAILY: ...,
    Frequency.INTEGER: ...,
    Frequency.UNKNOWN: ...,
}


def _resolve_frequency_span(
    databox: Databox,
    frequency_span: dict[Frequency | int: Iterable[Period]],
    span: Iterable[Period] | None = None,
    /,
) -> tuple[dict[Frequency: tuple[Period]], int]:
    """
    """
    #[
    # Argument span overrides frequency_span
    if span is None:
        frequency_span = (
            frequency_span
            if frequency_span is not None
            else _DEFAULT_FREQUENCY_SPAN
        )
    else:
        span = tuple(span)
        frequency = span[0].frequency
        frequency_span = {frequency: span}
    # Remove Nones, ensure Frequency objects
    frequency_span = {
        Frequency(k): v
        for k, v in frequency_span.items()
        if v is not None
    }
    #
    # Resolve date span for each ...
    frequency_span = {
        k: v if v is not ... else databox.get_span_by_frequency(k, )
        for k, v in frequency_span.items()
    }
    #
    # Expand date spans into tuples, remove empty spans
    frequency_span = {
        k: tuple(i for i in v)
        for k, v in frequency_span.items()
        if v is not EmptySpan() or k is Frequency.UNKNOWN
    }
    #
    return frequency_span
    #]


def _resolve_frequency_names(
    databox: Databox,
    frequency_span: Frequency | None,
    /,
) -> dict[Frequency: tuple[str, ...]]:
    """
    """
    #[
    return {
        k: tuple(databox.get_series_names_by_frequency(k, ))
        for k in frequency_span.keys()
    }


def _get_total_num_data_rows(
    frequency_span: dict[Frequency: tuple[Period]],
    /,
) -> int:
    """
    """
    #
    # Find maximum number of data rows
    return max((len(v) for v in frequency_span.values()), default=0, )


def _get_descriptions_for_names(
    self,
    names: Iterable[str],
    /,
) -> tuple[str, ...]:
    """
    """
    return tuple(self[n].get_description() for n in names)


def _get_num_data_columns_for_names(
    self,
    names: Iterable[str],
    /,
) -> tuple[int, ...]:
    """
    """
    return tuple(self[n].shape[1] for n in names)


def _get_data_array_for_names(
    self,
    names: Iterable[str],
    periods: Iterable[Period],
    /,
) -> _np.ndarray:
    """
    """
    empty_lead = _np.empty((len(periods), 0, ), dtype=_np.float64, )
    return _np.hstack([empty_lead] + [self[n].get_data(periods, ) for n in names], )


def _catch_empty(
    frequency_span: dict[Frequency: tuple[Period]],
    frequency_names: dict[Frequency: tuple[str, ...]],
    when_empty: Literal["error", "warning", "silent"],
    file_name: str,
    /,
) -> None:
    """
    """
    #[
    if not frequency_span or all(len(v) == 0 for v in frequency_names.values()):
        _wrongdoings.raise_as(when_empty, f"No data exported to {file_name}", )
    #]

