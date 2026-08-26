"""
Databox imports
"""


#[

from __future__ import annotations

from typing import Self
from collections.abc import Iterable, Callable
import csv as _cs
import numpy as _np
import dataclasses as _dc
import pickle as _pickle
import warnings as _wa
import documark as _dm

from ..periods import Period, Span
from ..frequencies import Frequency
from ..series import Series

#]


_DEFAULT_PERIOD_FROM_STRING = Period.from_sdmx_string


@_dc.dataclass
class _ImportBlock:
    """
    """
    #[
    row_index: Iterable[int] | None = None,
    periods: Iterable[Period] | None = None,
    column_start: int | None = None,
    num_columns: int | None = None,
    names: Iterable[str] | None = None,
    descriptions: Iterable[str] | None = None,

    def column_iterator(self, ):
        r"""
        """
        status = False
        names = self.names + [""]
        descriptions = self.descriptions + [""]
        current_columns = None
        current_name = None
        current_description = None
        for i, (n, d) in enumerate(zip(names, descriptions, )):
            if status and n!="*":
                status = False
                yield current_columns, current_name, current_description
            if status and n=="*":
                current_columns.append(i, )
            if not status and n and n!="*":
                status = True
                current_columns = [i]
                current_name = n
                current_description = d
    #]

#-------------------------------------------------------------------------------
# Mixin methods
#-------------------------------------------------------------------------------

class Mixin:
    #[

    @classmethod
    @_dm.reference(
        category="constructor",
        call_name="Databox.from_csv_file",
    )
    def from_csv_file(
        klass,
        file_name: str,
        *,
        period_from_string: Callable | None = None,
            date_creator: Callable | None = None,
        start_period_only: bool = False,
            start_date_only: bool | None = None,
        description_row: bool = False,
        delimiter: str = ",",
        name_row_transform: Callable | None = None,
        csv_reader_settings: dict = {},
        numpy_reader_settings: dict = {},
        databox_settings: dict = {},
    ) -> Self:
        r"""

................................................................................

## `Databox.from_csv_file`

==Creates a new databox by reading time series out of a CSV file written in the layout this package uses.==

    self = Databox.from_csv_file(
        file_name,
        *,
        period_from_string=None,
        date_creator=None,
        start_period_only=False,
        start_date_only=None,
        description_row=False,
        delimiter=",",
        name_row_transform=None,
        csv_reader_settings={},
        numpy_reader_settings={},
        databox_settings={},
    )

This is the counterpart of `to_csv_file`, and it expects that
method's layout: one block of columns per date frequency, each block
opening with a column of periods headed by a frequency mark such as
`__quarterly__`, followed by one column per series headed by its
name. A column headed `*` continues the series to its left as a
further variant. Blocks may sit side by side in the same file.
Columns before the first frequency mark, and columns whose name cell
is empty, are ignored -- which is why the empty separator columns
`to_csv_file` writes do no harm.

This is a class method: call it on the class, as
`Databox.from_csv_file(...)`, not on a databox you already have.


**Input arguments.** Every argument other than `file_name` is
keyword-only.


???+ input "file_name"
    The path to read. It must exist; a missing file raises
    `FileNotFoundError`. The file is read as UTF-8 and a byte-order mark
    at the start is discarded, so a sheet saved by Excel is read without
    trouble.

???+ input "period_from_string"
    Turns the text in a date column into a period. Left alone the text
    is expected in the standard form this package writes -- `2020-Q1`,
    `2020-01`, `(1)`. Your own function is called with the text and a
    `frequency=` keyword argument, so it has to accept that keyword even
    if it ignores it.

???+ input "date_creator"
    The old name of `period_from_string`. It still works and warns that
    it is deprecated.

???+ input "start_period_only"
    Decides how much of the date column is read. Left alone every row's
    date cell is read, and **a row whose date cell is empty is skipped,
    its numbers along with it**. Set it to `True` and only the first
    date is read, each following row counting one period on; no row is
    skipped then, and rows with a blank date keep their values. The same
    file can give you different numbers under the two settings.

???+ input "start_date_only"
    The old name of `start_period_only`. It does nothing at all and does
    not warn, because the check that swaps a legacy value in only fires
    when the new argument is `None`, and `start_period_only` starts at
    `False`.

???+ input "description_row"
    Says whether the file carries a second heading row of descriptions.
    It has to match the file, because nothing checks. A file that has
    one, read without this set, fails inside the period reader with
    `ValueError: not enough values to unpack (expected 2, got 1)`. A
    file that has none, read with it set, quietly loses its first row of
    data: those numbers are taken as the descriptions and the
    observations are gone.

???+ input "delimiter"
    Sets the separator, but only for half the reading. On its own it is
    not enough; see the paragraph after Returns.

???+ input "name_row_transform"
    Applied to every cell of the name row, the frequency marks included,
    so a transform that alters text beginning with `__` will stop the
    blocks being recognised. `str.upper` is safe; something that strips
    leading underscores is not. The row you return is not quite the row
    the block scan works on: a marker of its own is appended afterwards.

???+ input "csv_reader_settings"
    Holds extra arguments for the reader that splits the heading rows. A
    `delimiter` given here has no effect either.

???+ input "numpy_reader_settings"
    Holds extra arguments for the numeric reader, `numpy.genfromtxt`.
    `delimiter`, `skip_header` and `usecols` are already supplied by the
    method, so passing any of them here raises `TypeError`.

???+ input "databox_settings"
    Not settings. It is handed to the `Databox` constructor, and a
    databox is a dictionary, so `databox_settings={"note": 1}` puts an
    entry called `note` into the new databox rather than configuring
    anything.


### Returns


A new `Databox` holding one entry per named column group. A file with
no rows, or with no frequency mark anywhere in its first row, gives an
empty databox rather than an error. Two columns carrying the same name
give one entry, the right-hand one.

A file written with any separator other than a comma cannot be read
by `delimiter` alone. Both readers have to be told: pass
`delimiter=";"` for the numbers and a registered `csv` dialect
through `csv_reader_settings={"dialect": ...}` for the headings.
Without the second, the whole heading line arrives as a single cell
and the read fails while parsing periods.


### Examples


A round trip through a file, descriptions and variants included:

    >>> import numpy as np
    >>> import datapie as dp
    >>> db = dp.Databox()
    >>> db["gdp"] = dp.Series(start=dp.qq(2020,1),
    ...     values=np.array([1., 2.]), description="Output")
    >>> db.to_csv_file("rt.csv", description_row=True)
    >>> back = dp.Databox.from_csv_file("rt.csv", description_row=True)
    >>> back["gdp"].same_as(db["gdp"])
    True

Claiming a description row the file does not have costs you the first
observation:

    >>> rows = "__quarterly__,x,\n2020-Q1,1.0,\n2020-Q2,2.0,\n"
    >>> with open("plain.csv", "w") as fid:
    ...     _ = fid.write(rows)
    >>> odd = dp.Databox.from_csv_file("plain.csv", description_row=True)
    >>> odd["x"].get_data().tolist(), odd["x"].get_description()
    ([[2.0]], '1.0')

................................................................................
        """
        self = klass(**databox_settings, )
        #
        period_from_string = _resolve_legacy_option(
            period_from_string,
            date_creator,
            "The 'date_creator' option is deprecated; use 'period_from_string' instead",
            )
        start_period_only = _resolve_legacy_option(
            start_period_only,
            start_date_only,
            "The 'start_date_only' option is deprecated; use 'start_period_only' instead",
        )
        #
        num_header_rows = 1 + int(description_row)
        csv_rows = _read_csv(file_name, num_header_rows, **csv_reader_settings, )
        if not csv_rows:
            return self
        #
        header_rows = csv_rows[0:num_header_rows]
        data_rows = csv_rows[num_header_rows:]
        name_row = header_rows[0]
        #
        if name_row_transform:
            name_row = _apply_name_row_transform(name_row, name_row_transform, )
        #
        description_row = (
            header_rows[1] if description_row
            else [""] * len(name_row)
        )
        period_from_string = period_from_string or _DEFAULT_PERIOD_FROM_STRING
        #
        for b in _block_iterator(name_row, description_row, data_rows, period_from_string, start_period_only, ):
            array = _read_array_for_block(file_name, b, num_header_rows, delimiter=delimiter, **numpy_reader_settings, )
            _add_series_for_block(self, b, array, )
        #
        return self

    @classmethod
    @_dm.no_reference
    def from_sheet(klass, *args, **kwargs, ):
        r"""
................................................................................

## `Databox.from_sheet`

==Reads a databox from a CSV file, under an older name.==

    self = Databox.from_sheet(*args, **kwargs)

Everything is handed to `from_csv_file` unchanged, so the arguments,
the layout expected of the file and the traps are the ones documented
there. `from_csv` is a third name for the same method.


**Input arguments.**


???+ input "*args, **kwargs"
    Whatever `from_csv_file` takes. Nothing is checked or altered on the
    way through.


### Returns


A new `Databox`, exactly as `from_csv_file` would build it.

................................................................................
        """
        return klass.from_csv_file(*args, **kwargs, )

    # Legacy alias
    from_csv = from_csv_file

    @classmethod
    @_dm.reference(category="import_export", )
    def from_pickle_file(
        klass,
        file_name: str,
        **kwargs,
    ) -> Self:
        r"""
................................................................................

## `Databox.from_pickle_file`

==Reads back a databox written by `to_pickle_file`.==

    self = Databox.from_pickle_file(file_name, **kwargs)

Where a CSV file keeps only the time series and only their numbers,
a pickle file keeps the databox as it stood: descriptions,
multi-variant series, and the entries that are not series at all. Use
it for intermediate results passing between your own scripts.

This is a class method: call it on the class, as
`Databox.from_pickle_file(...)`. It is also available under the
shorter name `Databox.from_pickle`.


**Input arguments.**


???+ input "file_name"
    The path to read, opened in binary mode. A missing file raises
    `FileNotFoundError`.

???+ input "**kwargs"
    Passed to `pickle.load`, where `encoding` is the one occasionally
    needed for files written by very old versions of Python.


### Returns


Whatever the file contains. Nothing checks that it is a databox, so a
pickle holding a list hands you back a list, and the error only shows
up later when you use it as though it were a databox. The `Self`
annotation promises more than the method delivers.

Two things to keep in mind about this format. It stores the classes
along with the values, so a file written by one version of the
package may fail to load into another, which makes it a poor choice
for archiving. And reading one runs code stored inside the file, so
never open a pickle you did not write yourself.


### Examples


A round trip, and what happens when the file holds something else:

    >>> import pickle
    >>> import numpy as np
    >>> import datapie as dp
    >>> db = dp.Databox()
    >>> db["gdp"] = dp.Series(start=dp.qq(2020,1),
    ...     values=np.array([1., 2.]), description="Output")
    >>> db.to_pickle_file("db.pkl")
    >>> dp.Databox.from_pickle_file("db.pkl")["gdp"].same_as(db["gdp"])
    True
    >>> with open("list.pkl", "wb") as fid:
    ...     pickle.dump([1, 2, 3], fid)
    >>> dp.Databox.from_pickle_file("list.pkl")
    [1, 2, 3]

................................................................................
        """
        with open(file_name, "rb") as fid:
            return _pickle.load(fid, **kwargs, )


    from_pickle = from_pickle_file

    #]


#-------------------------------------------------------------------------------


def _read_csv(file_name, num_header_rows, delimiter=",", **kwargs, ):
    """
    Read CSV cells into a list of lists
    """
    #[
    with open(file_name, "rt", encoding="utf-8-sig", ) as fid:
        all_rows = [ line for line in _cs.reader(fid, **kwargs, ) ]
    return all_rows
    #]


def _remove_nonascii_from_start(string, ):
    """
    Remove non-ascii characters from the start of a string
    """
    #[
    while string and not string[0].isascii():
        string = string[1:]
    return string
    #]


def _block_iterator(
    name_row,
    description_row,
    data_rows,
    period_from_string,
    start_period_only,
):
    """
    """
    #[
    def _is_end(cell, ) -> bool:
        return cell.startswith("__")
    #
    def _is_start(cell, ) -> bool:
        if not cell.startswith("__"):
            return False
        try:
            letter = cell.removeprefix("__")[0]
            Frequency.from_letter(letter)
            return True
        except:
            return False
    #
    name_row += ["__"]
    status = False
    blocks = []
    current_date_column = None
    current_start = None
    current_frequency = None
    num_columns = len(name_row)
    for column, cell in enumerate(name_row):
        if status and _is_end(cell):
            status = False
            num_columns = column - current_start
            names = name_row[current_start:column]
            descriptions = description_row[current_start:column]
            row_index, periods = _extract_periods_from_data_rows(
                data_rows,
                current_frequency,
                current_date_column,
                period_from_string,
                start_period_only,
            )
            yield _ImportBlock(row_index, periods, current_start, num_columns, names, descriptions)
        if not status and _is_start(cell):
            status = True
            current_date_column = column
            current_start = column + 1
            current_frequency = Frequency.from_letter(cell)
    #]


def _extract_periods_from_data_rows(
    data_rows,
    frequency: Frequency | None,
    column: int,
    period_from_string: Callable,
    start_period_only: bool,
) -> tuple[tuple[int], tuple[Period]]:
    """
    """
    #[
    start_date = period_from_string(data_rows[0][column], frequency=frequency, )
    date_extractor = {
        True: lambda i, line: start_date + i,
        False: lambda i, line: period_from_string(line[column], frequency=frequency, ),
    }[start_period_only]
    row_indices_and_dates = ( 
        (i, date_extractor(i, line))
        for i, line in enumerate(data_rows)
        if start_period_only or line[column]
    )
    return tuple(zip(*row_indices_and_dates)) or ((), ())
    #]


def _read_array_for_block(file_name, block, num_header_rows, delimiter=",", **kwargs, ):
    #[
    skip_header = num_header_rows
    usecols = [ c for c in range(block.column_start, block.column_start+block.num_columns) ]
    return _np.genfromtxt(file_name, skip_header=skip_header, usecols=usecols, delimiter=delimiter, ndmin=2, **kwargs)
    #]


def _add_series_for_block(self, block, array, ):
    """
    """
    #[
    array = array[block.row_index, :]
    for columns, name, description in block.column_iterator():
        series = Series(num_variants=len(columns), description=description)
        series.set_data(block.periods, array[:, columns])
        self[name] = series
    #]

def _apply_name_row_transform(
    name_row: list[str],
    name_row_transform: Callable,
) -> list[str]:
    """
    """
    return [ name_row_transform(s) for s in name_row ]


def _resolve_legacy_option(
    option,
    legacy,
    warning_message: str,
):
    """
    """
    if (option is None) and (legacy is not None):
        _wa.warn(warning_message, FutureWarning, )
        option = legacy
    return option

