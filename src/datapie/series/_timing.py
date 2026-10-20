r"""
"""


#[

from __future__ import annotations

import textwrap as _tw
import documark as _dm

from ._functionalize import FUNC_STRING

#]


#-------------------------------------------------------------------------------
# Mixin methods
#-------------------------------------------------------------------------------


class Mixin:
    #[

    @_dm.reference(category="timing", call_name="Series.shift", )
    def shift(
        self,
        by: ShiftType = -1,
        **kwargs,
    ) -> None:
        r"""
==Move a series in time or use earlier calendar observations==

#### Syntax

##### Method form

    series.shift(
        by=-1,
        **kwargs,
    )

##### Function form

    new_series = datapie.shift(
        series,
        by=-1,
        **kwargs,
    )

#### Input arguments

!!! input "by"
    An integer number of periods or a calendar-shift name. Default: `-1`.
    Negative integers move the series later; positive integers move it earlier,
    without changing its values.

    `"yoy"` moves the series one year later. `"soy"` replaces observations with
    the first observation of their year. `"eopy"` uses the last period of the
    previous year. `"tty"` uses the previous period within the same year.

!!! input "neutral_value"
    A number to use at the first period of each year for `"tty"`.
    Default: `None`, which assigns a missing value. Pass it by keyword through
    `**kwargs`.

!!! input "**kwargs"
    Additional keyword settings forwarded to the selected shift.
    The supplied shifts use only `neutral_value` for `"tty"`.

#### Method form returns

!!! returns "None"
    No return value. The series is changed in place.

#### Function form returns

!!! returns "new_series"
    A new Series with the shift applied.

#### Mutation

The method changes the series in place; the function form leaves its
input unchanged. Integer shifts and `"yoy"` change only dates. Other calendar
shifts replace observations and trim missing rows at either end.

#### Details

Calendar shifts need periods that support the requested calendar operation.
When a source observation is outside the series, the result is missing.

#### See also

`redate`, [Indexing forms](#indexing-forms).
        """
        if isinstance(by, int):
            self._shift_by_number(by, **kwargs, )
        else:
            method_name = f"_shift_{by}"
            getattr(self, method_name)(**kwargs, )

    @_dm.reference(category="timing", call_name="Series.redate", )
    def redate(
        self,
        new_date: Period,
        old_date: Period | None = None,
    ) -> None:
        r"""
==Give observations new dates without changing their values==

#### Syntax

##### Method form

    series.redate(
        new_date,
        old_date=None,
    )

##### Function form

    new_series = datapie.redate(
        series,
        new_date,
        old_date=None,
    )

#### Input arguments

!!! input "new_date"
    The destination Period. When `old_date` is omitted, this becomes
    the new start period.

!!! input "old_date"
    The original Period to move to `new_date`. Default: `None`, the series'
    start. The distance between observations stays unchanged.

#### Method form returns

!!! returns "None"
    No return value. The series is changed in place.

#### Function form returns

!!! returns "new_series"
    A new Series with the revised dates.

#### Mutation

The method changes the start period but keeps all values and the description.
The function form leaves its input unchanged.

#### See also

`shift`.
        """
        if old_date is None:
            self.start = new_date
        else:
            self.start = new_date - (old_date - self.start)

    #]


#-------------------------------------------------------------------------------
# Functional forms
#-------------------------------------------------------------------------------


_functional_forms = {"shift", "redate", }

for n in _functional_forms:
    code = FUNC_STRING.format(n=n, )
    exec(_tw.dedent(code, ), globals(), )

__all__ = tuple(_functional_forms)

