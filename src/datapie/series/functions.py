r"""
Create a namespace for functional forms of Series methods
"""


from ._extrapolate import *
from ._extrapolate import __all__ as all_extrapolate

from ._temporal import *
from ._temporal import __all__ as all_temporal

from ._conversions import *
from ._conversions import __all__ as all_conversions

from ._filling import __all__ as all_filling
from ._filling import *

from ._lays import __all__ as all_lays
from ._lays import *

from ._hp import __all__ as all_hp
from ._hp import *

from ._x13 import __all__ as all_x13
from ._x13 import *

from ._timing import *
from ._timing import __all__ as all_timing

from ._moving import *
from ._moving import __all__ as all_moving

from ._uv_filters import *
from ._uv_filters import __all__ as all_uv_filters

from ._ell_one import __all__ as all_ell_one
from ._ell_one import *

from ._statistics import *
from ._statistics import __all__ as all_statistics

from ._elementwise import *
from ._elementwise import __all__ as all_elementwise


__all__ = (
    *all_extrapolate,
    *all_temporal,
    *all_conversions,
    *all_filling,
    *all_lays,
    *all_hp,
    *all_x13,
    *all_timing,
    *all_moving,
    *all_uv_filters,
    *all_ell_one,
    *all_statistics,
    *all_elementwise,
)

del all_extrapolate
del all_temporal
del all_conversions
del all_filling
del all_lays
del all_hp
del all_x13
del all_timing
del all_moving
del all_uv_filters
del all_ell_one
del all_statistics
del all_elementwise

