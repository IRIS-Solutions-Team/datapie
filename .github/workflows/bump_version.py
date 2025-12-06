#
# Bump version (mmp) in pyproject.toml
#

import argparse
import toml


_PYPROJECT_PATH = "./pyproject.toml"


def _upgrade_version_string(
    version_string: str,
    bump: str,
) -> str:
    """Bump the major-minor-patch number"""
    def add_one(number: str, ) -> str:
        return str(int(number) + 1)
    mmp = version_string.split(".")
    if bump == "major":
        mmp[0] = add_one(mmp[0], )
        mmp[1] = "0"
        mmp[2] = "0"
    elif bump == "minor":
        mmp[1] = add_one(mmp[1], )
        mmp[2] = "0"
    elif bump == "patch":
        mmp[2] = add_one(mmp[2], )
    else:
        raise ValueError(f"Unknown bump type: {bump}")
    return ".".join(mmp, )


parser = argparse.ArgumentParser()
parser.add_argument("--release-type", required=True, choices=["major", "minor", "patch"], )
args = parser.parse_args()

with open(_PYPROJECT_PATH, "rt", ) as f:
    toml_content = toml.load(f, )

current_version = toml_content["project"]["version"]
new_version = _upgrade_version_string(current_version, args.release_type, )
toml_content["project"]["version"] = new_version

with open(_PYPROJECT_PATH, "wt", ) as f:
    f.write(toml.dumps(toml_content, ), )

