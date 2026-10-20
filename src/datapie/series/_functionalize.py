r"""
"""


FUNC_STRING = """
def {n}(self, *args, **kwargs, ) -> Series:
    r'''
==Apply `{n}` to a copy of a time series==

#### Syntax

    result = datapie.{n}(
        series,
        *args,
        **kwargs,
    )

#### Input arguments

!!! input "series"

    The series to transform.

!!! input "*args, **kwargs"

    The same options as [`Series.{n}`](#{n}).

#### Returns

!!! returns "result"

    A new series, leaving the original unchanged. If the operation also
    produces extra information, it follows the new series in the result.

#### See also

[`Series.{n}`](#{n}).
    '''
    new = self.copy()
    out = new.{n}(*args, **kwargs, )
    if isinstance(out, tuple):
        return new, *out
    elif out is not None:
        return new, out
    else:
        return new
"""

