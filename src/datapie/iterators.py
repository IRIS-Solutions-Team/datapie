"""
Utility iterators
"""


#[

from __future__ import annotations

import itertools as _it

from collections.abc import Iterable, Iterator
from typing import Any

#]


def exhaust_then_last(
    iterable: Iterable[Any],
    default=None,
) -> Iterator[Any]:
    """
    Repeat the last element of an iterable indefinitely
    """
    last = default
    for item in iterable:
        yield item
        last = item
    while True:
        yield last


def zip_cycles_from(
    start: int,
    *iterables: Iterable[Any],
) -> Iterator[tuple[Any, ...]]:
    r"""
    """
    cycles = (_it.cycle(i) for i in iterables)
    zipped_cycles = zip(*cycles)
    for _ in range(start, ):
        next(zipped_cycles, )
    return zipped_cycles

