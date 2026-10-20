"""
Methods and functions applied elementwise to Series values
"""


#[

from __future__ import annotations

import numpy as _np
import scipy as _sp
import functools as _ft
import textwrap as _tw
import documark as _dm

#]


_ONE_ARG_FUNCTION_DISPATCH = {
    "log": "_np.log",
    "log2": "_np.log2",
    "log10": "_np.log10",
    "log1p": "_np.log1p",
    "exp": "_np.exp",
    "exp2": "_np.exp2",
    "expm1": "_np.expm1",
    "sqrt": "_np.sqrt",
    "abs": "_np.abs",
    "sign": "_np.sign",
    "sin": "_np.sin",
    "cos": "_np.cos",
    "tan": "_np.tan",
    "asin": "_np.asin",
    "acos": "_np.acos",
    "atan": "_np.atan",
    "expit": "_sp.special.expit",
    "logistic": "_sp.special.expit",
    "erf": "_sp.special.erf",
    "erfinv": "_sp.special.erfinv",
    "erfc": "_sp.special.erfc",
    "erfcinv": "_sp.special.erfcinv",
    "normal_cdf": "_sp.stats.norm.cdf",
    "normal_pdf": "_sp.stats.norm.pdf",
}

_TWO_ARGS_FUNCTION_DISPATCH = {
    "round": "_np.round",
    "maximum": "_np.maximum",
    "minimum": "_np.minimum",
}

ELEMENTWISE_FUNCTION_DISPATCH = {
    **_ONE_ARG_FUNCTION_DISPATCH,
    **_TWO_ARGS_FUNCTION_DISPATCH,
}


#---------------------------------------------------------------------------------
# Mixin methods
#---------------------------------------------------------------------------------


_TEMPLATE = r"""
@_dm.reference(category="elementwise", )
def {k}(self, *args, **kwargs, ):
    r'''
==Apply `{k}` to each observation==

#### See also

[Elementwise functions](#elementwise-functions).
    '''
    self.data = {v}(self.data, *args, **kwargs, )
"""


class Mixin:
    #[

    @staticmethod
    @_dm.topic(title="Elementwise functions", anchor="elementwise-functions", priority=160)
    def _reference_elementwise_functions():
        r"""
==Apply mathematical functions to each observation==

### Syntax

#### Method form

    series.log()
    series.exp()
    series.sqrt()
    series.round(decimals=0)
    series.maximum(other)
    series.minimum(other)

#### Function form

    new_series = datapie.log(series)
    new_series = datapie.exp(series)
    new_series = datapie.sqrt(series)
    new_series = datapie.round(series, decimals=0)
    new_series = datapie.maximum(series, other)
    new_series = datapie.minimum(series, other)

### Input arguments

!!! input "series"

    The series to transform. Function forms also accept a number, array,
    or another object with a matching method.

!!! input "*args"

    Additional inputs for the chosen calculation; omitted by default. maximum
    and minimum need a second value or array. round accepts the number of
    decimal places, with default 0.

!!! input "**kwargs"

    Additional options for the chosen NumPy or SciPy function; omitted by
    default. Options keep their usual defaults.

### Method form returns

!!! returns "None"

    No return value. The series is changed in place.

### Function form returns

!!! returns "new_series"

    For a Series input, a new Series containing the result. The input series is
    unchanged.

!!! returns "values"

    For a scalar or array input, the numerical result. For another object with a
    matching method, a transformed copy of that object.

The methods keep the period labels and do not remove missing rows.
Missing values and values outside a function's range follow the usual
NumPy or SciPy behavior. `maximum` and `minimum` do not match a second
series by period.

The family includes logarithms (`log`, `log2`, `log10`, `log1p`),
exponentials (`exp`, `exp2`, `expm1`), `sqrt`, `abs`, `sign`,
trigonometric functions (`sin`, `cos`, `tan`, `asin`, `acos`, `atan`),
`round`, `maximum`, `minimum`, `expit`, `logistic`, `erf`, `erfinv`,
`erfc`, `erfcinv`, `normal_cdf` and `normal_pdf`. Angles are in radians;
the normal distribution defaults to location `0` and scale `1`.

??? note "Details"

    NumPy supplies the elementary functions. SciPy supplies `expit`,
    `logistic`, the error functions and the normal distribution functions.
    Additional arguments are passed through unchanged. An explicit `out`
    option can write to the supplied array even in a function form.
    The concrete `Series.logistic` method takes no additional arguments.
        """
        pass

    for k, v in ELEMENTWISE_FUNCTION_DISPATCH.items():
        code = _tw.dedent(_TEMPLATE.format(k=k, v=v, ))
        exec(code, globals(), locals(), )

    #]


#---------------------------------------------------------------------------------
# Functional forms
#---------------------------------------------------------------------------------


_TEMPLATE = r"""
@_dm.reference(category="elementwise", )
def {k}(object, *args, **kwargs, ):
    r'''
==Apply `{k}` to each value==

#### Syntax

    result = datapie.{k}(
        object,
        *args,
        **kwargs,
    )

#### Input arguments

!!! input "object"
    A Series, scalar or array to transform. An object with a matching method
    is copied before that method is applied.

!!! input "*args"
    Additional inputs for the chosen calculation; omitted by default.

!!! input "**kwargs"
    Additional options for the chosen calculation; omitted by default.

#### Returns

!!! returns "result"
    A transformed copy for a Series or another object with a matching method.
    For a scalar or array, the numerical result.

#### See also

[Elementwise functions](#elementwise-functions).
    '''
    if hasattr(object, '{k}'):
        new = object.copy()
        new.{k}(*args, **kwargs, )
        return new
    else:
        return {v}(object, *args, **kwargs, )
"""


_functional_forms = set()

for k, v in ELEMENTWISE_FUNCTION_DISPATCH.items():
    code = _tw.dedent(_TEMPLATE.format(k=k, v=v, ))
    exec(code, globals(), locals(), )
    _functional_forms.add(k, )


__all__ = tuple(_functional_forms)


