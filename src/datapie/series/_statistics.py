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

_AXIS_FROM_ACROSS = {
    "variants": 1,
    "periods": 0,
}


_METHOD_TEMPLATE = r"""
    @_dm.reference(category="statistics", )
    def {n}(
        self: Self,
        *args,
        **kwargs,
    ) -> None:
        r'''
        ==Calculate `{n}` across variants==

        #### See also

        [Statistical reductions](#statistical-reductions) for syntax,
        arguments, return values, and mutation behavior.
        '''
        num_periods = self.data.shape[0]
        self.data = _np.{n}(self.data, *args, axis=1, **kwargs, ).T.reshape(num_periods, -1, )
        self.trim()
    """


_CUM_METHOD_TEMPLATE = r"""
    @_dm.reference(category="statistics", )
    def {n}(
        self: Self,
        *args,
        **kwargs,
    ) -> None:
        r'''
        ==Calculate running `{n}` results across variants==

        #### See also

        [Statistical cumulative operations](#statistical-cumulative-operations)
        for syntax, arguments, return values, and mutation behavior.
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

    _documark_topic__reference_statistical_reductions = r"""
documark = {title = "Statistical reductions", anchor = "statistical-reductions", priority = 150}

==Calculate statistics across variants or periods==

### Syntax

#### Method form

    series.sum()
    series.mean()
    series.std()
    series.percentile(q)
    series.quantile(q)

#### Function form

    new_series = datapie.sum(series, axis=1, unpack_singleton=True)
    new_series = datapie.mean(series, axis=1, unpack_singleton=True)
    new_series = datapie.std(series, axis=1, unpack_singleton=True)
    new_series = datapie.percentile(series, q, axis=1, unpack_singleton=True)
    new_series = datapie.quantile(series, q, axis=1, unpack_singleton=True)
    values = datapie.mean(
        series,
        axis=0,
        unpack_singleton=True,
    )

### Input arguments

!!! input "series"

    The series whose variants or periods are to be compared.

!!! input "*args"

    Additional inputs for the chosen statistic; omitted by default. percentile
    and nanpercentile require q between 0 and 100; quantile and nanquantile
    require q between 0 and 1. q can be one value or a list of values.

!!! input "axis"

    In function forms, 1 compares variants at each period and 0 compares periods
    for each variant. The default is 1. Methods always compare variants.

!!! input "unpack_singleton"

    A function-form option, with default True. With axis=0, a one-item result
    list is returned as that item. This option has no effect with axis=1.

!!! input "**kwargs"

    Options for the chosen NumPy statistic; omitted by default. std and var use
    ddof=0 unless changed, and percentiles and quantiles use method="linear"
    unless changed.

### Returns

!!! returns "None — method form"

    No return value. The series is changed in place.

!!! returns "new_series — function form, axis=1"

    With axis=1, a new Series containing the statistic for each period. The
    input is unchanged.

!!! returns "values — function form, axis=0"

    With axis=0, a scalar or list of values for the variants. Multiple requested
    percentiles or quantiles can give nested lists.

The family includes `sum`, `prod`, `mean`, `median`, `std`, `var`,
`max`, `min`, `percentile` and `quantile`, plus their `nan`-prefixed
forms. Methods calculate a value for each period by comparing variants.
Requesting several percentiles or quantiles gives several result variants.

The `nan`-prefixed forms use NumPy's rules for skipping missing values.
Other forms use its ordinary missing-value rules. Series results lose
rows missing in every variant at either end; scalar and list results do not.

??? note "Details"

    The statistics use the corresponding NumPy functions. Methods use
    `axis=1`, which cannot be overridden through their extra options.
    An explicit NumPy `out` option can write to the supplied array.
    """

    _documark_topic__reference_statistical_cumulative_operations = r"""
documark = {title = "Statistical cumulative operations", anchor = "statistical-cumulative-operations", priority = 140}

==Calculate running sums or products across variants==

### Syntax

#### Method form

    series.cumsum()
    series.cumprod()
    series.nancumsum()
    series.nancumprod()

#### Function form

    new_series = datapie.cumsum(series, axis=1)
    new_series = datapie.cumprod(series, axis=1)
    new_series = datapie.nancumsum(series, axis=1)
    new_series = datapie.nancumprod(series, axis=1)

### Input arguments

!!! input "series"

    The series whose variants are accumulated.

!!! input "*args"

    Additional inputs for the chosen NumPy calculation; omitted by default.

!!! input "axis"

    A function-form option with default 1. Currently ignored: the calculation
    always proceeds across variants, not across time.

!!! input "**kwargs"

    Additional NumPy options; omitted by default. dtype and out use their usual
    defaults of None. A method's axis is fixed and cannot be overridden.

### Returns

!!! returns "None — method form"

    No return value. The series is changed in place.

!!! returns "new_series — function form"

    A new Series containing the result. The input series is left unchanged.

The calculation proceeds from left to right across variants, separately
at each period. It does not run along time. `cumsum` and `cumprod` carry
missing values into later variants. `nancumsum` treats missing values as
zero; `nancumprod` treats them as one. Rows missing in every variant at
either end are removed.

??? note "Details"

    Options are passed to the matching NumPy function. An explicit `out`
    option can write to the supplied array even in a function form.
    """

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


_FUNCTION_TEMPLATE = r"""
    @_dm.reference(category="statistics", )
    def {n}(
        self: Series,
        *args,
        across: AcrossType | None = "variants",
        axis: AxisType | None = None,
        unpack_singleton: bool = True,
        **kwargs,
    ) -> Real | list[Real] | Series:
        r'''
        ==Calculate `{n}` across variants or periods==

        #### See also

        [Statistical reductions](#statistical-reductions).
        '''
        if axis is None:
            axis = _AXIS_FROM_ACROSS[across]
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


_CUM_FUNCTION_TEMPLATE = r"""
    @_dm.reference(category="statistics", )
    def {n}(
        self: Series,
        *args,
        axis: AxisType = 1,
        **kwargs,
    ) -> Self:
        r'''
        ==Return running `{n}` results across variants==

        #### See also

        [Statistical cumulative operations](#statistical-cumulative-operations).
        '''
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


