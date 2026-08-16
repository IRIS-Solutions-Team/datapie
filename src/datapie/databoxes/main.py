"""
Data management tools for storing and manipulating unstructured data
"""


#[

from __future__ import annotations

from typing import Self, TypeAlias, Literal, Sequence, Protocol, Any, NoReturn
from collections.abc import Iterable, Iterator, Callable
from numbers import Number
import json as _js
import copy as _co
import types as _ty
import numpy as _np
import re as _re
import operator as _op
import itertools as _it
import os as _os
import documark as _dm

from .. import iterators as _iterators
from ..series import Series
from .. import series as _series
from ..periods import Period, Span, EmptySpan
from ..frequencies import Frequency
from .. import periods as _periods
from .. import wrongdoings as _wrongdoings

from .. import descriptions as _descriptions

from . import _merge
from . import _imports
from . import _exports
from . import _views
from . import _jsonables

#]


SourceNames: TypeAlias = Iterable[str] | str | Callable[[str], bool] | None
TargetNames: TypeAlias = Iterable[str] | str | Callable[[str], str] | None
InterpretRange: TypeAlias = Literal["base", "extended", ]


class SteadyDataboxableProtocol(Protocol):
    """
    """
    #[

    max_lag: int
    max_lead: int
    def generate_steady_items(self, *args) -> Any: ...

    #]


@_dm.reference(
    path=("data_management", "databoxes.md", ),
    categories={
        "constructor": "Creating a new Databox",
        "copying": "Copying and converting a Databox",
        "api": "Acquiring data via third-party APIs",
        "information": "Getting information about a Databox",
        "manipulation": "Manipulating a Databox",
        "evaluation": "Evaluating a Databox",
        "multiple": "Manipulating multiple Databoxes",
        "retrieval": "Extracting data from a Databox",
        "import_export": "Importing and exporting a Databox",
    },
)
class Databox(
    _merge.Mixin,
    _exports.Mixin,
    _imports.Mixin,
    _jsonables.Mixin,
    _views.Mixin,
    _descriptions.Mixin,
    dict,
):
    r"""
................................................................................

Databoxes
==========

`Databoxes` extend the standard `dict` class (technically, they are a
subclass), serving as a universal tool for storing and manipulating
unstructured data organized as key-value pairs. The values stored within
`Databoxes` can be of any type.

`Databoxes` can use any methods implemented for the standard `dict`
objects, and have additional functionalities for data item manipulation,
batch processing, importing and exporting data, and more.

................................................................................
    """
    #[

    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        """
        """
        super().__init__(*args, **kwargs, )
        self._description = ""

    @classmethod
    @_dm.reference(
        category="constructor",
        call_name="Databox.empty",
        add_heading=False,
    )
    def empty(klass, ) -> Self:
        """
················································································

## `Databox.empty`

==Creates a new, empty Databox.==

    self = Databox.empty()

A class method taking no arguments, and the same thing as `Databox()`.


### Returns


A new Databox holding nothing.


### Examples


    >>> import datapie as dp
    >>> dict(dp.Databox.empty())
    {}

················································································
        """
        return klass()

    @classmethod
    @_dm.reference(category="constructor", call_name="Databox.from_dict", add_heading=False, )
    def from_dict(
        klass,
        _dict: dict,
    ) -> Self:
        """
················································································

## `Databox.from_dict`

==Creates a new Databox holding the contents of a plain dictionary.==

    self = Databox.from_dict(_dict)

A class method. The entries are copied across one by one, so the
dictionary itself is not kept and later changes to it do not reach the
Databox; the values, however, are the same objects.


**Input arguments.**


???+ input "_dict"
    The dictionary to read. Each key-value pair becomes one item in the
    new Databox.


### Returns


A new Databox holding the same items.


### Examples


    >>> import datapie as dp
    >>> db = dp.Databox.from_dict({"a": 1, "b": 2})
    >>> dict(sorted(db.items()))
    {'a': 1, 'b': 2}

················································································
        """
        self = klass()
        for k, v in _dict.items():
            self[k] = v
        return self

    @classmethod
    @_dm.reference(category="constructor", call_name="Databox.from_array", add_heading=False, )
    def from_array(
        klass,
        array: _np.ndarray,
        names: Sequence[str],
        *,
        descriptions: Iterable[str] | None = None,
        periods: Iterable[Period] | None = None,
        start: Period | None = None,
        target_db: Self | None = None,
        orientation: Literal["vertical", "horizontal", ] = "vertical",
    ) -> Self:
        """
················································································

## `Databox.from_array`

==Creates a new Databox with one time series per row or column of a numpy array.==

**This method does not currently work, and everything below describes what it
is meant to do rather than what it does.** The helper it delegates to,
`_from_horizontal_array_and_constructor`, has its assignment line commented out
and a debug `print` left in its place, so the call prints one line per name to
standard output and creates no series at all. It returns an empty `Databox`, or
`target_db` unchanged when one is given. Nothing in the package calls it.

Convert a two-dimensional [numpy](https://numpy.org) array data into a
Databox, with the individual time series created from the rows or columns
of the numeric array.

    self = Databox.from_array(
        array,
        names,
        *,
        descriptions=None,
        periods=None,
        start=None,
        target_db=None,
        orientation="vertical",
    )


**Input arguments.**


???+ input "array"
    A numpy array containing the data to be included in the Databox.

???+ input "names"
    A sequence of names corresponding to the series in the array.

???+ input "descriptions"
    Descriptions for each series in the array.

???+ input "periods"
    An iterable of time periods corresponding to the rows of the array. Used if the data
    represents time series.

???+ input "start"
    The start period for the time series data. Used if 'periods' is not provided.

???+ input "target_db"
    An existing Databox to which the array data will be added. If `None`, a new 
    Databox is created.

???+ input "orientation"
    The orientation of the array, indicating how time series are arranged: 

    * `"horizontal"` means each row is a time series;

    * `"vertical"` means each column is a time series.


### Returns


A new Databox populated with the data from the numpy array -- or would; see the
warning at the top of this entry.

················································································
        """
        array = array if orientation == "horizontal" else array.T
        series_constructor = _get_series_constructor(start, periods, )
        return klass._from_horizontal_array_and_constructor(
            array,
            names,
            series_constructor,
            descriptions=descriptions,
            target_db=target_db,
        )

    @classmethod
    def _from_horizontal_array_and_constructor(
        klass,
        array: _np.ndarray,
        names: Iterable[str],
        series_constructor: Callable,
        *,
        descriptions: Sequence[str] | None = None,
        target_db: Self | None = None,
    ) -> Self:
        """
        """
        self = target_db or klass()
        descriptions = (
            descriptions if descriptions is not None
            else _it.repeat("", )
        )
        for name, values, description in zip(names, array, descriptions, ):
            print(name, type(values), description, )
            # self[name] = series_constructor(values=values, description=description, )
        return self

    @_dm.reference(category="retrieval", add_heading=False, )
    def array_from_series(
        self,
        names: Iterable[str],
        periods: Iterable[Period],
        variant: int = 0,
    ) -> _np.ndarray:
        r"""
................................................................................

## `array_from_series`

==Collects the values of several time series into one numpy array, one row per series.==

    array = self.array_from_series(
        names,
        periods,
        variant=0,
    )

Both `names` and `periods` are required. Use it to hand a block of the
Databox to code that works on plain arrays.


**Input arguments.**


???+ input "names"
    A list of names of the time series to be converted to a numpy array.
    Each name should correspond to a time series item in the Databox.

???+ input "periods"
    A list of periods for which the values of the time series will be
    extracted.

???+ input "variant"
    The variant (column) of the time series to be extracted. This is typically an
    integer representing a specific variant of the time series data.


### Returns

A numpy array of shape `(len(names), len(periods))`: one row per series and
one column per period, both in the order asked for.

### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> db = dp.Databox()
    >>> db["gdp"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2.]))
    >>> db["cpi"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([3., 4.]))
    >>> db["n"] = 42
    >>> db.array_from_series(["gdp", "cpi"],
    ...     dp.Span(dp.qq(2020, 1), dp.qq(2020, 2))).tolist()
    [[1.0, 2.0], [3.0, 4.0]]

................................................................................
        """
        def retrieve_values(name: str, ) -> _np.ndarray:
            return self[name].get_values(periods, variant, )
        return _np.vstack([ retrieve_values(n, ) for n in names ])

    def iter_variants(
        self,
        #
        item_iterator: Iterator[Any] | None = None,
        keys: Iterable[Any] | None = None,
    ) -> Iterator[dict]:
        """
        """
        if item_iterator is None:
            item_iterator = _default_item_iterator
        if keys is None:
            keys = self.keys()
        dict_variant_iter = {
            k: item_iterator(self[k], )
            for k in keys if k in self
        }
        while True:
            yield { k: next(v, ) for k, v in dict_variant_iter.items() }

    @_dm.reference(category="information", add_heading=False, )
    def get_names(
        self, 
        test: None | Callable = None,
        filter: None | Callable = None, # Legacy argument, will be deprecated in the future
    ) -> list[str]:
        """
················································································

## `get_names`

==Lists the names of the items in the Databox, optionally only those passing a test.==

    names = self.get_names(test=None, )


**Input arguments.**


???+ input "test"
    A function that takes a name and returns `True` to include the name in the
    output list, or `False` to keep the name out. If `None`, all names are
    included.

???+ input "filter"
    A legacy name for `test`, marked in the signature for deprecation. It is
    still accepted and still works. It shadows the builtin `filter` inside the
    method, and it is a different thing from the `Databox.filter` method.


### Returns


A tuple of names. Every name in the Databox when no test is given.

### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> db = dp.Databox()
    >>> db["gdp"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2.]))
    >>> db["cpi"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([3., 4.]))
    >>> db["n"] = 42
    >>> sorted(db.get_names())
    ['cpi', 'gdp', 'n']
    >>> sorted(db.get_names(lambda n: n.startswith("g")))
    ['gdp']

················································································
        """
        keys = tuple(self.keys())
        if filter is not None and test is None:
            test = filter
        if test is not None:
            keys = tuple(k for k in keys if test(k, ))
        return keys

    @_dm.reference(category="information", add_heading=False, )
    def get_missing_names(self, names: Iterable[str], ) -> tuple[str]:
        """
················································································

## `get_missing_names`

==Reports which of the names you ask about the Databox does not hold.==

    missing_names = self.get_missing_names(names)


**Input arguments.**


???+ input "names"
    An iterable of names to check against the Databox's items.


### Returns


A tuple of the names that are not in the Databox, in the order they were
given. Empty when the Databox holds them all.

### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> db = dp.Databox()
    >>> db["gdp"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2.]))
    >>> db["cpi"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([3., 4.]))
    >>> db["n"] = 42
    >>> db.get_missing_names(["gdp", "zz", "qq"])
    ('zz', 'qq')

················································································
        """
        return tuple(i for i in names if i not in self)

    @property
    @_dm.reference(category="property", add_heading=False, )
    def num_items(self, ) -> int:
        r"""
················································································

## `num_items`

==Gives the number of items held in the Databox.==

    self.num_items

A read-only property. It counts every entry, whether or not it is a time
series.


### Returns


A whole number, zero for an empty Databox.


### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> db = dp.Databox()
    >>> db["gdp"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2.]))
    >>> db["note"] = "not a series"
    >>> db.num_items
    2

················································································
        """
        return len(self.keys())

    @_dm.reference(category="copying", add_heading=False, )
    def to_dict(self: Self) -> dict:
        r"""
................................................................................

## `to_dict`

==Converts a Databox to a plain dictionary.==

    diction = self.to_dict()

The keys and values are carried across unchanged, so the values are the
same objects rather than copies. Use it to hand a Databox to code that
expects an ordinary `dict`.

### Returns


A plain `dict` holding the same items.

### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> db = dp.Databox()
    >>> db["gdp"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2.]))
    >>> db["cpi"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([3., 4.]))
    >>> db["n"] = 42
    >>> sorted(db.to_dict())
    ['cpi', 'gdp', 'n']
    >>> type(db.to_dict()).__name__
    'dict'

................................................................................
        """
        return { k: v for k, v in self.items() }

    @_dm.reference(category="manipulation", add_heading=False, )
    def copy(
        self: Self,
        source_names: SourceNames = None,
        target_names: TargetNames = None,
        strict_names: bool = False,
    ) -> Self:
        """
................................................................................

## `copy`

==Returns a new Databox holding deep copies of the items you name, under the names you give them.==

It does **not** duplicate the whole Databox unless you leave `source_names`
alone: `copy(["gdp"], ["y"])` returns a Databox whose only key is `y`. The
values are copied, so writing into the result does not reach the original;
`shallow` shares them instead.

    new_databox = self.copy(
        source_names=None,
        target_names=None,
        strict_names=False,
    )


**Input arguments.**


???+ input "source_names"
    Names of the items to include in the copy. Can be a list of names, a single 
    name, a callable returning `True` for names to include, or `None` to copy 
    all items.

???+ input "target_names"
    New names for the copied items, corresponding to 'source_names'. Can be a 
    list of names, a single name, or a callable function taking a source name 
    and returning the new target name.

???+ input "strict_names"
    If set to `True’, strictly adheres to the provided names, raising an error 
    if any source name is not found in the Databox.


### Returns


A new Databox. The original is not changed.

### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> db = dp.Databox()
    >>> db["gdp"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2.]))
    >>> db["cpi"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([3., 4.]))
    >>> db["n"] = 42
    >>> sorted(db.copy(["gdp"], ["y"]).keys())
    ['y']
    >>> sorted(db.copy().keys())
    ['cpi', 'gdp', 'n']

................................................................................
        """
        new_databox = _co.deepcopy(self, )
        if source_names is None and target_names is None:
            return new_databox
        source_names, target_names, *_ = self._resolve_source_target_names(
            source_names, target_names, strict_names,
        )
        new_databox.rename(source_names, target_names, strict_names=strict_names, )
        new_databox.keep(target_names, strict_names=strict_names, )
        return new_databox

    def has(
        self: Self,
        names: Iterable[str] | str,
    ) -> bool:
        """
        """
        return (
            names in self if isinstance(names, str)
            else not self.get_missing_names(names, )
        )

    @_dm.reference(category="copying", add_heading=False, )
    def shallow(
        self: Self,
        source_names: SourceNames = None,
        target_names: TargetNames = None,
        strict_names: bool = False,
    ) -> Self:
        r"""
................................................................................

## `shallow`

==Returns a new Databox referring to the same items, rather than to copies of them.==

The container is new but the values are the very same objects, so writing
into a series in the result changes it in the original too. `copy` is the
form that duplicates the values.

    shallow_databox = self.shallow(
        source_names=None,
        target_names=None,
        strict_names=False,
    )

**Input arguments.**

???+ input "self"
    The Databox object to copy.

???+ input "source_names"
    Names of the items to include in the copy. Can be a list of names, a single
    name, a callable returning `True` for names to include, or `None` to copy
    all items.

???+ input "target_names"
    New names for the copied items, corresponding to 'source_names'. Can be a
    list of names, a single name, or a callable function taking a source name
    and returning the new target name.

???+ input "strict_names"
    If set to `True`, strictly adheres to the provided names, raising an error
    if any source name is not found in the Databox.


### Returns


A new Databox sharing the original's items.

### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> db = dp.Databox()
    >>> db["gdp"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2.]))
    >>> db["cpi"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([3., 4.]))
    >>> db["n"] = 42
    >>> sorted(db.shallow(["gdp"]).keys())
    ['gdp']
    >>> db.shallow(["gdp"])["gdp"] is db["gdp"]
    True

................................................................................
        """
        source_names, target_names, *_ = self._resolve_source_target_names(
            source_names, target_names, strict_names,
        )
        return type(self)(
            (t, self[s])
            for s, t in zip(source_names, target_names, )
        )

    @_dm.no_reference
    def print_contents(
        self,
        source_names: SourceNames = None,
    ) -> None:
        """
        """
        shallow = self.shallow(source_names=source_names, )
        content_view = shallow._get_content_view()
        print()
        print("\n".join(content_view, ))
        print()

    @_dm.reference(category="validation", add_heading=False, )
    def validate(
        self: Self,
        validators: dict[str, Callable] | None,
        #
        strict_names: bool = False,
        when_fails: Literal["critical", "error", "warning", "silent", ] = "error",
        title: str = "Databox validation errors",
        message_when_fails: str = "Failed validation",
        message_when_missing: str = "Missing item",
    ) -> None | NoReturn:
        r"""
················································································

## `validate`

==Checks Databox items against tests and reports the ones that fail.==

    self.validate(
        validators,
        strict_names=False,
        when_fails="error",
        title="Databox validation errors",
        message_when_fails="Failed validation",
        message_when_missing="Missing item",
    )

Every failure is collected and reported together at the end, rather than
raising on the first one.


**Input arguments.**


???+ input "validators"
    A dictionary from item name to the check for that item. **Each value must
    be a sequence, not a bare function**, despite the `dict[str, Callable]`
    annotation on the parameter: the body reads `validators[key][0]` for the
    test and `validators[key][1]` for the message. So `{"n": (func,)}` and
    `{"n": (func, "must be positive")}` both work, while `{"n": func}` raises
    `TypeError: 'function' object is not subscriptable`.

    The test is called with the item as its only argument and should return
    something truthy to pass. A value in the first position that is not
    callable is treated as passing. Falsy `validators`, including `None` and
    `{}`, returns immediately.

???+ input "strict_names"
    If `True`, a name in `validators` that the Databox does not hold is itself
    a failure, reported with `message_when_missing`. If `False`, such names are
    skipped.

???+ input "when_fails"
    What happens once every item has been checked: `"error"` raises, and
    `"critical"`, `"warning"` and `"silent"` behave as elsewhere in the
    package.

???+ input "title"
    The heading of the collected report.

???+ input "message_when_fails"
    The text used for a failing item when its validator supplies none of its
    own, that is when the sequence has only one entry.

???+ input "message_when_missing"
    The text used for a name that is missing under `strict_names=True`.


### Returns


`None`, or raises according to `when_fails`. The Databox is not modified.


### Examples


A validator is a *sequence*, and the second entry is the message:

    >>> import datapie as dp
    >>> db = dp.Databox()
    >>> db["n"] = 42
    >>> db.validate({"n": (lambda x: x > 0, )}) is None
    True
    >>> try:
    ...     db.validate({"n": (lambda x: x < 0, "must be negative")})
    ... except Exception as error:
    ...     type(error).__name__
    'Error'

················································································
        """
        if not validators:
            return
        when_fails_stream = _wrongdoings.create_stream(when_fails, title, )
        keys_to_validate = set(validators.keys())
        if not strict_names:
            keys_to_validate &= set(self.keys())
        for key in keys_to_validate:
            if key not in self:
                message = f"{message_when_missing}: {key}"
                when_fails_stream.add(message, )
                continue
            func = validators[key][0]
            result = func(self[key], ) if callable(func) else True
            if not result:
                message = validators[key][1] if len(validators[key]) > 1 else message_when_fails
                when_fails_stream.add(f"{message}: {key}", )
        when_fails_stream._raise()

    @_dm.reference(category="manipulation", add_heading=False, )
    def rename(
        self: Self,
        #
        source_names: SourceNames = None,
        target_names: TargetNames = None,
        strict_names: bool = False,
    ) -> None:
        r"""
................................................................................

## `rename`

==Renames items in the Databox, keeping their values where they are.==

    self.rename(
        source_names=None,
        target_names=None,
        strict_names=False,
    )

The two arguments do different jobs: `source_names` chooses which items
are affected and `target_names` says what they become. A callable in the
first position **selects**, and a callable in the second **renames**, so
`rename(lambda n: n.upper())` renames nothing -- it selects every name
and then supplies no new one.


**Input arguments.**


???+ input "source_names"
    The current names of the items to be renamed. Accepts a list of names, a 
    single name, or a callable that generates new names based on the given ones.

???+ input "target_names"
    The new names for the items. Should align with 'source_names'. Can be a list 
    of names, a single name, or a callable function taking each source name and 
    returning the corresponding target name.

???+ input "strict_names"
    If set to `True`, enforces strict adherence to the provided names, with an 
    error raised for any source name not found in the Databox.


### Returns


Nothing; the Databox is modified in place.

### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> db = dp.Databox()
    >>> db["gdp"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2.]))
    >>> db["cpi"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([3., 4.]))
    >>> db["n"] = 42
    >>> db.rename(["gdp"], ["output"])
    >>> sorted(db.keys())
    ['cpi', 'n', 'output']

................................................................................
        """
        source_names, target_names, *_ = self._resolve_source_target_names(
            source_names, target_names, strict_names,
        )
        for s, t in zip(source_names, target_names, ):
            self[t] = self.pop(s)

    @_dm.reference(category="manipulation", add_heading=False, )
    def remove(
        self: Self,
        remove_names: SourceNames = None,
        strict_names: bool = False,
    ) -> None:
        """
................................................................................

## `remove`

==Removes the named items from the Databox.==

    self.remove(
        remove_names=None,
        *,
        strict_names=False,
    )


**Input arguments.**


???+ input "remove_names"
    Names of the items to be removed from the Databox. Can be a list of names, a 
    single name, a callable that returns `True` for names to be removed, or 
    `None`. If `None`, no items are removed.

???+ input "strict_names"
    If `True`, strictly adheres to the provided names, raising an error if any 
    name is not found in the Databox.


### Returns


Nothing; the Databox is modified in place and the removed items are gone.
`keep` is the complement, naming what to retain instead.

### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> db = dp.Databox()
    >>> db["gdp"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2.]))
    >>> db["cpi"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([3., 4.]))
    >>> db["n"] = 42
    >>> db.remove(["n"])
    >>> sorted(db.keys())
    ['cpi', 'gdp']


················································································
        """
        if remove_names is None:
            return
        remove_names, *_ \
            = self._resolve_source_target_names(remove_names, None, strict_names, )
        for n in remove_names:
            del self[n]

    @_dm.reference(category="manipulation", add_heading=False, )
    def keep(
        self: Self,
        #
        keep_names: SourceNames = None,
        strict_names: bool = False,
    ) -> None:
        r"""
················································································

## `keep`

==Keeps the named items in the Databox and removes every other one.==

    self.keep(
        keep_names=None,
        strict_names=False,
    )


**Input arguments.**


???+ input "keep_names"
    The names of the items to be retained in the Databox. Can be a list of names, 
    a single name, or a callable function determining the items to keep.

???+ input "strict_names"
    If set to `True`, enforces strict adherence to the provided names, with an 
    error raised for any name not found in the Databox.


### Returns


Nothing; the Databox is modified in place and everything not named is gone.
`remove` is the complement, naming what to drop instead.

### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> db = dp.Databox()
    >>> db["gdp"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2.]))
    >>> db["cpi"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([3., 4.]))
    >>> db["n"] = 42
    >>> db.keep(["gdp"])
    >>> sorted(db.keys())
    ['gdp']

················································································
        """
        if keep_names is None:
            return
        keep_names, *_ \
            = self._resolve_source_target_names(keep_names, None, strict_names, )
        remove_names = set(self.keys()) - set(keep_names)
        for n in remove_names:
            del self[n]


    @_dm.reference(category="manipulation", add_heading=False, )
    def apply(
        self,
        func: Callable,
        source_names: SourceNames = None,
        in_place: bool = True,
        when_fails: Literal["critical", "error", "warning", "silent", ] = "critical",
        strict_names: bool = False,
    ) -> None:
        r"""
················································································


## `apply`

==Applies a function to the items you name, optionally writing what it returns back over them.==

    self.apply(
        func,
        source_names=None,
        in_place=True,
        when_fails="critical",
        strict_names=False,
    )


**Input arguments.**


???+ input "func"
    The function to apply to each selected item in the Databox.

???+ input "source_names"
    Names of the items to which the function will be applied. Can be a list of 
    names, a single name, a callable returning `True’ for names to include, or 
    `None` to apply to all items.

???+ input "in_place"
    Decides whether the value `func` returns is kept. With the default `True`
    the return value is **discarded**, and only changes `func` made to the item
    itself survive -- so `apply(lambda x: x*2)` leaves the databox untouched.
    With `False` the return value is assigned back over the item, which is what
    a function that computes rather than mutates needs.

???+ input "when_fails"
    Specifies the action to take if applying the function fails. Options are 
    "critical", "error", "warning", or "silent".

???+ input "strict_names"
    If set to `True`, strictly adheres to the provided names, raising an error 
    if any source name is not found in the Databox.


### Returns


Nothing; items are modified in the Databox itself. Note that `in_place`
applies to the *items*, not to the Databox. Errors are collected and handled
according to `when_fails`.

### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> db = dp.Databox()
    >>> db["gdp"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2.]))
    >>> db["cpi"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([3., 4.]))
    >>> db["n"] = 42
    >>> db.apply(lambda s: s*2, source_names=["gdp"], in_place=False)
    >>> db["gdp"].get_data()[:, 0].tolist()
    [2.0, 4.0]


················································································
        """
        source_names, *_ = self._resolve_source_target_names(
            source_names, None, strict_names,
        )
        when_fails_stream = _wrongdoings.create_stream(
            when_fails,
            f"Error(s) when applying function to Databox items:",
        )
        for s in source_names:
            try:
                output = func(self[s])
                if not in_place:
                    self[s] = output
            except Exception as e:
                when_fails_stream.add(f"{s}: {repr(e)}", )
        when_fails_stream._raise()

    @_dm.reference(category="manipulation", add_heading=False, )
    def generate(
        self,
        func: Callable,
        target_names: TargetNames,
        source_names: SourceNames = None,
        when_fails: Literal["critical", "error", "warning", "silent", ] = "critical",
        strict_names: bool = False,
    ) -> None:
        r"""
················································································


## `generate`

==Builds new items from existing ones by applying a function, leaving the originals in place.==

Where `apply` changes the items it touches, this adds items under new
names and keeps the sources.

    self.generate(
        func,
        target_names,
        source_names=None,
        when_fails="critical",
        strict_names=False,
    )


**Input arguments.**


???+ input "func"
    The function to apply to each selected item in the Databox to generate a new
    item.

???+ input "target_names"
    Names of the newly generate items, either an iterable of strings (ordered
    same as `source_names`), or a function transforming a string (an existing
    name) into another string (the new name).

???+ input "source_names"
    Names of the items to which the function will be applied. Can be a list of 
    names, a single name, a callable returning `True’ for names to include, or 
    `None` to apply to all items.

???+ input "when_fails"
    Specifies the action to take if applying the function fails. Options are 
    "critical", "error", "warning", or "silent".

???+ input "strict_names"
    If set to `True`, strictly adheres to the provided names, raising an error 
    if any source name is not found in the Databox.


### Returns


Nothing; the new items are added to the Databox. Errors are collected and
handled according to `when_fails`.

### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> db = dp.Databox()
    >>> db["gdp"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2.]))
    >>> db["cpi"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([3., 4.]))
    >>> db["n"] = 42
    >>> db.generate(lambda s: s*10, ["big"], ["gdp"])
    >>> sorted(db.keys())
    ['big', 'cpi', 'gdp', 'n']
    >>> db["big"].get_data()[:, 0].tolist()
    [10.0, 20.0]


················································································
        """
        source_names, target_names, *_ = self._resolve_source_target_names(
            source_names, target_names, strict_names,
        )
        when_fails_stream = _wrongdoings.create_stream(
            when_fails,
            f"Error(s) when applying function to Databox items:",
        )
        for s, t, in zip(source_names, target_names, ):
            try:
                self[t] = func(self[s], )
            except Exception as e:
                when_fails_stream.add(f"{s}: {repr(e)}", )
        when_fails_stream._raise()

    def max_abs(
        self,
        other: Self,
    ) -> Self:
        """
        """
        def _max_abs(x, ):
            return _np.nanmax(abs(_np.array(x)))
        output = type(self)()
        for n in self.keys():
            if n not in other:
                continue
            numeric_classes = (Number, _np.ndarray, )
            if isinstance(self[n], Series, ) and isinstance(other[n], Series, ):
                diff_array = (self[n] - other[n]).get_data()
                output[n] = _max_abs(diff_array) if diff_array.size else None
            elif isinstance(self[n], numeric_classes, ) and isinstance(other[n], numeric_classes, ):
                output[n] = _max_abs(self[n] - other[n], )
        return output

    @_dm.reference(category="information", add_heading=False, )
    def filter(
        self,
        #
        name_test: Callable | None = None,
        value_test: Callable | None = None,
    ) -> Iterable[str]:
        r"""
················································································


## `filter`

==Selects the names of items passing a test on the name, on the value, or on both.==

    filtered_names = self.filter(
        name_test=None,
        value_test=None,
    )

It returns names, not items, so the result is what you hand to `keep`,
`remove` or `array_from_series`. This is a different thing from the
legacy `filter` argument of `get_names`.


**Input arguments.**


???+ input "name_test"
    Called with each item's name; the name is kept when it returns `True`.
    Left as `None` every name passes.

???+ input "value_test"
    Called with each item's value on the same terms. Left as `None` every
    value passes. Both tests given, a name has to pass both.


### Returns


A tuple of the names that passed. With neither test given, every name in
the Databox.

### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> db = dp.Databox()
    >>> db["gdp"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2.]))
    >>> db["cpi"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([3., 4.]))
    >>> db["n"] = 42
    >>> sorted(db.filter(value_test=lambda v: isinstance(v, dp.Series)))
    ['cpi', 'gdp']


················································································
        """
        names = tuple(self.get_names())
        if name_test is None and value_test is None:
            return names
        name_test = name_test if name_test else lambda x: True
        value_test = value_test if value_test else lambda x: True
        return tuple(
            name
            for name in names
            if name_test(name) and value_test(self[name], )
        )

    @_dm.reference(category="information", add_heading=False, )
    def get_series_names_by_frequency(
        self,
        frequency: Frequency,
    ) -> tuple[str]:
        r"""
················································································

## `get_series_names_by_frequency`

==Lists the names of the time series held at one date frequency.==

    time_series_names = self.get_series_names_by_frequency(frequency)


**Input arguments.**


???+ input "frequency"
    The frequency to select by, a member of `Frequency`.


### Returns


A tuple of the names whose series carry that frequency. Entries that are
not time series never appear, and a frequency no series uses gives an
empty result rather than an error.

### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> db = dp.Databox()
    >>> db["gdp"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2.]))
    >>> db["cpi"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([3., 4.]))
    >>> db["n"] = 42
    >>> sorted(db.get_series_names_by_frequency(dp.Frequency.QUARTERLY))
    ['cpi', 'gdp']

················································································
        """
        def _is_series_with_frequency(x, ):
            return isinstance(x, Series) and x.frequency == frequency
        return self.filter(value_test=_is_series_with_frequency, )

    @_dm.reference(category="information", add_heading=False, )
    def get_span_by_frequency(
        self,
        frequency: Frequency,
    ) -> Span:
        r"""
················································································

## `get_span_by_frequency`

==Gives the span covering every time series held at one date frequency.==

    date_span = self.get_span_by_frequency(frequency)

The span reaches from the earliest start to the latest end among those
series, so it encompasses them all even where they do not overlap.


**Input arguments.**


???+ input "frequency"
    The frequency to select by, a member of `Frequency` or the plain
    integer behind one.


### Returns


A `Span` encompassing the matching series.

### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> db = dp.Databox()
    >>> db["gdp"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2.]))
    >>> db["cpi"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([3., 4.]))
    >>> db["n"] = 42
    >>> db.get_span_by_frequency(dp.Frequency.QUARTERLY)
    Span(qq(2020,1), qq(2020,2))

················································································
        """
        if frequency == Frequency.UNKNOWN:
            return EmptySpan()
        names = self.get_series_names_by_frequency(frequency)
        if not names:
            return EmptySpan()
        start_periods = (self[n].start_date for n in names)
        end_periods = (self[n].end_date for n in names)
        min_start_date = min(start_periods, key=_op.attrgetter("serial"), )
        max_end_date = max(end_periods, key=_op.attrgetter("serial"), )
        return Span(min_start_date, max_end_date, )

    @_dm.reference(category="multiple", add_heading=False, )
    def overlay_by_span(
        self,
        other: Self,
        **kwargs,
    ) -> None:
        """
................................................................................


## `overlay_by_span`

==Writes each series of another Databox over the matching one here, across the whole span of the other.==

    self.overlay_by_span(
        other,
        names=None,
        strict_names=False,
    )

Each pair of series is combined by `Series.overlay_by_span`, so everything
between `other`'s first and last observation comes from `other`, its own gaps
included. Use `overlay_by_observation` to take only the periods `other`
actually carries.


**Input arguments.**

???+ input "other"
    The Databox whose time series are overlaid onto the ones here.

???+ input "names"
    An optional iterable of names to overlay. If `None`, the operation covers
    the names both Databoxes hold as time series.

???+ input "strict_names"
    If `True`, the names in `names` are taken as given and a name missing from
    either Databox raises `KeyError`. If `False`, such names are dropped.


### Returns


Nothing; the Databox is modified in place. Entries that are not time series are
left alone, as are pairs whose frequencies differ or whose frequency is
`UNKNOWN`.

### Examples


`b` has a gap in 2020-Q2, which is what separates the two overlay forms:

    >>> import numpy as np
    >>> import datapie as dp
    >>> a = dp.Databox()
    >>> a["s"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2., 3., 4.]))
    >>> b = dp.Databox()
    >>> b["s"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([9., np.nan, 9., 9.]))
    >>> a.overlay_by_span(b)
    >>> a["s"].get_data()[:, 0].tolist()
    [9.0, nan, 9.0, 9.0]


................................................................................
"""
        self._lay(other, Series.overlay_by_span, **kwargs, )

    @_dm.reference(category="multiple", add_heading=False, )
    def overlay_by_observation(
        self,
        other: Self,
        **kwargs,
    ) -> None:
        r"""
................................................................................

## `overlay_by_observation`

==Writes each series of another Databox over the matching one here, only where the other has an observation.==

    self.overlay_by_observation(
        other,
        names=None,
        strict_names=False,
    )

Each pair of series is combined by `Series.overlay_by_observation`, so
`other` wins only in the periods where it actually has an observation.
Use `overlay_by_span` to hand over its gaps as well.


**Input arguments.**

???+ input "other"
    The Databox whose time series are overlaid onto the ones here.

???+ input "names"
    An optional iterable of names to overlay. If `None`, the operation covers
    the names both Databoxes hold as time series.

???+ input "strict_names"
    If `True`, the names in `names` are taken as given and a name missing from
    either Databox raises `KeyError`. If `False`, such names are dropped.


### Returns


Nothing; the Databox is modified in place. Entries that are not time series are
left alone, as are pairs whose frequencies differ or whose frequency is
`UNKNOWN`.


### Examples


`b` has a gap in 2020-Q2, which is what separates the two overlay forms:

    >>> import numpy as np
    >>> import datapie as dp
    >>> a = dp.Databox()
    >>> a["s"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2., 3., 4.]))
    >>> b = dp.Databox()
    >>> b["s"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([9., np.nan, 9., 9.]))
    >>> a.overlay_by_observation(b)
    >>> a["s"].get_data()[:, 0].tolist()
    [9.0, 2.0, 9.0, 9.0]

................................................................................
        """
        self._lay(other, Series.overlay_by_observation, **kwargs, )

    @_dm.reference(category="multiple", add_heading=False, )
    def underlay_by_span(
        self,
        other: Self,
        **kwargs,
    ) -> None:
        """
................................................................................


## `underlay_by_span`

==Slides each series of another Databox underneath the matching one here, so this Databox wins across its whole span.==

    self.underlay_by_span(
        other,
        names=None,
        strict_names=False,
    )

Each pair of series is combined by `Series.underlay_by_span`, so this Databox
keeps everything between its own first and last observation, its internal gaps
included, and `other` reaches only the periods outside that stretch. Use
`underlay_by_observation` to fill those internal gaps instead.


**Input arguments.**

???+ input "other"
    The Databox whose time series are laid underneath the ones here.

???+ input "names"
    An optional iterable of names to underlay. If `None`, the operation covers
    the names both Databoxes hold as time series.

???+ input "strict_names"
    If `True`, the names in `names` are taken as given and a name missing from
    either Databox raises `KeyError`. If `False`, such names are dropped.


### Returns


Nothing; the Databox is modified in place. Entries that are not time series are
left alone, as are pairs whose frequencies differ or whose frequency is
`UNKNOWN`.

### Examples


`a` has a gap in 2020-Q3, which is what separates the two underlay forms:

    >>> import numpy as np
    >>> import datapie as dp
    >>> a = dp.Databox()
    >>> a["s"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2., np.nan, 4.]))
    >>> b = dp.Databox()
    >>> b["s"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([9., 9., 9., 9.]))
    >>> a.underlay_by_span(b)
    >>> a["s"].get_data()[:, 0].tolist()
    [1.0, 2.0, nan, 4.0]


................................................................................
        """
        self._lay(other, Series.underlay_by_span, **kwargs, )

    @_dm.reference(category="multiple", add_heading=False, )
    def underlay_by_observation(
        self,
        other: Self,
        **kwargs,
    ) -> None:
        r"""
................................................................................

## `underlay_by_observation`

==Slides each series of another Databox underneath the matching one here, filling only the periods this one leaves empty.==

    self.underlay_by_observation(
        other,
        names=None,
        strict_names=False,
    )

Each pair of series is combined by `Series.underlay_by_observation`, so this
Databox wins wherever it holds a value and `other` shows through only where it
does not -- inside the span as well as outside it. This is the one to reach for
when filling gaps from a second Databox.


**Input arguments.**

???+ input "other"
    The Databox whose time series are laid underneath the ones here.

???+ input "names"
    An optional iterable of names to underlay. If `None`, the operation covers
    the names both Databoxes hold as time series.

???+ input "strict_names"
    If `True`, the names in `names` are taken as given and a name missing from
    either Databox raises `KeyError`. If `False`, such names are dropped.


### Returns


Nothing; the Databox is modified in place. Entries that are not time series are
left alone, as are pairs whose frequencies differ or whose frequency is
`UNKNOWN`.

### Examples


`a` has a gap in 2020-Q3, which is what separates the two underlay forms:

    >>> import numpy as np
    >>> import datapie as dp
    >>> a = dp.Databox()
    >>> a["s"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2., np.nan, 4.]))
    >>> b = dp.Databox()
    >>> b["s"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([9., 9., 9., 9.]))
    >>> a.underlay_by_observation(b)
    >>> a["s"].get_data()[:, 0].tolist()
    [1.0, 2.0, 9.0, 4.0]

................................................................................
        """
        self._lay(other, Series.underlay_by_observation, **kwargs, )

    def _lay(
        self,
        other: Self,
        func: Callable,
        names: Iterable[str] | None = None,
        strict_names: bool = False,
        **kwargs,
    ) -> None:
        """"
        """
        if names is None:
            def value_test(x): return isinstance(x, Series)
            self_names = self.filter(value_test=value_test, )
            other_names = other.filter(value_test=value_test, )
            names = tuple(set(self_names) & set(other_names))
        if not strict_names:
            names = tuple(set(names) & set(self.keys()) & set(other.keys()))
        for n in names:
            if self[n].frequency == Frequency.UNKNOWN:
                continue
            if self[n].frequency != other[n].frequency:
                continue
            func(self[n], other[n], **kwargs, )

    @_dm.reference(category="manipulation", add_heading=False, )
    def clip_series(
        self,
        new_start_date: Period | None = None,
        new_end_date: Period | None = None,
    ) -> None:
        """
................................................................................


## `clip_series`

==Shortens the time series in the Databox to a new start and end period.==

    self.clip_series(
        new_start_date=None,
        new_end_date=None,
    )

Only series matching the frequency of the periods given are touched; every
other entry, series or not, is left alone.


**Input arguments.**


???+ input "new_start_date"
    The new start date for clipping the series. If `None`, only `new_end_date`
    is considered.

???+ input "new_end_date"
    The new end date for clipping the series. If `None`, only `new_start_date`
    is considered.


### Returns


Nothing; the Databox is modified in place and the discarded observations are
gone.

### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> db = dp.Databox()
    >>> db["gdp"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2.]))
    >>> db["cpi"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([3., 4.]))
    >>> db["n"] = 42
    >>> db.clip_series(dp.qq(2020, 2), None)
    >>> db["gdp"].get_data()[:, 0].tolist()
    [2.0]

................................................................................
        """
        if new_start_date is None and new_end_date is None:
            return
        frequency = (
            new_start_date.frequency
            if new_start_date is not None
            else new_end_date.frequency
        )
        value_test = lambda x: isinstance(x, Series) and x.frequency == frequency
        for n in self.get_series_names_by_frequency(frequency, ):
            self[n].clip(new_start_date, new_end_date, )

    # Legacy alias for backward compatibility
    clip = clip_series

    @_dm.reference(category="multiple", add_heading=False, )
    def prepend(
        self,
        other: Self,
        end_prepending: Period,
    ) -> Self:
        """
................................................................................

## `prepend`

==Adds earlier observations from another Databox in front of the ones held here.==

    self.prepend(
        other,
        end_prepending,
    )

**Input arguments.**

???+ input "other"
    The Databox containing the time series data to prepend to `self`.

???+ input "end_prepending"
    The end date up to which the time series data from the `other` Databox will
    be added to `self`.

### Returns


Nothing; the Databox is modified in place. The work is done by the underlay
machinery, so this Databox's own observations always win where it has them.


### Examples


`b` covers 2020-Q1 to 2020-Q4, but only its history up to `end_prepending` is
taken, and the 99s it holds where `a` already has values are ignored:

    >>> import numpy as np
    >>> import datapie as dp
    >>> a = dp.Databox()
    >>> a["s"] = dp.Series(start=dp.qq(2020, 3),
    ...     values=np.array([3., 4.]))
    >>> b = dp.Databox()
    >>> b["s"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2., 99., 99.]))
    >>> a.prepend(b, dp.qq(2020, 2))
    >>> a["s"].start
    qq(2020,1)
    >>> a["s"].get_data()[:, 0].tolist()
    [1.0, 2.0, 3.0, 4.0]

................................................................................
        """
        other = other.copy()
        other.clip(None, end_prepending, )
        self.underlay_by_span(other, )

    @_dm.reference(category="evaluation", add_heading=False, )
    def evaluate_expression(
        self,
        expression: str,
        *args, 
        **kwargs,
    ) -> Any:
        """
................................................................................


## `evaluate_expression`

==Evaluates a string expression with the Databox entries as its variables.==

Evaluate a given string expression using the entries in the Databox as 
contextual variables. This method first checks if the expression directly 
matches an entry name within the Databox; if not, it attempts to evaluate the 
expression using Python's `eval()` with the current entries as the variable 
context.

    result = self.evaluate_expression(
        expression,
        series_function_context=False,
        context=None,
    )

Shortcut syntax:

    result = self(expression, context=None)

**Any expression containing an `=` character raises `TypeError: 'str' object
cannot be interpreted as an integer`.** The helper that rewrites such
expressions calls `expression.split(expression, "=")`, splitting the string by
itself and passing `"="` where a maximum split count belongs. The guard above it
is only `if "=" in expression`, so this reaches well past the intended `a=b`:
comparisons such as `a==b` and `a<=b`, any call using a keyword argument such as
`round(a, ndigits=2)`, and any default argument such as `lambda x=1: x` all
fail. Positional calls, attribute access, list comprehensions and dict literals
are unaffected, the last because they use `:` rather than `=`. The shortcut form
`self(expression)` fails the same way.


**Input arguments.**


???+ input "expression"
    The string expression to evaluate. If the expression matches an item name 
    in the Databox, the corresponding item is returned without further 
    evaluation.

???+ input "series_function_context"
    If `True`, the time series function context is added to the names available
    to the expression. `False` when left alone.

???+ input "context"
    An optional dictionary providing additional context for evaluation. Can 
    include variables that are not present directly in the Databox. Databox
    entries take precedence over both this and the series function context.


### Returns


Whatever the expression evaluates to -- often a `Series`, but any Python value
the expression can produce.


### Examples


    >>> import numpy as np
    >>> import datapie as dp
    >>> db = dp.Databox()
    >>> db["a"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2.]))
    >>> db["b"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([3., 4.]))
    >>> db.evaluate_expression("a+b").get_data()[:, 0].tolist()
    [4.0, 6.0]

Extra names can be supplied through `context`:

    >>> db.evaluate_expression("a*k", context={"k": 10}).get_data()[:, 0].tolist()
    [10.0, 20.0]


................................................................................
        """
        expression = expression.strip()
        if expression in self:
            return self[expression]
        else:
            return self.eval(expression, *args, **kwargs, )

    @_dm.no_reference
    def eval(
        self,
        expression: str,
        series_function_context: bool = False,
        context: dict[str, Any] | None = None,
    ) -> Any:
        """
        """
        expression = _reformat_eval_expression(expression, )
        all_context = {}
        if series_function_context:
            all_context.update(_series.function_context, )
        if context:
            all_context.update(context, )
        all_context.update({ k: v for k, v in self.items() })
        return eval(expression, all_context, )

    def __call__(self, *args, **kwargs, ) -> Any:
        r"""
        """
        return self.evaluate_expression(*args, **kwargs, )

    @classmethod
    @_dm.reference(category="constructor", add_heading=False, )
    def steady(
        klass,
        steady_databoxable: SteadyDataboxableProtocol,
        span: Iterable[Period],
        *,
        deviation: bool = False,
        unpack_single: bool = True,
        prepend_initial: bool = True,
        append_terminal: bool = True,
        **kwargs,
    ) -> Self:
        r"""
................................................................................


## `Databox.steady`

==Creates a Databox of steady-state time series for a model.==


Create a Databox with steady-state values for a model, based on the provided
model object and the time span. This method generates steady-state time series
data for each item in the model. This constructor can be used for models that
have well-defined steady state, i.e. Simultaneous models and
VectorAutoregression models.


    steady_databox = Databox.steady(
        steady_databoxable,
        span,
        *,
        deviation=False,
    )

This is a class method: call it on the class, not on a Databox you already have.


**Input arguments.**


???+ input "steady_databoxable"
    The model object for which to generate steady-state time series data. Any
    object satisfying `SteadyDataboxableProtocol` will do.


???+ input "span"
    The time span for which to generate steady-state time series data.

???+ input "deviation"
    If `True`, the steady-state values are generated as deviations from the
    steady state in the form depending on the log status of each variable. If
    `False`, the steady-state values are generated in their original level form.


### Returns

A Databox containing steady-state time series for `steady_databoxable`.

Further keyword arguments in the signature -- `unpack_single`,
`prepend_initial` and `append_terminal` -- are passed on to the model object and
are not described here.


................................................................................
        """
        self = klass()
        start, end, = _periods.extend_span(
            span,
            steady_databoxable.max_lag,
            steady_databoxable.max_lead,
            prepend_initial,
            append_terminal,
        )
        items = steady_databoxable.generate_steady_items(
            start, end,
            deviation=deviation,
            **kwargs,
        )
        return klass({ k: v for k, v in items })

    @classmethod
    @_dm.reference(category="constructor", add_heading=False, )
    def zero(
        klass,
        steady_databoxable: SteadyDataboxableProtocol,
        span: Iterable[Period],
        *,
        deviation: None = None,
        **kwargs,
    ) -> Self:
        r"""
................................................................................


## `Databox.zero`

==Creates a Databox of zero-deviation time series for a model.==

    zero_databox = Databox.zero(steady_databoxable, span, **kwargs)

This constructor is equivalent to calling

    zero_databox = Databox.steady(steady_databoxable, span, deviation=True, ...)

See the [`Databox.steady`](#steady) method for details of the arguments; they
are all passed straight through.


**Input arguments.**


???+ input "steady_databoxable"
    The model object for which to generate the zero-deviation time series.

???+ input "span"
    The time span to generate them over.

???+ input "deviation"
    Present in the signature only so that supplying it can be rejected. Passing
    it at all -- `True` or `False` alike -- raises `ValueError: The 'deviation'
    argument is not allowed for the Databox.zero method`, since this constructor
    exists precisely to fix it at `True`.


................................................................................
        """
        if deviation is not None:
            raise ValueError("The 'deviation' argument is not allowed for the Databox.zero method")
        return klass.steady(steady_databoxable, span, deviation=True, **kwargs, )

    @_dm.reference(category="manipulation", add_heading=False, )
    def minus_control(
        self,
        model,
        control: Self,
    ) -> None:
        r"""
................................................................................

## `minus_control`

==Subtracts a control Databox from this one, series by series.==

Subtract control values (usually steady-state values or control simulation
values) from the corresponding time series in the Databox.

    self.minus_control(
        model,
        control,
    )

**Input arguments.**

???+ input "model"
    The underlying model object based on which the `self` and `control` were
    created.

???+ input "control"
    The Databox containing control values to subtract from the corresponding
    time series in `self`. Only the names the model maps are touched, and each
    one keeps its description.

### Returns

Nothing; the Databox is modified in place. Only the names the model maps are
touched, and each keeps the description it had.


### Examples


Any object exposing `map_name_to_minus_control_func` will do; a real model
supplies one per variable. Note that `gdp` keeps its description:

    >>> import numpy as np
    >>> import datapie as dp
    >>> class Model:
    ...     def map_name_to_minus_control_func(self):
    ...         return {"gdp": lambda x, c: x - c}
    >>> db = dp.Databox()
    >>> db["gdp"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([10., 20.]), description="GDP")
    >>> control = dp.Databox()
    >>> control["gdp"] = dp.Series(start=dp.qq(2020, 1),
    ...     values=np.array([1., 2.]))
    >>> db.minus_control(Model(), control)
    >>> db["gdp"].get_data()[:, 0].tolist()
    [9.0, 18.0]
    >>> db["gdp"].get_description()
    'GDP'

................................................................................
        """
        name_to_minus_control_func = model.map_name_to_minus_control_func()
        for name, func in name_to_minus_control_func.items():
            description = self[name].get_description()
            self[name] = func(self[name], control[name], )
            self[name].set_description(description, )

    def __or__(self, other) -> Self:
        new = _co.deepcopy(self)
        new.update(other, )
        return new

    def _resolve_source_target_names(
        self,
        source_names: SourceNames,
        target_names: TargetNames,
        strict_names: bool = False,
    ) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
        """
        """
        context_names = self.get_names()
        if source_names is None:
            source_names = context_names
        if isinstance(source_names, str):
            source_names = (source_names, )
        if callable(source_names):
            func = source_names
            source_names = tuple(n for n in context_names if func(n))
        if target_names is None:
            target_names = source_names
        if isinstance(target_names, str):
            target_names = (target_names, )
        if callable(target_names):
            func = target_names
            target_names = tuple(func(n) for n in source_names)
        if not strict_names:
            source_target_pairs = tuple((s, t) for s, t in zip(source_names, target_names, ) if s in context_names)
            source_names, target_names = zip(*source_target_pairs, ) if source_target_pairs else ((), (), )
        return source_names, target_names, context_names,

    #]


def _reformat_eval_expression(expression: str, ) -> str:
    """
    """
    #[
    if "=" in expression:
        lhs, *rhs = expression.split(expression, "=", )
        rhs = "=".join(rhs, )
        expression = "({lhs})-({rhs})"
    return expression
    #]


def _default_item_iterator(value: Any, ) -> Iterator[Any]:
    """
    """
    #[
    is_value_iterable = (
        isinstance(value, Iterable)
        and not isinstance(value, str)
        and not isinstance(value, bytes)
    )
    value = value if is_value_iterable else [value, ]
    yield from _iterators.exhaust_then_last(value, None, )
    #]


def _get_series_constructor(
    start: Period | None = None,
    periods: Iterable[Period] | None = None,
) -> Callable | None:
    """
    """
    #[
    if start is not None:
        return lambda values: Series(start=start, values=values, )
    elif periods is not None:
        return lambda values: Series(periods=periods, values=values, )
    #]

