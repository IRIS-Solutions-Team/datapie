"""
Temporal change functions
"""


#[

from __future__ import annotations

from typing import Self, Callable
from numbers import Real
import numpy as _np
import textwrap as _tw
import documark as _dm

from ..periods import Span
from ._functionalize import FUNC_STRING

#]


#-------------------------------------------------------------------------------
# Mixin methodsFunctions to be mixed in
#-------------------------------------------------------------------------------


class Mixin:
    #[

    _documark_topic__reference_temporal_changes = r"""
documark = {title = "Temporal changes", anchor = "temporal-changes", priority = 200}

==Measure changes between periods==

### Syntax

#### Method form

    series.diff(shift=-1)
    series.diff_log(shift=-1)
    series.pct(shift=-1)
    series.roc(shift=-1)
    series.adiff()
    series.adiff_log()
    series.apct()
    series.aroc()

#### Function form

    new_series = datapie.diff(series, shift=-1)
    new_series = datapie.diff_log(series, shift=-1)
    new_series = datapie.pct(series, shift=-1)
    new_series = datapie.roc(series, shift=-1)
    new_series = datapie.adiff(series)
    new_series = datapie.adiff_log(series)
    new_series = datapie.apct(series)
    new_series = datapie.aroc(series)

### Input arguments

!!! input "series"

    The series whose changes are to be calculated.

!!! input "shift"

    A negative integer or a named reference period; the default is -1, the
    previous period. "yoy" means one year earlier, "soy" the first period of the
    current year, "eopy" the last period of the previous year, and "tty" the
    previous period within the same year. Available on diff, diff_log, pct and
    roc.

### Returns

!!! returns "None — method form"

    No return value. The series is changed in place.

!!! returns "new_series — function form"

    A new Series containing the result. The input series is left unchanged.

Annualized measures always compare with the previous period and use the
series frequency to express the change at a yearly rate. Variants are
processed separately. Missing reference values give missing results;
missing rows at either end are removed.

??? note "Details"

    For current value `x`, reference value `r` and the annualization factor
    `a = series.frequency.value or 1`:

    | Operation | Result |
    |---|---|
    | `diff` | `x - r` |
    | `diff_log` | `log(x) - log(r)` |
    | `pct` | `100*(x/r - 1)` |
    | `roc` | `x/r` |
    | `adiff` | `a*(x - r)` |
    | `adiff_log` | `a*(log(x) - log(r))` |
    | `apct` | `100*((x/r)**a - 1)` |
    | `aroc` | `(x/r)**a` |

    At the first period of a year, `"tty"` uses a reference value of `0`
    for differences and log differences, `1` for gross rates, and a missing
    value for percent changes. Logarithms and division follow NumPy's
    usual rules for missing or invalid values.
    """


    _documark_topic__reference_temporal_change_conversions = r"""
documark = {title = "Temporal change conversions", anchor = "temporal-change-conversions", priority = 180}

==Convert between measures of change==

### Syntax

#### Method form

    series.roc_from_pct()
    series.pct_from_roc()
    series.pct_from_apct()
    series.roc_from_apct()
    series.roc_from_aroc()

#### Function form

    new_series = datapie.roc_from_pct(series)
    new_series = datapie.pct_from_roc(series)
    new_series = datapie.pct_from_apct(series)
    new_series = datapie.roc_from_apct(series)
    new_series = datapie.roc_from_aroc(series)

### Input arguments

!!! input "series"

    The series containing the change measure to convert.

### Returns

!!! returns "None — method form"

    No return value. The series is changed in place.

!!! returns "new_series — function form"

    A new Series containing the result. The input series is left unchanged.

The methods take no additional arguments. They keep the period labels and do not
remove missing rows. The three conversions from annualized measures use
the series frequency to recover a per-period rate.

??? note "Details"

    For input value `x` and `a = series.frequency.value or 1`:

    | Operation | Result |
    |---|---|
    | `roc_from_pct` | `1 + x/100` |
    | `pct_from_roc` | `100*(x - 1)` |
    | `pct_from_apct` | `100*((1 + x/100)**(1/a) - 1)` |
    | `roc_from_apct` | `(1 + x/100)**(1/a)` |
    | `roc_from_aroc` | `x**(1/a)` |
    """


    _documark_topic__reference_temporal_cumulations = r"""
documark = {title = "Temporal cumulations", anchor = "temporal-cumulations", priority = 190}

==Rebuild levels from changes==

### Syntax

#### Method form

    series.cum_diff(shift=-1, initial=None, span=None)
    series.cum_diff_log(shift=-1, initial=None, span=None)
    series.cum_pct(shift=-1, initial=None, span=None)
    series.cum_roc(shift=-1, initial=None, span=None)

#### Function form

    new_series = datapie.cum_diff(series, shift=-1, initial=None, span=None)
    new_series = datapie.cum_diff_log(series, shift=-1, initial=None, span=None)
    new_series = datapie.cum_pct(series, shift=-1, initial=None, span=None)
    new_series = datapie.cum_roc(series, shift=-1, initial=None, span=None)

### Input arguments

!!! input "series"

    The series of changes from which levels are rebuilt.

!!! input "shift"

    A negative integer lag, with default -1. Forward cumulation also accepts
    calendar references supported by the periods, such as "yoy", "soy", "eopy"
    and "tty". Backward cumulation requires an integer lag.

!!! input "initial"

    A starting level, another Series supplying levels by date, or None. The
    default None means 0 for cum_diff and cum_diff_log, and 1 for cum_pct and
    cum_roc. For cum_diff_log, the default zero starting level gives zero levels
    for finite changes.

!!! input "span"

    A Span or None, with default None for the whole series. A forward span
    builds levels forwards; a backward span builds them backwards. In a backward
    span, the requested dates are the levels to recover, using changes from the
    corresponding later dates.

### Returns

!!! returns "None — method form"

    No return value. The series is changed in place.

!!! returns "new_series — function form"

    A new Series containing the result. The input series is left unchanged.

Cumulation replaces the whole data range, rather than keeping observations
outside the chosen span. Initialization can add more than one period:
with a full forward span and a lag of `-k`, it adds `k` preceding periods.
Missing changes carry through to later levels that depend on them.
Missing rows at either end are removed.

??? note "Details"

    Forward cumulation combines the earlier reconstructed level `p` and
    the current change `c` as follows:

    | Operation | New level |
    |---|---|
    | `cum_diff` | `p + c` |
    | `cum_diff_log` | `p*exp(c)` |
    | `cum_pct` | `p*(1 + c/100)` |
    | `cum_roc` | `p*c` |

    Backward cumulation reverses these operations. The reconstruction range
    is filled with `initial` before the requested periods are processed in
    span order. Dates without a calculation keep their initial levels.
    """


    @_dm.reference(category="temporal_change", )
    def temporal_change(
        self,
        by: int | str,
        func: Callable,
        **kwargs,
    ) -> None:
        r"""
==Apply a change calculation to current and reference values==

#### Syntax

    series.temporal_change(
        by,
        func,
        **kwargs,
    )

#### Input arguments

!!! input "by"
    A negative integer lag or a named reference period, as described under
    Temporal changes.

!!! input "func"
    A function taking current and reference values and returning their
    comparison.

!!! input "**kwargs"
    Options passed to the shift. For "tty", neutral_value sets the reference
    value at the first period of a year; the default is None.

#### Returns

!!! returns "None"
    No return value. The series is changed in place.

Missing rows at either end of the result are removed.

#### See also

[Temporal changes](#temporal-changes).
        """
        _catch_invalid_shift(by, )
        other = self.copy()
        other.shift(by, **kwargs, )
        self._binop(other, func, new=self, )



    @_dm.reference(category="temporal_change_conversion", )
    def temporal_change_conversion(self, ):
        r"""
==Leave observations unchanged==

#### See also

[Temporal change conversions](#temporal-change-conversions).
        """
        pass



    @_dm.reference(category="temporal_change", )
    def diff(
        self,
        shift: int | str = -1,
    ) -> None:
        r"""
==Calculate differences in levels==

#### See also

[Temporal changes](#temporal-changes).
        """
        self.temporal_change(shift, lambda x, y: x - y, neutral_value=0, )



    @_dm.reference(category="temporal_change", )
    def adiff(self, ) -> None:
        r"""
==Calculate annualized differences in levels==

#### See also

[Temporal changes](#temporal-changes).
        """
        shift = -1
        factor = self.frequency.value or 1
        self.temporal_change(shift, lambda x, y: factor*(x - y), neutral_value=0, )



    @_dm.reference(category="temporal_change", )
    def diff_log(
        self,
        shift: int | str = -1,
    ) -> None:
        r"""
==Calculate differences in natural logarithms==

#### See also

[Temporal changes](#temporal-changes).
        """
        self.temporal_change(shift, lambda x, y: _np.log(x) - _np.log(y), neutral_value=0, )



    @_dm.reference(category="temporal_change", )
    def adiff_log(self, ) -> None:
        r"""
==Calculate annualized differences in natural logarithms==

#### See also

[Temporal changes](#temporal-changes).
        """
        shift = -1
        factor = self.frequency.value or 1
        self.temporal_change(shift, lambda x, y: factor*(_np.log(x) - _np.log(y)), neutral_value=0, )



    @_dm.reference(category="temporal_change", )
    def roc(
        self,
        shift: int | str = -1,
    ) -> None:
        r"""
==Calculate gross rates of change==

#### See also

[Temporal changes](#temporal-changes).
        """
        self.temporal_change(shift, lambda x, y: x/y, neutral_value=1, )



    @_dm.reference(category="temporal_change", )
    def aroc(
        self,
    ) -> None:
        r"""
==Calculate annualized gross rates of change==

#### See also

[Temporal changes](#temporal-changes).
        """
        shift = -1
        factor = self.frequency.value or 1
        self.temporal_change(shift, lambda x, y: (x/y)**factor, neutral_value=1, )



    @_dm.reference(category="temporal_change", )
    def pct(
        self,
        shift: int | str = -1,
    ) -> None:
        r"""
==Calculate percent changes==

#### See also

[Temporal changes](#temporal-changes).
        """
        self.temporal_change(shift, lambda x, y: 100*(x/y - 1), neutral_value=None, )



    @_dm.reference(category="temporal_change", )
    def apct(
        self,
    ) -> None:
        r"""
==Calculate annualized percent changes==

#### See also

[Temporal changes](#temporal-changes).
        """
        shift = -1
        factor = self.frequency.value or 1
        self.temporal_change(shift, lambda x, y: 100*((x/y)**factor - 1), neutral_value=None, )



    @_dm.reference(category="temporal_change_conversion", )
    def roc_from_pct(
        self,
    ) -> None:
        r"""
==Convert percent changes to gross rates of change==

#### See also

[Temporal change conversions](#temporal-change-conversions).
        """
        self.data = 1 + self.data/100



    @_dm.reference(category="temporal_change_conversion", )
    def pct_from_roc(
        self,
    ) -> None:
        r"""
==Convert gross rates of change to percent changes==

#### See also

[Temporal change conversions](#temporal-change-conversions).
        """
        self.data = 100*(self.data - 1)



    @_dm.reference(category="temporal_change_conversion", )
    def pct_from_apct(
        self,
    ) -> None:
        r"""
==Convert annualized percent changes to per-period percent changes==

#### See also

[Temporal change conversions](#temporal-change-conversions).
        """
        factor = self.frequency.value or 1
        self.data = 100*((1 + self.data/100)**(1/factor) - 1)



    @_dm.reference(category="temporal_change_conversion", )
    def roc_from_apct(
        self,
    ) -> None:
        r"""
==Convert annualized percent changes to per-period gross rates==

#### See also

[Temporal change conversions](#temporal-change-conversions).
        """
        factor = self.frequency.value or 1
        self.data = (1 + self.data/100)**(1/factor)



    @_dm.reference(category="temporal_change_conversion", )
    def roc_from_aroc(
        self,
    ) -> None:
        r"""
==Convert annualized gross rates to per-period gross rates==

#### See also

[Temporal change conversions](#temporal-change-conversions).
        """
        factor = self.frequency.value or 1
        self.data = self.data**(1/factor)



    @_dm.reference(category="temporal_cumulation", )
    def cum_diff(self, *args, **kwargs, ) -> None:
        r"""
==Reconstruct levels from differences==

#### See also

[Temporal cumulations](#temporal-cumulations).
        """
        self.temporal_cumulation("diff", *args, **kwargs, )



    @_dm.reference(category="temporal_cumulation", )
    def cum_diff_log(self, *args, **kwargs, ) -> None:
        r"""
==Reconstruct levels from log differences==

#### See also

[Temporal cumulations](#temporal-cumulations).
        """
        self.temporal_cumulation("diff_log", *args, **kwargs, )



    @_dm.reference(category="temporal_cumulation", )
    def cum_pct(self, *args, **kwargs, ) -> None:
        r"""
==Reconstruct levels from percent changes==

#### See also

[Temporal cumulations](#temporal-cumulations).
        """
        self.temporal_cumulation("pct", *args, **kwargs, )



    @_dm.reference(category="temporal_cumulation", )
    def cum_roc(self, *args, **kwargs, ) -> None:
        r"""
==Reconstruct levels from gross rates of change==

#### See also

[Temporal cumulations](#temporal-cumulations).
        """
        self.temporal_cumulation("roc", *args, **kwargs, )



    @_dm.reference(category="temporal_cumulation", )
    def temporal_cumulation(
        self,
        func_name: str,
        shift: int | str = -1,
        initial: Real | Self | None = None,
        span: Span | None = None,
    ) -> None:
        r"""
==Rebuild levels from a selected measure of change==

#### Syntax

    series.temporal_cumulation(
        func_name,
        shift=-1,
        initial=None,
        span=None,
    )

#### Input arguments

!!! input "func_name"
    One of "diff", "diff_log", "pct" or "roc".

!!! input "shift"
    A negative integer lag, with default -1. Forward cumulation also accepts
    calendar references supported by the periods, such as "yoy", "soy", "eopy"
    and "tty". Backward cumulation requires an integer lag.

!!! input "initial"
    A starting level, another Series supplying levels by date, or None. The
    default None means 0 for "diff" and "diff_log", and 1 for "pct" and "roc".
    For "diff_log", the default zero starting level gives zero levels for finite
    changes.

!!! input "span"
    A Span or None, with default None for the whole series. A forward span
    builds levels forwards; a backward span builds them backwards. In a backward
    span, the requested dates are the levels to recover, using changes from the
    corresponding later dates.

#### Returns

!!! returns "None"
    No return value. The series is changed in place.

The result replaces the original data range. Missing rows at either end
are removed.

#### See also

[Temporal cumulations](#temporal-cumulations).
        """
        _catch_invalid_shift(shift, )
        span = Span(None, None, ) if span is None else span
        span = span.resolve(self, )
        direction = span.direction
        factory = _CUMULATIVE_FACTORY[func_name]
        cum_func = factory[direction]
        initial = factory["initial"] if initial is None else initial
        #
        if direction == "forward":
            _cumulate_forward(self, shift, cum_func, initial, span, )
        #
        elif direction == "backward":
            _cumulate_backward(self, shift, cum_func, initial, span, )


    #]


#-------------------------------------------------------------------------------
# Functional forms
#-------------------------------------------------------------------------------


_functional_forms = {
    # "temporal_change",
    "diff",
    "adiff",
    "diff_log",
    "adiff_log",
    "pct",
    "apct",
    "roc",
    "aroc",
    # "temporal_change_conversion",
    "roc_from_pct",
    "pct_from_roc",
    "pct_from_apct",
    "roc_from_apct",
    "roc_from_aroc",
    # "temporal_cumulation",
    "cum_diff",
    "cum_diff_log",
    "cum_pct",
    "cum_roc",
}

for n in _functional_forms:
    code = FUNC_STRING.format(n=n, )
    exec(_tw.dedent(code, ), )
    globals()[n].__doc__ = getattr(Mixin, n).__doc__


__all__ = tuple(_functional_forms)


#-------------------------------------------------------------------------------


def _cumulate_forward(self, shift, cum_func, initial, span, ) -> None:
    """
    """
    zipped_span = tuple((t, t.shift(shift, )) for t in span)
    zipped_span = tuple((t, sh) for t, sh in zipped_span if sh is not None)
    min_period = min((sh for t, sh in zipped_span), default=span.start_date, )
    initial_span = Span(min_period, span.end_date, )
    change = self.copy()
    self.empty()
    self.set_data(initial_span, initial)
    for t, sh in zipped_span:
        new_data = cum_func(self.get_data(sh, ), change.get_data(t, ), )
        self.set_data(t, new_data)


def _cumulate_backward(self, shift, cum_func, initial, shifted_backward_range, ) -> None:
    """
    """
    orig_range_shifted = Span(self.start_date, self.end_date, -1, )
    orig_range_shifted.shift(shift, )
    shifted_backward_range = shifted_backward_range.resolve(orig_range_shifted, )
    backward_range = shifted_backward_range.copy()
    backward_range.shift(-shift, )
    initial_span = Span(min(shifted_backward_range), backward_range.start_date, )
    orig = self.copy()
    self.empty()
    self.set_data(initial_span, initial, )
    for t, sh in zip(backward_range, shifted_backward_range, ):
        new_data = cum_func(self.get_data(t, ), orig.get_data(t, ), )
        self.set_data(sh, new_data, )



_CUMULATIVE_FACTORY = {
    "diff": {
        "forward": lambda x_past, change_curr: x_past + change_curr,
        "backward": lambda x_future, change_future: x_future - change_future,
        "initial": 0,
    },
    "diff_log": {
        "forward": lambda x_past, change_curr: x_past * _np.exp(change_curr),
        "backward": lambda x_future, change_future: x_future / _np.exp(change_future),
        "initial": 0,
    },
    "pct": {
        "forward": lambda x_past, change_curr: x_past * (1 + change_curr/100),
        "backward": lambda x_future, change_future: x_future / (1 + change_future/100),
        "initial": 1,
    },
    "roc": {
        "forward": lambda x_past, change_curr: x_past * change_curr,
        "backward": lambda x_future, change_future: x_future / change_future,
        "initial": 1,
    },
}


def _catch_invalid_shift(shift: int | str, ):
    """
    """
    if not isinstance(shift, str) and (int(shift) != shift or shift >= 0):
        raise ValueError("Time shift must be a negative integer or a string")


def _roc_from_pct(pct: Real, ) -> Real:
    """
    """
    return 1 + pct/100


