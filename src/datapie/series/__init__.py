r"""
Time series module
"""


from .main import *
from .main import __all__ as all_main

from .functions import *
from .functions import __all__ as all_functions

__all__ = (
    *all_main,
    *all_functions,
)

function_context = {}
for n in all_functions:
    function_context[n] = locals()[n]

del all_main
del all_functions


