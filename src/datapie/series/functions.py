r"""
Create a namespace for functional forms of Series methods
"""


#[

from __future__ import annotations

#]

from ._extrapolate import *
from ._extrapolate import __all__ as _all_extrapolate

from ._temporal import *
from ._temporal import __all__ as _all_temporal

from ._conversions import *
from ._conversions import __all__ as _all_conversions

from ._filling import __all__ as _all_filling
from ._filling import *

from ._lays import __all__ as _all_lays
from ._lays import *

from ._hp import __all__ as _all_hp
from ._hp import *

from ._x13 import __all__ as _all_x13
from ._x13 import *

from ._timing import *
from ._timing import __all__ as _all_timing

from ._moving import *
from ._moving import __all__ as _all_moving

from ._ell_one import __all__ as _all_ell_one
from ._ell_one import *

from ._statistics import *
from ._statistics import __all__ as _statistics_all

from ._elementwise import *
from ._elementwise import __all__ as _elementwise_all

__all__ = (
    *_all_extrapolate,
    *_all_temporal,
    *_all_conversions,
    *_all_filling,
    *_all_lays,
    *_all_hp,
    *_all_x13,
    *_all_timing,
    *_all_moving,
    *_all_ell_one,
    *_statistics_all,
    *_elementwise_all,
)

