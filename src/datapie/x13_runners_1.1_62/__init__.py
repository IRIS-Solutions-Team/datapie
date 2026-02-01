r"""
"""


#[

from __future__ import annotations

# Standard library imports
import platform as _pf

# Local imports
from . import windows
from . import darwin
from . import linux

#]


_SYSTEM_RUNNER_DISPATCH = {
    "windows": windows.run,
    "darwin": darwin.run,
    "linux": linux.run,
}

_SYSTEM = _pf.system()
run_x13_executable = _SYSTEM_RUNNER_DISPATCH[_SYSTEM.lower()]

