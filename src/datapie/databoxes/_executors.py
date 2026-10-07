r"""
"""

#[

# Standard library imports
import runpy
from typing import Callable, Self, Any
from types import ModuleType
from collections.abc import Iterable

#]


def _hard_exclude(name: str, value: Any, ) -> bool:
    return (
        name.startswith("__")
        or isinstance(value, ModuleType)
    )


def _default_exclude(name: str, value: Any, ) -> bool:
    return name.startswith("_")


class Mixin:
    r"""
    Mixin class for Databox executors.
    """
    #[

    @classmethod
    def from_file(
        klass,
        filename,
        *,
        exclude=_default_exclude,
    ) -> Self:
        r"""

        --------------------------------------------------------------------------------
        ## from_file

        ==Create a new databox from the objects defined in a Python script==

        ```
        self = Databox.from_file(
            filename,
            exclude=<filter>,
        )
        ```

        The script found at `filename` is executed as a standalone program,
        much as if it were launched with `python filename`, and the objects
        left in its global namespace are collected into a new databox, each
        under the name it had in the script, except for names that are
        excluded as described below. The new databox starts out empty, so the
        script does not see any pre-existing items. To run a script against an
        existing databox and add to it, use `execute_file`.

        ### Input arguments

        __`filename`__ (`str`)
        :   Path to the Python script to run. The script is executed in a
            namespace of its own and does not share globals with the calling
            code.

        __`exclude`__ (function or `None`)
        :   A filter that lets you decide which of the objects created by the
            script should not be stored in the new databox; see _Excluded
            names_ below. The filter is a function that is handed two things
            about each object, in this order: its name, as a string, and the
            object itself. It answers `True` if the object should be left out
            and `False` if it should be kept. The function must accept both
            arguments, even if it only looks at one of them. If you do not
            specify `exclude`, objects whose names begin with a single
            underscore, such as `_tmp` or `_helper`, are left out. If you
            specify `exclude=None`, no filter is applied, and only the fixed
            exclusions described below remain.

        ### Returns

        A new databox, of the same class as the one on which the method is
        called, holding the objects created by the script.

        ### Excluded names

        Whether an object created by the script is kept out of the databox is
        decided in two steps, and an object is left out if either step
        excludes it.

        The first step is fixed and cannot be changed, and it always leaves
        out two kinds of objects. The first kind are objects whose names begin
        with a double underscore, such as `__name__` and `__builtins__`;
        Python adds such names to every namespace for its own purposes, and
        they are never meant to be data. The second kind are modules, such as
        the one that `import numpy as np` brings in; these are tools the
        script uses rather than results it produces. As a consequence, an
        import never adds an item to the databox.

        The second step is custom and is controlled by the `exclude` argument.
        By default, it leaves out all objects whose names begin with a single
        underscore, following the usual convention that such names are private
        or temporary. You can replace this rule with your own filter, which is
        shown both the name and the value of each object and can therefore
        decide on either one, for instance to leave out names with a certain
        prefix, to keep some underscored names, or to leave out all objects of
        a certain type. You can also switch the custom step off entirely with
        `exclude=None`, in which case only the fixed step applies. Be aware
        that with `exclude=None`, single-underscore names, including the
        `_requires` helper, do end up in the databox.

        Every object that passes both steps is stored, not only data:
        functions and classes defined in the script are stored as well, unless
        `exclude` filters them out.

        ### Details

        Because the new databox starts out empty, calling the helper function
        `_requires` inside the script with any item name will raise a
        `ValueError`. Scripts that declare requirements are meant to be run
        against an existing databox with `execute_file`.

        Any exception raised by the script is propagated to the caller, and no
        databox is returned.

        --------------------------------------------------------------------------------

        """
        self = klass()
        self.execute_file(filename, exclude=exclude)
        return self

    @classmethod
    def from_string(
        klass,
        source,
        *,
        exclude=_default_exclude,
    ) -> Self:
        r"""

        --------------------------------------------------------------------------------
        ## from_string

        ==Create a new databox from the objects defined in Python source code held in a string==

        ```
        self = Databox.from_string(
            source,
            exclude=<filter>,
        )
        ```

        The code in `source` is executed as a standalone program, and the
        objects left in its global namespace are collected into a new databox,
        each under the name it had in the code, except for names that are
        excluded as described below. The new databox starts out empty, so the
        code does not see any pre-existing items. To run code against an
        existing databox and add to it, use `execute_string`.

        ### Input arguments

        __`source`__ (`str`)
        :   The Python source code to run, which may span many lines. It is
            executed in a namespace of its own and does not share globals with
            the calling code.

        __`exclude`__ (function or `None`)
        :   A filter that lets you decide which of the objects created by the
            code should not be stored in the new databox; see _Excluded names_
            below. The filter is a function that is handed two things about
            each object, in this order: its name, as a string, and the object
            itself. It answers `True` if the object should be left out and
            `False` if it should be kept. The function must accept both
            arguments, even if it only looks at one of them. If you do not
            specify `exclude`, objects whose names begin with a single
            underscore, such as `_tmp` or `_helper`, are left out. If you
            specify `exclude=None`, no filter is applied, and only the fixed
            exclusions described below remain.

        ### Returns

        A new databox, of the same class as the one on which the method is
        called, holding the objects created by the code.

        ### Excluded names

        Whether an object created by the code is kept out of the databox is
        decided in two steps, and an object is left out if either step
        excludes it.

        The first step is fixed and cannot be changed, and it always leaves
        out two kinds of objects. The first kind are objects whose names begin
        with a double underscore, such as `__builtins__`; Python adds such
        names to every namespace for its own purposes, and they are never
        meant to be data. The second kind are modules, such as the one that
        `import numpy as np` brings in; these are tools the code uses rather
        than results it produces. As a consequence, an import never adds an
        item to the databox.

        The second step is custom and is controlled by the `exclude` argument.
        By default, it leaves out all objects whose names begin with a single
        underscore, following the usual convention that such names are private
        or temporary. You can replace this rule with your own filter, which is
        shown both the name and the value of each object and can therefore
        decide on either one, for instance to leave out names with a certain
        prefix, to keep some underscored names, or to leave out all objects of
        a certain type. You can also switch the custom step off entirely with
        `exclude=None`, in which case only the fixed step applies. Be aware
        that with `exclude=None`, single-underscore names, including the
        `_requires` helper, do end up in the databox.

        Every object that passes both steps is stored, not only data:
        functions and classes defined in the code are stored as well, unless
        `exclude` filters them out.

        ### Details

        Because the new databox starts out empty, calling the helper function
        `_requires` inside the code with any item name will raise a
        `ValueError`. Code that declares requirements is meant to be run
        against an existing databox with `execute_string`.

        Any exception raised by the code, including a syntax error in
        `source`, is propagated to the caller, and no databox is returned.

        --------------------------------------------------------------------------------

        """
        self = klass()
        self.execute_string(source, exclude=exclude)
        return self

    def execute_file(
        self,
        filename: str,
        *,
        exclude=_default_exclude,
    ) -> None:
        r"""

        --------------------------------------------------------------------------------
        ## execute_file

        ==Run a Python script and store the objects it creates in the databox==

        ```
        self.execute_file(
            filename,
            exclude=<filter>,
        )
        ```

        The script found at `filename` is executed as a standalone program,
        much as if it were launched with `python filename`, except that it
        starts out with the current contents of the databox already available
        to it as global variables. When the script finishes, the objects left
        in its global namespace are written back into the databox, each under
        the name it had in the script, except for names that are excluded as
        described below. The databox is modified in place.

        ### Input arguments

        __`filename`__ (`str`)
        :   Path to the Python script to run. The script is executed with
            `runpy.run_path`, in a namespace derived from the contents of the
            databox: each item of the databox is available to the script as a
            global variable of the same name. The script does not share
            globals with the calling code.

        __`exclude`__ (function or `None`)
        :   A filter that lets you decide which of the objects created by the
            script should not be stored in the databox; see _Excluded names_
            below. The filter is a function that is handed two things about
            each object, in this order: its name, as a string, and the object
            itself. It answers `True` if the object should be left out and
            `False` if it should be kept. The function must accept both
            arguments, even if it only looks at one of them. If you do not
            specify `exclude`, objects whose names begin with a single
            underscore, such as `_tmp` or `_helper`, are left out. If you
            specify `exclude=None`, no filter is applied, and only the fixed
            exclusions described below remain.

        ### Returns

        This method returns `None`; the databox is updated in place. An item
        that already exists in the databox is replaced if the script assigns a
        new value to the same name, and all other existing items are left
        untouched.

        ### Excluded names

        Whether an object created by the script is kept out of the databox is
        decided in two steps, and an object is left out if either step
        excludes it.

        The first step is fixed and cannot be changed, and it always leaves
        out two kinds of objects. The first kind are objects whose names begin
        with a double underscore, such as `__name__` and `__builtins__`;
        Python adds such names to every namespace for its own purposes, and
        they are never meant to be data. The second kind are modules, such as
        the one that `import numpy as np` brings in; these are tools the
        script uses rather than results it produces. As a consequence, an
        import never adds an item to the databox, and never replaces an
        existing item of the same name.

        The second step is custom and is controlled by the `exclude` argument.
        By default, it leaves out all objects whose names begin with a single
        underscore, following the usual convention that such names are private
        or temporary. You can replace this rule with your own filter, which is
        shown both the name and the value of each object and can therefore
        decide on either one, for instance to leave out names with a certain
        prefix, to keep some underscored names, or to leave out all objects of
        a certain type. You can also switch the custom step off entirely with
        `exclude=None`, in which case only the fixed step applies. Be aware
        that with `exclude=None`, single-underscore names, including the
        `_requires` helper described below, do end up in the databox.

        Every object that passes both steps is stored, not only data:
        functions and classes defined in the script are stored as well, unless
        `exclude` filters them out.

        ### Details

        Inside the script, the function `_requires` is available. It accepts
        any number of item names and raises a `ValueError` if any of them is
        missing from the databox at the time the script starts. It is meant to
        be called at the top of a script to declare which items the script
        expects the databox to supply; see `requires` for the same check
        performed outside a script.

        The databox is updated only after the script has completed. Any
        exception raised by the script is propagated to the caller, and a
        script that fails part-way leaves the databox unchanged.

        --------------------------------------------------------------------------------

        """
        namespace = runpy.run_path(
            filename,
            init_globals=_create_context(self, ),
        )
        _update_from_namespace(self, namespace, exclude, )

    def execute_string(
        self,
        source,
        *,
        exclude=_default_exclude,
    ) -> None:
        r"""

        --------------------------------------------------------------------------------
        ## execute_string

        ==Run Python source code held in a string and store the objects it creates in the databox==

        ```
        self.execute_string(
            source,
            exclude=<filter>,
        )
        ```

        The code in `source` is executed as a standalone program, except that
        it starts out with the current contents of the databox already
        available to it as global variables. When the code finishes, the
        objects left in its global namespace are written back into the databox,
        each under the name it had in the code, except for names that are
        excluded as described below. The databox is modified in place.

        ### Input arguments

        __`source`__ (`str`)
        :   The Python source code to run, which may span many lines. It is
            executed in a namespace derived from the contents of the databox:
            each item of the databox is available to the code as a global
            variable of the same name. The code does not share globals with
            the calling code.

        __`exclude`__ (function or `None`)
        :   A filter that lets you decide which of the objects created by the
            code should not be stored in the databox; see _Excluded names_
            below. The filter is a function that is handed two things about
            each object, in this order: its name, as a string, and the object
            itself. It answers `True` if the object should be left out and
            `False` if it should be kept. The function must accept both
            arguments, even if it only looks at one of them. If you do not
            specify `exclude`, objects whose names begin with a single
            underscore, such as `_tmp` or `_helper`, are left out. If you
            specify `exclude=None`, no filter is applied, and only the fixed
            exclusions described below remain.

        ### Returns

        This method returns `None`; the databox is updated in place. An item
        that already exists in the databox is replaced if the code assigns a
        new value to the same name, and all other existing items are left
        untouched.

        ### Excluded names

        Whether an object created by the code is kept out of the databox is
        decided in two steps, and an object is left out if either step
        excludes it.

        The first step is fixed and cannot be changed, and it always leaves
        out two kinds of objects. The first kind are objects whose names begin
        with a double underscore, such as `__builtins__`; Python adds such
        names to every namespace for its own purposes, and they are never
        meant to be data. The second kind are modules, such as the one that
        `import numpy as np` brings in; these are tools the code uses rather
        than results it produces. As a consequence, an import never adds an
        item to the databox, and never replaces an existing item of the same
        name.

        The second step is custom and is controlled by the `exclude` argument.
        By default, it leaves out all objects whose names begin with a single
        underscore, following the usual convention that such names are private
        or temporary. You can replace this rule with your own filter, which is
        shown both the name and the value of each object and can therefore
        decide on either one, for instance to leave out names with a certain
        prefix, to keep some underscored names, or to leave out all objects of
        a certain type. You can also switch the custom step off entirely with
        `exclude=None`, in which case only the fixed step applies. Be aware
        that with `exclude=None`, single-underscore names, including the
        `_requires` helper described below, do end up in the databox.

        Every object that passes both steps is stored, not only data:
        functions and classes defined in the code are stored as well, unless
        `exclude` filters them out.

        ### Details

        Inside the code, the function `_requires` is available. It accepts any
        number of item names and raises a `ValueError` if any of them is
        missing from the databox at the time the code starts. It is meant to
        be called at the top of the code to declare which items it expects the
        databox to supply; see `requires` for the same check performed outside
        the code.

        The databox is updated only after the code has completed. Any
        exception raised by the code, including a syntax error in `source`, is
        propagated to the caller, and code that fails part-way leaves the
        databox unchanged.

        --------------------------------------------------------------------------------

        """
        namespace = _create_context(self, )
        exec(source, namespace, )
        _update_from_namespace(self, namespace, exclude, )

    def requires(
        self,
        *names: str,
    ) -> None:
        r"""

        --------------------------------------------------------------------------------
        ## requires

        ==Check that the databox contains all of the listed items==

        ```
        self.requires(
            name1,
            name2,
            ...
        )
        ```

        The method looks up each of the given names in the databox and raises
        an error if any of them is missing. It is a quick way to state, at the
        start of a piece of code, which items the code expects to find in the
        databox, and to fail early with a clear message instead of halfway
        through. If all of the names are present, the method does nothing and
        the databox is left untouched.

        ### Input arguments

        __`name1`, `name2`, ...__ (`str`)
        :   The names of the items the databox is required to contain. You can
            list as many names as you need, including none at all, in which
            case the check always succeeds.

        ### Returns

        This method returns `None`. Its only effect is to raise an error when
        the requirement is not met.

        ### Details

        When several items are missing, they are all reported together in the
        error message, in the order in which you listed them, so you do not
        need to fix them one at a time.

        Inside a script or a string of code run by `execute_file` or
        `execute_string`, the same check is available as the function
        `_requires`, which can be called without any reference to the databox.

        --------------------------------------------------------------------------------

        """
        missing = [
            i for i in names
            if i not in self
        ]
        if missing:
            raise ValueError(
                f"Required items missing from Databox: {missing}"
            )

    #]


def _update_from_namespace(
    self,
    namespace: dict,
    exclude: Callable | None,
) -> None:
    r"""
    """
    def _exclude(name, value, ):
        return (
            _hard_exclude(name, value, )
            or (exclude is not None and exclude(name, value, ))
        )
    self.update(
        (name, value)
        for name, value in namespace.items()
        if not _exclude(name, value, )
    )


def _create_context(self, ) -> dict:
    r"""
    """
    context = dict(self)
    context.update(
        _requires=self.requires,
    )
    return context

