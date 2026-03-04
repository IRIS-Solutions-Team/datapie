r"""
Determine the version of the package.
"""


import tomllib
import pathlib
from importlib.metadata import version, PackageNotFoundError

this_dir = pathlib.Path(__file__).parent
package_name = this_dir.name

try:
    __version__ = version(package_name, )

except PackageNotFoundError:
    # Read pyproject.toml (two levels up) to get the version
    pyproject_path = this_dir.parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        pyproject_data = tomllib.load(f, )
    __version__ = pyproject_data["project"]["version"]

