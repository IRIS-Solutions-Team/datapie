r"""
"""


#[

from __future__ import annotations

from dataclasses import dataclass, field, replace

#]


_DEFAULT_COLOR_ORDER = [
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#9467bd",
    "#8c564b",
    "#e377c2",
    "#7f7f7f",
    "#bcbd22",
    "#17becf",
]

_DEFAULT_DASH_ORDER = [
    "solid",
]


@dataclass
class _StyleState:
    color_order: list[str] = field(default_factory=lambda: list(_DEFAULT_COLOR_ORDER))
    dash_order: list[str] = field(default_factory=lambda: list(_DEFAULT_DASH_ORDER))


_STATE = _StyleState()


def get_color_order() -> list[str]:
    """
    Get the current global color order for plots.
    """
    return list(_STATE.color_order)


def set_color_order(order: list[str]) -> None:
    """
    Set the global color order for plots.
    """
    global _STATE
    _STATE = replace(_STATE, color_order=list(order))


def get_dash_order() -> list[str]:
    """
    Get the current global dash order for plots.
    """
    return list(_STATE.dash_order)


def set_dash_order(order: list[str]) -> None:
    """
    Set the global dash order for plots.
    """
    global _STATE
    _STATE = replace(_STATE, dash_order=list(order))


def configure(**kwargs) -> None:
    """
    Batch-set multiple style options at once.

    Parameters
    ----------
    color_order : list[str], optional
        Color order for plots.
    dash_order : list[str], optional
        Dash order for plots.
    """
    global _STATE
    _STATE = replace(_STATE, **kwargs)


def reset() -> None:
    """
    Reset all style settings to their defaults.
    """
    global _STATE
    _STATE = _StyleState()


class temporary:
    r"""
    Context manager for temporary style overrides.
    """

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.saved_state = None

    def __enter__(self):
        global _STATE
        self.saved_state = _STATE
        _STATE = replace(_STATE, **self.kwargs)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        global _STATE
        _STATE = self.saved_state
        return False

