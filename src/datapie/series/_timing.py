r"""
"""


#[

from __future__ import annotations

import textwrap as _tw

from ._functionalize import FUNC_STRING

#]


#-------------------------------------------------------------------------------
# Mixin methods
#-------------------------------------------------------------------------------


class Mixin:
    #[

    def shift(
        self,
        by: ShiftType = -1,
        **kwargs,
    ) -> None:
        r"""
................................................................................

==Shift the time series start date==

Shift the start date of the time series by a number of periods or to a specific
date.

    self.shift(by=-1, )

### Input arguments ###

???+ input "self"
    The current time series object that will be shifted.

???+ input "by"
    The number of periods to shift the observations by. If `by` is a string,
    the observations are manipulated as follows:

    * `"yoy"`: Shift all observations by one year back.

    * `"soy"`: Shift to the start of the year.

    * `"eopy"`: Shift to the end of the previous year.

................................................................................
        """
        if isinstance(by, int):
            self._shift_by_number(by, **kwargs, )
        else:
            method_name = f"_shift_{by}"
            getattr(self, method_name)(**kwargs, )

    def redate(
        self,
        new_date: Period,
        old_date: Period | None = None,
    ) -> None:
        r"""
        """
        if old_data is None:
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

