"""
"""


#[

from __future__ import annotations

import numpy as _np
import textwrap as _tw
import documark as _dm

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

    @_dm.reference(
        category=None,
        call_name="Statistical functions of time series",
        call_name_is_code=False,
        priority=20,
    )
    def statistical_functions(self, ) -> None:
        r"""
············································································

==Carries the documentation shared by the statistical functions generated in this file -- `sum`, `mean`, `std`, `cumsum` and the rest.==

    self.statistical_functions()

Calling it does nothing: the body is a single `pass`. It exists only to
carry this overview in the reference documentation.

| Function                 | Computes
|--------------------------|--------------------------------------------
| `sum`, `prod`            | Sum and product
| `mean`, `median`         | Mean and median
| `std`, `var`             | Standard deviation and variance
| `max`, `min`             | Largest and smallest value
| `percentile`, `quantile` | A percentile (0 to 100) or quantile (0 to 1)
| `cumsum`, `cumprod`      | Running sum and running product

`std` and `var` divide by the number of values unless you pass
`ddof=1`. `percentile` and `quantile` need the level, as in
`x.percentile(90)`; it has no default.

Each one has a `nan` twin -- `nansum`, `nanmean`, `nancumsum` and so
on -- that skips missing observations. Without the prefix, one missing
value makes the result missing. Any further argument is handed on to
the numpy function of the same name.

The method form, `x.sum()`, computes **across the variants**, one
period at a time, and changes the series in place, returning `None`. A
series with several variants is left with a single one holding the
statistic for each period, and is then trimmed. On a single-variant
series every function leaves the values as they are, except `std` and
`var`, which turn them all to zero.

The function form, `dp.sum(x)`, does the same on a copy and leaves `x`
alone. It also takes `axis`: left at 1 it behaves as just described,
while `axis=0` computes **over time** instead, once for each variant,
and returns plain numbers -- a list with one per variant, or a single
number for a single-variant series unless you pass
`unpack_singleton=False`. Any other `axis` raises `ValueError`. The
function form takes a time series only.

`cumsum`, `cumprod` and their `nan` twins also run across the variants,
not over time: in each period, the k-th variant becomes the running
total of the first k variants, and the series keeps its shape. Their
function forms accept `axis` but ignore it. For running totals over
time, use `cum_diff`, `cum_roc` and the other temporal cumulation
methods.


### Returns


`None`, and the series is untouched.


### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1), num_variants=2,
    ...     values=np.array([[1., 4.], [np.nan, 8.], [3., 12.]]))

Across the variants, period by period:

    >>> dp.sum(x).get_data()[:, 0].tolist()
    [5.0, nan, 15.0]
    >>> dp.nansum(x).get_data()[:, 0].tolist()
    [5.0, 8.0, 15.0]

Over time, one number per variant:

    >>> dp.nanmean(x, axis=0)
    [2.0, 8.0]

A running total across the variants:

    >>> dp.cumsum(x).get_data().tolist()
    [[1.0, 5.0], [nan, nan], [3.0, 15.0]]

············································································
        """
        pass

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


