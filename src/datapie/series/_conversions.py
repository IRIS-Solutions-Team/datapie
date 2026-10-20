r"""
Frequency conversion of time series
"""


#[

from __future__ import annotations

from typing import Self, Callable
from types import EllipsisType
import numpy as _np
import functools as _ft
import textwrap as _tw
import operator as _op
import statistics as _st
import documark as _dm

from . import arip as _arip
from ._functionalize import FUNC_STRING

from ..frequencies import Frequency
from ..periods import Span, Period
from .. import periods as _periods


#]


_builtin_min = min
_builtin_max = max
_builtin_sum = sum


_DEFAULT_METHOD = "mean"
_DEFAULT_DISCARD_MISSING = False


#-------------------------------------------------------------------------------
# Mixin methods
#-------------------------------------------------------------------------------


class Mixin:

    @_dm.reference(category="temporal_change_conversion", )
    def convert_roc(
        self,
        from_freq: Frequency,
        to_freq: Frequency,
    ) -> None:
        r"""
==Convert gross rates of change to another frequency==

#### Syntax

##### Method form

    x.convert_roc(
        from_freq,
        to_freq,
    )

##### Function form

    new_series = datapie.convert_roc(
        x,
        from_freq,
        to_freq,
    )

    new_value = datapie.convert_roc(
        roc,
        from_freq,
        to_freq,
    )

#### Input arguments

!!! input "roc"
    A gross rate of change, where `1` means no change, or a series of gross rates.

!!! input "from_freq"
    The frequency of the supplied changes, expressed as periods per year. Required.

!!! input "to_freq"
    The frequency to convert the changes to, expressed as periods per year. Required and nonzero.

#### Method form returns

!!! returns "None"
    The values are changed in place. Their periods, start and series frequency are unchanged; observations are not resampled.

#### Function form returns

!!! returns "new_series"
    With a series input, return a converted copy. The input is unchanged.

!!! returns "new_value"
    With a number input, return a number. The rate raised to the ratio of source to target frequencies.

Every variant is converted separately, and missing values remain missing. Both frequencies must be supplied explicitly; they are not inferred from the series.

??? note "Details"
    Rates are converted by raising the gross rate to the ratio of source to target frequencies. Percentage changes are converted to gross rates first and back to percentages afterwards. Negative gross rates raised to fractional powers may produce complex scalar results or missing series values.

#### See also

[`convert_pct`](#convert_pct), [`convert_diff`](#convert_diff)
        """
        self.data = self.data.astype(float, copy=False, ) ** (float(from_freq) / float(to_freq))


    @_dm.reference(category="temporal_change_conversion", )
    def convert_pct(
        self,
        from_freq: Frequency,
        to_freq: Frequency,
    ) -> None:
        r"""
==Convert percentage changes to another frequency==

#### Syntax

##### Method form

    x.convert_pct(
        from_freq,
        to_freq,
    )

##### Function form

    new_series = datapie.convert_pct(
        x,
        from_freq,
        to_freq,
    )

    new_value = datapie.convert_pct(
        pct,
        from_freq,
        to_freq,
    )

#### Input arguments

!!! input "pct"
    A percentage change, where `0` means no change, or a series of percentage changes.

!!! input "from_freq"
    The frequency of the supplied changes, expressed as periods per year. Required.

!!! input "to_freq"
    The frequency to convert the changes to, expressed as periods per year. Required and nonzero.

#### Method form returns

!!! returns "None"
    The values are changed in place. Their periods, start and series frequency are unchanged; observations are not resampled.

#### Function form returns

!!! returns "new_series"
    With a series input, return a converted copy. The input is unchanged.

!!! returns "new_value"
    With a number input, return a number. The equivalent percentage change at the target frequency.

Every variant is converted separately, and missing values remain missing. Both frequencies must be supplied explicitly; they are not inferred from the series.

??? note "Details"
    Rates are converted by raising the gross rate to the ratio of source to target frequencies. Percentage changes are converted to gross rates first and back to percentages afterwards. Negative gross rates raised to fractional powers may produce complex scalar results or missing series values.

#### See also

[`convert_roc`](#convert_roc), [`convert_diff`](#convert_diff)
        """
        self.data = 100*((1 + self.data.astype(float, copy=False, )/100) ** (float(from_freq) / float(to_freq)) - 1)


    @_dm.reference(category="temporal_change_conversion", )
    def convert_diff(
        self,
        from_freq: Frequency,
        to_freq: Frequency,
    ) -> None:
        r"""
==Scale additive changes to another frequency==

#### Syntax

##### Method form

    x.convert_diff(
        from_freq,
        to_freq,
    )

##### Function form

    new_series = datapie.convert_diff(
        x,
        from_freq,
        to_freq,
    )

    new_value = datapie.convert_diff(
        diff,
        from_freq,
        to_freq,
    )

#### Input arguments

!!! input "diff"
    An additive change, or a series of additive changes.

!!! input "from_freq"
    The frequency of the supplied changes, expressed as periods per year. Required.

!!! input "to_freq"
    The frequency to convert the changes to, expressed as periods per year. Required and nonzero.

#### Method form returns

!!! returns "None"
    The values are changed in place. Their periods, start and series frequency are unchanged; observations are not resampled.

#### Function form returns

!!! returns "new_series"
    With a series input, return a converted copy. The input is unchanged.

!!! returns "new_value"
    With a number input, return a number. The change multiplied by the ratio of source to target frequencies.

Every variant is converted separately, and missing values remain missing. Both frequencies must be supplied explicitly; they are not inferred from the series.

#### See also

[`convert_roc`](#convert_roc), [`convert_pct`](#convert_pct)
        """
        self.data = self.data.astype(float, copy=False, ) * (float(from_freq) / float(to_freq))

    #[

    @_dm.reference(category="conversion", )
    def aggregate(
        self,
        target_freq: Frequency,
        method: Literal["mean", "sum", "first", "last", "min", "max"] | Callable | None = None,
        discard_missing: bool | None = None,
        select: list[int] | None = None,
        # Do not include the following in the docstring
        remove_missing: bool | None = None, # Legacy
    ) -> None:
        r"""
==Combine observations into lower-frequency values==

#### Syntax

##### Method form

    x.aggregate(
        target_freq,
        method=None,
        discard_missing=None,
        select=None,
    )

##### Function form

    new_series = datapie.aggregate(
        x,
        target_freq,
        method=None,
        discard_missing=None,
        select=None,
    )

#### Input arguments

!!! input "target_freq"
    The lower frequency to use. Passing the current frequency leaves the series unchanged.

!!! input "method"
    How to combine the values in each target period. The default, `None`, means `"mean"`. Accepted names are `"mean"`, `"geometric_mean"`, `"sum"`, `"prod"`, `"first"`, `"last"`, `"min"` and `"max"`. A function may also be supplied; it receives the values for one target period and returns one value.

!!! input "discard_missing"
    Whether to omit missing observations before combining values. The default, `None`, means `False`. A period with no remaining observations is missing.

!!! input "select"
    Optional positions within each target period; the default is `None`, using all values. Selection of several positions is not currently supported reliably.

#### Method form returns

!!! returns "None"
    The series is changed in place.

#### Function form returns

!!! returns "new_series"
    A new series with the result. The input series is unchanged.

??? note "Details"
    Aggregation includes complete calendar years, padding unavailable observations with missing values. Results for partial first or last periods therefore depend on `method` and `discard_missing`. Missing rows at the ends of the result are removed.

#### See also

[`disaggregate`](#disaggregate)
        """
        # Resolve legacy options
        if remove_missing is not None and discard_missing is None:
            discard_missing = remove_missing
        if discard_missing is None:
            discard_missing = _DEFAULT_DISCARD_MISSING
        #
        method = method or _DEFAULT_METHOD
        method_func = (
            _AGGREGATION_METHOD_RESOLUTION[method]
            if isinstance(method, str) else method
        )
        #
        if target_freq == self.frequency:
            return
        if target_freq > self.frequency or target_freq is Frequency.UNKNOWN or self.frequency is Frequency.UNKNOWN:
            raise ValueError(f"Cannot aggregate from {self.frequency} frequency to {target_freq} frequency")
        #
        new_dater_class = _periods.PERIOD_CLASS_FROM_FREQUENCY_RESOLUTION[target_freq]
        #
        aggregate_within_data_func = _ft.partial(
            _aggregate_within_data,
            select,
            discard_missing,
            method_func,
        )
        #
        if self.frequency.is_regular:
            aggregate_func = _aggregate_regular_to_regular
        elif self.frequency is Frequency.DAILY:
            aggregate_func = _aggregate_daily_to_regular
        #
        new_start_date, new_data = aggregate_func(self, new_dater_class, aggregate_within_data_func, )
        self._replace_start_and_values(new_start_date, new_data, )


    @_dm.reference(category="conversion", )
    def disaggregate(
        self,
        target_freq: Frequency,
        #
        method: str = "flat",
        **kwargs,
    ) -> Self:
        r"""
==Spread observations across higher-frequency periods==

#### Syntax

##### Method form

    x.disaggregate(
        target_freq,
        method="flat",
    )

##### Function form

    new_series = datapie.disaggregate(
        x,
        target_freq,
        method="flat",
    )

#### Input arguments

!!! input "target_freq"
    The higher frequency to use. Passing the current frequency leaves the series unchanged.

!!! input "method"
    The default, `"flat"`, repeats each value in every higher-frequency period without dividing it. `"first"`, `"middle"` and `"last"` put the value in one period of each block and leave the others missing. `"arip"` fits a smooth path using autoregressive interpolation.

!!! input "**kwargs"
    Additional options for `"arip"`: `model` is required and `target` is optional, as described below. The other methods take no extra options.

#### Autoregressive interpolation { #disaggregate_arip }

!!! input "model"

    A pair choosing the kind of path and how its higher-frequency values
    combine. Use `"rate"` for growth rates or `"diff"` for additive changes,
    followed by `"sum"`, `"mean"`, `"first"` or `"last"`.

!!! input "target"

    An optional higher-frequency series whose available values are held
    fixed. The default is `None`. The first target variant is used for
    every input variant.

#### Method form returns

!!! returns "None"
    The series is changed in place.

#### Function form returns

!!! returns "new_series"
    A new series with the result. The input series is unchanged.

??? note "Details"
    The repeat and placement methods use a fixed number of higher-frequency periods per observation, rather than variable calendar lengths. For a block with an even number of periods, `"middle"` uses the later of the two central positions. Missing rows at the ends of the result are removed.

#### See also

[`aggregate`](#aggregate)
        """
        method_func = _CHOOSE_DISAGGREGATION_METHOD[method]
        #
        if target_freq == self.frequency:
            return
        #
        if target_freq < self.frequency \
            or target_freq is Frequency.UNKNOWN \
            or self.frequency is Frequency.UNKNOWN:
            #
            raise _wrongdoings.Critical(
                f"Cannot disaggregate from {self.frequency} frequency to {target_freq} frequency"
            )
        #
        new_dater_class = _periods.PERIOD_CLASS_FROM_FREQUENCY_RESOLUTION[target_freq]
        new_start_date, new_data, *_ = method_func(self, new_dater_class, **kwargs, )
        self._replace_start_and_values(new_start_date, new_data, )


    #]


#-------------------------------------------------------------------------------
# Functional forms
#-------------------------------------------------------------------------------


_functional_forms = {
    "convert_roc",
    "convert_pct",
    "convert_diff",
}

for n in ("aggregate", "disaggregate", ):
    code = FUNC_STRING.format(n=n, )
    exec(_tw.dedent(code, ), )
    _functional_forms.add(n, )

__all__ = tuple(_functional_forms)


#-------------------------------------------------------------------------------


def _aggregate_daily_to_regular(
    self,
    new_dater_class: type,
    aggregate_within_data_func: Callable,
) -> Self:
    """
    """
    #[
    start_date = self.start_date.create_soy()
    end_date = self.end_date.create_eoy()
    from_until = (start_date, end_date, )
    start_year = self.start_date.get_year()
    end_year = self.end_date.get_year()
    new_start_date = new_dater_class.from_year_segment(start_year, 1)
    new_end_date = new_dater_class.from_year_segment(end_year, "end")
    get_slice_func = lambda t: slice(
        t.to_daily(position="start", ) - start_date,
        t.to_daily(position="end", ) - start_date + 1,
    )
    new_data = tuple(
        tuple(
            aggregate_within_data_func(data_variant[get_slice_func(t)])
            for data_variant in self.iter_own_data_variants_from_until(from_until, )
        )
        for t in Span(new_start_date, new_end_date)
    )
    #
    new_data = _np.array(new_data, dtype=self.data_type, )
    return new_start_date, new_data
    #]


def _aggregate_regular_to_regular(
    self,
    new_dater_class: type,
    aggregate_within_data_func: Callable,
) -> tuple[Period, _np.ndarray]:
    """
    """
    #[
    start_year = self.start_date.get_year()
    start_date = self.start_date.create_soy()
    end_date = self.end_date.create_eoy()
    new_start_date = new_dater_class.from_year_segment(start_year, 1)
    target_freq = new_dater_class.frequency
    self_data = self.get_data_from_until((start_date, end_date))
    factor = self.frequency.value // target_freq
    #
    # Loop over variants, create within-period data, and aggregate
    multi_output_data_transposed = []
    for data_variant in self_data.T:
        output_data_transposed = tuple(
            aggregate_within_data_func(within_data)
            for within_data in data_variant.reshape((-1, factor), )
        )
        multi_output_data_transposed.append(output_data_transposed, )
    #
    multi_output_data = _np.array(multi_output_data_transposed, dtype=self.data_type, ).T
    return new_start_date, multi_output_data
    #]


def _disaggregate_flat(
    self,
    high_dater_class: type,
) -> tuple[Period, _np.ndarray]:
    """
    """
    #[
    high_freq = high_dater_class.frequency
    high_start_date = high_dater_class.from_ymd(*self.start_date.to_ymd(position="start", ), )
    factor = high_freq.value // self.frequency.value
    high_data = _np.repeat(self.data, factor, axis=0, )
    return high_start_date, high_data, factor
    #]


def _disaggregate_first(
    self,
    high_dater_class: type,
) -> tuple[Period, _np.ndarray]:
    """
    """
    #[
    high_start_date, flat_high_data, factor = _disaggregate_flat(self, high_dater_class, )
    high_data = _np.full(flat_high_data.shape, None, dtype=self.data_type, )
    high_data[::factor, :] = flat_high_data[::factor, :]
    return high_start_date, high_data, factor
    #]


def _disaggregate_middle(
    self,
    high_dater_class: type,
) -> tuple[Period, _np.ndarray]:
    """
    """
    #[
    high_start_date, flat_high_data, factor = _disaggregate_flat(self, high_dater_class, )
    high_data = _np.full(flat_high_data.shape, None, dtype=self.data_type, )
    high_data[factor//2::factor, :] = flat_high_data[factor//2::factor, :]
    return high_start_date, high_data, factor,
    #]


def _disaggregate_last(
    self,
    high_dater_class: type,
) -> tuple[Period, _np.ndarray]:
    """
    """
    #[
    high_start_date, flat_high_data, factor = _disaggregate_flat(self, high_dater_class, )
    high_data = _np.full(flat_high_data.shape, None, dtype=self.data_type, )
    high_data[factor-1::factor, :] = flat_high_data[factor-1::factor, :]
    return high_start_date, high_data, factor
    #]


def _aggregate_within_data(
    select: list[int] | None,
    discard_missing: bool,
    method_func: Callable,
    within_data: _np.ndarray,
) -> _np.ndarray:
    """
    """
    #[
    if select is not None:
        select = tuple(select)
        within_data = within_data[select]
    if discard_missing:
        within_data = within_data[~_np.isnan(within_data)]
    return method_func(within_data) if within_data.size > 0 else _np.nan
    #]


_AGGREGATION_METHOD_RESOLUTION = {
    "mean": _st.mean,
    "geometric_mean": _st.geometric_mean,
    "sum": _builtin_sum,
    "prod": _np.prod,
    "first": _op.itemgetter(0),
    "last": _op.itemgetter(-1),
    "min": _builtin_min,
    "max": _builtin_max,
}


_CHOOSE_DISAGGREGATION_METHOD = {
    "flat": _disaggregate_flat,
    "first": _disaggregate_first,
    "middle": _disaggregate_middle,
    "last": _disaggregate_last,
    "arip": _arip.disaggregate_arip,
}


@_dm.reference(category="temporal_change_conversion", )
def convert_roc(
    roc: Real,
    from_freq: Frequency,
    to_freq: Frequency,
) -> Real:
    r"""
==Convert gross rates of change to another frequency==

#### See also

[`Series.convert_roc`](#convert_roc) for method, series-input and scalar-input forms.
    """
    if hasattr(roc, "convert_roc"):
        new = roc.copy()
        new.convert_roc(from_freq, to_freq, )
        return new
    return float(roc) ** (float(from_freq) / float(to_freq))


@_dm.reference(category="temporal_change_conversion", )
def convert_pct(
    pct: Real,
    from_freq: Frequency,
    to_freq: Frequency,
) -> Real:
    r"""
==Convert percentage changes to another frequency==

#### See also

[`Series.convert_pct`](#convert_pct) for method, series-input and scalar-input forms.
    """
    if hasattr(pct, "convert_pct"):
        new = pct.copy()
        new.convert_pct(from_freq, to_freq, )
        return new
    return 100*(convert_roc(1 + float(pct)/100, from_freq, to_freq) - 1)


@_dm.reference(category="temporal_change_conversion", )
def convert_diff(
    diff: Real,
    from_freq: Frequency,
    to_freq: Frequency,
) -> Real:
    r"""
==Scale additive changes to another frequency==

#### See also

[`Series.convert_diff`](#convert_diff) for method, series-input and scalar-input forms.
    """
    if hasattr(diff, "convert_diff"):
        new = diff.copy()
        new.convert_diff(from_freq, to_freq, )
        return new
    return float(diff) * (float(from_freq) / float(to_freq))

