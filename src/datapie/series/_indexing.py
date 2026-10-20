"""
Time series indexing inlay
"""


#[

from __future__ import annotations

import textwrap as _tw
import numpy as _np
import documark as _dm

from ._functionalize import FUNC_STRING

#]


#-------------------------------------------------------------------------------
# Mixin methods
#-------------------------------------------------------------------------------


class Mixin:
    #[

    @_dm.reference(
        category="indexing",
        call_name="Series.indexing",
        call_name_is_code=True,
    )
    def indexing(self, /, ) -> None:
        r"""
==Refer to the available indexing forms==

#### Syntax

    series.indexing()

#### Details

This documentation placeholder raises `NotImplementedError` when called.
Use the indexing forms linked below to work with data.

#### See also

[Indexing forms](#indexing-forms).
        """
        raise NotImplementedError


    @staticmethod
    @_dm.topic(title="Indexing forms", anchor="indexing-forms", priority=210)
    def _indexing_forms():
        r"""
==Read or assign observations, or create a shifted or restricted series==

### Syntax

    new_series = series[shift]
    data = series[dates]
    data = series[dates, variants]
    series[dates] = data
    series[dates, variants] = data
    new_series = series(dates)
    new_series = series(dates, variants)

### Input arguments

!!! input "series"

    The series to read or update.

!!! input "shift"

    An integer number of periods. Negative values move a copy later in time;
    positive values move it earlier. The observations do not change.

!!! input "dates"

    A period, span, or collection of periods. `None`, `...`, and `:` select
    the existing span. In the call form, omitting dates also selects the full
    span. For square-bracket selection, put multiple dates in a collection
    rather than using a comma-separated tuple.

!!! input "variants"

    A zero-based column number, collection of numbers, or slice.
    Default: all variants.

!!! input "data"

    Values to assign: a number, NumPy array, tuple, list of variants, or
    another Series. A Series supplies its values at the selected dates.

### Returns

!!! returns "data or new_series"

    Square brackets with dates return an independent two-dimensional NumPy
    array: periods run down rows and variants across columns. Requested
    dates outside the series contain missing values.

    An integer in square brackets returns a shifted copy. Round brackets
    return a new Series with the selected data and data type, but an empty
    description. Missing rows at either end are trimmed.

### Mutation

Assignment changes the original series, extends its span when necessary,
and trims missing rows at either end. Reading, shifting by square brackets,
and selecting with round brackets leave it unchanged.

### See also

`get_data`, `set_data`, `shift`, `reverse_variants`, `reverse_periods`.
        """
        pass

    @_dm.reference(category="indexing", call_name="Series.__getitem__", )
    def __getitem__(
        self,
        index: int | tuple,
    ) -> _np.ndarray:
        r"""
==Return a shifted copy or selected observations==

#### See also

[Indexing forms](#indexing-forms).
        """
        if isinstance(index, int, ):
            # Time shift
            new = self.copy()
            new.shift(index, )
            return new
        else:
            # Extract data
            if isinstance(index, tuple, ):
                dates, variants = index
            else:
                dates, variants = index, None
            return self.get_data(dates, variants, )

    @_dm.reference(category="indexing", call_name="Series.__setitem__", )
    def __setitem__(
        self,
        index: int | tuple,
        data,
    ) -> None:
        r"""
==Assign observations at selected dates and variants==

#### See also

[Indexing forms](#indexing-forms).
        """
        if not isinstance(index, tuple):
            index = (index, None, )
        return self.set_data(index[0], data, index[1], )

    @_dm.reference(category="indexing", call_name="Series.__call__", )
    def __call__(
        self,
        *index,
    ) -> Self:
        r"""
==Create a new Series from selected observations==

#### See also

[Indexing forms](#indexing-forms).
        """
        return self._get_data_and_recreate(*index, )

    @_dm.reference(category="indexing", )
    def reverse_variants(self, ) -> None:
        r"""
==Reverse the order of variants==

#### Syntax

##### Method form

    series.reverse_variants()
    series.reverse_columns()

##### Function form

    new_series = datapie.reverse_variants(
        series,
    )
    new_series = datapie.reverse_columns(
        series,
    )

#### Method form returns

!!! returns "None"
    No return value. The series is changed in place.

#### Function form returns

!!! returns "new_series"
    A new Series with the reversed observations.

#### Mutation

The method reverses the columns in place, without changing dates.
The function form returns a changed copy and leaves the input unchanged.

#### Details

`reverse_columns` is an alias for `reverse_variants`.

#### See also

[Indexing forms](#indexing-forms).
        """
        self.data = self.data[:, ::-1]

    @_dm.reference(category="indexing", )
    def reverse_periods(self, ) -> None:
        r"""
==Reverse observations within the existing dates==

#### Syntax

##### Method form

    series.reverse_periods()
    series.reverse_rows()

##### Function form

    new_series = datapie.reverse_periods(
        series,
    )
    new_series = datapie.reverse_rows(
        series,
    )

#### Method form returns

!!! returns "None"
    No return value. The series is changed in place.

#### Function form returns

!!! returns "new_series"
    A new Series with the reversed observations.

#### Mutation

The method reverses the data rows in place, keeping the start and end
periods unchanged. The function form returns a changed copy and leaves
the input unchanged.

#### Details

`reverse_rows` is an alias for `reverse_periods`.

#### See also

[Indexing forms](#indexing-forms).
        """
        self.data = self.data[::-1, :]

    reverse_columns = reverse_variants
    reverse_rows = reverse_periods

    #]


#---------------------------------------------------------------------------------
# Functional forms
#---------------------------------------------------------------------------------


__all__ = (
    "reverse_variants",
    "reverse_columns",
    "reverse_periods",
    "reverse_rows",
)


for n in __all__:
    code = FUNC_STRING.format(n=n, )
    exec(_tw.dedent(code, ), )


