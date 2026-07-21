"""
"""


#[

from __future__ import annotations

import numpy as _np
import textwrap as _tw

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Self
    from numbers import Real
    from . import Series, AxisType

#]


_NANABLE_FUNCTIONS = (
    "sum",
    "prod",
    "mean",
    "median",
    "std",
    "var",
    "max",
    "min",
    "percentile",
    "quantile",
)

_NAN_FUNCTIONS = tuple( f"nan{n}" for n in _NANABLE_FUNCTIONS )

_ALL_FUNCTIONS = _NANABLE_FUNCTIONS + _NAN_FUNCTIONS

_NANABLE_CUM_FUNCTIONS = (
    "cumsum",
    "cumprod",
)

_NAN_CUM_FUNCTIONS = tuple( f"nan{n}" for n in _NANABLE_CUM_FUNCTIONS )

_ALL_CUM_FUNCTIONS = _NANABLE_CUM_FUNCTIONS + _NAN_CUM_FUNCTIONS


_METHOD_TEMPLATE = """
    def {n}(
        self: Self,
        *args,
        **kwargs,
    ) -> None:
        r'''
        Function {n}
        '''
        num_periods = self.data.shape[0]
        self.data = _np.{n}(self.data, *args, axis=1, **kwargs, ).T.reshape(num_periods, -1, )
        self.trim()
    """


_CUM_METHOD_TEMPLATE = """
    def {n}(
        self: Self,
        *args,
        **kwargs,
    ) -> None:
        r'''
        Function {n}
        '''
        num_periods = self.data.shape[0]
        self.data = _np.{n}(self.data, *args, axis=1, **kwargs, )
        self.trim()
    """


#-------------------------------------------------------------------------------
# Mixin methods
#-------------------------------------------------------------------------------


class Mixin:
    #[

    for n in _ALL_FUNCTIONS:
        code = _METHOD_TEMPLATE.format(n=n, )
        exec(_tw.dedent(code, ), )

    for n in _ALL_CUM_FUNCTIONS:
        code = _CUM_METHOD_TEMPLATE.format(n=n, )
        exec(_tw.dedent(code, ), )

    #]


#-------------------------------------------------------------------------------
# Functional forms
#-------------------------------------------------------------------------------


_FUNCTION_TEMPLATE = """
    def {n}(
        self: Series,
        *args,
        axis: AxisType = 1,
        unpack_singleton: bool = True,
        **kwargs,
    ) -> Real | list[Real] | Series:
        if axis == 0:
            result = _np.{n}(self.data, *args, axis=0, **kwargs, ).T.tolist()
            if unpack_singleton and len(result) == 1:
                result = result[0]
            return result
        elif axis == 1:
            new = self.copy()
            new.{n}(*args, **kwargs, )
            return new
        else:
            raise ValueError(f'Axis must be 0 or 1; got {{axis}}')
"""


_CUM_FUNCTION_TEMPLATE = """
    def {n}(
        self: Series,
        *args,
        axis: AxisType = 1,
        **kwargs,
    ) -> Self:
        new = self.copy()
        new.{n}(*args, **kwargs, )
        return new
"""


_functional_forms = set(_ALL_FUNCTIONS)

for n in _functional_forms:
    code = _FUNCTION_TEMPLATE.format(n=n, )
    exec(_tw.dedent(code, ), )


_cum_functional_forms = set(_ALL_CUM_FUNCTIONS)

for n in _cum_functional_forms:
    code = _CUM_FUNCTION_TEMPLATE.format(n=n, )
    exec(_tw.dedent(code, ), )


__all__ = tuple(_functional_forms) + tuple(_cum_functional_forms)


