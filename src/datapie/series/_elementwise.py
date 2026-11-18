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
def {k}(self, *args, **kwargs, ):
    self.data = {v}(self.data, *args, **kwargs, )
"""


class Mixin:
    #[

    @_dm.reference(
        category=None,
        call_name="Elementwise functions of time series",
        call_name_is_code=False,
        priority=20,
    )
    def elementwise_functions(self, ) -> None:
        r"""
············································································

==Carries the documentation shared by the elementwise functions generated in this file -- `log`, `exp`, `sqrt`, `sin`, `maximum` and the rest.==

    self.elementwise_functions()

Calling it does nothing: the body is a single `pass`. It exists only to
carry this overview in the reference documentation.

Each function below comes in two forms. The method form, `x.log()`,
applies the function to every observation of every variant and changes
the series in place, returning `None`. The function form, `dp.log(x)`,
leaves `x` alone and returns a changed copy. Given anything that is not
a time series, such as a number or a numpy array, the function form
hands it straight to the underlying numpy or scipy function.

| Function                   | Computes
|----------------------------|------------------------------------------
| `log`, `log2`, `log10`     | Natural, base-2 and base-10 logarithm
| `log1p`                    | `log(1 + x)`
| `exp`, `exp2`              | `e**x` and `2**x`
| `expm1`                    | `exp(x) - 1`
| `sqrt`                     | Square root
| `abs`                      | Absolute value
| `sign`                     | -1, 0 or 1, following the sign of the value
| `sin`, `cos`, `tan`        | Trigonometric functions, in radians
| `asin`, `acos`, `atan`     | Their inverses
| `expit`, `logistic`        | Logistic function, `1 / (1 + exp(-x))`
| `erf`, `erfc`              | Error function and its complement
| `erfinv`, `erfcinv`        | Their inverses
| `normal_cdf`, `normal_pdf` | Standard normal distribution and density
| `round`                    | Rounding to a number of decimals
| `maximum`, `minimum`       | The larger or smaller of the value and a number

Any further argument is handed on to the underlying function, so
`x.maximum(0)` replaces every negative value with zero.

`abs`, `logistic` and `round` have entries of their own. A time series
defines methods of those names itself, so the method forms that run are
those, and the function forms call them.

Missing observations stay missing. A value outside a function's domain
comes back as `nan` or `inf` -- the logarithm of a negative number is
`nan`, the logarithm of zero is `-inf` -- and the series keeps its span:
nothing is trimmed afterwards, even when every value has become `nan`.


### Returns


`None`, and the series is untouched.


### Examples


The method form works in place:

    >>> import numpy as np
    >>> import datapie as dp
    >>> x = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 4., 9.]))
    >>> x.sqrt()
    >>> x.get_data()[:, 0].tolist()
    [1.0, 2.0, 3.0]

The function form returns a copy and leaves the original alone:

    >>> y = dp.maximum(x, 2.)
    >>> y.get_data()[:, 0].tolist(), x.get_data()[:, 0].tolist()
    ([2.0, 2.0, 3.0], [1.0, 2.0, 3.0])

Given a plain number, it behaves like the numpy function:

    >>> float(dp.sqrt(16.))
    4.0

············································································
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
def {k}(object, *args, **kwargs, ):
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


