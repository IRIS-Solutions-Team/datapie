r"""
Execute X-13ARIMA-SEATS with the given SPC file on Darwin (macOS) systems.
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
    Execute X-13ARIMA-SEATS with the given SPC file on Darwin (macOS) systems.
    """

    # Ensure executable permissions (PyPI strips them)
    os.chmod(EXECUTABLE_PATH, 0o755, )

    # Set up environment
    ENVIRON = os.environ.copy()
    ENVIRON["DYLD_LIBRARY_PATH"] = THIS_DIR + ":" + ENVIRON.get("DYLD_LIBRARY_PATH", "")

    return sp.run(
        (EXECUTABLE_PATH, spc_file_without_ext, ),
        env=ENVIRON,
        text=True,
        stdout=sp.PIPE,
        check=True,
    )

