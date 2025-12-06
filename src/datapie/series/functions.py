r"""
Create a namespace for functional forms of Series methods
"""


#[

from __future__ import annotations

from ._conversions import __all__ as __all__conversions
from ._conversions import *

from ._hp import __all__ as __all__hp
from ._hp import *

from ._extrapolate import __all__ as __all__extrapolate
from ._extrapolate import *

from ._x13 import __all__ as __all__x13
from ._x13 import *

from ._moving import __all__ as __all__moving
from ._moving import *

from ._statistics import __all__ as __all__statistics
from ._statistics import *

from ._elementwise import __all__ as __all__elementwise
from ._elementwise import *

from ._ell_one import __all__ as __all__ell_one
from ._ell_one import *

#]


__all__ = []
__all__.extend(__all__conversions)
__all__.extend(__all__hp)
__all__.extend(__all__extrapolate)
__all__.extend(__all__x13)
__all__.extend(__all__moving)
__all__.extend(__all__statistics)
__all__.extend(__all__elementwise)
__all__.extend(__all__ell_one)


from ._functionalize import FUNC_STRING

from .main import FUNCTIONAL_FORMS as _main_FUNCTIONAL_FORMS
from ._lays import FUNCTIONAL_FORMS as _lays_FUNCTIONAL_FORMS
from ._temporal import FUNCTIONAL_FORMS as _temporal_FUNCTIONAL_FORMS
from ._filling import FUNCTIONAL_FORMS as _filling_FUNCTIONAL_FORMS

FUNCTIONAL_FORMS = []
FUNCTIONAL_FORMS.extend(_main_FUNCTIONAL_FORMS)
FUNCTIONAL_FORMS.extend(_lays_FUNCTIONAL_FORMS)
FUNCTIONAL_FORMS.extend(_temporal_FUNCTIONAL_FORMS)
FUNCTIONAL_FORMS.extend(_filling_FUNCTIONAL_FORMS)

for n in FUNCTIONAL_FORMS:
   code = FUNC_STRING.format(n=n, )
   exec(code, globals(), locals(), )

__all__.extend(FUNCTIONAL_FORMS, )

