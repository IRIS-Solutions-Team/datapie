"""
Autoregressive extrapolation
"""


#[

from __future__ import annotations

from typing import (TYPE_CHECKING, )
from numbers import (Number, )
import numpy as _np
import scipy as _sp
import documark as _dm

from ..periods import Period
from ._functionalize import FUNC_STRING

if TYPE_CHECKING:
    from typing import Iterable
    from numbers import Real

#]


#-------------------------------------------------------------------------------
# Mixin methods
#-------------------------------------------------------------------------------


class Mixin:
    #[

    @_dm.reference(category="homogenizing", )
    def extrapolate(
        self: Self,
        ar_coeffs: Iterable[Real],
        span: Iterable[Period],
        *,
        intercept: Real = 0,
        log: bool = False,
    ) -> None:
        r"""
==Generate observations from an autoregressive rule==

#### Syntax

##### Method form

    x.extrapolate(
        ar_coeffs,
        span,
        intercept=0,
        log=False,
    )

##### Function form

    new_series = datapie.extrapolate(
        x,
        ar_coeffs,
        span,
        intercept=0,
        log=False,
    )

#### Input arguments

!!! input "ar_coeffs"
    The autoregressive coefficients in lag order, first lag first. Supply a number for a first-order rule or a sequence for several lags.

!!! input "span"
    The ordered periods receiving generated values. Values already present in these periods are overwritten.

!!! input "intercept"
    The constant added at every step; the default is `0`. This option is keyword-only.

!!! input "log"
    Whether to apply the rule to logarithms and convert the generated values back afterwards. The default is `False`. This option is keyword-only.

#### Returns

!!! returns "None — method form"
    The series is changed in place.

!!! returns "new_series — function form"
    A new series with the result. The input series is unchanged.

??? note "Details"
    Each variant starts from its own observations immediately before the first requested period, using one starting value per coefficient. Missing starting values can produce missing results. An empty series or empty span is unchanged. Missing rows at the ends are removed after assignment.

    Each requested period advances the rule by one step, even if the requested periods are not consecutive. In log mode, starting values need to be positive for real-valued results.
        """
        if self.start is None:
            return
        span = self.resolve_periods(span, )
        if not span:
            return
        num_periods = len(span)
        ar_coeffs = (ar_coeffs, ) if isinstance(ar_coeffs, Number) else ar_coeffs
        order = len(ar_coeffs)
        ar = (1, ) + tuple(-i for i in ar_coeffs)
        start = span[0]
        initial_from_until = (start-order, start-1, )
        iter_initial_data = self.iter_own_data_variants_from_until(initial_from_until, )
        new_data = _np.hstack(tuple(
            _extrapolate_data(
                initial_data, num_periods, ar,
                intercept=intercept,
                log=log,
            )
            for initial_data in iter_initial_data
        ))
        self.set_data(span, new_data, )

    #]


#-------------------------------------------------------------------------------
# Functional forms
#-------------------------------------------------------------------------------


_functional_forms = {"extrapolate", }

for n in _functional_forms:
    code = FUNC_STRING.format(n=n, )
    exec(code, globals(), locals(), )

__all__ = tuple(_functional_forms)


#-------------------------------------------------------------------------------


def _extrapolate_data(
    initial: _np.ndarray,
    num_periods: int,
    ar: Iterable[Real],
    *,
    intercept: Real = 0,
    log: bool = False,
) -> None:
    """
    """
    #[
    initial = _np.flip(initial.flatten(), )
    if log:
        initial = _np.log(initial)
    innovation = _np.full((num_periods, ), intercept, dtype=_np.float64, )
    ma = (1, )
    zi = _sp.signal.lfiltic(ma, ar, initial, )
    out, *_ = _sp.signal.lfilter(ma, ar, innovation, zi=zi, axis=0, )
    if log:
        out = _np.exp(out)
    return out.reshape(-1, 1, )
    #]


