r"""
Execute X-13ARIMA-SEATS with the given SPC file on Windows systems.
"""


#[

from __future__ import annotations

# Standard library imports
import os
import functions as ft
import subprocess as sp

#]


THIS_DIR = os.path.dirname(__file__, )
EXECUTABLE_PATH = os.path.join(THIS_DIR, "x13as_ascii.exe", )


def run(spc_file: str, ):
    r"""
    Execute X-13ARIMA-SEATS with the given SPC file on Windows systems.
    """

    return sp.run(
        [EXECUTABLE_PATH, spc_file, ],
        capture_output=True,
        text=True,
        stdout=sp.PIPE,
        check=True,
    )

