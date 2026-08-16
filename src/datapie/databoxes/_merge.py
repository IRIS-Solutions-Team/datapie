r"""
Merge mixin
"""


#[

from __future__ import annotations

from typing import Literal
import warnings as _wa
import documark as _dm
import functools as _ft

from .. import wrongdoings as _wrongdoings
from ..series import main as _series
from . import main as _databoxes

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Self, Iterable

#]


MergeStrategyType = Literal[
    "stack", # Stack values as variants
    "hstack", # Legacy alias for stack, do not include in the docstring
    "overlay_by_observation",
    "overlay_by_span",
    "underlay_by_observation",
    "underlay_by_span",
    "replace", # Replace the existing value with the new one
    "discard", # Discard the new value and keep the existing one
    "silent", # Exactly the same as discard
    "warning", # Same as discard with a warning
    "error", # Throw an error for the first duplicate key
    "critical", # Throw a critical error for the first duplicate key
]


#-------------------------------------------------------------------------------
# Mixin methods
#-------------------------------------------------------------------------------


class Mixin:
    #[

    @classmethod
    def by_merging(
        klass,
        databoxes: Iterable[Self],
        *args, **kwargs,
    ) -> Self:
        r"""
................................................................................

## `Databox.by_merging`

==Builds a new databox by merging several databoxes together.==

    self = Databox.by_merging(databoxes, strategy="stack")

A class method, and the constructor form of `merge`: it starts from an
empty databox and merges everything into that, so none of the inputs is
modified. Because the first databox is merged into an empty one, its
keys never collide and `strategy` decides only what happens between the
inputs themselves.


**Input arguments.**


???+ input "databoxes"
    The databoxes to merge, as an iterable. A single databox may also be
    passed directly.

???+ input "*args, **kwargs"
    Handed to `merge`, so `strategy` is set here and means exactly what
    it means there.


### Returns


A new databox. None of the inputs is changed.


### Examples


    >>> import datapie as dp
    >>> a = dp.Databox()
    >>> a["x"] = 1
    >>> b = dp.Databox()
    >>> b["x"] = 2
    >>> b["y"] = 3
    >>> c = dp.Databox.by_merging([a, b])
    >>> dict(sorted(c.items()))
    {'x': [1, 2], 'y': 3}
    >>> dict(a)
    {'x': 1}

................................................................................
        """
        self = klass()
        self.merge(databoxes, *args, **kwargs, )
        return self

    @_dm.reference(category="multiple", add_heading=False, )
    def merge(
        self: Self,
        other: Self | Iterable[Self],
        strategy: MergeStrategyType = "stack",
        # Legacy argument
        merge_strategy: MergeStrategyType | None = None,
    ) -> None:
        r"""
................................................................................

## `merge`

==Merges other databoxes into this one, deciding what happens to keys that appear more than once.==

    self.merge(other, strategy="stack")

Keys this databox does not already hold are simply added. Keys it does
hold are handed to `strategy`. `Databox.by_merging` is the form that
builds a new databox instead of changing one.


**Input arguments.**


???+ input "other"
    A databox, or an iterable of them. A single databox may be passed
    directly: anything carrying an `items` method is treated as one
    databox rather than as a sequence of them.

???+ input "strategy"
    What happens to a key that is already present. `"stack"` when left
    alone, and an unrecognised name raises `KeyError` naming it.

    | Strategy | Effect on a duplicate key
    |----------|---------------------------
    | `"stack"` | Combines the two values: time series become variants of one series, lists are extended, and anything else is wrapped in a list first
    | `"replace"` | Takes the new value
    | `"discard"`, `"silent"` | Keeps the existing value
    | `"warning"` | Keeps the existing value and warns, once per duplicate key
    | `"error"` | Raises `wrongdoings.Error` listing the duplicate keys
    | `"critical"` | Raises `wrongdoings.Critical` listing them
    | `"overlay_by_span"`, `"overlay_by_observation"`, `"underlay_by_span"`, `"underlay_by_observation"` | Lays the two series over one another using the `Series` method of that name

    The four laying strategies are the ones to reach for when the second
    databox is meant to fill or override observations rather than add
    variants; `"underlay_by_observation"` in particular fills the gaps in
    this databox's series from the other's. They act only when **both**
    values are time series -- for anything else they leave the existing
    value alone, behaving as `"discard"` without saying so.

???+ input "merge_strategy"
    An older name for `strategy`. Unlike most legacy arguments in this
    package it still works: passing it overrides `strategy`. It issues no
    deprecation warning.


### Returns


Nothing; this databox is modified in place.


### Examples


Stacking turns two values under one key into a list, and a series pair
into a two-variant series:

    >>> import numpy as np
    >>> import datapie as dp
    >>> a = dp.Databox()
    >>> a["x"] = 1
    >>> b = dp.Databox()
    >>> b["x"] = 2
    >>> b["y"] = 3
    >>> a.merge(b)
    >>> dict(sorted(a.items()))
    {'x': [1, 2], 'y': 3}

`"underlay_by_observation"` fills the gap from the other databox and
leaves the observed values alone:

    >>> a = dp.Databox()
    >>> a["s"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2., np.nan, 4.]))
    >>> b = dp.Databox()
    >>> b["s"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([9., 9., 9., 9.]))
    >>> a.merge(b, strategy="underlay_by_observation")
    >>> a["s"].get_data()[:, 0].tolist()
    [1.0, 2.0, 9.0, 4.0]

................................................................................
        """
        if merge_strategy is not None:
            strategy = merge_strategy
        strategy_func = _MERGE_STRATEGY_DISPATCH[strategy]
        stream = _wrongdoings.create_stream(
            strategy,
            "Duplicate keys when merging databoxes",
            when_no_stream="silent",
        )
        if hasattr(other, "items", ):
            other = (other, )
        for t in other:
            for key, value in t.items():
                if key in self:
                    strategy_func(self, key, value, stream, )
                else:
                    self[key] = value
        stream._raise()

    #]


#-------------------------------------------------------------------------------


def _merge_stack(
    self,
    key: str,
    value: Any,
    stream: _wrongdoings.Stream,
) -> None:
    """
    Horizontal stack of values: time series are concatenated, lists are
    extended, non-lists are converted to lists and extended.
    """
    #[
    if isinstance(value, _series.Series, ):
        self[key] = self[key] | value
        return
    if not isinstance(self[key], list):
        self[key] = [self[key], ]
    if not isinstance(value, list):
        value = [value, ]
    self[key] += value
    #]


def _merge_lay(
    self,
    key: str,
    value: Any,
    stream: _wrongdoings.Stream,
    method: str,
) -> None:
    """
    Overlay time series by observation (index), other values are kept unchanged.
    """
    #[
    if isinstance(value, _series.Series, ) and isinstance(self[key], _series.Series, ):
        self[key] = self[key].copy()
        getattr(self[key], method, )(value, )
    #]


def _merge_replace(
    self,
    key: str,
    value: Any,
    stream: _wrongdoings.Stream,
) -> None:
    """
    """
    #[
    self[key] = value
    #]


def _merge_discard(
    self,
    key: str,
    value: Any,
    stream: _wrongdoings.Stream,
) -> None:
    """
    """
    #[
    pass
    #]


def _merge_report(
    self,
    key: str,
    value: Any,
    stream: _wrongdoings.Stream,
) -> None:
    """
    """
    #[
    stream.add(key, )
    #]


_MERGE_STRATEGY_DISPATCH = {
    "stack": _merge_stack,
    "hstack": _merge_stack,
    "overlay_by_observation": _ft.partial(_merge_lay, method="overlay_by_observation", ),
    "overlay_by_span": _ft.partial(_merge_lay, method="overlay_by_span", ),
    "underlay_by_observation": _ft.partial(_merge_lay, method="underlay_by_observation", ),
    "underlay_by_span": _ft.partial(_merge_lay, method="underlay_by_span", ),
    "replace": _merge_replace,
    "discard": _merge_discard,
    "silent": _merge_report,
    "warning": _merge_report,
    "error": _merge_report,
    "critical": _merge_report,
}

