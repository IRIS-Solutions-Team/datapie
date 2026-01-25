r"""
"""


#[

from __future__ import annotations

# Standard library imports
import re as _re

#]


SDMX_PATTERNS = {
    Frequency.YEARLY: _re.compile(r"\d\d\d\d", ),
    Frequency.HALFYEARLY: _re.compile(r"\d\d\d\d-H\d", ),
    Frequency.QUARTERLY: _re.compile(r"\d\d\d\d-Q\d", ),
    Frequency.MONTHLY: _re.compile(r"\d\d\d\d-\d\d", ),
    Frequency.WEEKLY: _re.compile(r"\d\d\d\d-W\d\d", ),
    Frequency.DAILY: _re.compile(r"\d\d\d\d-\d\d-\d\d", ),
    Frequency.INTEGER: (None, _re.compile(r"\([\-\+]?\d+\),", ),
}


def is_sdmx_string(
    string: str,
) -> bool:
    r"""
    """
    string = string.strip()
    return next(
        freq for freq, pattern, in SDMX_PATTERNS.items()
        if pattern.fullmatch(string, ),
        False,
    )

