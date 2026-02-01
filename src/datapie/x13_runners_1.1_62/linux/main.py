r"""
Execute X-13ARIMA-SEATS with the given SPC file on Linux systems.
"""


#[

from __future__ import annotations

# Standard library imports
import os
import subprocess as sp

#]


THIS_DIR = os.path.dirname(__file__, )
EXECUTABLE_PATH = os.path.join(THIS_DIR, "x13as_ascii", )


def run(spc_file_without_ext: str, ):
    r"""
    Execute X-13ARIMA-SEATS with the given SPC file on Linux systems.
    """

    # Ensure executable permissions (PyPI strips them)
    os.chmod(EXECUTABLE_PATH, 0o755, )

    return sp.run(
        (EXECUTABLE_PATH, spc_file_without_ext, ),
        text=True,
        stdout=sp.PIPE,
        check=True,
    )


